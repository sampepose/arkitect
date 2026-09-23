"""The mechanical model: the ventilation table, the cap finder, the dryer arithmetic,
the real units passing, and the figures A-001 quotes from it."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class CapFinderTests(unittest.TestCase):

    def _wall(self, openings, lo=0.0, hi=20.0):
        from src.mechanical import Opening, Wall
        return Wall('W', 'v', 0.0, lo, hi, [Opening(*o) for o in openings])

    def test_the_cap_lands_clear_of_the_window_in_any_direction(self):
        """A cap above a window's head may come closer along the wall than one beside
           it, because the distance is taken in the wall's plane."""
        from src.mechanical import EXH_CLR, cap_position
        from arkitect.codes.ohio.rco.mechanical import CAP_R, _dist
        w = self._wall([(8.0, 11.0, 2.5, 8.5, 'W')])
        beside = cap_position(w, 5.0, 10.0, EXH_CLR)
        above = cap_position(w, 9.9, 10.0, EXH_CLR)
        for a, z in ((beside, 5.0), (above, 9.9)):
            self.assertGreaterEqual(_dist(a, z, w.openings[0]), EXH_CLR+CAP_R-1e-9)
        self.assertAlmostEqual(beside, 11.0+EXH_CLR+CAP_R)
        self.assertLess(above-11.0, EXH_CLR+CAP_R)

    def test_a_legal_want_is_kept_and_a_taken_position_is_avoided(self):
        from src.mechanical import EXH_CLR, TERM_GAP, cap_position
        w = self._wall([(8.0, 11.0, 2.5, 8.5, 'W')])
        self.assertAlmostEqual(cap_position(w, 5.0, 2.0, EXH_CLR), 2.0)
        self.assertAlmostEqual(cap_position(w, 5.0, 2.0, EXH_CLR, taken=[4.0]), 4.0-TERM_GAP)

    def test_a_wall_with_no_room_raises(self):
        """The Units 4/5 rear wall: three windows with 5'-9" between them cannot take a
           cap 3'-0" from both neighbours. Nothing silently picks the least-bad spot."""
        from src.mechanical import EXH_CLR, cap_position
        w = self._wall([(1.0, 6.0, 2.5, 8.5, 'W')], 0.0, 7.0)
        with self.assertRaises(ValueError):
            cap_position(w, 5.0, 3.5, EXH_CLR)


