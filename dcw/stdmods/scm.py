# pylint: skip-file
from __future__ import annotations
import os
from typing import Callable, List, TypedDict

import yaml
from dcw.core import dcw_cmd, dcw_envy_cfg
from dcw.envy import EnvyCmd, EnvyState, dict_to_envy
from dcw.utils import check_for_missing_args
from pprint import pprint as pp
from git import Repo
from urllib.parse import urlparse, urlunparse
# --------------------------------------
#   SCM
# --------------------------------------
# region
__doc__ = 'Dcw SCM - handles DCW source code management'
NAME = name = 'scm'
SELECTOR = selector = ['scm']


DcwRepoConfig = TypedDict('DcwRepoConfig', {
    'type': str,
    'src_url': str,
    'dest_url': str,
    'src_version': str,
    'username': str,
    'password': str
})

DcwRepo = TypedDict('DcwRepo', {
    'name': str,
    'type': str,
    'src_url': str,
    'dest_url': str,
    'src_version': str,
    'dest_version': str,
    'username': str,
    'password': str,
    'is_dirty': bool
})


def get_version_from_url(url: str, default='main') -> str:
    url_parts = urlparse(url)
    if url_parts.fragment == '':
        return default
    return url_parts.fragment


def set_url_version(url: str, version) -> str:
    url_parts = urlparse(url)
    return urlunparse({
        **url_parts._asdict(),
        'fragment': version
    }.values())


def remove_url_version(url: str) -> str:
    url_parts = urlparse(url)
    return urlunparse({
        **url_parts._asdict(),
        'fragment': ''
    }.values())


def get_local_version_of_repo(repo_url: str) -> str:
    if not os.path.exists(repo_url):
        return ''

    repo = Repo.init(repo_url, mkdir=False)
    return repo.active_branch.name


def set_url_auth(url: str, username: str, password: str) -> str:
    if username in [None, ''] or password in [None, '']:
        return url

    url_parts = urlparse(url)
    return urlunparse({
        **url_parts._asdict(),
        'netloc': f'{username}:{password}@{url_parts.netloc}'
    }.values())


def check_is_local_repo_dirty(repo_url: str) -> bool:
    if not os.path.exists(repo_url):
        return False
    repo = Repo.init(repo_url, mkdir=False)
    return repo.is_dirty()


def clone_if_not_exist(repo: DcwRepo):
    url = remove_url_version(repo['src_url'])
    url = set_url_auth(url, repo.get('username', None), repo.get('password', None))
    git_repo = Repo.init(repo['dest_url'])
    remote = next(filter(lambda x: x.name == 'origin', git_repo.remotes), None)
    if remote is not None:
        git_repo.git.remote(['set-url', 'origin', url])
        return
    
    git_repo.git.remote(['add', 'origin', url])
    git_repo.git.fetch()
    git_repo.git.pull(['origin', repo['src_version']])


def reset_if_dirty(repo: DcwRepo):
    if not repo['is_dirty']:
        return
    git_repo = Repo.init(repo['dest_url'], mkdir=False)
    git_repo.head.reset(index=True, working_tree=True)
    git_repo.git.clean(['-fxd'])


def goto_src_version(repo: DcwRepo):
    git_repo = Repo.init(repo['dest_url'], mkdir=False)
    git_repo.git.fetch()
    git_repo.git.checkout(['-f', repo['src_version']])
    git_repo.git.pull(['origin', repo['src_version']])


def not_found_ex(name: str) -> Exception:
    return Exception(f'Scm repo {name} not found.')


@dcw_cmd()
def cmd_load(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    state = EnvyState(s, dcw_envy_cfg()) + run('proj', 'load')

    proj_root: str = state['proj.root']
    scm_root: str = state['proj.cfg.scm_root']
    scm_cfg: dict[str, DcwRepoConfig] = state['proj.cfg.scm']

    if scm_cfg == None:
        return []

    if scm_root == None:
        raise Exception('Property proj.cfg.scm_root not set')

    diff_state: dict[str, DcwRepo] = {}

    for rn, rcfg in scm_cfg.items():
        if rcfg.get('dest_url', None) in [None, '']:
            rcfg['dest_url'] = os.path.join(proj_root, scm_root, rn)
        if rcfg.get('src_version', None) in [None, '']:
            rcfg['src_version'] = get_version_from_url(rcfg['src_url'])

        diff_state[rn] = {
            'name': rn,
            **rcfg,
            'dest_version': get_local_version_of_repo(rcfg['dest_url']),
            'is_dirty': check_is_local_repo_dirty(rcfg['dest_url']),
        }

    return dict_to_envy(diff_state)


@dcw_cmd({'name': ...})
def cmd_sync(s: dict, args: dict, run: Callable) -> List[EnvyCmd]:
    check_for_missing_args(args, ['name'])
    repo_name = args['name']
    state = EnvyState(s, dcw_envy_cfg()) + run(NAME, 'load')

    repos: List[DcwRepo] = state[f'scm.{repo_name}']
    if isinstance(repos, list):
        repos = [repo for _, repo in repos]
    else:
        repos = [repos]

    for r in repos:
        clone_if_not_exist(r)
        reset_if_dirty(r)
        goto_src_version(r)

    return []


# endregion
