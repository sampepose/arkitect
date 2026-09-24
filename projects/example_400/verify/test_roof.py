"""400 Oak's roofs: the check passes, each hatch is in its hall between two trusses, the
   vents meet RCO 806, and the rules fire."""
import unittest

from projects.example_400.verify import enter, leave
from arkitect.codes.ohio.rco import roof_checks as roof_checks_shared


def setUpModule():
    enter()


def tearDownModule():
    leave()


class RoofTests(unittest.TestCase):

    def test_the_roofs_pass(self):
        from src import roof as r
        r.check_roof()

    def test_each_hatch_is_true_size_between_trusses(self):
        from src import roof as r
        from arkitect.codes.ohio.rco import roof_checks as rco_roof
        self.assertEqual([h.unit for h in r.HATCHES], ["UNIT 1", "UNIT 3"])
        for h in r.HATCHES:
            x0, y0, x1, y1 = h.page
            self.assertAlmostEqual(x1-x0, rco_roof.HATCH_L); self.assertAlmostEqual(y1-y0, rco_roof.HATCH_W)
            self.assertTrue(r.between_trusses(h))
        moved = r.HATCHES[0]._replace(page=(5.0, 15.5, 7.5, 17.33))
        self.assertFalse(r.between_trusses(moved))

    def test_a_hatch_on_a_ceiling_light_fails(self):
        from src import roof as r
        rooms, devices = r._ceilings()
        h = r.B1_ROOF.hatches[0]
        devices = dict(devices); devices["UNIT 1"] = [(h.cx, h.cy)]
        self.assertTrue(any("ceiling device" in v for v in roof_checks_shared.roof_violations(r.B1_ROOF, rooms, devices, truss_oc=r.TRUSS_OC)))

    def test_unit_1s_hatch_chase_clears_the_air_handler_and_one_over_it_fails(self):
        from src import roof as r
        self.assertTrue(r.in_hall_soffit(r.B1_ROOF.hatches[0]))              # the whole hall is soffit
        self.assertEqual(r.soffit_violations(r.B1_ROOF.hatches), [])
        old = r._hatch('UNIT 1', 'A-101', 'HALL', 7.5, r._BETWEEN, 'b1')     # the cross-hall, over AHU-2
        self.assertTrue(r.soffit_violations([old]))

    def test_the_vents_clear_806_and_a_poor_vent_does_not(self):
        from src import roof as r
        from arkitect.codes.ohio.rco import attic_ventilation as rco_attic
        for rf in r.ROOFS:
            for av in rco_attic.attic_vents(rf, r.penetrations(rf)):
                self.assertGreater(av.provided, av.required)
        try:
            rco_attic.EAVE_NFA, rco_attic.RIDGE_NFA = 3.0, 6.0
            rooms, devices = r._ceilings()
            self.assertTrue(any("806.2" in v for v in roof_checks_shared.roof_violations(r.B1_ROOF, rooms, devices, truss_oc=r.TRUSS_OC)))
        finally:
            rco_attic.EAVE_NFA, rco_attic.RIDGE_NFA = 9.0, 18.0

    def test_each_roof_cap_is_over_its_fan(self):
        from src import roof as r
        self.assertEqual([nm for rf in r.ROOFS for _x, _y, nm in r.penetrations(rf) if "ROOF CAP" in nm], ["EF-1B ROOF CAP", "EF-3 ROOF CAP"])
        for rf in r.ROOFS:
            for x, y, _nm in r.penetrations(rf):
                self.assertTrue(0 < x < rf.W and 0 < y < rf.D)


if __name__ == '__main__':
    unittest.main()
