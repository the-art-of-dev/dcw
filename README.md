# DCW - Deployment Configuration Wrapper | Docker Compose Wrapper

## Table of content

## Purpose

Manage deployment configuration for simple and semi-complex deployment environments using docker compose files in yaml
format, resulting in a deployment configuration specific to the deployment environment.

## Installation

Requirements:

- Python3 (>=3.7)
- docker-compose
- kompose

```sh
pip3 install "git+https://github.com/the-art-of-dev/dcw.git#egg=dcw"
```

## Boundaries

- Use docker compose yaml files to describe services you need

- Use simple text files to describe the deployment units with the services that should be deployed in them

- Use simple text files to describe environment variables used for templating the docker compose files

- Use simple text files to describe tenants to reuse the same deployment configuration in multiple product customizations

- Use text templates to standardize the process of creating the same type of services, environments, and units

- Use encrypted files to store sensitive information

## Terminology

This tool allows you to create clear interfaces toward development team. It's not intended to hide complexity of how
deployment/execution environments work but to create clear interface between members of the development team.

### Service

- A service is an application that is deployed in a unit
- A service is described in a docker compose file
- A service can be deployed in multiple units
- A service can be deployed in multiple environments
- A service uses environment variables to configure it's deployment
- A service can be deployed in multiple versions

### Unit

- A unit is a deployment unit that is deployed in an environment
- A unit is described in a simple text file
- A unit contains a list of services that should be deployed in it
- A unit can be deployed in multiple environments

### Environment

- An environment is a list of environment variables that are used to configure the deployment of units
- An environment is described in a simple text file
- An environment contains a list of environment variables

### Template

- A template is a text file that is used to create other text files
- A template can be used to create services
- A template can be used to create units
- A template can be used to create environments

### Tenant

- A tenant is a group of unit and environment pairs
- A tenant is described in a text file

## Supported deployment platforms

- Docker compose like (docker-compose)
- Kubernetes like (kubectl)


## Development

SETUP
```
python3 -m venv .
source source ./bin/activate
export PYTHONPATH="$(pwd)"
pip install -r requirements.txt
```

RUN
```
python dcw/cli.py
```