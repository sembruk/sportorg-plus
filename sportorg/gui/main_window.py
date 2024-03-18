import os
import ast
import logging
import time
import pylocker
from queue import Queue
from PySide2 import QtGui, QtWidgets
from PySide2.QtCore import Qt, QModelIndex, QItemSelectionModel, QTimer, QRect
from PySide2.QtWidgets import QMainWindow, QTableView, QMessageBox

from sportorg import config
from sportorg.gui.global_access import GlobalAccess
from sportorg.common.singleton import singleton
from sportorg.gui.dialogs.course_edit import CourseEditDialog
from sportorg.gui.dialogs.person_edit import PersonEditDialog
from sportorg.gui.dialogs.group_edit import GroupEditDialog
from sportorg.gui.dialogs.team_edit import TeamEditDialog
from sportorg.models.constant import RentCards
from sportorg.models.memory import Race, race, NotEmptyException, new_event, set_current_race_index
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.split_calculation import GroupSplits
from sportorg.modules.backup.file import File
from sportorg.modules.live.live import LiveClient
from sportorg.modules.printing.model import NoResultToPrintException, split_printout, NoPrinterSelectedException
from sportorg.modules.configs.configs import Config as Configuration, ConfigFile
from sportorg.modules.sfr.sfrreader import SFRReaderClient
from sportorg.modules.sound import Sound
from sportorg.modules.sportident.result_generation import ResultSportidentGeneration
from sportorg.common.broker import Broker
from sportorg.gui.dialogs.file_dialog import get_save_file_name
from sportorg.gui.menu import menu_list, Factory
from sportorg.gui.tabs import persons, groups, teams, results, courses, log
from sportorg.gui.tabs.memory_model import PersonMemoryModel, ResultMemoryModel, GroupMemoryModel, \
    CourseMemoryModel, TeamMemoryModel
from sportorg.gui.toolbar import toolbar_list
from sportorg.gui.utils.custom_controls import messageBoxQuestion
from sportorg.language import _
from sportorg.modules.sportident.sireader import SIReaderClient
from sportorg.modules.sportiduino.sportiduino import SportiduinoClient
from sportorg.modules.teamwork import Teamwork
from sportorg.modules.telegram.telegram import TelegramClient


class ConsolePanelHandler(logging.Handler):
    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.setFormatter(logging.Formatter('%(asctime)-15s %(levelname)s %(message)s'))
        self.setLevel('INFO')
        self.parent = parent

    def emit(self, record):
        self.parent.logging(self.format(record))


