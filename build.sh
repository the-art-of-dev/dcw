#!/bin/bash

# Docker compose wrapper build

source modules/dcw-version.sh

# If -p is passed, bump up patch version
if [ "$1" == "-p" ]; then
    bump_patch
fi

# If -m is passed, bump up minor version
if [ "$1" == "-m" ]; then
    bump_minor
fi

# If -M is passed, bump up major version
if [ "$1" == "-M" ]; then
    bump_major
fi

# Update version in VERSION file
echo $DCW_VERSION >VERSION

cat modules/logger.sh >dcw.sh
echo "export DCW_VERSION=$DCW_VERSION" >>dcw.sh
echo "export DCW_VERSION_MAJOR=$DCW_VERSION_MAJOR" >>dcw.sh
echo "export DCW_VERSION_MINOR=$DCW_VERSION_MINOR" >>dcw.sh
echo "export DCW_VERSION_PATCH=$DCW_VERSION_PATCH" >>dcw.sh
tail -n +2 modules/dcw-update.sh >>dcw.sh
tail -n +2 modules/cli.sh >>dcw.sh
tail -n +2 modules/dcw-services.sh >>dcw.sh
tail -n +2 modules/dcw-envs.sh >>dcw.sh
tail -n +2 modules/dcw-units.sh >>dcw.sh
tail -n +2 modules/main.sh >>dcw.sh
