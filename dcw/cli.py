import typer
import os
# from dotenv import dotenv_values
# from prompt_toolkit.shortcuts import checkboxlist_dialog
# from prompt_toolkit.shortcuts import radiolist_dialog
# from prompt_toolkit.shortcuts import input_dialog
# import prettytable
# from typing import List, Optional

# from typing_extensions import Annotated
from pprint import pprint as pp
import yaml

# from dcw.core import DCWUnit, DCWDataContext
# from dcw.config import get_config, set_config
# from dcw.infra import DCWGroupFileIO, export_dc_deployment
# from dcw.utils import is_tool

import enum

# from dcw.logger import logger

from dcw.config import import_config_from_file, DCWMagicConfigs
from dcw.context import DCWContext
from dcw.deployment import export_deployment_configuration
import prettytable
from dcw.security import encrypt_file, decrypt_file

dcw_config = import_config_from_file('.dcwrc.yaml')
dcw_context = None

# dcw_context = DCWC


class DCWUnitBundleOutputType(str, enum.Enum):
    DOCKER_COMPOSE = "dc"
    KUBERNETES = "k8s"


app = typer.Typer(
    help="Docker Compose Wrapper",
)


@app.callback()
def main(config: str = None):
    global dcw_config, dcw_context

    if config is not None:
        dcw_config = import_config_from_file(config)

    dcw_context = DCWContext(dcw_config)


svc_app = typer.Typer()
env_app = typer.Typer()
unit_app = typer.Typer()
depl_app = typer.Typer()
# tmpl_app = typer.Typer()
app.add_typer(svc_app, name="svc")
app.add_typer(env_app, name="env")
app.add_typer(unit_app, name="unit")
app.add_typer(depl_app, name="depl")
# app.add_typer(tmpl_app, name="tmpl")


def table_print_columns(data_columns: [(str, [str])]):
    tbl = prettytable.PrettyTable()
    for (title, items) in data_columns:
        tbl.add_column(title, items)
    print(tbl)


@env_app.command("list")
def env_list():
    """List all dcw environments"""
    envs = dcw_context.environments
    table_print_columns([
        ('#', [i+1 for i in range(len(envs))]),
        ('NAME', [envs[e].name for e in envs]),
    ])

@env_app.command("encrypt")
def env_encrypt():
    env = dcw_context.environments['example-local']
    encrypt_file(yaml.safe_dump(env.as_dict()), os.path.join('example-local.crypt'), 'krka1312')

@env_app.command("decrypt")
def env_decrypt():
    print(decrypt_file(os.path.join('example-local.crypt'), 'krka1312'))


@svc_app.command("list")
def svc_list():
    """List all dcw services"""
    svcs = dcw_context.services
    table_print_columns([
        ('#', [i+1 for i in range(len(svcs))]),
        ('NAME', [s for s in svcs]),
        ('IMAGE', [svcs[s].image for s in svcs]),
        ('PORTS', [svcs[s].ports for s in svcs]),
        ('GLOBAL ENV', [svcs[s].get_global_envs() for s in svcs])
    ])


@unit_app.command("list")
def unit_list(verbose: bool = False):
    """List all dcw units"""
    table_print_columns([
        ('NAME', [u for u in dcw_context.units])
    ])


@depl_app.command("list")
def depl_list():
    depls = dcw_context.deployments
    table_print_columns([
        ('#', [i+1 for i in range(len(depls))]),
        ('NAME', [d for d in depls]),
        ('TYPE', [depls[d].type for d in depls]),
        ('(UNIT, ENV)', [depls[d].depl_paris for d in depls]),
    ])


@depl_app.command("bundle")
def depl_bundle(name: str):
    depl = dcw_context.deployments[name]
    depl_config = depl.create_deployment_config(
        dcw_context.services,
        dcw_context.environments,
        dcw_context.units
    )

    data = {d: depl_config[d].as_dict() for d in depl_config}
    export_deployment_configuration(
        dcw_context.config[DCWMagicConfigs.DCW_DEPL_CONFIGS_PATH], depl, data)


if __name__ == "__main__":
    app()
