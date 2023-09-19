from dcw.service import DCWService
from dcw.environment import DCWEnv
from dcw.unit import DCWUnit
import os
import yaml


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


def export_deployment_configuration(dir_path: str, deployment: DCWDeployment, config: dict[str, DCWService]) -> None:
    export_dir = os.path.join(dir_path, deployment.name, deployment.type)
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    with open(os.path.join(export_dir, 'depl_config.yaml'), 'w') as f:
        yaml.safe_dump(config, f)
