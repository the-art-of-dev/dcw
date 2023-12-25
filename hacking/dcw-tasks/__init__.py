from invoke import Collection

import tasks, test_task

ns = Collection()
ns.add_collection(Collection.from_module(tasks))
ns.add_collection(Collection.from_module(test_task))
