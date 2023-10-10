# pylint: skip-file
import os
import click
from pprint import pprint as pp
from logger import logger as lgg
from dcw.context import DCWContext, import_dcw_context
from dcw.service import map_service_groups
from dcw.environment import DCWEnvMagicSettingType
from dcw.deployment import DCWDeploymentSpecificationType
from dcw.deployment import make_deployment_specifications
from dcw.deployment import export_deployment_spec
from dcw.deployment import DCWDeploymentMaker
from dcw.std import DockerComposeDeploymentMaker, K8SDeploymentMaker
from dcw.utils import table_print_columns
import sys


# Init deployment makers
DockerComposeDeploymentMaker()
K8SDeploymentMaker()

# Define cli application


@click.group()
@click.option('--config', default='.dcwrc.yaml')
def app(config: str):
    import_dcw_context(config)

# ------ SERVICES ------


@click.group('svc')
def svc_app():
    pass


app.add_command(svc_app)


@svc_app.command("list")
def svc_app_list():
    """List all dcw services"""
    dcw_ctx = DCWContext()
    svcs = sorted(dcw_ctx.services.values(), key=lambda s: s.name)
    table_print_columns([
        ('#', [i+1 for i in range(len(svcs))]),
        ('NAME', [s.name for s in svcs]),
        ('GROUPS', [s.groups for s in svcs]),
        ('IMAGE', [s.image for s in svcs]),
        ('PORTS', [s.ports for s in svcs]),
        ('GLOBAL ENV', [s.get_global_envs() for s in svcs])
    ])


@svc_app.command("show")
@click.argument("svc_name", nargs=1)
def svc_app_show(svc_name: str):
    """Prints service structure"""
    dcw_ctx = DCWContext()
    if svc_name not in dcw_ctx.services:
        lgg.error(f'Service {svc_name} not found.')
        sys.exit(-1)
    svc = dcw_ctx.services[svc_name]
    pp(svc.as_dict())


@svc_app.command("args")
@click.argument("svc_names", nargs=-1)
def svc_app_args(svc_names: [str]):
    """Lists all service arguments"""
    dcw_ctx = DCWContext()
    for sn in svc_names:
        if sn not in dcw_ctx.services:
            lgg.error(f'Service {sn} not found.')
            sys.exit(-1)

    svc_args = set()

    for sn in svc_names:
        svc = dcw_ctx.services[sn]
        svc_args.update(svc.get_global_envs())

    table_print_columns([
        ('#', [i+1 for i in range(len(svc_args))]),
        ('NAME', [i for i in sorted(list(svc_args))]),
    ])


# ------ ENVIRONMENT ------


@click.group('env')
def env_app():
    pass


app.add_command(env_app)


@env_app.command("list")
def env_app_list():
    """List all dcw environments"""
    dcw_ctx = DCWContext()
    envs = sorted(dcw_ctx.environments.values(), key=lambda e: e.name)
    table_print_columns([
        ('#', [i+1 for i in range(len(envs))]),
        ('NAME', [e.name for e in envs]),
        ('SERVICES', [e.services for e in envs]),
        ('SERVICE GROUPS', [e.svc_groups for e in envs]),
    ])


@env_app.command("show")
@click.argument("env_name", nargs=1)
def env_app_show(env_name: str):
    """Prints environment structure"""
    dcw_ctx = DCWContext()
    if env_name not in dcw_ctx.environments:
        lgg.error(f'Environment {env_name} not found.')
        sys.exit(-1)
    env = dcw_ctx.environments[env_name].as_dict()
    is_dcw_magic = []
    for en in env:
        is_dm = ''
        for dmst in DCWEnvMagicSettingType:
            if en.startswith(dmst.value):
                is_dm = '*'
                break
        is_dcw_magic.append(is_dm)

    table_print_columns([
        ('#', [i+1 for i in range(len(env))]),
        ('NAME', [en for en in env]),
        ('VALUE', [env[en] for en in env]),
        ('DCW MAGIC', is_dcw_magic),
    ])

# ------ SERVICE GROUP ------


@click.group('group')
def group_app():
    pass


app.add_command(group_app)


@group_app.command("list")
def group_app_list(verbose: bool = False):
    """List all dcw units"""
    dcw_ctx = DCWContext()
    svc_groups = sorted(map_service_groups(
        dcw_ctx.services).values(), key=lambda sg: sg.name)

    table_print_columns([
        ('#', [i+1 for i in range(len(svc_groups))]),
        ('NAME', [sg.name for sg in svc_groups]),
        ('SERVICES', [sg.services for sg in svc_groups])
    ])

# ------ DEPLOYMENT ------


@click.group('depl')
def depl_app():
    pass


app.add_command(depl_app)


@depl_app.command('make-spec')
@click.argument('env_name', nargs=1)
@click.option('--spec-type', default='FULL')
@click.option('--out', default=None)
def depl_app_make(env_name: str, spec_type: str, out: str):
    specs = make_deployment_specifications(env_name, spec_type, DCWContext())
    for s in specs:
        if out is None:
            pp(s.as_dict())
        elif spec_type == DCWDeploymentSpecificationType.FULL:
            export_deployment_spec(out, s)
        else:
            export_deployment_spec(os.path.join(out, f'{s.name}.yml'), s)


@depl_app.command('make')
@click.argument('env_name', nargs=1)
@click.option('--spec-type', default='FULL')
@click.option('--depl-type', default='std.docker-compose')
@click.option('--out', default=None)
def depl_app_make(env_name: str, spec_type: str, depl_type: str, out: str):
    specs = make_deployment_specifications(env_name, spec_type, DCWContext())
    for s in specs:
        if spec_type == DCWDeploymentSpecificationType.FULL and out is None:
            DCWDeploymentMaker.make_deployment(depl_type, s, f'{s.name}.yml')
        elif spec_type == DCWDeploymentSpecificationType.FULL:
            DCWDeploymentMaker.make_deployment(depl_type, s, out)
        else:
            DCWDeploymentMaker.make_deployment(
                depl_type, s, os.path.join(out, f'{s.name}.yml'))


# @env_app.command("encrypt")
# def env_encrypt():
#     env = dcw_context.environments['example-local']
#     encrypt_file(yaml.safe_dump(env.as_dict()), os.path.join('example-local.crypt'), 'krka1312')

# @env_app.command("decrypt")
# def env_decrypt():
#     print(decrypt_file(os.path.join('example-local.crypt'), 'krka1312'))

if __name__ == "__main__":
    app()
