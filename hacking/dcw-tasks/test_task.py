from invoke.tasks import task


@task
def test12(ctx):
    print('Poyy')


@task
def hello12(ctx, name):
    print(f'Poyy {name}')

