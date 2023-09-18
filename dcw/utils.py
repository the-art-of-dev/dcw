import re
import string

def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    from shutil import which

    return which(name) is not None

def template_env_vars(text: str):
    placeholders = re.findall(r'[^$]\$\{([^}]*)\}', text)
    return list(set(placeholders))

def render_template(text:str, env_vars: dict):
    template = string.Template(text)
    return template.safe_substitute(env_vars)