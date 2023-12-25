from fabric import task

@task
def test(c):
    with c.cd('../'):
        c.run('ls')