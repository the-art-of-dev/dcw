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
WELCOME TO DCW 0.1.3

Usage:	dcw.sh [options] [dcw-units] [docker-compose options]

Options:
	
	-h, --help (show help message)
	-e, --env [environment] (set environment)
	-l, --list (list available dcw-units)
	--init (init dcw-units directory)
	--list-env (list available environments)
	--show-env [environment] (show environment variables)
	--list-services, --ls (list available services)

	--debug (enable debug mode)

	-p, --project [project] (set project name)

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