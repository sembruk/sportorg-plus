import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QDialog, QCheckBox, QDialogButtonBox, QLabel, QTabWidget, QWidget, QPushButton, \
    QSpinBox

from sportorg import config
from sportorg.common.audio import get_sounds
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _, get_languages, current_locale
from sportorg.models.memory import races, Race, set_current_race_index, add_race, copy_race, get_current_race_index, \
    del_race, move_up_race, move_down_race
from sportorg.modules.configs.configs import Config


class Tab:
    def save(self):
        pass


class MainTab(Tab):
    def __init__(self, parent):
        self.widget = QWidget()
        self.layout = QFormLayout(parent)

        self.label_lang = QLabel(_('Language'))
        self.item_lang = AdvComboBox()
        self.item_lang.addItems(get_languages())
        self.item_lang.setCurrentText(current_locale)
        self.layout.addRow(self.label_lang, self.item_lang)

        self.item_auto_save = QSpinBox()
        self.item_auto_save.setMaximum(3600*24)
        self.item_auto_save.setValue(Config().configuration.get('autosave_interval'))
        self.item_auto_save.setToolTip(_('Autosave disabled if value is 0'))
        self.layout.addRow(_('Auto save') + ' (sec)', self.item_auto_save)

        self.item_show_toolbar = QCheckBox(_('Show toolbar'))
        self.item_show_toolbar.setChecked(Config().configuration.get('show_toolbar', True))
        self.layout.addRow(self.item_show_toolbar)

        self.item_open_recent_file = QCheckBox(_('Open recent file'))
        self.item_open_recent_file.setChecked(Config().configuration.get('open_recent_file'))
        self.layout.addRow(self.item_open_recent_file)

        self.item_use_birthday = QCheckBox(_('Use birthday'))
        self.item_use_birthday.setChecked(Config().configuration.get('use_birthday'))
        self.layout.addRow(self.item_use_birthday)

        self.item_check_updates = QCheckBox(_('Check updates'))
        self.item_check_updates.setChecked(Config().configuration.get('check_updates', True))
        self.layout.addRow(self.item_check_updates)

        self.item_try_restore_backup = QCheckBox(_('Try restore card data from backup'))
        self.item_try_restore_backup.setChecked(Config().configuration.get('try_restore_backup', False))
        self.item_try_restore_backup.setToolTip(_('Try restore card data from backup file in "log" directory if last session was interrupted'))
        self.layout.addRow(self.item_try_restore_backup)

        self.widget.setLayout(self.layout)

    def save(self):
        Config().configuration.set('current_locale', self.item_lang.currentText())
        Config().configuration.set('autosave_interval', self.item_auto_save.value())
        Config().configuration.set('open_recent_file', self.item_open_recent_file.isChecked())
        Config().configuration.set('use_birthday', self.item_use_birthday.isChecked())
        Config().configuration.set('check_updates', self.item_check_updates.isChecked())
        Config().configuration.set('try_restore_backup', self.item_try_restore_backup.isChecked())

        if Config().configuration.get('show_toolbar') != self.item_show_toolbar.isChecked():
            mw = GlobalAccess().get_main_window()
            if self.item_show_toolbar.isChecked():
                if(hasattr(mw, 'toolbar')):
                    mw.toolbar.show();
                else:
                    mw._setup_toolbar()
            else:
                mw.toolbar.hide();
        Config().configuration.set('show_toolbar', self.item_show_toolbar.isChecked())



