import os
import yaml
import subprocess
import re
import string
from typing import Any, Dict
import enum
import copy
from abc import ABC, abstractmethod

from dcw.config import get_config
from dcw.logger import logger
from pprint import pprint as pp
from dcw.utils import template_env_vars

# ----------------------------------
# DCW CORE
# ----------------------------------


class DockerComposeWrapper:
    def __init__(self, text: str) -> None:
        self.text = str
        self.config = yaml.safe_load(self.text)

    def validate(self):
        pass

class DCWService():
    def __init__(self) -> None:
        self.deployment_type = None
        self.build_type = None
        self.migration_type = None
        self.wrapper = DockerComposeWrapper()
    
    def deploy():
        pass
    
    def revert():
        pass

    def build():
        pass        


class DCWObject(ABC):
    def __init__(self, name: str) -> None:
        self.name = name


class DCWEvent(object):
    def __init__(self, name: str = None) -> None:
        self.__name = name
        self.__eventhandlers = []

    def __iadd__(self, handler):
        if isinstance(handler, DCWEvent):
            self.__eventhandlers.extend(handler.__eventhandlers)
        else:
            self.__eventhandlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__eventhandlers.remove(handler)
        return self

    def __call__(self, *args, **keywargs):
        for eventhandler in self.__eventhandlers:
            eventhandler(*args, **keywargs)


class DCWGroup:
    def __init__(self, name: str, objs: [DCWObject] = None) -> None:
        self.name = name
        self.objs = {s.name: s for s in objs} if objs is not None else {}
        self.__objs_iterable = []

    def add_obj(self, svc: DCWObject):
        """Add a object to this object group overwriting any existing object with the same name"""
        self.objs[svc.name] = svc

    def remove_obj(self, svc_name: str):
        """Remove a object from this object group if it exists"""
        if svc_name in self.objs:
            del self.objs[svc_name]

    def get_obj(self, svc_name: str):
        """Get a object from this object group if it exists"""
        return copy.deepcopy(self.objs[svc_name]) if svc_name in self.objs else None

    def __objs(self):
        return [self.get_obj(s) for s in self.objs.keys()]

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, DCWGroup) and self.name == __value.name and self.objs == __value.objs

    def __iter__(self):
        self.__objs_iterable = self.__objs()
        return iter(self.__objs_iterable)

    def __next__(self):
        return next(self.__objs_iterable)

    def __getitem__(self, key):
        return self.get_obj(key)

    def __iadd__(self, obj):
        if obj is None:
            return self
        elif isinstance(obj, DCWObject):
            self.add_obj(obj)
        elif isinstance(obj, DCWGroup):
            for o in obj:
                self.add_obj(o)
        return self

    def __isub__(self, obj):
        if obj is None:
            return self
        elif isinstance(obj, DCWObject):
            self.remove_obj(obj.name)
        elif isinstance(obj, DCWGroup):
            for o in obj:
                self.remove_obj(o.name)
        return self

    def __len__(self):
        return len(self.objs)


class DCWGroupIO(ABC):
    def __init__(self, id: str, group_root_path: str) -> None:
        self.id = id
        self.group_root_path = group_root_path

    @abstractmethod
    def import_group(self) -> DCWGroup:
        pass


