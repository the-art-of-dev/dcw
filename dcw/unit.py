from dcw.service import DCWService
from dcw.environment import DCWEnv
import os


class DCWUnit:
    def __init__(self, name: str, svc_names: [str] = None) -> None:
        self.name = name
        self.svc_names = svc_names if svc_names is not None else []

    def apply_env(self, env: DCWEnv, svc_group: dict[str, DCWService]) -> dict[str, DCWService]:
        """Apply an environment to this unit"""
        svcs = {}
        for svc_name in self.svc_names:
            if svc_name not in svc_group:
                raise Exception(
                    f'Service {svc_name} not found')

            svc_group[svc_name].apply_global_env(env.global_envs)
            if svc_name in env.service_configs:
                svc_group[svc_name].apply_config(env.service_configs[svc_name])
            svcs[svc_name] = svc_group[svc_name]
        return svcs


def import_unit_from_file(file_path: str) -> DCWUnit:
    file_name = os.path.basename(file_path)
    if not file_name.startswith('dcw.') or not file_name.endswith('.txt'):
        return None

    name = file_name[len('dcw.'):].split('.')[0]

    svc_names = []
    with open(file_path) as f:
        for line in f:
            svc_names.append(line.strip())

    return DCWUnit(name, svc_names[:])


def import_units_from_dir(dir_path: str) -> dict[str, DCWUnit]:
    units = {}
    for file_name in os.listdir(dir_path):
        u = import_unit_from_file(os.path.join(dir_path, file_name))
        if u is None:
            continue
        units[u.name] = u
    return units
