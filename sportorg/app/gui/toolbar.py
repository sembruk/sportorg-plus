from sportorg import config
from sportorg.language import _
from sportorg.app.gui.global_access import GlobalAccess

from sportorg.app.modules.sportident import sportident


def toolbar_list():
    return [
        (config.icon_dir('file.png'), _('New'), GlobalAccess().get_main_window().create_file),
        (config.icon_dir('folder.png'), _('Open'), GlobalAccess().get_main_window().open_file),
        (config.icon_dir('save.png'), _('Save'), GlobalAccess().get_main_window().save_file),
        (config.icon_dir('sportident.png'), _('SPORTident readout'), sportident.start_reader),
    ]