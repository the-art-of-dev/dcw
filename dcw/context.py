from dcw.config import DCWConfig, DCWMagicConfigs
from dcw.service import DCWService, import_services_from_dir
from dcw.unit import DCWUnit, import_units_from_dir
from dcw.environment import DCWEnv, import_envs_from_dir
from dcw.repository import DCWRepository
from dcw.registry import DCWRegistry
from dcw.deployment import DCWDeployment, import_deployments_from_dir

class DCWContext:
    def __init__(self, config: DCWConfig) -> None:
        self.config = config
        self.services = import_services_from_dir(
            self.config[DCWMagicConfigs.DCW_SVCS_PATH])
        self.environments = import_envs_from_dir(
            self.config[DCWMagicConfigs.DCW_ENVS_PATH])
        self.units = import_units_from_dir(
            self.config[DCWMagicConfigs.DCW_UNITS_PATH])
        self.deployments = import_deployments_from_dir(
            self.config[DCWMagicConfigs.DCW_DEPLS_PATH])
