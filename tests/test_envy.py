# pylint: skip-file
from dcw.envy import *


def test_str_to_envy():
    log = str_to_envy('''
    envy.select.[select.[task.name[[]]].is]@+=10
    envy.select.[select.[task.name].is1]@+=10
    envy.select.[select.[task.name].is2]@+=10
    ''', cfg=EnvyConfig())
    assert log == [
        EnvyCmd(selector=['select', 'select.[task.name[[]]].is'],
                op='@+',
                data='10'
                ),
        EnvyCmd(selector=['select', 'select.[task.name].is1'],
                op='@+',
                data='10'
                ),
        EnvyCmd(selector=['select', 'select.[task.name].is2'],
                op='@+',
                data='10'
                )
    ]


def test_get_selector_val():
    state = {
        'this': {
            'is': {'som[e]thing': '123'}
        }
    }

    v = get_selector_val(state, ['this', 'is', 'som[e]thing'])
    assert v == '123'

    v = get_selector_val(state, ['this'])
    assert v == {
        'is': {'som[e]thing': '123'}
    }

    v = get_selector_val(state, [])
    assert v == {
        'this': {
            'is': {'som[e]thing': '123'}
        }
    }

    v = get_selector_val(state, ['this', 'has'])
    assert v == None

def test_cmds_and_dict_to_envy():
    vv = cmd_add_str({
        'this': {
            'is': {'som[e]thing': '123'},
            'was': {'meeh': [2, 3, 4]},
            'remove': 'me'
        }
    }, ['this', 'is', 'som[e]thing'], '234')

    assert vv['this']['is']['som[e]thing'] == '123234'

    vv = cmd_unset(vv, ['this', 'remove'])
    assert 'remove' not in vv['this']

    vv = cmd_set_list(vv, ['this', 'new'], '-,-,-')
    assert vv['this']['new'] == ['-', '-', '-']

    vv = cmd_list_add(vv, ['this', 'new'], '*,0')
    assert vv['this']['new'] == ['-', '-', '-', '*', '0']

    vv = cmd_list_add(vv, ['this', 'new'], '1,rm')
    assert vv['this']['new'] == ['-', '-', '-', '*', '0', '1', 'rm']

    vv = cmd_list_rm(vv, ['this', 'new'], '*,rm')
    assert vv['this']['new'] == ['-', '-', '-', '0', '1']

    log = dict_to_envy(vv)
    assert log == [EnvyCmd(selector=['this', 'is', 'som[e]thing'], op='', data='123234'),
                   EnvyCmd(selector=['this', 'was', 'meeh'], op='@', data='2,3,4'),
                   EnvyCmd(selector=['this', 'new'], op='@', data='-,-,-,0,1')]


def test_apply_cmd():
    state = {
        'this': {
            'is': {'som[e]thing': '123'},
            'was': {'meeh': [2, 3, 4]},
            'remove': 'me'
        }
    }
    cfg = EnvyConfig()

    state = apply_cmd(state, EnvyCmd(['this', 'is', 'som[e]thing'], '+', '234'), cfg)
    assert state['this']['is']['som[e]thing'] == '123234'

    state = apply_cmd_log(state, [
        EnvyCmd(['this', 'remove'], '!', ''),
        EnvyCmd(['this', 'new'], '@', '-,-,-'),
    ], cfg)

    assert 'remove' not in state['this']
    assert state['this']['new'] == ['-', '-', '-']


def test_dataclass_map():
    s = {
        'tasks': {
            'first': {
                'name': 'first',
                'args': {}
            },
            'second': {
                'name': 'second',
                'args': {'fa': 'yo'}
            }
        }
    }

    def dict_val_mapper(vtype: Callable):
        def map_val(d: dict):
            return {k: vtype(**v) for k,v in d.items()}
        return map_val
    
    @dataclass
    class MyTask:
        name: str
        args: dict

    v = get_selector_val(s, ['tasks'], dict_val_mapper(MyTask))
    assert v['first'] == MyTask('first', {})
    assert v['second'] == MyTask('second', {'fa': 'yo'})
