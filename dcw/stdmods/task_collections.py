# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import os
from typing import Callable, List

from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, EnvyState, apply_cmd_log, dict_to_envy, get_selector_val
from pprint import pprint as pp
from invoke.tasks import task
from invoke.program import Program
from dcw.utils import check_for_missing_args, value_map_dict, value_map_list

# --------------------------------------
#   Task Collections
# --------------------------------------
# region
__doc__ = '''Dcw Task Collections - source of tasks'''
NAME = name = 'task_c'
SELECTOR = selector = ['task_c']

dcw_task = task


@dataclass
class DcwTaskCollection:
    tasks_root: str                                       # root path that contains module
    tasks_module: str                                     # module that contains tasks
    task_names: List[str] = field(default_factory=list)   # list of task names in collection


def load_task_c_module(tasks_root: str, tasks_module: str) -> DcwTaskCollection:
    inv_prg = Program()
    inv_prg.create_config()
    inv_prg.parse_core(['x', '--search-root', tasks_root, '-c', tasks_module])
    inv_prg.parse_collection()
    pairs = inv_prg._make_pairs(inv_prg.scoped_collection)
    return DcwTaskCollection(
        tasks_root,
        tasks_module,
        [x[0] for x in pairs]
    )


@dcw_cmd()
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state = EnvyState(s, dcw_envy_cfg()) + run('proj', 'load')
    if state['proj.cfg.task_c'] is None:
        return []

    diff = []
    for tc in state['proj.cfg.task_c']:
        tc_path = os.path.join(state['proj.root'], tc['tasks_root'])
        tc_mod = load_task_c_module(tc_path, tc['tasks_module'])
        diff.append(asdict(tc_mod))

    return dict_to_envy(diff)


def run_inv_task(tasks_root: str, tasks_module: str, tname: str, args: dict):
    inv_prg = Program()
    t_cmd = ['x', '--search-root', tasks_root, '-c', tasks_module, tname]
    for an, av in args.items():
        t_cmd.extend([f'--{an}', av])
    inv_prg.run(t_cmd)


@dcw_cmd({'name': ..., 'args': {}})
def cmd_run_task(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    state = EnvyState(s, dcw_envy_cfg())
    state += run(NAME, 'load')
    tname = args['name']

    task_colls: List[DcwTaskCollection] = state['task_c', value_map_list(DcwTaskCollection)]
    
    tc = next(filter(lambda c: tname in c.task_names, task_colls))
    if tc is None:
        raise Exception(f'Task with name {tname} not found in loaded collections.')
    
    run_inv_task(tc.tasks_root, tc.tasks_module, tname, args['args'])
    return []


@dcw_cmd()
def cmd_list(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state: EnvyState = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')
    pp([DcwTaskCollection(**tc) for _, tc in state['task_c.*']])
    return []

# endregion
