import json
import uuid

from sportorg import config
from sportorg.models.memory import races, new_event, Race, race, get_current_race_index, set_current_race_index
from sportorg.models.result.result_calculation import ResultCalculation
from sportorg.models.result.result_checker import ResultChecker
from sportorg.models.result.score_calculation import ScoreCalculation
from sportorg.models.result.split_calculation import RaceSplits
from sportorg.models.start.start_preparation import update_subgroups


def dump(file):
    data = {
        'version': config.VERSION.file,
        'current_race': get_current_race_index(),
        'races': [race_downgrade(r.to_dict()) for r in races()]
    }
    json.dump(data, file, sort_keys=True, indent=2, ensure_ascii=False)


def load(file):
    event, current_race = get_races_from_file(file)
    new_event(event)
    set_current_race_index(current_race)
    obj = race()
    for course in obj.courses:
        obj.add_cp_coords(course.get_cp_coords())
    ResultChecker.check_all()
    ResultCalculation(obj).process_results()
    RaceSplits(obj).generate()
    ScoreCalculation(obj).calculate_scores()
    update_subgroups()


def get_races_from_file(file):
    data = json.load(file)
    if 'races' not in data:
        data = {
            'races': [data] if not isinstance(data, list) else data,
            'current_race': 0
        }
    event = []
    for race_dict in data['races']:
        race_migrate(race_dict)
        obj = Race()
        obj.id = uuid.UUID(str(race_dict['id']))
        obj.update_data(race_dict)
        event.append(obj)
    current_race = 0
    if 'current_race' in data:
        current_race = int(data['current_race'])
    return event, current_race


def race_migrate(data):
    teams_groups = {}
    for person in data['persons']:
        if 'sportident_card' in person:
            person['card_number'] = person['sportident_card']
        if 'is_rented_sportident_card' in person:
            person['is_rented_card'] = person['is_rented_sportident_card']
        if 'organization_id' in person:
            person['team_id'] = person['organization_id']
            if 'organizations' in data:
                teams_groups[person['team_id']] = person['group_id']
    for result in data['results']:
        if 'sportident_card' in result:
            result['card_number'] = result['sportident_card']
    for group in data['groups']:
        if 'min_year' not in group:
            group['min_year'] = 0
        if 'max_year' not in group:
            group['max_year'] = 0
    if 'teams' not in data and 'organizations' in data:
        for org in data['organizations']:
            org['object'] = 'Team'
            if 'address' in org and org['address']:
                org['country'] = org['address']['country']['name']
                org['region'] = org['address']['state']
                if org['contact']:
                    org['contact'] = org['contact']['value']
            if org['id'] in teams_groups:
                org['group_id'] = teams_groups[org['id']]
        data['teams'] = data['organizations']
    settings = data['settings']
    if 'sportident_zero_time' in settings:
        settings['system_zero_time'] = settings['sportident_zero_time']
    if 'sportident_start_source' in settings:
        settings['system_start_source'] = settings['sportident_start_source']
    if 'sportident_start_cp_number' in settings:
        settings['system_start_cp_number'] = settings['sportident_start_cp_number']
    if 'sportident_finish_source' in settings:
        settings['system_finish_source'] = settings['sportident_finish_source']
    if 'sportident_finish_cp_number' in settings:
        settings['system_finish_cp_number'] = settings['sportident_finish_cp_number']
    if 'sportident_assign_chip_reading' in settings:
        settings['system_assign_chip_reading'] = settings['sportident_assign_chip_reading']
    if 'sportident_assignment_mode' in settings:
        settings['system_assignment_mode'] = settings['sportident_assignment_mode']
    if 'sportident_port' in settings:
        settings['system_port'] = settings['sportident_port']
    return data


def race_downgrade(data):
    return data
