from invoke.tasks import task
from invoke.context import Context
from dcw.stdmods.task_collections import dcw_task
from dcw.utils import is_false

@dcw_task
def test(ctx):
    print('Poyy')
    ctx.run('docker ps')

@task
def hello(ctx, name):
    '''Says poyy to everyone'''
    print(f'Hauk {name}')

@dcw_task
def dc_up(ctx, cwd='.', filename='docker-compose.yml', recreate='false'):
    with ctx.cd(cwd):
        cmd = f'docker-compose -f {filename} up -d'
        if not is_false(recreate):
            cmd += ' --force-recreate'
        ctx.run(cmd, echo=True)

@dcw_task
def dc_down(ctx, cwd='.', filename='docker-compose.yml', remove='false'):
    with ctx.cd(cwd):
        cmd = f'docker-compose -f {filename} down'
        if not is_false(remove):
            cmd += ' -v'
        ctx.run(cmd, echo=True)
