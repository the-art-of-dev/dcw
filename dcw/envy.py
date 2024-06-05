# pylint: skip-file
from __future__ import annotations
from dataclasses import dataclass, field
from functools import reduce
import re
from typing import Callable, List, Tuple, Any
import enum
from pprint import pprint as pp
import copy

from dcw.utils import flat_map

'''

Envy Command can be applied on the object like state to perform simple state changing operations.

Format:

env_name=value

env_name -> 
    Represents command

    COMMAND ~REGEX: ([SEL] | SEL)(.[SEL] | .SEL)*(OP)?
        [SEL] -> object property name that can cotain '.' and properly closed '[' and ']'
        SEL -> object property name
        . -> object property accessor
        OP -> optional operation, if not specified equals to DEFAULT_OP

value -> 
    Value can be interpreted differently based on the command applied on it and it's always stored as string
'''

# --------------------------------------
#   Envy Command Operations
# --------------------------------------


class EnvyStdOp(str, enum.Enum):
    SET_STR = ''        # sets data as str
    SET_LIST = '@'      # sets list from str splited by delimiter
    ADD_STR = '+'       # adds str to existing value
    APPEND = '@+'       # extends list with elements from str splited by delimiter
    REMOVE = '@-'       # removes elements from list
    UNSET = '!'         # deletes field
    NOOP = '_'          # no operation
    SET_STR_FILTERED = '%'  # uses set_filter_selector_val


@dataclass
class EnvyCmd:
    selector: List[str]
    op: str
    data: str


def match_filter(target: str, filter: str) -> bool:
    filter = filter.replace('*', '\\S+')
    regex = re.compile(rf'^{filter}$')
    return regex.match(target)


def match_selected_fields(d, sel: str) -> List[str]:
    if not isinstance(d, dict):
        return []
    fields = []
    for k in d:
        if match_filter(k, sel):
            fields.append(k)
    return fields


def list_to_dict(l: List) -> dict:
    return {f'<{i}>': l[i] for i in range(len(l))}


def dict_to_list(d: dict) -> List:
    return [d[f'<{k}>'] for k in sorted([int(i.strip('<>')) for i in d.keys()])]


def convert_to_lists(state: dict) -> dict | List:
    if not isinstance(state, dict):
        return state
    if is_dict_list(state):
        state = {k: convert_to_lists(state[k]) for k in state}
        return dict_to_list(state)
    return {k: convert_to_lists(state[k]) for k in state}


def convert_to_dicts(state: dict | List) -> dict:
    if not isinstance(state, dict) and not isinstance(state, list):
        return state
    if isinstance(state, list):
        state = [convert_to_dicts(x) for x in state]
        state = list_to_dict(state)
    return {k: convert_to_dicts(state[k]) for k in state}


def is_dict_list(d: dict) -> bool:
    if not isinstance(d, dict):
        return False
    return reduce(lambda x, y: x and y.startswith('<') and y.endswith('>') and y.strip('<>').isdigit(), d.keys(), True)


def get_selector_val(state: dict, selector: List[str], map_val: Callable = None) -> Any:
    ref = state

    for s in selector:
        if s == '<last>' and is_dict_list(s):
            ref = ref.get(sorted(ref.keys()).pop())
        elif isinstance(ref, dict) and ref.get(s) is not None:
            ref = ref.get(s)
        else:
            return None

    ref = convert_to_lists(ref)
    if map_val is None:
        return ref
    return map_val(ref)


def filter_to_selectors(ref: dict, envy_filter: List[str], selector: List[str]) -> List[List[str]]:
    if envy_filter == []:
        return [selector]

    if ref == None:
        ref = {}

    fields = match_selected_fields(ref, envy_filter[0])
    sels = list(map(lambda f: [*selector, f], fields))

    if sels == []:
        sels = [[*selector, envy_filter[0]]]

    return list(flat_map(lambda s: filter_to_selectors(ref.get(s[-1], None), envy_filter[1:], s), sels))


def get_filter_selector_val(state: dict, fselector: List[str]) -> List[Tuple[List[str], Any]]:
    return list(map(lambda s: (s, get_selector_val(state, s)), filter_to_selectors(state, fselector, [])))


