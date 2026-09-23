"""RCO Table 302.1(1), pinned row by row against the OAC 4101:8-3-01 text. One transcription, one pin."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class FireSeparationTableTests(unittest.TestCase):

    def test_wall_rows(self):
        from codes.ohio.rco import fire_separation as rco_fsd
        self.assertEqual(rco_fsd.WALLS, ((0.0, '1 HOUR'), (5.0, 'NONE')))
        self.assertEqual(rco_fsd.wall_rating(0.0), '1 HOUR')
        self.assertEqual(rco_fsd.wall_rating(4.99), '1 HOUR')
        self.assertEqual(rco_fsd.wall_rating(5.0), 'NONE')

    def test_projection_rows(self):
        from codes.ohio.rco import fire_separation as rco_fsd
        rated = '1 HOUR ON THE UNDERSIDE, OR HEAVY TIMBER, OR FIRE-RETARDANT-TREATED WOOD'
        self.assertEqual(rco_fsd.projection_rating(1.99), 'NOT ALLOWED')
        self.assertEqual(rco_fsd.projection_rating(2.0), rated)
        self.assertEqual(rco_fsd.projection_rating(4.99), rated)
        self.assertEqual(rco_fsd.projection_rating(5.0), 'NONE')

    def test_footnotes_a_and_b(self):
        """a: an eave fireblocked plate to sheathing; b: a rake with no gable vent. Each
           takes the rated row, and only that row, to 0 hours."""
        from codes.ohio.rco import fire_separation as rco_fsd
        self.assertEqual(rco_fsd.underside(2.0, rco_fsd.EAVE, fireblocked=True), '0 HOURS, FOOTNOTE a')
        self.assertEqual(rco_fsd.underside(2.0, rco_fsd.EAVE, fireblocked=False), rco_fsd.projection_rating(2.0))
        self.assertEqual(rco_fsd.underside(2.0, rco_fsd.RAKE, gable_vent=False), '0 HOURS, FOOTNOTE b')
        self.assertEqual(rco_fsd.underside(2.0, rco_fsd.RAKE, gable_vent=True), rco_fsd.projection_rating(2.0))
        self.assertEqual(rco_fsd.underside(2.0, rco_fsd.RAKE, fireblocked=True), rco_fsd.projection_rating(2.0))
        self.assertEqual(rco_fsd.underside(1.99, rco_fsd.EAVE, fireblocked=True), 'NOT ALLOWED')
        self.assertEqual(rco_fsd.underside(1.99, rco_fsd.RAKE, gable_vent=False), 'NOT ALLOWED')
        self.assertEqual(rco_fsd.underside(5.0, rco_fsd.RAKE), 'NONE')
        self.assertIn('fireblocking is provided from the wall top plate', rco_fsd.FOOTNOTE_A)
        self.assertIn('gable vent openings are not installed', rco_fsd.FOOTNOTE_B)

    def test_opening_rows(self):
        """Not allowed under 3'-0", 25 percent from 3'-0", unlimited from 5'-0"."""
        from codes.ohio.rco import fire_separation as rco_fsd
        self.assertEqual(rco_fsd.opening_max(2.99), 0.0)
        self.assertEqual(rco_fsd.opening_max(3.0), 0.25)
        self.assertEqual(rco_fsd.opening_max(4.99), 0.25)
        self.assertIsNone(rco_fsd.opening_max(5.0))

    def test_penetration_rows(self):
        from codes.ohio.rco import fire_separation as rco_fsd
        self.assertEqual(rco_fsd.penetration_rule(2.99), 'COMPLY WITH RCO 302.4')
        self.assertEqual(rco_fsd.penetration_rule(3.0), 'NONE REQUIRED')

    def test_rated_below_five_feet(self):
        from codes.ohio.rco import fire_separation as rco_fsd
        self.assertTrue(rco_fsd.rated(4.999))
        self.assertFalse(rco_fsd.rated(5.0))

    def test_an_edge_under_two_feet_is_not_permitted(self):
        from codes.ohio.rco import fire_separation as rco_fsd
        bad = rco_fsd.edge_violations([('X EAVE', rco_fsd.EAVE, 3.0, 1.25, True, True)])
        self.assertTrue(any('permits a projection at all' in b for b in bad), bad)


if __name__ == '__main__':
    unittest.main()
