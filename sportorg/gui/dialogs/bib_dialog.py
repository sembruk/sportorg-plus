import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QLabel, QDialog, QDialogButtonBox, QLineEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models import memory


class BibDialog(QDialog):
    def __init__(self, text=''):
        super().__init__(GlobalAccess().get_main_window())
        self.text = text
        self.person = None
        self.tmp_person = None

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Find person'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        if self.text:
            self.label_text = QLabel(self.text)
            self.layout.addRow(self.label_text)

        self.label_person = QLabel(_('Person'))
        self.item_person = AdvComboBox()
        self.add_persons()
        self.item_person.setCurrentText('')
        self.item_person.currentTextChanged.connect(self.show_person_info)
        self.layout.addRow(self.label_person, self.item_person)

        self.label_person_info = QLabel('')
        self.layout.addRow(self.label_person_info)

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

    def add_persons(self):
        person_list = []
        for person in memory.race().persons:
            person_list.append(('{} {} ({})'.format(person.full_name, person.get_year(), person.bib), person))
        person_list.sort(key=lambda x: x[0])
        for p in person_list:
            self.item_person.addItem(p[0], p[1])

    def show_person_info(self, text):
        if not text:
            return

        index = self.item_person.findText(text)
        person = None
        if index != 1:
            person = self.item_person.itemData(index)

        if person:
            info = person.full_name
            if person.group:
                info = '{}\n{}: {}'.format(info, _('Group'), person.group.name)
            if person.card_number:
                info = '{}\n{}: {}'.format(info, _('Card'), person.card_number)
            self.label_person_info.setText(info)
        else:
            self.label_person_info.setText(_('not found'))
        self.tmp_person = person

    def get_person(self):
        return self.person

    def found_person(self):
        return self.person

    def apply_changes_impl(self):
        self.person = self.tmp_person
