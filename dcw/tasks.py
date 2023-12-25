# pylint: skip-file

from dataclasses import dataclass, asdict, field
from invoke import task
from invoke.program import Program
import enum
from dcw.utils import str_to_bool
from pprint import pprint as pp
from dcw.deployment import DCWDeploymentSpecification

# chained and same arguments
#

inv_prg = Program()

class DCWTaskConfigMode(str, enum.Enum):
    ENVIRONMENT = 'environment'
    SERVICE_GROUP = 'service_group'
    SERVICE = 'service'


class DCWTaskArgsMergingMode(str, enum.Enum):
    CHAINABLE = 'chainable'     # SAME ARGUMENT NAME MULTIPLE VALUES
    REPLICATED = 'replicated'   # SAME ARGUMENT NAME FOR EVERY VALUE REPEAT N TIMES  !!! TODO
    NONE = 'none'               # SAME ARGUMENT NAME ONLY ONCE


class DCWTaskMagicArgs(str, enum.Enum):
    EXEC_ORDER = '__exec_order'
    MERGE_DISABLED = '__merge_disabled'
    CHILL_AFTER = '__chill_after'
    CHAINABLE_ARGS = '__chainable'
    REPLICATED_ARGS = '__replicated'
    CHAINABLE_ARGS_SEP = '__chainable_sep'

#   TODO: one task spec can have multiple arguments with the same name


@dataclass
class DCWTaskSpec:
    name: str = ''
    mode: DCWTaskConfigMode = DCWTaskConfigMode.ENVIRONMENT
    args: dict = field(default_factory=dict)


