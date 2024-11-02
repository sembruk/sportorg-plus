import os
import logging
from PySide2.QtGui import QIcon
from PySide2.QtCore import QUrl
from PySide2.QtWidgets import QFormLayout, QDialog, QTextBrowser, QDialogButtonBox

from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg import config

class TextBrowser(QTextBrowser):
    def setSource(self, filename):
        if isinstance(filename, QUrl):
            if filename.isRelative():
                current_url = self.source()
                current_path = current_url.path() if current_url.isValid() else ''
                filename = os.path.join(os.path.dirname(current_path), filename.toString())
        logging.debug(f'Open: {filename}')
        super().setSource(filename)

class HelpDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Help'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        #self.setModal(True)
        #self.setStyleSheet("background:white")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.layout = QFormLayout(self)

        text_browser = TextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setSearchPaths(['docs'])
        text_browser.setSource('index.md')
        text_browser.document().adjustSize()

        self.layout.addRow(text_browser)

        button_box = QDialogButtonBox(QDialogButtonBox.Reset | QDialogButtonBox.Close)
        button_back = button_box.button(QDialogButtonBox.Reset)
        button_back.setText(_('Back'))
        button_back.setEnabled(False)
        button_forward = button_box.addButton(_('Forward'), QDialogButtonBox.ResetRole)
        button_forward.setEnabled(False)
        button_close = button_box.button(QDialogButtonBox.Close)
        button_close.setText(_('Close'))
        button_close.setDefault(True)
        self.layout.addRow(button_box)

        text_browser.backwardAvailable.connect(button_back.setEnabled)
        text_browser.forwardAvailable.connect(button_forward.setEnabled)
        button_back.clicked.connect(text_browser.backward)
        button_forward.clicked.connect(text_browser.forward)
        button_close.clicked.connect(self.accept)

        #text_browser.sourceChanged.connect(lambda url, tb=text_browser: print(url, tb.source(), tb.searchPaths()))

        self.show()

