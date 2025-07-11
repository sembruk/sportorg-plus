from PySide2.QtWidgets import QTimeEdit, QApplication
from PySide2.QtCore import QTime, Qt, QEvent
from PySide2.QtGui import QKeyEvent, QValidator

class ExtendedTimeEdit(QTimeEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDisplayFormat("HH:mm:ss")
        self.setTime(QTime(0, 0, 0))
        
    def stepBy(self, steps):
        section = self.currentSection()
        time = self.time()
        
        if section == self.HourSection:
            new_hour = time.hour() + steps
            self.setTime(QTime(new_hour, time.minute(), time.second()))
        else:
            super().stepBy(steps)
            
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            step = 1 if event.key() == Qt.Key_Up else -1
            self.stepBy(step)
        else:
            super().keyPressEvent(event)
            
    def validate(self, input_text, pos):
        try:
            parts = input_text.split(':')
            if len(parts) > 0:
                hours = int(parts[0])
                if hours >= 0:  # Allow any positive hour value
                    return (QValidator.Acceptable, input_text, pos)
        except ValueError:
            pass
        return super().validate(input_text, pos)
        
    def time(self):
        return super().time()