class DCWService(DCWObject):
    """DCW Service represents a docker-compose service defined in a docker-compose.yml file"""

    def __init__(self,
                 name: str,
                 image: str = None,
                 ports: [str] = None,
                 environment: Dict = None,
                 labels: Dict = None,
                 networks: [str] = None,
                 config: Dict = None) -> None:
        super().__init__(name)
        self.image = image if image is not None else name
        self.ports = ports if ports is not None else []
        self.environment = environment if environment is not None else {}
        self.labels = labels if labels is not None else {}
        self.networks = networks if networks is not None else []
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
            self.environment = self.config['environment']
            del self.config['environment']

    def __set_labels_from_config(self):
        if 'labels' in self.config:
            self.labels = self.config['labels']
            del self.config['labels']

    def __set_networks_from_config(self):
        if 'networks' in self.config:
            self.networks = self.config['networks']
            del self.config['networks']

    def __set_from_config(self):
        self.__set_image_from_config()
        self.__set_ports_from_config()
        self.__set_environment_from_config()
        self.__set_labels_from_config()
        self.__set_networks_from_config()

    def as_dict(self):
        return {
            'image': self.image,
            'ports': self.ports,
            'environment': self.environment,
            'labels': self.labels,
            'networks': self.networks,
            **self.config,
        }

    def set_env(self, env_name: str, env_value: str):
        """Set an environment variable for this service"""
        self.environment[env_name] = env_value

    def get_env(self, env_name: str):
        """Get an environment variable for this service"""
        return self.environment[env_name]

    def set_label(self, lbl_name: str, lbl_value: str):
        """Set a label for this service"""
        self.labels[lbl_name] = lbl_value

    def get_label(self, lbl_name: str):
        """Get a label for this service"""
        return self.labels[lbl_name]

    def add_port(self, port: str):
        """Add a port for this service"""
        if port not in self.ports:
            self.ports.append(port)

    def add_network(self, network: str):
        """Add a network for this service"""
        if network not in self.networks:
            self.networks.append(network)

    def apply_config(self, config: Dict):
        """Apply a config to this service"""
        self.config = {
            **self.config,
            **config
        }
        self.__set_from_config()

    def get_global_envs(self):
        data = self.as_dict()
        all_envs = []
        # template_env_vars
        queue = [data]

        while len(queue) > 0:
            d = queue.pop(0)
            for k in d:
                if isinstance(d[k], str):
                    all_envs.extend(template_env_vars(d[k]))
                elif isinstance(d[k], list):
                    for v in d[k]:
                        if isinstance(v, str):
                            all_envs.extend(template_env_vars(v))
                        if isinstance(v, dict):
                            queue.append(v)
                elif isinstance(d[k], dict):
                    queue.append(d[k])

        return all_envs

    def apply_global_env(self, env_vars: dict):
        data = self.as_dict()
        pp(self.get_global_envs())
        print('---------------------')

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, DCWService) and self.name == __value.name and self.as_dict() == __value.as_dict()


class DCWEnvVariableType(str, enum.Enum):
    GLOBAL = "global",
    SERVICE = "service"


class DCWEnv(DCWObject):
    @staticmethod
    def type_of_env(env_name: str):
        '''Returns the type of dcw environment variable'''
        if env_name.startswith('svc.'):
            return DCWEnvVariableType.SERVICE
        else:
            return DCWEnvVariableType.GLOBAL

    @staticmethod
    def svc_name_from_env(env_name: str):
        '''Returns the service name from a dcw environment variable'''
        if DCWEnv.type_of_env(env_name) == DCWEnvVariableType.SERVICE:
            return env_name.split('.')[1]
        else:
            return None

    @staticmethod
    def svc_key_from_env(env_name: str):
        '''Returns the service config key from a dcw environment variable'''
        if DCWEnv.type_of_env(env_name) == DCWEnvVariableType.SERVICE:
            return env_name.split('.')[2]
        else:
            return None

    @staticmethod
    def get_env_name(env_name: str):
        '''Returns the environment variable name from a dcw environment variable'''
        if DCWEnv.type_of_env(env_name) == DCWEnvVariableType.SERVICE:
            return '.'.join(env_name.split('.')[3:])
        else:
            return env_name

    def __init__(self, name: str, env_vars: Dict = None) -> None:
        super().__init__(name)
        if env_vars is None:
            env_vars = {}
        self.global_envs = {}
        self.service_configs = {}
        self.__allowed_svc_config_keys = ['environment', 'labels']

        for k, v in env_vars.items():
            self.set_env(k, v)

    def get_env(self, env_name: str):
        """Get an environment variable for this environment"""
        if DCWEnv.type_of_env(env_name) == DCWEnvVariableType.SERVICE:
            svc_name = DCWEnv.svc_name_from_env(env_name)
            svc_key = DCWEnv.svc_key_from_env(env_name)
            svc_env_name = DCWEnv.get_env_name(env_name)
            return self.service_configs[svc_name][svc_key][svc_env_name]

        return self.global_envs[env_name]

    def set_env(self, env_name: str, env_value: str):
        """Set an environment variable for this environment"""
        if DCWEnv.type_of_env(env_name) == DCWEnvVariableType.SERVICE:
            svc_name = DCWEnv.svc_name_from_env(env_name)
            svc_key = DCWEnv.svc_key_from_env(env_name)
            svc_env_name = DCWEnv.get_env_name(env_name)

            if svc_name not in self.service_configs:
                self.service_configs[svc_name] = {}

            if svc_key not in self.__allowed_svc_config_keys:
                raise Exception(
                    f'Invalid service config key {svc_key} for service {svc_name}')

            if svc_key not in self.service_configs[svc_name]:
                self.service_configs[svc_name][svc_key] = {}

            self.service_configs[svc_name][svc_key][svc_env_name] = env_value
        else:
            self.global_envs[env_name] = env_value


