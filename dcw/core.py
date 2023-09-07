import typing
import yaml
import subprocess
import re
import string

from config import TMP_DIR

# ----------------------------------
# DCW CORE
# ----------------------------------

class DCWService:
    """DCW Service represents a docker-compose service defined in a docker-compose.yml file"""

    def __init__(self, name: str, filename: str, config) -> None:
        self.name = name
        self.filename = filename
        self.config = config
        self.tmp_filename = f'{TMP_DIR}/{self.name}.yml'

        if self.name not in self.config['services']:
            raise Exception(f'Service ${filename} not valid!')

        self.save_tmp()

    def set_env_var(self, env_name: str, env_value: str):
        if not env_name.startswith(f'svc.{self.name}.environment.') and not env_name.startswith(
                f'svc.{self.name}.labels.'):
            return

        section = 'environment' if env_name.startswith(
            f'svc.{self.name}.environment.') else 'labels'

        print(section)

        env_name = env_name[len(f'svc.{self.name}.{section}.'):]

        if section not in self.config['services'][self.name]:
            self.config['services'][self.name][section] = {}

        self.config['services'][self.name][section][env_name] = env_value

    def set_env_vars(self, env_vars: typing.Dict[str, str]):
        for k in env_vars:
            self.set_env_var(k, env_vars[k])
        self.save_tmp()

    def save_tmp(self):
        with open(self.tmp_filename, 'w') as f:
            yaml.safe_dump(self.config, f)


class DCWEnv:
    def __init__(self, name, filename, env_vars) -> None:
        self.name = name
        self.filename = filename
        self.env_vars = {}
        self.svc_env_vars = {}
        self.tmp_filename = f'{TMP_DIR}/.{self.name}.env'

        for k in env_vars:
            if k.startswith('svc.'):
                self.svc_env_vars[k] = env_vars[k]
            else:
                self.env_vars[k] = env_vars[k]

        self.save_env_tmp()

    def save_env_tmp(self):
        with open(self.tmp_filename, 'w') as f:
            yaml.safe_dump(self.env_vars, f)

    def __str__(self) -> str:
        return f"DCWEnv(name={self.name}, filename={self.filename})"


class DCWUnit:
    def __init__(self, name, filename, services) -> None:
        self.name = name
        self.filename = filename
        self.services = services

    def __str__(self) -> str:
        return f"DCWUnit(name={self.name}, filename={self.filename}, services={self.services})"

    def render(self, dcw_env):
        dc_files = [f'-f {s.tmp_filename}' for s in self.services]
        dc_command = f"docker-compose {' '.join(dc_files)} --env-file {dcw_env.tmp_filename} convert"
        # logger.info(f"Running command: {dc_command}")
        for svc in self.services:
            svc.set_env_vars(dcw_env.svc_env_vars)
        # os.system(dc_command)
        result = subprocess.run(dc_command.split(
            ' '), capture_output=True, text=True)
        return yaml.safe_load(result.stdout)

    def save(self):
        with open(self.filename, 'w') as f:
            f.writelines([f'{s.name.strip()}\n' for s in self.services])


class DCWTemplate:
    def __init__(self, name, filename, content):
        self.name = name
        self.filename = filename
        self.content = content

    def render(self, env_vars):
        template = string.Template(self.content)
        var_names = self.get_variable_names()
        for vn in var_names:
            if vn not in env_vars:
                raise Exception(f'{vn} is not set!')

        return yaml.safe_load(template.substitute(**env_vars))

    def get_variable_names(self):
        placeholders = re.findall(r'[^$]\$\{([^}]*)\}', self.content)
        return list(set(placeholders))
