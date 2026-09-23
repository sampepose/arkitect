"""Appliances — the equipment the units are fitted with, and the clearance one of them
requires. A stacked washer/dryer is an appliance, not furniture; so is the storage
water heater, whose RCO M1305.1 service space is drawn beside it here.
"""
import math
from .base import Symbol, ClearSpace, symbol, SIDE
from reportlab.lib.colors import black


@symbol
class Range(Symbol):
    """Four burners."""
    kinds = ('range',)

    def draw(s):
        c, X, Y, W, H = s.c, s.X, s.Y, s.W, s.H
        s.box()
        r = min(W, H) * 0.16
        for dx in (0.30, 0.70):
            for dy in (0.30, 0.70):
                c.circle(X + W * dx, Y + H * dy, r, fill=0, stroke=1)


@symbol
class Fridge(Symbol):
    """Cabinet, door line on its open face, and — where a hinge is named — the swing."""
    kinds = ('fridge',)

    def draw(s):
        c, X, Y, W, H, face = s.c, s.X, s.Y, s.W, s.H, s.face
        s.box()
        d = 0.28 * s.sc
        if face == 'n':   c.line(X, Y + d, X + W, Y + d)
        elif face == 's': c.line(X, Y + H - d, X + W, Y + H - d)
        elif face == 'w': c.line(X + d, Y, X + d, Y + H)
        else:             c.line(X + W - d, Y, X + W - d, Y + H)
        c.setFillColor(black); c.setFont('Helvetica-Bold', 5.4)
        c.drawCentredString(X + W / 2, Y + H / 2 - 2, 'FRIDGE')
        # A seventh field names the hinged edge, and where it is given the 90 deg
        # swing is drawn with it. An open door always stands on its hinge side, so
        # a box wedged against a wall on that side cannot open past about 90 deg
        # and its shelves and crisper drawers never come out. Drawing the swing is
        # what shows the hinge was chosen and not left to the appliance supplier.
        hinge = s.extra(6)
        if hinge:
            fd, hd = SIDE[face], SIDE[hinge]
            hx = X + (W if (fd[0] or hd[0]) > 0 else 0)
            hy = Y + (H if (fd[1] or hd[1]) > 0 else 0)
            r  = W if fd[1] else H          # the leaf spans the face, not the depth
            a0 = math.degrees(math.atan2(-hd[1], -hd[0]))     # shut, along the face
            a1 = math.degrees(math.atan2(fd[1], fd[0]))       # open, square to it
            c.setLineWidth(0.3); c.setDash([2, 2], 0)
            c.arc(hx - r, hy - r, hx + r, hy + r, a0, (a1 - a0 + 180) % 360 - 180)
            c.line(hx, hy, hx + fd[0] * r, hy + fd[1] * r)
            c.setDash()


@symbol
class Dishwasher(Symbol):
    """Under the counter, so dashed.

    What is drawn solid over it is the counter top inset 1-1/2": three of its four
    edges are the sink bowl, the end of the run and the cabinet faces, all already
    drawn solid, so a coincident rectangle disappears under them.
    """
    kinds = ('dw',)

    def draw(s):
        c, X, Y, W, H = s.c, s.X, s.Y, s.W, s.H
        i = 0.125 * s.sc
        c.setLineWidth(0.3); c.setDash([2.5, 2], 0)
        c.rect(X + i, Y + i, W - 2 * i, H - 2 * i, fill=0, stroke=1)
        c.setDash()


@symbol
class StackedWasherDryer(Symbol):
    """The 27" x 32" stacked washer/dryer: cabinet outline and one drum.

    Stacked rather than side by side because the mechanical closets are 1'-10" bays
    and a side-by-side pair needs 5'-0" of width none of them has. It is loaded from
    the closet, so the clear space in front of it is the closet door swing, not part
    of this symbol.
    """
    kinds = ('wd',)

    def draw(s):
        s.box()
        s.c.setLineWidth(0.3)
        s.c.circle(s.X + s.W / 2, s.Y + s.H / 2, min(s.W, s.H) * 0.32, fill=0, stroke=1)


@symbol
class WaterHeater(Symbol):
    """Floor-standing electric storage water heater, marked WH.

    A cylinder, so it is drawn as one inside its square footprint rather than as the
    diagonal-crossed box the wall-hung tankless used: the round outline is what tells a
    reader the thing takes its diameter in every direction and cannot be slid into a
    corner. Nothing burns fuel, so there is no vent and no combustion-air opening.
    P-601 notes 6 and 7.
    """
    kinds = ('wh',)

    def draw(s):
        c, X, Y, W, H = s.c, s.X, s.Y, s.W, s.H
        s.box()
        c.setLineWidth(0.3)
        c.circle(X + W / 2, Y + H / 2, min(W, H) / 2 - 0.4, fill=0, stroke=1)
        c.setFillColor(black); c.setFont('Helvetica-Bold', 4.8)
        c.drawCentredString(X + W / 2, Y + H / 2 - 1.7, 'WH')


@symbol
class WaterHeaterClearance(ClearSpace):
    """Water-heater service space: visually distinct dash-dot boundary.

    Measured from the appliance face, not the wall, and it projects toward and
    slightly through the open door plane. RCO M1305.1.
    """
    kinds = ('whclear',)
    dash = (6, 2, 1, 2)
    caption_at = 0.28
