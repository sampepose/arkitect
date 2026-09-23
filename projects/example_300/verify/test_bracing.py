"""The wall-bracing model: what S-104 draws, checked against the plans it is derived from."""
import os
import sys
import unittest
from arkitect.codes.ohio.rco import bracing as bracing_shared

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class WallRunTests(unittest.TestCase):

    def test_every_exterior_wall_of_both_levels_is_a_run(self):
        from src import bracing as b
        runs = b.wall_runs()
        self.assertEqual(len(runs), 16)
        for building, front in (('BUILDING 1', 'S ELM WALL'), ('BUILDING 2', 'COURTYARD WALL')):
            for level in (1, 2):
                names = sorted(r.name for r in runs if r.building == building and r.level == level)
                self.assertEqual(names, sorted([front, 'REAR WALL', 'SAGE WALL', 'ADJACENT-PARCEL WALL']))

    def test_the_openings_are_the_header_schedules_exterior_openings(self):
        """The same openings, level for level and wall for wall, as src/framing.py
           schedules headers over — counted, and each width matched."""
        from src import bracing as b
        from src.framing import _openings
        want = {}
        for building, level, wall, unit, kind, width, key, raw in _openings():
            if kind != 'BEARING':
                want.setdefault((building, level, wall), []).append(round(width, 6))
        got = {(r.building, r.level, r.name): sorted(round(o.b-o.a, 6) for o in r.openings)
               for r in b.wall_runs() if r.openings}
        self.assertEqual(got, {k: sorted(v) for k, v in want.items()})

    def test_openings_stay_inside_their_wall_and_do_not_overlap(self):
        from src import bracing as b
        for r in b.wall_runs():
            last = 0.0
            for o in r.openings:
                self.assertGreaterEqual(o.a, last-1e-9, r)
                self.assertLessEqual(o.b, r.length+1e-9, r)
                last = o.b

    def test_opening_heights_are_the_window_marks_and_d1(self):
        from src import bracing as b
        from src.openings import WIN_GEOM
        for r in b.wall_runs():
            for o in r.openings:
                if o.mark == 'D-1':
                    self.assertAlmostEqual(o.height, 6.0+8.0/12.0)
                else:
                    self.assertAlmostEqual(o.height, WIN_GEOM[o.mark[2:]][1])

    def test_unit_1s_entry_is_on_the_s_wayne_wall_at_level_1_only(self):
        from src import bracing as b
        from src.building1 import ENTRY_LEFT
        runs = {(r.building, r.level, r.name): r for r in b.wall_runs()}
        l1 = [o for o in runs[('BUILDING 1', 1, 'S ELM WALL')].openings if o.mark == 'D-1']
        self.assertEqual(len(l1), 1); self.assertAlmostEqual(l1[0].a, ENTRY_LEFT)
        self.assertFalse(any(o.mark == 'D-1' for o in runs[('BUILDING 1', 2, 'S ELM WALL')].openings))









