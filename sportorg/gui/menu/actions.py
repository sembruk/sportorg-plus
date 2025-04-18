import logging
import time
import uuid
from typing import Any

from PySide2 import QtCore, QtGui

from PySide2.QtWidgets import QMessageBox, QApplication, QTableView, QInputDialog

from sportorg import config
from sportorg.common.otime import OTime
from sportorg.gui.dialogs.about import AboutDialog
from sportorg.gui.dialogs.help import HelpDialog
from sportorg.gui.dialogs.cp_delete import CPDeleteDialog
from sportorg.gui.dialogs.filter_dialog import FilterDialog
from sportorg.gui.dialogs.entry_mass_edit import MassEditDialog
from sportorg.gui.dialogs.event_properties import EventPropertiesDialog
from sportorg.gui.dialogs.file_dialog import get_open_file_name, get_save_file_name
from sportorg.gui.dialogs.live_dialog import LiveDialog
from sportorg.gui.dialogs.not_start_dialog import NotStartDialog
from sportorg.gui.dialogs.number_change import NumberChangeDialog
from sportorg.gui.dialogs.print_properties import PrintPropertiesDialog
from sportorg.gui.dialogs.relay_clone_dialog import RelayCloneDialog
from sportorg.gui.dialogs.relay_number_dialog import RelayNumberDialog
from sportorg.gui.dialogs.rent_cards_dialog import RentCardsDialog
from sportorg.gui.dialogs.report_dialog import ReportDialog
from sportorg.gui.dialogs.search_dialog import SearchDialog
from sportorg.gui.dialogs.settings import SettingsDialog
from sportorg.gui.dialogs.sportorg_import_dialog import SportOrgImportDialog
from sportorg.gui.dialogs.start_handicap_dialog import StartHandicapDialog
from sportorg.gui.dialogs.start_preparation import StartPreparationDialog, guess_courses_for_groups
from sportorg.gui.dialogs.start_time_change_dialog import StartTimeChangeDialog
from sportorg.gui.dialogs.teamwork_properties import TeamworkPropertiesDialog
from sportorg.gui.dialogs.telegram_dialog import TelegramDialog
from sportorg.gui.dialogs.text_io import TextExchangeDialog
from sportorg.gui.dialogs.timekeeping_properties import TimekeepingPropertiesDialog
from sportorg.gui.menu.action import Action
from sportorg.gui.utils.custom_controls import messageBoxQuestion
from sportorg.libs.winorient.wdb import write_wdb
from sportorg.models.memory import race, ResultStatus, ResultManual, find
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.result_checker import ResultChecker
from sportorg.models.start.start_preparation import guess_corridors_for_groups, copy_bib_to_card_number, copy_card_number_to_bib, split_teams, update_subgroups, merge_groups
from sportorg.modules.backup.json import get_races_from_file
from sportorg.modules.iof import iof_xml
from sportorg.modules.live.live import live_client
from sportorg.modules.ocad import ocad
from sportorg.modules.ocad.ocad import OcadImportException
from sportorg.modules.coordinates import coordinates
from sportorg.modules.sfr.sfrreader import SFRReaderClient
from sportorg.modules.sportident.sireader import SIReaderClient
from sportorg.modules.sportiduino.sportiduino import SportiduinoClient
from sportorg.modules.teamwork import Teamwork
from sportorg.modules.telegram.telegram import TelegramClient
from sportorg.modules.updater import checker
from sportorg.modules.winorient import winorient
from sportorg.modules.winorient.wdb import WDBImportError, WinOrientBinary
from sportorg.modules.orgeo import orgeo
from sportorg.language import _


class ActionFactory(type):
    actions = {}

    def __new__(mcs, name, *args, **kwargs) -> Any:
        cls = super().__new__(mcs, name, *args, **kwargs)
        ActionFactory.actions[name] = cls
        return cls


class NewAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.create_file()


class SaveAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.save_file()


class OpenAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(_('Open SportOrg file'), _("SportOrg file (*.json)"))
        self.app.open_file(file_name)


class SaveAsAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.save_file_as()


class CopyAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab not in range(6):
            return
        table = self.app.get_current_table()
        sel_model = table.selectionModel()
        data = '\t'.join(sel_model.model().get_headers()) + '\n'
        indexes = sel_model.selectedRows()
        for index in indexes:
            row = [str(row) for row in sel_model.model().get_data(index.row())]
            data += '\t'.join(row) + '\n'
        QtGui.qApp.clipboard().setText(data)


class DuplicateAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab not in range(6):
            return
        table = self.app.get_current_table()
        sel_model = table.selectionModel()
        indexes = sel_model.selectedRows()
        if len(indexes):
            sel_model.model().duplicate(indexes[0].row())
            self.app.refresh()


class SettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        SettingsDialog().exec_()


class EventSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        EventPropertiesDialog().exec_()


class CSVWinorientImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(_('Open CSV Winorient file'), _("CSV Winorient (*.csv)"))
        if file_name:
            try:
                winorient.import_csv(file_name)
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(self.app, _('Error'), _('Import error') + ': ' + file_name)
            self.app.init_model()


class CSVOrgeoImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(_('Open Orgeo CSV file'), _("Orgeo CSV (*.csv)"))
        if file_name:
            try:
                ret = orgeo.import_csv(file_name)
                if ret:
                    QMessageBox.information(self.app, _('Warning'), ret)
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(self.app, _('Error'), _('Import error') + ': ' + file_name)
            self.app.init_model()


class WDBWinorientImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(_('Open WDB Winorient file'), _("WDB Winorient (*.wdb)"))
        if file_name:
            try:
                winorient.import_wo_wdb(file_name)
            except WDBImportError as e:
                logging.exception(e)
                QMessageBox.warning(self.app, _('Error'), _('Import error') + ': ' + file_name)
            self.app.init_model()


class OcadTXTv8ImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(_('Open Ocad txt v8 file'), _("Ocad classes v8 (*.txt)"))
        if file_name:
            try:
                ocad.import_txt_v8(file_name)
            except OcadImportException as e:
                logging.exception(e)
                QMessageBox.warning(self.app, _('Error'), _('Import error') + ': ' + file_name)
            self.app.init_model()

class CpCoordinatesImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(_('Open CP coordinates file'), _("CP coordinates (*.gpx *.csv *.xml)"))
        if file_name:
            try:
                if file_name.endswith('.gpx'):
                    coordinates.import_coordinates_from_gpx(file_name)
                elif file_name.endswith('.csv'):
                    coordinates.import_coordinates_from_csv(file_name)
                elif file_name.endswith('.xml'):
                    coordinates.import_coordinates_from_iof_xml(file_name)
                else:
                    raise Exception('Unknown file type')
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(self.app, _('Error'), _('Import error') + ': ' + file_name)
            self.app.refresh()


class WDBWinorientExportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_save_file_name(_('Save As WDB file'), _("WDB file (*.wdb)"),
                                       '{}_sportorg_export'.format(race().data.get_start_datetime().strftime("%Y%m%d")))
        if file_name:
            try:
                wb = WinOrientBinary()

                self.app.clear_filters(False)
                wdb_object = wb.export()
                self.app.apply_filters()

                write_wdb(wdb_object, file_name)
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(self.app, _('Error'), _('Export error') + ': ' + file_name)


class IOFResultListExportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_save_file_name(_('Save As IOF xml'), _('IOF xml (*.xml)'),
                                       '{}_resultList'.format(race().data.get_start_datetime().strftime("%Y%m%d")))
        if file_name:
            try:
                iof_xml.export_result_list(file_name)
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(self.app, _('Error'), _('Export error') + ': ' + file_name)


class IOFEntryListImportAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(_('Open IOF xml'), _('IOF xml (*.xml)'))
        if file_name:
            try:
                ret = iof_xml.import_from_iof(file_name)
                if ret:
                    QMessageBox.information(self.app, _('Warning'), ret)
            except Exception as e:
                logging.exception(e)
                QMessageBox.warning(self.app, _('Error'), _('Import error') + ': ' + file_name)
            self.app.init_model()


class AddObjectAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.add_object()


class DeleteAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.delete_object()


class TextExchangeAction(Action, metaclass=ActionFactory):
    def execute(self):
        TextExchangeDialog().exec_()
        self.app.refresh()


class MassEditAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab == 0:
            MassEditDialog().exec_()
            self.app.refresh()


class RefreshAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.refresh()


class FilterAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab not in range(2):
            return
        table = self.app.get_current_table()
        FilterDialog(table).exec_()
        self.app.refresh()


class SearchAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab not in range(6):
            return
        table = self.app.get_current_table()
        SearchDialog(table).exec_()
        self.app.refresh()


class ToStartPreparationAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(0)


class ToRaceResultsAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(1)


class ToGroupsAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(2)


class ToCoursesAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(3)


class ToTeamsAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(4)


class ToControlPointsAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(5)


class ToLogAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.select_tab(6)


class StartPreparationAction(Action, metaclass=ActionFactory):
    def execute(self):
        StartPreparationDialog().exec_()
        self.app.refresh()


class GuessCoursesAction(Action, metaclass=ActionFactory):
    def execute(self):
        guess_courses_for_groups()
        self.app.refresh()


class GuessCorridorsAction(Action, metaclass=ActionFactory):
    def execute(self):
        guess_corridors_for_groups()
        self.app.refresh()


class RelayNumberAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.relay_number_assign:
            self.app.relay_number_assign = False
            QApplication.restoreOverrideCursor()
        else:
            self.app.relay_number_assign = True
            QApplication.setOverrideCursor(QtCore.Qt.PointingHandCursor)
            RelayNumberDialog().exec_()
        self.app.refresh()


class NumberChangeAction(Action, metaclass=ActionFactory):
    def execute(self):
        NumberChangeDialog().exec_()
        self.app.refresh()


class StartTimeChangeAction(Action, metaclass=ActionFactory):
    def execute(self):
        StartTimeChangeDialog().exec_()
        self.app.refresh()


class StartHandicapAction(Action, metaclass=ActionFactory):
    def execute(self):
        StartHandicapDialog().exec_()
        self.app.refresh()


class RelayCloneAction(Action, metaclass=ActionFactory):
    def execute(self):
        RelayCloneDialog().exec_()
        self.app.refresh()


