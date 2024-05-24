# pylint: skip-file
from __future__ import annotations
import copy
from dataclasses import asdict
import os
from typing import Callable, List

import yaml
from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, EnvyState, apply_cmd_log, dict_to_envy, get_selector_val
from dcw.stdmods.deployments import DcwDeployment
from dcw.stdmods.services import DcwService
from pprint import pprint as pp
from dcw.utils import check_for_missing_args, value_map_dataclass
from old.dcw.utils import flatten
import docker

# --------------------------------------
#   DCW procedures
# --------------------------------------
# region
__doc__ = '''Dcw procedures - integration with dcw procedures'''
name = 'dcw_procs'
selector = ['dcw_procs']


@dcw_cmd({'name': ...})
def cmd_build(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    state = EnvyState(s, dcw_envy_cfg()) + run('svcs', 'load')

    svc: DcwService = state[f'svcs.{args['name']}', value_map_dataclass(DcwService)]
    s = apply_cmd_log(s, run('svcs', 'load'), dcw_envy_cfg())
    svc: DcwService = get_selector_val(s, ['svcs', args['name']], value_map_dataclass(DcwService))
    b_cfg = svc.builder_cfg()
    d_cli = docker.from_env(environment=b_cfg.environment)
    b_args = {
        'tag': svc.image,
        **b_cfg.cfg
    }
    d_cli.images.build(**b_args)
    return []

# endregion
