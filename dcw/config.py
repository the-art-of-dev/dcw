import os
import enum
import yaml
from pprint import pprint as pp


class DCWMagicConfigs(str, enum.Enum):
    DCW_ROOT = 'DCW_ROOT'
    DCW_SVCS_PATH = 'DCW_SVCS_PATH'
    DCW_UNITS_PATH = 'DCW_UNITS_PATH'
    DCW_ENVS_PATH = 'DCW_ENVS_PATH'
    DCW_TMPLS_PATH = 'DCW_TMPLS_PATH'
    DCW_DEPLS_PATH = 'DCW_DEPLS_PATH'
    DCW_DEPL_CONFIGS_PATH = 'DCW_DEPL_CONFIGS_PATH'
    DCW_CLI_VERBOSE = 'DCW_CLI_VERBOSE'


class DCWConfig:
    def __init__(self, config: dict = None) -> None:
        self.__dict = {
            DCWMagicConfigs.DCW_ROOT: '.',
            DCWMagicConfigs.DCW_SVCS_PATH: 'dcw-svcs',
            DCWMagicConfigs.DCW_ENVS_PATH: 'dcw-envs',
            DCWMagicConfigs.DCW_UNITS_PATH: 'dcw-units',
            DCWMagicConfigs.DCW_TMPLS_PATH: 'dcw-tmpls',
            DCWMagicConfigs.DCW_DEPLS_PATH: 'dcw-depls',
            DCWMagicConfigs.DCW_DEPL_CONFIGS_PATH: 'depl-configs'
        }
        if config is not None:
            self.__apply_config(config)

    def __getitem__(self, key: str):
        if key not in self.__dict:
            raise Exception(f'Invalid config key: {key}')

        if key.endswith('_PATH'):
            return os.path.join(self.__dict[DCWMagicConfigs.DCW_ROOT], self.__dict[key])

        return self.__dict[key]

    def __setitem__(self, key: str, value):
        self.__dict[key] = value

    def __apply_config(self, config: dict):
        if config is None:
            return

        self.__dict = {
            **self.__dict,
            ** config
        }

    def __iadd__(self, other):
        if isinstance(other, dict):
            self.__apply_config(other)
        return self


def import_config_from_file(file_path: str):
    file_name = os.path.basename(file_path)
    if not file_name.startswith('.dcwrc') and not file_name.endswith('.yaml'):
        return None
    if not os.path.exists(file_path):
        return DCWConfig()
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
        if 'config' in data:
            return DCWConfig(data['config'])
        return None
