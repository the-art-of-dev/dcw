from dcw.config import DCWConfig, DCWConfigMagic, import_config_from_file
from dcw.service import DCWService, import_services_from_dir
from dcw.unit import DCWUnit, import_units_from_dir
from dcw.environment import DCWEnv, import_envs_from_dir
from dcw.task import DCWTask, import_tasks_from_dir


class DCWContext:
    def __init__(self,
                 config: DCWConfig,
                 services: [dict, DCWService] = None,
                 units: [dict, DCWUnit] = None,
                 environments: [dict, DCWEnv] = None,
                 tasks: [dict, DCWTask] = None) -> None:
        self.config = config
        self.services: [dict, DCWService] = services if services else {}
        self.environments: [
            dict, DCWEnv] = environments if environments else {}
        self.units: [dict, DCWUnit] = units if units else {}
        self.tasks = tasks if tasks else {}


def build_dcw_context(config_path: str):
    config = import_config_from_file(config_path)
    svcs_path = config[DCWConfigMagic.DCW_SVCS_PATH]
    units_path = config[DCWConfigMagic.DCW_UNITS_PATH]
    envs_path = config[DCWConfigMagic.DCW_ENVS_PATH]
    tasks_path = config[DCWConfigMagic.DCW_TASKS_PATH]

    return DCWContext(config,
                      services=import_services_from_dir(svcs_path),
                      units=import_units_from_dir(units_path),
                      environments=import_envs_from_dir(envs_path),
                      tasks=import_tasks_from_dir(tasks_path))