class MainWindow(QMainWindow):
    def __init__(self, argv=None):
        super().__init__()
        self.menu_factory = Factory(self)
        self.recent_files = []
        self.action_by_id = {}
        self.menu_list_for_disabled = []
        self.toolbar_property = {}
        try:
            self.file = argv[1]
            self.add_recent_file(self.file)
        except IndexError:
            self.file = None

        self.log_queue = Queue()
        handler = ConsolePanelHandler(self)
        logging.root.addHandler(handler)
        self.last_update = time.time()
        self.relay_number_assign = False

        self.file_locker = pylocker.FACTORY(
            key='sportorgplus_locker_key', password='str(uuid.uuid1())', autoconnect=False
        )
        self.file_lock_id = None

    def _set_style(self):
        try:
            with open(config.style_dir('default.qss')) as s:
                self.setStyleSheet(s.read())
        except FileNotFoundError:
            pass

    def show_window(self):
        try:
            self.conf_read()
        except Exception as e:
            logging.error(e)
        self._set_style()
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_tab()
        self._setup_statusbar()
        self.show()
        self.post_show()

    sportident_status = False
    sportident_icon = {
        True: 'sportident-on.png',
        False: 'sportident.png',
    }

    def interval(self):
        if SIReaderClient().is_alive() != self.sportident_status:
            pass
        # FIXME
        """
            self.toolbar_property['sportident'].setIcon(
                QtGui.QIcon(config.icon_dir(self.sportident_icon[SIReaderClient().is_alive()])))
            self.sportident_status = SIReaderClient().is_alive()
        if Teamwork().is_alive() != self.teamwork_status:
            self.toolbar_property['teamwork'].setIcon(
                QtGui.QIcon(config.icon_dir(self.teamwork_icon[Teamwork().is_alive()])))
            self.teamwork_status = Teamwork().is_alive()
        """
        try:
            if self.get_configuration().get('autosave_interval'):
                if self.file:
                    if time.time() - self.last_update > int(self.get_configuration().get('autosave_interval')):
                        self.save_file()
                        logging.info(_('Auto save'))
                else:
                    logging.debug(translate('No file to auto save'))
        except Exception as e:
            logging.error(str(e))

        while not self.log_queue.empty():
            text = self.log_queue.get()
            self.statusbar_message(text)
            if hasattr(self, 'logging_tab'):
                self.logging_tab.write(text)

    def _close(self):
        self.conf_write()
        self.unlock_file()
        Broker().produce('close')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, _event):
        reply = messageBoxQuestion(self, _('Question'), 
                                   _('Save file before exit?'),
                                   QMessageBox.Save
                                   | QMessageBox.No
                                   | QMessageBox.Cancel)

        if reply == QMessageBox.Save:
            self.save_file()
            self._close()
            _event.accept()
        elif reply == QMessageBox.No:
            self._close()
            _event.accept()
        else:
            _event.ignore()

    def resizeEvent(self, e):
        Broker().produce('resize', self.get_size())

    def conf_read(self):
        Configuration().read()
        if Configuration().parser.has_section(ConfigFile.PATH):
            try:
                recent_files = ast.literal_eval(Configuration().parser.get(
                    ConfigFile.PATH, 'recent_files', fallback='[]'))
                if isinstance(recent_files, list):
                    self.recent_files = recent_files
            except Exception as e:
                logging.error(str(e))

    def conf_write(self):
        Configuration().set_option(ConfigFile.GEOMETRY, 'main', self.saveGeometry().toHex().data().decode())
        Configuration().set_option(ConfigFile.PATH, 'recent_files', self.recent_files)

        tabs = self.get_tables()
        for table in tabs:
            table_name = table.objectName()
            Configuration().set_option(ConfigFile.TAB_COLUMN_ORDER, table_name, table.get_column_order().toHex().data().decode())

        Configuration().save()

    def post_show(self):
        if self.file:
            self.open_file(self.file)
        elif Configuration().configuration.get('open_recent_file'):
            if len(self.recent_files):
                self.open_file(self.recent_files[0])

        Teamwork().set_call(self.teamwork)
        SIReaderClient().set_call(self.add_sportident_result_from_sireader)
        SportiduinoClient().set_call(self.add_sportiduino_result_from_reader)
        SFRReaderClient().set_call(self.add_sfr_result_from_reader)

        self.service_timer = QTimer(self)
        self.service_timer.timeout.connect(self.interval)
        self.service_timer.start(1000) # msec

        LiveClient().init()
        self._menu_disable(self.current_tab)

    def _setup_ui(self):
        geom = bytearray.fromhex(Configuration().parser.get(ConfigFile.GEOMETRY, 'main',  fallback='00'))
        if len(geom) == 1:
            self.resize(880, 470)
        self.restoreGeometry(geom)

        self.setWindowIcon(QtGui.QIcon(config.ICON))
        self.set_title()

        self.setLayoutDirection(Qt.LeftToRight)
        self.setDockNestingEnabled(False)
        self.setDockOptions(QtWidgets.QMainWindow.AllowTabbedDocks
                            | QtWidgets.QMainWindow.AnimatedDocks
                            | QtWidgets.QMainWindow.ForceTabbedDocks)

    def _create_menu(self, parent, actions_list):
        for action_item in actions_list:
            if 'show' in action_item and not action_item['show']:
                return
            if 'type' in action_item:
                if action_item['type'] == 'separator':
                    parent.addSeparator()
            elif 'action' in action_item:
                action = QtWidgets.QAction(self)
                action.setText(action_item['title'])
                action.triggered.connect(self.menu_factory.get_action(action_item['action']))
                if 'shortcut' in action_item:
                    shortcuts = [action_item['shortcut']] if isinstance(action_item['shortcut'], str)\
                        else action_item['shortcut']
                    action.setShortcuts(shortcuts)
                if 'status_tip' in action_item:
                    action.setStatusTip(action_item['status_tip'])
                if 'icon' in action_item:
                    action.setIcon(QtGui.QIcon(action_item['icon']))
                if 'tabs' in action_item:
                    self.menu_list_for_disabled.append((
                        action,
                        action_item['tabs']
                    ))
                if 'id' in action_item:
                    self.action_by_id[action_item['id']] = action
                parent.addAction(action)
            else:
                menu = QtWidgets.QMenu(parent)
                menu.setTitle(action_item['title'])
                if 'icon' in action_item:
                    menu.setIcon(QtGui.QIcon(action_item['icon']))
                if 'tabs' in action_item:
                    self.menu_list_for_disabled.append((
                        menu,
                        action_item['tabs']
                    ))
                if 'id' in action_item:
                    self.action_by_id[action_item['id']] = menu
                self._create_menu(menu, action_item['actions'])
                parent.addAction(menu.menuAction())

    def _setup_menu(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QRect(0, 0, 880, 21))
        self.menubar.setNativeMenuBar(False)
        self.setMenuBar(self.menubar)
        self._create_menu(self.menubar, menu_list())
        self._update_recent_files_menu()

    def _update_recent_files_menu(self):
        if 'open_recent' in self.action_by_id:
            menu = self.action_by_id['open_recent']
            menu.clear()
            if len(self.recent_files) == 0:
                action = menu.addAction(_('Empty'))
                action.setEnabled(False)
            else:
                for rf in self.recent_files[:10]:
                    action = menu.addAction(rf)
                    action.triggered.connect(lambda checked=False, x=rf: self.open_file(x))
                    menu.addAction(action)

    def _setup_toolbar(self):
        self.toolbar = self.addToolBar(_('Toolbar'))
        for tb in toolbar_list():
            tb_action = QtWidgets.QAction(QtGui.QIcon(tb[0]), tb[1], self)
            tb_action.triggered.connect(self.menu_factory.get_action(tb[2]))
            if len(tb) == 4:
                self.toolbar_property[tb[3]] = tb_action
            self.toolbar.addAction(tb_action)
        if not self.get_configuration().get('show_toolbar'):
            self.toolbar.hide()

    def _setup_statusbar(self):
        self.statusbar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusbar)

    def _setup_tab(self):
        self.centralwidget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.tabwidget = QtWidgets.QTabWidget(self.centralwidget)
        layout.addWidget(self.tabwidget)
        self.setCentralWidget(self.centralwidget)

        self.tabwidget.addTab(persons.Widget(), _('Competitors'))
        self.tabwidget.addTab(results.Widget(), _('Race Results'))
        self.tabwidget.addTab(groups.Widget(), _('Groups'))
        self.tabwidget.addTab(courses.Widget(), _('Courses'))
        self.tabwidget.addTab(teams.Widget(), _('Teams'))
        self.logging_tab = log.Widget()
        self.tabwidget.addTab(self.logging_tab, _('Logs'))
        self.tabwidget.currentChanged.connect(self._menu_disable)

        if Configuration().parser.has_section(ConfigFile.TAB_COLUMN_ORDER):
            try:
                tabs = self.get_tables()
                for table in tabs:
                    table_name = table.objectName()
                    column_order = bytearray.fromhex(Configuration().parser.get(ConfigFile.TAB_COLUMN_ORDER, table_name, fallback='00'))
                    if column_order:
                        table.set_column_order(column_order)
            except Exception as e:
                logging.error(str(e))

    def _menu_disable(self, tab_index):
        for item in self.menu_list_for_disabled:
            if tab_index not in item[1]:
                item[0].setDisabled(True)
            else:
                item[0].setDisabled(False)

    def get_size(self):

        return {
            'x': self.geometry().x(),
            'y': self.geometry().y(),
            'width': self.width(),
            'height': self.height(),
        }


    def set_title(self, title=None):
        main_title = '{} {}'.format(config.NAME, config.VERSION)
        if title:
            self.setWindowTitle('{} - {}'.format(title, main_title))
        elif self.file:
            self.set_title('{} [{}]'.format(race().data.get_start_datetime(), self.file))
        else:
            self.setWindowTitle(main_title)

    def statusbar_message(self, msg, msecs=5000):
        if hasattr(self, 'statusbar'):
            self.statusbar.showMessage('', 0)
            self.statusbar.showMessage(msg, msecs)

    def logging(self, text):
        self.log_queue.put(text)

    def select_tab(self, index):
        self.current_tab = index

    @property
    def current_tab(self):
        return self.tabwidget.currentIndex()

    @current_tab.setter
    def current_tab(self, index):
        if index < self.tabwidget.count():
            self.tabwidget.setCurrentIndex(index)
        else:
            logging.error("{} {}".format(index, _("Tab doesn't exist")))

    @staticmethod
    def get_configuration():
        return Configuration().configuration

    def init_model(self):
        try:
            self.clear_filters()  # clear filters not to loose filtered data

            table = self.get_person_table()

            if not table:
                return

            table.setModel(PersonMemoryModel())
            table = self.get_result_table()
            table.setModel(ResultMemoryModel())
            table = self.get_group_table()
            table.setModel(GroupMemoryModel())
            table = self.get_course_table()
            table.setModel(CourseMemoryModel())
            table = self.get_team_table()
            table.setModel(TeamMemoryModel())
            Broker().produce('init_model')
        except Exception as e:
            logging.error(str(e))

    def refresh(self):
        logging.debug('Refreshing interface')
        try:
            t = time.time()
            table = self.get_person_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = self.get_result_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = self.get_group_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = self.get_course_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()

            table = self.get_team_table()
            table.model().init_cache()
            table.model().layoutChanged.emit()
            self.set_title()

            print('Refresh in {:.3f} seconds.'.format(time.time() - t))
            Broker().produce('refresh')
        except Exception as e:
            logging.error(str(e))

    def clear_filters(self, remove_condition=True):
        if self.get_person_table():
            self.get_person_table().model().clear_filter(remove_condition)
            self.get_result_table().model().clear_filter(remove_condition)
            self.get_person_table().model().clear_filter(remove_condition)
            self.get_course_table().model().clear_filter(remove_condition)
            self.get_team_table().model().clear_filter(remove_condition)

    def apply_filters(self):
        if self.get_person_table():
            self.get_person_table().model().apply_filter()
            self.get_result_table().model().apply_filter()
            self.get_person_table().model().apply_filter()
            self.get_course_table().model().apply_filter()
            self.get_team_table().model().apply_filter()

    def add_recent_file(self, file):
        self.delete_from_recent_files(file)
        self.recent_files.insert(0, file)
        self._update_recent_files_menu()

    def delete_from_recent_files(self, file):
        if file in self.recent_files:
            self.recent_files.remove(file)
            self._update_recent_files_menu()

    def get_tables(self):
        return self.findChildren(QtWidgets.QTableView)

    def get_table_by_name(self, name):
        return self.findChild(QtWidgets.QTableView, name)

    def get_person_table(self):
        return self.get_table_by_name('PersonTable')

    def get_result_table(self):
        return self.get_table_by_name('ResultTable')

    def get_group_table(self):
        return self.get_table_by_name('GroupTable')

    def get_course_table(self):
        return self.get_table_by_name('CourseTable')

    def get_team_table(self):
        return self.get_table_by_name('TeamTable')

    def get_current_table(self):
        map_ = ['PersonTable', 'ResultTable', 'GroupTable', 'CourseTable', 'TeamTable']
        idx = self.current_tab
        if idx < len(map_):
            return self.get_table_by_name(map_[idx])

    def get_selected_rows(self, table=None):
        if table is None:
            table = self.get_current_table()
        sel_model = table.selectionModel()
        indexes = sel_model.selectedRows()

        ret = []
        for i in indexes:
            orig_index_int = i.row()
            ret.append(orig_index_int)
        return ret

    def add_sportident_result_from_sireader(self, result):
        try:
            assignment_mode = race().get_setting('system_assignment_mode', False)
            if not assignment_mode:
                self.clear_filters(remove_condition=False)
                rg = ResultSportidentGeneration(result)
                if rg.add_result():
                    result = rg.get_result()
                    ResultCalculation(race()).process_results()
                    if race().get_setting('split_printout', False):
                        try:
                            split_printout(result)
                        except NoResultToPrintException as e:
                            logging.error(str(e))
                        except NoPrinterSelectedException as e:
                            logging.error(str(e))
                        except Exception as e:
                            logging.error(str(e))
                    elif result.person and result.person.group:
                        GroupSplits(race(), result.person.group).generate(True)
                    Teamwork().send(result.to_dict())
                    TelegramClient().send_result(result)
                    if result.person:
                        if result.is_status_ok():
                            Sound().ok()
                        else:
                            Sound().fail()
                        if result.person.is_rented_card or RentCards().exists(result.person.card_number):
                            Sound().rented_card()
            else:
                mv = GlobalAccess().get_main_window()
                selection = mv.get_selected_rows(mv.get_table_by_name('PersonTable'))
                if selection:
                    for i in selection:
                        if i < len(race().persons):
                            cur_person = race().persons[i]
                            if cur_person.card_number:
                                confirm = messageBoxQuestion(self, _('Question'), _('Are you sure you want to reassign the chip number'), QMessageBox.Yes | QMessageBox.No)
                                if confirm == QMessageBox.No:
                                    break
                            race().person_card_number(cur_person, result.card_number)
                            break
                else:
                    for person in race().persons:
                        if not person.card_number:
                            old_person = race().person_card_number(person, result.card_number)
                            if old_person:
                                Teamwork().send(old_person.to_dict())
                            person.is_rented_card = True
                            Teamwork().send(person.to_dict())
                            break
            self.refresh()
        except Exception as e:
            logging.error(str(e))

    def add_sfr_result_from_reader(self, result):
        self.add_sportident_result_from_sireader(result)

    def add_sportiduino_result_from_reader(self, result):
        self.add_sportident_result_from_sireader(result)

    def teamwork(self, command):
        try:
            race().update_data(command.data)
            logging.info(repr(command.data))
            if 'object' in command.data and command.data['object'] in ['ResultManual', 'ResultSportident', 'ResultSFR', 'ResultSportiduino']:
                ResultCalculation(race()).process_results()
            Broker().produce('teamwork_recieving', command.data)
            self.refresh()
        except Exception as e:
            logging.error(str(e))

    # Actions
    def create_file(self, *args, update_data=True, is_new=True):
        file_name = get_save_file_name(
            _('Create SportOrg file'),
            _('SportOrg file (*.json)'),
            time.strftime("%Y%m%d")
        )
        if file_name:
            try:
                # protect from overwriting with empty file
                if is_new and os.path.exists(file_name):
                    if os.path.getsize(file_name) > 1000:
                        QMessageBox.warning(
                            self,
                            _('Error'),
                            _('Canceled overwriting existing file\n\"{}\"\nwith new empty file').format(file_name),
                        )
                        return

                if not self.lock_file(file_name):
                    return

                if update_data:
                    new_event([Race()])
                    set_current_race_index(0)
                self.clear_filters(remove_condition=False)
                File(file_name, logging.root, File.JSON).create()
                self.apply_filters()
                self.last_update = time.time()
                self.file = file_name
                self.add_recent_file(self.file)
                self.set_title()
                self.init_model()
            except Exception as e:
                logging.error(str(e))
                QMessageBox.warning(self, _('Error'), _('Cannot create file') + ': ' + file_name)
            self.refresh()

    def save_file_as(self):
        self.create_file(update_data=False, is_new=False)

    def save_file(self):
        if self.file:
            try:
                self.clear_filters(remove_condition=False)
                File(self.file, logging.root, File.JSON).save()
                self.apply_filters()
                self.last_update = time.time()
            except Exception as e:
                logging.error(str(e))
        else:
            self.save_file_as()

    def open_file(self, file_name=None):
        if file_name:
            try:
                if not self.lock_file(file_name):
                    return

                File(file_name, logging.root, File.JSON).open()
                self.file = file_name
                self.set_title()
                self.add_recent_file(self.file)
                self.init_model()
                self.last_update = time.time()
            except Exception as e:
                logging.exception(str(e))
                self.delete_from_recent_files(file_name)
                if isinstance(e, FileNotFoundError):
                    QMessageBox.warning(self, _('File not found'), str(e))
                else:
                    QMessageBox.warning(self, _('Error'), _('Cannot read file, format unknown') + ': ' + file_name)

    def split_printout_selected(self):
        if self.current_tab != 1:
            logging.warning(_('No result selected'))
            return
        try:
            indexes = self.get_selected_rows()
            if len(indexes) > 5:
                confirm = messageBoxQuestion(
                    self,
                    _('Question'),
                    _('Too many results selected for printing.\nAre you sure you want to continue?'),
                    QMessageBox.Yes | QMessageBox.No)
                if confirm == QMessageBox.No:
                    return

            obj = race()
            for index in indexes:
                if index < 0:
                    continue
                if index <= len(obj.results):
                    self.split_printout(obj.results[index])
        except Exception as e:
            logging.exception(str(e))

    def split_printout(self, result):
        try:
            split_printout(result)
        except NoResultToPrintException as e:
            logging.warning(str(e))
            mes = QMessageBox(self)
            mes.setText(_('No results to print'))
            mes.exec_()
        except NoPrinterSelectedException as e:
            logging.warning(str(e))
            mes = QMessageBox(self)
            mes.setText(_('No printer selected'))
            mes.exec_()

    def add_object(self):
        try:
            tab = self.current_tab
            if tab == 0:
                p = race().add_new_person()
                PersonEditDialog(p, True).exec_()
                self.refresh()
            elif tab == 1:
                self.menu_factory.execute('ManualFinishAction')
            elif tab == 2:
                g = race().add_new_group()
                GroupEditDialog(g, True).exec_()
                self.refresh()
            elif tab == 3:
                c = race().add_new_course()
                CourseEditDialog(c, True).exec_()
                self.refresh()
            elif tab == 4:
                o = race().add_new_team()
                TeamEditDialog(o, True).exec_()
                self.refresh()
        except Exception as e:
            logging.error(str(e))

    def delete_object(self):
        try:
            if self.current_tab not in range(5):
                return
            self._delete_object()
        except Exception as e:
            logging.error(str(e))

    def _delete_object(self):
        indexes = self.get_selected_rows()
        if not len(indexes):
            return

        confirm = messageBoxQuestion(self, _('Question'), _('Please confirm'), QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.No:
            return
        tab = self.current_tab
        res = []
        if tab == 0:
            res = race().delete_persons(indexes)
            ResultCalculation(race()).process_results()
            self.refresh()
        elif tab == 1:
            res = race().delete_results(indexes)
            ResultCalculation(race()).process_results()
            self.refresh()
        elif tab == 2:
            try:
                res = race().delete_groups(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(self.get_group_table(),
                                     _('Error'),
                                     _('Cannot remove group'))
            self.refresh()
        elif tab == 3:
            try:
                res = race().delete_courses(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(self.get_course_table(),
                                     _('Error'),
                                     _('Cannot remove course'))
            self.refresh()
        elif tab == 4:
            try:
                res = race().delete_teams(indexes)
            except NotEmptyException as e:
                logging.warning(str(e))
                QMessageBox.question(self.get_team_table(),
                                     _('Error'),
                                     _('Cannot remove team'))
            self.refresh()
        if len(res):
            Teamwork().delete([r.to_dict() for r in res])

    def lock_file(self, file_name: str):
        if self.file == file_name:
            # already locked by current process ('Save as' or 'Open' for the same file)
            return True

        # try to acquire the lock a single file path
        acquired, lock_id = self.file_locker.acquire_lock(file_name, timeout=0.5)
        if acquired:
            # new lock created, release previous lock if exists
            self.unlock_file()
            self.file_lock_id = lock_id
            logging.info(_('File lock created') + ': ' + file_name)
        else:
            # already locked = opened in another process, avoid parallel opening
            QMessageBox.warning(
                self,
                _('Error'),
                _('Cannot open file, it is already opened') + ':\n' + file_name,
            )
            return False
        return True

    def unlock_file(self):
        if self.file_lock_id is not None:
            self.file_locker.release(self.file_lock_id)
            logging.info(_('File lock released'))

