#!/bin/bash

# Docker compose wrapper logger module

# Print info message function
function info() {
    printf "[\e[32mINFO\e[0m] $1\n"
}

# Print error message function
function error() {
    printf "[\e[31mERROR\e[0m] $1\n"
}

# Print warning message function
function warning() {
    printf "[\e[33mWARNING\e[0m] $1\n"
}

# Print debug message function
function debug() {
    if [ "$DCW_DEBUG" == "true" ]; then
        printf "[\e[36mDEBUG\e[0m] $1\n"
    fi
}
export DCW_VERSION=0.1.3
export DCW_VERSION_MAJOR=0
export DCW_VERSION_MINOR=1
export DCW_VERSION_PATCH=3

# Compare two versions function
# Returns 0 if version1 is equal to version2
# Returns 1 if version1 is greater than version2
# Returns 2 if version1 is less than version2
function compare_versions() {
    if [ "$1" = "$2" ]; then
        echo 0
        return 0
    fi
    if [ "$1" = "$(echo -e "$1\n$2" | sort -V | head -n1)" ]; then
        echo 2
        return 2
    fi
    echo 1
    return 1
}

# Get last published version function
function get_last_published_version() {
    echo $(curl -s https://raw.githubusercontent.com/the-art-of-dev/dcw/main/VERSION)
}

# Check if last published version is greater than local version
# If it is, print warning message
function check_last_published_version() {
    PUB_VER=$(get_last_published_version)
    cmp_result=$(compare_versions $DCW_VERSION $PUB_VER)
    if [ $cmp_result -eq 2 ]; then
        warning "Local version is less than published version"
        warning "Please update dcw by running provided commands on https://github.com/the-art-of-dev/dcw"
    fi
}

# Docker compose wrapper cli module

function title() {
    printf "\e[1m\e[4m\e[3$((RANDOM % 6 + 1))m$1\e[0m\n"
}

# Pretty print help line function
function help_line() {
    printf "$1\t$2\n"
}

# Print random color message function
function random_color() {
    printf "\e[3$((RANDOM % 6 + 1))m$1\e[0m\n"
}

# Print welcome message function
function welcome() {
    title "WELCOME TO DCW $DCW_VERSION\n"
}

# Print help message function
function help() {
    welcome

    help_line "Usage:" "dcw.sh [options] [dcw-units] [docker-compose options]\n"
    help_line "Options:\n" ""
    help_line "" "-h, --help (show help message)"
    help_line "" "-e, --env [environment] (set environment)"
    help_line "" "-l, --list (list available dcw-units)"
    help_line "" "--init (init dcw-units directory)"
    help_line "" "--list-env (list available environments)"
    help_line "" "--show-env [environment] (show environment variables)"
    help_line "" "--list-services, --ls (list available services)\n"
    help_line "" "--debug (enable debug mode)\n"
    help_line "" "-p, --project [project] (set project name)"
    help_line "\nExamples:\n" ""
    help_line "" "dcw.sh be up -d"
    help_line "" "dcw.sh be.fe up -d (run multiple dcw-units)"
    help_line "" "dcw.sh -e dev be up -d (run with custom environment)"
    help_line "" "ENV=dev dcw.sh be up -d (run with custom environment)"
}

# Docker compose wrapper DCW service module

# Get services list function
function get_services() {
    for service in services/docker-compose.*.yml; do
        echo "${service##*/.}" | cut -d. -f2
    done
}
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

# Docker compose wrapper DCW unit module

# Check if dcw-units directory exists and option is not --int function
function check_dcw_units() {
    if [ ! -d "dcw-units" ] && [ "$1" != "--init" ]; then
        error "dcw-units directory not found"
        info "Run dcw.sh --init to init dcw-units directory"
        exit 1
    fi
}

# Init empty dcw-units directory function
function init_dcw_units() {
    if [ -d "dcw-units" ]; then
        warning "dcw-units directory already exists"
        return
    fi

    info "Initializing dcw-units directory"
    mkdir dcw-units
    touch dcw-units/dcw.example.txt

    info "dcw-units directory initialized"
}

# Get dcw-units names list function
function get_dcw_units() {
    for dcwu in dcw-units/dcw.*.txt; do
        echo "${dcwu##*/dcw.}" | cut -d. -f1
    done
}

# Run dcw-unit function
function run_dcw_unit() {
    if [ -f "dcw-units/dcw.$1.txt" ]; then
        info "Running ./dcw-units/dcw.$1.txt"

        local dcw_files=""
        while IFS= read -r line; do
            if [ -f "$line" ]; then
                dcw_files="$dcw_files -f $line"
            else
                warning "dcw-units/dcw.$1.txt: $line not found"
            fi
        done <"./dcw-units/dcw.$1.txt"

        if [ ! -z "$line" ]; then
            if [ -f "$line" ]; then
                dcw_files="$dcw_files -f $line"
            else
                warning "dcw-units/dcw.$1.txt: $line not found"
            fi
        fi

        debug "Running docker-compose ${dcw_files} --env-file $(get_env_path $1 $2) --profile true -p $DCW_PROJECT ${@:3}"

        docker-compose ${dcw_files} --env-file $(get_env_path $1 $2) --profile true -p $DCW_PROJECT ${@:3}

        info "Done"
    else
        error "dcw-units/dcw.$1.txt not found"
    fi
}

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
