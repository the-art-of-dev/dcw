# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Callable, List

from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, EnvyState, dict_to_envy, is_envy_log, prepand_selector
from dcw.utils import check_for_missing_args, value_map_list, raise_if, value_map_dataclass as vm_dc
from dcw.stdmods.services import DcwService
from pprint import pprint as pp

# --------------------------------------
#   Deployments
# --------------------------------------
# region
__doc__ = '''Dcw Deployments - source of services'''
NAME = name = 'depls'
SELECTOR = selector = ['depls']


@dataclass
class DcwDeployment:
    name: str
    envs: List[str] = field(default_factory=list)
    url: str = ''
    type: str = 'docker_compose'
    services: List[str] = field(default_factory=list)
    service_groups: List[str] = field(default_factory=list)
    tasks: dict[str, dict] = field(default_factory=dict)
    svcs: dict[str, dict] = field(default_factory=dict)

    def maker(self) -> str:
        return self.type.replace('-', '_')


def not_found_ex(name: str) -> Exception:
    return Exception(f'Deployment {name} not found.')


def cfg_to_depl(name: str, cfg: dict) -> DcwDeployment:
    return DcwDeployment(
        name=name,
        **cfg
    )


def val_map_depl(depl_name: str):
    return raise_if(not_found_ex(depl_name), vm_dc(DcwDeployment))


def val_map_depls(d: dict):
    return {dn: cfg_to_depl(dn, dc) for dn, dc in d.items()}


def load_from_cfg(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    s = EnvyState(s, dcw_envy_cfg()) + run('proj', 'load')
    depls_cfg: dict[str, DcwDeployment] = s['proj.cfg.depls', val_map_depls]
    return dict_to_envy({dn: asdict(dcfg) for dn, dcfg in depls_cfg.items()})


def make_depl_svcs(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    # Asumes that deployments are loaded
    # Asumes that services are loaded
    check_for_missing_args(args, ['name'])
    envy_cfg = dcw_envy_cfg()
    state = EnvyState(s, envy_cfg)
    depl_name = args['name']
    depl: DcwDeployment = state[f'depls.{depl_name}', vm_dc(DcwDeployment)]

    diff = EnvyState({}, envy_cfg)

    for depl_svc_name in depl.services:
        svcs = state[f'svcs.{depl_svc_name}']
        if not isinstance(svcs, list):
            svcs = [svcs]
        else:
            svcs = [svc for _, svc in svcs]
        svcs: List[DcwService] = [DcwService(**svc) for svc in svcs]

        for svc in svcs:
            diff[f'{depl.name}.svcs.{svc.name}'] = svc.__dict__

    return dict_to_envy(diff)


def assing_svcs(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    # asumes that depls are loaded
    state: EnvyState = EnvyState(s, dcw_envy_cfg()) + run('svcs', 'load')

    out_ecl = []
    for depl_name in state['depls']:
        diff_log = make_depl_svcs(state.state, {'name': depl_name}, run)
        out_ecl += diff_log
        state += diff_log

    return out_ecl


def apply_scripts(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    # asumes that depls are loaded
    state = EnvyState(s, dcw_envy_cfg()) + run('scripts', 'load')
    out_ecl = []
    for depl in state['depls'].values():
        for en in depl['envs']:
            ecl = state[f'scripts.{en}.envy_log', value_map_list(EnvyCmd)]
            if not is_envy_log(ecl):
                raise Exception(f'Script {en} not found for deployment {depl["name"]}.')
            ecl = prepand_selector(ecl, [depl['name']])
            out_ecl += ecl
    return out_ecl


def apply_templates(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    # asumes that depls are loaded
    envy_cfg = dcw_envy_cfg()
    state: EnvyState = EnvyState(s, envy_cfg)
    out_ecl = []
    diff = EnvyState(state['depls'], envy_cfg)
    for dn in state['depls']:
        diff_log = prepand_selector(run('templs', 'apply', {
            'templ': {**diff[dn]},
            'data': {**diff[dn]}
        }, False), [dn])

        diff += diff_log
        out_ecl += diff_log
    return out_ecl


@dcw_cmd()
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state = EnvyState(s, dcw_envy_cfg())
    out_ecl = []

    pipeline = [load_from_cfg, assing_svcs, apply_scripts, apply_templates]

    for step in pipeline:
        diff_ecl = step(state.state, args, run)
        out_ecl += diff_ecl
        state += prepand_selector(diff_ecl, SELECTOR)

    return out_ecl


@dcw_cmd()
def cmd_list(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')
    pp(state['depls'])
    return []


@dcw_cmd({'name': ..., 'output': ''})
def cmd_make(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    depl_name = args['name']
    state = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')
    depl: DcwDeployment = state[f'depls.{depl_name}', val_map_depl(depl_name)]
    return run(depl.maker(), 'make', args)


@dcw_cmd({'name': ..., 'depl_name': ...})
def cmd_build_svc(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['depl_name', 'name'])
    svc_name = args['name']
    depl_name = args['depl_name']

    state: EnvyState = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')
    map_svc = raise_if(Exception(f'Servivce {svc_name} not found in deployment {depl_name}.'), vm_dc(DcwService))
    svc: DcwService = state[f'depls.{depl_name}.svcs.{svc_name}', map_svc]

    builder_cfg = svc.builder_cfg()

    if builder_cfg is None or builder_cfg.type == 'depls':
        raise Exception(f'Build config for service {svc.name}, not found.')

    return run(builder_cfg.type, 'build_svc', args)


@dcw_cmd()
def cmd_deploy(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    return []


@dcw_cmd()
def cmd_rollback(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    return []

# endregion
