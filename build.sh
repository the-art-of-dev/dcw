#!/bin/bash

# Docker compose wrapper build

cat modules/logger.sh > dcw.sh
tail -n +2 modules/cli.sh >> dcw.sh
tail -n +2 modules/dcw-services.sh >> dcw.sh
tail -n +2 modules/dcw-envs.sh >> dcw.sh
tail -n +2 modules/dcw-units.sh >> dcw.sh
tail -n +2 modules/main.sh >> dcw.sh

