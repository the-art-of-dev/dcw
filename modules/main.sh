#!/bin/bash

# Docker compose wrapper DCW main module

# Check for new version
check_last_published_version

# Print help message if no arguments
if [ $# -eq 0 ]; then
    help
    exit 1
fi

check_dcw_units $1

# Parse multiple options
while [[ $# -gt 0 ]]; do
    if [[ $1 == -* ]]; then
        case $1 in
        -h | --help)
            help
            exit 0
            ;;
        -e | --env)
            export ENV=$2
            shift 2
            ;;
        -l | --list)
            get_dcw_units
            exit 0
            ;;
        --init)
            init_dcw_units
            init_environments
            shift
            ;;
        --list-env)
            get_environments
            exit 0
            ;;
        --show-env)
            show_env $2
            exit 0
            ;;
        --list-services | --ls)
            get_services
            exit 0
            ;;
        --debug)
            export DCW_DEBUG=true
            shift
            ;;
        -p | --project)
            export DCW_PROJECT=$2
            shift 2
            ;;
        *)
            error "Unknown option $1\n"
            help
            exit 1
            ;;
        esac
    else
        break
    fi
done

# Check if DCW_PROJECT is set
if [ -z "$DCW_PROJECT" ]; then
    warning "DCW_PROJECT is not set, using 'dcw' as default"
    export DCW_PROJECT=dcw
else
    info "DCW_PROJECT is set to $DCW_PROJECT"
fi

# If environment is not set, set it to example
if [ -z "$ENV" ]; then
    export ENV=example
    warning "ENV is not set, using 'example'"
else
    info "ENV is set to $ENV"
fi

# Split dcw-units by dot and run them
IFS='.' read -ra dcw_units <<<"$1"
for dcw_unit in "${dcw_units[@]}"; do
    run_dcw_unit $dcw_unit $ENV "${@:2}"
done
