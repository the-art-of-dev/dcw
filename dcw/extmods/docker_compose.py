# pylint: skip-file
from __future__ import annotations
import copy
from dataclasses import asdict
import os
from typing import Callable, List

import yaml
from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, apply_cmd_log, dict_to_envy, get_selector_val
from dcw.stdmods.deployments import DcwDeployment
from dcw.stdmods.services import DcwService
from pprint import pprint as pp
from dcw.utils import check_for_missing_args
from old.dcw.utils import flatten

# --------------------------------------
#   Docker Compose
# --------------------------------------
# region
__doc__ = '''Dcw Docker Compose - handles docker-compose deployments'''
name = 'docker_compose'
selector = ['docker_compose']


def dict_list_to_dict(dict_list: List[str]) -> dict:
    dl_dict = {}
    for lv in dict_list:
        (lbl, val) = lv.split('=')[0], '='.join(lv.split('=')[1:])
        dl_dict[lbl] = val
    return dl_dict


def dc_svc_to_dcw_svc(name: str, dc_svc: dict) -> DcwService:
    svc = DcwService(name)
    svc.image = dc_svc.get('image', svc.image)
    svc.ports = dc_svc.get('ports', svc.ports)
    env = dc_svc.get('environment', {})
    if isinstance(dc_svc.get('environment'), list):
        env = dict_list_to_dict(env)
    svc.environment = {**env}
    # set labels
    lbls = dc_svc.get('labels', {})
    if isinstance(dc_svc.get('labels'), list):
        lbls = dict_list_to_dict(dc_svc.get('labels'))
    svc.labels = lbls
    # set networks
    svc.networks = dc_svc.get('networks', svc.networks)
    # set volumes
    svc.volumes = dc_svc.get('volumes', [])
    # set extra_hosts
    eh_list = []
    if isinstance(dc_svc.get('extra_hosts'), list):
        for eh in dc_svc.get('extra_hosts'):
            if isinstance(eh, str) and eh.find('=') != -1:
                new_eh = (eh[:eh.find('=')], eh[eh.find('=')+1:])
            elif isinstance(eh, str) and eh.find(':') != -1:
                new_eh = (eh[:eh.find(':')], eh[eh.find(':')+1:])
            else:
                raise Exception(f'EXTRA HOST "{eh}" NOT IN SUPPORTED FORMAT')

            eh_list.append(new_eh)
    svc.extra_hosts = eh_list
    return svc


def dcw_svc_to_dc_svc(svc: DcwService) -> dict:
    dc_svc = {**svc.__dict__}
    del dc_svc['name']
    del dc_svc['version']
    if svc.environment == {}:
        del dc_svc['environment']
    return dc_svc


@dcw_cmd()
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    s = apply_cmd_log(s, run('proj', 'load'), dcw_envy_cfg())
    proj_root = get_selector_val(s, ['proj', 'root'])
    svcs_root = get_selector_val(s, ['proj', 'cfg', 'svcs_root'])

    svcs_path = os.path.join(proj_root, svcs_root)
    svcs: dict[str, DcwService] = {}

    for f_name in os.listdir(svcs_path):
        f_name = str(f_name)
        if f_name.endswith('.yml'):
            with open(os.path.join(svcs_path, f_name)) as f:
                dc_files = yaml.safe_load_all(f)
                for file in dc_files:
                    file_svcs = file['services']
                    for svc_name in file_svcs:
                        svcs[svc_name] = dc_svc_to_dcw_svc(svc_name, file_svcs[svc_name])

    return dict_to_envy({sn: {**svcs[sn].__dict__} for sn in svcs})


def is_named_volume(volume: str) -> bool:
    vn = volume.split(':')[0]
    return '.' not in vn and '/' not in vn and '\\' not in vn


@dcw_cmd({'name': ..., 'output': ''})
def cmd_make(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])

    s = apply_cmd_log(s, run('proj', 'load') + run('depls', 'load'), dcw_envy_cfg())
    depl = DcwDeployment(**get_selector_val(s, ['depls', args['name']]))
    # pp(depl.svcs)
    dc_depl = {'services': {n: dcw_svc_to_dc_svc(DcwService(**svc)) for n, svc in depl.svcs.items()}, 'networks': {}}
    dc_depl['networks'] = {nn: {} for nn in set(
        flatten([dc_depl['services'][sn]['networks'] for sn in dc_depl['services']]))}

    named_volumes = filter(lambda x: x is not None, [vn if is_named_volume(
        vn) else None for vn in flatten([dc_depl['services'][sn]['volumes'] for sn in dc_depl['services']])])

    dc_depl['volumes'] = {nv.split(':')[0]: {} for nv in named_volumes}

    if args['output'] == '':
        args['output'] = f'docker-compose.{args["name"]}.yml'

    with open(args['output'], 'w') as f:
        yaml.safe_dump(dc_depl, f)

    return []


def cmd_export(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    pass


def cmd_list(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    s = apply_cmd_log(s, run('proj', 'load'), dcw_envy_cfg())
    pp(get_selector_val(s, ['proj']))
    return []

# endregion
