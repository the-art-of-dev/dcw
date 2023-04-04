#!/bin/bash

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
