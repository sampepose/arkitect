"""One wall poche for the whole set, so a greyed trade plan has ONE wall grey.

The designer, 2026-09-15: on S-102, M-101, E-101, P-101 and P-102 (and P-104, since deleted
with the fuel gas) the top-most unit's
walls printed darker than every other unit's. Unit 1 is the top-most unit on the
Building 1 plans (plan y 0.46 to 23.67 of 48, and page y runs down), and it is the one
unit drawn as WALL RECTANGLES through its own inch-authored facade rather than as the
poche the library leaves between two punched rooms. Those rectangles were filled pure
black, and `GreyPen` maps black to GRAY (0.45) while it maps POCHE to LGREY (0.72): the
same wall, two greys, 60% darker for Unit 1.

The set has one wall poche and every wall takes it. On the architectural sheets the
difference was 0.0 against 0.15 and invisible, which is why this reached paper.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class Recorder:
    """A canvas that records every FILLED rect with the layer and color in force.

    It proxies a real canvas rather than standing in for one, so the drawing under test
    is the drawing the set makes — reportlab's own state machine, and `GreyPen` wrapping
    THIS object exactly as it wraps the build's canvas, so what lands here is the color
    after the grey mapping and not before it.
    """

    def __init__(s, c):
        s._c = c
        s.fill = None
        s.rects = []          # (layer, colour, (x, y, w, h))

    def __getattr__(s, n):
        return getattr(s._c, n)

    def setFillColor(s, col, *a, **k):
        s.fill = col
        return s._c.setFillColor(col, *a, **k)

    def rect(s, x, y, w, h, fill=0, stroke=1):
        from arkitect.lib.draw.context import current_layer
        if fill:
            s.rects.append((current_layer(), s.fill, (x, y, w, h)))
        return s._c.rect(x, y, w, h, fill=fill, stroke=stroke)

    def walls(s):
        """The wall fills: what is left of the poche, and Unit 1's own rectangles.
           White is a room punched out of the poche, not a wall."""
        from reportlab.lib.colors import white
        return [(col, box) for (lay, col, box) in s.rects
                if lay == 'A-WALL' and col != white]


def _greyed_b1_level(k, c):
    """The Building 1 background a trade sheet draws: the level greyed, no annotation,
       an overlay that draws nothing. Built the way M-101 and E-101 build it."""
    from arkitect.lib.draw.sheets import draw_level
    from src.building1 import _b1_level
    from src.sheets.plans import B1_DRAWING
    lv = _b1_level(k, [], [], [], units=[], u3stair=(k == 1), annotate=False, **B1_DRAWING)
    lv.overlay = lambda p: None
    return draw_level(c, lv, 100, 100)


def _canvas():
    from reportlab.pdfgen import canvas
    return Recorder(canvas.Canvas(os.devnull))


class WallPocheTests(unittest.TestCase):

    def test_a_greyed_trade_plan_draws_every_wall_in_one_grey(self):
        """The bug as the designer saw it: two greys on one plan, Unit 1's the darker."""
        from arkitect.lib.draw.page import GREY, LGREY
        for k in (1, 2):
            c = _canvas()
            _greyed_b1_level(k, c)
            greys = {col for (col, _) in c.walls()}
            self.assertNotIn(GREY, greys, 'Level %d: a wall drawn at the black grey' % k)
            self.assertEqual(greys, {LGREY}, 'Level %d wall greys' % k)

    def test_unit_1_is_most_of_those_walls_so_the_check_is_not_vacuous(self):
        """A plan whose Unit 1 stopped drawing would pass the test above saying nothing.
           Unit 1 draws 16 wall rectangles per level against the shell's one."""
        c = _canvas()
        _greyed_b1_level(1, c)
        self.assertGreaterEqual(len(c.walls()), 10)

    def test_a_unit_1_wall_takes_the_poche_the_shell_is_filled_with(self):
        """Ungreyed — on A-101 and A-102 — a Unit 1 wall is the library's poche, which is
           what makes the two agree once GreyPen lightens them together."""
        from arkitect.lib.draw.page import POCHE
        from arkitect.lib.draw.plan import PlanDraw
        from src.sheets.plans import PlanArtist, wall
        c = _canvas()
        p = PlanDraw(c, 100, 100, 18.0, 26, 48)
        ax = PlanArtist(p)
        wall(ax, 0.0, 0.0, 1.0, 1.0)
        ax.flush()
        self.assertEqual([col for (col, _) in c.walls()], [POCHE])

    def test_the_poche_the_facade_names_is_the_poche_the_library_draws(self):
        """Named once. Two independent 0.15s would drift apart without a word said."""
        from arkitect.lib.draw.page import POCHE
        from src.sheets.plans import _RGBA
        self.assertEqual(_RGBA['poche'], (POCHE.red, POCHE.green, POCHE.blue, 1.0))


if __name__ == '__main__':
    unittest.main()
