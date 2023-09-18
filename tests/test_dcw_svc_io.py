from dcw.core import DCWGroup, DCWGroupIO
from dcw.config import get_config


def test_new_service_importer():
    class TestImporter(DCWGroupIO):
        def import_group(self):
            pass
        def export_group(self, svc_group: DCWGroup) -> None:
            return super().export_group(svc_group)
    
    importer = TestImporter('test', get_config('DCW_SVCS_DIR'))
    assert importer.group_root_path == get_config('DCW_SVCS_DIR')
