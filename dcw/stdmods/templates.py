# pylint: skip-file
from __future__ import annotations
from collections import namedtuple
from dataclasses import asdict, dataclass, field
import enum
import os
from typing import Any, Callable, List

from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, selector_startswith, dict_to_envy, envy_selector, get_selector_val, apply_cmd
from pprint import pprint as pp
from dcw.utils import check_for_missing_args, render_template, template_vars, value_map_dict

# --------------------------------------
#   Templates
# --------------------------------------
# region
__doc__ = '''Dcw Templates - handles DCW templating engine'''
name = 'templs'
selector = ['templs']


@dataclass
class CustomSelector:
    prefix: List[str]
    ref_sel: List[str] = None

    def is_prefix(self, selector: List[str]) -> bool:
        return selector_startswith(selector, self.prefix, dcw_envy_cfg())


def apply_custom_selector(selector: List[str], csels: List[CustomSelector]) -> List[str]:
    for cs in csels:
        if cs.is_prefix(selector):
            return cs.ref_sel + selector
    return selector


def apply_filter_selector(sel: List[str], fsel: List[str]) -> List[str]:
    if '<i>' not in fsel:
        return fsel
    fi = fsel.index('<i>')
    if not selector_startswith(sel, fsel[:fi], dcw_envy_cfg()):
        return fsel
    return sel[:fi+1] + apply_filter_selector(sel[fi+1:], fsel[fi+1:])


@dcw_cmd({'templ': ..., 'data': ...})
def cmd_apply(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['templ', 'data'])

    templ = args['templ']
    data = args['data']
    csels = [CustomSelector(**s) for s in args.get('csels', [])]

    if not isinstance(data, dict):
        raise Exception(f'Apply template data type {type(data)} not supported.')
    envy_cfg = dcw_envy_cfg()
    templ_ecl = dict_to_envy(templ)
    diff_ecl = []
    for ecmd in templ_ecl:
        tvars = template_vars(ecmd.data)
        if tvars == []:
            continue

        tdata = {}
        for tv in tvars:
            sel = apply_custom_selector(envy_selector(tv, envy_cfg), csels)
            sel = apply_filter_selector(ecmd.selector, sel)
            tdata[tv] = get_selector_val(data, sel)

        diff_ecl.append(EnvyCmd(ecmd.selector, ecmd.op, render_template(ecmd.data, tdata)))
        data = apply_cmd(data, diff_ecl[-1], dcw_envy_cfg())
    return diff_ecl

# endregion
