"""Loose furniture — the tenant's, and not part of the work.

A-001 note 9a: beds are drawn for space planning only — each sleeping room takes one
with its door swing and egress window clear and its head on a wall with no opening in
it. Seating and dining furniture is deliberately NOT drawn on the issued plans, because
drawing it invites it to be read as fixed; the symbols exist because the capacity study
behind `u23_clear_rect()` (once A-001 note 18a) places them.
"""
from .base import Symbol, Rect, symbol


@symbol
class LooseRect(Rect):
    """Loose pieces that read as a plain rectangle."""
    kinds = ('desk', 'chair', 'box')


@symbol
class Bed(Symbol):
    """Mattress with a pillow band at the head. face = the wall the head is against."""
    kinds = ('bed',)

    def draw(s):
        c, X, Y, W, H, sc = s.c, s.X, s.Y, s.W, s.H, s.sc
        s.box()
        t = 1.15 * sc                      # pillow band at the head
        c.setLineWidth(0.3)
        if s.face == 'n':
            c.line(X, Y + H - t, X + W, Y + H - t)
            c.rect(X + 0.25 * sc, Y + H - t + 0.2 * sc, W / 2 - 0.35 * sc, t - 0.4 * sc, fill=0, stroke=1)
            c.rect(X + W / 2 + 0.1 * sc, Y + H - t + 0.2 * sc, W / 2 - 0.35 * sc, t - 0.4 * sc, fill=0, stroke=1)
        elif s.face == 's':
            c.line(X, Y + t, X + W, Y + t)
            c.rect(X + 0.25 * sc, Y + 0.2 * sc, W / 2 - 0.35 * sc, t - 0.4 * sc, fill=0, stroke=1)
            c.rect(X + W / 2 + 0.1 * sc, Y + 0.2 * sc, W / 2 - 0.35 * sc, t - 0.4 * sc, fill=0, stroke=1)
        elif s.face == 'w':
            c.line(X + t, Y, X + t, Y + H)
            c.rect(X + 0.2 * sc, Y + 0.25 * sc, t - 0.4 * sc, H / 2 - 0.35 * sc, fill=0, stroke=1)
            c.rect(X + 0.2 * sc, Y + H / 2 + 0.1 * sc, t - 0.4 * sc, H / 2 - 0.35 * sc, fill=0, stroke=1)
        else:
            c.line(X + W - t, Y, X + W - t, Y + H)
            c.rect(X + W - t + 0.2 * sc, Y + 0.25 * sc, t - 0.4 * sc, H / 2 - 0.35 * sc, fill=0, stroke=1)
            c.rect(X + W - t + 0.2 * sc, Y + H / 2 + 0.1 * sc, t - 0.4 * sc, H / 2 - 0.35 * sc, fill=0, stroke=1)


@symbol
class Sofa(Symbol):
    """Seat, back against `face`, and an arm at each end."""
    kinds = ('sofa',)

    def draw(s):
        c, X, Y, W, H = s.c, s.X, s.Y, s.W, s.H
        s.box()
        b = 0.62 * s.sc; a = 0.55 * s.sc
        c.setLineWidth(0.3)
        if s.face == 'n':
            c.line(X, Y + H - b, X + W, Y + H - b)
            c.line(X + a, Y, X + a, Y + H - b); c.line(X + W - a, Y, X + W - a, Y + H - b)
        elif s.face == 's':
            c.line(X, Y + b, X + W, Y + b)
            c.line(X + a, Y + b, X + a, Y + H); c.line(X + W - a, Y + b, X + W - a, Y + H)
        elif s.face == 'e':
            c.line(X + b, Y, X + b, Y + H)
            c.line(X + b, Y + a, X + W, Y + a); c.line(X + b, Y + H - a, X + W, Y + H - a)
        else:
            c.line(X + W - b, Y, X + W - b, Y + H)
            c.line(X, Y + a, X + W - b, Y + a); c.line(X, Y + H - a, X + W - b, Y + H - a)


@symbol
class Table(Symbol):
    """Round or oval, drawn to the box it is given."""
    kinds = ('table',)

    def draw(s):
        s.c.ellipse(s.X, s.Y, s.X + s.W, s.Y + s.H, fill=1, stroke=1)
