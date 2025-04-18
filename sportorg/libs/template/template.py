import locale
import datetime

import dateutil.parser
from jinja2 import Template, Environment, FileSystemLoader


def to_hhmmss(value, fmt=None):
    """value = 1/1000 s"""
    if value is None:
        return ''
    if not fmt:
        fmt = '%H:%M:%S'
    dt = value
    if not isinstance(value, datetime.datetime):
        dt = datetime.datetime(2000, 1, 1, value // 3600000 % 24, (value % 3600000) // 60000,
                           (value % 60000) // 1000, (value % 1000) * 10)
    return dt.strftime(fmt)


def date(value, fmt=None):
    if not value:
        return ''
    if not fmt:
        fmt = '%d.%m.%Y'
    return dateutil.parser.parse(value).strftime(fmt)


def finalize(thing):
    return thing if thing else ''


def get_text_from_template(searchpath, path, **kwargs):
    env = Environment(
        loader=FileSystemLoader(searchpath),
        finalize=finalize
    )
    env.filters['tohhmmss'] = to_hhmmss
    env.filters['date'] = date
    env.globals['current_time'] = datetime.datetime.now()
    env.policies['json.dumps_kwargs']['ensure_ascii'] = False
    template = env.get_template(path)

    return template.render(**kwargs)
