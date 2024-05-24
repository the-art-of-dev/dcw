# pylint: skip-file

import argparse
import itertools
import re
from typing import Callable, List
from functools import reduce


def value_map_dict(ktype: Callable, vtype: Callable):
    def map_val(d: dict):
        if not isinstance(d, dict):
            return d
        return {ktype(k): vtype(**v) for k, v in d.items()}
    return map_val


def value_map_list(vtype: Callable):
    def map_val(d: list):
        if not isinstance(d, list):
            return d
        return [vtype(**x) if isinstance(x, dict) else vtype(x) for x in d]
    return map_val


def value_map_dataclass(dctype: Callable):
    def map_val(any):
        if not isinstance(any, dict):
            return dctype(any)
        return dctype(**any)
    return map_val


def default_val(val):
    def check_val(any):
        if any == None:
            return val
        return any
    return check_val


def raise_if(ex, vm_f: Callable, val=None):
    def check_val(any):
        if any == val:
            raise ex
        return vm_f(any)
    return check_val


def missing_args(args: dict, arg_names: List[str]) -> List[str]:
    return list(filter(lambda an: an not in args or args[an] == Ellipsis, arg_names))


def check_for_missing_args(args: dict, arg_names: List[str]):
    missing = missing_args(args, arg_names)
    if missing != []:
        raise Exception(f'Missing arguments {missing}.')


def flatten(list_of_lists):
    return list(itertools.chain.from_iterable(list_of_lists))


def flat_map(f, xs): return reduce(lambda a, b: a + b, map(f, xs))


def str_to_bool(val: str) -> bool:
    return val.title() == 'True'


def template_vars(text: str):
    placeholders = re.findall(r'\$\{([^}]*)\}', text)
    return list(set(placeholders))


def render_template(text: str, data: dict):
    tvars = template_vars(text)
    for tv in tvars:
        if tv not in data or data[tv] == None:
            raise Exception(f'Template varialbe {tv} not found!')
        text = text.replace('${' + tv + '}', data.get(tv, '${' + tv + '}'))
    return text

    # template = string.Template(text)
    # return template.safe_substitute(data)


def is_false(any):
    return any in [None, ..., '', False, 'False', 'false']


class StoreDictKeyPair(argparse.Action):
     def __call__(self, parser, namespace, values, option_string=None):
         my_dict = {}
         for kv in values.split(","):
             k,v = kv.split("=")
             my_dict[k] = v
         setattr(namespace, self.dest, my_dict)