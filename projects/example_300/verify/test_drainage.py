"""The drainage model: what P-101 draws, checked against the fixtures it is derived
from, the strips it must clear and the water it must keep off, and the OPC tables it
sizes by, pinned to their text."""
import os
import sys
import unittest
from arkitect.codes.ohio import opc_drainage as opc_drainage_shared

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from arkitect.codes.ohio import opc_separation


class TallyTests(unittest.TestCase):


    def test_every_below_slab_fixture_has_its_own_dry_vent(self):
        """A stack that carries the level above is not a vent for the level below: 912 wet
           vents one floor and 913 takes no water closet, and B, C and D each carry one.
           Vent A and the laundry's dry vent were always right; the other four are new."""
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        self.assertEqual(d.vent_violations(), [])
        self.assertEqual(sorted(v.mark for v in d.DRY_VENTS),
                         ['V-A', 'V-B', 'V-C', 'V-D', 'V-K', 'V-L'])
        for dv in d.DRY_VENTS:
            self.assertNotEqual(dv.at_fixture, 'wc')        # never at the closet
        for _b, a in d.trap_arms():
            self.assertLessEqual(a.length, V.trap_arm_max(a.size), a.name)
        self.assertTrue(V.trap_arm_violations([V.Arm('X', 1.5, 6.4)]))

    def test_the_ties_clear_every_rim_on_their_stack(self):
        """905.4. Stack C carries a Level 2 kitchen sink, whose rim is the highest here."""
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        self.assertEqual(V.dry_vent_rise_violations(d.vent_ties()), [])
        low = [(m, rim+0.2, rim) for m, _t, rim in d.vent_ties()]
        self.assertEqual(len(V.dry_vent_rise_violations(low)), len(low))

    def test_stacks_e_and_f_are_913_waste_stack_vents(self):
        """Claimed on P-601 note 1w, so the load is checked: E sits exactly on Table 913.4's
           2 DFU at a branch interval and 4 in all for a 2" stack."""
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        rows = {r[0]: r for r in d.waste_stacks()}
        self.assertEqual(sorted(rows), ['E', 'F'])
        self.assertEqual(V.waste_stack_violations(d.waste_stacks()), [])
        for name in rows:
            _n, size, wc, by, total, offset = rows[name]
            self.assertFalse(wc); self.assertFalse(offset)
            per, cap = V.WASTE_STACK[size]
            self.assertLessEqual(total, cap)
            if per is not None:
                self.assertLessEqual(max(by), per)

    def test_the_real_units(self):
        from src import drainage as d
        b1, b2 = d.BUILDINGS
        self.assertEqual(d.unit_names(b1), ['UNIT 1', 'UNIT 2', 'UNIT 3'])
        self.assertEqual(opc_drainage_shared.unit_dfu(d._pm(b1), 'UNIT 1')[0], 14)
        self.assertEqual(opc_drainage_shared.unit_dfu(d._pm(b1), 'UNIT 2')[0], 9); self.assertEqual(opc_drainage_shared.unit_dfu(d._pm(b1), 'UNIT 3')[0], 9)
        self.assertEqual(opc_drainage_shared.unit_dfu(d._pm(b2), 'UNIT 4')[0], 9); self.assertEqual(opc_drainage_shared.unit_dfu(d._pm(b2), 'UNIT 5')[0], 9)
        self.assertEqual(d.building_dfu(b1), 32); self.assertEqual(d.building_dfu(b2), 18)
        self.assertEqual(d.total_dfu(), 50)
        rows = opc_drainage_shared.unit_dfu(d._pm(b1), 'UNIT 1')[1]
        self.assertEqual(rows[0], ('BATHROOM GROUP, 1.6 GPF WC', 2, 10))
        self.assertIn(('KITCHEN SINK WITH DISHWASHER', 1, 2), rows)
        self.assertIn(('KITCHEN SINK, DOMESTIC', 1, 2), opc_drainage_shared.unit_dfu(d._pm(b2), 'UNIT 4')[1])   # no dishwasher there

    def test_the_stacks_and_the_drains(self):
        """Pipes carry the fixtures on them, gathered by dwelling and level before the
           group value applies: a bathroom split between a stack and slab branches is
           one group again wherever a pipe carries all of it, so each building drain
           carries exactly its building's tally."""
        from src import drainage as d
        from arkitect.codes.ohio import opc_drainage as opc_drainage
        from arkitect.lib.model import drains as drains
        b1, b2 = d.BUILDINGS
        self.assertEqual({s.name: opc_drainage.stack_dfu(s) for s in b1.stacks}, {'A': 0, 'B': 6, 'C': 8, 'E': 4})
        self.assertEqual({s.name: opc_drainage.stack_dfu(s) for s in b2.stacks}, {'D': 6, 'F': 8})
        self.assertEqual(opc_drainage.run_dfu(b1, drains.exit_run(b1)), 32)
        self.assertEqual(opc_drainage.run_dfu(b2, drains.exit_run(b2)), 18)
        self.assertEqual(opc_drainage.run_dfu(b1, drains.exit_run(b1)), d.building_dfu(b1))
        self.assertEqual(opc_drainage.run_dfu(b2, drains.exit_run(b2)), d.building_dfu(b2))
        # Unit 2's bathroom whole (wc, tub arm, stack C's level-1 lavatory) plus Unit 3's level 2
        self.assertEqual(opc_drainage.run_dfu(b1, b1.runs[5]), 12)
        # a part of a group still counts singly: the tub and stack B's level-1 lavatory
        self.assertEqual(opc_drainage.run_dfu(b1, b1.runs[2]), 8)
        self.assertEqual(opc_drainage.run_dfu(b1, b1.runs[1]), 5)            # Unit 1's water closet and kitchen sink
        # Unit 4's bathroom whole plus Unit 5's group on stack D
        self.assertEqual(opc_drainage.run_dfu(b2, b2.runs[0]), 10)
        self.assertEqual(drains.exit_run(b1).size, '4'); self.assertEqual(drains.exit_run(b2).size, '4')
        self.assertIsNone(drains.stack_by_name(b1, 'A').foot)            # a vent only


