"""400 Oak's service equipment: on Building 1's north wall behind the dining area, clear of
   each other, the openings, the leader and the meter's working space; each rule fires."""
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class ServiceTests(unittest.TestCase):

    def test_the_equipment_passes(self):
        from src import services as S
        S.check_services()
        self.assertEqual([b.mark for b in S.on(1, "NORTH")], ["HP-1", "EM-1", "TC-1"])

    def _bad(self, mark, words, **change):
        from src import services as S
        eq = [b._replace(**change) if b.mark == mark else b for b in S.EQUIPMENT]
        bad = S.service_violations(eq)
        self.assertTrue(any(words in v for v in bad), bad)

    def test_a_box_on_the_bath_wall_fails(self):
        from src import services as S
        self._bad("TC-1", "off the wall behind the dining area", along0=S.B1_NORTH_RUN[1]+1.0, along1=S.B1_NORTH_RUN[1]+2.0)

    def test_a_low_meter_fails(self):
        self._bad("EM-1", "its center is", z0=1.0, z1=3.5)

    def test_the_outdoor_unit_in_the_meters_working_space_fails(self):
        from src import services as S
        em = next(b for b in S.EQUIPMENT if b.mark == "EM-1")
        self._bad("HP-1", "stands in its working space", along0=em.along0-3.5, along1=em.along0-0.5)

    def test_a_box_over_a_window_fails(self):
        from src import services as S
        a0, a1, z0, z1, mk = S.openings(1, "NORTH")[0]
        eq = [S.EQUIPMENT[0]._replace(along0=a0, along1=a1, z0=z0, z1=z0+1.0)]
        self.assertTrue(any("covers" in v for v in S.service_violations(eq)))

    def test_building_2_meters_north_units_south(self):
        from src import services as S
        self.assertEqual(sorted(b.mark for b in S.on(2, "NORTH")), ["EM-2", "TC-2"])
        self.assertEqual(sorted(b.mark for b in S.on(2, "SOUTH")), ["HP-2", "HP-3"])
        self.assertEqual(S.POSITIONS["EM-2"], 2)

    def test_an_outdoor_unit_by_the_egress_window_fails(self):
        from src import services as S
        wa = next(o for o in S.openings(2, "SOUTH") if o[4] == "W-A")
        self._bad("HP-3", "escape opening", along0=wa[0]-4.0, along1=wa[0]-1.0)

    def test_an_outdoor_unit_on_the_parking_walk_side_by_the_dryer_fails(self):
        from src import services as S
        bay = S.dryer_bays(2, "NORTH")[0]
        self._bad("HP-2", "dryer cap", wall="NORTH", along0=bay[1]+1.0, along1=bay[1]+4.0)

    def test_the_meter_bank_on_the_dryer_bay_fails(self):
        from src import services as S
        bay = S.dryer_bays(2, "NORTH")[0]
        self._bad("EM-2", "dryer cap", along0=bay[0], along1=bay[0]+2.33)

    def test_a_box_on_the_leader_fails(self):
        from src import services as S
        self.assertTrue(any("leader" in v for v in S.service_violations(None, [("DS-9", S.EQUIPMENT[0].along0+1.0)])))


if __name__ == '__main__':
    unittest.main()
