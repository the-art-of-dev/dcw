from dcw.core import DCWService
import dcw.config as config
import pytest
import os


def test_new_service():
    svc = DCWService('test')
    assert svc.name == 'test'
    assert svc.image == 'test'
    assert svc.ports == []
    assert svc.environment == {}
    assert svc.labels == {}
    assert svc.networks == []


def test_new_configured_service():
    svc = DCWService('test',
                     image='test-image',
                     ports=['80:80'],
                     environment={'TEST': 'test'},
                     labels={'TEST': 'test'},
                     networks=['test-network'])
    assert svc.name == 'test'
    assert svc.image == 'test-image'
    assert svc.ports == ['80:80']
    assert svc.environment == {'TEST': 'test'}
    assert svc.labels == {'TEST': 'test'}
    assert svc.networks == ['test-network']


def test_new_configured_service_with_config():
    svc = DCWService('test', image='test-image', config={'test': 'test'})
    assert svc.name == 'test'
    assert svc.image == 'test-image'
    assert svc.ports == []
    assert svc.environment == {}
    assert svc.labels == {}
    assert svc.networks == []
    assert svc.config == {'test': 'test'}


def test_new_configured_service_with_config_image():
    svc = DCWService('test', config={'image': 'test-image'})
    assert svc.name == 'test'
    assert svc.image == 'test-image'


def test_new_configured_service_with_config_ports():
    svc = DCWService('test', config={'ports': ['80:80']})
    assert svc.name == 'test'
    assert svc.ports == ['80:80']


def test_new_configured_service_with_config_environment():
    svc = DCWService('test', config={'environment': {'TEST': 'test'}})
    assert svc.name == 'test'
    assert svc.environment == {'TEST': 'test'}


def test_new_configured_service_with_config_labels():
    svc = DCWService('test', config={'labels': {'TEST': 'test'}})
    assert svc.name == 'test'
    assert svc.labels == {'TEST': 'test'}


def test_new_configured_service_with_config_networks():
    svc = DCWService('test', config={'networks': ['test-network']})
    assert svc.name == 'test'
    assert svc.networks == ['test-network']


def test_as_dict():
    svc = DCWService('test',
                     image='test-image',
                     ports=['80:80'],
                     environment={'TEST': 'test'},
                     labels={'TEST': 'test'},
                     networks=['test-network'],
                     config={'hostname': 'test'})
    assert svc.as_dict() == {
        'image': 'test-image',
        'ports': ['80:80'],
        'environment': {'TEST': 'test'},
        'labels': {'TEST': 'test'},
        'networks': ['test-network'],
        'hostname': 'test'
    }


def test_set_env():
    svc = DCWService('test')
    svc.set_env('TEST', 'test')
    assert svc.environment == {'TEST': 'test'}


def test_get_env():
    svc = DCWService('test')
    svc.set_env('TEST', 'test')
    assert svc.get_env('TEST') == 'test'


def test_get_env_invalid():
    svc = DCWService('test')
    with pytest.raises(KeyError):
        svc.get_env('TEST')


def test_set_label():
    svc = DCWService('test')
    svc.set_label('TEST', 'test')
    assert svc.labels == {'TEST': 'test'}


def test_get_label():
    svc = DCWService('test')
    svc.set_label('TEST', 'test')
    assert svc.labels == {'TEST': 'test'}


def test_get_label_invalid():
    svc = DCWService('test')
    with pytest.raises(KeyError):
        svc.get_label('TEST')


def test_add_port():
    svc = DCWService('test')
    svc.add_port('80:80')
    assert svc.ports == ['80:80']


def test_add_port_duplicate():
    svc = DCWService('test')
    svc.add_port('80:80')
    svc.add_port('80:80')
    assert svc.ports == ['80:80']


def test_add_network():
    svc = DCWService('test')
    svc.add_network('test-network')
    assert svc.networks == ['test-network']


def test_add_network_duplicate():
    svc = DCWService('test')
    svc.add_network('test-network')
    svc.add_network('test-network')
    assert svc.networks == ['test-network']


def test_apply_config():
    svc = DCWService('test', config={'container_name': 'test'})
    svc.apply_config({
        'image': 'test-image',
        'ports': ['80:80'],
        'environment': {'TEST': 'test'},
        'labels': {'TEST': 'test'},
        'networks': ['test-network'],
        'hostname': 'test'})
    assert svc.image == 'test-image'
    assert svc.ports == ['80:80']
    assert svc.environment == {'TEST': 'test'}
    assert svc.labels == {'TEST': 'test'}
    assert svc.networks == ['test-network']
    assert svc.config == {'container_name': 'test', 'hostname': 'test'}
