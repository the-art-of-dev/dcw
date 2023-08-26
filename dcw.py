import string

import typer
import colorlog
import logging
import os
import yaml
import typing
from dotenv import dotenv_values
import subprocess
import copy
import shutil
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.shortcuts import input_dialog
import prettytable
from typing import List, Optional

from typing_extensions import Annotated
import pprint as pp
import re

import enum

# CONSTANTS
DCW_SVCS_DIR = './dcw-services'
DCW_UNITS_DIR = './dcw-units'
DCW_ENVS_DIR = './dcw-envs'
DCW_TMPLS_DIR = './dcw-tmpls'
TMP_DIR = './tmp'

# LOGGER

colorlog_fmt = "{log_color}{levelname}: {message}"
colorlog.basicConfig(level=logging.DEBUG, style="{", format=colorlog_fmt, stream=None)

logger = logging.getLogger()


# DCW SERVICES

class DCWService:
    def __init__(self, name: str, filename: str, config) -> None:
        self.name = name
        self.filename = filename
        self.config = config
        self.tmp_filename = f'{TMP_DIR}/{self.name}.yml'

        if self.name not in self.config['services']:
            raise Exception(f'Service ${filename} not valid!')

        self.save_tmp()

    def set_env_var(self, env_name: str, env_value: str):
        if not env_name.startswith(f'svc.{self.name}.environment.') and not env_name.startswith(
                f'svc.{self.name}.labels.'):
            return

        section = 'environment' if env_name.startswith(f'svc.{self.name}.environment.') else 'labels'

        print(section)

        env_name = env_name[len(f'svc.{self.name}.{section}.'):]

        if section not in self.config['services'][self.name]:
            self.config['services'][self.name][section] = {}

        self.config['services'][self.name][section][env_name] = env_value

    def set_env_vars(self, env_vars: typing.Dict[str, str]):
        for k in env_vars:
            self.set_env_var(k, env_vars[k])
        self.save_tmp()

    def save_tmp(self):
        with open(self.tmp_filename, 'w') as f:
            yaml.safe_dump(self.config, f)


class DCWEnv:
    def __init__(self, name, filename, env_vars) -> None:
        self.name = name
        self.filename = filename
        self.env_vars = {}
        self.svc_env_vars = {}
        self.tmp_filename = f'{TMP_DIR}/.{self.name}.env'

        for k in env_vars:
            if k.startswith('svc.'):
                self.svc_env_vars[k] = env_vars[k]
            else:
                self.env_vars[k] = env_vars[k]

        self.save_env_tmp()

    def save_env_tmp(self):
        with open(self.tmp_filename, 'w') as f:
            yaml.safe_dump(self.env_vars, f)

    def __str__(self) -> str:
        return f"DCWEnv(name={self.name}, filename={self.filename})"


class DCWUnit:
    def __init__(self, name, filename, services) -> None:
        self.name = name
        self.filename = filename
        self.services = services

    def __str__(self) -> str:
        return f"DCWUnit(name={self.name}, filename={self.filename}, services={self.services})"

    def render(self, dcw_env):
        dc_files = [f'-f {s.tmp_filename}' for s in self.services]
        dc_command = f"docker-compose {' '.join(dc_files)} --env-file {dcw_env.tmp_filename} convert"
        logger.info(f"Running command: {dc_command}")
        for svc in self.services:
            svc.set_env_vars(dcw_env.svc_env_vars)
        # os.system(dc_command)
        result = subprocess.run(dc_command.split(' '), capture_output=True, text=True)
        return yaml.safe_load(result.stdout)

    def save(self):
        with open(self.filename, 'w') as f:
            f.writelines([f'{s.name.strip()}\n' for s in self.services])


class DCWTemplate:
    def __init__(self, name, filename, content):
        self.name = name
        self.filename = filename
        self.content = content

    def render(self, env_vars):
        template = string.Template(self.content)
        var_names = self.get_variable_names()
        for vn in var_names:
            if vn not in env_vars:
                raise Exception(f'{vn} is not set!')

        return yaml.safe_load(template.substitute(**env_vars))

    def get_variable_names(self):
        placeholders = re.findall(r'[^$]\$\{([^}]*)\}', self.content)
        return list(set(placeholders))


# -----------------------------


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
                svc = next(filter(lambda s: s.name == line.strip(), self.services), None)
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


if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)


class DCWUnitBundleOutputType(str, enum.Enum):
    DOCKER_COMPOSE = "dc"
    KUBERNETES = "k8s"


app = typer.Typer()
svc_app = typer.Typer()
env_app = typer.Typer()
unit_app = typer.Typer()
tmpl_app = typer.Typer()
app.add_typer(svc_app, name="svc")
app.add_typer(env_app, name="env")
app.add_typer(unit_app, name="unit")
app.add_typer(tmpl_app, name="tmpl")


