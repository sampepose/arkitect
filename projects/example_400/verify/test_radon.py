"""400 Oak's passive radon system: the check passes, the gravel areas are the strips', each
   is on one pipe, the risers stand in walls, and the rules fire."""
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class RadonTests(unittest.TestCase):

    def test_the_system_passes(self):
        from src import radon as r
        r.check_radon()

    def test_the_areas_are_derived_from_the_strips(self):
        """The house's stair-wall strip stops short of the rear and divides nothing; Building
           2's bearing strip runs wall to wall and makes two."""
        from src import radon as r
        self.assertEqual((len(r.areas(r._FB1)), len(r.areas(r._FB2))), (1, 2))

    def test_one_riser_a_building_and_one_lateral(self):
        from src import radon as r
        self.assertEqual([(x.mark, x.building, len(x.laterals)) for x in r.RISERS],
                         [('RR-1', 'BUILDING 1', 0), ('RR-2', 'BUILDING 2', 1)])

    def test_the_risers_stand_in_walls_on_both_levels(self):
        from src import radon as r
        for x in r.RISERS:
            self.assertIsNone(r._room_at(x.building, 1, x.pos), x.mark)
            self.assertIsNone(r._room_at(x.building, 2, x.up), x.mark)
        moved = r.RISERS[0]._replace(pos=(14.0, 20.0))
        self.assertTrue(any('not in a wall' in v for v in r.radon_violations([moved, r.RISERS[1]])))

    def test_building_2_without_its_lateral_fails(self):
        from src import radon as r
        bare = r.RISERS[1]._replace(laterals=[])
        self.assertTrue(any('on 0 vent pipes' in v for v in r.radon_violations([r.RISERS[0], bare])))

    def test_the_lateral_lies_over_the_drains(self):
        """The drains are COVER under the slab and the lateral is in the aggregate: crossing the
           collector in plan is not a conflict. At 300's 12-inch cover the 2-inch drains would be."""
        from src import radon as r, drainage as d
        from lib.model import runs as runs
        self.assertFalse([w for w in r._below_slab(d.BUILDING_2) if 'DRAIN' in w[0]])
        self.assertTrue(any(runs.crossing(a, b, p, q) is not None for run in d.BUILDING_2.runs
                            for p, q in zip(run.path, run.path[1:])
                            for a, b in zip(r.RISERS[1].laterals[0].path, r.RISERS[1].laterals[0].path[1:])))

    def test_a_roof_exit_on_the_ridge_fails(self):
        from src import radon as r
        on = r.RISERS[0]._replace(exit=(10.0, r.RISERS[0].exit[1]))
        self.assertTrue(any('off the ridge' in v for v in r.radon_violations([on, r.RISERS[1]])))

    def test_the_roof_carries_the_exits(self):
        from src import roof
        names = [nm for rf in roof.ROOFS for _x, _y, nm in roof.penetrations(rf)]
        self.assertIn('RR-1 RADON VENT', names); self.assertIn('RR-2 RADON VENT', names)

    def test_each_riser_has_its_attic_junction_box_within_reach(self):
        from src import radon as r, electrical as e
        self.assertEqual([d.kind for lv in (e.LEVEL_U1_L2, e.LEVEL_U3) for d in lv.devices if d.kind == 'jbox'], ['jbox', 'jbox'])
        self.assertFalse([d for lv in (e.LEVEL_U1_L1, e.LEVEL_U2) for d in lv.devices if d.kind == 'jbox'])
        box = next(d for d in e.LEVEL_U3.devices if d.kind == 'jbox')
        i = e.LEVEL_U3.devices.index(box)
        e.LEVEL_U3.devices[i] = box._replace(x=18.0, y=30.0)
        try:
            self.assertTrue(any('junction box' in v for v in r.radon_violations()))
        finally:
            e.LEVEL_U3.devices[i] = box

    def test_the_notes_carry_no_300_vocabulary(self):
        from src import radon as r
        from src.sheets.a601 import FB
        text = ' '.join(r.notes_text(FB))
        for stale in ('W4', 'SAGE', 'ELM', 'A-001 NOTE 4a', 'UNITS 4'):
            self.assertNotIn(stale, text)


if __name__ == '__main__':
    unittest.main()
