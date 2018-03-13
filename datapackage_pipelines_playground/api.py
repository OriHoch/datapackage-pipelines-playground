from datapackage_pipelines_playground.common import (get_config, temp_file, set_config,
                                                     get_service_account_json_file_path,
                                                     debug, os_system, os_system_generator)
import os, uuid, random, time, subprocess
from flask import Flask, render_template, Response, request


def create_cluster(google_project_id, cluster_name, service_account_json_file):
    os_system(""
              "gcloud auth activate-service-account --key-file={key_file} 2>/dev/null; "
              "gcloud --project={project} container clusters create {cluster} --zone=us-central1-a "
              "       --disk-size=100 --num-nodes=1; "
              "while true; do "
              "    NUM_CLUSTERS=$(gcloud --project=hasadna-oknesset container clusters list --zone=us-central1-a | grep 'knessetdata ' | wc -l); "
              "    ! [ -z \"${{NUM_CLUSTERS}}\" ] && [ \"${{NUM_CLUSTERS}}\" -gt 0 ] && break; "
              "    echo .; sleep 5; "
              "done; "
              "".format(key_file=service_account_json_file,
                        project=google_project_id,
                        cluster=cluster_name))


def setup_namespace(google_project_id, cluster_name, service_account_json_file):
    os_system(""
              "gcloud auth activate-service-account --key-file={key_file} 2>/dev/null; "
              "gcloud config set project {project} 2>/dev/null; "
              "gcloud container clusters get-credentials {cluster} --zone=us-central1-a; "
              "kubectl create namespace dpp-playground; "
              "kubectl create secret generic dpp-playground-sync --from-file=key.json={key_file} --namespace dpp-playground; "
              "".format(key_file=service_account_json_file,
                        project=google_project_id,
                        cluster=cluster_name))


def install_helm(google_project_id, cluster_name, service_account_json_file):
    with temp_file() as rbac_config:
        with open(rbac_config, "w") as f:
            f.write("""apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
""")
        os_system(""
                  "gcloud auth activate-service-account --key-file={key_file} 2>/dev/null; "
                  "gcloud config set project {project} 2>/dev/null; "
                  "gcloud container clusters get-credentials {cluster} --zone=us-central1-a; "
                  "while ! kubectl apply -f {rbac_config}; do sleep 5; echo .; done; "
                  "helm init --service-account tiller --upgrade --force-upgrade --history-max 1; "
                  "".format(key_file=service_account_json_file,
                            project=google_project_id,
                            cluster=cluster_name,
                            rbac_config=rbac_config))
        set_config("environments", [{"name": "default",
                                     "google_project_id": google_project_id,
                                     "cluster_name": cluster_name}])


