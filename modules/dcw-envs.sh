#!/bin/bash

# Docker compose wrapper DCW env module

# Get environments list function
function get_environments() {
    for env in environments/.*.env; do
        echo "${env##*/.}" | cut -d. -f1
    done
}

# Show environment variables function
function show_env() {
    if [ -f "environments/.$1.env" ]; then
        cat "environments/.$1.env"
    else
        error "environments/.$1.env not found"
    fi
}

# Get environment path from environment name and dcw unit name function
function get_env_path() {
    if [ -f "environments/.$1-$2.env" ]; then
        echo "environments/.$1-$2.env"
    else
        error "environments/.$1-$2.env not found"
        exit 1
    fi
}


# Init empty environments directory function
function init_environments() {
    if [ -d "environments" ]; then
        warning "environments directory already exists"
        return
    fi

    info "Initializing environments directory"
    mkdir environments
    touch environments/.example-local.env

    info "environments directory initialized"
}
