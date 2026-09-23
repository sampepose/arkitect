"""The water supply model: what P-102 and P-103 draw, checked against the plans it is
derived from, and the two IPC tables it sizes by, pinned to their text."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class TableTests(unittest.TestCase):

    def test_the_home_run_and_heater_connection_sizes(self):
        from src import plumbing as p
        self.assertEqual(p.HOME_RUN, '1/2'); self.assertEqual(p.HEATER_CONN, '3/4')

    def test_pipe_for_reads_the_right_column_and_row(self):
        from src import plumbing as p
        self.assertEqual(p.pipe_for(9.5, 80, pressure='50 TO 60'), ('3/4', '3/4'))
        self.assertEqual(p.pipe_for(9.6, 80, pressure='50 TO 60'), ('3/4', '1'))
        self.assertEqual(p.pipe_for(27.0, 121, pressure='50 TO 60'), ('1', '1'))     # 150 ft column: 3/4 / 1 gives 25
        self.assertEqual(p.pipe_for(27.0, 100, pressure='50 TO 60'), ('3/4', '1'))
        self.assertEqual(p.pipe_for(7.8, 121, meter='1', pressure='50 TO 60'), ('1', '1'))
        self.assertEqual(p.pipe_for(6.4, 82, meter='3/4', pressure='50 TO 60'), ('3/4', '3/4'))
        with self.assertRaises(ValueError):
            p.pipe_for(100.0, 40)
        with self.assertRaises(ValueError):
            p.pipe_for(1.0, 600)


class TallyTests(unittest.TestCase):

    def test_a_bath_is_a_group_and_the_rest_are_single(self):
        from src import plumbing as p
        F = p.Fixture
        fx = [F(0, 0, 1, 1, 'wc'), F(0, 0, 1, 1, 'lav'), F(0, 0, 1, 1, 'tub'), F(0, 0, 1, 1, 'sink'),
              F(0, 0, 1, 1, 'dw'), F(0, 0, 1, 1, 'wd'), F(0, 0, 1, 1, 'wh')]
        c, h, t, rows = p.tally(fx)
        self.assertAlmostEqual(t, 3.6+1.4+1.4+1.4); self.assertAlmostEqual(c, 2.7+1+0+1); self.assertAlmostEqual(h, 1.5+1+1.4+1)
        self.assertEqual(rows[0][:2], ('BATHROOM GROUP, FLUSH TANK WC', 1))
        self.assertEqual(sum(r[1] for r in rows), 4)
        c2, h2, t2, rows2 = p.tally(fx[:2])                              # no tub: no group
        self.assertAlmostEqual(t2, 2.2+0.7); self.assertEqual(len(rows2), 2)

    def test_the_real_units(self):
        from src import plumbing as p
        from arkitect.lib.model import water as water
        b1, b2 = p.BUILDINGS
        self.assertEqual(water.unit_names(b1), ['UNIT 1', 'UNIT 2', 'UNIT 3']); self.assertEqual(water.unit_names(b2), ['UNIT 4', 'UNIT 5'])
        self.assertAlmostEqual(p.unit_wsfu(b1, 'UNIT 1')[2], 11.4)
        self.assertAlmostEqual(p.unit_wsfu(b1, 'UNIT 2')[2], 7.8); self.assertAlmostEqual(p.unit_wsfu(b1, 'UNIT 3')[2], 7.8)
        self.assertAlmostEqual(p.unit_wsfu(b2, 'UNIT 4')[2], 6.4)
        self.assertAlmostEqual(p.sizes(b1)['total'], 27.0); self.assertAlmostEqual(p.sizes(b2)['total'], 12.8)
        # Units 2 and 3 have no dishwasher-less kitchen and Units 4 and 5 no dishwasher, as P-601 has them
        self.assertEqual([f.kind for f in b1.units[2].fixtures].count('dw'), 1)
        self.assertEqual([f.kind for f in b2.units[0].fixtures].count('dw'), 0)


class GeometryTests(unittest.TestCase):

    def test_fixtures_are_the_rectangles_the_plans_draw(self):
        """Units 2/3's and 4/5's fixtures go through the same regrid and mirror as their
           symbols; Unit 1's are the electrical model's rectangles."""
        from src import plumbing as p
        from src.building1 import PLAN_L1, F_U23
        from src.electrical import LEVEL_U1_L1
        tub = next(f for f in F_U23 if f[4] == 'tub')
        r = PLAN_L1.rect(tub)
        mine = next(f for f in p.BUILDING_1.units[2].fixtures if f.kind == 'tub')
        self.assertAlmostEqual(mine.x, 26.0-(r[0]+r[2])); self.assertAlmostEqual(mine.y, r[1])
        self.assertAlmostEqual(mine.w, r[2]); self.assertAlmostEqual(mine.h, r[3])
        lav = next(f for f in p.U1_L1_FIXTURES if f.kind == 'lav')
        self.assertEqual(tuple(round(v, 6) for v in lav[:4]), tuple(round(v, 6) for v in LEVEL_U1_L1.lavs[0][:4]))

    def test_stub_leaves_the_run_at_the_nearest_point(self):
        from src import plumbing as p
        from arkitect.lib.model import water as water
        r = p.Run('T', ('lav',), [(0.0, 0.0), (0.0, 10.0)])
        q, e = water.stub(r, p.Fixture(2.0, 4.0, 2.0, 1.0, 'lav'))
        self.assertEqual(q, (0.0, 4.5)); self.assertEqual(e, (2.0, 4.5))
        q, e, i = water.stub(p.Run('T', ('lav',), [(0.0, 0.0), (0.0, 10.0), (10.0, 10.0)]), p.Fixture(8.0, 11.0, 1.0, 1.0, 'lav'), where=True)
        self.assertEqual(i, 1); self.assertEqual(q, (8.5, 10.0)); self.assertEqual(e, (8.5, 11.0))

    def test_run_lines(self):
        from src import plumbing as p
        from arkitect.lib.model import water as water
        u = p.BUILDING_1.units[2]
        bath = next(r for r in u.runs if r.group == 'BATH')
        self.assertEqual(water.run_lines(bath, u.fixtures), (3, 2))
        self.assertEqual(water.run_lines(next(r for r in u.runs if r.group == 'HEATER'), u.fixtures), (1, 1))
        self.assertEqual(water.run_lines(next(r for r in u.runs if r.group == 'KITCHEN'), u.fixtures), (2, 2))

    def test_developed_lengths_include_the_assumed_main_and_the_rise(self):
        from src import plumbing as p
        from src import levels
        b1 = p.BUILDING_1
        self.assertGreater(p.developed_length(b1, 'UNIT 2'), p.MAIN_TO_WALL+29.0)
        self.assertAlmostEqual(p.developed_length(b1, 'UNIT 3')-p.developed_length(b1, 'UNIT 2'), levels.FLOOR_RISE)
        self.assertEqual(p.building_length(b1), p.developed_length(b1, 'UNIT 3'))


class CheckTests(unittest.TestCase):

    def test_the_real_model_passes(self):
        from src import plumbing as p
        self.assertEqual(p.plumbing_violations(), [])
        self.assertEqual(p.sizes(p.BUILDING_1)['service'], '1'); self.assertEqual(p.sizes(p.BUILDING_1)['meter'], '1')
        self.assertEqual(p.sizes(p.BUILDING_2)['service'], '1'); self.assertEqual(p.sizes(p.BUILDING_2)['meter'], '3/4')

    def _with(self, **changes):
        """A copy of the model with some names rebound, and its violations."""
        from src import plumbing as p
        saved = {k: getattr(p, k) for k in changes}
        try:
            for k, val in changes.items(): setattr(p, k, val)
            return p.plumbing_violations()
        finally:
            for k, val in saved.items(): setattr(p, k, val)

    def test_a_fixture_no_run_reaches_fails(self):
        from src import plumbing as p
        u = p.BUILDING_1.units[2]
        short = [r for r in u.runs if r.group != 'LAUNDRY']
        b = p.BUILDING_1._replace(units=[u._replace(runs=short) if x is u else x for x in p.BUILDING_1.units])
        v = self._with(BUILDINGS=[b, p.BUILDING_2])
        self.assertTrue(any('wd fixture(s) but 0 reached' in x for x in v), v)

    def test_a_manifold_outside_its_closet_fails(self):
        from src import plumbing as p
        u = p.BUILDING_2.units[0]
        b = p.BUILDING_2._replace(units=[u._replace(manifold=(10.0, 10.0, 0.3, 1.0))]+p.BUILDING_2.units[1:])
        v = self._with(BUILDINGS=[p.BUILDING_1, b])
        self.assertTrue(any('outside the mechanical closet' in x for x in v), v)

    def test_a_trunk_through_w4_above_the_slab_fails(self):
        from src import plumbing as p
        tr = [(names, path, False) for names, path, _u in p.BUILDING_1.trunks]
        v = self._with(BUILDINGS=[p.BUILDING_1._replace(trunks=tr), p.BUILDING_2])
        self.assertTrue(any('crosses W4 above the slab' in x for x in v), v)

    def test_a_unit_fed_by_no_trunk_fails(self):
        from src import plumbing as p
        v = self._with(BUILDINGS=[p.BUILDING_1._replace(trunks=p.BUILDING_1.trunks[:1]), p.BUILDING_2])
        self.assertTrue(any('0 trunks to UNIT 2' in x for x in v), v)

    def test_a_level_2_unit_with_no_riser_fails(self):
        from src import plumbing as p
        u = p.BUILDING_2.units[1]
        b = p.BUILDING_2._replace(units=[p.BUILDING_2.units[0], u._replace(riser=None)])
        v = self._with(BUILDINGS=[p.BUILDING_1, b])
        self.assertTrue(any('no riser' in x for x in v), v)

    def test_a_run_through_w4_fails(self):
        from src import plumbing as p
        u = p.BUILDING_1.units[2]
        bad = [r._replace(path=[(11.9, 47.15), (11.9, 20.0)]) if r.group == 'BATH' else r for r in u.runs]
        b = p.BUILDING_1._replace(units=[u._replace(runs=bad) if x is u else x for x in p.BUILDING_1.units])
        v = self._with(BUILDINGS=[b, p.BUILDING_2])
        self.assertTrue(any('crosses the W4 separation' in x for x in v), v)

    def test_a_service_off_the_safford_wall_fails(self):
        from src import plumbing as p
        v = self._with(BUILDINGS=[p.BUILDING_1, p.BUILDING_2._replace(entry=(27.0, 11.5))])
        self.assertTrue(any('Sage wall' in x for x in v), v)

    def test_a_load_off_the_table_fails_by_name(self):
        v = self._with(MAIN_TO_WALL=1000.0)
        self.assertTrue(any('off Table E201.1' in x for x in v), v)


class WorkingSpaceTests(unittest.TestCase):
    """The storage heaters against NEC 110.26(A) and RCO M1305.1. A tank stands on the
       floor where a tankless hung on a wall, so these closets are where the all-electric
       conversion is tightest; the diameter is what makes them work."""

    def test_the_model_passes_today(self):
        from src.plumbing import working_space_violations
        v, _lines = working_space_violations()
        self.assertEqual(v, [])

    def test_the_tanks_are_sized_by_bedroom_count(self):
        from arkitect.lib.units import IN
        from src.plumbing import WH_TANKS
        self.assertEqual(WH_TANKS['UNIT 1'], (50, IN(20)))
        self.assertEqual(WH_TANKS['UNITS 2 / 3'], (40, IN(18)))
        self.assertEqual(WH_TANKS['UNITS 4 / 5'], (40, IN(18)))

    def test_units_2_3_and_unit_1_keep_their_panel_spaces_clear(self):
        """The two that CAN be clear are clear, and nothing hides in the exception."""
        from src.plumbing import HEATER_RECT, PANEL_SPACE, PANEL_SPACE_EXCEPTION
        from arkitect.lib.model.water import _overlap_box
        for nm in ('UNIT 1', 'UNITS 2 / 3'):
            self.assertNotIn(nm, PANEL_SPACE_EXCEPTION)
            self.assertEqual(_overlap_box(HEATER_RECT[nm], PANEL_SPACE[nm]), (0.0, 0.0), nm)

    def test_a_bigger_tank_in_units_2_3_fails(self):
        """22\" is what a 50-gallon tank measures, and it does not fit: it lands inside
           the panel's working space. This is the assert that says so."""
        import src.plumbing as p
        keep = p.HEATER_RECT['UNITS 2 / 3']
        try:
            x, y, w, h = keep
            p.HEATER_RECT['UNITS 2 / 3'] = (x, y-4.0/12.0, w, h+4.0/12.0)
            v, _l = p.working_space_violations()
        finally:
            p.HEATER_RECT['UNITS 2 / 3'] = keep
        self.assertTrue(any('inside the panel working space' in x for x in v), v)

    def test_unit_1s_heater_space_stays_in_its_room(self):
        """Unit 1's heater space once started at the tank's west edge and ran 10" past the
           strip's east wall into Bath 1, and nothing failed. Put it back there and the
           build stops."""
        from arkitect.lib.units import IN
        import src.building1 as b
        import src.plumbing as p
        x, y, w, h = p.HEATER_SPACE['UNIT 1']
        self.assertAlmostEqual(x+w, b.site_x(b.MX1))            # flush to the strip's east wall
        keep = p.HEATER_SPACE['UNIT 1']
        try:
            p.HEATER_SPACE['UNIT 1'] = (b.site_x(b.MX1-IN(20)), y, w, h)
            v, _l = p.working_space_violations()
        finally:
            p.HEATER_SPACE['UNIT 1'] = keep
        self.assertTrue(any('heater working space leaves the mechanical room' in x for x in v), v)

    def test_the_units_4_5_exception_is_pinned(self):
        """That closet cannot give a clear space at any tank size; the overlap it does
           have is recorded, and the build fails if it grows."""
        import src.plumbing as p
        self.assertIn('UNITS 4 / 5', p.PANEL_SPACE_EXCEPTION)
        keep = p.PANEL_SPACE_EXCEPTION['UNITS 4 / 5']
        try:
            p.PANEL_SPACE_EXCEPTION['UNITS 4 / 5'] = 0.0
            v, _l = p.working_space_violations()
        finally:
            p.PANEL_SPACE_EXCEPTION['UNITS 4 / 5'] = keep
        self.assertTrue(any('UNITS 4 / 5' in x and 'panel working space' in x for x in v), v)

    def test_a_tank_out_of_its_closet_fails(self):
        import src.plumbing as p
        keep = p.HEATER_RECT['UNIT 1']
        try:
            p.HEATER_RECT['UNIT 1'] = (keep[0]+3.0, keep[1], keep[2], keep[3])
            v, _l = p.working_space_violations()
        finally:
            p.HEATER_RECT['UNIT 1'] = keep
        self.assertTrue(any('leaves its mechanical closet' in x for x in v), v)


