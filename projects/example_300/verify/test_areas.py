"""Net floor area, C.C. 3332.17: derived from each dwelling's framed zone less a typed
   deduction, so a wall that moves moves the area G-001 prints."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class NetFloorAreaTests(unittest.TestCase):

    def test_net_is_the_framed_zone_less_its_deduction(self):
        from src.sitework import FRAMED_SF, NET_DEDUCT, NET_SF
        self.assertEqual(sorted(NET_SF), [1, 2, 3, 4, 5])
        for u, sf in NET_SF.items():
            self.assertEqual(sf, round(FRAMED_SF[u]-NET_DEDUCT[u]))

    def test_the_framed_zones_are_the_models_own_faces(self):
        """Not typed: Unit 1's two levels of study frame, Units 2/3 from the W4 line to the
           rear studs, Units 4/5 inside Building 2's studs."""
        from arkitect.lib.model.regrid import EXT_STUD
        from src.building1 import D_STUD, W_STUD, Y_SEP_BOT
        from src.building2 import B2_D, B2_W
        from src.mirror import B1_W
        from src.sitework import FRAMED_SF
        self.assertAlmostEqual(FRAMED_SF[1], W_STUD*D_STUD*2.0)
        self.assertAlmostEqual(FRAMED_SF[2], (B1_W-2*EXT_STUD)*(48.0-EXT_STUD-Y_SEP_BOT))
        self.assertAlmostEqual(FRAMED_SF[4], (B2_W-2*EXT_STUD)*(B2_D-2*EXT_STUD))
        self.assertEqual(FRAMED_SF[3], FRAMED_SF[2])   # Unit 3 stacks on Unit 2
        self.assertEqual(FRAMED_SF[5], FRAMED_SF[4])

    def test_a_deeper_separation_takes_it_out_of_units_2_and_3(self):
        """The check the coordinator asked for: the printed area follows the wall. With W4
           two walls, Units 2/3's framed zone is 4-3/4" shallower than one stud row gave."""
        from arkitect.lib.model.regrid import EXT_STUD
        from src.partywall import SEP_STUD, W4_STUD
        from src.building1 import Y_SEP_TOP
        from src.mirror import B1_W
        from src.sitework import FRAMED_SF, NET_DEDUCT
        width = B1_W-2*EXT_STUD
        single = (48.0-EXT_STUD-(Y_SEP_TOP+W4_STUD))*width       # what one 2x4 row would give
        self.assertAlmostEqual(FRAMED_SF[2], single-(SEP_STUD-W4_STUD)*width, places=2)
        self.assertGreater(round(single-NET_DEDUCT[2]), round(FRAMED_SF[2]-NET_DEDUCT[2]))

    def test_each_deduction_is_a_small_stated_share(self):
        from src.sitework import FRAMED_SF, NET_DEDUCT
        for u, d in NET_DEDUCT.items():
            self.assertGreaterEqual(d/FRAMED_SF[u], 0.02, u)
            self.assertLessEqual(d/FRAMED_SF[u], 0.25, u)

    def test_the_adu_rule_still_holds_on_the_derived_areas(self):
        from src.sitework import ADU_NET, ADU_NET_MAX, NET_SF, PRINCIPAL_NET
        self.assertEqual(PRINCIPAL_NET, NET_SF[1]+NET_SF[2]+NET_SF[3])
        self.assertEqual(ADU_NET, NET_SF[4])
        self.assertLessEqual(ADU_NET, ADU_NET_MAX)
        self.assertLessEqual(ADU_NET, PRINCIPAL_NET)


if __name__ == '__main__':
    unittest.main()
