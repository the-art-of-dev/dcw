from dcw.core import DCWUnit, DCWService, DCWGroup, DCWEnv


def test_new_unit():
    unit = DCWUnit('test')
    assert unit.name == 'test'
    assert unit.svc_names == []


def test_new_unit_with_svcs():
    unit = DCWUnit('test', svc_names=['test', 'test2'])
    assert unit.name == 'test'
    assert unit.svc_names == ['test', 'test2']


def test_add_svc():
    unit = DCWUnit('test')
    unit.add_svc('test')
    assert unit.svc_names == ['test']


def test_add_svc_duplicates():
    unit = DCWUnit('test')
    unit.add_svc('test')
    unit.add_svc('test')
    assert unit.svc_names == ['test']


def test_remove_svc():
    unit = DCWUnit('test', svc_names=['test'])
    unit.remove_svc('test')
    assert unit.svc_names == []


def test_apply_env():
    svc = DCWService('test')
    svc_group = DCWGroup('test', objs=[svc])
    env = DCWEnv('test', env_vars={
                 'svc.test.environment.TEST.something': 'test'})
    unit = DCWUnit('test', svc_names=['test'])
    svcs = unit.apply_env(env, svc_group)

    expected_svc = DCWService('test', environment={'TEST.something': 'test'})
    assert svcs == {'test': expected_svc}

def test_apply_env_multiple():
    svc = DCWService('test')
    svc_group = DCWGroup('test', objs=[svc])
    env = DCWEnv('test', env_vars={
                 'svc.test.environment.TEST.something': 'test'})
    unit = DCWUnit('test', svc_names=['test'])
    svcs = unit.apply_env(env, svc_group)
    expected_svc = DCWService('test', environment={'TEST.something': 'test'})
    assert svcs == {'test': expected_svc}
    
    env2 = DCWEnv('test', env_vars={
                 'svc.test.environment.TEST.something': 'test2'})
    svcs = unit.apply_env(env2, svc_group)
    expected_svc = DCWService('test', environment={'TEST.something': 'test2'})
    assert svcs == {'test': expected_svc}

