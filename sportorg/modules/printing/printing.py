import sys
import platform
import logging
from multiprocessing import Process

from PySide2.QtCore import QSizeF
from PySide2.QtGui import QTextDocument
from PySide2.QtPrintSupport import QPrinter, QPrinterInfo
from PySide2.QtWidgets import QApplication

from sportorg.common.fake_std import FakeStd


class PrintProcess(Process):
    def __init__(self, printer_name, html, left=5.0, top=5.0, right=5.0, bottom=5.0, scale=1.0):
        super().__init__()
        self.printer_name = printer_name
        self.html = html
        self.margin_left = left
        self.margin_top = top
        self.margin_right = right
        self.margin_bottom = bottom
        self.scale = 1
        if scale > 0:
            self.scale = scale

    def run(self):
        try:
            sys.stdout = FakeStd()
            sys.stderr = FakeStd()
            if platform.system() == 'Windows':
                app = QApplication.instance()
                if app is None:
                    app = QApplication(['--platform', 'minimal'])
                # we need this call to correctly render images...
                app.processEvents()

            printer = QPrinter()
            if self.printer_name:
                printer.setPrinterName(self.printer_name)
                printer_info = QPrinterInfo.printerInfo(self.printer_name)
                if not printer_info.isNull():
                    printer.setPageSize(printer_info.defaultPageSize())
            else:
                # Print to file
                filename = '/tmp/print.pdf'
                logging.info('print to file: ' + filename)
                printer.setOutputFileName(filename)
                #printer.setResolution(96)

            text_document = QTextDocument()

            printer.setFullPage(True)
            printer.setPageMargins(
                self.margin_left,
                self.margin_top,
                self.margin_right,
                self.margin_bottom,
                QPrinter.Millimeter
            )

            page_size = QSizeF()
            page_size.setHeight(printer.height()/self.scale)
            page_size.setWidth(printer.width()/self.scale)
            text_document.setPageSize(page_size)
            text_document.setDocumentMargin(0.0)

            text_document.setHtml(self.html)
            text_document.print_(printer)
        except Exception as e:
            logging.exception(e)


def print_html(printer_name, html, left=5.0, top=5.0, right=5.0, bottom=5.0, scale=100):
    thread = PrintProcess(printer_name, html, left, top, right, bottom, scale/100.0)
    thread.start()
    logging.info('printing poccess started')
