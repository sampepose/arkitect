"""One window symbol and one window tag for the whole set.

The designer, 2026-09-15: Unit 1's windows did not match the other units'. They were the one set
of windows in the project drawn by the inch-authored facade in src/sheets/plans.py
instead of by `PlanDraw.window()`, and they showed it four ways — three lines centered
in the wall against the library's two set to the exterior face, jamb ticks the library
does not draw, a mark in model inches rotated up the page rather than placed in points,
and the whole symbol on A-FURN and A-WALL rather than A-GLAZ, so the glazing layer of
the DXF held every window in the set except Unit 1's.

The tag went the other way: Unit 1 printed W-A, which is what A-602's schedule row and
the elevations call that window, while Units 2 to 5 printed a bare A. The designer, asked, chose
W-A everywhere, so the prefix is now put on at the one place a plan draws a window.
"""
import collections
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _r(v):
    """Round every float in a recorded argument, however nested, to 1e-6."""
    if isinstance(v, float):
        r = round(v, 6)
        return 0.0 if r == 0 else r
    if isinstance(v, (list, tuple)):
        return tuple(_r(x) for x in v)
    return v


class Calls:
    """A canvas that records every call made through it, with the layer in force.

    It proxies a real canvas, so what it records is what reportlab was actually asked to
    do. A layer is not a canvas call — `LAY()` sets a variable the recording tools read —
    so it is captured per call, which is what lets a test say "the A-GLAZ calls" and mean
    the window symbol and nothing else.
    """

    def __init__(s, c):
        s._c = c
        s.log = []          # (layer, method, args, kwargs)

    def __getattr__(s, n):
        from lib.draw.context import current_layer
        a = getattr(s._c, n)
        if not callable(a):
            return a

        def recorded(*args, **kw):
            s.log.append((current_layer(), n, args, tuple(sorted(kw.items()))))
            return a(*args, **kw)
        return recorded

    def on(s, layer):
        """Every call made while `layer` was in force, the layer itself dropped: two
           streams that compare equal are the same drawing on that layer.

           Floats are rounded to 1e-6, which is lib/verify/trace.py's own tolerance and
           for its reason: the same arithmetic re-associated — a room face reached as
           26 - EXT/2 - EXT/2 rather than 26 - EXT — differs in the last bit and is not
           a difference in the drawing. 1e-6 pt is 1/72,000,000 of an inch on paper."""
        return [(m, _r(a), _r(k)) for (lay, m, a, k) in s.log if lay == layer]

    def strings(s, layer):
        from reportlab.pdfgen.canvas import Canvas
        drawers = {n for n in dir(Canvas) if n.startswith('draw') and 'String' in n}
        return [a[-1] for (m, a, _) in s.on(layer) if m in drawers]


def _canvas():
    from reportlab.pdfgen import canvas
    return Calls(canvas.Canvas(os.devnull))


def _plan(c):
    from lib.draw.plan import PlanDraw
    return PlanDraw(c, 100, 100, 18.0, 26, 48)


def _unit_1_windows(level, c):
    """Unit 1's windows alone, drawn the way its plan draws them."""
    from src.sheets.plans import PlanArtist, draw_windows
    ax = PlanArtist(_plan(c))
    draw_windows(ax, level)
    ax.flush()


def _greyed_b1_level(k, c):
    """A whole Building 1 level as a trade sheet draws it: greyed, unannotated."""
    from lib.draw.sheets import draw_level
    from src.building1 import _b1_level
    from src.sheets.plans import B1_DRAWING
    lv = _b1_level(k, [], [], [], units=[], u3stair=(k == 1), annotate=False, **B1_DRAWING)
    lv.overlay = lambda p: None
    draw_level(c, lv, 100, 100)


class Unit1WindowSymbolTests(unittest.TestCase):

    def test_unit_1_draws_the_librarys_window_symbol_and_nothing_of_its_own(self):
        """The whole point: not a symbol that resembles the library's, the library's.

        The reference names Unit 1's three window walls by their ROOM FACE, which is the
        face `PlanDraw.window()` takes and every other opening in the set is dimensioned
        to: the S Elm wall's is Y_OFFSET inside plan y 0, the Sage wall's is EXT
        inside plan x 0, and the parcel wall's is EXT inside plan x 26.
        """
        from src.building1 import EXT, Y_OFFSET, windows
        for level in (1, 2):
            want = _canvas()
            p = _plan(want)
            for (x, y, ln, o, mark) in windows(level):
                if o == 'h':
                    p.window(x, Y_OFFSET, ln, 'h', 'W-' + mark)
                else:
                    p.window(EXT if x < 13 else 26 - EXT, y, ln, 'v', 'W-' + mark)
            got = _canvas()
            _unit_1_windows(level, got)
            self.assertEqual(got.on('A-GLAZ'), want.on('A-GLAZ'),
                             'Level %d: Unit 1 is not drawing the library window' % level)

    def test_unit_1_puts_its_windows_on_the_glazing_layer(self):
        """They used to land on A-FURN, so A-GLAZ held every window but Unit 1's."""
        c = _canvas()
        _unit_1_windows(1, c)
        self.assertTrue(c.on('A-GLAZ'), 'nothing on A-GLAZ')
        self.assertEqual(c.strings('A-GLAZ'), ['W-A', 'W-A', 'W-A', 'W-B', 'W-A'])

    def test_unit_1_keeps_no_window_drawing_of_its_own_on_the_furniture_layer(self):
        """The three centered lines and the jamb ticks are gone, not merely covered."""
        c = _canvas()
        _unit_1_windows(1, c)
        self.assertEqual([m for (m, _, _) in c.on('A-FURN')], [])


