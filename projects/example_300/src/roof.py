"""The roofs of both buildings, derived: what S-103 draws.

Page feet, the system S-101 and S-102 use. Both roofs are what the set already commits
to — a 4:12 gable with its ridge front to back, trusses at 24" o.c. spanning the
Sage wall to the adjacent-parcel wall and bearing on those two walls only (S-102
note 8, A-202, A-601 R1, levels.ROOF_PITCH). Eaves and rakes overhang 12", Building 1's
rear rake 6", as A-201, A-202 and A-301 draw them. Nothing is typed here that another
sheet prints; the trusses themselves are the manufacturer's, designed to the loads
stated below.

The three attic hatches are authored as a CENTER in each unit's own frame — Unit 1's
page feet, Units 2/3's and Building 2's model feet, the frames src/electrical.py lays
the ceilings out in — and built on the page at their true size about the mapped
center. Authoring the rectangle in model feet and mapping its corners would hand the
regrid a 30" opening and get 28-3/4" back.

Attic ventilation is continuous slots: a shingle-over intake vent along both eaves and a
ridge vent along the ridge. Each stops short of a gable end, at the W4 band and either
side of a roof penetration near its line; what is left is measured and held to 806.2.
No product is named, so the area provided is computed at the minimum ratings S-103
note 7 states for the submittal.
"""
from collections import namedtuple
from arkitect.lib.units import IN
from arkitect.lib.model.regrid import EXT_STUD
from src.partywall import W4_FACE
from src import levels
from src.building1 import PLAN_L2, U1_ATTIC, U23_E_RISER, Y_SEP_BOT, Y_SEP_TOP, site_x, site_y
from src.building2 import B2_D, B2_W, PLAN_B2
from src.mirror import B1_W
from arkitect.codes.ohio.rco.attic_ventilation import _attic
from arkitect.codes.ohio.rco.roof_checks import HATCH_L, HATCH_W, roof_violations as _shared_roof_violations
from functools import partial

# ---------------- basis ----------------
TRUSS_OC   = IN(24)
W4_BAND    = 4.0            # FRT sheathing each side of W4, RCO 302.2.4 exception, A-601
HEEL_NOM   = levels.ROOF_HEEL   # the raised heel the details draw; the truss design sets it
INSUL_DEPTH = IN(14)        # R-49 blown at about R-3.5 per inch, A-602; HEEL_NOM holds it plus the baffle
ROOF_PITCH = levels.ROOF_PITCH

# ---------------- the roof edge ----------------
# Every overhang is horizontal, from the face of the wall sheathing to the outside face of
# the fascia or rake trim, drip edge included; the gutter is not counted. That is the
# figure RCO Table 302.1(1) measures a projection's distance to, so it is the one built to.
EAVE_OVERHANG = IN(12)      # every eave of both buildings
RAKE_OVERHANG = IN(12)      # every rake but one
# Building 1's rear gable stands src/fsd.py's OFF_B1 from the imaginary line. 12" there
# would leave exactly the 2'-0" under which the table permits no projection at all; 6"
# leaves 2'-6". The designer's call, 2026-09-16.
RAKES = {('BUILDING 1', 'REAR'): IN(6)}
# Table 302.1(1) footnote a: an eave fireblocked from the top plate to the underside of
# the roof sheathing needs no rating on its underside. Every eave is, 2x between the truss
# heels on the wall line (S-103 detail 1), so the parcel eaves' 5'-0" carries no margin.
EAVE_FIREBLOCKED = True
# Footnote b: a rake over a gable with no gable vent needs no rating on its underside.
# No gable is vented (the designer, 2026-09-19): the eave intake and the ridge vent are each attic's
# only vents, as the ridge-vent makers require -- a gable vent short-circuits the ridge
# vent, S-103 note 7. Building 1's rear rake leans on it: 2'-6" to the line is 0 hours only
# while its gable has no vent.
VENTED_GABLES = ()

