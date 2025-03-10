import csv
import logging
import dateutil.parser
from sportorg.language import _
from sportorg.models import memory
from sportorg.models.memory import Qualification, Sex
from sportorg.modules.configs.configs import Config


def detect_encoding(file_path):
    for encoding in ['utf-8', 'cp1251']:
        try:
            with open (file_path, encoding=encoding) as file:
                _ = file.read()  # Attempt to read the file
            return encoding
        except UnicodeDecodeError:
            pass  # Continue to the next encoding
    return None

class OrgeoCSVReader:
    def __init__(self, data=None):
        self._data = [] if data is None else data

        self._groups = set()
        self._teams = {}
        self._cards = set()
        self._headers = {}

    def parse(self, source):
        encoding = detect_encoding(source)
        if encoding is None:
            print("Unable to detect the encoding.")
        with open(source, encoding=encoding) as csv_file:
            spam_reader = csv.reader(csv_file, delimiter=';')

            headers_dict = {
                'Группа': 'group_name',
                'Пол': 'sex',
                'Фамилия': 'surname',
                'Имя': 'name',
                'Команда': 'team_name',
                'Код': 'code',
                'Регион': 'district',
                'Квал.': 'qual_str',
                'Дата рожд.': 'date_of_birth',
                'Год': 'date_of_birth',
                'Дата рождения': 'date_of_birth',
                '№ чипа': 'sportident_card',
                'Номер чипа': 'sportident_card',
                'Примечания': 'comment',
                'Кем подана': 'representative',
                'Телефон': 'cell_number',
                'E-mail': 'email',
                'Номер заявки': 'claim_id',
                'Номер команды': 'claim_id',
                'Время подачи': 'claim_time',
                'Статус': 'status'
            }
            first_row = next(spam_reader, None)
            col_index = 0
            for col_name in first_row:
                if col_name in headers_dict:
                    self._headers[col_index] = headers_dict[col_name]
                col_index += 1
            for row in spam_reader:
                self.append(row)

        return self

    @property
    def data(self):
        return self._data

    def append(self, person):
        if not person or len(person) < 1:
            return

        person_dict = {}

        for i in range(len(person)):
            if i in self._headers:
                person_dict[self._headers[i]] = person[i]

        if 'code' in person_dict and person_dict['code'].isdigit():
            person_dict['code'] = int(person_dict['code'])
        if 'date_of_birth' in person_dict:
            date_of_birth = dateutil.parser.parse(person_dict['date_of_birth']).date()
            if not Config().configuration.get('use_birthday', False):
                date_of_birth = date_of_birth.replace(day=1, month=1)
            person_dict['date_of_birth'] = date_of_birth
        if 'claim_id' in person_dict:
            person_dict['claim_id'] = int(person_dict['claim_id'])
            claim_id = person_dict['claim_id']
            team_name = person_dict['team_name'] if 'team_name' in person_dict else ''
            self._teams[claim_id] = team_name
        self._data.append(person_dict)

    @property
    def groups(self):
        if not self._groups:
            for row in self.data:
                self._groups.add(row['group_name'])

        return self._groups

    @property
    def cards(self):
        if not len(self._cards):
            for row in self.data:
                self._cards.add(row['sportident_card'])

        return self._cards

    @property
    def teams(self):
        return self._teams


def import_csv(source):
    csv_reader = OrgeoCSVReader()
    orgeo_data = csv_reader.parse(source)

    obj = memory.race()

    old_lengths = obj.get_lengths()

    for group_name in orgeo_data.groups:
        group = memory.find(obj.groups, name=group_name)
        if group is None:
            group = memory.Group()
            group.name = group_name
            group.long_name = group_name
            obj.groups.append(group)

    for claim_id,team_name in orgeo_data.teams.items():
        team = memory.find(obj.teams, number=claim_id)
        if team is None:
            team = memory.Team()
            team.name = team_name
            team.number = claim_id
            obj.teams.append(team)

    for person_dict in orgeo_data.data:
        person_team = None
        if 'claim_id' in person_dict:
            person_team = memory.find(obj.teams, number=person_dict['claim_id'])
            if 'representative' in person_dict:
                person_team.contact = person_dict['representative']
            if 'cell_number' in person_dict:
                person_team.contact += ' ' + person_dict['cell_number']
            if 'email' in person_dict:
                person_team.contact += ' ' + person_dict['email']
            person_team.code = str(person_dict['code']) if 'code' in person_dict else ''
            if 'district' in person_dict:
                person_team.region = person_dict['district']

        person = memory.Person()
        person.name = person_dict['name']
        person.surname = person_dict['surname']
        if 'sex' in person_dict:
            person.sex = Sex.M if person_dict['sex'] == 'М' else Sex.F
        person.bib = person_dict['bib'] if 'bib' in person_dict else 0
        person.birth_date = person_dict['date_of_birth']
        if 'sportident_card' in person_dict and person_dict['sportident_card'].isdigit():
            person.card_number = int(person_dict['sportident_card'])
        else:
            person.is_rented_card = True
        person.group = memory.find(obj.groups, name=person_dict['group_name'])
        if person_team is not None:
            if obj.is_team_race():
                person_team.group = person.group
            person.team = person_team
        if 'qual_id' in person_dict and person_dict['qual_id'].isdigit():
            person.qual = Qualification(int(person_dict['qual_id']))
        elif 'qual_str' in person_dict:
            person.qual = Qualification.get_qual_by_name(person_dict['qual_str'])
        if 'status' in person_dict:
            person.comment = person_dict['status'] + ' '
        if 'comment' in person_dict:
            person.comment += person_dict['comment']

        obj.persons.append(person)

    new_lengths = obj.get_lengths()

    logging.info(_('Import result'))
    logging.info('{}: {}'.format(_('Persons'), new_lengths[0]-old_lengths[0]))
    logging.info('{}: {}'.format(_('Groups'), new_lengths[2]-old_lengths[2]))
    logging.info('{}: {}'.format(_('Teams'), new_lengths[4]-old_lengths[4]))

    persons_dupl_cards = obj.get_duplicate_card_numbers()
    persons_dupl_names = obj.get_duplicate_names()

    if len(persons_dupl_cards):
        logging.info('{}'.format(_('Duplicate card numbers (card numbers are reset)')))
        for person in persons_dupl_cards:
            logging.info('{} {} {} {}'.format(
                person.full_name,
                person.group.name if person.group else '',
                person.team.name if person.team else '',
                person.card_number
            ))
            person.card_number = 0
    if len(persons_dupl_names):
        logging.info('{}'.format(_('Duplicate names')))
        for person in persons_dupl_names:
            person.card_number = 0
            logging.info('{} {} {} {}'.format(
                person.full_name,
                person.get_year(),
                person.group.name if person.group else '',
                person.team.name if person.team else ''
            ))

    if len(persons_dupl_names) or len(persons_dupl_cards):
        return _('Duplicate names or card numbers detected.\nSee Log tab')
    return ''

