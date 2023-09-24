import subprocess
from pprint import pprint as pp
import sys
import yaml
from dcw.templates import render_template


class DCWTask:
    def __init__(self, name: str, config: dict) -> None:
        self.name = name
        self.config = config

    def apply_config(self, config: dict):
        self.config = {
            **self.config,
            **config
        }

    def apply_env(self, env_vars: dict):
        new_data = yaml.safe_load(render_template(
            yaml.safe_dump(self.config), env_vars))
        self.apply_config(new_data)


def import_tasks_from_dir(tasks_dir: str):
    pass


def execute_ansible_task(task_file_path: str, command: [str]):
    cmd = ['ansible-playbook', *command, task_file_path]

    proc = subprocess.Popen(args=cmd,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout,
                            stderr=sys.stderr,
                            cwd='.'
                            )
    try:
        proc.communicate(timeout=15)
    except subprocess.SubprocessError as errs:
        proc.kill()
        sys.exit("Error: {}".format(errs))
