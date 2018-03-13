FROM frictionlessdata/datapackage-pipelines:1.6.11

RUN apk --update --no-cache add build-base python3-dev curl python bash libc6-compat openssh-client git jq \
                                libxml2 libxml2-dev git libxslt libxslt-dev openssl &&\
    pip install --upgrade pip && pip install --no-cache-dir pipenv pew python-dotenv pyyaml crcmod

ENV CLOUD_SDK_VERSION 190.0.1
ENV PATH /google-cloud-sdk/bin:$PATH
RUN cd / && curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz &&\
    tar xzf google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && rm google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && ln -s /lib /lib64 &&\
    gcloud config set core/disable_usage_reporting true && gcloud config set component_manager/disable_update_check true &&\
    gcloud config set metrics/environment github_docker_image && gcloud --version
VOLUME ["/root/.config"]

RUN gcloud --quiet components install kubectl &&\
    curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get > get_helm.sh &&\
    chmod 700 get_helm.sh &&\
    ./get_helm.sh &&\
    rm ./get_helm.sh

COPY Pipfile /pipelines/
COPY Pipfile.lock /pipelines/
RUN pipenv install --system --deploy --ignore-pipfile && pipenv check

COPY *.py /pipelines/
COPY charts /pipelines/charts
COPY datapackage_pipelines_playground /pipelines/datapackage_pipelines_playground
RUN pip install -e .

ENTRYPOINT ["dppctl"]