class WindowMarkTests(unittest.TestCase):

    def test_a_window_mark_is_drawn_in_something_that_prints(self):
        """The designer, 2026-09-15: found while matching Unit 1's windows to the others'. NO plan
           in the set has ever printed a window tag. `PlanDraw.window()` punches the
           opening white, sets the STROKE back to black for the two lines, and then draws
           the mark — which takes the FILL color, still white from the punch. The text is
           in the PDF and reads out of it; it has never been on the paper.

           Text prints in the fill color, so that is what this asserts, at the moment the
           mark is drawn and not merely somewhere in the call stream."""
        from reportlab.lib.colors import black, white
        for o in ('h', 'v'):
            c = _canvas()
            p = _plan(c)
            p.window(0.5, 4.0, 3.0, 'v', 'W-A') if o == 'v' else p.window(4.0, 0.5, 3.0, 'h', 'W-A')
            fill, drawn = None, []
            for (m, a, _) in c.on('A-GLAZ'):
                if m == 'setFillColor':
                    fill = a[0]
                elif 'String' in m:
                    drawn.append((a[-1], fill))
            self.assertEqual(len(drawn), 1, '%s: one mark expected, got %r' % (o, drawn))
            self.assertNotEqual(drawn[0][1], white, '%s: the mark is drawn in white' % o)
            self.assertEqual(drawn[0][1], black, '%s: mark fill' % o)


class WindowTagTests(unittest.TestCase):

    def test_every_window_on_a_plan_is_tagged_the_way_the_schedule_calls_it(self):
        """A-602's row is W-A and the elevations tag W-A. The designer, 2026-09-15: the plans
           follow, Units 2 to 5 included — they used to print a bare A."""
        want = {1: {'W-A': 8, 'W-B': 1, 'W-C': 1},
                2: {'W-A': 10, 'W-C': 1}}
        for level in (1, 2):
            c = _canvas()
            _greyed_b1_level(level, c)
            self.assertEqual(dict(collections.Counter(c.strings('A-GLAZ'))), want[level],
                             'Level %d window tags' % level)


class Unit5KitchenWindowTests(unittest.TestCase):
    """The designer, 2026-09-16: a window on Building 2's courtyard face for Unit 5's kitchen, above
       the flight — a W-C, centered where the W-B first went. Unit 4's wall below is under
       the stair and takes none."""

    def test_level_2_only_on_the_courtyard_wall(self):
        from src.building2 import B2_U5_KITCHEN_WIN, b2_wins
        self.assertNotIn(B2_U5_KITCHEN_WIN, b2_wins(1))
        self.assertIn(B2_U5_KITCHEN_WIN, b2_wins(2))
        self.assertEqual(B2_U5_KITCHEN_WIN[1:], (0.5, 5.0, 'h', 'C'))

    def test_centred_between_the_fridge_and_the_range_as_drawn(self):
        from src.building2 import B2_U5_KITCHEN_WIN, F_B2, PLAN_B2
        fr = next(f for f in F_B2 if f[4] == 'fridge')
        rg = next(f for f in F_B2 if f[4] == 'range')
        x = PLAN_B2.x(B2_U5_KITCHEN_WIN[0], 0.5)
        self.assertAlmostEqual(x-(PLAN_B2.x(fr[0], 0.5)+fr[2]), PLAN_B2.x(rg[0], 0.5)-(x+5.0), places=6)

    def test_the_schedule_and_the_mechanical_wall_count_it_once(self):
        from src.mechanical import WALLS
        from src.schedules import window_totals
        self.assertEqual((window_totals()['B'], window_totals()['C']), (3, 5))
        court = [o.name for o in WALLS[2]['COURTYARD WALL'].openings]
        self.assertEqual(court.count('UNIT 5 W-C'), 1)
        self.assertEqual(court.count('UNIT 4 W-C'), 0)


if __name__ == '__main__':
    unittest.main()
