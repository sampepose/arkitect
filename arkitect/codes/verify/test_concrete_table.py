"""RCO Table 402.2, pinned against the OAC 4101:8-4-01 text. One transcription, one pin."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from arkitect.codes.ohio.rco import concrete as T


class ConcreteTableTests(unittest.TestCase):

    def test_table_r402_2_is_the_ohio_text(self):
        """OAC 4101:8-4-01 efT. 3-1-2024, Table 402.2, cell by cell with its footnotes."""
        self.assertEqual(T.WEATHERINGS, ("NEGLIGIBLE", "MODERATE", "SEVERE"))
        self.assertEqual(T.T_R402_2, (
            ((2500, ""), (2500, ""), (2500, "c")),
            ((2500, ""), (2500, ""), (2500, "c")),
            ((2500, ""), (3000, "d"), (3000, "d")),
            ((2500, ""), (3000, "def"), (3500, "def"))))
        self.assertEqual((T.AIR_MIN, T.AIR_MAX), (0.05, 0.07))
        self.assertEqual(T.ACI_DEICING, "ACI 318 SECTION 19.3.3.4")

    def test_a_wall_standing_out_of_grade_is_held_to_the_exposed_row(self):
        wall = T.Concrete("WALL", T.NOT_EXPOSED, 3000, "AE")
        self.assertEqual(T.table_violations((wall,), "SEVERE", "WALL", 0.0), [])
        bad = T.table_violations((wall,), "SEVERE", "WALL", 0.5)
        self.assertEqual(len(bad), 1); self.assertIn("exposed to the weather", bad[0][1])

    def test_strength_and_air_are_held_to_the_cell(self):
        porch = T.Concrete("STEPS", T.PORCH_STEPS, 3000, "c")
        why = [w for _e, w in T.table_violations((porch,), "SEVERE", "WALL", 0.0)]
        self.assertEqual(len(why), 2)          # under 3,500 psi, and not air-entrained under footnote d
        self.assertEqual(T.table_violations((porch._replace(psi=3500, air="AE"),), "SEVERE", "WALL", 0.0), [])


if __name__ == '__main__':
    unittest.main()
