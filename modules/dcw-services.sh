#!/bin/bash

# Docker compose wrapper DCW service module

# Get services list function
function get_services() {
    for service in services/docker-compose.*.yml; do
        echo "${service##*/.}" | cut -d. -f2
    done
}