class MixingValveTests(unittest.TestCase):
    """The designer's instruction of 2026-09-15: store at 140 F, mix to 120 F at the tank outlet.
       The capacity uplift is a mass balance, so it is derived and asserted, never typed."""

    def test_the_settings(self):
        from src.plumbing import WH_STORE_F, WH_DELIVER_F, WH_COLD_F, WH_TMV_STD
        self.assertEqual((WH_STORE_F, WH_DELIVER_F, WH_COLD_F), (140, 120, 50))
        # ASSE 1017 is the distribution-system valve; 1070 is point-of-use and is not it
        self.assertEqual(WH_TMV_STD, 'ASSE 1017')

    def test_the_uplift_is_the_mass_balance(self):
        from src.plumbing import usable_factor
        self.assertAlmostEqual(usable_factor(), (140-50)/(120-50.0), places=9)
        self.assertAlmostEqual(usable_factor(), 1.2857142857, places=9)
        # a warmer inlet gives MORE, so the quoted 50 F is the conservative case
        self.assertGreater(usable_factor(cold=55), usable_factor(cold=50))
        self.assertLess(usable_factor(cold=45), usable_factor(cold=50))

    def test_the_delivered_equivalents(self):
        """The figures P-601 note 6a prints: the 40s deliver like 51, Unit 1's 50 like 64."""
        from src.plumbing import effective_gallons
        self.assertEqual(effective_gallons('UNITS 2 / 3'), 51)
        self.assertEqual(effective_gallons('UNITS 4 / 5'), 51)
        self.assertEqual(effective_gallons('UNIT 1'), 64)

    def test_storage_stays_out_of_the_legionella_band(self):
        """Growth runs to about 113 F; storing AT the delivery temperature would sit in
           the top of that band, which is the reason for storing hot and mixing down."""
        from src.plumbing import WH_STORE_F
        self.assertGreater(WH_STORE_F, 113)

    def test_an_impossible_blend_raises(self):
        from src.plumbing import usable_factor
        with self.assertRaises(AssertionError):
            usable_factor(store=110, deliver=120)     # cannot deliver hotter than stored
        with self.assertRaises(AssertionError):
            usable_factor(cold=125, deliver=120)      # cold inlet above the delivery


if __name__ == '__main__':
    unittest.main(verbosity=2)
