from dcw.environment import import_env_from_file
from pprint import pprint as pp
from dcw.service import import_services_from_file
from dcw.deployment import make_deployment_specifications, DCWDeploymentMaker, import_deployment_maker_from_file
from dcw.std import DockerComposeDeploymentMaker, K8SDeploymentMaker
from dcw.context import DCWContext

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

depl_specs = make_deployment_specifications(env.name, 'FULL', ctx)

# for dc in depl_specs:
#     # print(dc.name)
#     # for s in dc.services:
#         # pp(dc.services[s])
#     DCWDeploymentMaker.make_deployment(
#         'std.k8s', dc, f'./hacking/k8s.test-svc-{dc.name}.yml')

import_deployment_maker_from_file('hacking.test-maker')