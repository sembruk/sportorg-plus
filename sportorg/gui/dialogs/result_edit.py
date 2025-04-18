import logging

from abc import abstractmethod

from datetime import datetime

from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QLabel, QLineEdit, QDialog, \
    QTimeEdit, QSpinBox, QGroupBox, QTextEdit, QDialogButtonBox, QComboBox

from sportorg import config
from sportorg.gui.dialogs.person_edit import PersonEditDialog
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.constant import StatusComments
from sportorg.models.memory import race, Result, find, ResultStatus, Person, Limit, Split
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.result_checker import ResultChecker, ResultCheckerException
from sportorg.models.result.split_calculation import GroupSplits
from sportorg.modules.live.live import live_client
from sportorg.modules.teamwork import Teamwork
from sportorg.utils.time import time_to_qtime, time_to_otime, hhmmss_to_time


class ResultEditDialog(QDialog):
    control_was_pressed = False;

    def __init__(self, result, is_new=False):
        super().__init__(GlobalAccess().get_main_window())
        self.current_object = result
        self.is_new = is_new

        self.time_format = 'hh:mm:ss'
        time_accuracy = race().get_setting('time_accuracy', 0)
        if time_accuracy:
            self.time_format = 'hh:mm:ss.zzz'

    def exec_(self):
        self.init_ui()
        self.set_values_from_model()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Result'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        self.setMaximumWidth(300)

        self.layout = QFormLayout(self)

        self.item_created_at = QTimeEdit()
        self.item_created_at.setDisplayFormat(self.time_format)
        self.item_created_at.setReadOnly(True)

        self.item_card_number = QSpinBox()
        self.item_card_number.setMaximum(9999999)

        self.item_bib = QSpinBox()
        self.item_bib.setMaximum(Limit.BIB)
        self.item_bib.valueChanged.connect(self.show_person_info)

        self.label_person_info = QLabel('')

        self.item_days = QSpinBox()
        self.item_days.setMaximum(365)

        self.item_finish = QTimeEdit()
        self.item_finish.setDisplayFormat(self.time_format)

        self.item_start = QTimeEdit()
        self.item_start.setDisplayFormat(self.time_format)

        self.item_time = QTimeEdit()
        self.item_time.setDisplayFormat(self.time_format)
        self.item_time.setEnabled(False)

        self.item_result = QLineEdit()
        self.item_result.setEnabled(False)

        self.item_credit = QTimeEdit()
        self.item_credit.setDisplayFormat(self.time_format)

        self.item_penalty = QTimeEdit()
        self.item_penalty.setDisplayFormat(self.time_format)

        self.item_penalty_points = QSpinBox()
        self.item_penalty_points.setEnabled(False)

        self.item_penalty_laps = QSpinBox()
        self.item_penalty_laps.setMaximum(1000000)

        self.item_status = QComboBox()
        status_titles = [s.get_title() for s in ResultStatus if s not in (ResultStatus.MISSING_PUNCH, ResultStatus.OVERTIME)]
        self.item_status.addItems(status_titles)

        self.item_status_comment = AdvComboBox()
        self.item_status_comment.setMaximumWidth(300)
        self.item_status_comment.view().setMinimumWidth(600)
        self.item_status_comment.addItems(StatusComments().get_all())
        for i, k in enumerate(StatusComments().get_all()):
            self.item_status_comment.setItemData(i, k, Qt.ToolTipRole)

        more24 = race().get_setting('time_format_24', 'less24') == 'more24'
        self.splits = SplitsText(more24=more24)

        self.layout.addRow(QLabel(_('Created at')), self.item_created_at)
        if self.current_object.is_punch():
            self.layout.addRow(QLabel(_('Card number')), self.item_card_number)
        self.layout.addRow(QLabel(_('Bib')), self.item_bib)
        self.layout.addRow(QLabel(''), self.label_person_info)
        if more24:
            self.layout.addRow(QLabel(_('Days')), self.item_days)
        self.layout.addRow(QLabel(_('Start')), self.item_start)
        self.layout.addRow(QLabel(_('Finish')), self.item_finish)
        if race().get_setting('result_processing_mode', 'time') == 'scores':
            self.layout.addRow(QLabel(_('Time')), self.item_time)
        self.layout.addRow(QLabel(_('Credit')), self.item_credit)
        self.layout.addRow(QLabel(_('Penalty')), self.item_penalty)
        if race().get_setting('result_processing_mode', 'time') == 'scores':
            self.layout.addRow(QLabel(_('Penalty points')), self.item_penalty_points)
        else:
            self.layout.addRow(QLabel(_('Penalty legs')), self.item_penalty_laps)
        self.layout.addRow(QLabel(_('Result')), self.item_result)
        self.layout.addRow(QLabel(_('Status')), self.item_status)
        self.layout.addRow(QLabel(_('Comment')), self.item_status_comment)

        if self.current_object.is_punch():
            start_source = race().get_setting('system_start_source', 'protocol')
            finish_source = race().get_setting('system_finish_source', 'station')
            if start_source == 'protocol' or start_source == 'cp' or start_source == 'group':
                #self.item_start.setDisabled(True)
                pass
            if finish_source == 'cp':
                self.item_finish.setDisabled(True)
            self.layout.addRow(self.splits.widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_ok = button_box.button(QDialogButtonBox.Ok)
        self.button_ok.setText(_('OK'))
        self.button_ok.clicked.connect(self.apply_changes)
        self.button_cancel = button_box.button(QDialogButtonBox.Cancel)
        self.button_cancel.setText(_('Cancel'))
        self.button_cancel.clicked.connect(self.cancel_changes)

        if self.current_object.person:
            button_person = button_box.addButton(_('Entry properties'), QDialogButtonBox.ActionRole)
            button_person.clicked.connect(self.open_person)

        self.layout.addRow(button_box)

        self.show()
        self.item_bib.setFocus()

    def cancel_changes(self):
        self.close()

    def apply_changes(self):
        try:
            self.apply_changes_impl()
        except Exception as e:
            logging.exception(e)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel_changes()
        if event.key() == Qt.Key_Control:
            self.control_was_pressed = True
        if event.key() in [Qt.Key_Return, Qt.Key_Enter] and self.control_was_pressed:
            self.apply_changes()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.control_was_pressed = False

    def show_person_info(self):
        bib = self.item_bib.value()
        self.label_person_info.setText('')
        if bib:
            person = find(race().persons, bib=bib)
            if person:
                info = person.full_name
                if person.group:
                    info = '{}\n{}: {}'.format(info, _('Group'), person.group.name)
                if person.card_number:
                    info = '{}\n{}: {}'.format(info, _('Card'), person.card_number)
                self.label_person_info.setText(info)
            else:
                self.label_person_info.setText(_('not found'))

    def set_values_from_model(self):
        if self.current_object.is_punch():
            if self.current_object.card_number:
                self.item_card_number.setValue(int(self.current_object.card_number))
            self.splits.splits(self.current_object.splits)
            self.splits.show()
        if self.current_object.created_at:
            self.item_created_at.setTime(time_to_qtime(datetime.fromtimestamp(self.current_object.created_at)))
        if self.current_object.finish_time:
            self.item_finish.setTime(time_to_qtime(self.current_object.finish_time))
        #if race().get_setting('system_start_source', 'protocol') == 'group':
        #    if self.current_object.person.group and self.current_object.person.group.start_time:
        #        self.item_start.setTime(time_to_qtime(self.current_object.person.group.start_time))
        #elif self.current_object.start_time:
        #    self.item_start.setTime(time_to_qtime(self.current_object.start_time))
        #elif self.current_object.person.start_time:
        #    self.item_start.setTime(time_to_qtime(self.current_object.person.start_time))
        self.item_start.setTime(time_to_qtime(self.current_object.get_start_time()))
        self.item_time.setTime(time_to_qtime(self.current_object.get_result_otime()))
        if self.current_object.finish_time:
            self.item_result.setText(str(self.current_object.get_result()))
        if self.current_object.credit_time:
            self.item_credit.setTime(time_to_qtime(self.current_object.credit_time))
        if self.current_object.penalty_time:
            self.item_penalty.setTime(time_to_qtime(self.current_object.penalty_time))
        if self.current_object.penalty_points:
            self.item_penalty_points.setValue(self.current_object.penalty_points)
        if self.current_object.penalty_laps:
            self.item_penalty_laps.setValue(self.current_object.penalty_laps)
        self.item_bib.setValue(self.current_object.get_bib())

        self.item_days.setValue(self.current_object.days)

        status = self.current_object.status.get_title()
        if self.item_status.findText(status) == -1:  # not found
            self.item_status.addItem(status)

        self.item_status.setCurrentText(status)

        self.item_status_comment.setCurrentText(self.current_object.status_comment)

        self.item_bib.selectAll()

    def open_person(self):
        try:
            PersonEditDialog(self.current_object.person).exec_()
        except Exception as e:
            logging.exception(e)

    def apply_changes_impl(self):
        result = self.current_object
        if self.is_new:
            race().results.insert(0, result)

        if result.is_punch():
            if result.card_number != self.item_card_number.value():
                result.card_number = self.item_card_number.value()

            new_splits = self.splits.splits()
            if len(result.splits) == len(new_splits):
                for i, split in enumerate(result.splits):
                    if split != new_splits[i]:
                        break
            result.splits = new_splits

        time_ = time_to_otime(self.item_finish.time())
        if result.finish_time != time_:
            result.finish_time = time_

        time_ = time_to_otime(self.item_start.time())
        if self.item_start.isEnabled() and result.start_time != time_:
            result.start_time = time_

        time_ = time_to_otime(self.item_credit.time())
        if result.credit_time != time_:
            result.credit_time = time_

        time_ = time_to_otime(self.item_penalty.time())
        if result.penalty_time != time_:
            result.penalty_time = time_

        if result.penalty_laps != self.item_penalty_laps.value():
            result.penalty_laps = self.item_penalty_laps.value()

        cur_bib = -1
        new_bib = self.item_bib.value()
        if result.person:
            cur_bib = result.person.bib

        if new_bib == 0:
            if result.person and result.is_punch():
                if result.person.card_number == result.card_number:
                    result.person.card_number = 0
            result.person = None
        elif cur_bib != new_bib:
            new_person = find(race().persons, bib=new_bib)
            if new_person:
                if result.person:
                    if result.is_punch():
                        result.person.card_number = 0
                result.person = new_person
                if result.is_punch():
                    race().person_card_number(result.person, result.card_number)
            result.bib = new_bib

            GlobalAccess().get_main_window().get_result_table().model().init_cache()

        if self.item_days.value() != result.days:
            result.days = self.item_days.value()

        result.status = ResultStatus.get_by_name(self.item_status.currentText())

        status = StatusComments().remove_hint(self.item_status_comment.currentText())
        if result.status_comment != status:
            result.status_comment = status

        if result.is_punch():
            result.clear()
            try:
                ResultChecker.checking(result)
                if race().is_team_race() and result.person and result.person.team:
                    team = result.person.team
                    if team.result:
                        for r in team.result.members_results:
                            if r is not result:
                                ResultChecker.checking(r)
                if result.person and result.person.group:
                    GroupSplits(race(), result.person.group).generate(True)
            except ResultCheckerException as e:
                logging.exception(e)
        ResultCalculation(race()).process_results()
        if race().is_team_race() and result.person and result.person.team:
            live_client.send(result.person.team)
        else:
            live_client.send(result)
        self.close()
        Teamwork().send(result.to_dict())


class SplitsObject:
    @property
    @abstractmethod
    def widget(self):
        pass

    @abstractmethod
    def splits(self, splits=None):
        pass

    @abstractmethod
    def show(self):
        pass


class SplitsText(SplitsObject):
    def __init__(self, splits=None, more24=False):
        self._splits = splits
        self._more24 = more24
        self._box = QGroupBox(_('Splits'))
        self._layout = QFormLayout()
        self._text = QTextEdit()
        self._text.setTabChangesFocus(True)
        self._text.setMinimumHeight(200)
        self._layout.addRow(QLabel(self._get_example_text()), self._text)
        self._box.setLayout(self._layout)

    @property
    def widget(self):
        return self._box

    def splits(self, splits=None):
        if splits is None:
            text_row = self._text.toPlainText().split('\n')
            splits = []
            for row in text_row:
                if not row.strip():
                    continue
                item = row.split()
                if len(item) >= 2:
                    split = Split()
                    split.code = item[0]
                    split.time = hhmmss_to_time(item[1])
                    if self._more24 and len(item) >= 3 and item[2].isdigit():
                        split.days = int(item[2])
                    splits.append(split)
                else:
                    logging.error('In "{}" no code and no time'.format(row))
            self._splits = splits
        else:
            self._splits = splits
        return self._splits

    def show(self):
        splits = self._splits if self._splits else []
        text = ''
        time_accuracy = race().get_setting('time_accuracy', 0)
        for split in splits:
            if self._more24:
                text += '{} {} {}\n'.format(split.code, split.time.to_str(time_accuracy), split.days)
            else:
                text += '{} {}\n'.format(split.code, split.time.to_str(time_accuracy))

        self._text.setText(text)

    @staticmethod
    def _get_example_text():
        return '31 12:45:00\n32 12:46:32\n33 12:49:12\n...'
