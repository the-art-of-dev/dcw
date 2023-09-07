import typer
import os
from dotenv import dotenv_values
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.shortcuts import input_dialog
import prettytable
from typing import List, Optional

from typing_extensions import Annotated
import pprint as pp

from dcw.core import DCWUnit
from dcw.config import DCW_ENVS_DIR, DCW_SVCS_DIR, DCW_UNITS_DIR, DCW_TMPLS_DIR, TMP_DIR
from dcw.infra import DCWServicesLoader, DCWEnvironmentsLoader, DCWUnitLoader, DCWTemplateLoader, DCWUnitDockerComposeExporter, DCWUnitKubernetesExporter

import enum


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
