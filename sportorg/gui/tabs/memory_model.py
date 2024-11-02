import logging
import re
import uuid
from abc import abstractmethod
from copy import copy, deepcopy
from datetime import datetime

from PySide2.QtCore import QAbstractTableModel, Qt
from typing import List

from sportorg.language import _
from sportorg.models.constant import RentCards
from sportorg.models.memory import race
from sportorg.utils.time import time_to_hhmmss
from sportorg.modules.configs.configs import Config


class AbstractSportOrgMemoryModel(QAbstractTableModel):
    """
    Used to specify common table behavior
    """
    def __init__(self):
        super().__init__()
        self.race = race()
        self.cache = []
        self.init_cache()
        self.filter = {}
        self.r_count = 0
        self.max_rows_count = 5000
        self.c_count = len(self.get_headers())

        # temporary list, used to keep records, that are not filtered
        # main list will have only filtered elements
        # while clearing of filter list is recovered from backup
        self.filter_backup = []

        self.search = ''
        self.search_old = ''
        self.search_offset = 0

    @abstractmethod
    def init_cache(self):
        pass

    @abstractmethod
    def get_values_from_object(self, obj):
        pass

    @abstractmethod
    def get_source_array(self) -> List:
        pass

    @abstractmethod
    def set_source_array(self, array):
        pass

    @abstractmethod
    def get_headers(self) -> List:
        pass

    @abstractmethod
    def get_data(self, position):
        pass

    @abstractmethod
    def duplicate(self, position):
        pass

    def columnCount(self, parent=None, *args, **kwargs):
        return self.c_count

    def rowCount(self, parent=None, *args, **kwargs):
        return min(len(self.cache), self.max_rows_count)

    def headerData(self, index, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                columns = self.get_headers()
                return columns[index]
            if orientation == Qt.Vertical:
                return str(index+1)

    def data(self, index, role=None):
        if role == Qt.DisplayRole:
            try:
                row = index.row()
                column = index.column()
                answer = self.cache[row][column]
                return answer
            except Exception as e:
                logging.error(str(e))
        return

    def clear_filter(self, remove_condition=True):
        if remove_condition:
            self.filter.clear()
        if self.filter_backup and len(self.filter_backup):
            whole_list = self.get_source_array()
            whole_list.extend(self.filter_backup)
            self.set_source_array(whole_list)
            self.filter_backup.clear()

    def set_filter_for_column(self, column_num, filter_regexp, strict_check=False):
        self.filter.update({column_num: [filter_regexp, strict_check]})

    def apply_filter(self):
        # get initial list and filter it
        current_array = self.get_source_array()
        current_array.extend(self.filter_backup)
        self.filter_backup.clear()
        for column in self.filter.keys():
            check_regexp = re.escape(self.filter.get(column)[0])
            strict_check = self.filter.get(column)[1]

            check = re.compile('.*' + check_regexp + '.*')

            if strict_check:
                check = re.compile('^' + check_regexp + '$')

            i = 0
            while i < len(current_array):
                value = self.get_item(current_array[i], column)
                if not check.match(str(value)):
                    self.filter_backup.append(current_array.pop(i))
                    i -= 1
                i += 1

        # set main list to result
        # note, unfiltered items are in filter_backup
        self.set_source_array(current_array)
        self.init_cache()


    def apply_search(self):
        if not self.search:
            return
        if self.search != self.search_old:
            self.search_offset = 0
        else:
            self.search_offset += 1
        current_array = self.get_source_array()
        escaped_text = re.escape(self.search)
        check = re.compile(escaped_text, re.IGNORECASE)

        count_columns = len(self.get_headers())
        columns = range(count_columns)

        # 1 phase - full match
        i = 0
        maximum = len(current_array)
        while i < maximum:
            cur_pos = (self.search_offset + i) % maximum
            obj = self.get_values_from_object(current_array[cur_pos])
            for column in columns:
                value = str(obj[column])
                if value == self.search:
                    self.search_offset = cur_pos
                    self.search_old = self.search
                    return
            i += 1

        # 2 phase - match
        i = 0
        maximum = len(current_array)
        while i < maximum:
            cur_pos = (self.search_offset + i) % maximum
            obj = self.get_values_from_object(current_array[cur_pos])
            for column in columns:
                value = str(obj[column])
                if check.match(value):
                    self.search_offset = cur_pos
                    self.search_old = self.search
                    return
            i += 1

        # 3 phase - search
        i = 0
        maximum = len(current_array)
        while i < maximum:
            cur_pos = (self.search_offset + i) % maximum
            obj = self.get_values_from_object(current_array[cur_pos])
            for column in columns:
                value = str(obj[column])
                if check.search(value):
                    self.search_offset = cur_pos
                    self.search_old = self.search
                    return
            i += 1

        self.search_offset = -1

    def sort(self, p_int, order=None):
        """Sort table by given column number.
        """
        def sort_key(x):
            item = self.get_item(x, p_int)
            return item is None, str(type(item)), item
        try:
            self.layoutAboutToBeChanged.emit()

            source_array = self.get_source_array()

            if len(source_array):
                source_array = sorted(source_array, key=sort_key)
                if order == Qt.DescendingOrder:
                    source_array = source_array[::-1]

                self.set_source_array(source_array)

                self.init_cache()
            self.layoutChanged.emit()
        except Exception as e:
            logging.error(str(e))

    def update_one_object(self, part, index):
        self.values[index] = self.get_values_from_object(part)

    def get_item(self, obj, n_col):
        return self.get_values_from_object(obj)[n_col]

    def get_column_unique_values(self, n_col):
        # returns sorted unique values from specified column
        return sorted(set([str(row[n_col]) for row in self.cache]))


class PersonMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.init_cache()

    def get_headers(self):
        use_birthday = Config().configuration.get('use_birthday', False)
        headers = [_('Last name'), _('First name'), _('Sex'), _('Age') if use_birthday else _('Year title'),
                   _('Qualification title'), _('Group'), _('Team'),
                   _('Bib'), _('Start'), _('Card title'),
                   _('Comment'), _('Result count title'), _('Rented card'),
                   _('World code title'), _('National code title'),
                   _('Out of competition title')]

        if self.race.is_relay():
            headers.insert(9, _('Start group'))
        if self.race.is_team_race():
            headers.insert(11, _('Subgroup'))
        return headers

    def init_cache(self):
        self.cache.clear()
        for i in range(len(self.race.persons)):
            self.cache.append(self.get_data(i))

    def get_data(self, position):
        return self.get_values_from_object(self.race.persons[position])

    def duplicate(self, position):
        person = self.race.persons[position]
        new_person = copy(person)
        new_person.id = uuid.uuid4()
        new_person.bib = 0
        new_person.card_number = 0
        self.race.persons.insert(position, new_person)

    def get_values_from_object(self, obj):
        ret = []
        person = obj

        is_rented_card = person.is_rented_card or RentCards().exists(person.card_number)

        ret.append(person.surname)
        ret.append(person.name)
        ret.append(person.sex.get_title())
        use_birthday = Config().configuration.get('use_birthday', False)
        if use_birthday:
            ret.append(person.age)
        else:
            ret.append(person.get_year())
        if person.qual:
            ret.append(person.qual.get_title())
        else:
            ret.append('')
        if person.group:
            ret.append(person.group.name)
        else:
            ret.append('')
        if person.team:
            ret.append(person.team.full_name)
        else:
            ret.append('')
        ret.append(person.bib)
        if self.race.get_setting('system_start_source', 'protocol') == 'group':
            if person.group and person.group.start_time:
                ret.append(time_to_hhmmss(person.group.start_time))
            else:
                ret.append('')
        else:
            if person.start_time:
                ret.append(time_to_hhmmss(person.start_time))
            else:
                ret.append('')
        if self.race.is_relay():
            ret.append(person.start_group)
        ret.append(person.card_number)
        ret.append(person.comment)
        if self.race.is_team_race():
            ret.append(person.subgroups_str())
        ret.append(person.result_count)
        ret.append(_('Rented card') if is_rented_card else _('Rented stub'))
        ret.append(str(person.world_code) if person.world_code else '')
        ret.append(str(person.national_code) if person.national_code else '')

        out_of_comp_status = ''
        if person.is_out_of_competition:
            out_of_comp_status = _('o/c')
        ret.append(out_of_comp_status)

        return ret

    def get_source_array(self):
        return self.race.persons

    def set_source_array(self, array):
        self.race.persons = array


class ResultMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()
        self.values = None
        self.count = None

    def get_headers(self):
        if self.race.get_setting('marked_route_mode', 'off') == 'off':
            return [_('Last name'), _('First name'), _('Group'), _('Team'), _('Bib'), _('Card title'),
                    _('Start'), _('Finish'), _('Result'), _('Status'), _('Penalty'),
                    _('Place'), _('Type'), _('Readout'), _('Rented card')]
        return [_('Last name'), _('First name'), _('Group'), _('Team'), _('Bib'), _('Card title'),
                _('Start'), _('Finish'), _('Result'), _('Status'), _('Credit'), _('Penalty'), _('Penalty legs title'),
                _('Place'), _('Type'), _('Readout'), _('Rented card')]

    def init_cache(self):
        self.cache.clear()
        for i in range(len(self.race.results)):
            self.cache.append(self.get_data(i))

    def get_data(self, position):
        ret = self.get_values_from_object(self.race.results[position])
        return ret

    def duplicate(self, position):
        result = self.race.results[position]
        new_result = copy(result)
        new_result.id = uuid.uuid4()
        new_result.splits = deepcopy(result.splits)
        self.race.results.insert(position, new_result)

    def get_values_from_object(self, result):
        i = result
        person = i.person

        group = ''
        team = ''
        first_name = ''
        last_name = ''
        bib = result.get_bib()
        rented_card = ''
        if person:
            is_rented_card = person.is_rented_card or RentCards().exists(i.card_number)
            first_name = person.name
            last_name = person.surname

            if person.group:
                group = person.group.name

            if person.team:
                team = person.team.full_name

            rented_card = _('Rented card') if is_rented_card else _('Rented stub')

        start = ''
        if i.get_start_time():
            time_accuracy = self.race.get_setting('time_accuracy', 0)
            start = i.get_start_time().to_str(time_accuracy)

        finish = ''
        if i.get_finish_time():
            time_accuracy = self.race.get_setting('time_accuracy', 0)
            finish = i.get_finish_time().to_str(time_accuracy)

        penalty = time_to_hhmmss(i.get_penalty_time())
        if self.race.get_setting('result_processing_mode', 'time') == 'scores':
            penalty = i.penalty_points

        if self.race.get_setting('marked_route_mode', 'off') == 'off':
            return [
                last_name,
                first_name,
                group,
                team,
                bib,
                i.card_number,
                start,
                finish,
                i.get_result(),
                i.status.get_title(),
                penalty,
                i.get_place(),
                str(i.system_type),
                time_to_hhmmss(datetime.fromtimestamp(i.created_at)),
                rented_card
            ]
        return [
            last_name,
            first_name,
            group,
            team,
            bib,
            i.card_number,
            start,
            finish,
            i.get_result(),
            i.status.get_title(),
            time_to_hhmmss(i.get_credit_time()),
            penalty,
            i.penalty_laps,
            i.get_place(),
            str(i.system_type),
            time_to_hhmmss(datetime.fromtimestamp(i.created_at)),
            rented_card
        ]

    def get_source_array(self):
        return self.race.results

    def set_source_array(self, array):
        self.race.results = array


class GroupMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self):
        return [_('Name'), _('Full name'), _('Course name'), _('Start fee title'), _('Type'), _('Length title'),
                _('Point count title'), _('Climb title'), _('Sex'),
                _('Min age') if self.race.is_team_race() else _('Min year title'),
                _('Max age') if self.race.is_team_race() else _('Max year title'),
                _('Start time'), _('Max time'), _('Start interval title'), _('Start corridor title'),
                _('Order in corridor title')]

    def init_cache(self):
        self.cache.clear()
        for i in range(len(self.race.groups)):
            self.cache.append(self.get_data(i))

    def get_data(self, position):
        ret = self.get_values_from_object(self.race.groups[position])
        return ret

    def duplicate(self, position):
        group = self.race.groups[position]
        new_group = copy(group)
        new_group.id = uuid.uuid4()
        new_group.name = new_group.name + '_'
        self.race.groups.insert(position, new_group)

    def get_values_from_object(self, group):
        course = group.course

        control_count = len(course.get_unrolled_controls()) if course else 0

        return [
            group.name,
            group.long_name,
            course.name if course else '',
            group.price,
            self.race.get_type(group).get_title(),
            course.length if course else 0,
            control_count,
            course.climb if course else 0,
            group.sex.get_title(),
            group.min_age if self.race.is_team_race() else group.min_year,
            group.max_age if self.race.is_team_race() else group.max_year,
            time_to_hhmmss(group.start_time),
            time_to_hhmmss(group.max_time),
            group.start_interval,
            group.start_corridor,
            group.order_in_corridor,
        ]

    def get_source_array(self):
        return self.race.groups

    def set_source_array(self, array):
        self.race.groups = array


class CourseMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self):
        return [_('Name'), _('Length title'), _('Point count title'), _('Climb title'), _('Controls')]

    def init_cache(self):
        self.cache.clear()
        for i in range(len(self.race.courses)):
            self.cache.append(self.get_data(i))

    def get_data(self, position):
        ret = self.get_values_from_object(self.race.courses[position])
        return ret

    def duplicate(self, position):
        course = self.race.courses[position]
        new_course = copy(course)
        new_course.id = uuid.uuid4()
        new_course.name = new_course.name + '_'
        new_course.controls = deepcopy(course.controls)
        self.race.courses.insert(position, new_course)

    def get_values_from_object(self, course):
        return [
            course.name,
            course.length,
            len(course.get_unrolled_controls()),
            course.climb,
            ' '.join(course.get_code_list()),
        ]

    def get_source_array(self):
        return self.race.courses

    def set_source_array(self, array):
        self.race.courses = array


class TeamMemoryModel(AbstractSportOrgMemoryModel):
    def __init__(self):
        super().__init__()

    def get_headers(self):
        return [_('Name'), _('Number'), _('Group'), _('Code'), _('Country'), _('Region'), _('Contact')]

    def init_cache(self):
        self.cache.clear()
        for i in range(len(self.race.teams)):
            self.cache.append(self.get_data(i))

    def get_data(self, position):
        ret = self.get_values_from_object(self.race.teams[position])
        return ret

    def duplicate(self, position):
        team = self.race.teams[position]
        new_team = copy(team)
        new_team.id = uuid.uuid4()
        new_team.name = new_team.name + '_'
        new_team.number = 0
        self.race.teams.insert(position, new_team)

    def get_values_from_object(self, team):
        return [
            team.name,
            team.number,
            team.group.name if team.group else '',
            team.code,
            team.country,
            team.region,
            team.contact
        ]

    def get_source_array(self):
        return self.race.teams

    def set_source_array(self, array):
        self.race.teams = array