# RCO Table R301.6, R301.7 and G-001: the truss design is to these. Dead loads are this
# set's R1 assembly (A-601).
ROOF_LIVE       = 20        # psf, Table R301.6
TC_DEAD         = 10        # psf, shingles, sheathing, top chord
BC_DEAD         = 10        # psf, 5/8" gypsum, R-49 blown, bottom chord
ROOF_DEFLECTION = 'L/240 LIVE, BOTTOM CHORD WITH GYPSUM CEILING'

Bay   = namedtuple('Bay', 'name x0 y0 x1 y1 bearing')                 # trusses span x, spaced along y
Hatch = namedtuple('Hatch', 'unit sheet room cx cy frame page')       # page: (x0, y0, x1, y1) page feet
Roof  = namedtuple('Roof', 'name W D ridge_x bays bearing gables w4 w4_band vents hatches attics')
# w4: W4's two finished faces, (y0, y1), or None; w4_band: the FRT sheathing band about it.


def _page(frame, x, y):
    """A unit-frame point on the page: Unit 1 is authored in page feet already, Units
       2/3 and Building 2 in their model feet, through the same regrid and mirror as
       the plans that draw them (src/framing.py header_positions does the same)."""
    if frame == 'u1':  return x, y
    if frame == 'u23': return B1_W-PLAN_L2.x(x, y), PLAN_L2.y(y)
    if frame == 'b2':  return B2_W-PLAN_B2.x(x, y), PLAN_B2.y(y)
    raise ValueError('no such frame %r' % frame)


def _hatch(unit, sheet, room, cx, cy, frame):
    px, py = _page(frame, cx, cy)
    return Hatch(unit, sheet, room, cx, cy, frame,
                 (px-HATCH_L/2.0, py-HATCH_W/2.0, px+HATCH_L/2.0, py+HATCH_W/2.0))


# ---------------- Building 1 ----------------
# Unit 1's hatch is the A-102 rectangle. Unit 3 has no hall — its bedrooms open off the
# living room — so its hatch is in the living room ceiling, clear of that room's two
# luminaires and its alarms. Unit 5's hall is 5'-0" x 3'-8" with its light and both
# alarms on the ceiling, so its hatch is in the living room too, beside the bearing
# wall; a living room is R807.1's "other readily accessible location".
_U1_CX = site_x((U1_ATTIC[0]+U1_ATTIC[2])/2.0)
_U1_CY = site_y((U1_ATTIC[1]+U1_ATTIC[3])/2.0)
B1_ROOF = Roof('BUILDING 1', B1_W, 48.0, B1_W/2.0,
    bays=[Bay('BUILDING 1', EXT_STUD, 0.0, B1_W-EXT_STUD, 48.0, ('SAGE WALL', 'ADJACENT-PARCEL WALL'))],
    bearing=[(0.0, 0.0, EXT_STUD, 48.0, 'SAGE WALL'),
             (B1_W-EXT_STUD, 0.0, B1_W, 48.0, 'ADJACENT-PARCEL WALL')],
    gables=[(0.0, 'S ELM AVENUE'), (48.0, 'REAR')],
    # W4's finished faces, and the FRT band 4'-0" past each of them, as A-301 dimensions
    w4=(Y_SEP_TOP-W4_FACE, Y_SEP_BOT+W4_FACE),
    w4_band=(Y_SEP_TOP-W4_FACE-W4_BAND, Y_SEP_BOT+W4_FACE+W4_BAND),
    # stack E rises in the Units 2/3 rear wall and goes through the roof there, P-601 1d
    vents=[(B1_W-PLAN_L2.x(U23_E_RISER, 47.5), 48.0-EXT_STUD-0.5, 'STACK E VENT, P-601 1d')],
    hatches=[_hatch('UNIT 1', 'A-102', 'HALL', _U1_CX, _U1_CY, 'u1'),
             _hatch('UNIT 3', 'A-102', 'KITCHEN / LIVING / DINING', 22.75, 36.92, 'u23')],
    # W4 continues to the roof deck, so Building 1 has two attics, one each side of it
    attics=[_attic('UNIT 1 ATTIC, S ELM SIDE OF W4', B1_W, 0.0, Y_SEP_TOP),
            _attic('UNITS 2 / 3 ATTIC, REAR SIDE OF W4', B1_W, Y_SEP_BOT, 48.0)])

