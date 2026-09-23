"""300 reads codes/columbus/zoning.py's constants rather than its own copies.

Moved here from codes/verify/test_zoning_rules.py in phase 1 of the public release: it is a
claim about this project, and the engine's tests may not lean on a project the public engine
does not ship. The promotion to the shared layer is only real if the copy left."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class ConsumerTests(unittest.TestCase):

    def test_300_reads_these_rather_than_its_own_copies(self):
        from codes.columbus import zoning as Z
        from src import sitework
        self.assertIs(sitework.ADU_PCT_MAX, Z.ADU_PCT_MAX)
        self.assertIs(sitework.COVERAGE_PERMITTED, Z.COVERAGE_MAX)
        self.assertIs(sitework.VISION_ST, Z.VISION_TRIANGLE_ST)
        self.assertIs(sitework.MANEUVER, Z.MANEUVER_MIN)
        self.assertIs(sitework.PARK_D, Z.STALL_D)


if __name__ == '__main__':
    unittest.main()
