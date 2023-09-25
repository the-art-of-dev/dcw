import enum
from dcw.templates import template_env_vars, render_template
import yaml
import os
from dcw.environment import DCWEnv


class DCWServiceMagic(str, enum.Enum):
    UNITS = 'dcw.units'


class DCWService:
    """DCW Service represents a docker compose service defined in a docker-compose.yml file"""

    def __init__(self,
                 name: str,
                 config: dict = None) -> None:
        self.name = name
        self.units = []
        self.image = ''
        self.ports = []
        self.environment = {}
        self.labels = {}
        self.networks = []
        self.config = config if config is not None else {}
        self.__set_from_config()

    def __set_image_from_config(self):
        if 'image' in self.config:
            self.image = self.config['image']
            del self.config['image']

    def __set_ports_from_config(self):
        if 'ports' in self.config:
            self.ports = self.config['ports']
            del self.config['ports']

    def __set_environment_from_config(self):
        if 'environment' in self.config:
            if self.config['environment'] is list:
                for ev in self.config['environment']:
                    (env, val) = ev.split('=')
                    self.config[env] = val
            else:
                self.environment = self.config['environment']
            del self.config['environment']

    def __set_labels_from_config(self):
        if 'labels' in self.config:
            if self.config['labels'] is list:
                for lv in self.config['labels']:
                    (lbl, val) = lv.split('=')
                    self.config[lbl] = val
            else:
                self.labels = self.config['labels']
            del self.config['labels']

    def __set_networks_from_config(self):
        if 'networks' in self.config:
            self.networks = self.config['networks']
            del self.config['networks']

    def __set_units_from_label(self):
        if DCWServiceMagic.UNITS in self.labels:
            self.units = self.lables[DCWServiceMagic.UNITS]

    def __set_from_config(self):
        self.__set_image_from_config()
        self.__set_ports_from_config()
        self.__set_environment_from_config()
        self.__set_labels_from_config()
        self.__set_networks_from_config()
        self.__set_units_from_label()

    def __str__(self) -> str:
        return yaml.safe_dump(self.as_dict())

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, DCWService) and self.name == __value.name and self.as_dict() == __value.as_dict()

    def as_dict(self):
        return {
            'image': self.image,
            'ports': self.ports,
            'environment': self.environment,
            'labels': self.labels,
            'networks': self.networks,
            **self.config,
        }

    def apply_config(self, config: dict):
        """Apply a config to this service"""
        self.config = {
            **self.config,
            **config
        }
        self.__set_from_config()

    def get_global_envs(self):
        return template_env_vars(yaml.safe_dump(self.as_dict()))

    def apply_global_env(self, env_vars: dict):
        new_data = yaml.safe_load(render_template(
            yaml.safe_dump(self.as_dict()), env_vars))
        self.apply_config(new_data)

    def apply_environment(self, env: DCWEnv):
        self.apply_config(env.service_configs[self.name])
        self.apply_global_env(env.global_envs)


def import_service_from_file(file_path: str) -> DCWService:
    file_name = os.path.basename(file_path)
    if not file_name.startswith('docker-compose.') or not file_name.endswith('.yml'):
        return None

    name = file_name[len('docker-compose.'):].split('.')[0]

    with open(file_path) as f:
        x = next(iter(yaml.safe_load(f)['services'].values()))
        return DCWService(name, config=x)


def import_services_from_dir(dir_path: str) -> dict[str, DCWService]:
    svcs = {}
    for file_name in os.listdir(dir_path):
        svc = import_service_from_file(os.path.join(dir_path, file_name))
        if svc is not None:
            svcs[svc.name] = svc
    return svcs
