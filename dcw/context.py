from dcw.config import DCWConfig, DCWConfigMagic, import_config_from_file
from dcw.service import DCWService, import_services_from_dir
from dcw.environment import DCWEnv, import_envs_from_dir


class DCWContext(object):
    _instance = None

    def __new__(cls,
                config: DCWConfig = None,
                services: dict[str, DCWService] = None,
                environments: dict[str, DCWEnv] = None):
        if cls._instance is None:
            cls._instance = super(DCWContext, cls).__new__(cls)
            cls._instance.config = config
            cls._instance.environments = environments
            cls._instance.services = services
        return cls._instance

    def __init__(self, *args, **kwargs) -> None:
        self.config: DCWConfig
        self.environments: dict[str, DCWEnv]
        self.services: dict[str, DCWService]


def import_dcw_context(config_path: str):
    config = import_config_from_file(config_path)
    svcs_path = config[DCWConfigMagic.DCW_SVCS_PATH]
    envs_path = config[DCWConfigMagic.DCW_ENVS_PATH]

    DCWContext(config,
               services=import_services_from_dir(svcs_path),
               environments=import_envs_from_dir(envs_path))
