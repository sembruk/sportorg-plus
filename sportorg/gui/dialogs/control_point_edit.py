import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QLabel, QLineEdit, QSpinBox, QDialog, QDialogButtonBox

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race, find
from sportorg.modules.teamwork import Teamwork


class ControlPointEditDialog(QDialog):
    def __init__(self, control_point, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        self.current_object = control_point
        self.is_new = is_new

    def exec_(self):
        self.init_ui()
        self.set_values_from_model()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Control point properties'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_code = QLabel(_('Code'))
        self.item_code = QLineEdit()
        self.item_code.textChanged.connect(self.check_code)
        self.layout.addRow(self.label_code, self.item_code)

        self.label_score = QLabel(_('Score'))
        self.item_score = QSpinBox()
        self.item_score.setMinimum(0)
        self.item_score.setMaximum(10000)
        self.layout.addRow(self.label_score, self.item_score)

        self.label_x = QLabel(_('X, meters'))
        self.item_x= QSpinBox()
        self.item_x.setMinimum(-10000000)
        self.item_x.setMaximum(10000000)
        self.layout.addRow(self.label_x, self.item_x)

        self.label_y = QLabel(_('Y, meters'))
        self.item_y = QSpinBox()
        self.item_y.setMinimum(-10000000)
        self.item_y.setMaximum(10000000)
        self.layout.addRow(self.label_y, self.item_y)

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

    def check_code(self):
        code = self.item_code.text()
        self.button_ok.setDisabled(False)
        if code and code != self.current_object.code:
            cp = find(race().control_points, code=code)
            if cp:
                self.button_ok.setDisabled(True)

    def set_values_from_model(self):
        self.item_code.setText(self.current_object.code)
        self.item_code.selectAll()
        self.item_score.setValue(self.current_object.score)
        self.item_x.setValue(self.current_object.x)
        self.item_y.setValue(self.current_object.y)

    def apply_changes_impl(self):
        cp = self.current_object
        if self.is_new:
            race().control_points.insert(0, cp)

        cp.code = self.item_code.text()
        cp.score = self.item_score.value()
        cp.x = self.item_x.value()
        cp.y = self.item_y.value()

        Teamwork().send(cp.to_dict())

