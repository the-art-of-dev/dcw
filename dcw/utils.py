import re
import string
import itertools

def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    from shutil import which

    return which(name) is not None

def flatten(list_of_lists):
    return list(itertools.chain.from_iterable(list_of_lists))
