import re
import string

def template_env_vars(text: str):
    placeholders = re.findall(r'[^$]\$\{([^}]*)\}', text)
    return list(set(placeholders))

def render_template(text:str, env_vars: dict):
    template = string.Template(text)
    return template.safe_substitute(env_vars)