import os
import yaml
import subprocess
import re
import string
from typing import Dict
import enum
import copy
from abc import ABC, abstractmethod

from dcw.config import get_config
from dcw.logger import logger

# ----------------------------------
# DCW CORE
# ----------------------------------


class DCWObject(ABC):
    def __init__(self, name: str) -> None:
        self.name = name


class DCWEvent(object):
    def __init__(self):
        self.__eventhandlers = []

    def __iadd__(self, handler):
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

    def add_obj(self, svc: DCWObject):
        """Add a service to this service group overwriting any existing service with the same name"""
        self.objs[svc.name] = svc

    def remove_obj(self, svc_name: str):
        """Remove a service from this service group if it exists"""
        if svc_name in self.objs:
            del self.objs[svc_name]

    def get_obj(self, svc_name: str):
        """Get a service from this service group if it exists"""
        return copy.deepcopy(self.objs[svc_name]) if svc_name in self.objs else None

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, DCWGroup) and self.name == __value.name and self.objs == __value.objs


class DCWGroupIO(ABC):
    def __init__(self, id: str, group_path: str) -> None:
        self.id = id
        self.group_path = group_path

    @abstractmethod
    def import_group(self) -> DCWGroup:
        pass

    @abstractmethod
    def export_group(self, svc_group: DCWGroup) -> None:
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

    def import_group(self):
        self.group = self.group_io.import_group()
        self.svcs_group = self.__svc_group()
        self.envs_group = self.__envs_group()
        self.units_group = self.__units_group()

    def export_group(self):
        self.group_io.export_group(self.group)

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


class DCWProcessState(str, enum.Enum):
    CREATED = "created",
    QUEUED = "queued",
    RUNNING = "running",
    FINISHED = "finished",
    FAILED = "failed"


class DCWProcess:
    def __init__(self, name: str, data_context: DCWDataContext = None) -> None:
        self.name = name
        self.data_context = data_context
        self.state = DCWProcessState.CREATED
        self.__on_queued = DCWEvent()
        self.__on_running = DCWEvent()
        self.__on_finished = DCWEvent()
        self.__on_failed = DCWEvent()

    def on_queued(self, handler):
        self.__on_queued += handler

    def remove_on_queued(self, handler):
        self.__on_queued -= handler

    def on_running(self, handler):
        self.__on_running += handler

    def remove_on_running(self, handler):
        self.__on_running -= handler

    def on_finished(self, handler):
        self.__on_finished += handler

    def remove_on_finished(self, handler):
        self.__on_finished -= handler

    def on_failed(self, handler):
        self.__on_failed += handler

    def remove_on_failed(self, handler):
        self.__on_failed -= handler

    def quee(self):
        self.state = DCWProcessState.QUEUED
        self.__on_queued(self)

    def run(self):
        self.state = DCWProcessState.RUNNING
        self.__on_running(self)

    def finish(self):
        self.state = DCWProcessState.FINISHED
        self.__on_finished(self)

    def fail(self):
        self.state = DCWProcessState.FAILED
        self.__on_failed(self)


class DCWProcessingQueue:
    def __init__(self, data_context: DCWDataContext) -> None:
        self.__data_context = data_context
        self.__processes = []

    def add_process(self, process: DCWProcess):
        process.data_context = self.__data_context
        self.__processes.append(process)
        process.quee()
        self.__data_context = process.data_context

    def remove_process(self, process: DCWProcess):
        self.__processes.remove(process)

    def run(self):
        for p in self.__processes:
            p.data_context = self.__data_context
            try:
                p.run()
                p.finish()
                self.__data_context = p.data_context
            except Exception as e:
                p.fail()
                self.__data_context = p.data_context
                return
  