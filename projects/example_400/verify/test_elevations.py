"""400 Oak's elevations: every opening on the plans stands on one face, read the way the
   face is seen, and both sheets are in the set."""
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class ElevationTests(unittest.TestCase):

    def test_the_elevations_pass(self):
        from src.sheets import elevations as E
        E.check_elevations()

    def test_the_house_front_is_read_from_dana(self):
        from src.sheets import elevations as E
        ops = E.openings(1, 'FRONT')
        self.assertEqual(sorted(o[4] for o in ops), ["D-1", "W-A", "W-A", "W-C"])
        from src.building1 import B1_W
        door = next(o for o in ops if o[5] == "d"); wc = next(o for o in ops if o[4] == "W-C")
        a, b = sorted(o for o in ops if o[4] == "W-A")
        self.assertAlmostEqual(a[0]+a[1]/2.0+b[0]+b[1]/2.0, B1_W, places=6)      # Level 2 mirrors about the face
        self.assertAlmostEqual(wc[0]+wc[1]/2.0, a[0]+a[1]/2.0, places=6)          # the left bay stacks
        self.assertLessEqual(abs(door[0]+door[1]/2.0-(b[0]+b[1]/2.0)), 4/12.0)    # the right bay, within the door's 3"
        self.assertLess(wc[0], door[0])           # 404 Oak on the left: the living room window, then the entry

    def test_opposite_faces_are_flipped(self):
        from src.sheets import elevations as E
        from src.building2 import B2_D
        # Building 2's kitchen windows are at its courtyard end: on the left of the north
        # face, read with the front on the left, and on the right of the south face
        north = min(o[0] for o in E.openings(2, 'NORTH'))
        south_wc = next(o for o in E.openings(2, 'SOUTH') if o[4] == "W-C")
        self.assertLess(north, B2_D/2.0)
        self.assertGreater(south_wc[0], B2_D/2.0)

    def test_the_back_door_is_on_the_rear_face_under_its_landing(self):
        from src.sheets import elevations as E
        from src import grading as G
        from src.building1 import B1_W
        door = next(o for o in E.openings(1, 'REAR') if o[5] == "d")
        self.assertEqual(door[4], "D-2")
        # the rear face is read with 396 Oak on the left, which is site x less the side yard
        self.assertLessEqual(G.U1_REAR.x0-G.B1X0, door[0]+1e-6)
        self.assertGreaterEqual(G.U1_REAR.x1-G.B1X0, door[0]+door[1]-1e-6)
        self.assertLess(door[0]+door[1], B1_W)

    def test_the_south_face_level_2_mirrors_and_no_window_is_for_show(self):
        from src.sheets import elevations as E
        from src.building1 import B1_D, L1_WINS, Y_RB
        south = E.openings(1, 'SOUTH')
        l1 = sorted(o[0]+o[1]/2.0 for o in south if o[2] < 10.0)
        l2 = sorted(o[0]+o[1]/2.0 for o in south if o[2] > 10.0)
        self.assertEqual((len(l1), len(l2)), (2, 2))                 # the living room's and the sink's; Bedrooms 1 and 2
        self.assertAlmostEqual(l2[0]+l2[1], B1_D, places=6)          # Level 2 mirrors about the middle
        self.assertAlmostEqual(l1[1], l2[1], places=6)               # Bedroom 2's stands over the living room's
        self.assertFalse([w for w in L1_WINS if w[3] == 'v' and w[1] >= Y_RB])      # the pantry has none

    def test_bedroom_3_mirrors_bedroom_1(self):
        from src.sheets import elevations as E
        from src.building1 import B1_D
        north = E.openings(1, 'NORTH')
        self.assertEqual([o[4] for o in north], ["W-D", "W-B"])      # over the stair, fixed; and Bedroom 3's
        south = sorted(o for o in E.openings(1, 'SOUTH') if o[2] > 10.0)
        for n, m in zip(north, reversed(south)):                     # each is the south wall's, read from the other side
            self.assertAlmostEqual(n[0], B1_D-(m[0]+m[1]), places=6)

    def test_the_stair_window_is_over_the_well(self):
        from src import building1 as b
        w = next(w for w in b.L2_WINS if w[3] == 'v' and w[0] > b.B1_W-1.0 and w[1] < b.Y_WELL)
        self.assertGreaterEqual(w[1], b.Y_TOP_RISER)
        self.assertLessEqual(w[1]+w[2], b.Y_WELL)

    def test_the_index_has_both_sheets(self):
        from src.sheets.g001 import SHEET_INDEX
        self.assertTrue({"A-201", "A-202"} <= {n for n, _t in SHEET_INDEX})


if __name__ == '__main__':
    unittest.main()
