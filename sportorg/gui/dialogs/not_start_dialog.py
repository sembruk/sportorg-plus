import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QLabel, QDialog, QDialogButtonBox, QTextEdit

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.constant import StatusComments
from sportorg.models.memory import race, ResultStatus, find, ResultManual
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.modules.live.live import live_client
from sportorg.modules.teamwork import Teamwork


class NotStartDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Not started numbers'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_controls = QLabel(_('Bibs'))
        self.item_numbers = QTextEdit()
        self.item_numbers.setPlaceholderText(_('1 4 15 25\n58 32\n33\n34\n...\n150\n'))

        self.layout.addRow(self.label_controls, self.item_numbers)

        self.label_status_comment = QLabel(_('Status comment'))
        self.item_status_comment = AdvComboBox()
        self.item_status_comment.addItems(StatusComments().get_all())

        self.layout.addRow(self.label_status_comment, self.item_status_comment)

        def cancel_changes():
            self.person = None
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
        status_comment = StatusComments().remove_hint(self.item_status_comment.currentText())
        text = self.item_numbers.toPlainText()
        numbers = []
        for item in text.split('\n'):
            if not len(item):
                continue
            for n_item in item.split():
                if n_item.isdigit():
                    numbers.append(int(n_item))
        old_numbers = []
        obj = race()
        for number in numbers:
            if number not in old_numbers:
                person = find(obj.persons, bib=number)
                if person:
                    old_result = find(obj.results, person=person)
                    if old_result:
                        logging.info(_('Result of {} already exists').format(person))
                        continue
                    result = race().new_result(ResultManual)
                    result.person = person
                    result.status = ResultStatus.DID_NOT_START
                    result.status_comment = status_comment
                    live_client.send(result)
                    Teamwork().send(result.to_dict())
                    obj.add_new_result(result)
                else:
                    logging.info(_('Person with bib {} not found').format(number))
                old_numbers.append(number)
        ResultCalculation(race()).process_results()
