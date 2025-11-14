import locale
import datetime

import dateutil.parser
from jinja2 import Template, Environment, FileSystemLoader


def to_hhmmss(value, less24=True, fmt=None):
    """value = 1/1000 s"""
    if value is None:
        return ''
    if not fmt:
        fmt = '%H:%M:%S'
    dt = value
    if not isinstance(value, datetime.datetime):
        hour = value // 3600000
        if less24:
            hour = hour % 24
        minute = (value % 3600000) // 60000
        sec = (value % 60000) // 1000
        dt = datetime.datetime(2000, 1, 1, hour, minute, sec, (value % 1000) * 10)
    return dt.strftime(fmt)

def to_hhmmss_rlt(value):
    return to_hhmmss(value, less24=False)


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
    env.filters['tohhmmss_rlt'] = to_hhmmss_rlt
    env.filters['date'] = date
    env.globals['current_time'] = datetime.datetime.now()
    env.policies['json.dumps_kwargs']['ensure_ascii'] = False
    template = env.get_template(path)

    return template.render(**kwargs)
