# pylint: skip-file
from os import PathLike
from typing import Any, Dict, Optional
from dcw.environment import import_env_from_file
from pprint import pprint as pp
from dcw.service import import_services_from_file
from dcw.deployment import make_deployment_specifications, DCWDeploymentMaker, import_deployment_maker_from_file
from dcw.std import DockerComposeDeploymentMaker, K8SDeploymentMaker
from dcw.context import DCWContext
import docker_compose_diagram
from docker_compose_diagram.di_container.facade import docker_compose_parser, plugins
from docker_compose_diagram.renderer.base import Renderer
from docker_compose_diagram.renderer.diagrams import DiagramsRenderer
from dcw.tasks import DCWTask, DCWTaskCollection, DCWTaskSpec, asdict

env = import_env_from_file('./hacking/dcw-envs/.checker.env')
# pp(env.global_envs)
# pp(env.service_configs)
# pp(env.svc_group_configs)
# pp(env.as_dict())

svcs = import_services_from_file(
    './hacking/dcw-svcs/docker-compose.checker.yml')

# for svc in svcs:
#   new_svc = env.apply_on_service(svcs[svc])
#   pp(svcs[svc].config)
#   print('*'*20)
#   pp(new_svc.config)
#   print('-'*80)

DockerComposeDeploymentMaker()
K8SDeploymentMaker()

ctx = DCWContext(None, svcs, {env.name: env})
# ctx2 = DCWContext()

# pp(ctx.environments[env.name])
# ctx2.environments[env.name].set_env('playground-set', 'LLLL')
# pp(ctx.environments[env.name].get_env('playground-set'))

# depl_specs = make_deployment_specifications(env.name, 'FULL', ctx)

# for dc in depl_specs:
# print(dc.name)
# for s in dc.services:
# pp(dc.services[s])
# DCWDeploymentMaker.make_deployment(
#     'std.docker-compose', dc, f'./hacking/docker-compose-{dc.name}.yml')

# DCWDeploymentMaker.make_deployment(
#     'std.k8s', dc, f'./hacking/k8s.{dc.name}.yml')

# import_deployment_maker_from_file('hacking.test-maker')

# services = docker_compose_parser.parse(
#             file_path=f'./hacking/docker-compose-{dc.name}.yml',
#         )

# renderer: Renderer = DiagramsRenderer(
#             plugins=plugins,
#             config={
#             },
#         )


# renderer.render(
#     services=services,
#     destination_file=f'./hacking/docker-compose-{dc.name}',
# )


# task_fsl = FilesystemLoader()
# task_fsl._start='./hacking/dcw-tasks'
# # task_fsl.config['tasks']['collection_name'] = 'dcw-tasks'
# tasks = task_fsl.load()
# pp(tasks)

# coll = Collection()
# coll.add_task(tasks[0])

# # Local(context=Context())
# exctr = Executor(coll)
# exctr.execute('test')

# class MyConfig(Config):
#     def __init__(self, overrides: Dict[str, Any] | None = None, defaults: Dict[str, Any] | None = None, system_prefix: str | None = None, user_prefix: str | None = None, project_location: PathLike | None = None, runtime_path: PathLike | None = None, lazy: bool = False):
#         super().__init__(overrides, defaults, system_prefix, user_prefix, project_location, runtime_path, lazy)
#         self['tasks']['search_root'] = './hacking'
#         self['tasks']['collection_name'] = 'dcw-tasks'

# inv_cfg = Config()
# inv_cfg['tasks']['search_root'] = './hacking/dcw-tasks'

# inv_ctx = Context(inv_cfg)
# inv_fsl = FilesystemLoader()

# prg = Program()
# prg.run(['x', '--search-root', './hacking', '-c', 'dcw-tasks', '-l'])

# {
#     'name': 'tasks.test',
#     'mode': 'ENVIRONMENT',
#     'args': {}
# }


# run_task(DCWTask('tasks.hello', 'SERVICE', {'name': 'yo'}))

first_task = DCWTask(asdict(DCWTaskSpec('tasks.hello', 'SERVICE', {'name': 'yo', '__merge_disabled': 'true'})))
second_task = DCWTask(asdict(DCWTaskSpec('tasks.hello', 'SERVICE', {'name': 'poyy'})))

first_task.run('./hacking', 'dcw-tasks')
second_task.run('./hacking', 'dcw-tasks')

print('-'*20)

coll = DCWTaskCollection([
    DCWTaskSpec('tasks.hello', 'SERVICE', {'name': 'yo', '__merge_disabled': 'true'}),
    DCWTaskSpec('tasks.hello', 'SERVICE', {'name': 'poyy', '__merge_disabled': 'false'})
], './hacking', 'dcw-tasks')

coll.run_task('tasks.hello', 'SERVICE')

print('-'*20)

coll = DCWTaskCollection([
    DCWTaskSpec('tasks.hello', 'SERVICE', {'name': 'yo', '__merge_disabled': 'false'}),
    DCWTaskSpec('tasks.hello', 'SERVICE', {'name': 'poyy', '__merge_disabled': 'false'})
], './hacking', 'dcw-tasks')

coll.run_task('tasks.hello', 'SERVICE')

print('-'*20)



coll = DCWTaskCollection([
    DCWTaskSpec(**{'args': {'name': 'poyy', 'name.__chainable': ''},
            'mode': 'SERVICE',
            'name': 'tasks.hello'}),
    DCWTaskSpec(**{'args': {'name': 'yo', 'name.__chainable': ''},
            'mode': 'SERVICE',
            'name': 'tasks.hello'})
], './hacking', 'dcw-tasks')

coll.run_task('tasks.hello', 'SERVICE')