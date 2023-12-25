from invoke.tasks import task
from invoke.context import Context

@task
def test(ctx):
    print('Poyy')
    ctx.run('docker ps')

@task
def hello(ctx, name):
    '''Says poyy to everyone'''
    print(f'Hauk {name}')

