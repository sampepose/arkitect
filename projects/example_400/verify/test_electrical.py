"""400 Oak's electrical model: the NEC 2023 checks pass on both buildings, and each of a
   few of them fires when the plan breaks the rule it guards."""
import importlib
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    fresh()
    leave()


def fresh():
    from src import electrical
    return importlib.reload(electrical)


def _without(devs, pred):
    """Drop the first device matching pred from a LEVEL's own list (a Level copies its
       devices when it is built, so the module's E_* lists are not what is checked)."""
    i = next(k for k, d in enumerate(devs) if pred(d))
    del devs[i]


class ElectricalTests(unittest.TestCase):

    def tearDown(self):
        fresh()

    def test_both_buildings_pass(self):
        fresh().check_electrical()

    def test_a_bedroom_wall_short_of_a_receptacle_fails(self):
        e = fresh()
        _without(e.LEVEL_U1_L2.devices, lambda d: d.kind == 'dup' and d.x == 19.5 and d.y == 30.0)   # Bedroom 3
        v = e.check_unit(e.UNIT_1)
        self.assertTrue(any('BEDROOM 3' in m and '210.52(A)' in m for m in v), v)

    def test_a_stair_light_with_one_switch_fails(self):
        e = fresh()
        _without(e.LEVEL_U1_L2.devices, lambda d: d.kind == 'sw3')
        v = e.check_unit(e.UNIT_1)
        self.assertTrue(any('210.70(A)(2)(c)' in m for m in v), v)

    def test_a_bedroom_without_a_smoke_alarm_fails(self):
        e = fresh()
        _without(e.LEVEL_U2.devices, lambda d: d.kind == 'sd' and d.x == 16.0)                  # Bedroom 2
        v = e.check_unit(e.UNIT_23)
        self.assertTrue(any('RCO 314' in m for m in v), v)

    def test_the_services(self):
        e = fresh()
        b1 = e.service_loads(e.SERVICES[0])
        b2 = e.service_loads(e.SERVICES[1])
        self.assertGreaterEqual(b1[3], e.SERVICES[0]['positions'][0][1])   # never under its panel
        self.assertGreaterEqual(b1[3], 100)                                 # 230.79(C)
        self.assertGreaterEqual(b2[3], b2[2]['amps'])
        for s in e.SERVICES:
            self.assertIn('EMERGENCY', s['marking'])                        # 230.85, both

    def test_no_heat_pump_range_dryer_or_water_heater_circuit_carries_gfci(self):
        """The designer, 2026-09-19: Ohio's minimum, RCO 3401.1's 210.8(A) and 210.8(F) Exception No. 2."""
        e = fresh()
        from src.sheets.e_common import NOTES
        kinds = ('range', 'dryer', 'hp', 'wh')
        for cks in (e.UNIT_1.circuits, e.UNIT_23.circuits):
            self.assertEqual(sorted(c.kind for c in cks if c.kind in kinds), sorted(kinds))
            self.assertEqual({c.prot for c in cks if c.kind in kinds}, {'—'})
        self.assertNotIn('GFCI', NOTES[3])


if __name__ == '__main__':
    unittest.main()
