import re

class Version:
    def __init__(self, version):
        self.version = version
        self.major, self.minor, self.patch, self.prerelease, self.build = self.parse_version(version)

    @staticmethod
    def parse_version(version):
        # Regex to parse semantic version components
        pattern = r'^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$'
        match = re.match(pattern, version)
        if not match:
            raise ValueError(f"Invalid semantic version: {version}")

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        prerelease = match.group(4)
        build = match.group(5)
        return major, minor, patch, prerelease, build

    @staticmethod
    def compare_prerelease(pr1, pr2):
        """
        Compare pre-release versions:
        - Identifiers consisting of only digits are compared numerically.
        - Identifiers with letters are compared lexically.
        - A pre-release is always less than a non-pre-release version.
        """
        if pr1 is None and pr2 is None:
            return 0
        if pr1 is None:
            return 1
        if pr2 is None:
            return -1

        pr1_parts = pr1.split(".")
        pr2_parts = pr2.split(".")
        for p1, p2 in zip(pr1_parts, pr2_parts):
            if p1.isdigit() and p2.isdigit():
                diff = int(p1) - int(p2)
                if diff != 0:
                    return diff
            elif p1.isdigit():
                return -1
            elif p2.isdigit():
                return 1
            else:
                if p1 != p2:
                    return (p1 > p2) - (p1 < p2)

        return len(pr1_parts) - len(pr2_parts)

    def __lt__(self, other):
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        prerelease_comparison = self.compare_prerelease(self.prerelease, other.prerelease)
        return prerelease_comparison < 0

    def __eq__(self, other):
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)

    def __le__(self, other):
        return self < other or self == other

    def __str__(self):
        return self.version

    def __repr__(self):
        return str(self)

    def is_compatible(self, o):
        return self.major == o.major

