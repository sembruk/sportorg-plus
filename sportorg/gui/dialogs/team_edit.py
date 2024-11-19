import logging

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QLabel, QLineEdit, QSpinBox, QDialog, QDialogButtonBox, QTableWidget, \
    QTableWidgetItem, QHeaderView, QHBoxLayout, QVBoxLayout, QPushButton
from PySide2.QtCore import Qt

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.gui.dialogs.bib_dialog import BibDialog
from sportorg.language import _
from sportorg.models.constant import get_countries, get_regions, get_race_groups
from sportorg.models.memory import race, Team, find, Limit
from sportorg.models.start.start_preparation import update_subgroups
from sportorg.modules.live.live import live_client
from sportorg.modules.teamwork import Teamwork

class QTableWidgetItemNotEditable(QTableWidgetItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlags(~Qt.ItemIsEditable)

class TeamEditDialog(QDialog):
    def __init__(self, team, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        self.current_object = team
        self.is_new = is_new

    def exec_(self):
        self.init_ui()
        self.set_values_from_model()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Team properties'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_name = QLabel(_('Name'))
        self.item_name = QLineEdit()
        #self.item_name.textChanged.connect(self.check_name)
        self.layout.addRow(self.label_name, self.item_name)

        self.label_number = QLabel(_('Number'))
        self.item_number= QSpinBox()
        self.item_number.setMinimum(0)
        self.item_number.setMaximum(10000000)
        self.item_number.valueChanged.connect(self.check_number)
        self.layout.addRow(self.label_number, self.item_number)

        self.label_group = QLabel(_('Group'))
        self.item_group = AdvComboBox()
        self.item_group.addItems(get_race_groups())
        self.layout.addRow(self.label_group, self.item_group)

        self.label_code = QLabel(_('Code'))
        self.item_code = QLineEdit()
        self.layout.addRow(self.label_code, self.item_code)

        self.label_country = QLabel(_('Country'))
        self.item_country = AdvComboBox()
        self.item_country.addItems(get_countries())
        self.layout.addRow(self.label_country, self.item_country)

        self.label_region = QLabel(_('Region'))
        self.item_region = AdvComboBox()
        self.item_region.addItems(get_regions())
        self.layout.addRow(self.label_region, self.item_region)

        self.label_contact = QLabel(_('Contact'))
        self.item_contact = QLineEdit()
        self.layout.addRow(self.label_contact, self.item_contact)

        self.members_table = QTableWidget(0, 4)
        self.members_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.members_table.setSelectionMode(QTableWidget.SingleSelection)
        self.members_table.setHorizontalHeaderLabels( (_("Last name"), _("First name"), _("Year title"), _("Bib")) )
        self.members_table.verticalHeader().setVisible(False)
        self.members_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.add_member_button = QPushButton(_('Add'))
        self.add_member_button.clicked.connect(self.add_member)
        self.delete_member_button = QPushButton(_('Delete'))
        self.delete_member_button.setToolTip(_('Move selected member to new team'))
        self.delete_member_button.clicked.connect(self.delete_member)
        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.add_member_button)
        vbox_layout.addWidget(self.delete_member_button)
        vbox_layout.addStretch()
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(self.members_table)
        hbox_layout.addLayout(vbox_layout)
        self.layout.addRow(hbox_layout)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except Exception as e:
                logging.error(str(e))
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

    def add_member(self):
        bib_dialog = BibDialog()
        bib_dialog.exec_()
        person = bib_dialog.get_person()
        if person:
            person.team = self.current_object
            self.add_person_to_table(person)

    def delete_member(self):
        row = self.members_table.currentRow()
        if row >= 0:
            person_id = self.members_table.item(row, 0).data(Qt.UserRole)
            team = race().add_new_team(append_to_race=True)
            team.name = self.current_object.name + '-2'
            team.group = self.current_object.group
            person = find(race().persons, id=person_id)
            person.team = team
            self.members_table.removeRow(row)

    def check_name(self):
        name = self.item_name.text()
        self.button_ok.setDisabled(False)
        if name and name != self.current_object.name:
            team = find(race().teams, name=name)
            if team:
                self.button_ok.setDisabled(True)

    def check_number(self):
        number = self.item_number.value()
        self.button_ok.setDisabled(False)
        if number and number != self.current_object.number:
            team = find(race().teams, number=number)
            if team:
                self.button_ok.setDisabled(True)

    def set_values_from_model(self):
        self.item_name.setText(self.current_object.name)
        self.item_name.selectAll()
        self.item_number.setValue(self.current_object.number)
        if self.current_object.group:
            self.item_group.setCurrentText(self.current_object.group.name)
        else:
            self.item_group.setCurrentText('')
        self.item_code.setText(str(self.current_object.code))
        self.item_country.setCurrentText(self.current_object.country)
        self.item_region.setCurrentText(self.current_object.region)
        self.item_contact.setText(self.current_object.contact)

        members = race().get_persons_by_team(self.current_object)
        if members:
            for person in members:
                self.add_person_to_table(person)

    def add_person_to_table(self, person):
        r = self.members_table.rowCount()
        self.members_table.insertRow(r)
        surname_item = QTableWidgetItemNotEditable(person.surname)
        surname_item.setData(Qt.UserRole, person.id)
        self.members_table.setItem(r, 0, surname_item)
        self.members_table.setItem(r, 1, QTableWidgetItemNotEditable(person.name))
        self.members_table.setItem(r, 2, QTableWidgetItemNotEditable(str(person.get_year())))
        self.members_table.setItem(r, 3, QTableWidgetItemNotEditable(str(person.bib)))

    def apply_changes_impl(self):
        team = self.current_object
        if self.is_new:
            race().teams.insert(0, team)

        team.number = self.item_number.value()
        team.name = self.item_name.text()
        if (team.group and team.group.name != self.item_group.currentText()) or\
                (team.group is None and len(self.item_group.currentText()) > 0):
            team.group = find(race().groups, name=self.item_group.currentText())

        team.code = self.item_code.text()
        team.country = self.item_country.currentText()
        team.region = self.item_region.currentText()
        team.contact = self.item_contact.text()

        team.update_subgroups()
        race().update_team_max_number()
        race().update_team_person_counters()

        live_client.send(team)
        Teamwork().send(team.to_dict())
