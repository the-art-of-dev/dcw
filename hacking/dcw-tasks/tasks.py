from invoke.tasks import task
from invoke.context import Context

@task
def test(ctx):
    print('Poyy')


@task
def hello(ctx, name):
    '''Says poyy to everyone'''
    print(f'Poyy {name}')