def run(run_params):
    config = get_config()
    if len(config.get("environments", [])) < 1:
        print("Please run dppctl init to initialize the environment")
        return False
    elif len(config["environments"]) > 1:
        raise NotImplementedError()
    else:
        environment = config["environments"][0]
        pipeline_id = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz0123456789', 32))
        format_kwargs = dict(key_file=get_service_account_json_file_path(),
                             project=environment["google_project_id"],
                             cluster=environment["cluster_name"],
                             pipeline_id=pipeline_id,
                             run_params=run_params)
        debug(format_kwargs)
        debug("Copying pipeline")
        assert os_system(""
                         "gcloud auth activate-service-account --key-file={key_file} 2>/dev/null; "
                         "gcloud config set project {project} 2>/dev/null; "
                         "gsutil -m cp -R /pipeline/'*.yaml' gs://{project}-dpp-playground/pipelines/{pipeline_id}/pipeline/; "
                         "gsutil -m cp -R /pipeline/'*.py' gs://{project}-dpp-playground/pipelines/{pipeline_id}/pipeline/; "
                         "".format(**format_kwargs)) == 0
        # Install the pipeline chart
        with temp_file() as chart_values_filename:
            format_kwargs.update(values=chart_values_filename)
            with open(chart_values_filename, "w") as f:
                f.write("""id: {pipeline_id}
runParams: {run_params}
pipelineGsUrl: gs://{project}-dpp-playground/pipelines/{pipeline_id}/pipeline
""".format(**format_kwargs))
            debug("Installing pipeline chart")
            assert os_system(""
                             "gcloud auth activate-service-account --key-file={key_file} 2>/dev/null; "
                             "gcloud config set project {project} 2>/dev/null; "
                             "gcloud container clusters get-credentials {cluster} --zone=us-central1-a; "
                             "helm install charts/pipeline "
                             "             --name pipeline-{pipeline_id} "
                             "             --namespace dpp-playground "
                             "             --values {values}; "
                             "".format(**format_kwargs)) == 0
            assert os.system(""
                             "while ! kubectl logs pipeline-{pipeline_id} -n dpp-playground -c pipeline -f 2>/dev/null; do sleep 1; done & "
                             "while ! gsutil ls gs://{project}-dpp-playground/pipelines/{pipeline_id}/pipeline/pipelines_complete >/dev/null 2>&1; do sleep 1; done; "
                             "".format(**format_kwargs)) == 0
            assert os_system(""
                             "helm del --purge pipeline-{pipeline_id}; "
                             "gsutil ls gs://{project}-dpp-playground/pipelines/{pipeline_id}/pipeline/data && "
                             "gsutil cp -R gs://{project}-dpp-playground/pipelines/{pipeline_id}/pipeline/data /pipeline/"
                             "".format(**format_kwargs)) == 0

def run_from_gist(gist_url, run_params='all'):
    config = get_config()
    environment = config["environments"][0]
    pipeline_id = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz0123456789', 32))
    format_kwargs = dict(key_file=get_service_account_json_file_path(),
                         project=environment["google_project_id"],
                         cluster=environment["cluster_name"],
                         pipeline_id=pipeline_id,
                         run_params=run_params,
                         gist_url=gist_url)
    debug(format_kwargs)
    with temp_file() as chart_values_filename:
        format_kwargs.update(values=chart_values_filename)
        with open(chart_values_filename, "w") as f:
            f.write("""id: {pipeline_id}
runParams: {run_params}
publicGistUrl: {gist_url}
""".format(**format_kwargs))
        yield from os_system_generator("echo Initializing pipelines environment; "
                                       "( gcloud auth activate-service-account --key-file={key_file}; "
                                       "  gcloud config set project {project} 2>/dev/null; "
                                       "  gcloud container clusters get-credentials {cluster} --zone=us-central1-a; "
                                       "  helm install charts/pipeline "
                                       "               --name pipeline-{pipeline_id} "
                                       "               --namespace dpp-playground "
                                       "               --values {values}; ) >/dev/null 2>&1; "
                                       "echo waiting for pipelines to start; "
                                       "while ! kubectl logs pipeline-{pipeline_id} -n dpp-playground -c pipeline -f 2>/dev/null; do sleep 1; done & "
                                       "( while ! gsutil ls gs://{project}-dpp-playground/pipelines/{pipeline_id}/pipeline/pipelines_complete; do sleep 1; done; "
                                       "  helm del --purge pipeline-{pipeline_id}; ) >/dev/null 2>&1; "
                                       "".format(**format_kwargs))
        yield "done"


def init(google_project_id, cluster_name):
    config = get_config()
    if len(config.get("environments", [])) > 0:
        raise NotImplementedError()
    else:
        print("Creating a new environment for cluster {}".format(cluster_name))
        service_account_json_file = get_service_account_json_file_path()
        create_cluster(google_project_id, cluster_name, service_account_json_file)
        install_helm(google_project_id, cluster_name, service_account_json_file)
        setup_namespace(google_project_id, cluster_name, service_account_json_file)


def serve_playground(*args, **kwargs):
    app = Flask("dpp-playground")

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/", methods=["POST"])
    def run():
        gist_url = request.form["gist_url"]
        def stream_run_response():
            for line in run_from_gist(gist_url):
                yield "<pre>{}</pre>".format(line)
        return Response(stream_run_response())


    app.run(*args, **kwargs)

