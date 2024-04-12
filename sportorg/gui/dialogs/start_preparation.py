import logging
from time import sleep

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import QTime
from PySide2.QtWidgets import QDialog, QSizePolicy

from sportorg import config
from sportorg.common.otime import OTime
from sportorg.gui.global_access import GlobalAccess
from sportorg.language import _
from sportorg.models.memory import race, Group, Limit
from sportorg.models.start.start_preparation import StartNumberManager, DrawManager, ReserveManager, \
    StartTimeManager
from sportorg.utils.time import time_to_otime


class StartPreparationDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())
        self.time_format = 'hh:mm:ss'

    def exec_(self):
        self.setup_ui()
        return super().exec_()

    def setup_ui(self):
        self.setWindowIcon(QtGui.QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)
        #self.setFixedSize(self.size())
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.setLayout(self.grid_layout)

        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.grid_layout.addWidget(self.button_box, 3, 0, 1, 2)

        self.reserve_group_box = QtWidgets.QGroupBox(self)
        self.reserve_group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout.addWidget(self.reserve_group_box, 0, 0)
        self.reserve_layout = QtWidgets.QFormLayout(self.reserve_group_box)
        self.reserve_layout.setContentsMargins(2, 2, 2, 2)
        self.reserve_prefix_label = QtWidgets.QLabel(self.reserve_group_box)
        self.reserve_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.reserve_prefix_label)
        self.reserve_prefix = QtWidgets.QLineEdit(self.reserve_group_box)
        self.reserve_prefix.setEnabled(False)
        self.reserve_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.reserve_prefix)
        self.reserve_group_count_label = QtWidgets.QLabel(self.reserve_group_box)
        self.reserve_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.reserve_group_count_label)
        self.reserve_group_count_spin_box = QtWidgets.QSpinBox(self.reserve_group_box)
        self.reserve_group_count_spin_box.setEnabled(False)
        self.reserve_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.reserve_group_count_spin_box)
        self.reserve_group_percent_label = QtWidgets.QLabel(self.reserve_group_box)
        self.reserve_layout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.reserve_group_percent_label)
        self.reserve_group_percent_spin_box = QtWidgets.QSpinBox(self.reserve_group_box)
        self.reserve_group_percent_spin_box.setEnabled(False)
        self.reserve_group_percent_spin_box.setMaximum(100)
        self.reserve_group_percent_spin_box.setSingleStep(5)
        self.reserve_layout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.reserve_group_percent_spin_box)
        self.reserve_check_box = QtWidgets.QCheckBox(self)
        self.reserve_layout.setWidget(0, QtWidgets.QFormLayout.SpanningRole, self.reserve_check_box)
        self.reserve_check_box.stateChanged.connect(self.reserve_activate)


        self.draw_group_box = QtWidgets.QGroupBox(self)
        self.draw_group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout.addWidget(self.draw_group_box, 0, 1)
        self.draw_layout = QtWidgets.QFormLayout(self.draw_group_box)
        self.draw_layout.setContentsMargins(2, 2, 2, 2)
        self.draw_check_box = QtWidgets.QCheckBox(self.draw_group_box)
        self.draw_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.draw_check_box)
        self.draw_groups_check_box = QtWidgets.QCheckBox(self.draw_group_box)
        self.draw_groups_check_box.setEnabled(False)
        self.draw_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.draw_groups_check_box)
        self.draw_teams_check_box = QtWidgets.QCheckBox(self.draw_group_box)
        self.draw_teams_check_box.setEnabled(False)
        self.draw_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.draw_teams_check_box)
        self.draw_regions_check_box = QtWidgets.QCheckBox(self.draw_group_box)
        self.draw_regions_check_box.setEnabled(False)
        self.draw_regions_check_box.setMinimumHeight(13)
        self.draw_layout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.draw_regions_check_box)
        self.draw_mix_groups_check_box = QtWidgets.QCheckBox(self.draw_group_box)
        self.draw_mix_groups_check_box.setEnabled(False)
        self.draw_mix_groups_check_box.setMinimumHeight(13)
        self.draw_layout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.draw_mix_groups_check_box)

        self.draw_check_box.stateChanged.connect(self.draw_activate)

        self.start_group_box = QtWidgets.QGroupBox(self)
        self.start_group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout.addWidget(self.start_group_box, 1, 0)
        self.start_layout = QtWidgets.QFormLayout(self.start_group_box)
        self.start_layout.setContentsMargins(2, 2, 2, 2)
        self.start_check_box = QtWidgets.QCheckBox(self.start_group_box)
        self.start_layout.setWidget(0, QtWidgets.QFormLayout.SpanningRole, self.start_check_box)
        self.start_first_label = QtWidgets.QLabel(self.start_group_box)
        self.start_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.start_first_label)
        self.start_first_time_edit = QtWidgets.QTimeEdit(self.start_group_box)
        self.start_first_time_edit.setEnabled(False)
        self.start_first_time_edit.setDisplayFormat(self.time_format)
        self.start_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.start_first_time_edit)
        self.start_interval_radio_button = QtWidgets.QRadioButton(self.start_group_box)
        self.start_interval_radio_button.setChecked(True)
        self.start_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.start_interval_radio_button)
        self.start_interval_time_edit = QtWidgets.QTimeEdit(self.start_group_box)
        self.start_interval_time_edit.setEnabled(False)
        self.start_interval_time_edit.setDisplayFormat(self.time_format)
        self.start_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.start_interval_time_edit)
        self.start_group_settings_radio_button = QtWidgets.QRadioButton(self.start_group_box)
        self.start_group_settings_radio_button.setEnabled(False)
        self.start_group_settings_radio_button.setChecked(False)
        self.start_layout.setWidget(3, QtWidgets.QFormLayout.SpanningRole, self.start_group_settings_radio_button)
        self.start_one_minute_qty_label = QtWidgets.QLabel(self.start_group_box)
        self.start_layout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.start_one_minute_qty_label)
        self.start_one_minute_qty = QtWidgets.QSpinBox(self.start_group_box)
        self.start_one_minute_qty.setValue(1)
        self.start_one_minute_qty.setMaximum(100)
        self.start_layout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.start_one_minute_qty)
        self.start_check_box.stateChanged.connect(self.start_activate)

        self.numbers_group_box = QtWidgets.QGroupBox(self)
        self.numbers_group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.grid_layout.addWidget(self.numbers_group_box, 1, 1)
        self.numbers_vert_layout = QtWidgets.QVBoxLayout(self.numbers_group_box)
        self.numbers_vert_layout.setContentsMargins(2, 2, 2, 2)
        self.numbers_check_box = QtWidgets.QCheckBox(self.numbers_group_box)
        self.numbers_vert_layout.addWidget(self.numbers_check_box)
        self.numbers_teams_check_box = QtWidgets.QCheckBox(self.numbers_group_box)
        self.numbers_teams_check_box.stateChanged.connect(self.numbers_teams_activate)
        self.numbers_vert_layout.addWidget(self.numbers_teams_check_box)
        self.numbers_skip_hor_layout = QtWidgets.QHBoxLayout()
        self.numbers_skip_line_edit = QtWidgets.QLineEdit(self.numbers_group_box)
        self.numbers_skip_line_edit.setPlaceholderText("123,456,789")
        self.numbers_skip_hor_layout.addWidget(QtWidgets.QLabel(_("Skip")))
        self.numbers_skip_hor_layout.addWidget(self.numbers_skip_line_edit)
        self.numbers_vert_layout.addLayout(self.numbers_skip_hor_layout)
        self.numbers_interval_hor_layout = QtWidgets.QHBoxLayout()
        self.numbers_interval_radio_button = QtWidgets.QRadioButton(self.numbers_group_box)
        self.numbers_interval_radio_button.setChecked(True)
        self.numbers_interval_radio_button.setMinimumWidth(70)
        self.numbers_interval_hor_layout.addWidget(self.numbers_interval_radio_button)
        self.numbers_first_spin_box = QtWidgets.QSpinBox(self.numbers_group_box)
        self.numbers_first_spin_box.setEnabled(False)
        self.numbers_first_spin_box.setMinimumWidth(47)
        self.numbers_first_spin_box.setMaximum(Limit.BIB)
        self.numbers_first_spin_box.setMinimumHeight(20)
        self.numbers_interval_hor_layout.addWidget(self.numbers_first_spin_box)
        self.numbers_interval_label = QtWidgets.QLabel(self.numbers_group_box)
        self.numbers_interval_hor_layout.addWidget(self.numbers_interval_label)
        self.numbers_interval_spin_box = QtWidgets.QSpinBox(self.numbers_group_box)
        self.numbers_interval_spin_box.setMinimumHeight(20)
        self.numbers_interval_spin_box.setEnabled(False)
        self.numbers_interval_hor_layout.addWidget(self.numbers_interval_spin_box)
        self.numbers_vert_layout.addLayout(self.numbers_interval_hor_layout)
        self.numbers_minute_radio_button = QtWidgets.QRadioButton(self.numbers_group_box)
        self.numbers_minute_radio_button.setEnabled(False)
        self.numbers_minute_radio_button.setChecked(False)
        self.numbers_vert_layout.addWidget(self.numbers_minute_radio_button)
        self.numbers_order_radio_button = QtWidgets.QRadioButton(self.numbers_group_box)
        self.numbers_order_radio_button.setEnabled(False)
        self.numbers_order_radio_button.setChecked(False)
        self.numbers_vert_layout.addWidget(self.numbers_order_radio_button)
        self.numbers_check_box.stateChanged.connect(self.number_activate)
        self.numbers_skip_line_edit.raise_()
        self.numbers_minute_radio_button.raise_()
        self.numbers_order_radio_button.raise_()
        self.numbers_interval_radio_button.raise_()
        self.numbers_first_spin_box.raise_()
        self.numbers_interval_label.raise_()
        self.numbers_interval_spin_box.raise_()

        self.progress_bar = QtWidgets.QProgressBar(self)
        #self.progress_bar.setGeometry(QtCore.QRect(10, 280, 621, 23))
        self.grid_layout.addWidget(self.progress_bar, 2, 0, 1, 2)
        self.progress_bar.setProperty("value", 0)

        self.button_box.raise_()
        self.reserve_group_box.raise_()
        self.progress_bar.raise_()
        self.draw_group_box.raise_()
        self.start_group_box.raise_()
        self.numbers_group_box.raise_()

        self.retranslate_ui()
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.recover_state()

    def retranslate_ui(self):
        self.setWindowTitle(_("Start Preparation"))
        self.reserve_group_box.setTitle(_("Reserves insert"))
        self.reserve_prefix_label.setText(_("Reserve prefix"))
        self.reserve_prefix.setText(_("Reserve"))
        self.reserve_group_count_label.setText(_("Reserves per group, ps"))
        self.reserve_group_percent_label.setText(_("Reserves per group, %"))
        self.reserve_check_box.setText(_("Insert reserves"))
        self.draw_group_box.setTitle(_("Draw"))
        self.draw_check_box.setText(_("Draw"))
        self.draw_groups_check_box.setText(_("Split by start groups"))
        self.draw_teams_check_box.setText(_("Split by teams"))
        self.draw_regions_check_box.setText(_("Split by regions"))
        self.draw_mix_groups_check_box.setText(_("Mix groups"))
        self.start_group_box.setTitle(_("Start time"))
        self.start_check_box.setText(_("Change start time"))
        self.start_first_label.setText(_("First start in corridor"))
        self.start_interval_radio_button.setText(_("Fixed start interval"))
        self.start_group_settings_radio_button.setText(_("Take start interval from group settings"))
        self.start_one_minute_qty_label.setText(_("Several athletes on one minute"))
        self.numbers_group_box.setTitle(_("Start numbers"))
        self.numbers_check_box.setText(_("Change start numbers"))
        self.numbers_interval_radio_button.setText(_("First number"))
        self.numbers_interval_label.setText(_("interval"))
        self.numbers_minute_radio_button.setText(_("Number = corridor + minute"))
        self.numbers_order_radio_button.setText(_("Number = corridor + order"))
        self.numbers_teams_check_box.setText(_("For teams but not for persons"))

    def reserve_activate(self):
        status = self.reserve_check_box.isChecked()
        for child in self.reserve_group_box.findChildren(QtWidgets.QWidget):
            if child != self.reserve_check_box:
                child.setEnabled(status)

    def number_activate(self):
        status = self.numbers_check_box.isChecked()
        for child in self.numbers_group_box.findChildren(QtWidgets.QWidget):
            if child != self.numbers_check_box:
                child.setEnabled(status)

    def numbers_teams_activate(self):
        status = self.numbers_teams_check_box.isChecked()
        self.numbers_skip_line_edit.setEnabled(not status)

    def start_activate(self):
        status = self.start_check_box.isChecked()
        for child in self.start_group_box.findChildren(QtWidgets.QWidget):
            if child != self.start_check_box:
                child.setEnabled(status)

    def draw_activate(self):
        status = self.draw_check_box.isChecked()
        for child in self.draw_group_box.findChildren(QtWidgets.QWidget):
            if child != self.draw_check_box:
                child.setEnabled(status)

    def get_skip_numbers(self):
        return [int(x.strip()) for x in self.numbers_skip_line_edit.text().split(',') if x.strip().isdigit()]

    def accept(self, *args, **kwargs):
        try:
            progressbar_delay = 0.01
            obj = race()
            obj.update_counters()
            if self.reserve_check_box.isChecked():
                reserve_prefix = self.reserve_prefix.text()
                reserve_count = self.reserve_group_count_spin_box.value()
                reserve_percent = self.reserve_group_percent_spin_box.value()

                ReserveManager(obj).process(reserve_prefix, reserve_count, reserve_percent)

            self.progress_bar.setValue(25)
            sleep(progressbar_delay)

            mix_groups = False
            if self.draw_check_box.isChecked():
                split_start_groups = self.draw_groups_check_box.isChecked()
                split_teams = self.draw_teams_check_box.isChecked()
                split_regions = self.draw_regions_check_box.isChecked()
                mix_groups = self.draw_mix_groups_check_box.isChecked()
                DrawManager(obj).process(split_start_groups, split_teams, split_regions, mix_groups)

            self.progress_bar.setValue(50)
            sleep(progressbar_delay)

            if self.start_check_box.isChecked():

                corridor_first_start = time_to_otime(self.start_first_time_edit.time())
                fixed_start_interval = time_to_otime(self.start_interval_time_edit.time())
                one_minute_qty = self.start_one_minute_qty.value()
                if self.start_interval_radio_button.isChecked():
                    StartTimeManager(obj).process(corridor_first_start, False, fixed_start_interval, one_minute_qty,
                                                  mix_groups=mix_groups)

                if self.start_group_settings_radio_button.isChecked():
                    StartTimeManager(obj).process(corridor_first_start, True, fixed_start_interval, one_minute_qty)

            self.progress_bar.setValue(75)
            sleep(progressbar_delay)

            if self.numbers_check_box.isChecked():
                if self.numbers_minute_radio_button.isChecked():
                    StartNumberManager(obj).process('corridor_minute')
                elif self.numbers_order_radio_button.isChecked():
                    StartNumberManager(obj).process('corridor_order')
                elif self.numbers_interval_radio_button.isChecked():
                    first_number = self.numbers_first_spin_box.value()
                    interval = self.numbers_interval_spin_box.value()
                    numbers_skip = self.get_skip_numbers()
                    for_teams = self.numbers_teams_check_box.isChecked()
                    StartNumberManager(obj).process('interval', first_number, interval, mix_groups=mix_groups, skip_list=numbers_skip, for_teams=for_teams)

            self.progress_bar.setValue(100)

            self.save_state()
        except Exception as e:
            logging.error(str(e))
        super().accept(*args, **kwargs)

    def save_state(self):
        obj = race()
        obj.set_setting('is_start_preparation_reserve', self.reserve_check_box.isChecked())
        obj.set_setting('reserve_prefix', self.reserve_prefix.text())
        obj.set_setting('reserve_count', self.reserve_group_count_spin_box.value())
        obj.set_setting('reserve_percent', self.reserve_group_percent_spin_box.value())

        obj.set_setting('is_start_preparation_draw', self.draw_check_box.isChecked())
        obj.set_setting('is_split_start_groups', self.draw_groups_check_box.isChecked())
        obj.set_setting('is_split_teams', self.draw_teams_check_box.isChecked())
        obj.set_setting('is_split_regions', self.draw_regions_check_box.isChecked())
        obj.set_setting('is_mix_groups', self.draw_mix_groups_check_box.isChecked())

        obj.set_setting('is_start_preparation_time', self.start_check_box.isChecked())
        obj.set_setting('is_fixed_start_interval', self.start_interval_radio_button.isChecked())
        obj.set_setting('start_interval', time_to_otime(self.start_interval_time_edit.time()).to_msec())
        obj.set_setting('start_first_time', time_to_otime(self.start_first_time_edit.time()).to_msec())
        obj.set_setting('start_one_minute_qty', self.start_one_minute_qty.value())

        obj.set_setting('is_start_preparation_numbers', self.numbers_check_box.isChecked())
        obj.set_setting('is_fixed_number_interval', self.numbers_interval_radio_button.isChecked())
        obj.set_setting('is_corridor_minute_number', self.numbers_minute_radio_button.isChecked())
        obj.set_setting('is_corridor_order_number', self.numbers_order_radio_button.isChecked())
        obj.set_setting('numbers_interval', self.numbers_interval_spin_box.value())
        obj.set_setting('numbers_first', self.numbers_first_spin_box.value())
        numbers_skip = self.get_skip_numbers()
        obj.set_setting('numbers_skip', numbers_skip)

    def recover_state(self):
        obj = race()

        self.reserve_check_box.setChecked(obj.get_setting('is_start_preparation_reserve', False))
        self.reserve_prefix.setText(obj.get_setting('reserve_prefix', _('Reserve')))
        self.reserve_group_count_spin_box.setValue(obj.get_setting('reserve_count', 1))
        self.reserve_group_percent_spin_box.setValue(obj.get_setting('reserve_percent', 0))

        self.draw_check_box.setChecked(obj.get_setting('is_start_preparation_draw', False))
        self.draw_groups_check_box.setChecked(obj.get_setting('is_split_start_groups', False))
        self.draw_teams_check_box.setChecked(obj.get_setting('is_split_teams', False))
        self.draw_regions_check_box.setChecked(obj.get_setting('is_split_regions', False))
        self.draw_mix_groups_check_box.setChecked(obj.get_setting('is_mix_groups', False))

        self.start_check_box.setChecked(obj.get_setting('is_start_preparation_time', False))

        if obj.get_setting('is_fixed_start_interval', True):
            self.start_interval_radio_button.setChecked(True)
        else:
            self.start_group_settings_radio_button.setChecked(True)
        t = OTime(msec=obj.get_setting('start_interval', 60000))
        self.start_interval_time_edit.setTime(QTime(t.hour, t.minute, t.sec))
        t = OTime(msec=obj.get_setting('start_first_time', 60000))
        self.start_first_time_edit.setTime(QTime(t.hour, t.minute, t.sec))
        self.start_one_minute_qty.setValue(obj.get_setting('start_one_minute_qty', 1))

        self.numbers_check_box.setChecked(obj.get_setting('is_start_preparation_numbers', False))
        if obj.get_setting('is_fixed_number_interval', True):
            self.numbers_interval_radio_button.setChecked(True)
        elif obj.get_setting('is_corridor_minute_number', False):
            self.numbers_minute_radio_button.setChecked(True)
        elif obj.get_setting('is_corridor_order_number', False):
            self.numbers_order_radio_button.setChecked(True)
        self.numbers_interval_spin_box.setValue(obj.get_setting('numbers_interval', 1))
        self.numbers_first_spin_box.setValue(obj.get_setting('numbers_first', 1))
        numbers_skip = obj.get_setting('numbers_skip')
        if numbers_skip is not None:
            self.numbers_skip_line_edit.setText(','.join(map(str, numbers_skip)))

        self.draw_activate()
        self.number_activate()
        self.start_activate()
        self.reserve_activate()

def guess_courses_for_groups():
    obj = race()
    for cur_group in obj.groups:
        if not cur_group.course or True:  # TODO check empty courses after export!
            for cur_course in obj.courses:
                course_name = cur_course.name
                group_name = cur_group.name
                if str(course_name).find(group_name) > -1:
                    cur_group.course = cur_course
                    logging.debug('Connecting: group ' + group_name + ' with course ' + course_name)
                    break
