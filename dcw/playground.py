from dcw.environment import import_env_from_file
from pprint import pprint as pp
from dcw.service import import_services_from_file
from dcw.deployment import make_deployment_specifications, DCWDeploymentMaker
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
depl_specs = make_deployment_specifications(env.name, 'SVC', ctx)

for dc in depl_specs:
    print(dc.name + ' ' + dc.deployment_type)
    for s in dc.services:
        pp(dc.services[s])
    DCWDeploymentMaker.make_deployment(
        'k8s', dc, f'./hacking/k8s.test-svc-{dc.name}.yml')
