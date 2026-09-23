"""400 Oak's A-601: the one separation and what holds it up, the distances Table 302.1(1)
   is read at, and the concealed floor spaces under RCO 302.12."""
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class AssemblyTests(unittest.TestCase):

    def test_the_rated_walls_end_with_the_vapor_retarder(self):
        from src.sheets import a601
        from src.envelope import check_wall_rows
        check_wall_rows(a601.wall_rows())

    def test_f1_is_ul_l528_with_type_c_and_an_unpierced_membrane(self):
        from src.sheets import a601
        text = " ".join(a601._f1_notes())
        self.assertIn("TYPE X IS NOT AN ALTERNATE", text)
        # The listing bars INSULATION from the cavity, not the piping P-601 and M-101 run
        # through the open webs: the two sheets may not read as a contradiction.
        self.assertIn("NO INSULATION IN THE CAVITY", text)
        self.assertNotIn("NOTHING IN THE CAVITY", text)
        self.assertIn("WITHOUT PIERCING THE MEMBRANE", text)
        self.assertIn("SOFFIT", text)
        for gone in ("RADIATION DAMPER", "TJI", "ESR-1153", "MINERAL WOOL", "I-JOIST"):
            self.assertNotIn(gone, text)
        for stale in ("A-001", "A-301", "P-601", "UNITS 4", "S-103"):
            self.assertNotIn(stale, text)

    def test_the_stair_row_states_one_condition_in_each_cell(self):
        from arkitect.lib.units import fmt
        from src import fsd
        from src.sheets import a601
        row = next(r for r in a601.fire_separation_rows() if r[0].startswith("UNIT 3 STAIR"))
        # The rating is read at the LIMIT, which leaves exactly the table's 5'-0"; the
        # stair as drawn is narrower and leaves more. A cell carrying one figure from each
        # reads as a condition that does not exist on an 8'-9" face.
        self.assertEqual(fsd.PROJ_MAX+fsd.PROJ_FREE, fsd.OFF_B2)
        self.assertEqual(fsd.stair_clear()+fsd.STAIR_W, fsd.OFF_B2)
        self.assertIn(fmt(fsd.PROJ_MAX), row[2])
        self.assertIn(fmt(fsd.PROJ_FREE), row[2])
        self.assertNotIn(fmt(fsd.stair_clear()), row[2])
        self.assertIn(fmt(fsd.STAIR_W), row[3])
        self.assertIn(fmt(fsd.stair_clear()), row[3])
        self.assertNotIn(fmt(fsd.PROJ_MAX), row[3])

    def test_no_floor_needs_draftstopping(self):
        from src.sheets import a601
        self.assertLess(max(a601.floor_areas().values()), a601.DRAFTSTOP_SF)
        self.assertEqual(len(a601._fireblocking_notes()), len(a601.FB))
        # 302.12 names open-web trusses as a trigger: FB-7 says what S-102 frames, and the
        # 1,000 SF is what lets it off.
        from src.framing import FRAMING
        fb7 = a601._fireblocking_notes()[-1]
        self.assertIn(FRAMING, fb7)
        self.assertNotIn("NO JOIST IS OPEN-WEB", fb7)

    def test_the_sheet_is_in_the_set(self):
        from src.sheets.g001 import SHEET_INDEX
        self.assertIn("A-601", [n for n, _t in SHEET_INDEX])


if __name__ == '__main__':
    unittest.main()