class LineTests(unittest.TestCase):

    def _run(self, length, openings, o='x', at=0.0):
        from src import bracing as b
        return b.WallRun('T', 1, 'S ELM WALL', o, at, length, tuple(b.Opening(a, a+w, h, m) for a, w, h, m in openings))

    def test_the_real_lines_pass_and_there_are_sixteen(self):
        from src import bracing as b
        self.assertEqual(len(b.LINES), 16)
        self.assertEqual(b.bracing_violations(b.LINES), [])
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()) as out:
            b.check_bracing()
        self.assertEqual(out.getvalue().count('\nBRACING ')+out.getvalue().startswith('BRACING '), 17)

    def test_required_length_is_the_interpolated_row_times_the_factors(self):
        from src import bracing as b
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        from src import levels
        from src.roof import HEEL_NOM
        ln = [l for l in b.LINES if l.building == 'BUILDING 1' and l.level == 1 and l.tag == '1'][0]
        etr = 13.0*levels.ROOF_PITCH+HEEL_NOM          # the heel counted once
        self.assertAlmostEqual(b.eave_to_ridge(26.0), etr)
        want = 13.5*1.00*(0.85+(etr-5.0)/5.0*0.15)*1.00*1.00
        self.assertAlmostEqual(ln.required, want)
        top = [l for l in b.LINES if l.building == 'BUILDING 2' and l.level == 2 and l.tag == 'A'][0]
        self.assertAlmostEqual(top.base, 4.1)
        self.assertEqual(top.story, rco_bracing.ROOF_ONLY)

    def test_a_segment_short_of_the_table_is_not_a_panel(self):
        from src import bracing as b
        # 9 ft wall beside a 72" W-A: 27" minimum. 24" at the corner is not a panel,
        # 2'-4-3/4" between the windows is, 7-1/4" at the far corner is not.
        run = self._run(10.0, [(2.0, 3.0, 6.0, 'W-A'), (7.4, 2.0, 6.0, 'W-A')])
        self.assertEqual([(p.a, p.b) for p in b.panels(run, 9.0)], [(5.0, 7.4)])
        self.assertEqual([(p.a, p.b) for p in b.panels(self._run(10.0, [(2.0, 3.0, 6.0, 'W-A')]), 9.0)], [(5.0, 10.0)])

    def test_a_long_line_with_one_panel_fails_and_a_door_side_portal_rescues_it(self):
        from src import bracing as b
        run = self._run(26.0, [(17.0, 3.0, 6.0, 'W-A'), (21.0, 3.0, 6.0+8/12.0, 'D-1')])
        ps = b.panels(run, 8.95)
        self.assertTrue(any('1 braced wall panel' in x for x in b.location_violations(26.0, ps)))
        pf = b.panels(run, 8.95, portal=True)
        self.assertEqual([p.method for p in pf], ['CS-WSP', 'CS-PF'])
        self.assertAlmostEqual(pf[1].credit, 1.5*2.0)
        self.assertEqual(b.location_violations(26.0, pf), [])

    def test_the_ten_and_twenty_foot_rules(self):
        from src import bracing as b
        P = b.Panel
        self.assertTrue(any('first panel' in x for x in b.location_violations(40.0, [P(11.0, 14.0, 'CS-WSP', 2, 3), P(30.0, 40.0, 'CS-WSP', 2, 10)])))
        self.assertTrue(any('between the panels' in x for x in b.location_violations(40.0, [P(0.0, 3.0, 'CS-WSP', 2, 3), P(24.0, 40.0, 'CS-WSP', 2, 16)])))
        self.assertEqual(b.location_violations(12.0, [P(0.0, 4.0, 'CS-WSP', 2, 4)]), [])       # one 48" panel on a short line

    def test_end_conditions_in_order(self):
        from src import bracing as b
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        from arkitect.lib.units import IN
        run = self._run(20.0, [(3.0, 3.0, 6.0, 'W-A'), (15.0, 3.0, 6.0, 'W-A')])
        ps = b.panels(run, 9.0)
        self.assertEqual(rco_bracing.end_condition(run, 'lo', ps, IN(24)).condition, 1)
        self.assertEqual(rco_bracing.end_condition(run, 'lo', ps, IN(12)), rco_bracing.End('lo', 2, 0.0))
        wide = self._run(20.0, [(5.0, 3.0, 6.0, 'W-A')])
        self.assertEqual(rco_bracing.end_condition(wide, 'lo', b.panels(wide, 9.0), IN(12)).condition, 3)
        near = self._run(20.0, [(0.5, 3.0, 6.0, 'W-A'), (8.0, 3.0, 6.0, 'W-A')])
        pn = b.panels(near, 9.0)
        self.assertEqual(rco_bracing.end_condition(near, 'lo', pn, IN(24)), rco_bracing.End('lo', 5, 3.5))           # 6" to the corner: no D
        d24 = self._run(20.0, [(2.0, 3.0, 6.0, 'W-A'), (8.0, 3.0, 6.0, 'W-A')])
        self.assertEqual(rco_bracing.end_condition(d24, 'lo', b.panels(d24, 9.0), IN(24)).condition, 4)
        far = self._run(30.0, [(0.5, 11.0, 6.0, 'W-A')])
        self.assertIsNone(rco_bracing.end_condition(far, 'lo', b.panels(far, 9.0), IN(24)).condition)

    def test_unit_1s_front_wall_takes_a_hold_down_at_the_safford_corner(self):
        from src import bracing as b
        ln = [l for l in b.LINES if l.building == 'BUILDING 1' and l.level == 1 and l.tag == '1'][0]
        self.assertEqual(ln.ends[0].condition, 5)
        self.assertAlmostEqual(ln.ends[0].hold_down, ln.panels[0].a)

    def test_building_2s_courtyard_wall_has_its_portal_at_the_parcel_corner(self):
        """Level 1 only. Unit 5's kitchen W-C (the designer, 2026-09-16) splits Level 2's long
           panel in two, and that line no longer needs the portal beside its door."""
        from src import bracing as b
        by = {l.level: l for l in b.LINES if l.building == 'BUILDING 2' and l.tag == '1'}
        self.assertEqual([p.method for p in by[1].panels], ['CS-WSP', 'CS-PF'])
        self.assertAlmostEqual(by[1].panels[-1].b, 26.0)
        self.assertEqual([p.method for p in by[2].panels], ['CS-WSP', 'CS-WSP'])

    def test_connections_follow_the_joists_and_the_trusses(self):
        from src import bracing as b
        by = {(l.building, l.level, l.tag): l for l in b.LINES}
        self.assertEqual(b.floor_connection(by[('BUILDING 1', 1, 'A')]), 1)   # joists cross the side walls
        self.assertEqual(b.floor_connection(by[('BUILDING 1', 1, '1')]), 2)
        self.assertEqual(b.floor_connection(by[('BUILDING 2', 1, 'A')]), 2)   # joists run front to back
        self.assertEqual(b.floor_connection(by[('BUILDING 2', 1, '1')]), 1)
        self.assertTrue(b.truss_perpendicular(by[('BUILDING 2', 2, 'B')]))
        self.assertFalse(b.truss_perpendicular(by[('BUILDING 1', 2, '2')]))
        self.assertEqual(bracing_shared.roof_connection(heel_nom=b.HEEL_NOM), 'ITEM 3')

    def test_a_short_line_and_a_nail_that_does_not_reach_fail(self):
        from src import bracing as b
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        ln = [l for l in b.LINES if l.building == 'BUILDING 1' and l.level == 1 and l.tag == '1'][0]
        short = ln._replace(panels=ln.panels[:1], required=50.0)
        v = b.bracing_violations([short])
        self.assertTrue(any('of bracing where' in x for x in v), v)
        self.assertTrue(any('not two braced wall lines' in x for x in v), v)
        old = rco_bracing.NAIL_LENGTH[rco_bracing.NAIL_W1R]
        try:
            rco_bracing.NAIL_LENGTH[rco_bracing.NAIL_W1R] = 2.5/12.0
            self.assertTrue(any('penetrates' in x for x in b.bracing_violations(b.LINES)))
        finally:
            rco_bracing.NAIL_LENGTH[rco_bracing.NAIL_W1R] = old


