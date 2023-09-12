from dcw.core import DCWTemplate, DCWTemplateType


def test_new_template():
    template = DCWTemplate('test', DCWTemplateType.SVC, '')
    assert template.name == 'test'
    assert template.type == DCWTemplateType.SVC
    assert template.text == ''

def test_all_vars():
    template = DCWTemplate('test', DCWTemplateType.SVC, 'hello ${x}!!!')
    assert template.all_vars() == ['x']

def test_render_template():
    template = DCWTemplate('test', DCWTemplateType.SVC, 'hello ${x}!!!')
    assert template.render({'x': 'srbine'}) == 'hello srbine!!!'
