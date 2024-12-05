import logging

from sportorg.models.memory import race, Person, Group, Team
from sportorg.modules.backup.file import File


def test_main():
    File('tests/data/test.json', logging.root, File.JSON).open()
    r = race()
    person = None
    for p in r.persons:
        if p.full_name == 'Akhtarov Danil' and p.card_number == 9777775:
            person = p
    assert isinstance(person, Person), 'Import person failed'
    assert isinstance(person.group, Group), 'Import group failed'
    assert isinstance(person.team, Team), 'Import team failed'
