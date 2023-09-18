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

from dcw.core import DCWUnit, DCWDataContext
from dcw.config import get_config, set_config
from dcw.infra import DCWGroupFileIO, export_dc_deployment
from dcw.utils import is_tool

import enum

from dcw.logger import logger

data_context = DCWDataContext(DCWGroupFileIO())
data_context.import_group()


class DCWUnitBundleOutputType(str, enum.Enum):
    DOCKER_COMPOSE = "dc"
    KUBERNETES = "k8s"


app = typer.Typer(
    help="Docker Compose Wrapper | Depyment Configuration Wrapper",
)
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
    if name is None:
        name = radiolist_dialog(
            title="DCW Unit Bundler",
            text="Select DCW Unit",
            values=[(u.name, u.name) for u in data_context.units_group]
        ).run()

    if env is None:
        env = radiolist_dialog(
            title="DCW Unit Bundler",
            text="Select DCW Environment",
            values=[(e.name, e.name) for e in data_context.envs_group]
        ).run()

    dcw_env = data_context.envs_group[env]
    dcw_unit = data_context.units_group[name]

    if outputType == DCWUnitBundleOutputType.DOCKER_COMPOSE:
        export_dc_deployment(data_context.svcs_group,
                             dcw_env, dcw_unit, output)
    else:
        raise Exception('Not supported type')


@unit_app.command("list")
def unit_list(verbose: bool = False):
    """List all dcw units"""
    tbl = prettytable.PrettyTable()
    name_column = []
    svc_name_column = []
    for u in data_context.units_group:
        name_column.append(u.name)
        svc_name_column.append('')
        if verbose:
            for sn in u.svc_names:
                svc = data_context.svcs_group[sn]
                name_column.append('')
                svc_name_column.append(svc.name)

    tbl.add_column('UNITS', name_column)

    if verbose:
        tbl.add_column('Service name', svc_name_column)

    print(tbl)


# @unit_app.command("new")
# def unit_new(name: str = typer.Option(None, help='New unit name'),
#              filename: str = typer.Option(None, help='New unit file path'),
#              svc: Annotated[Optional[List[str]], typer.Option()] = None,
#              prompt: bool = False):
#     if name is None:
#         name = input_dialog(
#             title='New DCW unit',
#             text='Enter new DCW unit path:',
#             default=f'new-unit').run()

#     if filename is None:
#         filename = input_dialog(
#             title='New DCW unit',
#             text='Enter new DCW unit path:',
#             default=f'./dcw-units/dcw.{name}.txt').run()

#     all_services = DCWServicesLoader(get_config('DCW_SVCS_DIR')).load_all()

#     if prompt:
#         svc = checkboxlist_dialog(
#             title="New DCW unit",
#             text=f"Select services for {name} DCW unit",
#             values=[(s.name, s.name) for s in all_services],
#             default_values=svc
#         ).run()

#     services = []
#     for sn in svc:
#         s = next(filter(lambda x: x.name == sn, all_services), None)
#         if s is None:
#             raise Exception(f'Service {s} not found!')
#         services.append(s)

#     new_unit = DCWUnit(name, filename, services)
#     new_unit.save()


@svc_app.command("list")
def svc_list():
    """List all dcw services"""
    svcs = data_context.svcs_group
    tbl = prettytable.PrettyTable()
    tbl.add_column('#', [i+1 for i in range(len(svcs))])
    tbl.add_column('SERVICE', [s.name for s in svcs])
    tbl.add_column('IMAGE', [s.image for s in svcs])
    tbl.add_column('PORTS', [s.ports for s in svcs])
    print(tbl)


# @svc_app.command("new")
# def tmpl_new(tmpl_name: str = typer.Option(None, help="Template to use for creating service"),
#              tmpl_vars_file: str = typer.Option(None, help="Variables file to use for template placeholders")):
#     """List all dcw services"""
#     tmpls = DCWTemplateLoader(get_config('DCW_TMPLS_DIR')).load_all()

#     if tmpl_name is None:
#         tmpl_name = radiolist_dialog(
#             title="Show DCW Environment",
#             text="Select DCW Environment",
#             values=[(t.name, t.name) for t in tmpls]
#         ).run()

#     tmpl = next(filter(lambda x: x.name == tmpl_name, tmpls), None)

#     tmpl_vars = {}
#     if tmpl_vars_file is not None:
#         tmpl_vars = dotenv_values(tmpl_vars_file)

