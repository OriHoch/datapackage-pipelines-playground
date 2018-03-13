# datapackage-pipelines-playground
Provide a user friendly interface to use the datapackage pipelines framework online

**work in progress**

![design doc](image.png)


## Usage

Install [Docker](https://docs.docker.com/install/)

Create a directory to hold the dppctl configuration and persistent data

```
mkdir -p $HOME/.dpp-playground
```

Create a Google Compute Cloud service account with permissions to modify / create the cluster

Save the service account json key file to `$HOME/.dpp-playground/secret.json`

See the available commands and usage

```
docker run -it \
           -v $HOME/.dpp-playground:/etc/dpp-playground \
           orihoch/dppctl
```

To run a pipeline, you need to mount the pipeline directory into the container at /pipeline directory

```
docker run -it \
           -v $HOME/.dpp-playground:/etc/dpp-playground \
           -v `pwd`/tests/pipelines/noise:/pipeline \
           orihoch/dppctl run ./noise
```

The pipeline directory should contain only `pipeline-spec.yaml` files and related `.py` files for custom processors

Other files will be ignored


## Development

Build

```
docker build -t dppctl .
```

run with debugging and code directory mounted as volume

```
docker run -it \
           -v $HOME/.dpp-playground:/etc/dpp-playground \
           -v `pwd`:/pipelines \
           -e DEBUG=1 \
           dppctl
```

run a pipeline

```
docker run -it \
           -v $HOME/.dpp-playground:/etc/dpp-playground \
           -v `pwd`:/pipelines \
           -v `pwd`/tests/pipelines/noise:/pipeline \
           -e DEBUG=1 \
           dppctl run ./noise
```
