"""RCO 602.10's tables, pinned cell by cell against the code text. One transcription, one pin."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from arkitect.lib.units import IN


class BracingTableTests(unittest.TestCase):

    def test_table_r602_10_3_1_at_115_mph_continuous_sheathing_column(self):
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        self.assertEqual(rco_bracing.REQ_LENGTH[rco_bracing.ROOF_ONLY], ((10, 2.0), (20, 3.5), (30, 4.5), (40, 6.0), (50, 7.5), (60, 9.0)))
        self.assertEqual(rco_bracing.REQ_LENGTH[rco_bracing.ROOF_AND_FLOOR], ((10, 3.5), (20, 6.5), (30, 9.0), (40, 11.5), (50, 14.0), (60, 17.0)))
        self.assertEqual(rco_bracing.MAX_SPACING, 60.0)

    def test_figure_r602_10_6_4_portal_header(self):
        """The sawn header the schedule prints over a portal is DERIVED from the figure's
           net minimum, not typed beside it: two plies make the 3" net width and a 2x12's
           dressed depth makes the 11-1/4"."""
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        self.assertEqual(rco_bracing.PORTAL_HEADER, (IN(3), IN(11.25)))
        self.assertEqual(rco_bracing.portal_header_size(), '2-2x12')
        self.assertGreaterEqual(rco_bracing.header_depth(rco_bracing.portal_header_size()),
                                rco_bracing.PORTAL_HEADER[1]-1e-9)

    def test_the_portal_header_follows_its_minimum(self):
        """Deepen the figure's minimum and the scheduled size follows it, rather than
           staying at the 2x12 that happens to suit today's figures."""
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        keep = rco_bracing.PORTAL_HEADER
        try:
            rco_bracing.PORTAL_HEADER = (IN(3), IN(13.0))
            self.assertEqual(rco_bracing.portal_header_size(), '2-2x14')
        finally:
            rco_bracing.PORTAL_HEADER = keep

    def test_table_r602_10_3_2_factors(self):
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        self.assertEqual(rco_bracing.F_EXPOSURE['B'], 1.00)
        self.assertEqual(rco_bracing.F_EAVE_RIDGE[rco_bracing.ROOF_ONLY], ((5, 0.70), (10, 1.00), (15, 1.30), (20, 1.60)))
        self.assertEqual(rco_bracing.F_EAVE_RIDGE[rco_bracing.ROOF_AND_FLOOR], ((5, 0.85), (10, 1.00), (15, 1.15), (20, 1.30)))
        self.assertEqual(rco_bracing.F_STORY_HEIGHT, ((8, 0.90), (9, 0.95), (10, 1.00), (11, 1.05), (12, 1.10)))
        self.assertEqual(rco_bracing.F_LINES, ((2, 1.00), (3, 1.30), (4, 1.45), (5, 1.60)))

    def test_table_r602_10_5_rows_this_set_reads(self):
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        self.assertEqual(rco_bracing.CS_WSP_MIN[9][:5], ((64, 27), (68, 27), (72, 27), (76, 29), (80, 30)))
        self.assertEqual(rco_bracing.CS_WSP_MIN[10][:5], ((64, 30), (68, 30), (72, 30), (76, 30), (80, 30)))
        self.assertEqual(rco_bracing.CS_WSP_MIN[8][:5], ((64, 24), (68, 26), (72, 27), (76, 30), (80, 32)))
        self.assertEqual(rco_bracing.CS_WSP_MIN[8][-1], (96, 48)); self.assertEqual(rco_bracing.CS_WSP_MIN[12][-1], (144, 72))
        self.assertEqual(rco_bracing.CS_PF_MIN, ((8, 16), (9, 18), (10, 20))); self.assertEqual(rco_bracing.CS_PF_CREDIT, 1.5)

    def test_location_end_and_connection_limits(self):
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        from arkitect.lib.units import IN
        self.assertEqual((rco_bracing.FIRST_PANEL_MAX, rco_bracing.PANEL_GAP_MAX, rco_bracing.TWO_PANEL_LINE), (10.0, 20.0, 16.0))
        self.assertAlmostEqual(rco_bracing.RETURN_MIN, IN(24)); self.assertAlmostEqual(rco_bracing.CORNER_D_MIN, IN(24))
        self.assertAlmostEqual(rco_bracing.END_PANEL_ALONE, IN(48)); self.assertEqual(rco_bracing.HOLD_DOWN_LB, 800)
        self.assertAlmostEqual(rco_bracing.HEEL_NO_BLOCKING, IN(9.25)); self.assertAlmostEqual(rco_bracing.HEEL_BLOCKING_MAX, IN(15.25))
        self.assertAlmostEqual(rco_bracing.NAIL_PENETRATION, IN(1.75))

    def test_lookups_read_the_column_and_row_at_or_above(self):
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        from arkitect.lib.units import IN
        self.assertAlmostEqual(rco_bracing.cs_wsp_min(8.95, 6.0), IN(27))            # 9 ft column, 72" row
        self.assertAlmostEqual(rco_bracing.cs_wsp_min(9.02, 6.0+8/12.0), IN(30))     # 10 ft column, 80" row
        self.assertAlmostEqual(rco_bracing.cs_wsp_min(8.0, 4.0), IN(24))             # <= 64" row
        self.assertAlmostEqual(rco_bracing.cs_wsp_min(8.0, 6.5), IN(32))             # 78" reads the 80" row
        self.assertAlmostEqual(rco_bracing.cs_pf_min(8.95), IN(18))
        with self.assertRaises(ValueError):
            rco_bracing.cs_wsp_min(8.0, 8.5)                                         # past the 8 ft column's last row
        self.assertAlmostEqual(rco_bracing.interp(rco_bracing.REQ_LENGTH[rco_bracing.ROOF_AND_FLOOR], 48.0), 13.5)
        self.assertAlmostEqual(rco_bracing.interp(rco_bracing.F_EAVE_RIDGE[rco_bracing.ROOF_ONLY], 3.0), 0.70)

    def test_table_r602_10_6_4_exposure_b_115_mph_column(self):
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        self.assertEqual(rco_bracing.STRAP_B115[0], ('2x4 NO. 2', 0, 10, 18, 1000))
        self.assertEqual(rco_bracing.STRAP_B115[1:4], (('2x4 NO. 2', 1, 10, 9, 1000), ('2x4 NO. 2', 1, 10, 16, 1025), ('2x4 NO. 2', 1, 10, 18, 1275)))
        self.assertEqual(rco_bracing.STRAP_B115[-1], ('2x6 STUD', 4, 12, 18, 3800))
        self.assertEqual(len(rco_bracing.STRAP_B115), 18)
        self.assertEqual((rco_bracing.PORTAL_MAX_PER_LINE, rco_bracing.PORTAL_OPENING, rco_bracing.PORTAL_MAX_HEADER_HEIGHT, rco_bracing.PORTAL_ANCHOR_LB), (4, (2.0, 18.0), 10.0, 670))

    def test_strap_lookup(self):
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        self.assertEqual(rco_bracing.strap_lb(8.95, 3.0), 1000)
        self.assertEqual(rco_bracing.strap_lb(9.02, 12.0, pony=1.0), 1025)
        self.assertEqual(rco_bracing.strap_lb(11.0, 3.0), 1500)  # a 12 ft wall reads the 2 ft pony wall rows, their limit a maximum
        with self.assertRaises(ValueError):
            rco_bracing.strap_lb(9.0, 20.0)                      # past the 18 ft opening of every row

    def test_lookups_at_the_heights_a_nine_foot_story_reads(self):
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        self.assertEqual(rco_bracing.interp(rco_bracing.REQ_LENGTH[rco_bracing.ROOF_AND_FLOOR], 20), 6.5)
        self.assertEqual(rco_bracing.interp(rco_bracing.REQ_LENGTH[rco_bracing.ROOF_ONLY], 33), 4.5+0.3*1.5)
        self.assertEqual(rco_bracing.cs_wsp_min(9.0, 6.0), IN(27))          # 9 ft wall, 72 in opening
        self.assertEqual(rco_bracing.cs_wsp_min(9.02, 6.0), IN(30))         # Level 2's 9'-0-1/4" reads the 10 ft column
        self.assertEqual(rco_bracing.cs_pf_min(9.0), IN(18))


if __name__ == '__main__':
    unittest.main()