#     for vn in tmpl.get_variable_names():
#         if vn not in tmpl_vars:
#             tmpl_vars[vn] = input_dialog(
#                 title='New DCW templated service',
#                 text=f'Enter {vn}:').run()

#     pp.pprint(tmpl.render(tmpl_vars))


@env_app.command("list")
def env_list():
    """List all dcw environments"""
    envs = data_context.envs_group
    tbl = prettytable.PrettyTable()
    tbl.add_column('#', [i+1 for i in range(len(envs))])
    tbl.add_column('NAME', [e.name for e in envs])
    svcs = []
    for e in envs:
        esvcs = list(e.service_configs.keys())
        if len(esvcs) > 5:
            esvcs = esvcs[:5]
            esvcs.append('...')
        svcs.append(esvcs)
    tbl.add_column('SERVICES', svcs)

    print(tbl)


# @env_app.command("show")
# def env_show():
#     """List all dcw environments"""
#     envs = DCWEnvironmentsLoader(get_config('DCW_ENVS_DIR')).load_all()
#     result = radiolist_dialog(
#         title="Show DCW Environment",
#         text="Select DCW Environment",
#         values=[(e.name, e.name) for e in envs]
#     ).run()
#     env = next(filter(lambda s: s.name == result, envs), None)
#     pp.pprint(env.env_vars)


# @tmpl_app.command("list")
# def tmpl_list():
#     tmpls = DCWTemplateLoader(get_config('DCW_TMPLS_DIR')).load_all()
#     tbl = prettytable.PrettyTable()
#     tbl.add_column('Name', [t.name for t in tmpls])
#     tbl.add_column('Filename', [t.filename for t in tmpls])
#     print(tbl)


# @app.command("init")
# def init_dcw(dir: str = typer.Option(None, help="DCW directory path"),
#              examples: bool = typer.Option(False, help="Create examples while initting dcw")):

#     # check for dcw dir, if not exist create it
#     if dir is None:
#         dir = '.'

#     if not os.path.exists(dir):
#         os.makedirs(dir)

#     # init dcw-envs [with examples], hanlde errors
#     try:
#         os.makedirs(get_config('DCW_ENVS_DIR'))
#         logger.info(f'Created {get_config("DCW_ENVS_DIR")}')
#     except Exception as e:
#         logger.warning(
#             f'{get_config("DCW_ENVS_DIR")} already exists or cannot be created')

#     # init dcw-svcs [with examples], hanlde errors
#     try:
#         os.makedirs(get_config('DCW_SVCS_DIR'))
#         logger.info(f'Created {get_config("DCW_SVCS_DIR")}')
#     except Exception as e:
#         logger.warning(
#             f'{get_config("DCW_SVCS_DIR")} already exists or cannot be created')

#     # init dcw-tmpls [with examples], hanlde errors
#     try:
#         os.makedirs(get_config('DCW_TMPLS_DIR'))
#         logger.info(f'Created {get_config("DCW_TMPLS_DIR")}')
#     except Exception as e:
#         logger.warning(
#             f'{get_config("DCW_TMPLS_DIR")} already exists or cannot be created')

#     # init dcw-units [with examples], hanlde errors
#     try:
#         os.makedirs(get_config('DCW_UNITS_DIR'))
#         logger.info(f'Created {get_config("DCW_UNITS_DIR")}')
#     except Exception as e:
#         logger.warning(
#             f'{get_config("DCW_UNITS_DIR")} already exists or cannot be created')


# @app.command("check")
# def check_dcw(dir: str = typer.Option(None, help="DCW directory path"),
#               fail: bool = typer.Option(
#                   False, help="Fail application when check fails"),
#               lint: bool = typer.Option(True, help="Check files for syntax errors")):

#     # check for docker-compose/docker compose
#     if not is_tool('docker-compose'):
#         logger.error('docker-compose not found!')
#         logger.info(
#             'Please visit https://github.com/docker/compose to install docker-compose and try again.')
#         raise typer.Abort()

#     # check for kompose
#     if not is_tool('kompose'):
#         logger.error(
#             'Please visit https://github.com/kubernetes/kompose to install kompose and try again.')
#         raise typer.Abort()

#     # check for dcw-envs with syntax checking [, fail when check fails]
#     # check for dcw-svcs with syntax checking [, fail when check fails]
#     # check for dcw-tmpls with syntax checking [, fail when check fails]
#     # check for dcw-units with syntax checking [, fail when check fails]


if not os.path.exists(get_config('TMP_DIR')):
    os.makedirs(get_config('TMP_DIR'))

if __name__ == "__main__":
    app()
