from dcw.deployment import DCWDeploymentMaker
from dcw.utils import flatten
import yaml

class TestDeploymentMaker(DCWDeploymentMaker):
    def __init__(self) -> None:
        super().__init__("test.docker-compose", "docker-compose")

    def _make_deployment(self, depl_spec, output_path: str):
        dc_depl = {'services': depl_spec.services, 'networks': {}}
        dc_depl['networks'] = {nn: {} for nn in set(
            flatten([dc_depl['services'][sn]['networks'] for sn in dc_depl['services']]))}

        with open(output_path, 'w') as f:
            yaml.safe_dump(dc_depl, f)

maker = TestDeploymentMaker