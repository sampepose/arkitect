"""Plan symbols, grouped by what the thing actually is.

    base.py         Symbol, Rect, ClearSpace, the registry and the @symbol decorator
    plumbing.py     tub, wc, lav, sink                — what P-601 counts as fixtures
    appliances.py   range, fridge, dw, wd, wh         — and the water heater's clearance
    electrical.py   panel                             — and its NEC 110.26(A) clearance
    casework.py     counter, chase, wardrobe, rod            — built in, part of the work
    furniture.py    bed, sofa, table, desk, chair, box — loose, the tenant's, not drawn

This was one module called `furniture` holding all of it behind an 18-branch if/elif
chain, which put a stacked washer/dryer, a water closet and a required electrical
working space under the same heading. They are not the same kind of thing and they are
not answerable to the same code: the fixtures drive P-601's drainage fixture units, the
appliances drive the gas and electrical loads, the clearances are code minimums that
must not be built over, and the furniture is explicitly not in the contract.

The plans still name symbols by the same short `kind` strings, and `draw` still takes
the same item tuples, so nothing outside this package changed.

KNOWN WART: everything here is drawn on CAD layer A-FURN, which is now visibly wrong
for the fixtures, appliances and clearances. Splitting it — A-FLOR-CASE, P-FIXT and so
on — would change the DXF, so it is left alone until that is wanted.
"""
from .base import REGISTRY, LW
# Imported for the side effect ONLY: importing each module runs its @symbol decorators,
# which is what fills REGISTRY. Nothing here reads the names, so a linter sees five dead
# imports; they are named in __all__ below to say they are deliberate. Removing them
# empties the registry and every symbol silently stops drawing. Do not remove.
from . import plumbing, appliances, electrical, casework, furniture, mechanical
from reportlab.lib.colors import black, white

# What this package exports. `draw` and `LOOSE` are what the plans and the dimensioning
# code actually import; REGISTRY and LW are re-exported from base for anything that
# needs to look a kind up. The five submodules are listed because they are imported for
# their side effect alone — see above.
__all__ = ['draw', 'LOOSE', 'REGISTRY', 'LW',
           'plumbing', 'appliances', 'electrical', 'casework', 'furniture', 'mechanical']


# Loose furniture: drawn in the capacity studies, never on the issued plans (A-001 note
# 9a). The dimensioning code needs the same set, to place a room's dimensions clear of
# what is actually drawn.
LOOSE = {'table', 'chair', 'sofa'}


def draw(p, items, captions=None):
    """items = (x, y, w, h, kind, face) in plan feet. face in n/s/e/w.

    Every item gets the same pen before it draws and the same pen restored after, so a
    symbol may change weight, color or dash freely without leaking into the next one.

    `captions` maps a kind to the two lines its symbol prints inside itself, for the
    clearance rectangles that carry a code citation. Supplied by the project, because
    the citation belongs to a jurisdiction and this module draws for any of them.

    An unknown kind RAISES. It used to draw nothing, which is what the if/elif chain did
    by falling off the end of itself -- but the chain's silence was an accident of how it
    was written, not a decision, and carrying it into the registry made a typo in a kind
    string ('wardobe', 'sinl') delete a contract fixture from a plan with no error, no
    warning and nothing for a test to catch. draw_device() in symbols/electrical.py has
    raised on the same mistake all along; this is the two agreeing.
    """
    from lib.draw.page import LAY; LAY("A-FURN")
    captions = captions or {}
    c = p.c
    for it in items:
        kind = it[4]
        if kind not in REGISTRY:
            raise KeyError('no such symbol kind %r; the registry has %s'
                           % (kind, ', '.join(sorted(REGISTRY))))
        cls = REGISTRY[kind]
        c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(LW)
        cls(p, it, captions.get(kind)).draw()
        c.setLineWidth(LW)
