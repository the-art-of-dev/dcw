```yaml
services:
  web-server:
    service_groups: [unit2, unit3]
    tasks:
      - wst1
      - wst2
      - setup_db
    image: websrv:latest
    ports:
      - 2020:2020
    labels: {}
    environment: {}   
    docker-compose-config: {}

tasks:
  setup_db:
    debug:
      msg: ${DB_HOST} is used as db host!


environments:
  ep-dev:
    tenant: europoint
    deployment_types: docker-compose
    services:
      - neki1
    service_gorups:
      - unit1
    tasks:
      - task1
    variables:
      ENV1: nesto
      ENV2: nesto
  ep-qa:
    tenant: europoint
    deployment_types: [docker-compose, k8s]
    services:
      - neki1
      - neki2
    service_gorups:
      - unit1
    tasks:
      - task2
    variables:
      ENV1: nesto1
      ENV2: nesto1

```