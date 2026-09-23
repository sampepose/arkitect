"""400 Oak's A-001: the figures it quotes are the checks' own, its labels ascend, and no
   300 vocabulary is left in it."""
import re
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class PlanNoteTests(unittest.TestCase):

    def test_the_quoted_figures_are_the_models(self):
        from src.sheets import a001
        from arkitect.lib.units import inches
        text = " ".join(a001.plan_notes())
        self.assertIn(inches(a001._wc_side()), text)
        self.assertGreaterEqual(a001._wc_side(), 15/12.0)
        u1, u23 = a001._glazing()
        self.assertIn("%.0f%% IN UNIT 1 AND %.0f%% IN UNITS 2 AND 3" % (u1, u23), text)

    def test_the_labels_ascend(self):
        from src.sheets import a001
        labels = [re.match(r"(\d+)([a-z]?)\.", n).groups() for n in a001.plan_notes()]
        keys = [(int(n), s) for n, s in labels]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(len(set(keys)), len(keys))

    def test_no_300_vocabulary(self):
        from src.sheets import a001
        text = " ".join(a001.plan_notes())
        for stale in ("W4", "W5", "SAGE", "ELM", "UNIT 4", "UNIT 5", "A-103", "P-601", "TANKLESS", "GAS METER"):
            self.assertNotIn(stale, text)


if __name__ == '__main__':
    unittest.main()
