#!/bin/bash

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

        debug "Running docker-compose ${dcw_files} --env-file $(get_env_path $1 $2) --profile true -p gen2 ${@:3}"

        docker-compose ${dcw_files} --env-file $(get_env_path $1 $2) --profile true -p gen2 ${@:3}

        info "Done"
    else
        error "dcw-units/dcw.$1.txt not found"
    fi
}
