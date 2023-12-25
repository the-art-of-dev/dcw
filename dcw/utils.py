# pylint: skip-file
import collections
import re
import string
import itertools

import prettytable

def str_to_bool(val: str) -> bool:
    return val.title() == 'True'

def template_env_vars(text: str):
    placeholders = re.findall(r'[^$]\$\{([^}]*)\}', text)
    return list(set(placeholders))

def render_template(text:str, env_vars: dict):
    template = string.Template(text)
    return template.safe_substitute(env_vars)

def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    from shutil import which

    return which(name) is not None


def flatten(list_of_lists):
    return list(itertools.chain.from_iterable(list_of_lists))


def flatten_dict(dd: dict, separator='_', prefix='') -> dict:
    res = {}
    for key, value in dd.items():
        if isinstance(value, dict):
            res.update(flatten_dict(
                value, separator, prefix + key + separator))
        else:
            res[prefix + key] = value
    return res


def dot_env_to_dict(env_name: str, env_val=None, last_flat_key: str = None) -> dict:
    keys = env_name.split('.')
    stack = []
    current_dict = {}

    if len(keys) == 1:
        return {keys[0]: env_val}

    for key in keys:
        if not stack:
            current_dict[key] = None
            stack.append(current_dict)
        elif len(stack) == len(keys):
            if last_flat_key is not None:
                stack[-1][key][last_flat_key] = env_val
            else:
                stack[-1][key] = env_val
        else:
            new_dict = {}
            current_dict[key] = new_dict
            stack.append(new_dict)
            current_dict = new_dict
    return stack[0]


def dot_env_to_dict_rec(env_name, env_val, last_flat_key=None):
    sep = '.'
    if sep not in env_name:
        if last_flat_key:
            return {env_name: {last_flat_key: env_val}}
        return {env_name: env_val}
    key, val = env_name.split(sep, 1)
    return {key: dot_env_to_dict_rec(val, env_val, last_flat_key)}


def deep_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def table_print_columns(data_columns: [(str, [str])]):
    tbl = prettytable.PrettyTable()
    for (title, items) in data_columns:
        tbl.add_column(title, items)
    print(tbl)