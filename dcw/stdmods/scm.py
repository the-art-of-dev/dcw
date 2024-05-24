# pylint: skip-file
from __future__ import annotations
from dataclasses import asdict, dataclass
import os
from typing import Callable, List

import yaml
from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, EnvyState, apply_cmd_log, get_selector_val, dict_to_envy
from dcw.utils import check_for_missing_args, value_map_dict, value_map_dataclass as vm_dc, raise_if
from pprint import pprint as pp
from git import GitCommandError, InvalidGitRepositoryError, Repo

# --------------------------------------
#   Code Repository
# --------------------------------------
# region
__doc__ = 'Dcw Tasks - handles DCW code repositories'
NAME = name = 'scm'
SELECTOR = selector = ['scm']


@dataclass
class DcwCodeRepo:
    name: str
    type: str
    url: str
    username: str = ''
    password: str = ''
    version: str = 'main'
    _local_url: str = ''

    def remote_url(self) -> str:
        if self.username == '' or self.password == '':
            return self.url
        else:
            return f"https://{self.username}:{self.password}@{self.url.removeprefix('https://')}"

    def local_url(self) -> str:
        if self._local_url != '' and isinstance(self._local_url, str):
            return self._local_url
        return self.name


def not_found_ex(name: str) -> Exception:
    return Exception(f'Scm repo {name} not found.')


@dcw_cmd()
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state = EnvyState(s, dcw_envy_cfg()) + run('proj', 'load')
    scm_cfg: dict = state['proj.cfg.scm']
    if scm_cfg is None:
        return []

    return dict_to_envy({n: asdict(DcwCodeRepo(n, **cr)) for n, cr in scm_cfg.items()})


def find_code_repo(s: dict, name: str, run: Callable) -> DcwCodeRepo:
    cl = run('proj', 'load') + run('scm', 'load')
    s = apply_cmd_log(s, cl, dcw_envy_cfg())
    code_repos: dict[str, DcwCodeRepo] = get_selector_val(s, ['scm'], value_map_dict(str, DcwCodeRepo))
    if name not in code_repos:
        raise Exception(f'Code repo with name {name} not found!')
    return code_repos[name]


def clone_repo(code_repo: DcwCodeRepo, local_path: str) -> bool:
    try:
        Repo.clone_from(code_repo.remote_url(), local_path)
        return True
    except GitCommandError as e:
        print(f"An error occurred: {e}")
        return False


def map_cr(name: str):
    return raise_if(not_found_ex(name), vm_dc(DcwCodeRepo))


@dcw_cmd({'name': ...})
def cmd_clone(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    repo_name = args['name']
    state = EnvyState(s, dcw_envy_cfg()) + run('proj', 'load') + run(NAME, 'load')
    repo: DcwCodeRepo = state[f'scm.{repo_name}', map_cr(repo_name)]

    if not clone_repo(repo, os.path.join(state['proj.root'], state['proj.cfg.scm_root'], repo.name)):
        raise Exception(f'Error while clonning repo {repo.name}')
    return []


def checkout_version(code_repo: DcwCodeRepo) -> bool:
    try:
        repo = Repo(code_repo.local_url)
        repo.git.checkout(code_repo.version)
        return True
    except GitCommandError as e:
        print(f"Error: {e}")
        return False


@dcw_cmd({'name': ...})
def cmd_checkout(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    repo_name = args['name']
    state = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')
    repo: DcwCodeRepo = state[f'scm.{repo_name}', map_cr(repo_name)]

    if not checkout_version(repo):
        raise Exception(f'Error while checking out version on repo {repo.name}')
    return []


def pull_repo(code_repo: DcwCodeRepo) -> bool:
    try:
        repo = Repo(code_repo.local_url)
        repo.remotes['origin'].fetch()
        repo.remotes['origin'].pull()
        return True
    except InvalidGitRepositoryError:
        print("Invalid Git repository.")
        return False
    except GitCommandError as e:
        print("Error pulling code:", e)
        return False


@dcw_cmd({'name': ...})
def cmd_pull(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    cr = find_code_repo(s, args['name'], run)
    if not pull_repo(cr):
        raise Exception(f'Error while pulling code repo {cr.name}')
    return []


def tag_repo(code_repo: DcwCodeRepo, tag_name: str) -> bool:
    try:
        repo = Repo(code_repo.local_url)
        tag = repo.create_tag(tag_name)
        repo.remotes['origin'].push(tag)
        return True
    except GitCommandError as e:
        print(f"Error: {e}")
        return False


@dcw_cmd({'name': ..., 'tag_name': ...})
def cmd_tag(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name', 'tag_name'])
    cr = find_code_repo(s, args['name'], run)
    if not tag_repo(cr, args['tag_name']):
        raise Exception(f'Error while tagging code repo {cr.name}')
    return []


# endregion