class DCWUnit(DCWObject):
    def __init__(self, name: str, svc_names: [str] = None) -> None:
        super().__init__(name)
        self.svc_names = svc_names if svc_names is not None else []

    def add_svc(self, svc_name: str):
        """Add a service to this unit"""
        if svc_name not in self.svc_names:
            self.svc_names.append(svc_name)

    def remove_svc(self, svc_name: str):
        """Remove a service from this unit"""
        if svc_name in self.svc_names:
            self.svc_names.remove(svc_name)

    def apply_env(self, env: DCWEnv, svc_group: DCWGroup) -> Dict[str, DCWService]:
        """Apply an environment to this unit"""
        svcs = {}
        for svc_name in self.svc_names:
            svc = svc_group.get_obj(svc_name)
            if svc is None:
                raise Exception(
                    f'Service {svc_name} not found in service group {svc_group.name}')
            for k, v in env.service_configs[svc_name].items():
                svc.apply_config({k: v})
            svcs[svc_name] = svc
        return svcs


class DCWDeployment(DCWObject):
    def __init__(self, name: str, deployment_pairs: [(str, str)]) -> None:
        super().__init__(name)
        self.deployment_pairs = deployment_pairs

class DCWMigration():
    def __init__(self, name, type) -> None:
        pass
    
class DCWDeploymentConfig():
    def __init__(self) -> None:
        pass


class DCWTemplateType(str, enum.Enum):
    SVC = "svc",
    ENV = "env",
    UNIT = "unit"


class DCWTemplate:
    '''DCW Template represents a text template that can be rendered with environment variables'''

    def __init__(self, name: str, type: DCWTemplateType, text: str):
        self.name = name
        self.type = type
        self.text = text

    def render(self, env_vars: Dict[str, str]):
        template = string.Template(self.text)
        var_names = self.all_vars()
        for vn in var_names:
            if vn not in env_vars:
                raise Exception(f'{vn} is not set!')

        return template.substitute(**env_vars)

    def all_vars(self):
        placeholders = re.findall(r'[^$]\$\{([^}]*)\}', self.text)
        return list(set(placeholders))


class DCWDataContext:
    def __init__(self, group_io: DCWGroupIO) -> None:
        if group_io is None:
            raise Exception('group_io is required')
        self.group = None
        self.svcs_group = None
        self.envs_group = None
        self.units_group = None
        self.group_io = group_io
        self.data = {}

    def import_group(self):
        self.group = self.group_io.import_group()
        self.svcs_group = self.__svc_group()
        self.envs_group = self.__envs_group()
        self.units_group = self.__units_group()

    def __svc_group(self):
        svcs = [o if isinstance(o, DCWService)
                else None for o in self.group.objs.values()]
        return DCWGroup('svc', objs=filter(lambda x: x is not None, svcs))

    def __envs_group(self):
        envs = [o if isinstance(o, DCWEnv)
                else None for o in self.group.objs.values()]
        return DCWGroup('svc', objs=filter(lambda x: x is not None, envs))

    def __units_group(self):
        units = [o if isinstance(o, DCWUnit)
                 else None for o in self.group.objs.values()]
        return DCWGroup('svc', objs=filter(lambda x: x is not None, units))

    def __setitem__(self, __name: str, __value: Any) -> None:
        self.data[__name] = __value

    def __getitem__(self, __name: str) -> Any:
        return self.data[__name]
