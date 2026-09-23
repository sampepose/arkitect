"""The roof model: what S-103 draws, checked against the plans it is derived from."""
import os
import sys
import unittest
from codes.ohio.rco import roof_checks as roof_checks_shared

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

STUD = 5.5/12.0


class RoofTests(unittest.TestCase):

    def test_both_roofs_span_the_side_walls_and_bear_only_there(self):
        from src import roof as r
        from codes.ohio.rco import roof_checks as rco_roof
        from lib.model.regrid import EXT_STUD
        for rf in r.ROOFS:
            (b,) = rf.bays
            self.assertAlmostEqual(b.x0, EXT_STUD); self.assertAlmostEqual(b.x1, rf.W-EXT_STUD)
            self.assertAlmostEqual(b.y0, 0.0); self.assertAlmostEqual(b.y1, rf.D)
            self.assertAlmostEqual(rco_roof.truss_span(b), rf.W-2*EXT_STUD)
            self.assertAlmostEqual(rf.ridge_x, rf.W/2.0)
            self.assertEqual([ln[4] for ln in rf.bearing], ['SAGE WALL', 'ADJACENT-PARCEL WALL'])
        self.assertEqual([rf.name for rf in r.ROOFS], ['BUILDING 1', 'BUILDING 2'])
        self.assertAlmostEqual(r.EAVE_OVERHANG*12, 12.0)
        self.assertAlmostEqual(r.rake(r.B1_ROOF, 'S ELM AVENUE')*12, 12.0)
        self.assertAlmostEqual(r.rake(r.B1_ROOF, 'REAR')*12, 6.0)
        self.assertAlmostEqual(r.rake(r.B2_ROOF, 'COURTYARD')*12, 12.0)
        self.assertAlmostEqual(r.rake(r.B2_ROOF, 'REAR')*12, 12.0)
        self.assertEqual(r.dripline(r.B1_ROOF), (-1.0, -1.0, r.B1_ROOF.W+1.0, 48.5))
        self.assertAlmostEqual(r.plan_area(r.B1_ROOF), 28.0*49.5)
        self.assertAlmostEqual(r.plan_area(r.B2_ROOF), 28.0*30.0)

    def test_the_w4_band_is_four_feet_past_each_finished_face(self):
        from src import roof as r
        from src.building1 import Y_SEP_TOP, Y_SEP_BOT
        from src.partywall import W4_FACE
        lo, hi = r.B1_ROOF.w4_band
        self.assertAlmostEqual(lo, Y_SEP_TOP-W4_FACE-4.0); self.assertAlmostEqual(hi, Y_SEP_BOT+W4_FACE+4.0)
        self.assertIsNone(r.B2_ROOF.w4_band)

    def test_truss_lines_at_two_feet_inside_the_bay(self):
        from src import roof as r
        b = r.Bay('T', 0.0, 0.0, 10.0, 8.0, ('A', 'B'))
        ls = roof_checks_shared.truss_lines(b, truss_oc=r.TRUSS_OC)
        self.assertEqual(len(ls), 3)                     # 2, 4, 6 ft; the gable trusses are the sheet's
        self.assertAlmostEqual(ls[0][1], 2.0); self.assertAlmostEqual(ls[-1][1], 6.0)
        self.assertEqual((ls[0][0], ls[0][2]), (0.0, 10.0))

    def test_three_hatches_at_their_true_size_on_the_page(self):
        from src import roof as r
        from codes.ohio.rco import roof_checks as rco_roof
        from src.building1 import U1_ATTIC, site_x, site_y
        self.assertEqual([h.unit for h in r.HATCHES], ['UNIT 1', 'UNIT 3', 'UNIT 5'])
        self.assertEqual([h.sheet for h in r.HATCHES], ['A-102', 'A-102', 'A-103'])
        for h in r.HATCHES:
            x0, y0, x1, y1 = h.page
            self.assertAlmostEqual(x1-x0, rco_roof.HATCH_L); self.assertAlmostEqual(y1-y0, rco_roof.HATCH_W)
        u1 = r.HATCHES[0].page
        self.assertAlmostEqual(u1[0], site_x(U1_ATTIC[0])); self.assertAlmostEqual(u1[1], site_y(U1_ATTIC[1]))
        self.assertAlmostEqual(u1[2], site_x(U1_ATTIC[2])); self.assertAlmostEqual(u1[3], site_y(U1_ATTIC[3]))

    def test_attic_areas_and_r806_free_area(self):
        from src import roof as r
        from src.building1 import Y_SEP_TOP, Y_SEP_BOT
        a1, a23 = r.B1_ROOF.attics
        self.assertAlmostEqual(a1.area, 26.0*Y_SEP_TOP); self.assertAlmostEqual(a23.area, 26.0*(48.0-Y_SEP_BOT))
        (b2,) = r.B2_ROOF.attics
        self.assertAlmostEqual(b2.area, 26.0*28.0); self.assertAlmostEqual(b2.nfa, 26.0*28.0/150.0)

    def test_stack_e_is_over_the_units_2_3_mechanical_closet_and_outside_the_band(self):
        from src import roof as r
        ((x, y, nm),) = r.B1_ROOF.vents
        self.assertIn('STACK E', nm)
        self.assertTrue(8.0 < x < 14.5, x)
        self.assertTrue(y > r.B1_ROOF.w4_band[1], (y, r.B1_ROOF.w4_band))


