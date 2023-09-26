from dcw.service import DCWService
from dcw.environment import DCWEnv
import os
import yaml
from dcw.utils import flatten
from pprint import pprint as pp
import shutil
import subprocess
import sys
from dcw.context import DCWContext
from dcw.config import DCWConfigMagic


class DCWDeploymentSpec:
    def __init__(self,
                 name: str,
                 type: str,
                 unit: str,
                 services: dict,
                 env: dict,
                 host_list: [str]) -> None:
        self.name = name
        self.type = type
        self.unit = unit
        self.host_list = host_list
        self.services = services
        self.environment = env

    def as_dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'unit': self.unit,
            'services': self.services,
            'environment': self.environment,
            'host_list': self.host_list,
        }

    @classmethod
    def from_dict(cfg_dict: dict):
        return DCWDeploymentSpec(
            cfg_dict['name'],
            cfg_dict['type'],
            cfg_dict['unit'],
            cfg_dict['services'],
            cfg_dict['env'],
            cfg_dict['host_list']
        )


def export_deployment_spec(spec_path: str, depl_sepc: DCWDeploymentSpec):
    export_dir = os.path.dirname(spec_path)
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    with open(spec_path, 'w') as f:
        yaml.safe_dump(depl_sepc.as_dict(), f)
    return spec_path


def import_deployment_spec(spec_path: str) -> DCWDeploymentSpec:
    if not os.path.exists(spec_path):
        raise Exception(f'Dployment specification {spec_path} not found!')
    with open(spec_path, 'r') as f:
        return DCWDeploymentSpec.from_dict(yaml.safe_load(f))


class DCWDeployment:
    def __init__(self,
                 name: str,
                 type: str,
                 unit: DCWUnit,
                 serivce_map: [str, DCWService],
                 env: DCWEnv,
                 host_list: [str]) -> None:
        self.name = name
        self.type = type
        self.unit = unit
        self.serivce_map = serivce_map
        self.env = env
        self.host_list = host_list

    def make_deployment_spec(self):
        return DCWDeploymentSpec(
            self.name,
            self.type,
            self.unit.name,
            self.unit.apply_env(self.env, self.serivce_map),
            self.env.as_dict(),
            self.host_list
        )


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


class DCWTenantDeploymentConfig:
    def __init__(self) -> None:
        self.name = ''
        self.type = ''
        self.unit = ''
        self.services = ''
        self.enironment = ''
        self.host_list = ''
        self.tasks = ''


class DCWTenant:
    def __init__(self, name: str, depl_cfgs: dict[str, DCWTenantDeploymentConfig], ctx: DCWContext) -> None:
        self.name = name
        self.tenant_root = os.path.join(
            ctx.config[DCWConfigMagic.DCW_TENANT_DEPL_ROOT], name)
        self.depl_map = {c: self.__convert_dcfg(
            depl_cfgs[c], ctx) for c in depl_cfgs}

    def __convert_dcfg(self, cfg: DCWTenantDeploymentConfig, ctx: DCWContext) -> DCWDeployment:
        unit = ctx.units[cfg.unit]
        svcs = [ctx.services[s] for s in unit.s]
        env = ctx.environments[cfg.enironment]
        return DCWDeployment(cfg.name,
                             cfg.type,
                             unit,
                             svcs,
                             env,
                             cfg.host_list)

    # ---- DEPLOYMENTS -----

    def __make_docker_compose_deployment(self, depl_spec: DCWDeploymentSpec):
        dc_depl_path = os.path.join(
            self.tenant_root, depl_spec.name, 'docker-compose.yml')
        dc_depl_dir = os.path.dirname(dc_depl_path)
        if not os.path.exists(dc_depl_dir):
            os.makedirs(dc_depl_dir)

        dc_depl = {'services': depl_spec.services, 'networks': {}}
        dc_depl['networks'] = {nn: {} for nn in set(flatten(
            [dc_depl['services'][sn]['networks'] for sn in dc_depl['services']]))}
        with open(dc_depl_path, 'w') as f:
            yaml.safe_dump(dc_depl, f)

    def __convert_dc_to_k8s_deployment(self):
        pass

    def __make_k8s_deployment(self, depl_spec: DCWDeploymentSpec):
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
          

    def make_deployment(self, depl_names: [str]):
        maker_map = {
            'dc': self.__make_docker_compose_deployment,
            'k8s': self.__make_k8s_deployment
        }

        for dn in depl_names:
            if dn not in self.depl_map:
                raise Exception(f'Deployment {dn} not exist')
            depl = self.depl_map[dn]
            if depl.type not in maker_map:
                raise Exception(f'Deployment type {depl.type} not supported')
            maker_map[depl.type](depl)

    def execute_deployment_command(self):
        pass

    # ---- TASKS ----

    def run_task(self):
        pass

    def run_deployment_task(self):
        pass

    def run_deployment_svc_task(self):
        pass
