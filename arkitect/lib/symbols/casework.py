"""Built-in work: counters, the reach-in wardrobes and their rods.

A closet recessed into a wall is casework and not a wall length — A-001 note 12b —
which is why these are symbols drawn over the plan rather than part of the poche.
"""
from .base import Symbol, Rect, symbol


@symbol
class Counter(Rect):
    """Base cabinet run, drawn to its own outline."""
    kinds = ('counter',)


@symbol
class Chase(Symbol):
    """A furred pipe chase: its box, and the pipe in it as a circle."""
    kinds = ('chase',)

    def draw(s):
        s.box()
        s.c.setLineWidth(0.4)
        s.c.circle(s.X + s.W / 2, s.Y + s.H / 2, min(s.W, s.H) * 0.28, fill=0, stroke=1)


@symbol
class Wardrobe(Rect):
    """A rectangle crossed corner to corner, the usual plan mark for a wardrobe."""
    kinds = ('wardrobe',)

    def draw(s):
        s.box()
        s.c.setLineWidth(0.3)
        s.c.line(s.X, s.Y, s.X + s.W, s.Y + s.H)
        s.c.line(s.X, s.Y + s.H, s.X + s.W, s.Y)


@symbol
class ClosetRod(Symbol):
    """Closet rod, dashed, running the long way of its box."""
    kinds = ('rod',)

    def draw(s):
        c, X, Y, W, H = s.c, s.X, s.Y, s.W, s.H
        c.setLineWidth(0.5); c.setDash([3, 2], 0)
        if W > H: c.line(X, Y + H / 2, X + W, Y + H / 2)
        else:     c.line(X + W / 2, Y, X + W / 2, Y + H)
        c.setDash()
