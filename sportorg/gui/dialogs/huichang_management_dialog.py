import logging

from PySide2.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QSpinBox,
    QLabel
)

from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _


class HuichangManagementDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        logging.debug('Init huichang management dialog')
        self.setWindowTitle(_('Huichang Management'))
        self.setMinimumSize(400, 300)
        self.layout = QVBoxLayout(self)

        self.timeGroupBox = QGroupBox(_('Time Calibration'))
        self.timeLayout = QVBoxLayout(self.timeGroupBox)

        self.timeSyncButton = QPushButton(_('Time Sync'))
        self.timeLayout.addWidget(self.timeSyncButton)

        self.layout.addWidget(self.timeGroupBox)

        self.stationNumberGroupBox = QGroupBox(_('Station Number'))
        self.stationNumberLayout = QHBoxLayout(self.stationNumberGroupBox)

        self.stationSpin = QSpinBox()
        self.stationSpin.setRange(1, 255)
        self.stationSpin.setValue(31)
        self.stationNumberApplyButton = QPushButton(_('Apply'))
        self.stationNumberLayout.addWidget(self.stationSpin)
        self.stationNumberLayout.addWidget(self.stationNumberApplyButton)

        self.layout.addWidget(self.stationNumberGroupBox)

        self.show()

