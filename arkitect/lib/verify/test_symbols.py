"""A kind string that names no symbol is an error, not a blank space on the plan.

`symbols.draw()` used to skip an item whose kind was not in the registry. That silence
was inherited from the if/elif chain the registry replaced, where falling off the end
did nothing -- an accident of how the chain was written rather than a decision anyone
made. The cost is specific: a plan item is `(x, y, w, h, kind, face)` and the kind is a
bare string, so `'wardobe'` for `'wardrobe'` or `'sinl'` for `'sink'` removed a contract
fixture from a sheet with no error, no warning, and nothing for any of the six oracles
to catch -- the trace sees one fewer call it has no reason to expect, and the tests
measure derived figures, of which a missing lavatory is not one.

draw_device() in arkitect/lib/symbols/electrical.py has raised on exactly this mistake since it
was written. These tests hold the two to the same rule.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from arkitect.lib import symbols


class Pen:
    """The pen calls draw() makes around every item, and nothing else."""

    def __init__(s):
        s.calls = []

    def __getattr__(s, n):
        def rec(*a, **k):
            s.calls.append((n, a))
        return rec


class Plan:
    """The little of a PlanDraw that a symbol reads: a canvas, a scale, and the two
       coordinate flips. 12 points per foot keeps the arithmetic readable."""

    def __init__(s, c):
        s.c = c
        s.sc = 12.0
        s.W = 26.0
        s.D = 48.0

    def X(s, x):
        return x * s.sc

    def Y(s, y):
        return (s.D - y) * s.sc


class UnknownKindTests(unittest.TestCase):

    def test_an_unknown_kind_raises(self):
        p = Plan(Pen())
        with self.assertRaises(KeyError) as caught:
            symbols.draw(p, [(1.0, 1.0, 2.0, 2.0, 'wardobe', 'n')])
        self.assertIn('wardobe', str(caught.exception))

    def test_the_message_names_what_it_could_have_been(self):
        """A typo is only cheap to fix when the error says what the near miss was."""
        p = Plan(Pen())
        with self.assertRaises(KeyError) as caught:
            symbols.draw(p, [(1.0, 1.0, 2.0, 2.0, 'sinl', 'n')])
        said = str(caught.exception)
        self.assertIn('sink', said)
        self.assertIn('wardrobe', said)

    def test_it_raises_before_it_draws_anything(self):
        """The bad item is the first of three. Nothing may reach the canvas: a half
           drawn plan that also raises is harder to read than one that never started."""
        p = Plan(Pen())
        items = [(1.0, 1.0, 2.0, 2.0, 'nosuchthing', 'n'),
                 (4.0, 1.0, 2.0, 2.0, 'lav', 'n'),
                 (7.0, 1.0, 2.0, 2.0, 'wc', 'n')]
        with self.assertRaises(KeyError):
            symbols.draw(p, items)
        drew = [n for (n, _) in p.c.calls
                if n not in ('setStrokeColor', 'setFillColor', 'setLineWidth')]
        self.assertEqual(drew, [], 'drew %r before raising' % drew)


class KnownKindTests(unittest.TestCase):

    def test_every_registered_kind_still_draws(self):
        """The guard must not have turned a working kind into an error. Each one gets a
           generous 3 x 3 box so a symbol that scales its detail in real inches has room
           for it, and each must put something on the canvas beyond the pen.

           A clearance rectangle needs its two caption lines supplied -- they are the
           project's, not this module's -- so a placeholder stands in for whatever a
           project would actually pass."""
        captions = {'clear': ('A', 'B'), 'whclear': ('A', 'B')}
        for kind in sorted(symbols.REGISTRY):
            with self.subTest(kind):
                p = Plan(Pen())
                symbols.draw(p, [(1.0, 1.0, 3.0, 3.0, kind, 'n')], captions)
                drew = [n for (n, _) in p.c.calls
                        if n not in ('setStrokeColor', 'setFillColor', 'setLineWidth')]
                if kind in symbols.LOOSE:
                    continue        # A-001 note 9a: studies only, never the issued plans
                self.assertTrue(drew, '%r drew nothing but the pen' % kind)

    def test_the_registry_is_not_empty(self):
        """Guards the two tests above: if the registry failed to populate, every kind
           would be unknown and the loop over it would pass by running nothing."""
        self.assertGreater(len(symbols.REGISTRY), 15, sorted(symbols.REGISTRY))
        for expect in ('wc', 'lav', 'tub', 'sink', 'wh', 'whclear', 'panel', 'clear'):
            self.assertIn(expect, symbols.REGISTRY)


class LegendCoverageTests(unittest.TestCase):
    """arkitect/lib/symbols/electrical.py's LAYER (every device kind E-101/E-102 can draw) and
       arkitect/codes/columbus/legends.py's DEVICE_KINDS (the legend row for each) used to be one
       dict, so a kind added to one was necessarily in the other. Splitting the
       description out to arkitect/codes/ (this task) removed that guarantee: nothing now stops
       a kind from being added to one side and forgotten on the other. A kind drawn but
       not described prints its symbol on a sheet with no legend row, no error and no
       other failing test; a kind described but never drawn is dead text no plan can
       ever trigger. Both are silent, so both are checked here.
    """

    def test_every_drawable_device_kind_has_a_legend_description(self):
        from arkitect.lib.symbols import electrical as es
        from arkitect.codes.columbus.legends import DEVICE_KINDS
        drawable = set(es.LAYER)
        described = set(DEVICE_KINDS)
        self.assertEqual(drawable - described, set(),
                          'drawable with no legend description: %s'
                          % sorted(drawable - described))
        self.assertEqual(described - drawable, set(),
                          'legend description for a kind that never draws: %s'
                          % sorted(described - drawable))


class ClearanceCoverageTests(unittest.TestCase):
    """The same split happened to the clearance pair: `arkitect/codes/columbus/legends.py`'s
       CLEARANCE_CAPTIONS carries the two lines of text a ClearSpace prints (the code
       citation is Columbus's, not the engine's), while the registry still decides which
       kinds draw as a ClearSpace at all. A kind added to one and not the other is as
       silent as the device-legend split above -- a clearance drawn with no caption text
       supplied, or caption text for a kind nothing ever draws -- so it gets the same
       guard. The drawable set is derived from the registry's own classes, never typed,
       so a new ClearSpace subclass is covered the moment it registers a kind.
    """

    def test_every_drawn_clearance_kind_has_a_caption_pair(self):
        from arkitect.lib.symbols.base import ClearSpace
        from arkitect.codes.columbus.legends import CLEARANCE_CAPTIONS
        drawable = {kind for kind, cls in symbols.REGISTRY.items()
                    if issubclass(cls, ClearSpace)}
        described = set(CLEARANCE_CAPTIONS)
        self.assertEqual(drawable - described, set(),
                          'clearance kind with no caption pair: %s'
                          % sorted(drawable - described))
        self.assertEqual(described - drawable, set(),
                          'caption pair for a clearance kind that never draws: %s'
                          % sorted(described - drawable))


if __name__ == '__main__':
    unittest.main()