class CheckTests(unittest.TestCase):

    def test_the_real_roofs_pass(self):
        from src import roof as r
        r.check_roof()

    def _roof(self, **kw):
        from src import roof as r
        base = dict(name='T', W=26.0, D=20.0, ridge_x=13.0,
                    bays=[r.Bay('T', STUD, 0.0, 26.0-STUD, 20.0, ('A', 'B'))],
                    bearing=[(0.0, 0.0, STUD, 20.0, 'A'), (26.0-STUD, 0.0, 26.0, 20.0, 'B')],
                    gables=[(0.0, 'F'), (20.0, 'R')], w4=None, w4_band=None, vents=[], hatches=[], attics=[])
        base.update(kw)
        return r.Roof(**base)

    def _hatch(self, cx, cy, page=None):
        from src import roof as r
        from codes.ohio.rco import roof_checks as rco_roof
        page = page or (cx-rco_roof.HATCH_L/2.0, cy-rco_roof.HATCH_W/2.0, cx+rco_roof.HATCH_L/2.0, cy+rco_roof.HATCH_W/2.0)
        return r.Hatch('U', 'A', 'R', cx, cy, 'u1', page)

    ROOM = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]

    def test_the_synthetic_roof_passes(self):
        from src import roof as r
        self.assertEqual(r.roof_violations(self._roof(hatches=[self._hatch(5.0, 5.0)]), {'U': self.ROOM}, {}), [])

    def test_a_bay_ending_in_the_air_fails(self):
        from src import roof as r
        rf = self._roof(bays=[r.Bay('T', 1.0, 0.0, 20.0, 20.0, ('A', 'X'))])
        v = r.roof_violations(rf, {}, {})
        self.assertTrue(any('does not end on a bearing line' in x for x in v), v)

    def test_a_vent_in_the_band_fails(self):
        from src import roof as r
        rf = self._roof(w4_band=(8.0, 12.0), vents=[(13.0, 10.0, 'V')])
        self.assertTrue(any('penetrates the W4 band' in x for x in r.roof_violations(rf, {}, {})))
        rf = self._roof(w4_band=(8.0, 12.0), vents=[(13.0, 15.0, 'V')])
        self.assertEqual(r.roof_violations(rf, {}, {}), [])

    def test_a_hatch_outside_its_room_or_on_a_light_fails(self):
        from src import roof as r
        rf = self._roof(hatches=[self._hatch(5.0, 5.0)])
        small = [(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)]
        self.assertTrue(any('outside' in x for x in r.roof_violations(rf, {'U': small}, {})))
        self.assertTrue(any('ceiling device' in x for x in r.roof_violations(rf, {'U': self.ROOM}, {'U': [(5.0, 5.0)]})))
        self.assertEqual(r.roof_violations(rf, {'U': self.ROOM}, {'U': [(5.0, 8.0)]}), [])
        self.assertTrue(any('no room polygon' in x for x in r.roof_violations(rf, {}, {})))

    def test_a_hatch_wider_than_the_truss_space_or_under_size_fails(self):
        from src import roof as r
        wide = self._hatch(5.0, 5.0, page=(3.0, 3.0, 6.0, 5.0))
        self.assertTrue(any('wider across the trusses' in x for x in r.roof_violations(self._roof(hatches=[wide]), {'U': self.ROOM}, {})))
        short = self._hatch(5.0, 5.0, page=(4.0, 4.0, 6.0, 5.5))
        self.assertTrue(any('under 22 x 30' in x for x in r.roof_violations(self._roof(hatches=[short]), {'U': self.ROOM}, {})))

    def test_a_hatch_across_w4_fails_but_one_in_the_sheathing_band_does_not(self):
        from src import roof as r
        rf = self._roof(w4=(4.9, 5.4), w4_band=(0.9, 9.4), hatches=[self._hatch(5.0, 5.0)])
        self.assertTrue(any('across W4' in x for x in r.roof_violations(rf, {'U': self.ROOM}, {})))
        rf = self._roof(w4=(7.0, 7.5), w4_band=(3.0, 11.5), hatches=[self._hatch(5.0, 5.0)])
        self.assertEqual(r.roof_violations(rf, {'U': self.ROOM}, {}), [])

    def test_unit_1s_hatch_is_in_the_sheathing_band_and_clear_of_w4(self):
        from src import roof as r
        h = r.B1_ROOF.hatches[0]
        self.assertTrue(r.B1_ROOF.w4_band[0] < h.page[3] < r.B1_ROOF.w4[0], (h.page, r.B1_ROOF.w4, r.B1_ROOF.w4_band))


