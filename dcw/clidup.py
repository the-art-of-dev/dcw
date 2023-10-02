import typer
import os
from pprint import pprint as pp
import yaml
import enum

from dcw.config import import_config_from_file, DCWMagicConfigs
from dcw.context import DCWContext
from dcw.deployment import export_deployment_configuration, upgrade_k8s_deployment, make_k8s_deployment
import prettytable
from dcw.vault import encrypt_file, decrypt_file, read_valut_config_from_file

dcw_config = import_config_from_file('.dcwrc.yaml')
dcw_context = None

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
vault_app = typer.Typer()
app.add_typer(svc_app, name="svc")
app.add_typer(env_app, name="env")
app.add_typer(unit_app, name="unit")
app.add_typer(depl_app, name="depl")
app.add_typer(vault_app, name="vault")


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
    make_k8s_deployment(depl_config_path)
    upgrade_k8s_deployment(depl_config_path)

@vault_app.command("encrypt")
def vault_encrypt(key: str):
    vault_dir = dcw_config[DCWMagicConfigs.DCW_VAULT_PATH]
    env_dir = f'{vault_dir}/vault-envs'
    if not os.path.exists(env_dir):
        if not os.path.exists(vault_dir):
            os.makedirs(vault_dir)
        os.makedirs(env_dir)
    vault_data = read_valut_config_from_file()
    for e in vault_data.environments:
        env = yaml.safe_dump(dcw_context.environments[e].as_dict())
        encrypt_file(env, f"{env_dir}/.{e}.env.crypt", key)

@vault_app.command("decrypt")
def vault_encrypt(key: str):
    envs_dir = dcw_config[DCWMagicConfigs.DCW_ENVS_PATH]
    vault_dir = dcw_config[DCWMagicConfigs.DCW_VAULT_PATH]
    vault_data = read_valut_config_from_file()
    for e in vault_data.environments:
        with open(envs_dir + f'/{e}.test.env', "w") as file:
            pp(decrypt_file(f"{vault_dir}/vault-envs/.{e}.env.crypt", key))
            yaml.safe_dump(decrypt_file(f"{vault_dir}/vault-envs/.{e}.env.crypt", key), file)

@vault_app.command("test")
def vault_encrypt():
    pp(read_valut_config_from_file())
    

if __name__ == "__main__":
    app()
