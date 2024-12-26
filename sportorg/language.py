import configparser
import gettext
import logging
import os
from PySide2.QtCore import QLocale
from sportorg import config


def _get_conf_locale():
    conf = configparser.ConfigParser()
    try:
        conf.read(config.CONFIG_INI)
    except Exception as e:
        logging.exception(e)
        # remove incorrect config
        os.remove(config.CONFIG_INI)
    system_locale = QLocale.system().name()
    logging.debug(f"Sytem locale: {system_locale}")
    default_locale = 'ru_RU'
    if default_locale != system_locale:
        default_locale = 'en_US'
    return conf.get('locale', 'current', fallback=default_locale)


current_locale = _get_conf_locale()


if config.DEBUG:
    import polib

    def _generate(lang):
        path = config.base_dir(config.LOCALE_DIR, lang, 'LC_MESSAGES', 'sportorg')
        try:
            po = polib.pofile(path + '.po')
            po.save_as_mofile(path + '.mo')
        except Exception as e:
            logging.error(str(e))

    _generate('ru_RU')
    _generate('en_US')


def locale():
    cat = gettext.Catalog('sportorg', config.LOCALE_DIR, languages=[current_locale])

    def get_text(message):
        result = cat.gettext(message)
        # if result == message:
        #     logging.debug('No translation "{}"'.format(result))
        return result

    return get_text


def get_languages():
    dirs = os.listdir(path=config.LOCALE_DIR)
    return dirs


_ = locale()
tr = locale()

