# DCW

## Install & Update

Via curl
```
curl https://raw.githubusercontent.com/the-art-of-dev/dcw/main/dcw.sh -o dcw.sh
chmod +x dcw.sh
```

Via wget
```
wget -O dcw.sh https://raw.githubusercontent.com/the-art-of-dev/dcw/main/dcw.sh 
chmod +x dcw.sh
```

## Usage

```
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

## Roadmap

- Fix version sorting
- Fix default environment
- Support generating Jenkins pipelines
- Integrate with maven
- Improve docs