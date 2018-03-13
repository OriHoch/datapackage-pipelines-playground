import sys
from datapackage_pipelines_playground import api


def usage():
    print("Available Commands:\n"
          "\n"
          "dppctl init <GOOGLE_PROJECT_ID> <CLUSTER_NAME>\n"
          "    Initialize the playground environment\n"
          "    GOOGLE_PROJECT_ID - google cloud platform project id\n"
          "    CLUSTER_NAME - name of the cluster to schedule workloads on\n"
          "\n"
          "dppctl run <DPP_RUN_ARGS>..\n"
          "    Run a pipeline on the playground\n"
          "    DPP_RUN_ARGS - arguments to pass to dpp from the playground pipeline directory\n"
          "\n"
          "dppctl serve-playground [PORT:8080]\n"
          "    Serve the playground web-app\n"
          )


def dppctl():
    if len(sys.argv) > 2 and sys.argv[1] == "init":
        exit(0 if api.init(sys.argv[2], sys.argv[3]) else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "run":
        exit(0 if api.run(" ".join(sys.argv[2:])) else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "serve-playground":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        exit(0 if api.serve_playground(port=port) else 1)
    else:
        usage()
        exit(1)
