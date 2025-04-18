import polib

from sportorg import config
from sportorg.language import get_languages


def test_duplicates():
    locales = get_languages()
    for locale in locales:
        path = config.base_dir(config.LOCALE_DIR, locale, 'LC_MESSAGES', 'sportorg')
        po = polib.pofile(path + '.po', check_for_duplicates=True)
        po.save_as_mofile(path + '.mo')