class GeometryTests(unittest.TestCase):



    def test_the_real_crossings(self):
        """The Building 1 trunk crosses the Units 2/3 water trunk on the rear wall; the
           stack F branch crosses the Building 2 service; each trunk passes below one
           strip, at a right angle."""
        from src import drainage as d
        b1, b2 = d.BUILDINGS
        self.assertEqual([x for _r, x in opc_separation.crossings(b1, d.GROUND)], [(6.0, 46.95)])
        self.assertEqual([x for _r, x in opc_separation.crossings(b2, d.GROUND)], [(1.5, 12.2)])
        self.assertEqual([nm for _r, nm, _x in opc_separation.strip_crossings(b1, d.GROUND)], ['W4'])
        self.assertEqual([nm for _r, nm, _x in opc_separation.strip_crossings(b2, d.GROUND)], ['UNITS 4 AND 5 BEARING WALL'])

    def test_the_crossings_meet_603_2(self):
        """Building 1's Units 2/3 trunk passes above its building drain, in the gravel under
           the slab, 12" clear of the drain's top within 5'-0". Building 2's service cannot:
           1'-6" from the stack F branch it is out through the wall and below frost, and it
           crosses the building sewer on the lot below frost. So it is sleeved, once, from
           5'-0" past that sewer, 12'-0" out from the wall, to its riser."""
        from src import drainage as d
        from arkitect.lib.model import drains as drains
        b1, b2 = d.BUILDINGS
        self.assertEqual([(nm, x, k) for _r, nm, x, k in opc_separation.water_crossings(b1, d.GROUND)], [('UNITS 2 AND 3 TRUNK', (6.0, 46.95), 'above')])
        self.assertEqual([(nm, x, k) for _r, nm, x, k in opc_separation.water_crossings(b2, d.GROUND)], [('SERVICE', (1.5, 12.2), 'sleeved')])
        r, _nm, x, _k = opc_separation.water_crossings(b1, d.GROUND)[0]
        self.assertEqual(drains.drain_name(b1, r), 'BUILDING DRAIN')
        self.assertGreaterEqual(-opc_separation.highest_top_near(b1, r, x, d.GROUND)-d.WATER_BED, opc_separation.VERT_CLEAR)
        self.assertEqual(drains.drain_name(b2, opc_separation.water_crossings(b2, d.GROUND)[0][0]), 'STACK F BRANCH')
        self.assertEqual(opc_separation.site_crossings(b1, d.GROUND), [])
        [(nm, x, top, k)] = opc_separation.site_crossings(b2, d.GROUND)
        self.assertEqual((nm, k), ('BUILDING SEWER', 'sleeved'))
        self.assertAlmostEqual(x[0], 1.0); self.assertAlmostEqual(x[1], 92.2)
        self.assertGreater(top, d.FROST_DEPTH*-1)                     # the sewer is above frost there
        out, inn = d.service_sleeve(b2)
        self.assertAlmostEqual(out, 12.0)
        self.assertAlmostEqual(inn, d._pm(b2).riser[0])               # up through the slab at the riser
        self.assertIsNone(d.service_sleeve(b1))
        self.assertGreaterEqual(d.service_to_sewer(b1), opc_separation.SEWER_SEP)
        self.assertEqual(d.drainage_violations(), [])

    def test_a_sleeve_that_reaches_the_main_stops_the_build(self):
        from unittest import mock
        from src import drainage as d, plumbing as pm
        with mock.patch.object(pm, 'MAIN_TO_WALL', 10.0):
            self.assertIn('BUILDING 2: the service sleeve reaches the main', d.drainage_violations())

    def test_penetrations_sit_in_their_fixtures(self):
        """The authored points are tied to the model's rectangles, so a tub that moves
           on A-101 moves its box-out or fails the build."""
        from src import drainage as d
        from arkitect.lib.model import runs as runs
        b1 = d.BUILDING_1
        wc1 = next(p for p in b1.pens if p.mark == 2)
        self.assertTrue(runs.in_rect(wc1.pos, (d.U1_WC.x, d.U1_WC.y, d.U1_WC.w, d.U1_WC.h)))
        tub2 = next(p for p in b1.pens if p.mark == 8)
        self.assertTrue(runs.in_rect(tub2.pos, tub2.box))
        self.assertAlmostEqual(d.STACK_E_X, 26.0-d.PLAN_L1.x(d.U23_E_RISER, 47.5))   # where S-103 puts its vent


