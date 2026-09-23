"""The separation in section, src/separation.py: W4A and W4B, two U305 walls back to
back, each platform-framed in its own unit — what A-603 draws."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class W4SectionTests(unittest.TestCase):

    def test_the_model_passes(self):
        from src import separation as s
        self.assertEqual(s.w4_violations(), [])

    def test_two_walls_back_to_back(self):
        """One wall per unit, each 4-3/4", the pair 9-1/2" and the plans' stud-to-stud."""
        from src.partywall import SEP_STUD, W4_FACE
        from src import separation as s
        self.assertEqual([w.name for w in s.WALLS], ['W4A', 'W4B'])
        self.assertEqual([w.unit for w in s.WALLS], ['UNIT 1', 'UNITS 2 / 3'])
        self.assertEqual([w.side for w in s.WALLS], [-1, 1])
        self.assertAlmostEqual(s.FACE*12, 4.75)
        self.assertAlmostEqual(s.FINISHED*12, 9.5)
        self.assertAlmostEqual(s.FINISHED, SEP_STUD+2*W4_FACE)
        self.assertAlmostEqual(s.PLATE_STEP*12, 2.125)

    def test_a_pair_that_does_not_match_the_plans_fails(self):
        from lib.units import IN
        from src import separation as s
        self.assertTrue(any('the plans are drawn to' in x for x in s.w4_violations(finished=s.FINISHED+IN(1))))

    def test_each_wall_carries_its_own_floor_at_its_own_plate(self):
        from src import levels, separation as s
        a, b = s.WALLS
        self.assertEqual((a.floor, b.floor), ('F2', 'F1'))
        self.assertAlmostEqual(a.plate, levels.F2_PLATE)
        self.assertAlmostEqual(b.plate, levels.F1_PLATE)
        self.assertEqual((a.bears, b.bears), ('W1', 'W1R / W3'))

    def test_every_tier_is_under_ten_feet(self):
        from src import separation as s
        for w in s.WALLS:
            for t, h in s.unsupported(w):
                self.assertLessEqual(h, s.STUD_MAX, (w.name, t.name))

    def test_a_tier_over_ten_feet_fails_the_build(self):
        from src import separation as s
        tall = s.WALLS[0]._replace(plate=s.SLAB+11.0)
        self.assertTrue(any('602.3(5)' in x for x in s.w4_violations(walls=(tall,))))

    def test_neither_rim_crosses_the_joint(self):
        """Each rim sits on its own wall's plate, clear of the other unit's wall — the
           whole point of RCO 302.2.6."""
        from src import separation as s
        for w in s.WALLS:
            x0, x1, z0, z1 = s.rim(w)
            self.assertGreaterEqual(min(abs(x0), abs(x1)), s.CORE-1e-9)
            self.assertEqual(w.side > 0, x0 > 0)
            self.assertAlmostEqual(z0, w.plate)
            self.assertAlmostEqual(z1-z0, w.joist)

    def test_each_wall_is_fireblocked_at_its_own_floor_and_ceiling(self):
        from src import levels, separation as s
        for w in s.WALLS:
            zones = dict((nm, (z0, z1)) for nm, z0, z1 in s.fireblocks(w))
            self.assertLessEqual(zones['FLOOR LINE'][0], w.ceiling)
            self.assertGreaterEqual(zones['FLOOR LINE'][1], levels.SUBFLOOR_TOP)
            self.assertLessEqual(zones['CEILING LINE'][0], levels.UPPER_CEILING)
            self.assertGreaterEqual(zones['CEILING LINE'][1], levels.ROOF_PLATE)
            for _a, _b, h in s.cavities(w):
                self.assertLessEqual(h, s.FIREBLOCK_MAX)

    def test_a603_tags_and_zones_come_from_the_fireblocking_model(self):
        from src import separation as s
        ids, tags, zones = s.fireblock_model()
        self.assertEqual(s.w4_violations(fb=(ids, tags, zones)), [])
        self.assertEqual(sorted(zones), ['W4A', 'W4B'])
        missing = dict(tags); missing.pop('RIM')
        self.assertTrue(any('tag RIM' in x for x in s.w4_violations(fb=(ids, missing, zones))))
        one = {'W4A': zones['W4A']}
        self.assertTrue(any('no solid zone' in x for x in s.w4_violations(fb=(ids, tags, one))))

    def test_a_floor_line_short_of_its_zone_fails(self):
        from src import separation as s
        ids, tags, zones = s.fireblock_model()
        low = dict(zones, W4B=(s.SLAB, zones['W4B'][1]))
        self.assertTrue(any('solid zone' in x for x in s.w4_violations(fb=(ids, tags, low))))


if __name__ == '__main__':
    unittest.main()
