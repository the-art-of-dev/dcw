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
