from dcw.core import DCWEnv
from unittest.mock import MagicMock


def test_new_env():
    dcw_env = DCWEnv('test', '.env.test', {
                     'version': '1.0.0', 'svc.test.environment.TEST': 'test', 'svc.test.labels.TEST': 'test', 'svc.test.xyz.TEST2': 'test2'})
    assert dcw_env.name == 'test'
    assert dcw_env.filename == '.env.test'
    assert dcw_env.env_vars == {'version': '1.0.0'}
    assert dcw_env.svc_env_vars == {'svc.test.environment.TEST': 'test',
                                    'svc.test.labels.TEST': 'test',
                                    'svc.test.xyz.TEST2': 'test2'}