class CopyBibToCardNumber(Action, metaclass=ActionFactory):
    def execute(self):
        msg = _('Use bib as card number') + '?'
        reply = messageBoxQuestion(self.app, _('Question'), msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            copy_bib_to_card_number()
            self.app.refresh()


class CopyCardNumberToBib(Action, metaclass=ActionFactory):
    def execute(self):
        msg = _('Use card number as bib') + '?'
        reply = messageBoxQuestion(self.app, _('Question'), msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            copy_card_number_to_bib()
            self.app.refresh()


class SplitTeamsAction(Action, metaclass=ActionFactory):
    def execute(self):
        split_teams()
        self.app.refresh()

class MergeGroupsAction(Action, metaclass=ActionFactory):
    def execute(self):
        try:
            if self.app.current_tab != 2:
                logging.warning(_('Can only merge groups in groups tab'))
                return
            indexes = self.app.get_selected_rows()
            if len(indexes) < 2:
                logging.warning(_('Please select at least 2 groups'))
                return
            selected_groups = {race().groups[i].name: i for i in indexes}
            group_name, ok = QInputDialog.getItem(self.app, _('Merge groups'), _('Keep group'), selected_groups.keys(), 0, False)
            if not ok:
                return
            if merge_groups(indexes, selected_groups[group_name]):
                self.app.clear_selection()
            self.app.refresh()
        except Exception as e:
            logging.exception(e)

class UpdateSubroups(Action, metaclass=ActionFactory):
    def execute(self):
        update_subgroups()
        self.app.refresh()


class ManualFinishAction(Action, metaclass=ActionFactory):
    def execute(self):
        result = race().new_result(ResultManual)
        Teamwork().send(result.to_dict())
        live_client.send(result)
        race().add_new_result(result)
        logging.info(_('Manual finish'))
        self.app.refresh()


class SPORTidentReadoutAction(Action, metaclass=ActionFactory):
    def execute(self):
        SIReaderClient().toggle()


class SportiduinoReadoutAction(Action, metaclass=ActionFactory):
    def execute(self):
        SportiduinoClient().toggle()


class SFRReadoutAction(Action, metaclass=ActionFactory):
    def execute(self):
        SFRReaderClient().toggle()


class CreateReportAction(Action, metaclass=ActionFactory):
    def execute(self):
        ReportDialog().exec_()


class SplitPrintoutAction(Action, metaclass=ActionFactory):
    def execute(self):
        self.app.split_printout_selected()


class RecheckingAction(Action, metaclass=ActionFactory):
    def execute(self):
        ResultChecker.check_all()
        ResultCalculation(race()).process_results()
        self.app.refresh()


class GroupFinderAction(Action, metaclass=ActionFactory):
    def execute(self):
        obj = race()
        indices = self.app.get_selected_rows()
        results = obj.results
        for index in indices:
            if index < 0:
                continue
            if index >= len(results):
                break
            result = results[index]
            if result.person and result.status in [ResultStatus.MISSING_PUNCH]:
                for group in obj.groups:
                    if result.check(group.course):
                        result.person.group = group
                        result.status = ResultStatus.OK
                        break
        self.app.refresh()


class PenaltyCalculationAction(Action, metaclass=ActionFactory):
    def execute(self):
        logging.debug('Penalty calculation start')
        for result in race().results:
            if result.person:
                ResultChecker.calculate_penalty(result)
        logging.debug('Penalty calculation finish')
        ResultCalculation(race()).process_results()
        self.app.refresh()


class PenaltyRemovingAction(Action, metaclass=ActionFactory):
    def execute(self):
        logging.debug('Penalty removing start')
        for result in race().results:
            result.penalty_time = OTime(msec=0)
            result.penalty_laps = 0
        logging.debug('Penalty removing finish')
        ResultCalculation(race()).process_results()
        self.app.refresh()


class ChangeStatusAction(Action, metaclass=ActionFactory):
    def execute(self):
        if self.app.current_tab != 1:
            logging.warning(_('No result selected'))
            return
        obj = race()

        status_dict = {
            ResultStatus.NONE: ResultStatus.OK,
            ResultStatus.OK: ResultStatus.DISQUALIFIED,
            ResultStatus.DISQUALIFIED: ResultStatus.DID_NOT_START,
            ResultStatus.DID_NOT_START: ResultStatus.DID_NOT_FINISH,
            ResultStatus.DID_NOT_FINISH: ResultStatus.RESTORED,
            ResultStatus.RESTORED: ResultStatus.OK,
        }

        table = self.app.get_result_table()
        index = table.currentIndex().row()
        if index < 0:
            index = 0
        if index >= len(obj.results):
            mes = QMessageBox()
            mes.setText(_('No results to change status'))
            mes.exec_()
            return
        result = obj.results[index]
        if result.status in status_dict:
            result.status = status_dict[result.status]
        else:
            result.status = ResultStatus.OK
        Teamwork().send(result.to_dict())
        live_client.send(result)
        self.app.refresh()


class SetDNSNumbersAction(Action, metaclass=ActionFactory):
    def execute(self):
        NotStartDialog().exec_()
        self.app.refresh()


class CPDeleteAction(Action, metaclass=ActionFactory):
    def execute(self):
        CPDeleteDialog().exec_()
        self.app.refresh()


class AddSPORTidentResultAction(Action, metaclass=ActionFactory):
    def execute(self):
        result = race().new_result()
        race().add_new_result(result)
        Teamwork().send(result.to_dict())
        logging.info('SPORTident result')
        self.app.get_result_table().model().init_cache()
        self.app.refresh()


class TimekeepingSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        TimekeepingPropertiesDialog().exec_()
        self.app.refresh()


class TeamworkSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        TeamworkPropertiesDialog().exec_()


class TeamworkEnableAction(Action, metaclass=ActionFactory):
    def execute(self):
        host = race().get_setting('teamwork_host', 'localhost')
        port = race().get_setting('teamwork_port', 50010)
        token = race().get_setting('teamwork_token', str(uuid.uuid4())[:8])
        connection_type = race().get_setting('teamwork_type_connection', 'client')
        Teamwork().set_options(host, port, token, connection_type)
        Teamwork().toggle()


class TeamworkSendAction(Action, metaclass=ActionFactory):
    def execute(self):
        try:
            obj = race()
            data_list = [obj.persons, obj.results, obj.groups, obj.courses, obj.teams]
            if self.app.current_tab >= len(data_list):
                return
            items = data_list[self.app.current_tab]
            indexes = self.app.get_selected_rows()
            items_dict = []
            for index in indexes:
                if index < 0:
                    continue
                if index >= len(items):
                    break
                items_dict.append(items[index].to_dict())
            Teamwork().send(items_dict)
        except Exception as e:
            logging.exception(e)


class PrinterSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        PrintPropertiesDialog().exec_()


class LiveSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        LiveDialog().exec_()
        self.app.refresh()


class TelegramSettingsAction(Action, metaclass=ActionFactory):
    def execute(self):
        TelegramDialog().exec_()


class TelegramSendAction(Action, metaclass=ActionFactory):
    def execute(self):
        try:
            if not self.app.current_tab == 1:
                logging.warning(_('No result selected'))
                return
            items = race().results
            indexes = self.app.get_selected_rows()
            for index in indexes:
                if index < 0:
                    continue
                if index >= len(items):
                    pass
                TelegramClient().send_result(items[index])
        except Exception as e:
            logging.exception(e)


class OnlineSendAction(Action, metaclass=ActionFactory):
    def execute(self):
        try:
            items = []
            if self.app.current_tab == 0:
                items = race().persons
            if self.app.current_tab == 1:
                items = race().results
            if self.app.current_tab == 2:
                items = race().groups
            if self.app.current_tab == 3:
                items = race().courses
            if self.app.current_tab == 4:
                items = race().teams
            indexes = self.app.get_selected_rows()
            if not indexes:
                return
            selected_items = []
            for index in indexes:
                if index < 0 or index >= len(items):
                    continue
                selected_items.append(items[index])
            if self.app.current_tab == 1:
                # Most recent results are sent last
                selected_items = selected_items[::-1]
            live_client.send(selected_items)
        except Exception as e:
            logging.exception(e)


class AboutAction(Action, metaclass=ActionFactory):
    def execute(self):
        AboutDialog().exec_()


class HelpAction(Action, metaclass=ActionFactory):
    def execute(self):
        HelpDialog().exec_()


class CheckUpdatesAction(Action, metaclass=ActionFactory):
    def execute(self):
        try:
            message = checker.update_available(config.VERSION)

            if message is None:
                message = _('You are using the latest version')

            QMessageBox.information(self.app, _('Info'), message)
        except Exception as e:
            logging.exception(e)
            QMessageBox.warning(self.app, _('Error'), str(e))


class AssignResultByBibAction(Action, metaclass=ActionFactory):
    def execute(self):
        for result in race().results:
            if result.person is None and result.bib:
                result.person = find(race().persons, bib=result.bib)
        self.app.refresh()


class AssignResultByCardNumberAction(Action, metaclass=ActionFactory):
    def execute(self):
        for result in race().results:
            if result.person is None and result.card_number:
                result.person = find(race().persons, card_number=result.card_number)
        self.app.refresh()


class ImportSportOrgAction(Action, metaclass=ActionFactory):
    def execute(self):
        file_name = get_open_file_name(_('Open SportOrg json'), _('SportOrg (*.json)'))
        if file_name:
            with open(file_name) as f:
                attr = get_races_from_file(f)
            SportOrgImportDialog(*attr).exec_()
            self.app.refresh()


class RentCardsAction(Action, metaclass=ActionFactory):
    def execute(self):
        RentCardsDialog().exec_()
        self.app.refresh()