class PortalTests(unittest.TestCase):



    def test_the_real_portals_stand_beside_building_2s_courtyard_doors(self):
        from src import bracing as b
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        pf = [(ln, p, o) for ln in b.LINES for p, o in b.portal_openings(ln)]
        self.assertEqual(sorted((ln.building, ln.level, ln.tag) for ln, p, o in pf), [('BUILDING 2', 1, '1')])
        for ln, p, o in pf:
            self.assertEqual(o.mark, 'D-1'); self.assertAlmostEqual(o.b, p.a)
            h = b.schedule_header(ln, o)
            self.assertIsNotNone(h)
            self.assertLessEqual(rco_bracing.header_depth(h.size), rco_bracing.PORTAL_HEADER[1])

    def test_header_depths(self):
        from arkitect.codes.ohio.rco import bracing as rco_bracing
        from arkitect.lib.units import IN
        self.assertAlmostEqual(rco_bracing.header_depth('2-2x6'), IN(5.5))
        self.assertAlmostEqual(rco_bracing.header_depth('3-2x12'), IN(11.25))
        self.assertEqual(rco_bracing.header_depth('PER 602.7.4'), 0.0)

    def test_a_portal_beside_nothing_or_too_many_fail(self):
        from src import bracing as b
        ln = [l for l in b.LINES if l.building == 'BUILDING 2' and l.level == 1 and l.tag == '1'][0]
        lone = ln._replace(openings=tuple(o for o in ln.openings if o.mark != 'D-1'))
        self.assertTrue(any('beside no D-1' in x for x in b.bracing_violations([lone])))
        pf = ln.panels[-1]
        many = ln._replace(panels=ln.panels+tuple(pf for _ in range(4)))
        self.assertTrue(any('over the 4 of 602.10.6.4' in x for x in b.bracing_violations([many])))


if __name__ == '__main__':
    unittest.main()
