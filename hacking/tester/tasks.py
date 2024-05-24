# pylint: skip-file

from invoke.tasks import task

@task
def unit(c):
    print("Running unit tests!")

@task
def integration(c):
    print("Running integration tests!")