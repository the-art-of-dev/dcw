# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Callable, List

from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, EnvyState, dict_to_envy
from dcw.utils import check_for_missing_args, raise_if, value_map_dataclass as vm_dc
from pprint import pprint as pp

# --------------------------------------
#   Artefact Registry
# --------------------------------------
# region
__doc__ = 'Dcw Tasks - handles DCW code repositories'
NAME = name = 'regs'
SELECTOR = selector = ['regs']


@dataclass
class DcwRegistry:
    name: str = ''
    type: str = ''
    url: str = ''
    username: str = ''
    password: str = ''
    _: dict = field(default_factory=dict)

@dcw_cmd()
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state = EnvyState(s, dcw_envy_cfg())
    state += run('proj', 'load')
    if state['proj.cfg.regs'] is None:
        return []

    diff = EnvyState({}, dcw_envy_cfg())
    for regname, regcfg in state['proj.cfg.regs'].items():
        diff[regname] = asdict(DcwRegistry(regname, **regcfg))
    return dict_to_envy(diff)


@dcw_cmd({'name': ...})
def cmd_install(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    reg_name = args['name']
    state = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')

    map_reg = raise_if(Exception(f'Registry {reg_name} not found.'), vm_dc(DcwRegistry))
    reg: DcwRegistry = state[f'regs.{reg_name}', map_reg]

    return run(reg.type, 'install_reg', args, False)


# endregion
