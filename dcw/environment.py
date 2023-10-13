# pylint: skip-file
import copy
import enum
import os
import re
from dotenv import dotenv_values
from dcw.utils import dot_env_to_dict_rec, flatten_dict, deep_update
from pprint import pprint as pp
from dcw.service import DCWService


class DCWEnvMagicSettingType(str, enum.Enum):
    SERVICE_GROUPS = 'dcw.service_groups'
    SERVICES = 'dcw.services'
    DEPLOYMENT_TYPE = 'dcw.deployment_type'
    SERVICE_SELECTOR = 'dcw.svc.'
    SERVICE_GROUP_SELECTOR = 'dcw.svc_group.'


class DCWEnvMagicSettingsPropertySelectorType(str, enum.Enum):
    OBJECT = 'object'
    FLAT = 'flat'


class DCWEnvMagicSettingsSelectorWildcard(str, enum.Enum):
    ANY = '*'


class DCWEnv:
    def __init__(self, name: str, env_vars: dict = None) -> None:
        if env_vars is None:
            env_vars = {}

        self.name = name
        self.services = []
        self.svc_groups = []
        self.global_envs = {}
        self.service_configs: dict[str, dict] = {}
        self.svc_group_configs: dict[str, dict] = {}
        self.__env_vars = env_vars

        for k, v in self.__env_vars.items():
            self.set_env(k, v)

    def __type_from_magic_env_name(self, env_name: str) -> DCWEnvMagicSettingType:
        for st in DCWEnvMagicSettingType:
            if env_name.startswith(st.value):
                return st
        return None

    def __selector_from_magic_env_name(self, env_name: str) -> str:
        env_type = self.__type_from_magic_env_name(env_name)
        if env_type == DCWEnvMagicSettingType.SERVICE_SELECTOR:
            return env_name[len(env_type.value):].split('.')[0]
        elif env_type == DCWEnvMagicSettingType.SERVICE_GROUP_SELECTOR:
            return env_name[len(env_type.value):].split('.')[0]
        else:
            return None

    def __prop_selector_from_magic_env_name(self, env_name: str):
        env_type = self.__type_from_magic_env_name(env_name)
        prop_selector = None
        if env_type == DCWEnvMagicSettingType.SERVICE_SELECTOR:
            selector = self.__selector_from_magic_env_name(env_name)
            prop_selector = env_name[len(f'{env_type.value}{selector}.'):]
        elif env_type == DCWEnvMagicSettingType.SERVICE_GROUP_SELECTOR:
            selector = self.__selector_from_magic_env_name(env_name)
            prop_selector = env_name[len(f'{env_type.value}{selector}.'):]

        if prop_selector.endswith('[]'):
            prop_selector = prop_selector[:-2]

        return prop_selector

    def __prop_selector_type_from_magic_env_name(self, env_name: str):
        prop_selector = self.__prop_selector_from_magic_env_name(env_name)

        if prop_selector.endswith(']') and prop_selector.count('.[') == 1:
            return DCWEnvMagicSettingsPropertySelectorType.FLAT
        else:
            return DCWEnvMagicSettingsPropertySelectorType.OBJECT

    def __selector_value_dict(self, env_name: str, env_value: str):
        prop_selector = self.__prop_selector_from_magic_env_name(env_name)
        prop_selector_type = self.__prop_selector_type_from_magic_env_name(
            env_name)
        prop_value = env_value.split(
            ',') if env_name.endswith('[]') else env_value

        if prop_selector_type == DCWEnvMagicSettingsPropertySelectorType.OBJECT:
            return dot_env_to_dict_rec(prop_selector, prop_value)
        elif prop_selector_type == DCWEnvMagicSettingsPropertySelectorType.FLAT:
            flat_key = prop_selector.split('.[')[1][:-1]
            ps_key = prop_selector.split('.[')[0]
            return dot_env_to_dict_rec(ps_key, prop_value, flat_key)

    def __match_selector(self, target: str, selector: str) -> bool:
        selector = selector.replace(
            DCWEnvMagicSettingsSelectorWildcard.ANY, '\\S+')
        regex = re.compile(rf'^{selector}$')
        return regex.match(target)

    def set_env(self, env_name: str, env_value: str):
        """Set an environment variable for this environment"""
        self.__env_vars[env_name] = env_value
        env_type = self.__type_from_magic_env_name(env_name)
        if env_type is None:
            self.global_envs[env_name] = env_value
        elif env_type == DCWEnvMagicSettingType.SERVICES:
            self.services = [s.strip() for s in env_value.split(',')]
        elif env_type == DCWEnvMagicSettingType.SERVICE_GROUPS:
            self.svc_groups = [s.strip() for s in env_value.split(',')]
        elif env_type == DCWEnvMagicSettingType.SERVICE_SELECTOR:
            selector = self.__selector_from_magic_env_name(env_name)
            if selector not in self.service_configs:
                self.service_configs[selector] = {}
            selector_value = self.__selector_value_dict(env_name, env_value)
            self.service_configs[selector] = deep_update(
                self.service_configs[selector], selector_value)
        elif env_type == DCWEnvMagicSettingType.SERVICE_GROUP_SELECTOR:
            selector = self.__selector_from_magic_env_name(env_name)
            if selector not in self.svc_group_configs:
                self.svc_group_configs[selector] = {}
            selector_value = self.__selector_value_dict(env_name, env_value)
            self.svc_group_configs[selector] = deep_update(
                self.svc_group_configs[selector], selector_value)

    def get_env(self, env_name: str):
        return self.__env_vars[env_name]

    def apply_on_service(self, service: DCWService) -> DCWService:
        svc_copy = copy.deepcopy(service)
        for svc_selector in self.service_configs:
            if self.__match_selector(svc_copy.name, svc_selector):
                svc_copy.apply_config(self.service_configs[svc_selector])
        for svc_group_selector in self.svc_group_configs:
            for svc_group in svc_copy.groups:
                if self.__match_selector(svc_group, svc_group_selector):
                    svc_copy.apply_config(
                        self.svc_group_configs[svc_group_selector])
        svc_copy.apply_global_env(self.global_envs)
        return svc_copy

    def as_dict(self):
        result = {
            **self.global_envs
        }

        if self.services:
            result[f'{DCWEnvMagicSettingType.SERVICES}'] = ','.join(
                self.services)
        if self.svc_groups:
            result[f'{DCWEnvMagicSettingType.SERVICE_GROUPS}'] = ','.join(
                self.svc_groups)

        for svc_name in self.service_configs:
            flattened = flatten_dict(self.service_configs[svc_name])
            for prop in flattened:
                prop_value = flattened[prop]
                result_key = f'{DCWEnvMagicSettingType.SERVICE_SELECTOR}{svc_name}.{prop}'
                if isinstance(prop_value, list):
                    prop_value = '.'.join(prop_value)
                    result_key += '[]'
                result[result_key] = prop_value

        for svc_group_name in self.svc_group_configs:
            flattened = flatten_dict(self.svc_group_configs[svc_group_name])
            for prop in flattened:
                prop_value = flattened[prop]
                result_key = f'{DCWEnvMagicSettingType.SERVICE_GROUP_SELECTOR}{svc_group_name}.{prop}'
                if isinstance(prop_value, list):
                    prop_value = '.'.join(prop_value)
                    result_key += '[]'
                result[result_key] = prop_value

        return result


def import_env_from_file(file_path: str) -> DCWEnv:
    file_name = os.path.basename(file_path)
    if not file_name.startswith('.') or not file_name.endswith('.env'):
        return None

    name = file_name[1:].split('.')[0]
    return DCWEnv(name, dotenv_values(file_path))


def import_envs_from_dir(dir_path: str) -> dict[str, DCWEnv]:
    envs = {}
    for file_name in os.listdir(dir_path):
        env = import_env_from_file(os.path.join(dir_path, file_name))
        if env is None:
            continue
        envs[env.name] = env
    return envs


def list_global_environment_variables(env: DCWEnv, all_svcs: dict[str, DCWService]) -> [str]:
    all_global_env_vars = set()

    for svc_name in env.services:
        if svc_name not in all_svcs:
            raise Exception(f'SERVICE {svc_name} DOES NOT EXIST!')
        all_global_env_vars.update(all_svcs[svc_name].get_global_envs())

    for group_name in env.svc_groups:
        svcs = filter(lambda s: group_name in s.groups,
                      [all_svcs[s] for s in all_svcs])
        for s in svcs:
            all_global_env_vars.update(s.get_global_envs())

    return all_global_env_vars
