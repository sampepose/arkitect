"""Plumbing fixtures — the things P-601 counts as drainage fixture units."""
from .base import Symbol, symbol


@symbol
class Tub(Symbol):
    """Alcove tub: rim, inner basin, and the drain at the end the plumbing is on.

    A seventh field names the drain end. Where it is absent the drain falls at the
    `face` end, which is how the symbol behaved before the field existed.
    """
    kinds = ('tub',)

    def draw(s):
        c, X, Y, W, H, sc = s.c, s.X, s.Y, s.W, s.H, s.sc
        s.box()
        i = 0.28 * sc
        c.roundRect(X + i, Y + i, W - 2 * i, H - 2 * i, min(W, H) * 0.14, fill=0, stroke=1)
        r = 0.13 * sc
        drain_end = s.extra(6)
        if drain_end in ('w', 'e'):
            # Conventional alcove tub drain, schematically 8-1/2" from the
            # selected plumbing end and centred across the tub width.
            dx = 8.5 / 12.0 * sc
            cx = X + dx if drain_end == 'w' else X + W - dx
            c.circle(cx, Y + H / 2, r, fill=0, stroke=1)
        elif drain_end in ('n', 's'):
            dy = 8.5 / 12.0 * sc
            cy = Y + H - dy if drain_end == 'n' else Y + dy
            c.circle(X + W / 2, cy, r, fill=0, stroke=1)
        elif s.face == 'n':   c.circle(X + W / 2, Y + H - 0.55 * sc, r, fill=0, stroke=1)
        elif s.face == 's': c.circle(X + W / 2, Y + 0.55 * sc, r, fill=0, stroke=1)
        elif s.face == 'w': c.circle(X + 0.55 * sc, Y + H / 2, r, fill=0, stroke=1)
        else:             c.circle(X + W - 0.55 * sc, Y + H / 2, r, fill=0, stroke=1)


@symbol
class Shower(Symbol):
    """Shower pan: the curb, a line from each corner of the pan to the drain at its
    centre, the way the floor falls, and the drain."""
    kinds = ('shower',)

    def draw(s):
        c, X, Y, W, H, sc = s.c, s.X, s.Y, s.W, s.H, s.sc
        s.box()
        i = 0.28 * sc
        c.rect(X + i, Y + i, W - 2 * i, H - 2 * i, fill=0, stroke=1)
        cx, cy, r = X + W / 2, Y + H / 2, 0.13 * sc
        c.setLineWidth(0.3)
        for px, py in ((X + i, Y + i), (X + W - i, Y + i), (X + i, Y + H - i), (X + W - i, Y + H - i)):
            c.line(px, py, cx, cy)
        c.circle(cx, cy, r, fill=1, stroke=1)


@symbol
class WaterCloset(Symbol):
    """Tank against the wall, bowl pointing away from it.

    `face` does not mean one thing for both axes, and the drawing below is what the sets
    are authored against, so it is stated rather than changed:
      'n' / 's'  name the side the TANK is on: 'n' the tank at the low-y (top of page)
                 edge, bowl toward high y; 's' the reverse.
      'e' / 'w'  name the way the BOWL points: 'e' the tank at the left, bowl to the
                 right; 'w' the reverse. (A model's 'e'/'w' are swapped by the mirror.)
    RCO 307.1 wants 15" to each side of the pan center and 21" in front of it; the side
    clearance is measured by lib/model/dimensions.py wc_clearances(), not drawn here.
    """
    kinds = ('wc',)

    def draw(s):
        c, X, Y, W, H = s.c, s.X, s.Y, s.W, s.H
        t = 0.62 * s.sc
        if s.face in ('n', 's'):
            bw = W * 0.80; bx = X + (W - bw) / 2
            if s.face == 'n':
                c.rect(X, Y + H - t, W, t, fill=1, stroke=1)
                c.ellipse(bx, Y, bx + bw, Y + H - t, fill=1, stroke=1)
            else:
                c.rect(X, Y, W, t, fill=1, stroke=1)
                c.ellipse(bx, Y + t, bx + bw, Y + H, fill=1, stroke=1)
        else:
            bh = H * 0.80; by = Y + (H - bh) / 2
            if s.face == 'w':
                c.rect(X + W - t, Y, t, H, fill=1, stroke=1)
                c.ellipse(X, by, X + W - t, by + bh, fill=1, stroke=1)
            else:
                c.rect(X, Y, t, H, fill=1, stroke=1)
                c.ellipse(X + t, by, X + W, by + bh, fill=1, stroke=1)


@symbol
class Lavatory(Symbol):
    """Vanity top with an oval basin."""
    kinds = ('lav',)

    def draw(s):
        c, X, Y, W, H = s.c, s.X, s.Y, s.W, s.H
        s.box()
        i = 0.22 * s.sc
        c.ellipse(X + i, Y + i, X + W - i, Y + H - i, fill=0, stroke=1)


@symbol
class Sink(Symbol):
    """Double-bowl kitchen sink, the bowls split along the longer side."""
    kinds = ('sink',)

    def draw(s):
        c, X, Y, W, H = s.c, s.X, s.Y, s.W, s.H
        s.box()
        i = 0.20 * s.sc
        if W > H:
            m = X + W / 2
            c.rect(X + i, Y + i, (W - 3 * i) / 2, H - 2 * i, fill=0, stroke=1)
            c.rect(m + i / 2, Y + i, (W - 3 * i) / 2, H - 2 * i, fill=0, stroke=1)
        else:
            m = Y + H / 2
            c.rect(X + i, Y + i, W - 2 * i, (H - 3 * i) / 2, fill=0, stroke=1)
            c.rect(X + i, m + i / 2, W - 2 * i, (H - 3 * i) / 2, fill=0, stroke=1)
