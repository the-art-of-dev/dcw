#!/bin/bash

# Get patch version from version function
get_patch_version() {
    echo "$1" | cut -d. -f3
}

# Get minor version from version function
get_minor_version() {
    echo "$1" | cut -d. -f2
}

# Get major version from version function
get_major_version() {
    echo "$1" | cut -d. -f1
}

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

export DCW_VERSION=$(cat VERSION)
export DCW_VERSION_MAJOR=$(get_major_version $DCW_VERSION)
export DCW_VERSION_MINOR=$(get_minor_version $DCW_VERSION)
export DCW_VERSION_PATCH=$(get_patch_version $DCW_VERSION)
