"""400 Oak's mechanical model: the check passes, the caps stand where the rules put them,
   the tables are the code's, and the rules fire."""
import unittest

from projects.example_400.verify import enter, leave
from codes.ohio.rco import mechanical as mechanical_shared


def setUpModule():
    enter()


def tearDownModule():
    leave()


class MechanicalTests(unittest.TestCase):

    def test_the_model_passes(self):
        from src import mechanical as m
        m.check_mechanical()

    def test_the_terminations(self):
        from src import mechanical as m
        from codes.ohio.rco import mechanical as rco_mech
        got = {r['term'].mark: r['term'].wall for r in mechanical_shared.terminations(levels=m.LEVELS, walls=m.WALLS)}
        self.assertEqual(got, {'DR-1': 'REAR WALL', 'EF-1A': 'NORTH WALL', 'EF-1B': 'ROOF',
                               'DR-2': 'NORTH WALL', 'EF-2': 'SOUTH WALL', 'DR-3': 'NORTH WALL', 'EF-3': 'ROOF'})
        for r in mechanical_shared.terminations(levels=m.LEVELS, walls=m.WALLS):
            if r['clr'] is not None:
                self.assertGreaterEqual(r['clr'], m.EXH_CLR)
            if r['equiv'] is not None:
                self.assertLessEqual(r['equiv'], rco_mech.DRYER_MAX)

    def test_table_m1505_4_3_1(self):
        from src import mechanical as m
        from codes.ohio.rco import mechanical as rco_mech
        self.assertEqual(rco_mech.whole_house_cfm(1, 1500), 30)
        self.assertEqual(rco_mech.whole_house_cfm(3, 1320), 45)
        self.assertEqual(rco_mech.whole_house_cfm(2, 660), 45)
        self.assertEqual(rco_mech.whole_house_cfm(4, 1501), 75)
        self.assertEqual(rco_mech.whole_house_cfm(8, 9000), 165)
        self.assertEqual([r['required'] for r in m.ventilation()], [45, 45])

    def test_one_outdoor_unit_per_dwelling_with_its_indoor_units(self):
        """Unit 1 is ducted in two zones (the designer, 2026-09-19); the ADUs keep three heads each."""
        from src import mechanical as m
        rows = m.outdoor_units()
        self.assertEqual([(r['mark'], r['wall'], len(r['heads'])) for r in rows],
                         [('HP-1', 'NORTH', 2), ('HP-2', 'SOUTH', 3), ('HP-3', 'SOUTH', 3)])
        self.assertEqual(rows[0]['heads'], ['AHU-1 (LEVEL 1)', 'AHU-2 (LEVEL 2)'])

    def test_unit_1s_two_zones_are_in_their_hall_soffits(self):
        """An air handler per level, hung in that level's hall soffit with its ducts, every
           register inside the room it names, and the soffit still a legal ceiling."""
        from src import mechanical as m, building1 as B1
        from lib.units import IN
        self.assertEqual(m.ducted_violations(m.UNIT_1), [])
        self.assertEqual(sorted(m.AHU_MARK.values()), ['AHU-1', 'AHU-2'])
        for level in (1, 2):
            self.assertGreaterEqual(m.soffit_clear(level), m.HALL_CEILING_MIN)
            self.assertEqual(len(m.registers(1, level, returns=True)), 1)
            self.assertTrue(m.registers(1, level))
        keep = B1.U1_SOFFIT_DROP
        try:                                   # a soffit deep enough to eat the hall's ceiling
            B1.U1_SOFFIT_DROP = IN(24)
            self.assertTrue(any('under RCO 305.1' in v for v in m.ducted_violations(m.UNIT_1)))
        finally:
            B1.U1_SOFFIT_DROP = keep

    def test_every_system_has_its_thermostat(self):
        """RCO 1103.1 (the designer, 2026-09-19): Unit 1's two ducted zones take a programmable
           thermostat each and the ADUs a wall control, each on an interior wall of a room
           its system serves and clear of the supply air."""
        from src import mechanical as m
        from codes.ohio.rco import mechanical as rco_mech
        systems = m._systems()
        self.assertEqual([s['name'] for s in systems],
                         ['UNIT 1 LEVEL 1 ZONE', 'UNIT 1 LEVEL 2 ZONE', 'UNIT 2', 'UNIT 3'])
        for s in systems:
            self.assertEqual(len(s['controls']), 1, s['name'])
        self.assertEqual(rco_mech.control_violations(systems), [])
        x, y, room, _ = systems[0]['controls'][0]
        moved = dict(systems[0], controls=[(x, y, room, True)])
        self.assertTrue(any('exterior wall' in v for v in rco_mech.control_violations([moved])))

    def test_a_cap_is_pushed_off_an_opening(self):
        from src import mechanical as m
        from codes.ohio.rco import mechanical as rco_mech
        wall = m.Wall('T', 'v', 0.0, 0.0, 30.0, [m.Opening(10.0, 13.0, 3.0, 8.0, 'W')])
        a = m.cap_position(wall, 5.0, 11.0, m.EXH_CLR)
        self.assertAlmostEqual(min(abs(a-(10.0-m.EXH_CLR-rco_mech.CAP_R)), abs(a-(13.0+m.EXH_CLR+rco_mech.CAP_R))), 0.0)
        tight = m.Wall('T', 'v', 0.0, 0.0, 8.0, [m.Opening(2.5, 5.5, 3.0, 8.0, 'W')])
        with self.assertRaises(ValueError):
            m.cap_position(tight, 5.0, 4.0, m.EXH_CLR)

    def test_a_window_beside_the_dryer_cap_fails(self):
        from src import mechanical as m
        wall = m.WALLS[2]['NORTH WALL']
        dr = next(t for t in m.TERMS[2]['NORTH WALL'] if t.mark == 'DR-2')
        keep = list(wall.openings)
        wall.openings.append(m.Opening(dr.along+1.0, dr.along+3.0, 3.0, 8.0, 'L1 W-X'))
        try:
            with self.assertRaises(AssertionError):
                m.check_mechanical()
        finally:
            wall.openings[:] = keep

    def test_the_line_sets_run_the_short_way(self):
        """The designer, 2026-09-18: heads stand on or toward their outdoor unit's wall. As drawn the
           three dwellings take about 123 ft; across the buildings they took 209."""
        from src import mechanical as m
        got = m.lineset_lengths()
        self.assertLess(got[1], 45.0); self.assertLess(got[2], 45.0); self.assertLess(got[3], 40.0)
        # Unit 1's two air handlers run 34 ft where its four heads ran 42
        self.assertLess(got[1], 36.0)
        ahus = [a for lv in m.LEVELS if lv.unit == 1 for a in lv.ahus]
        self.assertEqual(len(ahus), 2)

    def test_a_head_across_a_window_fails(self):
        """The window heads stand at 8'-0": a wall head cannot hang over one."""
        from src import mechanical as m
        self.assertEqual(m.head_violations(), [])
        lv = next(l for l in m.LEVELS if l.name == 'UNIT 2')
        win = next(o for o in m.WALLS[2]['SOUTH WALL'].openings if o.name == 'L1 W-C')
        keep = list(lv.heads)
        lv.heads.append((m.B2M.B2_W-0.5, (win.lo+win.hi)/2.0, 'e', 'LIVING'))
        try:
            self.assertTrue(any('L1 W-C' in v for v in m.head_violations()))
        finally:
            lv.heads[:] = keep

    def test_the_walls_hold_every_opening_the_elevations_draw(self):
        from src import mechanical as m
        from src.sheets import elevations as el
        for n in (1, 2):
            for which, name in (('NORTH', 'NORTH WALL'), ('SOUTH', 'SOUTH WALL'), ('FRONT', m.FRONT_NAME[n]), ('REAR', 'REAR WALL')):
                self.assertEqual(len(el.openings(n, which)), len(m.WALLS[n][name].openings), (n, which))

    def test_the_elevations_draw_every_wall_cap(self):
        from src import mechanical as m
        from src.sheets import elevations as el
        drawn = sorted(t[2] for n in (1, 2) for f in el.FACES for t in el.face_terms(n, f))
        self.assertEqual(drawn, sorted(r['term'].mark for r in mechanical_shared.terminations(levels=m.LEVELS, walls=m.WALLS) if r['term'].wall != 'ROOF'))

    def test_a_cap_reads_beside_the_right_window_on_each_face(self):
        """A cap is placed in page feet and a face reads flipped or not: its clearance to the
           face's nearest opening, measured on the face, is the model's."""
        from src import mechanical as m
        from codes.ohio.rco import mechanical as rco_mech
        from src.sheets import elevations as el
        for n, which, name in ((2, 'NORTH', 'NORTH WALL'), (2, 'SOUTH', 'SOUTH WALL'), (1, 'REAR', 'REAR WALL')):
            for x, z, mark, _k in el.face_terms(n, which):
                on_face = min(rco_mech._dist(x, z, m.Opening(o[0], o[0]+o[1], o[2], o[2]+o[3], o[4])) for o in el.openings(n, which))
                t = next(t for t in m.TERMS[n][name] if t.mark == mark)
                self.assertAlmostEqual(on_face, rco_mech.nearest_opening(m.WALLS[n][name], t.along, t.z)[0], places=6)

    def test_no_stale_vocabulary_on_the_sheets(self):
        from src.sheets import m_common
        text = ' '.join(m_common.NOTES)
        for word in ('SAGE', 'ELM', 'W4', 'UNIT 4', 'UNIT 5', 'P-601', 'TANKLESS', 'GAS'):
            self.assertNotIn(word, text)


if __name__ == '__main__':
    unittest.main()
