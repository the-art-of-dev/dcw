# DCW CLI Commands

```bash
dcw
```

| Option name | Option description | Default |
| :---------: | ------------------ | :-----: |
| `--tenant`  | Specify tenant     |  local  |
|             |                    |         |

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

## unit

```bash
dcw unit [OPTIONS] (COMMAND)
```

| Argument name | Argument description    |
| :-----------: | ----------------------- |
|   `COMMAND`   | `list`, `show`, `apply` |

## task

```bash
dcw task [OPTIONS] (COMMAND)
```

| Argument name | Argument description   |
| :-----------: | ---------------------- |
|   `COMMAND`   | `list`, `show`, `args` |

## tnt | tenant

```bash
dcw tnt [OPTIONS] (COMMAND)
```

| Argument name | Argument description                     |
| :-----------: | ---------------------------------------- |
|   `COMMAND`   | `list`, `show`, `check`, `envs`, `depls` |

## depl | deployment

```bash
dcw depl [OPTIONS] (COMMAND)
```

| Argument name | Argument description                               |
| :-----------: | -------------------------------------------------- |
|   `COMMAND`   | `list`, `show`, `check`, `bundle`, `tasks`, `spec` |

| Option name | Option description | Default |
| :---------: | ------------------ | :-----: |
|  `--unit`   | Specify units      |         |
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

## r | run

```bash
dcw r [OPTIONS] (deployment) (task)
```

| Argument name | Argument description                 |
| :-----------: | ------------------------------------ |
| `deployment`  | Specify tenant deployment(unit name) |
|    `task`     | Specify deployment task to run       |

## rs | run-service

```bash
dcw rs [OPTIONS] (deployment) (service) (task)
```

| Argument name | Argument description                 |
| :-----------: | ------------------------------------ |
| `deployment`  | Specify tenant deployment(unit name) |
|   `service`   | Specify deployment service           |
|    `task`     | Specify deployment task to run       |

## valut

```bash
dcw vault [OPTIONS] (COMMAND)
```

| Argument name | Argument description                 |
| :-----------: | ------------------------------------ |
|   `COMMAND`   | `list`, `show`, `encrypt`, `decrypt` |
