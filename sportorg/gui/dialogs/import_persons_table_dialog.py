import logging
from enum import Enum

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QApplication,
)

from sportorg import config
from sportorg.gui.dialogs.text_io import set_property
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models import memory
from sportorg.models.memory import find, race, Sex
from sportorg.utils.time import ddmmyyyy_to_time


class ImportPersonsTableDialog(QDialog):
    _header_indexes = []

    class ExtendedEnum(Enum):
        @classmethod
        def list(cls):
            return list(map(lambda c: c.value, cls))

        @classmethod
        def name(cls, val):
            return {v: k for k, v in dict(vars(cls)).items() if isinstance(v, int)}.get(
                val, None
            )

    class HEADER(ExtendedEnum):
        NONE = ""
        BIB = _("Bib")
        GROUP = _("Group")
        TEAM = _("Team")
        TEAM_NUMBER = _("Team number")
        NAME = _("First name")
        SURNAME = _("Last name")
        SURNAME_NAME = _("Surname and name")
        YEAR = _("Year of birth")
        BIRTHDAY = _("Birthday")
        SEX = _("Sex")
        QUAL = _("Qualification")
        CARD = _("Card number")
        COMMENT = _("Comment")
        CONTACT = _("Contact")
        PAID = _("Paid")
        START = _("Start")
        FINISH = _("Finish")
        START_GROUP = _("Start group")

    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_("Import persons from table (clipboard)"))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(True)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.REPLACEMENT_BY_BIB = _("Replacement by bib")
        self.REPLACEMENT_BY_NAME = _("Replacement by name")
        self.INSERT_NEW = _("Insert new records")

        self.option_import = AdvComboBox()
        self.option_import.addItems(
            [self.INSERT_NEW, self.REPLACEMENT_BY_BIB, self.REPLACEMENT_BY_NAME]
        )
        self.layout.addRow(self.option_import)

        self.headers = self.HEADER.list()

        copied_values = self.parse_clipboard_value()

        self.count_rows = len(copied_values)
        self.count_columns = len(copied_values[0]) if len(copied_values) else 0

        self.persons_info_table = QTableWidget(self)
        self.persons_info_table.setRowCount(self.count_rows + 1)
        self.persons_info_table.setColumnCount(self.count_columns)

        for i in range(self.count_columns):
            header_import = AdvComboBox()
            header_import.addItems(self.headers)

            if i < len(self._header_indexes):
                index = header_import.findText(self._header_indexes[i])
                if index >= 0:
                    header_import.setCurrentIndex(index)
            self.persons_info_table.setCellWidget(0, i, header_import)

        for idRow, row in enumerate(copied_values):
            for idColumn, cell in enumerate(row):
                new_item = QTableWidgetItem(cell)
                self.persons_info_table.setItem(idRow + 1, idColumn, new_item)

        self.layout.addRow(self.persons_info_table)

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
        self.button_ok.setText(_("OK"))
        self.button_ok.clicked.connect(apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_("Cancel"))
        self.button_cancel.clicked.connect(cancel_changes)
        self.layout.addRow(button_box)

        self.resize(900, 300)
        self.show()

    def apply_changes_impl(self):
        self.import_data()
        return

    def closeEvent(self, event):
        self.__class__._header_indexes = [
            self.persons_info_table.cellWidget(0, i).currentText()
            for i in range(self.persons_info_table.columnCount())
        ]
        event.accept()

    @staticmethod
    def parse_clipboard_value():
        text = QApplication.clipboard().text()
        output_list = []
        for row in filter(None, text.splitlines()):
            output_list.append(row.split("\t"))
        return output_list

    def import_data(self):
        obj = race()
        self.input_headers = {}
        for i in range(self.count_columns):
            item = self.persons_info_table.cellWidget(0, i)
            self.input_headers[self.HEADER(item.currentText())] = i

        for i in range(1, self.count_rows + 1):
            person: memory.Person = None
            if self.option_import.currentText() == self.INSERT_NEW:
                person = memory.Person()

            if self.option_import.currentText() == self.REPLACEMENT_BY_BIB:
                if self.HEADER.BIB not in self.input_headers:
                    logging.error("{}".format(_("Bib header not found")))
                    break
                bib = self.get_value_table(i, self.HEADER.BIB)
                if not bib.isdigit():
                    logging.error("{}".format(_("Bib not found") + ":" + bib))
                    continue
                person = find(race().persons, bib=int(bib))
                if person is None:
                    logging.error("{}".format(_("Bib not found") + ":" + bib))
                    continue

            name = None
            surname = None
            if self.HEADER.SURNAME_NAME in self.input_headers:
                surname_name = self.get_value_table(i, self.HEADER.SURNAME_NAME)
                surname = surname_name.split()[0]
                name = surname_name.split()[1] if len(surname_name.split()) > 1 else ''
            if self.HEADER.NAME in self.input_headers:
                name = self.get_value_table(i, self.HEADER.NAME)
            if self.HEADER.SURNAME in self.input_headers:
                surname = self.get_value_table(i, self.HEADER.SURNAME)

            if self.option_import.currentText() == self.REPLACEMENT_BY_NAME:
                if not name or not surname:
                    logging.error("{}".format(_("Name header not found")))
                    break
                person = find(race().persons, name=name, surname=surname)
                if person is None:
                    logging.error(
                        "{}".format(
                            _("Person not found") + ":" + name + " " + surname
                        )
                    )
                    continue

            person.name = name
            person.surname = surname

            if self.HEADER.YEAR in self.input_headers:
                year = self.get_value_table(i, self.HEADER.YEAR)
                if year.isdigit():
                    person.set_year(int(self.get_value_table(i, self.HEADER.YEAR)))

            if self.HEADER.GROUP in self.input_headers:
                group_name = self.get_value_table(i, self.HEADER.GROUP)
                group = find(obj.groups, name=group_name)
                if group is None:
                    group = memory.Group()
                    group.name = group_name
                    group.long_name = group_name
                    obj.groups.append(group)
                person.group = group

            team_number = None
            if self.HEADER.TEAM_NUMBER in self.input_headers:
                team_number = self.get_value_table(i, self.HEADER.TEAM_NUMBER)
                if not team_number.isdigit():
                    logging.error("{}".format(_("Unrecognized team number") + ":" + team_number))
                    continue

            if self.HEADER.TEAM in self.input_headers:
                team_name = self.get_value_table(i, self.HEADER.TEAM)
                if team_number is not None:
                    team = find(obj.teams, number=int(team_number))
                else:
                    team = find(obj.teams, name=team_name)
                if team is None:
                    team = memory.Team()
                    team.name = team_name
                    team.group = person.group
                    if team_number is not None:
                        team.number = team_number
                    obj.teams.append(team)
                elif obj.is_team_race():
                    if team.group is None:
                        team.group = person.group
                    elif person.group is not None and team.group != person.group:
                        new_team = team.clone()
                        new_team.group = person.group
                        obj.teams.append(new_team)
                        team = new_team

                person.team = team

            if self.HEADER.BIB in self.input_headers:
                bib = self.get_value_table(i, self.HEADER.BIB)
                if bib != "":
                    set_property(person, self.HEADER.BIB.value, bib)

            if self.HEADER.CARD in self.input_headers:
                card = self.get_value_table(i, self.HEADER.CARD)
                if card != "":
                    set_property(person, self.HEADER.CARD.value, card)

            if self.HEADER.QUAL in self.input_headers:
                qual = self.get_value_table(i, self.HEADER.QUAL)
                if qual != "":
                    set_property(person, self.HEADER.QUAL.value, qual)

            if self.HEADER.SEX in self.input_headers:
                sex_str = self.get_value_table(i, self.HEADER.SEX)
                person.sex = Sex.M if sex_str.lower().strip() in ('м', 'm') else Sex.F

            if self.HEADER.COMMENT in self.input_headers:
                set_property(
                    person,
                    self.HEADER.COMMENT.value,
                    self.get_value_table(i, self.HEADER.COMMENT),
                )

            if self.HEADER.CONTACT in self.input_headers:
                if person.team is not None:
                    person.team.contact = self.get_value_table(i, self.HEADER.CONTACT)

            if self.HEADER.PAID in self.input_headers:
                paid = self.get_value_table(i, self.HEADER.PAID)
                if paid and paid.strip() != "0":
                    person.is_paid = True

            if self.HEADER.START in self.input_headers:
                set_property(
                    person,
                    self.HEADER.START.value,
                    self.get_value_table(i, self.HEADER.START),
                )

            if self.HEADER.FINISH in self.input_headers:
                set_property(
                    person,
                    self.HEADER.FINISH.value,
                    self.get_value_table(i, self.HEADER.FINISH),
                )

            if self.HEADER.START_GROUP in self.input_headers:
                set_property(
                    person,
                    self.HEADER.START_GROUP.value,
                    self.get_value_table(i, self.HEADER.START_GROUP),
                )

            if self.HEADER.BIRTHDAY in self.input_headers:
                birthday = self.get_value_table(i, self.HEADER.BIRTHDAY)
                if birthday != "":
                    person.birth_date = ddmmyyyy_to_time(birthday)

            if self.option_import.currentText() == self.INSERT_NEW and person:
                obj.persons.append(person)

        persons_dupl_cards = obj.get_duplicate_card_numbers()
        persons_dupl_names = obj.get_duplicate_names()

        if len(persons_dupl_cards):
            logging.info(
                "{}".format(
                    _("Duplicate card numbers (card numbers are reset)")
                )
            )
            for person in sorted(persons_dupl_cards, key=lambda x: x.card_number):
                logging.info(
                    "{} {} {} {}".format(
                        person.full_name,
                        person.group.name if person.group else "",
                        person.team.name if person.team else "",
                        person.card_number,
                    )
                )
                person.set_card_number(0)
        if len(persons_dupl_names):
            logging.info("{}".format(_("Duplicate names")))
            for person in sorted(persons_dupl_names, key=lambda x: x.full_name):
                logging.info(
                    "{} {} {} {}".format(
                        person.full_name,
                        person.get_year(),
                        person.group.name if person.group else "",
                        person.team.name if person.team else "",
                    )
                )

    def get_value_table(self, idx, header):
        return (
            self.persons_info_table.item(idx, self.input_headers[header]).text().strip()
        )
