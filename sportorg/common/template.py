import os

from sportorg.libs.template import template
from sportorg import config


def get_templates(path='', exclude_path=''):
    if not path:
        path = config.template_dir()
    if not exclude_path:
        exclude_path = config.template_dir()
    files = []
    for p in os.listdir(path):
        full_path = os.path.join(path, p)
        if os.path.isdir(full_path):
            fs = get_templates(full_path)
            for f in fs:
                f = f.replace(exclude_path, '')
                f = f.replace('\\', '/')
        else:
            if full_path.endswith('.html') or full_path.endswith('.docx'):
                full_path = full_path.replace(exclude_path, '')
                full_path = full_path.replace('\\', '/')
                files.append(full_path)

    return sorted(files)


def get_text_from_file(path, **kwargs):
    kwargs['name'] = config.NAME
    kwargs['version'] = str(config.VERSION)
    if os.path.isfile(path):
        return template.get_text_from_path(path, **kwargs)
    else:
        return template.get_text_from_template(config.template_dir(), path, **kwargs)
