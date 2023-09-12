from dcw.core import DCWEnv, DCWEnvVariableType
from unittest.mock import MagicMock
import pytest


def test_type_of_env():
    assert DCWEnv.type_of_env(
        'svc.test.environment.TEST') == DCWEnvVariableType.SERVICE
    assert DCWEnv.type_of_env('TEST') == DCWEnvVariableType.GLOBAL


def test_get_env_name():
    assert DCWEnv.get_env_name(
        'svc.test.environment.TEST.something') == 'TEST.something'
    assert DCWEnv.get_env_name('TEST') == 'TEST'


def test_svc_name_from_env():
    assert DCWEnv.svc_name_from_env(
        'svc.test.environment.TEST.something') == 'test'
    assert DCWEnv.svc_name_from_env('TEST') == None


def test_svc_key_from_env():
    assert DCWEnv.svc_key_from_env(
        'svc.test.environment.TEST.something') == 'environment'
    assert DCWEnv.svc_key_from_env('TEST') == None


def test_new_env():
    env = DCWEnv('test')
    assert env.name == 'test'
    assert env.global_envs == {}
    assert env.service_configs == {}


def test_new_env_with_env_vars():
    env = DCWEnv('test',
                 env_vars={
                     'TEST': 'test',
                     'svc.test.environment.TEST.something': 'test',
                 })

    assert env.name == 'test'
    assert env.global_envs == {'TEST': 'test'}
    assert env.service_configs == {
        'test': {'environment': {'TEST.something': 'test'}}}


def test_get_env():
    env = DCWEnv('test', env_vars={'TEST': 'test'})
    assert env.get_env('TEST') == 'test'


def test_set_env():
    env = DCWEnv('test')
    env.set_env('TEST', 'test')
    env.set_env('svc.test.environment.some', 'test')
    assert env.global_envs == {'TEST': 'test'}
    assert env.service_configs == {
        'test': {'environment': {'some': 'test'}}}


def test_set_env_invalid():
    env = DCWEnv('test')
    with pytest.raises(Exception):
        env.set_env('svc.test.invalid.some', 'test')
