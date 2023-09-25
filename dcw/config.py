import os
import enum
import yaml
from pprint import pprint as pp


class DCWConfigMagic(str, enum.Enum):
    DCW_ROOT = 'DCW_ROOT'
    DCW_SVCS_PATH = 'DCW_SVCS_PATH'
    DCW_UNITS_PATH = 'DCW_UNITS_PATH'
    DCW_ENVS_PATH = 'DCW_ENVS_PATH'
    DCW_TMPLS_PATH = 'DCW_TMPLS_PATH'
    DCW_DEPLS_PATH = 'DCW_DEPLS_PATH'
    DCW_DEPL_CONFIGS_PATH = 'DCW_DEPL_CONFIGS_PATH'
    DCW_VAULT_PATH = 'DCW_VAULT_PATH'
    DCW_TASKS_PATH = 'DCW_TASKS_PATH'
    DCW_TENANT = 'DCW_TENANT'
    DCW_TENANT_DEPL_ROOT = 'DCW_TENANT_DEPL_ROOT'


class DCWConfig:
    def __init__(self, config: dict = None) -> None:
        self.__dict = {
            DCWConfigMagic.DCW_ROOT: '.',
            DCWConfigMagic.DCW_SVCS_PATH: 'dcw-svcs',
            DCWConfigMagic.DCW_ENVS_PATH: 'dcw-envs',
            DCWConfigMagic.DCW_UNITS_PATH: 'dcw-units',
            DCWConfigMagic.DCW_TMPLS_PATH: 'dcw-tmpls',
            DCWConfigMagic.DCW_DEPLS_PATH: 'dcw-depls',
            DCWConfigMagic.DCW_DEPL_CONFIGS_PATH: 'depl-configs',
            DCWConfigMagic.DCW_VAULT_PATH: 'dcw-vault',
            DCWConfigMagic.DCW_TENANT: 'local',
            DCWConfigMagic.DCW_TENANT_DEPL_ROOT: 'tenants'
        }
        if config is not None:
            self.__apply_config(config)

    def __getitem__(self, key: str):
        if key not in self.__dict:
            raise Exception(f'Invalid config key: {key}')

        if key.endswith('_PATH'):
            return os.path.join(self.__dict[DCWConfigMagic.DCW_ROOT], self.__dict[key])

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
    file_dir = os.path.dirname(file_path)
    if not file_name.startswith('.dcwrc') and not file_name.endswith('.yaml'):
        return None
    if not os.path.exists(file_path):
        return DCWConfig()
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
        if 'dcw_rc' in data:
            return import_config_from_file(os.path.join(file_dir, data['dcw_rc']))
        if 'config' in data:
            return DCWConfig(data['config'])
        return None