def set_selector_val(state: dict, selector: List[str], val: Any) -> dict:
    state_c = copy.deepcopy(state)
    ref = state_c
    for s in selector[:-1]:
        if not isinstance(ref, dict):
            ref = {}
        if s == '<last>' and is_dict_list(ref):
            ref = ref.get(sorted(ref.keys()).pop())
        elif ref.get(s) is not None:
            ref = ref.get(s)
        else:
            ref[s] = {}
            ref = ref.get(s)
    sel = selector[-1]
    if selector[-1] == '<last>' and is_dict_list(ref):
        sel = sorted(ref.keys()).pop()
    ref[sel] = convert_to_dicts(val)
    if val is None:
        del ref[sel]
    return state_c


def set_filter_selector_val(state: dict, fselector: List[str], val: Any) -> dict:
    sels = filter_to_selectors(state, fselector, [])
    if sels == []:
        raise Exception('No selectors found!')
    return reduce(lambda x, y: set_selector_val(x, y, val), sels, state)


def cmd_add_str(state: dict, selector: List[str], data: str) -> dict:
    return set_selector_val(state, selector, get_selector_val(state, selector) + data)


def cmd_set_str(state: dict, selector: List[str], data: str) -> dict:
    return set_selector_val(state, selector, data)


def cmd_unset(state: dict, selector: List[str], data: str = '') -> dict:
    return set_selector_val(state, selector, None)


def cmd_set_list(state: dict, selector: List[str], data: str) -> dict:
    ls = data.strip().split(',') if data.strip() != '' else []
    return set_selector_val(state, selector, [x.strip() for x in ls])


def cmd_list_add(state: dict, selector: List[str], data: str) -> dict:
    if selector == []:
        return data
    si = -1
    if '<>' in selector:
        si = selector.index('<>')
        ls = selector[:si]
        l: List = get_selector_val(state, ls)
        if l == None:
            l = []
        l.append(cmd_list_add({}, selector[si+1:], data))
        return set_selector_val(state, ls, l)

    return set_selector_val(state, selector, data)


def cmd_list_rm(state: dict, selector: List[str], data: str) -> dict:
    rm_items = list(map(lambda x: x.strip(), data.split(',')))
    return set_selector_val(state,
                            selector,
                            [x for x in get_selector_val(state, selector) if x not in rm_items])


def cmd_noop(state: dict, selector: List[str], data: str) -> dict:
    return state


def cmd_set_filter_str(state: dict, selector: List[str], data: str) -> dict:
    return set_filter_selector_val(state, selector, data)


def envy_std_ops() -> dict:
    return {
        f'{EnvyStdOp.SET_STR.value}': cmd_set_str,
        f'{EnvyStdOp.SET_LIST.value}': cmd_set_list,
        f'{EnvyStdOp.ADD_STR.value}': cmd_add_str,
        f'{EnvyStdOp.APPEND.value}': cmd_list_add,
        f'{EnvyStdOp.REMOVE.value}': cmd_list_rm,
        f'{EnvyStdOp.UNSET.value}': cmd_unset,
        f'{EnvyStdOp.NOOP.value}': cmd_noop,
        f'{EnvyStdOp.SET_STR_FILTERED.value}': cmd_set_filter_str,
    }


@dataclass
class EnvyConfig:
    cmd_delim: str = '\n'
    cmd_prefix: str = 'envy.'
    sel_start: str = '['
    sel_end: str = ']'
    prop_delim: str = '.'
    default_op: str = ''
    default_sel: List[str] = field(default_factory=lambda: ['_'])
    operations: dict[str, Callable[[dict, List[str], str], dict]] = field(default_factory=envy_std_ops)


def envy_op(cmd: str, cfg: EnvyConfig) -> str:
    op_ordered = sorted(cfg.operations.keys(), key=lambda x: len(x), reverse=True)
    for op in op_ordered:
        if cmd.endswith(op):
            return op
    return cfg.default_op


def envy_selector(cmd: str, cfg: EnvyConfig) -> List[str]:
    cmd = cmd.removeprefix(cfg.cmd_prefix)
    op = envy_op(cmd, cfg)
    cmd = cmd.removesuffix(op)
    selector = []

    prop = ''
    flat_chksum = 0

    def flat():
        return flat_chksum > 0

    for i in range(len(cmd)):
        if cmd[i] not in [cfg.sel_start, cfg.sel_end, cfg.prop_delim]:
            prop += cmd[i]
            continue

        if cmd[i] == cfg.prop_delim and not flat():
            selector.append(prop)
            prop = ''
            continue

        if cmd[i] == cfg.sel_start and not flat():
            flat_chksum += 1
            continue

        if cmd[i] == cfg.sel_end and not flat():
            raise Exception('flat selector error')

        if cmd[i] == cfg.sel_start:
            flat_chksum += 1
        elif cmd[i] == cfg.sel_end:
            flat_chksum -= 1

        if flat():
            prop += cmd[i]

    if prop != '':
        selector.append(prop)

    return selector