class SoundTab(Tab):
    def __init__(self, parent):
        self.widget = QWidget()
        self.layout = QFormLayout(parent)

        self.sounds = get_sounds()

        self.item_enabled = QCheckBox(_('Enabled'))
        self.item_enabled.setChecked(Config().sound.get('enabled'))
        self.layout.addRow(self.item_enabled)

        self.label_successful = QLabel(_('Successful result'))
        self.item_successful = AdvComboBox()
        self.item_successful.addItems(self.sounds)
        self.item_successful.setCurrentText(Config().sound.get('successful') or config.sound_dir('ok.wav'))
        self.layout.addRow(self.label_successful, self.item_successful)

        self.label_unsuccessful = QLabel(_('Unsuccessful result'))
        self.item_unsuccessful = AdvComboBox()
        self.item_unsuccessful.addItems(self.sounds)
        self.item_unsuccessful.setCurrentText(Config().sound.get('unsuccessful') or config.sound_dir('failure.wav'))
        self.layout.addRow(self.label_unsuccessful, self.item_unsuccessful)

        self.item_enabled_rented_card = QCheckBox(_('Enable rented card sound'))
        self.item_enabled_rented_card.setChecked(Config().sound.get('enabled_rented_card', Config().sound.get('enabled')))
        self.layout.addRow(self.item_enabled_rented_card)

        self.label_rented_card = QLabel(_('Rented card sound'))
        self.item_rented_card = AdvComboBox()
        self.item_rented_card.addItems(self.sounds)
        self.item_rented_card.setCurrentText(Config().sound.get('rented_card') or config.sound_dir('rented_card.wav'))
        self.layout.addRow(self.label_rented_card, self.item_rented_card)

        self.widget.setLayout(self.layout)

    def save(self):
        Config().sound.set('enabled', self.item_enabled.isChecked())
        Config().sound.set('successful', self.item_successful.currentText())
        Config().sound.set('unsuccessful', self.item_unsuccessful.currentText())
        Config().sound.set('enabled_rented_card', self.item_enabled_rented_card.isChecked())
        Config().sound.set('rented_card', self.item_rented_card.currentText())


class MultidayTab(Tab):
    def __init__(self, parent):
        self.widget = QWidget()
        self.layout = QFormLayout(parent)

        self.item_races = AdvComboBox()
        self.fill_race_list()

        max_button_width = 100

        def select_race():
            index = self.item_races.currentIndex()
            set_current_race_index(index)
            GlobalAccess().get_main_window().init_model()
            GlobalAccess().get_main_window().set_title()

        self.item_races.currentIndexChanged.connect(select_race)
        self.layout.addRow(self.item_races)

        def add_race_function():
            add_race()
            self.fill_race_list()
        self.item_new = QPushButton(_('New'))
        self.item_new.clicked.connect(add_race_function)
        self.item_new.setMaximumWidth(max_button_width)
        self.layout.addRow(self.item_new)

        def copy_race_function():
            copy_race()
            self.fill_race_list()
        self.item_copy = QPushButton(_('Copy'))
        self.item_copy.clicked.connect(copy_race_function)
        self.item_copy.setMaximumWidth(max_button_width)
        self.layout.addRow(self.item_copy)

        def move_up_race_function():
            move_up_race()
            self.fill_race_list()
        self.item_move_up = QPushButton(_('Move up'))
        self.item_move_up.clicked.connect(move_up_race_function)
        self.item_move_up.setMaximumWidth(max_button_width)
        self.layout.addRow(self.item_move_up)

        def move_down_race_function():
            move_down_race()
            self.fill_race_list()
        self.item_move_down = QPushButton(_('Move down'))
        self.item_move_down.clicked.connect(move_down_race_function)
        self.item_move_down.setMaximumWidth(max_button_width)
        self.layout.addRow(self.item_move_down)

        def del_race_function():
            del_race()
            self.fill_race_list()
        self.item_del = QPushButton(_('Delete'))
        self.item_del.clicked.connect(del_race_function)
        self.item_del.setMaximumWidth(max_button_width)
        self.layout.addRow(self.item_del)

        self.widget.setLayout(self.layout)

    def save(self):
        pass

    def fill_race_list(self):
        race_list = []
        index = get_current_race_index()

        self.item_races.clear()
        for cur_race in races():
            race_list.append(str(cur_race.data.get_start_datetime()))
        self.item_races.addItems(race_list)

        self.item_races.setCurrentIndex(index)


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.widgets = [
            (MainTab(self), _('Main settings')),
            (SoundTab(self), _('Sounds')),
            (MultidayTab(self), _('Multi day')),
        ]

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Settings'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.tab_widget = QTabWidget()

        for tab, title in self.widgets:
            self.tab_widget.addTab(tab.widget, title)

        self.layout = QFormLayout(self)
        self.layout.addRow(self.tab_widget)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.exception(e)
            self.close()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(_('OK'))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.show()

    def apply_changes_impl(self):
        for tab, _ in self.widgets:
            tab.save()
        Config().save()
