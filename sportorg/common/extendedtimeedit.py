from PySide2.QtWidgets import QTimeEdit, QHBoxLayout, QSpinBox, QWidget, QLabel
from PySide2.QtCore import QTime, Qt, QEvent

class DurationEdit(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create layout and widgets
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.timeEdit = QTimeEdit()
        self.timeEdit.setDisplayFormat("hh:mm:ss")

        self.daysSpin = QSpinBox()
        self.daysSpin.setRange(0, 9)
        self.daysSpin.setValue(0)
        self.daysSpin.setMaximumWidth(45)
        self.daysLabel1 = QLabel("+")
        self.daysLabel2 = QLabel("дней")

        layout.addWidget(self.timeEdit)
        layout.addWidget(self.daysLabel1)
        layout.addWidget(self.daysSpin)
        layout.addWidget(self.daysLabel2)
        layout.addStretch()
        
    def seconds(self):
        return (self.daysSpin.value()*86400 +
                self.timeEdit.time().hour()*3600 +
                self.timeEdit.time().minute()*60 +
                self.timeEdit.time().second())
        
    def setSeconds(self, sec):
        self.daysSpin.setValue(sec//86400)
        self.timeEdit.setTime(QTime(sec%86400//3600, sec%3600//60, sec%60))

