import pytest

from sportorg.common.version import Version


@pytest.mark.parametrize(('version1', 'version2', 'expected'), [
    ("1.0.0", "2.0.0", -1),
    ("2.0.0", "1.0.0", 1),
    ("1.0.0", "1.0.0", 0),
    ("1.10.0", "1.2.0", 1),
    ("1.0.0-alpha", "1.0.0", -1),
    ("1.0.0", "1.0.0-alpha", 1),
    ("1.0.0-alpha", "1.0.0-beta", -1),
    ("1.0.0-beta", "1.0.0-beta.2", -1),
    ("1.0.0-beta.2", "1.0.0-beta.10", -1),
    ("1.0.0-beta.10", "1.0.0-rc.1", -1),
])

def test_version(version1, version2, expected):
    if expected == 0:
        assert Version(version1) == Version(version2)
    elif expected > 0:
        assert Version(version1) > Version(version2)
    else:
        assert Version(version1) < Version(version2)

def test_version_is_compatible():
    assert Version('1.12.0').is_compatible(Version('1.11.2-beta.0'))
    assert not Version('1.12.0').is_compatible(Version('2.12.0-beta.0'))
