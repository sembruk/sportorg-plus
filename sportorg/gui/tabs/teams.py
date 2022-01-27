import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtWidgets import QAbstractItemView, QHeaderView

from sportorg.gui.dialogs.team_edit import TeamEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.tabs.memory_model import TeamMemoryModel
from sportorg.gui.tabs.table import TableView
from sportorg.models.memory import race


class TeamsTableView(TableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup_items = []


class Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.team_table = TeamsTableView(self)
        self.team_layout = QtWidgets.QGridLayout(self)
        self.setup_ui()

    def setup_ui(self):

        self.team_table.setObjectName('TeamTable')
        self.team_table.setModel(TeamMemoryModel())

        def team_double_clicked(index):
            try:
                if index.row() < len(race().teams):
                    dialog = TeamEditDialog(race().teams[index.row()])
                    dialog.exec_()
                    GlobalAccess().get_main_window().refresh()
            except Exception as e:
                logging.error(str(e))

        self.team_table.activated.connect(team_double_clicked)
        self.team_layout.addWidget(self.team_table)

    def get_table(self):
        return self.team_table
