# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import os
from typing import Callable, List

import yaml

from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.stdmods.services import DcwService
from dcw.envy import EnvyCmd, EnvyState, dict_to_envy, prepand_selector
from pprint import pprint as pp
from dcw.utils import check_for_missing_args, is_false, value_map_dataclass as vm_dc, raise_if
from dcw.logger import logger as lgg

# --------------------------------------
#   Procedures
# --------------------------------------
# region
'''Dcw Procedures - handles DCW procedure automation'''
NAME = name = 'procs'
SELECTOR = selector = ['procs']


@dataclass
class DcwProcedure:
    desc: str = ''
    name: str = ''
    cmd: str = ''
    module: str = ''
    is_active: str = ''
    tasks: List[DcwProcedure] = field(default_factory=dict)
    args: dict = field(default_factory=dict)
    _: dict = field(default_factory=dict)


def not_found_ex(name: str) -> Exception:
    return Exception(f'Procedure {name} not found.')


def run_proc(s: dict, proc: DcwProcedure, run: Callable) -> List[EnvyCmd]:
    lgg.info(f'Running - {proc.desc}')
    envy_cfg = dcw_envy_cfg()
    state = EnvyState(s, envy_cfg)
    out_ecl = []

    if is_false(state[proc.is_active]):
        return out_ecl

    if proc.module != '' and proc.cmd != '':
        diff_ecl = run(proc.module, proc.cmd, proc.args)
        out_ecl += diff_ecl
        state += diff_ecl

    for task in proc.tasks:
        diff_ecl = run_proc(state.state, task, run)
        out_ecl += diff_ecl
        state += diff_ecl

    return out_ecl


def dict_to_proc(d: dict) -> DcwProcedure:
    if not isinstance(d, dict):
        return None
    return DcwProcedure(
        desc=d.get('desc', ''),
        name=d.get('name', ''),
        args=d.get('args', {}),
        cmd=d.get('cmd', ''),
        module=d.get('module', ''),
        is_active=d.get('is_active', ''),
        tasks=[dict_to_proc(t) for t in d.get('tasks', [])]
    )


def load_proc_from_yml(filepath: str) -> DcwProcedure:
    proc_cfg = None

    with open(filepath) as f:
        proc_cfg = yaml.safe_load(f)
    proc = DcwProcedure(name=os.path.basename(filepath).split('.')[0])
    if isinstance(proc_cfg, list):
        proc.tasks = [dict_to_proc(t) for t in proc_cfg]
    elif isinstance(proc_cfg, dict):
        proc = dict_to_proc(proc_cfg)
    else:
        raise Exception(f'File {filepath} is not a DCW Procedure')

    return proc


@dcw_cmd()
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state = EnvyState(s, dcw_envy_cfg()) + run('proj', 'load')
    proj_root = state['proj.root']
    procs_root = state['proj.cfg.procs_root']
    procs_path = os.path.join(proj_root, procs_root)
    diff = EnvyState({}, dcw_envy_cfg())
    for file_name in os.listdir(procs_path):
        fn: str = os.path.basename(file_name)
        if fn.endswith('.yml') or fn.endswith('.yaml'):
            p = load_proc_from_yml(os.path.join(procs_path, file_name))
            diff[p.name] = asdict(p)
    return dict_to_envy(diff.state)


@dcw_cmd({'name': ...})
def cmd_run(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    proc_name = args['name']
    envy_cfg = dcw_envy_cfg()
    state: EnvyState = EnvyState(s, envy_cfg) + run(NAME, 'load')
    proc: DcwProcedure = state[f'procs.{proc_name}', raise_if(not_found_ex(proc_name), dict_to_proc)]
    return prepand_selector(run_proc(state.state, proc, run), ['runs'])


@dcw_cmd({'name': ..., 'depl_name': ''})
def cmd_build_svc(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    svc_name = args['name']
    depl_name = args['depl_name']
    envy_cfg = dcw_envy_cfg()
    
    state: EnvyState = EnvyState(s, envy_cfg)
    state += run(NAME, 'load')
    state += run('svcs', 'load')
    state += run('depls', 'load')

    svc: DcwService = None
    if is_false(depl_name):
        svc = state[f'svcs.{svc_name}', vm_dc(DcwService)]
    else:
        svc = state[f'depls.{depl_name}.svcs.{svc_name}', vm_dc(DcwService)]
    

    proc_name = svc.builder_cfg().cfg.get('name', None)
    if proc_name is None:
        raise Exception(f'Procedure name not found for building service {svc_name} in deploymet {depl_name}')
    
    return cmd_run(asdict(s), {'name': proc_name}, run)

# endregion
