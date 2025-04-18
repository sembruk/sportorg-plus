"""
https://developer.github.com/v3/
"""

import logging
import requests
from sportorg import config
from sportorg.common.version import Version
from sportorg.language import _


VERSION = None


def get_last_tag_name():
    try:
        r = requests.get('https://api.github.com/repos/' + config.REPO_BASE + '/releases/latest', timeout=5)
        body = r.json()
        return body['tag_name']
    except requests.exceptions.RequestException as e:
        logging.error(_("Error fetching latest version: {}").format(e))
    return ''


def get_latest_version():
    global VERSION
    if not VERSION:
        VERSION = get_last_tag_name()
    return VERSION


def check_version_is_latest(version):
    latest_version = get_latest_version()
    logging.debug('Check version is latest: {} >= {}'.format(version, latest_version))
    if not latest_version:
        return True
    return version >= Version(latest_version)

def update_available(version):
    if not check_version_is_latest(version):
        return """
        <p>{} {}</p>
        <p><a href="{}">{}</a></p>
        """.format(
            _('Update available'),
            get_latest_version(),
            config.REPO_URL + '/releases/latest',
            _('Download'),
        )

    return None

