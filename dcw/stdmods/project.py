# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import os
from typing import Callable, List

import yaml
from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, EnvyState, dict_to_envy
from pprint import pprint as pp

# --------------------------------------
#   Project
# --------------------------------------
# region
__doc__ = '''Dcw Project - handles DCW project configuration'''
NAME = name = 'proj'
SELECTOR = selector = ['proj']


@dataclass
class DcwProject:
    name: str
    root: str = '.'
    cfg: dict = field(default_factory=dict)


def load_project_file(proj_file: str) -> DcwProject:
    if not os.path.exists(proj_file):
        raise Exception(f"Proj file {proj_file} doesn't exist")
    data = {}
    with open(proj_file, 'r') as f:
        data = yaml.safe_load(f)

    return DcwProject(**data)

@dcw_cmd({
    'filename': '.dcwrc.yml'
})
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    '''Loads project from .dcwrc.yml'''
    return dict_to_envy(asdict(load_project_file(args['filename'])))

@dcw_cmd()
def cmd_list(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')
    pp(state[SELECTOR])
    return []

# endregion
