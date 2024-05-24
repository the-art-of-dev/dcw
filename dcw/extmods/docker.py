# pylint: skip-file
from __future__ import annotations
import copy
from dataclasses import asdict
import os
from typing import Callable, List

import yaml
from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, apply_cmd_log, dict_to_envy, get_selector_val, EnvyState
from dcw.stdmods.deployments import DcwDeployment
from dcw.stdmods.regs import DcwRegistry
from dcw.stdmods.services import DcwService
from pprint import pprint as pp
from dcw.utils import check_for_missing_args, is_false, value_map_dataclass as vm_dc
from old.dcw.utils import flatten
import docker

# --------------------------------------
#   Docker
# --------------------------------------
# region
__doc__ = '''Docker - integration with docker'''
NAME = name = 'docker'
NAME = selector = ['docker']


@dcw_cmd({'name': ..., 'depl_name': ''})
def cmd_build_svc(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    svc_name = args['name']
    depl_name = args['depl_name']
    state = EnvyState(s, dcw_envy_cfg()) + run('svcs', 'load') + run('depls', 'load')
    
    svc: DcwService = None
    if is_false(depl_name):
        svc = state[f'svcs.{svc_name}', vm_dc(DcwService)]
    else:
        svc = state[f'depls.{depl_name}.svcs.{svc_name}', vm_dc(DcwService)]
    
    build_cfg = svc.builder_cfg()
    docker_cli = docker.from_env(environment=build_cfg.environment)
    build_args = {
        'tag': svc.image,
        **build_cfg.cfg
    }
    docker_cli.images.build(**build_args)
    return []


def reg_login(reg: DcwRegistry) -> bool:
    try:
        client = docker.from_env()
        client.login(username=reg.username, password=reg.password, registry=reg.url)
        return True
    except docker.errors.APIError as e:
        print(f"Failed to login: {e}")
        return False


@dcw_cmd({'name': ...})
def cmd_install_reg(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    reg_name = args['name']
    state = EnvyState(s, dcw_envy_cfg()) + run('regs', 'load')

    reg: DcwRegistry = state[f'regs.{reg_name}', vm_dc(DcwRegistry)]
    reg_login(reg)

    return []

# endregion
