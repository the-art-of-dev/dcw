# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import enum
import os
from typing import Callable, List

from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, apply_cmd_log, dict_to_envy, get_selector_val
from pprint import pprint as pp
from dcw.utils import check_for_missing_args, value_map_dict

# --------------------------------------
#   Tasks
# --------------------------------------
# region
__doc__ = '''Dcw Tasks - handles DCW automation with predefined task setups'''
NAME = name = 'tasks'
SELECTOR = selector = ['tasks']


class DcwTaskConfigMode(str, enum.Enum):
    PROJECT = 'project'                 # runs against project (per project) (only once for now)
    DEPLOYMENT = 'deployment'           # runs against deployment (one task per env)
    SERVICE_GROUP = 'service_group'     # runs against service group (one task per service group)
    SERVICE = 'service'                 # runs against service (one task per service)


@dataclass
class DcwTask:
    name: str                   # name of the task
    mode: DcwTaskConfigMode     # mode of task config (infulence structure of args)
    args: dict = field(default_factory=dict)  # if not project mode first level is mapped

    def key(self) -> str:
        return '{self.name}-{self.mode}'


@dcw_cmd()
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    s = apply_cmd_log(s, run('proj', 'load'), dcw_envy_cfg())
    tasks_cfg: dict[str, dict] = get_selector_val(s, ['proj', 'cfg', 'tasks'])
    mode = DcwTaskConfigMode.PROJECT.value
    return dict_to_envy({f'{n}-{mode}': asdict(DcwTask(n, mode, a)) for n, a in tasks_cfg.items()})


@dcw_cmd({'name': ...})
def cmd_xp(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    tname = args['name']
    mode = DcwTaskConfigMode.PROJECT.value

    cl = run('task_c', 'load') + run('tasks', 'load')
    s = apply_cmd_log(s, cl, dcw_envy_cfg())

    tasks: dict[str, DcwTask] = get_selector_val(s, ['tasks'], value_map_dict(str, DcwTask))
    if f'{tname}-{mode}' not in tasks:
        raise Exception(f'Task key {tname}-{mode} not found.')

    run('task_c', 'run_task', {
        **args,
        'args': {**tasks[f'{tname}-{mode}'].args}
    })

    return []


@dcw_cmd({'name': ..., 'depl': ...})
def cmd_xe(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name', 'depl'])
    tname = args['name']
    depl_name = args['depl']
    mode = DcwTaskConfigMode.DEPLOYMENT.value
    tkey = f'{tname}-{mode}'

    cl = run('task_c', 'load') + run('tasks', 'load')
    s = apply_cmd_log(s, cl, dcw_envy_cfg())

    targs = get_selector_val(s, ['tasks', tkey, depl_name])
    if targs is None:
        raise Exception(f'Task with key {tkey} not foud for env {depl_name}.')
    run('task_c', 'run_task', {
        **args,
        'args': {**targs}
    })
    return []


@dcw_cmd({'name': ..., 'env': ...})
def cmd_xs(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name', 'env'])
    tname = args['name']
    svc_name = args['svc']
    tkey = f'{tname}-{mode}'
    mode = DcwTaskConfigMode.SERVICE.value

    cl = run('task_c', 'load') + run('tasks', 'load') + run('scripts', 'load')
    s = apply_cmd_log(s, cl, dcw_envy_cfg())

    targs = get_selector_val(s, ['tasks', tkey, svc_name])
    if targs is None:
        raise Exception(f'Task with key {tkey} not foud for svc {svc_name}.')
    run('task_c', 'run_task', {
        **args,
        'args': {**targs}
    })
    return []

# endregion