class InvertTests(unittest.TestCase):

    def test_cover_and_the_crown_drop(self):
        """A head has COVER over its top; where a 3" run ends at the 4" trunk's head the
           crowns line up, so the trunk starts an inch lower than that run's tail."""
        from src import drainage as d
        from arkitect.lib.model import runs as runs
        from arkitect.lib.units import IN
        b1 = d.BUILDING_1
        r1, r2, r5 = b1.runs[0], b1.runs[1], b1.runs[4]
        self.assertAlmostEqual(opc_drainage_shared.head_invert(b1, r1, cover=d.COVER), -(d.COVER+IN(2)))
        self.assertAlmostEqual(opc_drainage_shared.head_invert(b1, r2, cover=d.COVER), opc_drainage_shared.tail_invert(b1, r1, cover=d.COVER)-IN(1))
        self.assertAlmostEqual(opc_drainage_shared.head_invert(b1, r5, cover=d.COVER), opc_drainage_shared.tail_invert(b1, r2, cover=d.COVER)-IN(1))
        self.assertLess(opc_drainage_shared.tail_invert(b1, r5, cover=d.COVER), opc_drainage_shared.head_invert(b1, r5, cover=d.COVER))
        self.assertAlmostEqual(d.fall(r1), 0.25/12.0*runs.length(r1.path))

    def test_exits_and_the_sewer(self):
        from src import drainage as d
        from arkitect.lib.model import drains as drains
        from arkitect.lib.units import IN
        b1, b2 = d.BUILDINGS
        self.assertEqual(drains.exit_site(b1), (14.0, 68.0)); self.assertEqual(drains.exit_site(b2), (8.0, 97.0))
        s = d.sewer()
        self.assertAlmostEqual(s['on_lot'], 71.0); self.assertAlmostEqual(s['to_main'], 71.0+17.5/2.0)
        self.assertAlmostEqual(s['fall'], 79.75/8.0/12.0)
        self.assertLess(s['exit1'], -IN(18)); self.assertGreater(s['exit1'], -IN(24))       # through the wall, above the footing top
        self.assertGreater(s['exit2'], s['exit1'])
        self.assertGreater(s['lateral_fall'], 0.0)
        self.assertLess(s['main_max'], s['exit1'])
        self.assertGreater(d.below_grade(opc_drainage_shared.exit_invert(b1, cover=d.COVER)), d.FOOTING_TOP)


