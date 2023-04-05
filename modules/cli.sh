#!/bin/bash

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
