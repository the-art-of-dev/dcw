from core import DCWService, DCWEnv, DCWUnit, DCWTemplate
import yaml
from dotenv import dotenv_values
import os
import copy
import shutil
import subprocess


class DCWServicesLoader:
    def __init__(self, dirPath: str) -> None:
        self.dirPath = dirPath

    def load_dc_service(self, filename: str):
        if not filename.startswith('docker-compose.') or not filename.endswith('.yml'):
            return None

        name = filename[len('docker-compose.'):].split('.')[0]
        full_path = f"{self.dirPath}/{filename}"

        with open(full_path) as f:
            return DCWService(name, full_path, yaml.safe_load(f))

    def load_all(self):
        return list(filter(lambda x: x is not None,
                           [self.load_dc_service(filename) for filename in os.listdir(self.dirPath)]))


class DCWEnvironmentsLoader:
    def __init__(self, dirPath: str) -> None:
        self.dirPath = dirPath

    def load_env(self, filename: str):
        if not filename.startswith('.') or not filename.endswith('.env'):
            return None

        name = filename[1:].split('.')[0]
        full_path = f"{self.dirPath}/{filename}"

        return DCWEnv(name, full_path, dotenv_values(full_path))

    def load_all(self):
        return list(filter(lambda x: x is not None,
                           [self.load_env(filename) for filename in os.listdir(self.dirPath)]))


class DCWUnitLoader:
    def __init__(self, dirPath: str, services: [DCWService]) -> None:
        self.dirPath = dirPath
        self.services = services

    def load_unit(self, filename: str):
        if not filename.startswith('dcw.') or not filename.endswith('.txt'):
            return None

        name = filename[len('dcw.'):].split('.')[0]
        full_path = f"{self.dirPath}/{filename}"

        svcs = []
        with open(full_path) as f:
            for line in f:
                svc = next(filter(lambda s: s.name ==
                           line.strip(), self.services), None)
                if svc is None:
                    continue
                svcs.append(svc)

        return DCWUnit(name, full_path, copy.deepcopy(svcs))

    def load_all(self):
        return list(filter(lambda x: x is not None,
                           [self.load_unit(filename) for filename in os.listdir(self.dirPath)]))


class DCWTemplateLoader:
    def __init__(self, dirPath: str):
        self.dirPath = dirPath

    def load_template(self, filename):
        if not filename.endswith('.template'):
            return None

        name = filename[:-len('.template')]
        full_path = os.path.join(self.dirPath, filename)

        with open(full_path) as f:
            return DCWTemplate(name, full_path, f.read())

    def load_all(self):
        return list(filter(lambda x: x is not None,
                           [self.load_template(filename) for filename in os.listdir(self.dirPath)]))


class DCWUnitDockerComposeExporter:
    def __init__(self, dcw_unit, dcw_env, output_filename=None):
        self.unit_env_name = dcw_env.name if dcw_env.name.startswith(
            dcw_unit.name) else f'{dcw_unit.name}-{dcw_env.name}'

        if output_filename is None:
            output_filename = f'docker-compose.{self.unit_env_name}.yml'

        self.output_filename = output_filename
        self.dcw_unit = dcw_unit
        self.dcw_env = dcw_env

    def export(self):
        data = self.dcw_unit.render(self.dcw_env)
        data['name'] = self.unit_env_name
        with open(self.output_filename, 'w') as f:
            yaml.safe_dump(data, f)


class DCWUnitKubernetesExporter(DCWUnitDockerComposeExporter):
    def __init__(self, dcw_unit, dcw_env, output_dir=None):
        super().__init__(dcw_unit, dcw_env, None)

        self.output_dir = output_dir
        if self.output_dir is None:
            self.output_dir = f'./k8s-{self.unit_env_name}'

        self.dcw_unit = dcw_unit
        self.dcw_env = dcw_env

    def export(self):
        super().export()
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)

        shutil.move(self.output_filename, self.output_dir)
        subprocess.run(['kompose', '-f', self.output_filename, 'convert'], cwd=self.output_dir, capture_output=True,
                       text=True)

        os.remove(os.path.join(self.output_dir, self.output_filename))
