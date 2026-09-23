"""400 Oak's water supply: the model passes, the tables are the code's, the one service is
   sized for all three dwellings, and the rules fire."""
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class WaterTests(unittest.TestCase):

    def test_the_model_passes(self):
        from src import plumbing as p
        p.check_plumbing()


    def test_a_shower_makes_a_bathroom_group(self):
        from src import plumbing as p
        F = p.Fixture
        rows = p.tally([F(0, 0, 1, 1, k) for k in ('wc', 'lav', 'shower')])[3]
        self.assertEqual([(r[0], r[1]) for r in rows], [('BATHROOM GROUP, FLUSH TANK WC', 1)])

    def test_the_tallies(self):
        from src import plumbing as p
        self.assertAlmostEqual(p.unit_wsfu(p.BUILDING_1, 'UNIT 1')[2], 12.1)
        self.assertAlmostEqual(p.unit_wsfu(p.BUILDING_2, 'UNIT 2')[2], 6.4)
        self.assertAlmostEqual(p.service()['total'], 24.9)

    def test_one_service_sized_at_the_longest_run(self):
        from src import plumbing as p
        from arkitect.codes.ohio import water_supply as water_supply
        sv = p.service()
        self.assertEqual((sv['meter'], sv['service']), ('3/4', '1-1/4'))
        self.assertAlmostEqual(sv['length'], max(p.building_length(b) for b in p.BUILDINGS))
        self.assertGreater(p.UPSTREAM[2], p.UPSTREAM[1])
        for b in p.BUILDINGS:
            self.assertLessEqual(water_supply.pipe_size(p.sizes(b)['service']), water_supply.pipe_size(sv['service']))

    def test_a_lower_pressure_takes_a_bigger_pipe(self):
        from src import plumbing as p
        self.assertEqual(p.pipe_for(24.9, 160.0, pressure='40 TO 49'), ('3/4', '1-1/4'))
        self.assertEqual(p.pipe_for(30.0, 300.0, pressure='40 TO 49'), ('1', '1-1/4'))

    def test_no_heater_stands_in_a_panels_working_space(self):
        from src import plumbing as p
        self.assertEqual(p.working_space_violations()[0], [])
        self.assertEqual(p.PANEL_SPACE_EXCEPTION, {})

    def test_a_heater_back_on_the_panels_wall_fails(self):
        """Where Building 2's heater first stood: 6-5/8\" inside the panel's 30\" band."""
        from src import plumbing as p
        keep = p.HEATER_RECT['UNITS 2 / 3']
        panel = p.PANEL_SPACE['UNITS 2 / 3']
        p.HEATER_RECT['UNITS 2 / 3'] = (0.5, panel[1]+panel[3]-0.55, keep[2], keep[3])
        try:
            self.assertTrue(any('inside the panel working space' in v for v in p.working_space_violations()[0]))
        finally:
            p.HEATER_RECT['UNITS 2 / 3'] = keep

    def test_a_fixture_no_run_reaches_fails(self):
        from src import plumbing as p
        u = p.UNIT_1_L1
        u.fixtures.append(p.Fixture(1.0, 1.0, 1.0, 1.0, 'lav'))
        try:
            self.assertTrue(any('lav fixture' in v for v in p.plumbing_violations()))
        finally:
            u.fixtures.pop()

    def test_the_site_water_is_in_the_north_yard(self):
        from src import plumbing as p
        from src.sitework import B1_X
        w = p.site_water()
        self.assertTrue(all(0.0 < x < B1_X for x, _y in w['service']))

    def test_no_300_vocabulary(self):
        from src.sheets import p_common, p601
        text = ' '.join(p_common.NOTES)+' '.join(p601.plumbing_notes())
        for stale in ('SAGE', 'ELM', 'W4', 'W5', 'UNIT 4', 'UNIT 5', 'UNITS 4', 'TANKLESS', 'A-103', 'ALLEY MAIN'):
            self.assertNotIn(stale, text)


if __name__ == '__main__':
    unittest.main()
