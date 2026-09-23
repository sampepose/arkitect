"""twins.py finds what two projects carry word for word, and the count may not grow."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path: sys.path.insert(0, HERE)
from arkitect.lib import workspace
from arkitect.lib.verify import twins

SHARED = '''def area(w, d):
    """Plan area."""
    return w*d
'''
READS_A_GLOBAL = '''def depth():
    """Reads a figure the two projects set differently."""
    return COVER*2
'''
IMPORTS_INSIDE = '''def rows():
    """Imports the project's model in its body."""
    from src.framing import HEADERS
    return len(HEADERS)
'''
READS_THE_PACKAGE = '''def wall():
    """Reads the project's own model."""
    return levels.PLATE
'''


def _tree(root, name, cover, body):
    d = os.path.join(root, name, twins.PACKAGE); os.makedirs(d)
    with open(os.path.join(d, 'model.py'), 'w') as f:
        f.write('from src import levels\nCOVER = %s\n\n%s\n%s\n%s\n%s\n' % (cover, SHARED, READS_A_GLOBAL, IMPORTS_INSIDE, body))
    return d


class TwinsTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); root = self.tmp.name
        _tree(root, 'one', '1.0', READS_THE_PACKAGE + '\ndef only_here():\n    x = 1\n    return x\n')
        _tree(root, 'two', '2.0', READS_THE_PACKAGE + '\ndef only_here():\n    x = 2\n    return x\n')
        rows = twins.survey(root)
        self.assertEqual(len(rows), 1)
        self.rel, _a, _b, self.movable, self.needs = rows[0]
        self.total = twins.total(rows)

    def tearDown(self): self.tmp.cleanup()

    def test_an_identical_function_is_movable(self):
        self.assertEqual(self.movable, {'area': 3})

    def test_a_function_that_differs_is_not_a_twin(self):
        self.assertNotIn('only_here', self.movable); self.assertNotIn('only_here', self.needs)

    def test_a_twin_reading_a_differing_global_needs_parameters(self):
        self.assertEqual(self.needs['depth'], (3, ['COVER']))

    def test_a_twin_reading_the_projects_package_needs_parameters(self):
        self.assertEqual(self.needs['wall'], (3, ['levels']))

    def test_a_twin_importing_the_package_in_its_body_needs_parameters(self):
        self.assertEqual(self.needs['rows'], (4, ['src.framing']))

    def test_the_total_is_every_twin_line(self):
        self.assertEqual(self.total, 13)


def ceiling(ws=None):
    """What the workspace's projects may still carry word for word, in lines (twins.py prints
       the list): arkitect.toml's [verify] twins_ceiling, 0 when unset. It belongs to the
       projects, not the engine -- a new workspace starts at nothing copied. Lower it when a
       move takes it down."""
    return workspace.setting('verify', 'twins_ceiling', 0, ws)


class CeilingTests(unittest.TestCase):

    def test_no_definition_was_copied_between_projects(self):
        got = twins.total(twins.survey(os.path.join(workspace.WORKSPACE, 'projects')))
        self.assertLessEqual(got, ceiling(),
            'a definition was copied between projects: share it in arkitect/lib/ or arkitect/codes/ instead '
            '(python3 arkitect/lib/verify/twins.py --why)')


if __name__ == '__main__':
    unittest.main()
