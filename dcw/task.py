import subprocess
from pprint import pprint as pp
import sys

class DCWTask:
    def __init__(self) -> None:
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
