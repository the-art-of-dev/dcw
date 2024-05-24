# pylint: skip-file

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, List
from pprint import pprint as pp
import sys
from types import ModuleType
from typing import Callable, List
import importlib.util

from dcw.logger import logger as lgg
import traceback

from dcw.envy import EnvyCmd, EnvyConfig, apply_cmd_log, dict_to_envy

DCW_CMD_PREFIX = 'cmd_'


def dcw_envy_cfg() -> EnvyConfig:
    return EnvyConfig(cmd_prefix='dcw.')


@dataclass
class DcwState:
    envy_log: List[EnvyCmd]
    data: dict


@dataclass
class DcwModule:
    name: str
    selector: List[str]
    description: str
    import_url: str
    cmds: dict[str, Callable[[dict, dict, Callable], List[EnvyCmd]]]


@dataclass
class DcwCmdInfo:
    name: str
    description: str
    args: dict = field(default_factory=dict)


@dataclass
class DcwModuleInfo:
    name: str
    selector: List[str]
    description: str
    import_url: str
    cmds: dict[str, DcwCmdInfo] = field(default_factory=list)


def cmd_to_info(name: str, cmd: Callable) -> DcwCmdInfo:
    return DcwCmdInfo(
        name=name,
        description=cmd.__doc__,
        args=cmd.__dict__.get('dcw_args', {})
    )


def mod_to_info(mod: DcwModule) -> DcwModuleInfo:
    return DcwModuleInfo(
        name=mod.name,
        description=mod.description,
        selector=mod.selector,
        import_url=mod.import_url,
        cmds={n: cmd_to_info(n, c) for n, c in mod.cmds.items()}
    )


class DcwContext:
    def __init__(self, state=DcwState([], {}), modules: dict[str, DcwModule] = {}) -> None:
        self.state: DcwState = state
        self.modules: dict[str, DcwModule] = modules
        self.debug = False

        cl = dict_to_envy({
            '_ctx': {n: asdict(mod_to_info(m)) for n, m in self.modules.items()}
        })

        self.state.envy_log = self.state.envy_log + cl
        self.state.data = apply_cmd_log(self.state.data, cl, dcw_envy_cfg())

    def _run_cmd(self, module: str, cmd: str, args: dict = {}, prepand_sel: bool = True) -> List[EnvyCmd]:
        if module not in self.modules:
            raise Exception(f'Dcw module {module} not found.')
        if cmd not in self.modules[module].cmds:
            raise Exception(f'Command {cmd} not found in Dcw module {module}.')
        cl = self.modules[module].cmds[cmd](self.state.data, args, self._run_cmd)
        if prepand_sel:
            for c in cl:
                c.selector = self.modules[module].selector + c.selector
        return cl

    def run(self, module: str, cmd: str, args: dict = {}):
        try:
            cl = self._run_cmd(module, cmd, args)
            self.state.envy_log = self.state.envy_log + cl
            self.state.data = apply_cmd_log(self.state.data, cl, dcw_envy_cfg())
        except Exception as e:
            if self.debug:
                print(traceback.format_exc())
            lgg.error(e)

def dcw_cmd(argument={}, hooks=[]):
    def decorator(func):
        def wrapper(s, args, run):
            return func(s, {**argument, **args}, run)
        n = func.__name__
        if not n.startswith(DCW_CMD_PREFIX):
            n = f'{DCW_CMD_PREFIX}{n}'
        wrapper.__name__ = n
        wrapper.dcw_args = argument
        return wrapper
    return decorator


def sys_to_dcw_module(module: ModuleType) -> DcwModule:
    name = module.__dict__.get('name', module.__name__)
    selector = module.__dict__.get('selector', ['name'])

    cmds = {}
    for k in module.__dict__.keys():
        if isinstance(module.__dict__[k], Callable) and  \
                f'{module.__dict__[k].__name__}'.startswith(DCW_CMD_PREFIX):
            cmd_name = f'{module.__dict__[k].__name__}'[len(DCW_CMD_PREFIX):]
            cmds[cmd_name] = module.__dict__[k]

    return DcwModule(
        name=name,
        selector=selector,
        description=module.__doc__,
        import_url=module.__file__,
        cmds=cmds
    )


def load_dcw_module(name: str, url: str) -> DcwModule:
    if name in sys.modules:
        return sys_to_dcw_module(sys.modules[name])
    elif (spec := importlib.util.find_spec(name)) is not None:
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return sys_to_dcw_module(sys.modules[name])
    else:
        print(f"can't find the {name!r} module")
    return None
