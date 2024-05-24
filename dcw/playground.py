# pylint: skip-file
from dataclasses import dataclass, field
from pprint import pprint as pp
from typing import List
from dcw.core import DcwContext, DcwState, dcw_envy_cfg, sys_to_dcw_module
from dcw.stdmods import project, scripts, task_collections, tasks, services, docs, deployments
from dcw.extmods import docker_compose
from dcw.envy import EnvyCmd, EnvyState, filter_to_selectors, get_filter_selector_val, set_filter_selector_val, set_selector_val
from dcw.utils import value_map_dataclass

proj_mod = sys_to_dcw_module(project)
task_c_mod = sys_to_dcw_module(task_collections)
tasks_mod = sys_to_dcw_module(tasks)
svcs_mod = sys_to_dcw_module(services)
docker_compose_mod = sys_to_dcw_module(docker_compose)
envs_mod = sys_to_dcw_module(scripts)
depls_mod = sys_to_dcw_module(deployments)

ctx = DcwContext(state=DcwState([], {}), modules={
    proj_mod.name: proj_mod,
    task_c_mod.name: task_c_mod,
    tasks_mod.name: tasks_mod,
    envs_mod.name: envs_mod,
    svcs_mod.name: svcs_mod,
    docker_compose_mod.name: docker_compose_mod,
    depls_mod.name: depls_mod
})

# docs.cmd_make(ctx, {})

# ctx.run('depls', 'load')


# ctx.run('envs', 'load')
# ctx.run('envs', 'apply', {'env_name': 'bobabrena'})
# ctx.run('svcs', 'load')
# ctx.run('scm', 'load')
# ctx.run('procs', 'load')
# ctx.run('procs', 'run', {
#     'name': 'proc_test'
# })

# ctx.run('proj', 'load')
# ctx.run('task_c', 'load')
# ctx.run('task_c', 'list')
# ctx.run('tasks', 'load')


# ctx.run('envs', 'list')
# pp(ctx.state.data)
# ctx.run('envs', 'load', {
#     'env_name': 'bobabrena'
# })

# ctx.run('tasks', 'xp', {
#     'name': 'hello'
# })

# ctx.run('task_c', 'run_task', {
#     'name': 'hello',
#     'args': {
#         'name': 'yyy'
#     }
# })

# pp(ctx.state.cmd_log)

# pp('-'*40)
# pp('-'*40)

# pp(ctx.state.data)

obj = {
    'svcs': {
        'svc-1': {
            'image': 'webapp',
            'environment': {
                'MY_KEY': '2*656'
            },
            'envy': ''
        },
        'svc-2': {
            'image': 'webapp',
            'environment': {
                'MY_KEY': '2*2*328'
            }
        }
    }
}
# sels = filter_to_selectors(obj, ['svcs', 'svc-*', 'env*'], [])

# pp(sels)

# pp(get_filter_selector_val(obj, ['svcs', 'svc-*', 'env*']))

# pp(set_selector_val(obj, ['svcs', 'svc-1', 'environment', 'new_key'], 'yo'))

# pp(set_filter_selector_val(obj, ['svcs', 'svc-*', 'envi*', 'new_key'], 'yo'))


@dataclass
class MySvc:
    image: str = ''
    environment: dict = field(default_factory=dict)
    envy: str = ''
    labels: List[str] = field(default_factory=list)


envy_state = EnvyState(obj, dcw_envy_cfg()) + [EnvyCmd(['volumes', '<0>'],
                                                       '', 'vol_one'), EnvyCmd(['volumes', '<1>'], '', 'vol_two')]

envy_state['svcs.*.labels.mylbl'] = 'Yo'
envy_state['svcs.svc-1.labels.mylbl'] = 'YoYo'
# pp(envy_state['svcs.svc-1', value_map_dataclass(MySvc)])
x = envy_state['volumes']
pp(envy_state)
pp(type(x))
pp(x)
