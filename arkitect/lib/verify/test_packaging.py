"""The pins are written twice -- pyproject.toml for an install, requirements.txt with the reasons
-- and must say the same; CI tests exactly the Pythons the package claims."""
import os
import re
import tomllib
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _pins(lines):
    return dict(m.groups() for m in (re.match(r'^\s*"?([A-Za-z0-9_.-]+)==([^"\s,]+)', ln) for ln in lines) if m)


class PackagingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(HERE, 'pyproject.toml'), 'rb') as fh:
            cls.project = tomllib.load(fh)['project']
        with open(os.path.join(HERE, 'requirements.txt')) as fh:
            cls.requirements = _pins(ln for ln in fh if not ln.lstrip().startswith('#'))

    def test_every_pin_agrees(self):
        declared = _pins(self.project['dependencies'] + self.project['optional-dependencies']['dev'])
        self.assertEqual(declared, self.requirements)

    def test_ci_tests_the_pythons_the_package_claims(self):
        with open(os.path.join(HERE, '.github', 'workflows', 'ci.yml')) as fh:
            ci = re.search(r'python: \[([^\]]+)\]', fh.read()).group(1)
        tested = sorted(v.strip(' "') for v in ci.split(','))
        lo, hi = re.match(r'>=3\.(\d+),<3\.(\d+)', self.project['requires-python']).groups()
        self.assertEqual(tested, ['3.%d' % m for m in range(int(lo), int(hi))])


if __name__ == '__main__':
    unittest.main()
