# Vault

> NOTE: Vault directory path is configurable via .dcwrc.yaml config

Vault reades 

CLI examples:
```
dcw vault encrypt [--key]
dcw vault decrypt [--key]
```

## Environments

Contains list of environment names to be stored in vault

### Encrypt

For every environemnt name (example: `example-secure`) encrypt its file (example: `./dcw-envs/.example-secure.env`) and store it to path `./dcw-vault/envs/.example-secure.env.crypt`

### Decrypt

For every environemnt name (example: `example-secure`) decrypt its vault file (example: `./dcw-vault/envs/.example-secure.env.crypt`) and restore it to its file path `./dcw-envs/.example-secure.env`