@unit_app.command("bundle")
def unit_bundle(
        name: str = typer.Option(None, help="Name of the unit to run"),
        env: str = typer.Option(None, help="Name of the environment to use"),
        output: str = typer.Option(None, help="Name of the output file"),
        outputType: DCWUnitBundleOutputType = typer.Option(DCWUnitBundleOutputType.DOCKER_COMPOSE,
                                                           help="Type of output bundle")):
    """Build a dcw unit"""
    envs = DCWEnvironmentsLoader(DCW_ENVS_DIR).load_all()
    svcs = DCWServicesLoader(DCW_SVCS_DIR).load_all()
    units = DCWUnitLoader(DCW_UNITS_DIR, svcs).load_all()

    if name is None:
        name = radiolist_dialog(
            title="DCW Unit Bundler",
            text="Select DCW Unit",
            values=[(u.name, u.name) for u in units]
        ).run()

    if env is None:
        env = radiolist_dialog(
            title="DCW Unit Bundler",
            text="Select DCW Environment",
            values=[(e.name, e.name) for e in envs]
        ).run()

    dcw_env = next(filter(lambda s: s.name == env, envs), None)
    dcw_unit = next(filter(lambda u: u.name == name, units), None)

    if outputType == DCWUnitBundleOutputType.DOCKER_COMPOSE:
        DCWUnitDockerComposeExporter(dcw_unit, dcw_env, output).export()
    elif outputType == DCWUnitBundleOutputType.KUBERNETES:
        DCWUnitKubernetesExporter(dcw_unit, dcw_env, output).export()
    else:
        raise Exception('Not supported type')


@unit_app.command("list")
def unit_list(verbose: bool = False):
    """List all dcw units"""
    svcs = DCWServicesLoader(DCW_SVCS_DIR).load_all()
    units = DCWUnitLoader(DCW_UNITS_DIR, svcs).load_all()
    tbl = prettytable.PrettyTable()
    name_column = []
    filename_column = []
    svc_name_column = []
    svc_filename_column = []
    for u in units:
        name_column.append(u.name)
        filename_column.append(u.filename)
        svc_name_column.append('')
        svc_filename_column.append('')
        if verbose:
            for s in u.services:
                name_column.append('')
                filename_column.append('')
                svc_name_column.append(s.name)
                svc_filename_column.append(s.filename)

    tbl.add_column('Name', name_column)
    tbl.add_column('Filename', filename_column)

    if verbose:
        tbl.add_column('Service name', svc_name_column)
        tbl.add_column('Service Filename', svc_filename_column)

    print(tbl)


@unit_app.command("new")
def unit_new(name: str = typer.Option(None, help='New unit name'),
             filename: str = typer.Option(None, help='New unit file path'),
             svc: Annotated[Optional[List[str]], typer.Option()] = None,
             prompt: bool = False):
    if name is None:
        name = input_dialog(
            title='New DCW unit',
            text='Enter new DCW unit path:',
            default=f'new-unit').run()

    if filename is None:
        filename = input_dialog(
            title='New DCW unit',
            text='Enter new DCW unit path:',
            default=f'./dcw-units/dcw.{name}.txt').run()

    all_services = DCWServicesLoader(DCW_SVCS_DIR).load_all()

    if prompt:
        svc = checkboxlist_dialog(
            title="New DCW unit",
            text=f"Select services for {name} DCW unit",
            values=[(s.name, s.name) for s in all_services],
            default_values=svc
        ).run()

    services = []
    for sn in svc:
        s = next(filter(lambda x: x.name == sn, all_services), None)
        if s is None:
            raise Exception(f'Service {s} not found!')
        services.append(s)

    new_unit = DCWUnit(name, filename, services)
    new_unit.save()


@svc_app.command("list")
def svc_list():
    """List all dcw services"""
    svcs = DCWServicesLoader(DCW_SVCS_DIR).load_all()
    tbl = prettytable.PrettyTable()
    tbl.add_column('Name', [s.name for s in svcs])
    tbl.add_column('Filename', [s.filename for s in svcs])
    print(tbl)


@svc_app.command("new")
def tmpl_new(tmpl_name: str = typer.Option(None, help="Template to use for creating service"),
             tmpl_vars_file: str = typer.Option(None, help="Variables file to use for template placeholders")):
    """List all dcw services"""
    tmpls = DCWTemplateLoader(DCW_TMPLS_DIR).load_all()

    if tmpl_name is None:
        tmpl_name = radiolist_dialog(
            title="Show DCW Environment",
            text="Select DCW Environment",
            values=[(t.name, t.name) for t in tmpls]
        ).run()

    tmpl = next(filter(lambda x: x.name == tmpl_name, tmpls), None)

    tmpl_vars = {}
    if tmpl_vars_file is not None:
        tmpl_vars = dotenv_values(tmpl_vars_file)

    for vn in tmpl.get_variable_names():
        if vn not in tmpl_vars:
            tmpl_vars[vn] = input_dialog(
                title='New DCW templated service',
                text=f'Enter {vn}:').run()

    pp.pprint(tmpl.render(tmpl_vars))


@env_app.command("list")
def env_list():
    """List all dcw environments"""
    envs = DCWEnvironmentsLoader(DCW_ENVS_DIR).load_all()
    tbl = prettytable.PrettyTable()
    tbl.add_column('Name', [e.name for e in envs])
    tbl.add_column('Filename', [e.filename for e in envs])
    print(tbl)


@env_app.command("show")
def env_show():
    """List all dcw environments"""
    envs = DCWEnvironmentsLoader(DCW_ENVS_DIR).load_all()
    result = radiolist_dialog(
        title="Show DCW Environment",
        text="Select DCW Environment",
        values=[(e.name, e.name) for e in envs]
    ).run()
    env = next(filter(lambda s: s.name == result, envs), None)
    pp.pprint(env.env_vars)


@tmpl_app.command("list")
def tmpl_list():
    tmpls = DCWTemplateLoader(DCW_TMPLS_DIR).load_all()
    tbl = prettytable.PrettyTable()
    tbl.add_column('Name', [t.name for t in tmpls])
    tbl.add_column('Filename', [t.filename for t in tmpls])
    print(tbl)


if __name__ == "__main__":
    app()