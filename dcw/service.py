# pylint: skip-file
import enum
from dcw.utils import template_env_vars, render_template
import yaml
import os
from dcw.utils import deep_update
from dataclasses import dataclass


class DCWServiceMagicLabels(str, enum.Enum):
    GROUPS = 'dcw.svc_groups'


class DCWService:
    """DCW Service represents a docker service defined in a docker-compose.yml file"""

    def __init__(self,
                 name: str,
                 config: dict = None) -> None:
        self.name = name
        self.groups: [str] = []
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

    def __set_ports_from_config(self):
        if 'ports' in self.config:
            self.ports = self.config['ports']

    def __set_environment_from_config(self):
        if 'environment' in self.config:
            if self.config['environment'] is list:
                for ev in self.config['environment']:
                    (env, val) = ev.split('=')
                    self.config[env] = val
            else:
                self.environment = self.config['environment']

    def __set_labels_from_config(self):
        if 'labels' not in self.config:
            self.config['labels'] = {}
        if isinstance(self.config['labels'], list):
            for lv in self.config['labels']:
                (lbl, val) = lv.split('=')
                self.labels[lbl] = val

            self.config['labels'] = self.labels
        else:
            self.labels = self.config['labels']

    def __set_networks_from_config(self):
        if 'networks' in self.config:
            self.networks = self.config['networks']

    def __set_groups_from_label(self):
        if DCWServiceMagicLabels.GROUPS in self.labels:
            self.groups = self.labels[DCWServiceMagicLabels.GROUPS].split(',')

    def __set_from_config(self):
        self.__set_image_from_config()
        self.__set_ports_from_config()
        self.__set_environment_from_config()
        self.__set_labels_from_config()
        self.__set_networks_from_config()
        self.__set_groups_from_label()

    def __str__(self) -> str:
        return yaml.safe_dump(self.as_dict())

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, DCWService) and self.name == __value.name and self.as_dict() == __value.as_dict()

    def as_dict(self):
        return {
            **self.config,
        }

    def apply_config(self, config: dict):
        """Apply a config to this service"""
        self.config = deep_update(self.config, config)
        self.__set_from_config()

    def get_global_envs(self):
        return template_env_vars(yaml.safe_dump(self.as_dict()))

    def apply_global_env(self, env_vars: dict):
        for ev in self.get_global_envs():
            if ev not in env_vars:
                raise Exception(
                    f'GLOBAL ENVIRONMENT VARIABLE "{ev}" NOT SATISFIED')
        new_data = yaml.safe_load(render_template(
            yaml.safe_dump(self.as_dict()), env_vars))
        self.apply_config(new_data)


@dataclass
class ServiceGroup:
    name: str
    services: [str]


def map_service_groups(svcs: dict[str, DCWService]) -> dict[str, ServiceGroup]:
    svc_groups_map: dict[str, ServiceGroup] = {}
    for sn in svcs:
        for sg in svcs[sn].groups:
            if sg not in svc_groups_map:
                svc_groups_map[sg] = ServiceGroup(sg, [])
            svc_groups_map[sg].services.append(sn)

    return svc_groups_map


def import_services_from_file(file_path: str) -> dict[str, DCWService]:
    file_name = os.path.basename(file_path)
    if not file_name.startswith('docker-compose.') or not file_name.endswith('.yml'):
        return None

    services = {}

    with open(file_path) as f:
        dc_files = yaml.safe_load_all(f)
        for file in dc_files:
            file_svcs = file['services']
            for svc_name in file_svcs:
                services[svc_name] = DCWService(
                    svc_name, config=file_svcs[svc_name])

    return services


def import_services_from_dir(dir_path: str) -> dict[str, DCWService]:
    services = {}
    for file_name in os.listdir(dir_path):
        file_svcs = import_services_from_file(
            os.path.join(dir_path, file_name))
        for svc in file_svcs:
            services[svc] = file_svcs[svc]
    return services
