# {{ cookiecutter.project_name }}

{{ cookiecutter.project_short_description }}

## Overview

This connector provides and integration for DSX-Connect with a {{ cookiecutter.repository }}.  When this
connector is running, you can get the status of the connector from its home page, typically:
```http request
{{ cookiecutter.__base_connector_url }}
```

and the API that it serves can be accessed via:

```http request
{{ cookiecutter.__base_connector_url }}/docs
```

## Deploying Filesystem Connector
### Docker Compose
This package contains an easy to use docker-compose.yaml file for configuration and deployment of the
Filesystem Connector in a docker environment.

#### Config via docker-compose

The first part that should be changed, the ports this service listens on (optional), and a
volume definition.  For the Filesystem Connector you are mounting the folder that you want to
scan external to the docker environment, and what that maps to within the connector.

##### Port and Volume Maps
In the case, the volume mapping is from a local directory to /app/scan_folder.  Note that this /app/scan_folder
should be mirrored in the configuration specified in the next section (DSXCONNECTOR_LOCATION).

```yaml
      ports:
        - "8590:8590"
      volumes:
        - /Users/localuser/Documents/SAMPLES:/app/scan_folder  # this directory should have been created in the Dockerfile
```

##### Connector service configuration
This connector's configuration has defaults defined in the config.py file in this same directory, a Pydantic
BaseSettings class.  Pydantic is used because it provides data validation and type safety, and a class structure for easy
and IDE friendly development.  Pydantic also has convenient built-in functions so that users
can override default settings with .env files or environment settings (among other mechanisms), which is a preferred
method to configure docker containers deployed in dockers or kubernetes.

While the config.py file defines all fo the defaults, you probably don't want to edit these directly in the
python script unless you want to permanently change the defaults settings.

To configure this connector (and override config.py defaults), you simply set name=value environment settings by
specifying DSXCONNECTOR_<NAME_OF_SETTING>=<value> (note all CAPS)

```yaml
      environment:
        - PYTHONUNBUFFERED=1
        - DSXCONNECTOR_CONNECTOR_URL=http://filesystem-connector-api:8590 # see aliases below
        - DSXCONNECTOR_DSX_CONNECT_URL=http://dsx-connect-api:8586 # note, this works if running on the same internal network on Docker as the dsx_connect_core...
        - DSXCONNECTOR_LOCATION=/app/scan_folder
        - LOG_LEVEL=debug
        - DSXCONNECTOR_ITEM_ACTION=nothing
        - DSXCONNECTOR_ITEM_ACTION_MOVE_DIR=/app/quarantine # this directory should have been created in the Dockerfile
        - DSXCONNECTOR_RECURSIVE=true

```

##### Networking
The remainder is configuration of this service, and the docker network this connector shares with
DSX Connect.  The external name of the dsx-network below should be the same as the network
DSX Connect uses, if deployed within the same docker environment.

```yaml
      networks:
        dsx-network:
        aliases:
          - filesystem-connector-api  # this is how dsx-connect will communicate with this on the network
      command:
        python connectors/filesystem/filesystem_connector.py
```

```yaml
# The following assumes an already created docker network like this:
# docker network create dsx-connect-network --driver bridge
networks:
  dsx-network:
    external: true
    name: dsx-connect-network  # change this to an existing docker network
```
#### Deployment
Run docker compose from the same directoy as the docker-compose.yaml file using
up command (-d to detach from execution)
```shell
docker-compose up -d
```
To shut down:
```shell
docker-compose down
```