def selector_to_str(selector: List[str], cfg: EnvyConfig) -> str:
    tokens = [cfg.sel_start, cfg.sel_end, cfg.prop_delim]
    result = []
    for s in selector:
        if any([t in s for t in tokens]):
            result.append(f'{cfg.sel_start}{s}{cfg.sel_end}')
        else:
            result.append(s)
    return '.'.join(result)


def cmd_to_str(cmd: EnvyCmd, cfg: EnvyConfig) -> str:
    return selector_to_str(cmd.selector, cfg) + cmd.op + '=' + cmd.data


def apply_cmd(state: dict, cmd: EnvyCmd, cfg: EnvyConfig) -> dict:
    if cmd.op not in cfg.operations:
        raise Exception(f'Envy operation {cmd.op} not found.')
    return cfg.operations[cmd.op](state, cmd.selector, cmd.data)


def apply_cmd_log(state: dict, cmd_log: List[EnvyCmd], cfg: EnvyConfig) -> dict:
    return reduce(lambda x, y: apply_cmd(x, y, cfg), cmd_log, state)


def prepand_selector(envy_log: List[EnvyCmd], selector: List[str]) -> List[EnvyCmd]:
    return [EnvyCmd(selector + c.selector, c.op, c.data) for c in envy_log]


def selector_startswith(selector: List[str], prefix: List[str], cfg: EnvyConfig) -> bool:
    return selector_to_str(selector, cfg).startswith(selector_to_str(prefix, cfg))


def is_filter_selector(selector: str | List[str], cfg: EnvyConfig) -> bool:
    if isinstance(selector, str):
        selector = envy_selector(selector, cfg)
    return any('*' in s for s in selector)


def is_envy_log(obj: Any) -> bool:
    return isinstance(obj, list) and all([isinstance(li, EnvyCmd) for li in obj])


class EnvyState:
    def __init__(self, state: dict | List, cfg: EnvyConfig) -> None:
        self.state = convert_to_dicts(state)
        self.cfg = cfg

    def __getitem__(self, selector: Any) -> Any | List[Any]:
        map_val = None
        if isinstance(selector, tuple):
            selector, map_val = selector
        if isinstance(selector, str):
            selector = envy_selector(selector, self.cfg)
        if is_filter_selector(selector, self.cfg):
            return get_filter_selector_val(self.state, selector)

        return get_selector_val(self.state, selector, map_val)

    def __setitem__(self, selector:  Any, value: Any):
        if isinstance(selector, str):
            selector = envy_selector(selector, self.cfg)
        if is_filter_selector(selector, self.cfg):
            self.state = set_filter_selector_val(self.state, selector, value)
        else:
            self.state = set_selector_val(self.state, selector, value)
        return EnvyState(self.state, self.cfg)

    def __add__(self, obj: Any) -> EnvyState:
        if is_envy_log(obj):
            self.state = apply_cmd_log(self.state, obj, self.cfg)
        return EnvyState(self.state, self.cfg)


def str_to_envy(input: str, cfg: EnvyConfig) -> List[EnvyCmd]:
    lines = list(filter(lambda x: '=' in x, [s.strip() for s in input.split(cfg.cmd_delim)]))
    cmds = []

    for l in lines:
        k = l.split('=')[0]
        v = '='.join(l.split('=')[1:])
        if not k.startswith(cfg.cmd_prefix):
            cmds.append(EnvyCmd(
                selector=cfg.default_sel + [k],
                op=cfg.default_op,
                data=f'{v}'
            ))
        else:
            cmds.append(EnvyCmd(
                op=envy_op(k, cfg),
                selector=envy_selector(k, cfg),
                data=f'{v}'
            ))
    return cmds


def dict_to_envy(input: dict, selector: List[str] = None) -> List[EnvyCmd]:
    if isinstance(input, EnvyState):
        input = input.state
    if selector == None:
        selector = []
    cmds: List[EnvyCmd] = []
    input = convert_to_dicts(input)
    for k in input.keys():
        curr_sel = [*selector, k]
        if isinstance(input[k], dict):
            cmds.extend(dict_to_envy(input[k], curr_sel))
        else:
            cmds.append(EnvyCmd(
                selector=curr_sel,
                op=EnvyStdOp.SET_STR.value,
                data=f'{input[k]}'
            ))
    return cmds
