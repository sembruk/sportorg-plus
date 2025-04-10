import codecs
import logging
import os

import webbrowser

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QFormLayout, QLabel, QDialog, QPushButton, QDialogButtonBox, QCheckBox
from docxtpl import DocxTemplate
from copy import copy, deepcopy

from sportorg import config
from sportorg.common.template import get_templates, get_text_from_file
from sportorg.gui.dialogs.file_dialog import get_open_file_name, get_save_file_name
from sportorg.gui.global_access import GlobalAccess
from sportorg.gui.utils.custom_controls import AdvComboBox
from sportorg.language import _
from sportorg.models.constant import RentCards
from sportorg.models.memory import race, races, get_current_race_index
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.score_calculation import ScoreCalculation
from sportorg.models.result.split_calculation import RaceSplits

_settings = {
    'last_template': None,
    'open_in_browser': True,
    'last_file': None,
    'save_to_last_file': False,
    'selected': False,
}


class ReportDialog(QDialog):
    def __init__(self):
        super().__init__(GlobalAccess().get_main_window())

    def exec_(self):
        self.init_ui()
        return super().exec_()

    def init_ui(self):
        self.setWindowTitle(_('Report creating'))
        self.setWindowIcon(QIcon(config.ICON))
        self.setSizeGripEnabled(False)
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.label_template = QLabel(_('Template'))
        self.item_template = AdvComboBox()
        self.item_template.addItems(get_templates(config.template_dir('reports')))
        self.layout.addRow(self.label_template, self.item_template)
        if _settings['last_template']:
            self.item_template.setCurrentText(_settings['last_template'])

        self.item_custom_path = QPushButton(_('Choose template'))

        def select_custom_path():
            file_name = get_open_file_name(_('Open HTML template'), _("HTML file (*.html)"))
            self.item_template.setCurrentText(file_name)

        self.item_custom_path.clicked.connect(select_custom_path)
        self.layout.addRow(self.item_custom_path)

        self.item_open_in_browser = QCheckBox(_('Open in browser'))
        self.item_open_in_browser.setChecked(_settings['open_in_browser'])
        self.layout.addRow(self.item_open_in_browser)

        self.item_save_to_last_file = QCheckBox(_('Save to last file'))
        self.item_save_to_last_file.setChecked(_settings['save_to_last_file'])
        self.layout.addRow(self.item_save_to_last_file)
        if _settings['last_file'] is None:
            self.item_save_to_last_file.setDisabled(True)

        self.item_selected = QCheckBox(_('Send selected'))
        self.item_selected.setChecked(_settings['selected'])
        self.layout.addRow(self.item_selected)

        def cancel_changes():
            self.close()

        def apply_changes():
            try:
                self.apply_changes_impl()
            except FileNotFoundError as e:
                logging.exception(e)
            except Exception as e:
                logging.exception(e)
                logging.exception(e)
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
        self.button_ok.setFocus()

    def apply_changes_impl(self):
        obj = race()
        mw = GlobalAccess().get_main_window()
        map_items = [obj.persons, obj.results, obj.groups, obj.courses, obj.teams]
        map_names = ['persons', 'results', 'groups', 'courses', 'teams']
        selected_items = {
            'persons': [],
            'results': [],
            'groups': [],
            'courses': [],
            'teams': [],
        }

        template_path = self.item_template.currentText()

        _settings['last_template'] = template_path
        _settings['open_in_browser'] = self.item_open_in_browser.isChecked()
        _settings['save_to_last_file'] = self.item_save_to_last_file.isChecked()
        _settings['selected'] = self.item_selected.isChecked()

        if _settings['selected']:
            cur_items = map_items[mw.current_tab]

            for i in mw.get_selected_rows():
                selected_items[map_names[mw.current_tab]].append(cur_items[i].to_dict())

        ResultCalculation(obj).process_results()
        RaceSplits(obj).generate()
        ScoreCalculation(obj).calculate_scores()

        races_dict = [r.to_dict() for r in races()]
        current_race = copy(races_dict[get_current_race_index()])

        if selected_items['groups']:
            current_race['groups'] = selected_items['groups']

        # Remove some private data
        for team in current_race['teams']:
            team.pop('contact', None)
        for person in current_race['persons']:
            person.pop('birth_date', None)
        current_race['settings'] = deepcopy(current_race['settings'])
        current_race['settings'].pop('live_token', None)
        current_race['settings'].pop('live_url', None)
        current_race['settings'].pop('live_urls', None)

        template_path_items = template_path.split('/')[-1]
        template_path_items = '.'.join(template_path_items.split('.')[:-1]).split('_')

        # remove tokens, containing only digits
        for i in template_path_items:
            if str(i).isdigit():
                template_path_items.remove(i)
        report_suffix = '_'.join(template_path_items)

        if template_path.endswith('.docx'):
            # DOCX template processing
            full_path = config.template_dir() + template_path
            doc = DocxTemplate(full_path)
            context = {}
            context['race'] = current_race
            context['name'] = config.NAME
            context['version'] = str(config.VERSION)
            doc.render(context)

            if _settings['save_to_last_file']:
                file_name = _settings['last_file']
            else:
                file_name = get_save_file_name(_('Save As MS Word file'), _("MS Word file (*.docx)"),
                                               '{}_official'.format(obj.data.get_start_datetime().strftime("%Y%m%d")))
            if file_name:
                doc.save(file_name)
                os.startfile(file_name)

        else:
            template = get_text_from_file(
                template_path,
                race=current_race,
                races=races_dict,
                rent_cards=list(RentCards().get()),
                current_race=get_current_race_index(),
                selected={}
            )

            if _settings['save_to_last_file']:
                file_name = _settings['last_file']
            else:
                default_name = '{}_{}'.format(obj.data.get_start_datetime().strftime("%Y%m%d"), report_suffix)
                if template_path.endswith('.html'):
                    file_name = get_save_file_name(
                        _('Save As HTML file'),
                        _("HTML file (*.html)"),
                        default_name
                    )
                elif template_path.endswith('.csv'):
                    file_name = get_save_file_name(
                        _('Save As CSV file'),
                        _("CSV file (*.csv)"),
                        default_name
                    )
            if len(file_name):
                _settings['last_file'] = file_name
                with codecs.open(file_name, 'w', 'utf-8') as file:
                    file.write(template)
                    file.close()

                # Open file in your browser
                if template_path.endswith('.html') and _settings['open_in_browser']:
                    webbrowser.open('file://' + file_name, new=2)
