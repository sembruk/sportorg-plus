import pytest

from sportorg.models.memory import race
from sportorg.modules.coordinates.coordinates import import_coordinates_from_gpx, import_coordinates_from_iof_xml, import_coordinates_from_csv

@pytest.mark.parametrize(
    'file_name, function',
    [
        ('course.gpx', import_coordinates_from_gpx),
        ('course.xml', import_coordinates_from_iof_xml),
        ('course.csv', import_coordinates_from_csv),
    ]
)

def test_import_coordinates_from_gpx(file_name, function):
    cur_race = race()
    cur_race.control_points = []  # Clear control points to ensure test isolation

    function('tests/data/' + file_name)
    assert len(cur_race.control_points) == 6

    expected = [
        ('31', 3, 100, -359),
        ('32', 3, -214, -462),
        ('33', 3, -574, -309),
        ('34', 3, -482, 82),
        ('finish', 0, -194, 177),
        ('start', 0, 0, 0),
    ]

    for i, (code, score, x, y) in enumerate(expected):
        cp = cur_race.control_points[i]
        assert cp.code == code
        assert cp.score == score
        assert cp.x == x
        assert cp.y == y

