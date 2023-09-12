from dcw.core import DCWGroup, DCWService


def test_new_service_group():
    svc_group = DCWGroup('test')
    assert svc_group.name == 'test'
    assert svc_group.objs == {}


def test_new_service_group_with_svcs():
    svc = DCWService('test')
    svc_group = DCWGroup('test', objs=[svc])
    assert svc_group.name == 'test'
    assert svc_group.objs == {'test': svc}


def test_add_svc():
    svc = DCWService('test')
    svc_group = DCWGroup('test')
    svc_group.add_obj(svc)
    assert svc_group.objs == {'test': svc}

def test_remove_svc():
    svc = DCWService('test')
    svc_group = DCWGroup('test', objs=[svc])
    svc_group.remove_obj('test')
    assert svc_group.objs == {}

def test_get_svc():
    svc = DCWService('test')
    svc_group = DCWGroup('test', objs=[svc])
    assert svc_group.get_obj('test') == svc
    assert svc_group.get_obj('test2') == None