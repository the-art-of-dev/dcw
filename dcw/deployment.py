from abc import ABC, abstractmethod
import enum
from dcw.environment import DCWEnv
import os
import yaml
from pprint import pprint as pp
from dcw.context import DCWContext


class DCWDeploymentSpecificationType(str, enum.Enum):
    FULL = 'FULL'
    SVC_GROUP = 'SVC_GROUP'
    SVC = 'SVC'


class DCWDeploymentSpecification:
    def __init__(self,
                 name: str,
                 services: dict[str, dict],
                 env: dict) -> None:
        self.name = name
        self.services = services
        self.environment = env

    def as_dict(self):
        return {
            'name': self.name,
            'services': self.services,
            'environment': self.environment
        }

    @classmethod
    def from_dict(cfg_dict: dict):
        return DCWDeploymentSpecification(
            cfg_dict['name'],
            cfg_dict['services'],
            cfg_dict['environment'],
        )


def __make_full_deplyoment_specification(env_name: str, dcw_ctx: DCWContext) -> [DCWDeploymentSpecification]:
    environment: DCWEnv = dcw_ctx.environments[env_name]
    depl_specs = []
    default_spec_svcs = {}

    for svc_name in environment.services:
        if svc_name not in dcw_ctx.services:
            raise Exception(f'SERVICE {svc_name} DOES NOT EXIST!')
        svc = dcw_ctx.services[svc_name]
        default_spec_svcs[svc_name] = environment.apply_on_service(
            svc).as_dict()

    for group_name in environment.svc_groups:
        svcs = filter(lambda s: group_name in s.groups, [
                      dcw_ctx.services[s] for s in dcw_ctx.services])
        for s in svcs:
            default_spec_svcs[s.name] = environment.apply_on_service(
                s).as_dict()

    depl_specs.append(DCWDeploymentSpecification(
        'default', default_spec_svcs, environment.as_dict()))

    return depl_specs


def __make_per_svc_group_deployment_specification(env_name: str, dcw_ctx: DCWContext) -> [DCWDeploymentSpecification]:
    environment: DCWEnv = dcw_ctx.environments[env_name]
    depl_specs = []

    if environment.services:
        default_spec_svcs = {}
        for svc_name in environment.services:
            if svc_name not in dcw_ctx.services:
                raise Exception(f'SERVICE {svc_name} DOES NOT EXIST!')
            svc = dcw_ctx.services[svc_name]
            default_spec_svcs[svc_name] = environment.apply_on_service(
                svc).as_dict()

        depl_specs.append(DCWDeploymentSpecification(
            'default', default_spec_svcs, environment.as_dict()))

    for group_name in environment.svc_groups:
        svcs = filter(lambda s: group_name in s.groups, [
                      dcw_ctx.services[s] for s in dcw_ctx.services])
        group_depl_svcs = {}
        for s in svcs:
            group_depl_svcs[s.name] = environment.apply_on_service(s).as_dict()
        depl_specs.append(DCWDeploymentSpecification(
            group_name, group_depl_svcs, environment.as_dict()))

    return depl_specs


def __make_per_svc_deployment_specification(env_name: str, dcw_ctx: DCWContext) -> [DCWDeploymentSpecification]:
    environment: DCWEnv = dcw_ctx.environments[env_name]
    depl_specs = []

    if environment.services:
        for svc_name in environment.services:
            if svc_name not in dcw_ctx.services:
                raise Exception(f'SERVICE {svc_name} DOES NOT EXIST!')
            svc = dcw_ctx.services[svc_name]
            depl_specs.append(DCWDeploymentSpecification(
                svc_name, {svc_name: environment.apply_on_service(svc).as_dict()}, environment.as_dict()))

    for group_name in environment.svc_groups:
        svcs = filter(lambda s: group_name in s.groups, [
                      dcw_ctx.services[s] for s in dcw_ctx.services])
        for s in svcs:
            depl_specs.append(DCWDeploymentSpecification(
                s.name, {s.name: environment.apply_on_service(s).as_dict()}, environment.as_dict()))

    return depl_specs


def make_deployment_specifications(env_name: str, spec_type: DCWDeploymentSpecificationType, dcw_ctx: DCWContext) -> [DCWDeploymentSpecification]:
    if spec_type == DCWDeploymentSpecificationType.FULL:
        return __make_full_deplyoment_specification(env_name, dcw_ctx)
    elif spec_type == DCWDeploymentSpecificationType.SVC_GROUP:
        return __make_per_svc_group_deployment_specification(env_name, dcw_ctx)
    elif spec_type == DCWDeploymentSpecificationType.SVC:
        return __make_per_svc_deployment_specification(env_name, dcw_ctx)
    return []


def export_deployment_spec(spec_path: str, depl_sepc: DCWDeploymentSpecification):
    export_dir = os.path.dirname(spec_path)
    if export_dir != '' and not os.path.exists(export_dir):
        os.makedirs(export_dir)
    with open(spec_path, 'w') as f:
        yaml.safe_dump(depl_sepc.as_dict(), f)
    return spec_path


def import_deployment_spec(spec_path: str) -> DCWDeploymentSpecification:
    if not os.path.exists(spec_path):
        raise Exception(f'Dployment specification {spec_path} not found!')
    with open(spec_path, 'r') as f:
        return DCWDeploymentSpecification.from_dict(yaml.safe_load(f))


class DCWDeploymentMaker(ABC):
    deployment_makers: dict = {}

    def __init__(self, name, deployment_type) -> None:
        self.name = name
        self.deployment_type = deployment_type
        DCWDeploymentMaker.deployment_makers[deployment_type] = self

    @abstractmethod
    def _make_deployment(self, depl_spec: DCWDeploymentSpecification, output_path: str):
        pass

    @staticmethod
    def make_deployment(depl_type: str, depl_spec: DCWDeploymentSpecification, output_path: str):
        if depl_type not in DCWDeploymentMaker.deployment_makers:
            raise Exception(f'Deployment Maker {depl_type} not found.')
        DCWDeploymentMaker.deployment_makers[depl_type]._make_deployment(
            depl_spec, output_path)
