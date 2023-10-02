import os
import click
from pprint import pprint as pp
import enum
from typing import List
import prettytable
import yaml

from dcw.config import import_config_from_file, DCWMagicConfigs
from dcw.context import DCWContext
from dcw.deployment import export_deployment_configuration, make_deployment, execute_deployment_command
from dcw.vault import encrypt_file, decrypt_file, read_valut_config_from_file
from dcw.environment import load_env, dump_env, export_env_to_dir

dcw_config = import_config_from_file('.dcwrc.yaml')
dcw_context: DCWContext = None


class DCWUnitBundleOutputType(str, enum.Enum):
    DOCKER_COMPOSE = "dc"
    KUBERNETES = "k8s"


@click.group()
@click.option('--config', default='.dcwrc.yaml')
def app(config: str):
    global dcw_context
    dcw_config = import_config_from_file(config)
    dcw_context = DCWContext(dcw_config)


@click.group('svc')
def svc_app():
    pass


@click.group('env')
def env_app():
    pass


@click.group('unit')
def unit_app():
    pass


@click.group('depl')
def depl_app():
    pass


@click.group('vault')
def vault_app():
    pass


app.add_command(svc_app)
app.add_command(env_app)
app.add_command(unit_app)
app.add_command(depl_app)
app.add_command(vault_app)


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

# @env_app.command("encrypt")
# def env_encrypt():
#     env = dcw_context.environments['example-local']
#     encrypt_file(yaml.safe_dump(env.as_dict()), os.path.join('example-local.crypt'), 'krka1312')

# @env_app.command("decrypt")
# def env_decrypt():
#     print(decrypt_file(os.path.join('example-local.crypt'), 'krka1312'))


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
    depl_config_path = export_deployment_configuration(
        dcw_context.config[DCWMagicConfigs.DCW_DEPL_CONFIGS_PATH], depl, data)
    make_deployment(depl_config_path)


@vault_app.command("encrypt")
@click.argument('key')
def vault_encrypt(key: str):
    vault_dir = dcw_config[DCWMagicConfigs.DCW_VAULT_PATH]
    env_dir = f'{vault_dir}/vault-envs'

    if not os.path.exists(env_dir):
        if not os.path.exists(vault_dir):
            os.makedirs(vault_dir)
        os.makedirs(env_dir)

    vault_data = read_valut_config_from_file()

    for e in vault_data.environments:
        encrypt_file(dump_env(dcw_context.environments[e]), f"{env_dir}/.{e}.env.crypt", key)


@vault_app.command("decrypt")
@click.argument('key')
def vault_decrypt(key: str):
    envs_dir = dcw_config[DCWMagicConfigs.DCW_ENVS_PATH]
    vault_dir = dcw_config[DCWMagicConfigs.DCW_VAULT_PATH]
    vault_data = read_valut_config_from_file()

    for e in vault_data.environments:
        env_file_path = os.path.join(vault_dir, 'vault-envs', f".{e}.env.crypt")
        str_data = decrypt_file(env_file_path, key)
        export_env_to_dir(envs_dir, load_env(e, str_data))

@app.command('x', context_settings={"ignore_unknown_options": True})
@click.argument('name')
@click.argument('args', nargs=-1)
def execute_depl(name: str, args: [str]):
    depl = dcw_context.deployments[name]
    execute_deployment_command(
        dcw_context.config[DCWMagicConfigs.DCW_DEPL_CONFIGS_PATH], depl, args)

# @app.command('task', context_settings={"ignore_unknown_options": True})
# @click.argument('args', nargs=-1)
# def execute_task(args: [str]):
#     execute_ansible_task('./hacking/dcw-tasks/copy_file.yaml', list(args))


if __name__ == "__main__":
    app()
