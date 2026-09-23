"""RCO 1103.1's rule on thermostats, on synthetic systems: one per system, in a room it
   serves, on an interior wall, and not under its own supply air."""
import unittest

from codes.ohio.rco import mechanical as rco_mech


def system(controls, served=('LIVING',), air=()):
    return dict(name='TEST', controls=list(controls), served=list(served), air=list(air))


class ControlTests(unittest.TestCase):

    def test_one_control_in_a_served_room_on_an_interior_wall_passes(self):
        ok = system([(5.0, 5.0, 'LIVING', False)])
        self.assertEqual(rco_mech.control_violations([ok]), [])

    def test_none_and_two_both_fail(self):
        for cs in ([], [(5.0, 5.0, 'LIVING', False), (9.0, 5.0, 'LIVING', False)]):
            v = rco_mech.control_violations([system(cs)])
            self.assertTrue(any('RCO 1103.1 asks one per system' in m for m in v), v)

    def test_a_room_the_system_does_not_serve_fails(self):
        v = rco_mech.control_violations([system([(5.0, 5.0, 'BEDROOM 2', False)])])
        self.assertTrue(any('does not serve' in m for m in v), v)

    def test_an_exterior_wall_fails(self):
        v = rco_mech.control_violations([system([(5.0, 5.0, 'LIVING', True)])])
        self.assertTrue(any('exterior wall' in m for m in v), v)

    def test_a_control_under_its_own_supply_air_fails(self):
        near = system([(5.0, 5.0, 'LIVING', False)], air=[(5.0, 7.0)])       # 2 ft away
        self.assertTrue(rco_mech.control_violations([near]))
        far = system([(5.0, 5.0, 'LIVING', False)], air=[(5.0, 8.5)])        # 3.5 ft
        self.assertEqual(rco_mech.control_violations([far]), [])
        self.assertEqual(rco_mech.CONTROL_REG_CLR, 3.0)


if __name__ == '__main__':
    unittest.main()
