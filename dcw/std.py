# pylint: skip-file
import os
import subprocess
from dcw.deployment import DCWDeploymentSpecification, DCWDeploymentMaker, DCWDeploymentExecute
from dcw.utils import flatten
import yaml
from pprint import pprint as pp


class DockerComposeDeploymentMaker(DCWDeploymentMaker):
    def __init__(self) -> None:
        super().__init__("std.docker-compose", "docker-compose")

    def __is_named_volume(self, volume: str) -> bool:
        vn = volume.split(':')[0]
        return '.' not in vn and '/' not in vn and '\\' not in vn

    def _make_deployment(self, depl_spec: DCWDeploymentSpecification, output_path: str):
        dc_depl = {'services': depl_spec.services, 'networks': {}}
        dc_depl['networks'] = {nn: {} for nn in set(
            flatten([dc_depl['services'][sn]['networks'] for sn in dc_depl['services']]))}

        named_volumes = filter(lambda x: x is not None, [vn if self.__is_named_volume(
            vn) else None for vn in flatten([dc_depl['services'][sn]['volumes'] for sn in dc_depl['services']])])

        dc_depl['volumes'] = {nv.split(':')[0]: {} for nv in named_volumes}

        with open(output_path, 'w') as f:
            yaml.safe_dump(dc_depl, f)


class DockerComposeDeploymentExecute(DCWDeploymentExecute):
    pass


class K8SDeploymentMaker(DCWDeploymentMaker):
    def __init__(self) -> None:
        super().__init__("std.k8s", "k8s")

    def _make_deployment(self, depl_spec: DCWDeploymentSpecification, output_path: str):
        for svc in depl_spec.services:
            if 'depends_on' in depl_spec.services[svc]:
                del depl_spec.services[svc]['depends_on']

        DCWDeploymentMaker.make_deployment(
            'std.docker-compose', depl_spec, f'{output_path}.tmp.yml')
        proc = subprocess.run(
            ['kompose', 'convert', '-f', f'{output_path}.tmp.yml', '--stdout'], capture_output=True, text=True)
        os.remove(f'{output_path}.tmp.yml')
        if proc.stderr:
            print(proc.stderr)
            return
        k8s_kinds = yaml.safe_load_all(proc.stdout)
        k8s_kinds = self.__enrich_k8s(k8s_kinds, depl_spec)

        with open(output_path, 'w') as f:
            yaml.safe_dump_all(k8s_kinds, f)

    def __enrich_k8s_svc(self, k8s_svc: dict, depl_spec: DCWDeploymentSpecification):
        name: str = k8s_svc['metadata']['name']
        if name not in depl_spec.services:
            return
        service = depl_spec.services[name]
        if 'dcw.kompose.service.loadbalancerip' in service['labels']:
            print('dimra')
            k8s_svc['spec']['loadBalancerIP'] = service['labels']['dcw.kompose.service.loadbalancerip']

    def __enrich_k8s_kind(self, k8s_kind: dict, depl_spec: DCWDeploymentSpecification):
        name: str = k8s_kind['metadata']['name']
        if name not in depl_spec.services:
            return

        service = depl_spec.services[name]
        if 'dcw.kompose.namespace' in service['labels']:
            k8s_kind['metadata']['namespace'] = service['labels']['dcw.kompose.namespace']

        # specific kinds
        if k8s_kind['kind'].upper() == 'SERVICE':
            self.__enrich_k8s_svc(k8s_kind, depl_spec)

    def __enrich_k8s(self, k8s_kinds, depl_spec: DCWDeploymentSpecification):
        new_k8s_kinds = list(k8s_kinds)[:]
        for kind_config in new_k8s_kinds:
            if 'kind' not in kind_config:
                continue

            self.__enrich_k8s_kind(kind_config, depl_spec)

        return new_k8s_kinds
