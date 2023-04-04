#!/bin/bash

export DCW_VERSION_MAJOR=$(cat VERSION | cut -d. -f1)
export DCW_VERSION_MINOR=$(cat VERSION | cut -d. -f2)
export DCW_VERSION_PATCH=$(cat VERSION | cut -d. -f3)

export DCW_VERSION="$DCW_VERSION_MAJOR.$DCW_VERSION_MINOR.$DCW_VERSION_PATCH"

# Bump up patch version function
bump_patch() {
    export DCW_VERSION_PATCH=$((DCW_VERSION_PATCH + 1))
    export DCW_VERSION="$DCW_VERSION_MAJOR.$DCW_VERSION_MINOR.$DCW_VERSION_PATCH"
}

# Bump up minor version function
bump_minor() {
    export DCW_VERSION_MINOR=$((DCW_VERSION_MINOR + 1))
    export DCW_VERSION_PATCH="0"
    export DCW_VERSION="$DCW_VERSION_MAJOR.$DCW_VERSION_MINOR.$DCW_VERSION_PATCH"
}

# Bump up major version function
bump_major() {
    export DCW_VERSION_MAJOR=$((DCW_VERSION_MAJOR + 1))
    export DCW_VERSION_MINOR="0"
    export DCW_VERSION_PATCH="0"
    export DCW_VERSION="$DCW_VERSION_MAJOR.$DCW_VERSION_MINOR.$DCW_VERSION_PATCH"
}

# Compare two versions function
# Returns 0 if version1 is equal to version2
# Returns 1 if version1 is greater than version2
# Returns 2 if version1 is less than version2
function compare_versions() {
    if [ "$1" = "$2" ]; then
        return 0
    fi
    if [ "$1" = "$(echo -e "$1\n$2" | sort -V | head -n1)" ]; then
        return 2
    fi
    return 1
}

# Get last published version function
function get_last_published_version() {
    echo $(curl -s https://raw.githubusercontent.com/the-art-of-dev/dcw/main/VERSION)
}