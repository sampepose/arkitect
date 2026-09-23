"""The electrical symbols: every kind has a layer and draws, and a wall device stands off into its room.

These lived in one project's tests and touch nothing but arkitect/lib/symbols."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class ElectricalSymbolTests(unittest.TestCase):

    def test_every_kind_has_a_layer_and_draws_at_a_point_or_on_the_page(self):
        from arkitect.lib.symbols import electrical as es
        from reportlab.pdfgen import canvas
        from arkitect.lib.draw.plan import PlanDraw
        c = canvas.Canvas(os.devnull)
        p = PlanDraw(c, 100, 100, 18.0, 26, 48)
        for kind in es.LAYER:
            self.assertIn(es.LAYER[kind], ('E-POWR', 'E-LITE', 'E-ALRM'))
            es.draw_device(p, 5.0, 5.0, kind, 'n', 'A', 3)
            es.draw_device(p, 5.0, 5.0, kind, 'w', 'A', 3)
        self.assertGreaterEqual(len(es.LAYER), 18)
        descriptions = {k: k for k in es.LAYER}
        y = es.legend(p, 50, 700, list(es.LAYER), descriptions)
        self.assertLess(y, 700-len(es.LAYER)*8)
        with self.assertRaises(KeyError):
            es.draw_device(p, 1, 1, 'nope', 'n')

    def test_a_wall_device_stands_off_into_the_room(self):
        from arkitect.lib.symbols.electrical import stand_off, OFF
        self.assertEqual(stand_off(10, 20, 'n'), (10, 20+OFF))     # wall to the north: south of it
        self.assertEqual(stand_off(10, 20, 's'), (10, 20-OFF))
        self.assertEqual(stand_off(10, 20, 'e'), (10-OFF, 20))
        self.assertEqual(stand_off(10, 20, 'w'), (10+OFF, 20))
        self.assertEqual(stand_off(10, 20, 'w5'), (10, 20+OFF))
        self.assertEqual(stand_off(10, 20, 'c'), (10, 20))


if __name__ == '__main__':
    unittest.main()
