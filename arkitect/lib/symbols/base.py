"""What every drawn symbol has in common: a page rectangle, and a place in the registry.

A symbol is one fixture, appliance, piece of casework or required clearance drawn over
the plan. The plans name them by a short `kind` string in the item tuples; this module
holds the base classes and the registry that maps one to the other. The symbols
themselves live beside the things they are — plumbing fixtures in plumbing.py,
appliances in appliances.py, and so on.
"""
from reportlab.lib.colors import black, white

LW = 0.4

# Which way each face letter points on the page. The plan is drawn y-down, so 'n' is
# the larger-y edge — the same sense the tub, wc and fridge symbols already use.
SIDE = {'n': (0, -1), 's': (0, 1), 'w': (-1, 0), 'e': (1, 0)}

REGISTRY = {}

def symbol(cls):
    """Register a Symbol subclass under every kind string it answers to."""
    for k in cls.kinds:
        assert k not in REGISTRY, "two symbols claim the kind %r" % k
        REGISTRY[k] = cls
    return cls


class Symbol:
    """One symbol, placed on the page and ready to draw.

    An item is (x, y, w, h, kind[, face[, extra]]) in plan feet. By the time a Symbol
    exists, that has been turned into a page rectangle: X, Y are its lower-left corner
    in points, W and H its size. `sc` is points per foot, for the symbols whose detail
    is dimensioned in real inches rather than as a fraction of the box.
    """
    kinds = ()
    caption = ()

    def __init__(s, p, it, caption=None):
        s.p = p
        s.c = p.c
        s.sc = p.sc
        s.it = it
        s.x, s.y, s.w, s.h, s.kind = it[:5]
        s.face = it[5] if len(it) > 5 else 'n'
        s.caption = caption or s.caption
        s.X = p.X(s.x)
        s.Y = p.Y(s.y + s.h)                 # lower-left on the page
        s.W = s.w * p.sc
        s.H = s.h * p.sc

    def extra(s, i, default=None):
        """Field i of the raw item, for the few symbols that carry one."""
        return s.it[i] if len(s.it) > i else default

    def box(s, fill=1, stroke=1):
        s.c.rect(s.X, s.Y, s.W, s.H, fill=fill, stroke=stroke)

    def draw(s):
        raise NotImplementedError


class Rect(Symbol):
    """Anything that reads as a plain filled rectangle in plan.

    Not registered: the kinds that draw this way are spread across casework and loose
    furniture, and each names its own.
    """

    def draw(s):
        s.box()


class ClearSpace(Symbol):
    """A required working space: a dashed boundary with the rule that demands it.

    Not registered either. The working spaces differ only in dash pattern, line weight
    and the two lines of text they carry, and each lives beside the equipment whose
    clearance it is.
    """
    dash = ()
    weight = 0.45
    caption = ()
    # Where up its box the caption stands. Two working spaces often nearly coincide — a panel's
    # and the water heater's beside it — and two captions centered in two coinciding boxes print
    # as one smudge, which they did on two sheets for a week. Each kind takes its own height.
    caption_at = 0.5

    def draw(s):
        c, X, Y, W, H = s.c, s.X, s.Y, s.W, s.H
        c.setFillColor(white); c.setLineWidth(s.weight); c.setDash(list(s.dash), 0)
        c.rect(X, Y, W, H, fill=0, stroke=1); c.setDash()
        c.setFillColor(black); c.setFont('Helvetica', 4.2)
        # an item may carry its own height as a 7th field, where its kind's default meets a
        # neighbour's caption
        at = s.extra(6, s.caption_at)
        rows = ((Y + H * at + 1.3, s.caption[0]), (Y + H * at - 4.0, s.caption[1]))
        if s.extra(7):           # an 8th field: on white, where another box's edge crosses it
            for yy, t in rows:
                w = c.stringWidth(t, 'Helvetica', 4.2)
                c.setFillColor(white); c.rect(X + W / 2 - w / 2 - 0.8, yy - 1.2, w + 1.6, 5.0, fill=1, stroke=0)
            c.setFillColor(black)
        for yy, t in rows:
            c.drawCentredString(X + W / 2, yy, t)