class CheckTests(unittest.TestCase):

    def test_the_real_model_passes(self):
        from src import drainage as d
        self.assertEqual(d.drainage_violations(), [])

    def _with(self, **changes):
        from src import drainage as d
        saved = {k: getattr(d, k) for k in changes}
        try:
            for k, val in changes.items(): setattr(d, k, val)
            return d.drainage_violations()
        finally:
            for k, val in saved.items(): setattr(d, k, val)

    def _b1(self, **fields):
        from src import drainage as d
        return [d.BUILDING_1._replace(**fields), d.BUILDING_2]

    def test_a_fixture_nobody_drains_fails(self):
        from src import drainage as d
        stacks = [s._replace(serves=()) if s.name == 'E' else s for s in d.BUILDING_1.stacks]
        v = self._with(BUILDINGS=self._b1(stacks=stacks))
        self.assertTrue(any('UNIT 2 level 1 has 1 wd fixture(s) but 0 served' in x for x in v), v)

    def test_a_drain_that_disagrees_with_the_tally_fails(self):
        """A fixture served twice puts the building drain over the tally P-101 prints."""
        from src import drainage as d
        pens = [p._replace(serves=p.serves+(('UNIT 3', 2, ('sink',)),)) if p.mark == 7 else p for p in d.BUILDING_1.pens]
        v = self._with(BUILDINGS=self._b1(pens=pens))
        self.assertTrue(any('BUILDING 1: the building drain carries 34 DFU, the fixture tally is 32' in x for x in v), v)

    def test_a_penetration_in_a_strip_fails(self):
        from src import drainage as d
        pens = [p._replace(pos=(6.0, 23.8)) if p.mark == 6 else p for p in d.BUILDING_1.pens]
        v = self._with(BUILDINGS=self._b1(pens=pens))
        self.assertTrue(any('penetration 6 is within 6" of the W4 strip' in x for x in v), v)

    def test_a_penetration_away_from_its_fixture_fails(self):
        from src import drainage as d
        pens = [p._replace(pos=(20.0, 17.5)) if p.mark == 2 else p for p in d.BUILDING_1.pens]
        runs = [r._replace(path=[(20.0, 17.5), d.CO1]) if i == 1 else r for i, r in enumerate(d.BUILDING_1.runs)]
        v = self._with(BUILDINGS=self._b1(pens=pens, runs=runs))
        self.assertTrue(any('penetration 2 is not at the UNIT 1 wc' in x for x in v), v)

    def test_a_water_closet_on_a_two_inch_run_fails(self):
        from src import drainage as d
        runs = [r._replace(size='2') if i == 1 else r for i, r in enumerate(d.BUILDING_1.runs)]
        v = self._with(BUILDINGS=self._b1(runs=runs))
        self.assertTrue(any('run 2 (2")' in x and 'carries a water closet' in x for x in v), v)

    def test_a_run_along_the_water_fails(self):
        from src import drainage as d
        runs = [r._replace(path=[d.E_FOOT, (d.E_FOOT[0], 46.5), (d.TRUNK_X, 46.5)]) if i == 8 else r
                for i, r in enumerate(d.BUILDING_1.runs)]
        v = self._with(BUILDINGS=self._b1(runs=runs))
        self.assertTrue(any('parallel to the water below the slab' in x for x in v), v)

    def test_a_run_along_a_strip_fails(self):
        from src import drainage as d
        runs = [r._replace(path=[(4.9, d.WC1[1]), (4.9, 48.0)]) if i == 4 else r for i, r in enumerate(d.BUILDING_1.runs)]
        pens = [p._replace(pos=(4.9, 48.0)) if p.kind == 'exit' else p for p in d.BUILDING_1.pens]
        v = self._with(BUILDINGS=self._b1(runs=runs, pens=pens))
        self.assertTrue(any('UNIT 1 STAIR WALL strip' in x for x in v), v)

    def test_an_exit_off_the_wall_fails(self):
        from src import drainage as d
        pens = [p._replace(pos=(6.0, 47.0)) if p.kind == 'exit' else p for p in d.BUILDING_1.pens]
        runs = [r._replace(path=[d.CO1, (6.0, 47.0)]) if i == 4 else r for i, r in enumerate(d.BUILDING_1.runs)]
        v = self._with(BUILDINGS=self._b1(pens=pens, runs=runs))
        self.assertTrue(any('not on an outside face' in x for x in v), v)

    def test_a_branch_entering_below_its_drain_fails(self):
        """A long shallow-sloped branch dropping into a trunk near the trunk's head."""
        from src import drainage as d
        from arkitect.lib.model import drains as drains
        # the laundry standpipe run rerouted as a 2" of 40 ft into the trunk 1 ft from its head
        long = drains.Run('2', [d.CW1, (d.CW1[0], 2.0), (5.0, 2.0), (5.0, 18.5), (d.TRUNK_X, 18.5)])
        runs = [long if i == 3 else r for i, r in enumerate(d.BUILDING_1.runs)]
        v = self._with(BUILDINGS=self._b1(runs=runs))
        self.assertTrue(any('enters it below its invert' in x for x in v), v)

    def test_a_tail_on_nothing_fails(self):
        from src import drainage as d
        runs = [r._replace(path=[d.KS2, (5.0, d.KS2[1])]) if i == 7 else r for i, r in enumerate(d.BUILDING_1.runs)]
        v = self._with(BUILDINGS=self._b1(runs=runs))
        self.assertTrue(any('run 8' in x and 'on no run' in x for x in v), v)

    def test_a_stack_over_its_table_fails(self):
        from src import drainage as d
        stacks = [s._replace(size='2') if s.name == 'C' else s for s in d.BUILDING_1.stacks]
        pens = [p._replace(size='2') if p.mark == 10 else p for p in d.BUILDING_1.pens]
        v = self._with(BUILDINGS=self._b1(stacks=stacks, pens=pens))
        self.assertTrue(any('stack C carries a water closet at 2"' in x for x in v), v)
        self.assertTrue(any('stack C UNIT 3 level 2 puts 7 DFU into one branch interval' in x for x in v), v)



