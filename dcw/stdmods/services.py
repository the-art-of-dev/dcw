# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import os
from typing import Callable, List

import yaml
from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, apply_cmd_log, dict_to_envy, get_selector_val, str_to_envy, EnvyState
from pprint import pprint as pp
from dcw.utils import check_for_missing_args, raise_if, value_map_dataclass as vm_dc, value_map_dict


# --------------------------------------
#   Services
# --------------------------------------
# region
__doc__ = '''Dcw Services - source of services'''
NAME = name = 'svcs'
SELECTOR = selector = ['svcs']


@dataclass
class DcwServiceBuilderConfig:
    type: str
    environment: dict = None
    cfg: dict = field(default_factory=dict)


class DcwService:
    def __init__(self,
                 name: str,
                 image: str = '',
                 version: str = '',
                 ports: List[str] = None,
                 environment: dict = None,
                 labels: dict = None,
                 networks: List[str] = None,
                 volumes: List[str] = None,
                 extra_hosts: List[tuple[str, str]] = None) -> None:
        self.name = name
        self.image = image
        self.version = version
        self.ports = ports if ports != None else []
        self.environment = environment if environment != None else {}
        self.labels = labels if labels != None else {}
        self.networks = networks if networks != None else []
        self.volumes = volumes if volumes != None else []
        self.extra_hosts = extra_hosts if extra_hosts != None else []

    def groups(self) -> List[str]:
        cfg = dcw_envy_cfg()
        cfg.default_op = '_'
        s = EnvyState({}, cfg)
        s += str_to_envy(self.labels_envy_str(), cfg)
        gs = s['groups']
        if gs is None:
            return []
        return gs

    def builder_cfg(self) -> DcwServiceBuilderConfig:
        cfg = dcw_envy_cfg()
        cfg.default_op = '_'
        s = EnvyState({}, cfg)
        s += str_to_envy(self.labels_envy_str(), cfg)
        bcfg_dict = s['builder']
        return DcwServiceBuilderConfig(**bcfg_dict) if bcfg_dict != None else None

    def labels_envy_str(self) -> str:
        envy_str = []
        for ln, lv in self.labels.items():
            envy_str.append(f'{ln}={lv}')
        return '\n'.join(envy_str)


@dcw_cmd({'loader': 'docker_compose'})
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['loader'])
    loader_mod = args['loader']
    state: EnvyState = EnvyState(s, dcw_envy_cfg()) + run(loader_mod, 'load', args)
    svcs: dict[str, DcwService] = state[loader_mod, value_map_dict(str, DcwService)]

    out_ecl = []

    for svc in svcs.values():
        if svc.groups() == []:
            out_ecl += dict_to_envy({svc.name: svc.__dict__})
            continue
        for g in svc.groups():
            new_name = f'{g}-{svc.name}'
            out_ecl += dict_to_envy({new_name: {**svc.__dict__, 'name': new_name}})
    return out_ecl


@dcw_cmd({'name': ...})
def cmd_build(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    svc_name = args['name']
    state: EnvyState = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')

    map_svc = raise_if(Exception(f'Service {svc_name} not found.'), vm_dc(DcwService))
    svc: DcwService = state[f'svcs.{svc_name}', map_svc]

    builder_cfg = svc.builder_cfg()

    if builder_cfg is None:
        raise Exception(f'Build config for service {svc.name}, not found.')

    return run(builder_cfg.type, 'build_svc', {**args, **builder_cfg.cfg})


@dcw_cmd()
def cmd_list(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')
    pp(state['svcs'])
    return []

# endregion
