from PySide2.QtWidgets import QTimeEdit, QHBoxLayout, QSpinBox, QWidget, QLabel
from PySide2.QtCore import QTime, Qt, QEvent

class DurationEdit(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create layout and widgets
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.daysSpin = QSpinBox()
        self.daysSpin.setRange(0, 99)
        self.daysSpin.setValue(0)
        self.daysLabel = QLabel("дней")

        self.timeEdit = QTimeEdit()
        self.timeEdit.setDisplayFormat("hh:mm:ss")

        layout.addWidget(self.daysSpin)
        layout.addWidget(self.daysLabel)
        layout.addWidget(self.timeEdit)
        
    def seconds(self):
        return (self.daysSpin.value()*86400 +
                self.timeEdit.time().hour()*3600 +
                self.timeEdit.time().minute()*60 +
                self.timeEdit.time().second())
        
    def setSeconds(self, sec):
        self.daysSpin.setValue(sec//86400)
        self.timeEdit.setTime(QTime(sec%86400//3600, sec%3600//60, sec%60))

