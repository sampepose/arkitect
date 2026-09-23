"""UL Design U305 as transcribed, and the two things a drawing gets wrong about it.

A reviewer, 2026-09-21: "U305 does permit particular spray foams, but ties them to specific
board and fastening provisions. Generic 'closed-cell spray polyurethane foam' does not
identify that combination." These pin the tie, so a later edit cannot quietly drop it.
"""
import unittest

from arkitect.codes import ul_u305 as U


class DesignTests(unittest.TestCase):

    def test_the_design_is_a_2x4_wall_at_16_inches(self):
        self.assertEqual(U.STUD_NOMINAL, '2x4')
        self.assertEqual(U.STUD_OC_MAX_IN, 16.0)
        self.assertIn('Nom 2 by 4 in.', U.STUDS)
        self.assertEqual(U.BEARING_WALL_RATING, '1 HR')

    def test_every_foamed_plastic_ties_to_one_board_item(self):
        """The reviewer's point, as data: not one foam in the design stands on its own."""
        foams = [f for f in U.CAVITY_FILLS.values() if 'FOAMED PLASTIC' in f.material]
        self.assertEqual(len(foams), 5)
        for f in foams:
            self.assertIsNotNone(f.board_item, f.item)
            self.assertIn(f.board_item, U.BOARD_ITEMS, f.item)
        self.assertEqual(sorted(f.board_item for f in foams), ['3R', '3U', '3V', '3W', '3X'])

    def test_item_5_is_the_one_partial_fill_that_ties_to_nothing(self):
        self.assertEqual(U.untied_items(), ('5', '5A', '5B', '5F', '5G'))
        both = [i for i in U.partial_fill_items() if U.CAVITY_FILLS[i].board_item is None]
        self.assertEqual(both, ['5'])
        self.assertIn('partially fill', U.CAVITY_FILLS['5'].condition)
        self.assertIn('mineral wool', U.CAVITY_FILLS['5'].condition)

    def test_the_sprayed_fibers_are_listed_only_at_a_complete_fill(self):
        for item in ('5A', '5B', '5F', '5G'):
            self.assertFalse(U.CAVITY_FILLS[item].partial, item)
            self.assertIn('completely fill', U.CAVITY_FILLS[item].condition)

    def test_a_foam_without_its_board_item_is_a_finding(self):
        v = U.fill_violations([('W1R BAY', '5K', '3A', True)])
        self.assertEqual(len(v), 1)
        self.assertIn('Item 5K', v[0])
        self.assertIn('board Item 3V', v[0])
        self.assertEqual(U.fill_violations([('W1R BAY', '5K', '3V', True)]), [])

    def test_a_partial_fill_of_something_listed_only_complete_is_a_finding(self):
        v = U.fill_violations([('W1R BAY', '5A', '3', True)])
        self.assertEqual(len(v), 1)
        self.assertIn('complete fill', v[0])
        self.assertEqual(U.fill_violations([('W1R BAY', '5A', '3', False)]), [])

    def test_a_material_the_design_does_not_carry_is_a_finding(self):
        v = U.fill_violations([('W1R BAY', '5Z', '3', True)])
        self.assertEqual(len(v), 1)
        self.assertIn('no cavity insulation Item 5Z', v[0])

    def test_the_board_attaches_to_studs_or_steel_and_never_to_wood_furring(self):
        """There is no wood furring item in U305. A bay furred out in wood with the board
           hung on the furring is an ordinary-looking detail and is not this design."""
        self.assertEqual(U.board_attachment_violations([('W1R', '3A')]), [])
        self.assertEqual(U.board_attachment_violations([('W1R', '7')]), [])
        v = U.board_attachment_violations([('W1R', '2x2 WOOD FURRING')])
        self.assertEqual(len(v), 1)
        self.assertIn('no item of', v[0])

    def test_the_foam_board_items_all_re_specify_the_whole_wall(self):
        """Why choosing a foam to insulate one bay is the wrong trade: each of these is an
           alternate to Item 3, so it governs the gypsum everywhere."""
        for item in ('3U', '3V', '3W'):
            self.assertIn('VERTICALLY', U.BOARD_ITEMS[item])
            self.assertIn('staggered', U.BOARD_ITEMS[item])
        self.assertIn('TWO LAYERS', U.BOARD_ITEMS['3X'])


if __name__ == '__main__':
    unittest.main()
