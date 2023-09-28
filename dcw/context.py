from dcw.config import DCWConfig, DCWConfigMagic, import_config_from_file
from dcw.service import DCWService, import_services_from_dir
from dcw.environment import DCWEnv, import_envs_from_dir


class DCWContext:
    def __init__(self,
                 config: DCWConfig,
                 services: dict[str, DCWService] = None,
                 environments: dict[str, DCWEnv] = None) -> None:
        self.config = config
        self.services: dict[str, DCWService] = services if services else {}
        self.environments: dict[str,
                                DCWEnv] = environments if environments else {}


def build_dcw_context(config_path: str):
    config = import_config_from_file(config_path)
    svcs_path = config[DCWConfigMagic.DCW_SVCS_PATH]
    envs_path = config[DCWConfigMagic.DCW_ENVS_PATH]

    return DCWContext(config,
                      services=import_services_from_dir(svcs_path),
                      environments=import_envs_from_dir(envs_path))
