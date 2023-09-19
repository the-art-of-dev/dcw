from dcw.core import DCWService, DCWEnv, DCWUnit, DCWTemplate, DCWGroupIO, DCWGroup
import yaml
from dotenv import dotenv_values
import os
import copy
import shutil
import subprocess
from config import get_config
from pprint import pprint as pp
import itertools


class DCWGroupFileIO(DCWGroupIO):
    def __init__(self):
        super().__init__('file', os.getcwd())
        self.svc_path = get_config('DCW_SVCS_DIR')
        self.env_path = get_config('DCW_ENVS_DIR')
        self.unit_path = get_config('DCW_UNITS_DIR')

    def __import_svc(self, filename):
        if not filename.startswith('docker-compose.') or not filename.endswith('.yml'):
            return None

        name = filename[len('docker-compose.'):].split('.')[0]
        full_path = os.path.join(self.svc_path, filename)

        with open(full_path) as f:
            x = next(iter(yaml.safe_load(f)['services'].values()))
            return DCWService(name, config=x)

    def __import_svcs(self):
        svcs = []
        for filename in os.listdir(self.svc_path):
            svc = self.__import_svc(filename)
            if svc is None:
                continue
            svcs.append(svc)
        return svcs

    def __import_env(self, filename):
        if not filename.startswith('.') or not filename.endswith('.env'):
            return None

        name = filename[1:].split('.')[0]
        full_path = os.path.join(self.env_path, filename)

        return DCWEnv(name, dotenv_values(full_path))

    def __import_envs(self):
        envs = []
        for filename in os.listdir(self.env_path):
            env = self.__import_env(filename)
            if env is None:
                continue
            envs.append(env)
        return envs

    def __import_unit(self, filename):
        if not filename.startswith('dcw.') or not filename.endswith('.txt'):
            return None

        name = filename[len('dcw.'):].split('.')[0]
        full_path = os.path.join(self.unit_path, filename)

        svc_names = []
        with open(full_path) as f:
            for line in f:
                svc_names.append(line.strip())

        return DCWUnit(name, svc_names[:])

    def __import_units(self):
        units = []
        for filename in os.listdir(self.unit_path):
            unit = self.__import_unit(filename)
            if unit is None:
                continue
            units.append(unit)
        return units

    def import_group(self):
        objs = []
        objs.extend(self.__import_svcs())
        objs.extend(self.__import_envs())
        objs.extend(self.__import_units())

        return DCWGroup('file', objs=objs)

    def export_group(self, group):
        raise NotImplementedError('Not implemented')


def flatten(list_of_lists):
    return list(itertools.chain.from_iterable(list_of_lists))

def export_dc_deployment(svc_group: DCWGroup, env: DCWEnv, unit: DCWUnit, output=None):
    unit_env_name = env.name if env.name.startswith(
        unit.name) else f'{unit.name}-{env.name}'

    if output is None:
        output = f'docker-compose.{unit_env_name}.yml'

    svcs_data = unit.apply_env(env, svc_group)
    dc_data = {
        'services': {sn: svcs_data[sn].as_dict() for sn in svcs_data},
        'networks': {nn: {} for nn in set(flatten([svcs_data[sn].as_dict()['networks'] for sn in svcs_data]))},
    }
    with open(output, 'w') as f:
        yaml.safe_dump(dc_data, f)

    with open('.env', 'w') as f:
        yaml.safe_dump(env.global_envs, f)

    dc_command = f"docker compose -f {output} convert --output {output}"
    res = os.system(dc_command)
    os.remove('.env')


# class DCWUnitKubernetesExporter():
#     def __init__(self, dcw_unit, dcw_env, output_dir=None):
#         super().__init__(dcw_unit, dcw_env, None)

#         self.output_dir = output_dir
#         if self.output_dir is None:
#             self.output_dir = f'./k8s-{self.unit_env_name}'

#         self.dcw_unit = dcw_unit
#         self.dcw_env = dcw_env

#     def export(self):
#         super().export()
#         if os.path.exists(self.output_dir):
#             shutil.rmtree(self.output_dir)
#         os.makedirs(self.output_dir)

#         shutil.move(self.output_filename, self.output_dir)
#         subprocess.run(['kompose', '-f', self.output_filename, 'convert'], cwd=self.output_dir, capture_output=True,
#                        text=True)

#         os.remove(os.path.join(self.output_dir, self.output_filename))
