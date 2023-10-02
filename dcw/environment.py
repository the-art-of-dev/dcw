import enum
import os
import io
from dotenv import dotenv_values


class DCWEnvVariableType(str, enum.Enum):
    GLOBAL = "global",
    SERVICE = "service"


class DCWEnv:
    def __init__(self, name: str, env_vars: dict = None) -> None:
        self.name = name
        if env_vars is None:
            env_vars = {}
        self.global_envs = {}
        self.service_configs = {}

        for k, v in env_vars.items():
            self.set_env(k, v)

    def __type_of_env(self, env_name: str):
        if env_name.startswith('svc.'):
            return DCWEnvVariableType.SERVICE
        else:
            return DCWEnvVariableType.GLOBAL

    def __svc_name_from_env(self, env_name: str):
        if self.__type_of_env(env_name) == DCWEnvVariableType.SERVICE:
            return env_name.split('.')[1]
        else:
            return None

    def __svc_key_from_env(self, env_name: str):
        if self.__type_of_env(env_name) == DCWEnvVariableType.SERVICE:
            return env_name.split('.')[2]
        else:
            return None

    def __get_env_name(self, env_name: str):
        if self.__type_of_env(env_name) == DCWEnvVariableType.SERVICE:
            return '.'.join(env_name.split('.')[3:])
        else:
            return env_name

    def set_env(self, env_name: str, env_value: str):
        """Set an environment variable for this environment"""
        if self.__type_of_env(env_name) == DCWEnvVariableType.SERVICE:
            svc_name = self.__svc_name_from_env(env_name)
            svc_key = self.__svc_key_from_env(env_name)
            svc_env_name = self.__get_env_name(env_name)

            if svc_name not in self.service_configs:
                self.service_configs[svc_name] = {}

            if svc_env_name == '__set':
                self.service_configs[svc_name][svc_key] = env_value
            elif svc_env_name == '__setarr':
                self.service_configs[svc_name][svc_key] = env_value.split(',')
            else:
                if svc_key not in self.service_configs[svc_name] or self.service_configs[svc_name][svc_key] is None:
                    self.service_configs[svc_name][svc_key] = {}
                self.service_configs[svc_name][svc_key][svc_env_name] = env_value
        else:
            self.global_envs[env_name] = env_value

    def as_dict(self):
        result = {
            **self.global_envs
        }
        for svc_name in self.service_configs:
            for svc_key in self.service_configs[svc_name]:
                if isinstance(self.service_configs[svc_name][svc_key], dict):
                    for svc_env_name in self.service_configs[svc_name][svc_key]:
                        result[f'svc.{svc_name}.{svc_key}.{svc_env_name}'] = self.service_configs[svc_name][svc_key][svc_env_name]
                elif isinstance(self.service_configs[svc_name][svc_key], list):
                    result[f'svc.{svc_name}.{svc_key}.__setarr'] = ','.join(
                        self.service_configs[svc_name][svc_key])
                else:
                    result[f'svc.{svc_name}.{svc_key}.__set'] = self.service_configs[svc_name][svc_key]
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


def export_env_to_dir(dir_path: str, env: DCWEnv):
    env_file_path = os.path.join(dir_path, f".{env.name}.env")
    with open(env_file_path, "w") as f:
        f.write(dump_env(env))


def load_env(name: str, str_data: str) -> DCWEnv:
    return DCWEnv(name, dotenv_values(stream=io.StringIO(str_data)))


def dump_env(env: DCWEnv) -> str:
    env_data = env.as_dict()
    str_env_data = ""
    for k in env_data:
        str_env_data += f"{k}={env_data[k]}\n"
    return str_env_data
