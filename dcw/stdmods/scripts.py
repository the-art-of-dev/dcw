# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import os
from typing import Callable, List

import yaml
from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, EnvyState, apply_cmd_log, dict_to_envy, str_to_envy, get_selector_val
from pprint import pprint as pp
from dcw.utils import check_for_missing_args

# --------------------------------------
#   Envys
# --------------------------------------
# region
__doc__ = '''Dcw Envys - handles enironments as envy scripts'''
NAME = name = 'scripts'
SELECTOR = selector = ['scripts']


@dataclass
class DcwScript:
    name: str
    envy_log: List[EnvyCmd] = field(default_factory=list)


def load_script(proj_root: str, scripts_root: str, name: str) -> DcwScript:
    with open(os.path.join(proj_root, scripts_root, f'.{name}.env'), 'r') as f:
        return DcwScript(name, str_to_envy(f.read(), dcw_envy_cfg()))


def load_script(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    # Asumes that proj is loaded
    envy_cfg = dcw_envy_cfg()
    check_for_missing_args(args, ['filename'])
    state = EnvyState(s, envy_cfg)

    filename: str = os.path.join(state['proj.root'], state['proj.cfg.scripts_root'], args['filename'])
    name = next(filter(lambda x: x != '', args['filename'].split('.')), None)

    if name is None:
        raise Exception(f'Unsupported filename {args["filename"]}')

    diff = EnvyState({}, envy_cfg)

    with open(filename, 'r') as f:
        diff[name] = asdict(DcwScript(name, str_to_envy(f.read(), envy_cfg)))

    return dict_to_envy(diff)


@dcw_cmd()
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state: EnvyState = EnvyState(s, dcw_envy_cfg()) + run('proj', 'load')

    scripts_root = os.path.join(state['proj.root'], state['proj.cfg.scripts_root'])
    allowed_scripts = state['proj.cfg.allowed_scripts']
    out_ecl = []

    for file_name in os.listdir(scripts_root):
        file_name: str = os.path.basename(file_name)
        if any([file_name.endswith(ext) for ext in allowed_scripts]):
            out_ecl += load_script(state.state, {'filename': file_name}, run)

    return out_ecl


@dcw_cmd()
def cmd_list(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state: EnvyState = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')
    pp([n for _, n in state['scripts.*.name']])
    return []


# endregion
