from dcw.service import DCWService
from dcw.environment import DCWEnv
from dcw.unit import DCWUnit
import os
import yaml
from dcw.utils import flatten
from pprint import pprint as pp
import shutil
import subprocess


class DCWDeployment:
    def __init__(self, name: str, type: str, depl_pairs: [(str, str)]) -> None:
        self.name = name
        self.depl_paris = depl_pairs
        self.type = type

    def create_deployment_config(self, svc_group: dict[str, DCWService], env_group: dict[str, DCWEnv], unit_group: dict[str, DCWUnit]) -> dict[str, DCWService]:
        depl_config = {}
        for (unit_name, env_name) in self.depl_paris:
            if unit_name not in unit_group:
                raise Exception(f'Unit {unit_name} not found!')
            if env_name not in env_group:
                raise Exception(f'Environment {env_name} not found!')

            unit = unit_group[unit_name]
            env = env_group[env_name]
            depl_config = {
                **depl_config,
                **unit.apply_env(env, svc_group)
            }
        return depl_config


def import_deployment_from_file(file_path: str) -> DCWDeployment:
    file_name = os.path.basename(file_path)
    file_name_parts = file_name.split('.')
    if file_name_parts.pop() != 'txt':
        return None
    if len(file_name_parts) <= 1:
        return None
    type = file_name_parts.pop(0)
    name = '.'.join(file_name_parts)
    depl_pairs = []
    with open(file_path, 'r') as f:
        for line in f:
            depl_pairs.append(tuple(line.strip().split(':')))
    return DCWDeployment(name, type, depl_pairs)


def import_deployments_from_dir(dir_path: str) -> dict[str, DCWDeployment]:
    depls = {}
    for file_name in os.listdir(dir_path):
        d = import_deployment_from_file(os.path.join(dir_path, file_name))
        if d is None:
            continue
        depls[d.name] = d

    return depls


def get_depl_config_path(dir_path: str, deployment: DCWDeployment):
    return os.path.join(dir_path, deployment.name, 'depl_config.yaml')


def export_deployment_configuration(dir_path: str, deployment: DCWDeployment, config: dict[str, DCWService]) -> str:
    depl_config_path = get_depl_config_path(dir_path, deployment)
    export_dir = os.path.dirname(depl_config_path)
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    with open(depl_config_path, 'w') as f:
        yaml.safe_dump(config, f)
    return depl_config_path


def make_dc_deployment(depl_config_path: str):
    depl_config_dir = os.path.dirname(depl_config_path)
    depl_config = {'services': {}, 'networks': {}}
    with open(depl_config_path) as f:
        depl_config['services'] = yaml.safe_load(f)
    depl_config['networks'] = {nn: {} for nn in set(flatten(
        [depl_config['services'][sn]['networks'] for sn in depl_config['services']]))}

    dc_depl_path = os.path.join(depl_config_dir, 'docker-compose.yml')
    with open(dc_depl_path, 'w') as f:
        yaml.safe_dump(depl_config, f)


def make_k8s_deployment(depl_config_path: str):
    make_dc_deployment(depl_config_path)
    depl_config_dir = os.path.dirname(depl_config_path)
    k8s_depl_dir = os.path.join(depl_config_dir, 'k8s')
    if os.path.exists(k8s_depl_dir):
        shutil.rmtree(k8s_depl_dir)
    os.makedirs(k8s_depl_dir)
    proc = subprocess.run(['kompose', 'convert', '--out', 'k8s'],
                          cwd=depl_config_dir, capture_output=True, text=True)
    if proc.stderr:
        print(proc.stderr)
        return


def upgrade_k8s_deployment(depl_config_path: str):
    if not os.path.exists(depl_config_path):
        return

    depl_config = {}
    with open(depl_config_path) as f:
        depl_config = yaml.safe_load(f)

    depl_config_dir = os.path.dirname(depl_config_path)
    k8s_depl_dir = os.path.join(depl_config_dir, 'k8s')
    if not os.path.exists(k8s_depl_dir):
        return

    for file_name in os.listdir(k8s_depl_dir):
        print(file_name)
        k8s_config_path = os.path.join(k8s_depl_dir, file_name)
        k8s_config = {}
        with open(k8s_config_path) as f:
            k8s_config = yaml.safe_load(f)
        if 'kind' not in k8s_config:
            continue
        kind = k8s_config['kind']
        name: str = k8s_config['metadata']['name']
        if name.strip('-tcp') not in depl_config:
            continue
        svc_config = depl_config[name.strip('-tcp')]
        if 'rich-kompose.service.loadbalancerip' in svc_config['labels'] and kind.upper() == 'SERVICE':
            k8s_config['spec']['loadBalancerIP'] = svc_config['labels']['rich-kompose.service.loadbalancerip']
        with open(k8s_config_path, 'w') as f:
            yaml.safe_dump(k8s_config, f)