class DCWTask:
    def __init__(self, task_config: dict) -> None:
        self.spec = DCWTaskSpec(**task_config)

        self.name: str = self.spec.name
        self.mode: DCWTaskConfigMode = self.spec.mode
        self.args: dict = self.spec.args

        self.exec_order: int = 0
        self.merge_disabled: bool = False
        self.chill_after: int = 0
        self.chainable_args: [str] = []
        self.replicated_args: [str] = []
        self.chainable_args_sep: str = ','
        self.__set_from_args()

    def __set_exec_order_from_args(self):
        if DCWTaskMagicArgs.EXEC_ORDER.value in self.args:
            self.exec_order = int(self.args[DCWTaskMagicArgs.EXEC_ORDER.value])
            del self.args[DCWTaskMagicArgs.EXEC_ORDER.value]

    def __set_merge_from_args(self):
        if DCWTaskMagicArgs.MERGE_DISABLED.value in self.args:
            self.merge_disabled = str_to_bool(self.args[DCWTaskMagicArgs.MERGE_DISABLED.value])
            del self.args[DCWTaskMagicArgs.MERGE_DISABLED.value]

    def __set_chill_after_from_args(self):
        if DCWTaskMagicArgs.CHILL_AFTER.value in self.args:
            self.chill_after = self.args[DCWTaskMagicArgs.CHILL_AFTER.value]
            del self.args[DCWTaskMagicArgs.CHILL_AFTER.value]

    def __set_chainable_args_from_args(self):
        for argn in self.args:
            if argn.endswith(f'.{DCWTaskMagicArgs.CHAINABLE_ARGS.value}'):
                can = argn[:-len(f'.{DCWTaskMagicArgs.CHAINABLE_ARGS.value}')]
                if can not in self.chainable_args:
                    self.chainable_args.append(can)

        for can in self.chainable_args:
            if f'{can}.{DCWTaskMagicArgs.CHAINABLE_ARGS.value}' in self.args:
                del self.args[f'{can}.{DCWTaskMagicArgs.CHAINABLE_ARGS.value}']

    def __set_replicated_args_from_args(self):
        if DCWTaskMagicArgs.REPLICATED_ARGS.value in self.args:
            self.replicated_args = self.args[DCWTaskMagicArgs.REPLICATED_ARGS.value]
            del self.args[DCWTaskMagicArgs.REPLICATED_ARGS.value]

    def __set_chainable_args_sep_from_args(self):
        if DCWTaskMagicArgs.CHAINABLE_ARGS_SEP.value in self.args:
            self.chainable_args_sep = self.args[DCWTaskMagicArgs.CHAINABLE_ARGS_SEP.value]
            del self.args[DCWTaskMagicArgs.CHAINABLE_ARGS_SEP.value]

    def __set_from_args(self):
        self.__set_exec_order_from_args()
        self.__set_merge_from_args()
        self.__set_chill_after_from_args()
        self.__set_chainable_args_from_args()
        self.__set_replicated_args_from_args()
        self.__set_chainable_args_sep_from_args()

    def can_merge_with_task(self, other_task) -> bool:
        if self.merge_disabled or other_task.merge_disabled:
            return False
        if self.chainable_args != other_task.chainable_args:
            return False
        if self.name != other_task.name or self.mode != other_task.mode:
            return False
        return True

    # Input:
    #   other - DCWTaskSpec to be merged with
    # Return types:
    #   DCWTaskSpec - resulting merged task specifications
    # TODO

    def merge_spec(self, other: DCWTaskSpec) -> DCWTaskSpec | None:
        other_task = DCWTask(asdict(other))

        if not self.can_merge_with_task(other_task):
            return None

        res_spec = DCWTaskSpec(**self.as_dict())

        for argn in other_task.args:
            argv = other_task.args[argn]
            if argn not in res_spec.args:
                res_spec.args[argn] = argv
            if argn in other_task.chainable_args:
                res_spec.args[argn] += f'{self.chainable_args_sep}{argv}'

        return res_spec

    def run(self, tasks_root: str, tasks_module: str):
        cmd = ['x', '--search-root', tasks_root, '-c', tasks_module]
        cmd.append(self.name)
        for argn in self.args:
            argv = self.args[argn]
            cmd.append(f'--{argn}')
            cmd.append(argv)

        inv_prg.run(cmd)

    def as_dict(self):
        res_dict = {
            'name': self.name,
            'mode': self.mode,
            'args': {
                **self.args,
                DCWTaskMagicArgs.EXEC_ORDER.value: self.exec_order,
                DCWTaskMagicArgs.MERGE_DISABLED.value: f'{self.merge_disabled}',
                DCWTaskMagicArgs.CHILL_AFTER.value: self.chill_after,
                DCWTaskMagicArgs.CHAINABLE_ARGS_SEP.value: self.chainable_args_sep
            }
        }

        for argn in self.chainable_args:
            res_dict['args'][f'{argn}.{DCWTaskMagicArgs.CHAINABLE_ARGS.value}'] = ''

        return res_dict


class DCWTaskCollection:
    def __init__(self, taks_specs: [DCWTaskSpec], tasks_root: str, tasks_module: str) -> None:
        self.__task_sepcs: [DCWTaskSpec] = taks_specs
        self.tasks: [DCWTask] = []
        self.tasks_root = tasks_root
        self.tasks_module = tasks_module
        self.__make_tasks()

    def __make_tasks(self):
        self.tasks = []
        for ts in self.__task_sepcs:
            if len(self.tasks) == 0:
                self.tasks.append(DCWTask(asdict(ts)))
                continue

            update_task: DCWTask = None
            update_task_index: int = -1

            for ti in range(len(self.tasks)):
                t: DCWTask = self.tasks[ti]
                res_sepc = t.merge_spec(ts)
                if res_sepc is not None:
                    update_task = DCWTask(asdict(res_sepc))
                    update_task_index = ti

            if update_task is not None:
                self.tasks[update_task_index] = update_task
            else:
                self.tasks.append(DCWTask(asdict(ts)))

    def run_task(self, name: str, mode: DCWTaskConfigMode):
        for t in self.tasks:
            if t.name == name and t.mode == mode:
                t.run(self.tasks_root, self.tasks_module)


def make_task_coll_from_depl_spec(depl_spec: DCWDeploymentSpecification, tasks_root: str, tasks_module: str) -> DCWTaskCollection:
    return DCWTaskCollection([DCWTaskSpec(**t) for t in depl_spec.tasks], tasks_root, tasks_module)
