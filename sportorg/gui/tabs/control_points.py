import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.gui.dialogs.control_point_edit import ControlPointEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.tabs.memory_model import ControlPointMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race


class ControlPointsTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.control_points_table = ControlPointsTableView(self)
        self.control_points_layout = QtWidgets.QGridLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.control_points_table.setObjectName('ControlPointTable')
        self.control_points_table.setModel(ControlPointMemoryModel())

        def control_point_double_clicked(index):
            try:
                if index.row() < len(race().control_points):
                    dialog = ControlPointEditDialog(race().control_points[index.row()])
                    dialog.exec_()
                    GlobalAccess().get_main_window().refresh()
                    pass
            except Exception as e:
                logging.error(str(e))

        self.control_points_table.activated.connect(control_point_double_clicked)
        self.control_points_layout.addWidget(self.control_points_table)

    def get_table(self):
        return self.control_points_table
