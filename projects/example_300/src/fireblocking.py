"""Fireblocking, RCO 302.11, and draftstopping, 302.12: the figures A-601's fireblocking
   note and W4 detail print, read from the plates, the floors and the W4 line they depend on.

   Ohio's 302.11 is the IRC's with item 6 widened to any building of more than one dwelling
   unit (OAC 4101:8-3-01, codes.ohio.gov). Nothing here is typed from a sheet."""
import math
from collections import OrderedDict

from lib.model.regrid import EXT_STUD
from lib.units import IN, fmt
from src import levels
from src.building1 import W_STUD
from src.framing import FLOORS
from src.mirror import B1_W

# A-601's fireblocking notes, by topic. A-603's W4 sections tag their fireblocks with these
# ids, so a label here is a cross-reference between sheets: never renumber one in place.
FB = OrderedDict([('W4', 'FB-1'), ('W5', 'FB-2'), ('LINES', 'FB-3'), ('PENETRATIONS', 'FB-4'),
                  ('STAIR', 'FB-5'), ('SOFFITS', 'FB-6'), ('CORNICE', 'FB-7'), ('MATERIALS', 'FB-8'),
                  ('DRAFTSTOP', 'FB-9')])

# The tags a section draws at each fireblock, agreed with the W4 sections of A-603.
TAGS = OrderedDict([
    ('W4_FLOOR',   "FIREBLOCK — PLATES AND RIM, EACH W4 WALL AT ITS OWN FLOOR LINE, A-601 %s" % FB['W4']),
    ('W4_CEILING', "FIREBLOCK — EACH W4 WALL'S TOP PLATES AT THE CEILING LINE, A-601 %s" % FB['W4']),
    ('W5_PLATES',  "FIREBLOCK — W5 PLATES AT FLOOR AND CEILING, A-601 %s" % FB['W5']),
    ('RIM',        "RIM ON ITS OWN WALL — FLOOR CAVITY CLOSED, A-601 %s" % FB['LINES']),
    ('PLATE_HOLE', "SEAL ANNULAR SPACE, A-601 %s" % FB['PENETRATIONS']),
])

BLOCK_T      = IN(1.5)      # 2" nominal lumber, 302.11.1 item 1
W5_BLOCK_MAX = 10.0         # concealed wall spaces, horizontally, 302.11 item 1.2
BATT_BLOCK_H = IN(16)       # unfaced glass fiber used as a fireblock, 302.11.1.2
DRAFTSTOP_SF = 1000.0       # the largest concealed floor-ceiling space, 302.12

# The separation is two walls back to back, W4A carrying Unit 1's floors and W4B Units
# 2 / 3', each with its own plates. So each wall's stud cavity is closed at ITS OWN floor
# line — from its top plate, under its own floor, to its Level 2 sole plate on that floor's
# subfloor — and there is no cavity spanning both. With no air space between the walls,
# their inner layers touch and no concealed space forms between them, so item 1.2's 10'-0"
# blocking is a W5 rule only.
W4_BLOCK_ZONES = OrderedDict([('W4A', (levels.F2_PLATE, levels.SUBFLOOR_TOP)),
                              ('W4B', (levels.F1_PLATE, levels.SUBFLOOR_TOP))])

# The longest W5 run each face of the W4 line allows, stud face to stud face: Unit 1 between
# its own side walls, Units 2/3 between the exterior studs.
W5_RUNS = (("UNIT 1", W_STUD), ("UNITS 2 / 3", B1_W-2*EXT_STUD))


def w5_blocks(run):
    """(intermediate full-depth blocks, their spacing) for a chase run at W5_BLOCK_MAX."""
    bays = max(1, math.ceil(run/W5_BLOCK_MAX - 1e-9))
    return bays-1, run/bays


def floor_areas():
    """Each floor-ceiling's concealed space, SF, keyed by the dwelling units it separates:
       its joist bays together, a stair well not deducted, so the figure errs high."""
    areas = OrderedDict()
    for fl in FLOORS:
        for b in fl.bays:
            key = b.name.split(' F')[0]
            areas[key] = areas.get(key, 0.0) + (b.x1-b.x0)*(b.y1-b.y0)
    return areas


def check_fireblocking():
    """Each W4 wall's floor-line block has depth to exist, and no floor-ceiling is large
       enough for 302.12 to want draftstopping."""
    for name, (lo, hi) in W4_BLOCK_ZONES.items():
        assert hi-lo >= BLOCK_T-1e-9, ("%s: its floor line is only %s deep, too little for the plates and rim "
                                       "to close its stud cavity" % (name, fmt(hi-lo)))
    areas = floor_areas()
    for name, sf in areas.items():
        assert sf <= DRAFTSTOP_SF, ("%s: the floor-ceiling encloses %.0f SF, over the %.0f SF of RCO 302.12 — "
                                    "draftstop it" % (name, sf, DRAFTSTOP_SF))
    runs = "; ".join("%s %s, %d blocks at %s" % ((n, fmt(r))+(w5_blocks(r)[0], fmt(w5_blocks(r)[1])))
                     for n, r in W5_RUNS)
    zones = "; ".join("%s +%s to +%s" % (n, fmt(lo), fmt(hi)) for n, (lo, hi) in W4_BLOCK_ZONES.items())
    print("FIREBLOCKING, RCO 302.11: each W4 wall closed at its own floor line, %s; W5 %s; largest floor-ceiling "
          "%.0f SF of %.0f, no draftstopping (302.12)" % (zones, runs, max(areas.values()), DRAFTSTOP_SF))