class VentTests(unittest.TestCase):
    """RCO 806.2: the eave and ridge runs stop at the gables, at the W4 bands and at
       penetrations near their line, and what is left still meets 1/150."""

    def test_attic_extents_along_the_ridge(self):
        from src import roof as r
        from src.building1 import Y_SEP_TOP, Y_SEP_BOT
        a1, a23 = r.B1_ROOF.attics
        self.assertEqual((a1.y0, a1.y1), (0.0, Y_SEP_TOP))
        self.assertEqual((a23.y0, a23.y1), (Y_SEP_BOT, 48.0))
        (b2,) = r.B2_ROOF.attics
        self.assertEqual((b2.y0, b2.y1), (0.0, 28.0))

    def test_no_run_enters_the_w4_band(self):
        from src import roof as r
        from codes.ohio.rco import attic_ventilation as rco_attic
        lo, hi = r.B1_ROOF.w4_band
        runs = rco_attic.vent_runs(r.B1_ROOF, r.penetrations(r.B1_ROOF))
        self.assertTrue(runs)
        for run in runs:
            self.assertTrue(run.y1 <= lo+1e-9 or run.y0 >= hi-1e-9, run)

    def test_both_eaves_run_from_a_foot_inside_the_gable_to_the_band(self):
        from src import roof as r
        from codes.ohio.rco import attic_ventilation as rco_attic
        lo, hi = r.B1_ROOF.w4_band
        runs = rco_attic.vent_runs(r.B1_ROOF, r.penetrations(r.B1_ROOF))
        eaves = sorted((u.x, u.y0, u.y1) for u in runs if u.kind == 'EAVE')
        self.assertEqual(len(eaves), 4)
        for x, y0, y1 in eaves:
            self.assertIn(x, (0.0, 26.0))
        u1 = [e for e in eaves if e[1] < lo]
        u23 = [e for e in eaves if e[1] >= hi-1e-9]
        for _x, y0, y1 in u1:
            self.assertAlmostEqual(y0, rco_attic.SLOT_STOP); self.assertAlmostEqual(y1, lo)
        for _x, y0, y1 in u23:
            self.assertAlmostEqual(y0, hi); self.assertAlmostEqual(y1, 48.0-rco_attic.SLOT_STOP)

    def test_a_penetration_near_the_ridge_breaks_the_ridge_run(self):
        from codes.ohio.rco import attic_ventilation as rco_attic
        rf = self._roof()
        (a,) = rf.attics
        whole = [u for u in rco_attic.vent_runs(rf, []) if u.kind == 'RIDGE']
        self.assertEqual([(u.y0, u.y1) for u in whole], [(rco_attic.SLOT_STOP, 20.0-rco_attic.SLOT_STOP)])
        broken = [u for u in rco_attic.vent_runs(rf, [(13.2, 10.0, 'P')]) if u.kind == 'RIDGE']
        self.assertEqual([(u.y0, u.y1) for u in broken], [(rco_attic.SLOT_STOP, 10.0-rco_attic.VENT_CLR), (10.0+rco_attic.VENT_CLR, 20.0-rco_attic.SLOT_STOP)])
        clear = [u for u in rco_attic.vent_runs(rf, [(11.0, 10.0, 'P')]) if u.kind == 'RIDGE']
        self.assertEqual(len(clear), 1)

    def test_every_real_attic_meets_one_one_fiftieth_with_the_runs_left(self):
        from src import roof as r
        from codes.ohio.rco import attic_ventilation as rco_attic
        for rf in r.ROOFS:
            for v in rco_attic.attic_vents(rf, r.penetrations(rf)):
                self.assertGreaterEqual(v.provided, v.required, v)
                self.assertAlmostEqual(v.intake, v.eave_lf*rco_attic.EAVE_NFA)
                self.assertAlmostEqual(v.exhaust, v.ridge_lf*rco_attic.RIDGE_NFA)
                self.assertAlmostEqual(v.required, v.attic.nfa*144.0)

    def test_stack_e_and_ef_5_break_their_ridges(self):
        from src import roof as r
        from codes.ohio.rco import attic_ventilation as rco_attic
        pens1 = r.penetrations(r.B1_ROOF); pens2 = r.penetrations(r.B2_ROOF)
        self.assertTrue(any('STACK E' in p[2] for p in pens1))
        self.assertTrue(any('EF-5' in p[2] for p in pens2))
        self.assertEqual(len([u for u in rco_attic.vent_runs(r.B2_ROOF, pens2) if u.kind == 'RIDGE']), 2)
        u23_ridge = [u for u in rco_attic.vent_runs(r.B1_ROOF, pens1) if u.kind == 'RIDGE' and u.attic.startswith('UNITS 2 / 3')]
        (run,) = u23_ridge
        self.assertLess(run.y1, 48.0-rco_attic.SLOT_STOP)

    def test_an_under_ventilated_attic_fails(self):
        from src import roof as r
        from codes.ohio.rco import attic_ventilation as rco_attic
        rf = self._roof(attics=[rco_attic._attic('BIG', 26.0, 0.0, 200.0)], D=200.0)
        rf = rf._replace(bays=[r.Bay('T', STUD, 0.0, 26.0-STUD, 200.0, ('A', 'B'))],
                         bearing=[(0.0, 0.0, STUD, 200.0, 'A'), (26.0-STUD, 0.0, 26.0, 200.0, 'B')],
                         gables=[(0.0, 'F'), (200.0, 'R')])
        self.assertEqual(r.roof_violations(rf, {}, {}), [])
        tall = rf._replace(attics=[rco_attic._attic('BIG', 400.0, 0.0, 200.0)])
        self.assertTrue(any('net free area' in x for x in r.roof_violations(tall, {}, {}, pens=[])))

    def _roof(self, **kw):
        from src import roof as r
        from codes.ohio.rco import attic_ventilation as rco_attic
        base = dict(name='T', W=26.0, D=20.0, ridge_x=13.0,
                    bays=[r.Bay('T', STUD, 0.0, 26.0-STUD, 20.0, ('A', 'B'))],
                    bearing=[(0.0, 0.0, STUD, 20.0, 'A'), (26.0-STUD, 0.0, 26.0, 20.0, 'B')],
                    gables=[(0.0, 'F'), (20.0, 'R')], w4=None, w4_band=None, vents=[], hatches=[],
                    attics=[rco_attic._attic('T', 26.0, 0.0, 20.0)])
        base.update(kw)
        return r.Roof(**base)


if __name__ == '__main__':
    unittest.main(verbosity=2)