# ---------------- Building 2 ----------------
B2_ROOF = Roof('BUILDING 2', B2_W, B2_D, B2_W/2.0,
    bays=[Bay('BUILDING 2', EXT_STUD, 0.0, B2_W-EXT_STUD, B2_D, ('SAGE WALL', 'ADJACENT-PARCEL WALL'))],
    bearing=[(0.0, 0.0, EXT_STUD, B2_D, 'SAGE WALL'),
             (B2_W-EXT_STUD, 0.0, B2_W, B2_D, 'ADJACENT-PARCEL WALL')],
    gables=[(0.0, 'COURTYARD'), (B2_D, 'REAR')],
    w4=None, w4_band=None, vents=[],
    hatches=[_hatch('UNIT 5', 'A-103', 'LIVING / KITCHEN / DINING', 9.25, 9.4, 'b2')],
    attics=[_attic('BUILDING 2 ATTIC', B2_W, 0.0, B2_D)])

ROOFS = (B1_ROOF, B2_ROOF)
HATCHES = tuple(h for r in ROOFS for h in r.hatches)


def rake(roof, gable):
    """The overhang of the rake over the named gable of this roof."""
    return RAKES.get((roof.name, gable), RAKE_OVERHANG)


def gable_vented(roof, gable):
    return (roof.name, gable) in VENTED_GABLES



def dripline(roof):
    """The roof's edge in its own page feet, (x0, y0, x1, y1): the eaves past both side
       walls, the rakes past both gables. y0 is the first gable's end, y1 the second's."""
    (_y0, g0), (_y1, g1) = roof.gables
    return (-EAVE_OVERHANG, -rake(roof, g0), roof.W+EAVE_OVERHANG, roof.D+rake(roof, g1))


def plan_area(roof):
    """SF of roof in plan, to the dripline: what its gutters and the site drain carry."""
    x0, y0, x1, y1 = dripline(roof)
    return (x1-x0)*(y1-y0)




def penetrations(roof):
    """Everything through this roof as (x, y, name) in page feet: the vents the roof
       holds, the Level 2 bath caps src/mechanical.py places on this building and the
       radon risers' exits src/radon.py places."""
    from src import mechanical, radon
    caps = [(t.along[0], t.along[1], '%s ROOF CAP' % t.mark)
            for lv in mechanical.LEVELS if 'BUILDING %d' % lv.bldg == roof.name for t in lv.roofcaps]
    return list(roof.vents)+caps+radon.roof_exits(roof.name)


roof_violations = partial(_shared_roof_violations, truss_oc=TRUSS_OC)


def _ceilings():
    """The room polygons and ceiling devices, unit by unit, from src/electrical.py —
       the one place each ceiling is already laid out, in the hatches' own frames."""
    from src import electrical as e
    def poly(level, name):
        for pts, nm in level.polys:
            if nm == name: return pts
        for x, y, w, d, nm in [r[:5] for r in level.rooms]:
            if nm == name: return [(x, y), (x+w, y), (x+w, y+d), (x, y+d)]
        raise KeyError('%s has no %s' % (level.name, name))
    def ceiling(level): return [(d.x, d.y) for d in level.devices if d.mount == 'c']
    levels_ = {'UNIT 1': e.LEVEL_U1_L2, 'UNIT 3': e.LEVEL_U23, 'UNIT 5': e.LEVEL_U5}
    rooms = {u: poly(levels_[u], h.room) for r in ROOFS for h in r.hatches for u in (h.unit,)}
    devices = {u: ceiling(lv) for u, lv in levels_.items()}
    return rooms, devices


def check_roof():
    """Fails the build when a roof line no longer agrees with the plans it is derived
       from. Prints nothing."""
    rooms, devices = _ceilings()
    v = [x for r in ROOFS for x in roof_violations(r, rooms, devices, penetrations(r))]
    assert not v, 'ROOF: ' + '; '.join(v)
