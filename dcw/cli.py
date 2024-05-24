# pylint: skip-file
import os
import sys
from typing import List
from dcw.core import DcwContext, DcwModule, DcwState, load_dcw_module, sys_to_dcw_module, dcw_envy_cfg
from argparse import ArgumentParser, BooleanOptionalAction
from dcw.stdmods import project, regs, scm, scripts, task_collections, tasks, services, templates, deployments, proocedures
from dcw.extmods import docker_compose, docker, jenkins
from dcw.envy import EnvyCmd, EnvyConfig
from pprint import pprint as pp

from dcw.utils import StoreDictKeyPair

proj_mod = sys_to_dcw_module(project)
task_c_mod = sys_to_dcw_module(task_collections)
tasks_mod = sys_to_dcw_module(tasks)
svcs_mod = sys_to_dcw_module(services)
docker_compose_mod = sys_to_dcw_module(docker_compose)
scripts_mod = sys_to_dcw_module(scripts)
depls_mod = sys_to_dcw_module(deployments)
scm_mod = sys_to_dcw_module(scm)
docker_mod = sys_to_dcw_module(docker)
procs_mod = sys_to_dcw_module(proocedures)
templs_mod = sys_to_dcw_module(templates)
jenkins_mod = sys_to_dcw_module(jenkins)
regs_mod = sys_to_dcw_module(regs)


def make_cmd_parser(module: DcwModule) -> ArgumentParser:
    parser = ArgumentParser(prog='dcw',
                            description='Development Configuration Wrapper Command',
                            epilog='AoD')
    subparser = parser.add_subparsers()

    for cn, cmd in module.cmds.items():
        p = subparser.add_parser(cn, help=cmd.__doc__)
        if cmd.__dict__.get('dcw_args', False):
            for k, v in cmd.__dict__['dcw_args'].items():
                if v == Ellipsis:
                    p.add_argument(f'{k}', default=v)
                elif isinstance(v, dict):
                    p.add_argument(f'--{k}', default=v, action=StoreDictKeyPair)
                else:
                    p.add_argument(f'--{k}', default=v)

    return parser


def make_mod_parser(modules: dict[str, DcwModule], add_help=False) -> ArgumentParser:
    parser = ArgumentParser(prog='dcw',
                            add_help=add_help,
                            description='Development Configuration Wrapper',
                            epilog='AoD')
    parser.add_argument('module', help='Name of the dcw module', choices=[i for i in modules])
    parser.add_argument('--DEBUG', help='Enables debug logs', default=False, type=bool, action=BooleanOptionalAction)
    parser.add_argument('--STATE', help='Prints state to stdout',
                        default=False, type=bool, action=BooleanOptionalAction)
    parser.add_argument('--STATECTX', help='Prints state with _ctx to stdout',
                        default=False, type=bool, action=BooleanOptionalAction)
    parser.add_argument('--LOG', help='Prints envy log to stdout',
                        default=False, type=bool, action=BooleanOptionalAction)
    return parser


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def selector_to_str_colored(selector: List[str], cfg: EnvyConfig) -> str:
    tokens = [cfg.sel_start, cfg.sel_end, cfg.prop_delim]
    result = []
    for s in selector:
        if any([t in s for t in tokens]):
            result.append(bcolors.BOLD + bcolors.OKBLUE + cfg.sel_start + bcolors.ENDC + bcolors.ENDC + bcolors.OKCYAN +
                          s + bcolors.ENDC + bcolors.BOLD + bcolors.OKBLUE + cfg.sel_end + bcolors.ENDC + bcolors.ENDC)
        else:
            result.append(bcolors.BOLD + bcolors.OKCYAN + s + bcolors.ENDC + bcolors.ENDC)
    return f'{bcolors.FAIL}.{bcolors.ENDC}'.join(result)


def cmd_to_stdout(cmd: EnvyCmd, cfg: EnvyConfig):
    return selector_to_str_colored(cmd.selector, cfg) + bcolors.OKGREEN + cmd.op + bcolors.ENDC + '=' + bcolors.WARNING + cmd.data + bcolors.ENDC


def load_custom_mods() -> List[DcwModule]:
    if not os.path.exists('modules'):
        return []
    mods = []
    for filename in os.listdir('modules'):
        if filename.endswith('.py'):
            mods.append(load_dcw_module('modules.'+filename.removesuffix('.py'),
                        os.path.abspath(os.path.join('modules', filename))))
    return mods


def app():
    ctx = DcwContext(state=DcwState([], {}), modules={
        proj_mod.name: proj_mod,
        task_c_mod.name: task_c_mod,
        tasks_mod.name: tasks_mod,
        scripts_mod.name: scripts_mod,
        svcs_mod.name: svcs_mod,
        docker_compose_mod.name: docker_compose_mod,
        depls_mod.name: depls_mod,
        scm_mod.name: scm_mod,
        docker_mod.name: docker_mod,
        procs_mod.name: procs_mod,
        templs_mod.name: templs_mod,
        jenkins_mod.name: jenkins_mod,
        regs_mod.name: regs_mod
    })

    for cm in load_custom_mods():
        ctx.modules[cm.name] = cm

    parser = make_mod_parser(ctx.modules, len(list(filter(lambda x: not x.startswith('-'), sys.argv))) < 2)
    args, rest_args = parser.parse_known_args()
    ctx.debug = args.DEBUG
    cmd_parser = make_cmd_parser(ctx.modules[args.module])
    if rest_args == []:
        cmd_parser.print_help()
        sys.exit(-1)
    cmd = rest_args[0]
    cmd_args, _ = cmd_parser.parse_known_args(rest_args)
    ctx.run(args.module, cmd, cmd_args.__dict__)
    if args.STATE:
        pp({**ctx.state.data, '_ctx': '...'})
    elif args.STATECTX:
        pp(ctx.state.data)
    if args.LOG:
        ecfg = dcw_envy_cfg()
        print('\n'.join([cmd_to_stdout(c, ecfg) for c in ctx.state.envy_log]))


if __name__ == '__main__':
    app()
