# DCW CLI Commands

## svc | service

```bash
dcw svc [OPTIONS] (COMMAND)
```

| Argument name | Argument description   |
| :-----------: | ---------------------- |
|   `COMMAND`   | `list`, `show`, `args` |

## env | environment

```bash
dcw env [OPTIONS] (COMMAND)
```

| Argument name | Argument description |
| :-----------: | -------------------- |
|   `COMMAND`   | `list`, `show`       |

## svc-group | service group

```bash
dcw svc-group [OPTIONS] (COMMAND)
```

| Argument name | Argument description |
| :-----------: | -------------------- |
|   `COMMAND`   | `list`, `show`       |

## depl | deployment

```bash
dcw depl [OPTIONS] (COMMAND)
```

| Argument name | Argument description                      |
| :-----------: | ----------------------------------------- |
|   `COMMAND`   | `list`, `show`, `check`, `bundle`, `spec` |

| Option name | Option description | Default |
| :---------: | ------------------ | :-----: |
|   `--env`   | Specify units      |         |
|   `--svc`   | Specify services   |         |
|             |                    |         |

## x | execute

```bash
dcw x [OPTIONS] (deployment) (command)
```

| Argument name | Argument description                                                           |
| :-----------: | ------------------------------------------------------------------------------ |
| `deployment`  | Specify tenant deployment(unit name)                                           |
|   `command`   | Command to run on deployment specific cli tool (e.g.: docker-compose, kubectl) |

## xs | execute-service

```bash
dcw xs [OPTIONS] (deployment) (service) (command)
```

| Argument name | Argument description                                                           |
| :-----------: | ------------------------------------------------------------------------------ |
| `deployment`  | Specify tenant deployment(unit name)                                           |
|   `command`   | Command to run on deployment specific cli tool (e.g.: docker-compose, kubectl) |

## valut

```bash
dcw vault [OPTIONS] (COMMAND)
```

| Argument name | Argument description                 |
| :-----------: | ------------------------------------ |
|   `COMMAND`   | `list`, `show`, `encrypt`, `decrypt` |
