# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import inspect
import os
from typing import Callable, List

import yaml
from dcw.core import dcw_envy_cfg, DcwContext
from dcw.envy import EnvyCmd, apply_cmd_log, dict_to_envy, get_selector_val
from pprint import pprint as pp

# --------------------------------------
#   Docs
# --------------------------------------
# region
'''Dcw Docs - handles DCW project documentation'''
NAME = name = 'docs'
SELECTOR = selector = ['docs']

# def cmd_make(ctx: DcwContext, args: dict) -> List[EnvyCmd]:
#     doc_str = ''
#     for mod in ctx.modules.values():
#         doc_str += f'## {mod.name}\n'
#         doc_str += f'{mod.description}\n'
#         doc_str += '\n'
#         doc_str += '### Commands\n'
#         doc_str += '\n'
#         doc_str += '|Name|Description|\n'
#         doc_str += '|--|--|\n'
#         for cn, cmd in mod.cmds.items():
#             doc_str += f'|`{cn}`|{cmd.__doc__}|\n'
#         doc_str += '\n'
#     with open('docs/docs.md', 'w') as f:
#         f.write(doc_str)
#     return []

# def cmd_test(s: dict, args: dict = {
#     'name': ...,
#     'type': None,
#     'cwd': '.'
# }, run: Callable = ...) -> List[EnvyCmd]:
#     pass

# spec = inspect.getfullargspec(cmd_test)
# pp(spec.defaults[0])
# endregion