class RealUnitsTests(unittest.TestCase):

    def test_check_mechanical_passes(self):
        import io, contextlib
        from src.mechanical import check_mechanical
        with contextlib.redirect_stdout(io.StringIO()):
            check_mechanical()

    def test_every_wall_termination_clears_its_wall(self):
        """The five WH caps went with the fuel gas: an electric storage heater vents
           nothing, so the only terminations left are dryers, baths and Unit 1's hood."""
        from src.mechanical import EXH_CLR, LEVELS, WALLS
        from arkitect.codes.ohio.rco.mechanical import terminations
        from arkitect.codes.ohio.rco.mechanical import DRYER_MAX
        rows = terminations(levels=LEVELS, walls=WALLS)
        self.assertEqual(sorted(r['term'].mark for r in rows),
                         sorted(['DR-1', 'RH-1', 'EF-1A', 'EF-1B', 'DR-2', 'EF-2', 'DR-3', 'EF-3',
                                 'DR-4', 'EF-4', 'DR-5', 'EF-5']))
        self.assertFalse([r for r in rows if r['term'].what == 'HEATER VENT'])
        for r in rows:
            t = r['term']
            if t.wall == 'ROOF': continue
            self.assertGreaterEqual(r['clr'], EXH_CLR-1e-9, t.mark)
            if t.what == 'DRYER EXHAUST':
                self.assertLessEqual(r['equiv'], DRYER_MAX)

    def test_the_storage_heaters_vent_nothing(self):
        """Nothing in src/mechanical.py knows about a heater vent any more: no WH mark,
           no CONCENTRIC duct, and no project clearance for one."""
        import src.mechanical as M
        self.assertFalse(hasattr(M, 'WH_CLR'))
        self.assertFalse(hasattr(M, 'U23_WH_CLR'))
        self.assertFalse([d for m in M.LEVELS for d in m.ducts if d.size == 'CONCENTRIC'])
        self.assertFalse([t for m in M.LEVELS for t in m.terms if t.mark.startswith('WH-')])


    def test_level_2_baths_go_through_the_roof_and_level_1_through_a_wall(self):
        from src.mechanical import LEVELS
        for m in LEVELS:
            ef = [t for t in m.terms if t.what == 'BATH EXHAUST']
            self.assertEqual(len(ef), 1, m.name)
            self.assertEqual(ef[0].wall == 'ROOF', m.level == 2, m.name)

    def test_the_schedules(self):
        from src.mechanical import outdoor_units, ventilation
        hp = {r['mark']: r for r in outdoor_units()}
        self.assertEqual(sorted(hp), ['HP-1', 'HP-2', 'HP-3', 'HP-4', 'HP-5'])
        self.assertEqual(len(hp['HP-1']['heads']), 5)
        self.assertTrue(all(len(hp[m]['heads']) == 3 for m in ('HP-2', 'HP-3', 'HP-4', 'HP-5')))
        self.assertEqual((hp['HP-1']['mca'], hp['HP-1']['mocp']), (30, 40))
        v = {r['name']: r for r in ventilation()}
        self.assertEqual((v['UNIT 1']['bedrooms'], v['UNIT 1']['required']), (4, 60))
        self.assertEqual((v['UNITS 2 / 3']['bedrooms'], v['UNITS 2 / 3']['required']), (2, 45))
        self.assertEqual((v['UNITS 4 / 5']['bedrooms'], v['UNITS 4 / 5']['required']), (2, 45))

    def test_every_dwelling_has_one_wall_control(self):
        """RCO 1103.1 (the designer, 2026-09-19): one wall control per ductless system -- five of
           them, Unit 1's two levels counting as the one system they are."""
        from src import mechanical as m
        from arkitect.codes.ohio.rco import mechanical as rco_mech
        systems = m._systems()
        self.assertEqual([s['name'] for s in systems], ['UNIT %d' % u for u in range(1, 6)])
        for s in systems:
            self.assertEqual(len(s['controls']), 1, s['name'])
            self.assertFalse(s['air'])                      # ductless: no register to stand off
        self.assertEqual(rco_mech.control_violations(systems), [])

    def test_the_fan_rates_live_on_the_m_sheets_not_a001(self):
        """The ventilation schedule on M-101 / M-102 is the rates' one home (it reads
           ventilation() directly); A-001 note 11 points there and states no CFM figure."""
        from src.sheets.a001 import PLAN_NOTES
        from src.sheets.m_common import NOTES
        i = next(k for k, t in enumerate(PLAN_NOTES) if t.startswith('11. '))
        j = next(k for k, t in enumerate(PLAN_NOTES) if k > i and t.startswith('11a'))
        text = ' '.join(PLAN_NOTES[i:j])
        self.assertNotIn('CFM', text)
        self.assertIn('VENTILATION SCHEDULE', text)
        vent = next(n for n in NOTES if n.startswith('4.'))      # by its number, not its place
        self.assertIn('RATES AS THE VENTILATION SCHEDULE', vent)


class OutdoorUnitTests(unittest.TestCase):
    """No dryer cap discharges onto an outdoor unit's coil: each keeps ODU_TERM_CLR
       along its wall from every outdoor unit on that wall, at any height."""


    def test_every_dryer_cap_clears_every_outdoor_unit(self):
        from src.mechanical import ODU_TERM_CLR, odu_clearances
        rows = odu_clearances()
        self.assertIn(('HP-1', 'DR-1'), [(hp, t.mark) for hp, t, _g in rows])
        self.assertTrue(all(t.what == 'DRYER EXHAUST' for _hp, t, _g in rows))
        for hp, t, gap in rows:
            self.assertGreaterEqual(gap, ODU_TERM_CLR-1e-9, '%s / %s' % (hp, t.mark))

    def test_hp1_where_it_stood_had_dr1_over_it(self):
        """HP-1 at site y 39.95 had DR-1 inside its length, which is why it moved."""
        from src.mechanical import TERMS
        from arkitect.codes.ohio.rco.mechanical import odu_gap
        caps = {t.mark: t for t in TERMS[1]['SAGE WALL']}
        self.assertEqual(odu_gap(39.95-20.0, 2.75, caps['DR-1'].along), 0.0)



class HeadTests(unittest.TestCase):
    """400 Oak's check, run here on 2026-09-18, found seven heads hanging across windows whose
       heads are at 8'-0"."""

    def test_no_head_stands_across_an_opening_on_its_level(self):
        from src import mechanical as m
        self.assertEqual(m.head_violations(), [])

    def test_a_head_put_back_across_the_w_c_fails(self):
        from src import mechanical as m
        lv = next(l for l in m.LEVELS if l.name == 'UNIT 4')
        keep = list(lv.heads)
        lv.heads[:] = [(h[0], 6.0, h[2], h[3]) if 'LIVING' in h[3] else h for h in keep]
        try:
            self.assertTrue(any('UNIT 4 W-C' in v for v in m.head_violations()))
        finally:
            lv.heads[:] = keep


if __name__ == '__main__':
    unittest.main()
