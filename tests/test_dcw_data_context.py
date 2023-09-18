from dcw.core import DCWDataContext, DCWGroupIO, DCWGroup, DCWService


class MockGroupIO(DCWGroupIO):
    def import_group(self):
        return DCWGroup('test', objs=[DCWService('test')])

    def export_group(self, group):
        return super().export_group(group)


def test_new_orchestrator():
    mock = MockGroupIO('mock', 'mock-path')
    orch = DCWDataContext(mock)
    assert orch.group == None
    assert orch.svcs_group == None
    assert orch.envs_group == None
    assert orch.units_group == None
    assert orch.group_io == mock


def test_import_groups():
    mock_io = MockGroupIO('mock', 'mock-path')
    orch = DCWDataContext(mock_io)
    orch.import_group()
    assert orch.group == DCWGroup('test', objs=[DCWService('test')])
    assert orch.svcs_group == DCWGroup('svc', objs=[DCWService('test')])


