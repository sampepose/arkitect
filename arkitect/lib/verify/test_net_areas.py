"""net_areas(): the net figure on a notched room's label, and what it says was deducted."""
import unittest

from arkitect.lib.model.dimensions import net_areas

# a 10 x 12 room with a 2 x 3 notch out of one corner: 114 SF net of a 120 SF box
NOTCHED = [(0, 0), (8, 0), (8, 3), (10, 3), (10, 12), (0, 12)]
BOX = [(0, 0), (10, 0), (10, 12), (0, 12)]


def label(pts, name="BEDROOM 2", wording=None):
    return net_areas([(pts, [(5, 6, name, None, "AUTO SF")])], wording)[0][1][0]


class NetAreas(unittest.TestCase):
    def test_a_notched_room_says_net_of_closet_by_default(self):
        self.assertEqual(label(NOTCHED)[4], "114 SF NET OF CLOSET")

    def test_a_room_named_in_wording_says_what_it_names(self):
        self.assertEqual(label(NOTCHED, wording={"BEDROOM 2": "NET OF HALL"})[4], "114 SF NET OF HALL")

    def test_wording_for_another_room_leaves_this_one_alone(self):
        self.assertEqual(label(NOTCHED, wording={"BEDROOM 1": "NET OF HALL"})[4], "114 SF NET OF CLOSET")

    def test_a_rectangle_says_nothing_whatever_the_wording(self):
        self.assertEqual(label(BOX, wording={"BEDROOM 2": "NET OF HALL"})[4], "120 SF")


if __name__ == "__main__":
    unittest.main()