class StackAtAnOpeningTests(unittest.TestCase):
    """Vent A rose in the parcel wall behind Unit 1's sink — through the W-B over it and the W-A
       above that. Found 2026-09-18 by the check 400 Oak's Stack E taught."""

    def test_no_stack_stands_where_an_opening_is(self):
        from src import drainage as d
        self.assertEqual(d.stack_violations(), [])

    def test_vent_a_stands_past_the_windows_within_a_trap_arm_of_the_sink(self):
        from src import drainage as d
        from arkitect.lib.model import drains as drains
        a = drains.stack_by_name(d.BUILDING_1, 'A')
        self.assertGreater(a.pos[1], max(w[1]+w[2] for w in d._A_WINS))
        self.assertLess(abs(a.pos[1]-d.KS1[1]), 8.0)              # a 2" trap arm reaches 8'-0"

    def test_a_laundry_stack_on_the_dryer_duct_fails(self):
        from src import drainage as d, mechanical as M
        self.assertEqual(d.laundry_violations(), [])
        t = next(t for ts in M.TERMS[2].values() for t in ts if t.what == 'DRYER EXHAUST')
        keep = d.BUILDING_2.stacks[1]
        d.BUILDING_2.stacks[1] = keep._replace(pos=(keep.pos[0], t.along+0.1))
        try:
            self.assertTrue(any('dryer duct' in v for v in d.laundry_violations()))
        finally:
            d.BUILDING_2.stacks[1] = keep

    def test_vent_a_put_back_behind_the_sink_fails(self):
        from src import drainage as d
        keep = d.BUILDING_1.stacks[0]
        d.BUILDING_1.stacks[0] = keep._replace(pos=(keep.pos[0], d.KS1[1]))
        try:
            bad = d.stack_violations()
            self.assertTrue(any('L1 W-B' in v for v in bad) and any('L2 W-A' in v for v in bad), bad)
        finally:
            d.BUILDING_1.stacks[0] = keep


if __name__ == '__main__':
    unittest.main(verbosity=2)
