# DCW

```bash
WELCOME TO DCW

Usage:  dcw.sh [options] [dcw-units] [docker-compose options]

Option: -h, --help (show help message)
Option: -e, --env [environment] (set environment)
Option: -l, --list (list available dcw-units)
Option: --init (init dcw-units directory)
Option: --list-env (list available environments)
Option: --show-env [environment] (show environment variables)
Option: --list-services, --ls (list available services)


Examples:

        dcw.sh be up -d
        dcw.sh be.fe up -d (run multiple dcw-units)
        dcw.sh -e dev be up -d (run with custom environment)
        ENV=dev dcw.sh be up -d (run with custom environment)
```