# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import os
from typing import Callable, List

import docker
import yaml
from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, apply_cmd_log, get_selector_val, dict_to_envy
from dcw.utils import check_for_missing_args, value_map_dict
from pprint import pprint as pp

# --------------------------------------
#   Artefact Registry
# --------------------------------------
# region
__doc__ = 'Dcw Tasks - handles DCW code repositories'
NAME = name = 'artf_regs'
SELECTOR = selector = ['artf_regs']


@dataclass
class DcwArtefactRegistry:
    name: str
    type: str
    url: str
    username: str
    password: str
    cfg: dict = field(default_factory=dict)


@dcw_cmd()
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    s = apply_cmd_log(s, run('proj', 'load'), dcw_envy_cfg())
    pp(s)
    artf_regs_cfg: dict[str, dict] = get_selector_val(s, ['proj', 'cfg', 'artf_regs'])
    return dict_to_envy({n: asdict(DcwArtefactRegistry(**{'name': n, **ar})) for n, ar in artf_regs_cfg.items()})


def find_artf_reg(s: dict, name: str, run: Callable) -> DcwArtefactRegistry:
    cl = run('proj', 'load') + run('artf_reg', 'load')
    s = apply_cmd_log(s, cl, dcw_envy_cfg())
    artf_regs: dict[str, DcwArtefactRegistry] = get_selector_val(
        s, ['artf_regs'], value_map_dict(str, DcwArtefactRegistry))
    if name not in artf_regs:
        raise Exception(f'Artefact Registry with name {name} not found!')
    return artf_regs[name]


def artf_reg_login(artf_reg: DcwArtefactRegistry) -> bool:
    try:
        client = docker.from_env()
        client.login(username=artf_reg.username, password=artf_reg.password, registry=artf_reg.url)
        return True
    except docker.errors.APIError as e:
        print(f"Failed to login: {e}")
        return False


@dcw_cmd({'name': ...})
def cmd_login(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    ar = find_artf_reg(s, args['name'], run)
    if not artf_reg_login(ar):
        raise Exception(f'Error while loggin into artefact registry {ar.name}')
    return []


# endregion
