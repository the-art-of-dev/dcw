from os import path


config = {
    'DCW_SVCS_DIR': 'dcw-svcs',
    'DCW_UNITS_DIR': 'dcw-units',
    'DCW_ENVS_DIR': 'dcw-envs',
    'DCW_TMPLS_DIR': 'dcw-tmpls',
    'TMP_DIR': 'tmp',
    'DCW_ROOT': '.'
}


def get_config(name: str) -> str:
    if name not in config:
        raise Exception(f'Invalid config name: {name}')

    if name.endswith('_DIR'):
        return path.join(config['DCW_ROOT'], config[name])

    return config[name]


def set_config(name: str, value: str):
    if name not in config:
        raise Exception(f'Invalid config name: {name}')

    config[name] = value
