from dcw.core import DCWDataContext, DCWProcess, DCWGroupIO, DCWGroup, DCWService, DCWProcessState, DCWProcessingQueue


class MockGroupIO(DCWGroupIO):
    def import_group(self):
        return DCWGroup('test', objs=[DCWService('test')])

    def export_group(self, group):
        return super().export_group(group)


def test_new_process():
    data_context = DCWDataContext(MockGroupIO('mock', 'mock-path'))
    build_proc = DCWProcess('build', data_context=data_context)
    assert build_proc.name == 'build'
    assert build_proc.data_context == data_context
    assert build_proc.state == DCWProcessState.CREATED

def fail_if_not_test_group(s):
    if s.data_context.group is None or s.data_context.group.name != 'test':
        raise Exception('Group is not test')
    return True

def test_processing_queue():
    data_context = DCWDataContext(MockGroupIO('mock', 'mock-path'))

    load_proc = DCWProcess('load')
    load_proc.on_running(lambda s: s.data_context.import_group())

    build_proc = DCWProcess('build')
    build_proc.on_running(fail_if_not_test_group)

    queue = DCWProcessingQueue(data_context)
    queue.add_process(load_proc)
    queue.add_process(build_proc)
    queue.run()
    assert load_proc.state == DCWProcessState.FINISHED
    assert build_proc.state == DCWProcessState.FINISHED
    assert data_context.group == DCWGroup('test', objs=[DCWService('test')])

def test_processing_queue_fail():
    data_context = DCWDataContext(MockGroupIO('mock', 'mock-path'))

    load_proc = DCWProcess('load')

    build_proc = DCWProcess('build')
    build_proc.on_running(fail_if_not_test_group)

    queue = DCWProcessingQueue(data_context)
    queue.add_process(load_proc)
    queue.add_process(build_proc)
    queue.run()
    assert load_proc.state == DCWProcessState.FINISHED
    assert build_proc.state == DCWProcessState.FAILED
    assert data_context.group == None
