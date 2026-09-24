"""The roofs of both buildings, derived: what S-103 draws.

Page feet, the system S-101, S-102 and S-104 use: x from the north face (396 Oak), y from
the front face. Both roofs are 4:12 gables on prefabricated trusses spanning x, north wall
to south wall, so the ridge runs front to back and the gables face Oak, the courtyard and
the alley. Neither building has a wall that continues to the deck, so each has one attic.

Attic hatches are authored as a CENTER in their unit's own model feet, as the electrical
devices are, and built on the page at a true 22" x 30": the regrid maps a rectangle corner
by corner and would shrink it. Each stands between two trusses. The Level 2 bath fans
exhaust straight up, so each roof cap is its fan's place in src/electrical.py.
"""
from collections import namedtuple
from arkitect.lib.units import IN
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.lib.model.runs import rects_overlap
from src import levels
from src.building1 import B1_D, B1_W, PLAN_B1_L2, X_COR0, X_COR1, soffit_pages
from src.building2 import B2_D, B2_W, PLAN_B2
from src.foundation import ROOF_OVERHANG
from src.framing import TRUSS_OC
from arkitect.codes.ohio.rco.attic_ventilation import _attic, attic_vents
from arkitect.codes.ohio.rco.roof_checks import HATCH_L, HATCH_W, roof_violations

# ---------------- basis ----------------
HEEL_NOM   = levels.ROOF_HEEL   # the raised heel the details draw; the truss design sets it
INSUL_DEPTH = IN(14)        # R-49 blown at about R-3.5 per inch, A-602; HEEL_NOM holds it plus the baffle
ROOF_PITCH = levels.ROOF_PITCH
EAVE_OVERHANG = ROOF_OVERHANG      # every eave and every rake, to the outside of the trim
RAKE_OVERHANG = ROOF_OVERHANG
RAKES = {}                         # no rake differs: the imaginary line stands clear of them all, src/fsd.py

ROOF_LIVE       = 20        # psf, Table R301.6
TC_DEAD         = 10        # psf, shingles, sheathing, top chord
BC_DEAD         = 10        # psf, 5/8" gypsum, R-49 blown, bottom chord
ROOF_DEFLECTION = 'L/240 LIVE, BOTTOM CHORD WITH GYPSUM CEILING'

Bay   = namedtuple('Bay', 'name x0 y0 x1 y1 bearing')                 # trusses span x, spaced along y
Hatch = namedtuple('Hatch', 'unit sheet room cx cy frame page')       # page: (x0, y0, x1, y1) page feet
Roof  = namedtuple('Roof', 'name W D ridge_x bays bearing gables w4 w4_band vents hatches attics')

_FRAME = {'b1': (B1_W, PLAN_B1_L2), 'b2': (B2_W, PLAN_B2)}


def _page(frame, x, y):
    """A unit's model point on the page, through the same regrid and mirror as its plan."""
    W, P = _FRAME[frame]
    return W-P.x(x, y), P.y(y)


def _hatch(unit, sheet, room, cx, page_cy, frame):
    """A hatch at model x `cx`, centered on page y `page_cy`, which is midway between two
       trusses."""
    _W, P = _FRAME[frame]
    cy = P.inv_y(page_cy)
    px, py = _page(frame, cx, cy)
    return Hatch(unit, sheet, room, cx, cy, frame,
                 (px-HATCH_L/2.0, py-HATCH_W/2.0, px+HATCH_L/2.0, py+HATCH_W/2.0))


def _roof(name, W, D, gables, hatches):
    return Roof(name, W, D, W/2.0,
                bays=[Bay(name, EXT_STUD, 0.0, W-EXT_STUD, D, ('NORTH WALL', 'SOUTH WALL'))],
                bearing=[(0.0, 0.0, EXT_STUD, D, 'NORTH WALL'), (W-EXT_STUD, 0.0, W, D, 'SOUTH WALL')],
                gables=gables, w4=None, w4_band=None, vents=[], hatches=hatches,
                attics=[_attic('%s ATTIC' % name, W, 0.0, D)])


# Each hatch is in its unit's Level 2 hall, between two trusses, clear of that hall's
# luminaires and alarms. Unit 3's is between the trusses at 16'-0" and 18'-0" from the
# front face. Unit 1's is in the corridor beside the well, between those at 4'-0" and
# 6'-0": its cross-hall is the soffit that hides AHU-2 and its runs, and the hatch stays
# out of it.
_BETWEEN = 8*TRUSS_OC+TRUSS_OC/2.0
_B1_BETWEEN = 2*TRUSS_OC+TRUSS_OC/2.0
B1_ROOF = _roof('BUILDING 1', B1_W, B1_D, [(0.0, 'OAK AVENUE'), (B1_D, 'REAR')],
                [_hatch('UNIT 1', 'A-101', 'HALL', (X_COR0+X_COR1)/2.0, _B1_BETWEEN, 'b1')])
B2_ROOF = _roof('BUILDING 2', B2_W, B2_D, [(0.0, 'COURTYARD'), (B2_D, 'REAR')],
                [_hatch('UNIT 3', 'A-102', 'HALL', 10.0, _BETWEEN, 'b2')])

ROOFS = (B1_ROOF, B2_ROOF)
HATCHES = tuple(h for r in ROOFS for h in r.hatches)


def rake(roof, gable):
    return RAKES.get((roof.name, gable), RAKE_OVERHANG)


def dripline(roof):
    """The roof's edge in its own page feet, (x0, y0, x1, y1): the eaves past both side
       walls, the rakes past both gables. y0 is the first gable's end, y1 the second's."""
    (_y0, g0), (_y1, g1) = roof.gables
    return (-EAVE_OVERHANG, -rake(roof, g0), roof.W+EAVE_OVERHANG, roof.D+rake(roof, g1))


def plan_area(roof):
    """SF of roof in plan, to the dripline: what its gutters and the site drain carry."""
    x0, y0, x1, y1 = dripline(roof)
    return (x1-x0)*(y1-y0)




def _level2(roof):
    from src import electrical as e
    return {'BUILDING 1': ('b1', e.LEVEL_U1_L2, 'EF-1B'), 'BUILDING 2': ('b2', e.LEVEL_U3, 'EF-3')}[roof.name]


def penetrations(roof):
    """Everything through this roof as (x, y, name) in page feet: the Level 2 bath fans'
       roof caps, each over its fan in src/electrical.py, and the radon risers' exits src/radon.py places. Plumbing vents are placed by the
       plumber to note 9's rules; no plumbing model places them yet."""
    frame, lv, mark = _level2(roof)
    fans = [d for d in lv.devices if d.kind in ('fan', 'fanc')]
    from src import radon
    return list(roof.vents)+[_page(frame, d.x, d.y)+('%s ROOF CAP' % mark,) for d in fans]+radon.roof_exits(roof.name)




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
    levels_ = {'UNIT 1': e.LEVEL_U1_L2, 'UNIT 3': e.LEVEL_U3}
    rooms = {h.unit: poly(levels_[h.unit], h.room) for h in HATCHES}
    devices = {u: ceiling(lv) for u, lv in levels_.items()}
    return rooms, devices


def between_trusses(h):
    """Does the hatch stand wholly between two adjacent trusses, clear of their 1-1/2"?"""
    k = int(h.page[1]//TRUSS_OC)
    return k*TRUSS_OC+IN(0.75) <= h.page[1]+1e-9 and h.page[3] <= (k+1)*TRUSS_OC-IN(0.75)+1e-9


def _wh(r):
    """(x0, y0, x1, y1) as the (x, y, w, h) arkitect.lib.model.runs takes."""
    return (r[0], r[1], r[2]-r[0], r[3]-r[1])


def soffit_violations(hatches):
    """Unit 1's hatch may not open into the Level 2 hall soffit: that is where AHU-2 and
       its runs are, between the ceiling and the attic the hatch is for."""
    return ['%s: hatch in the hall soffit, over the air handler and its runs' % h.unit
            for h in hatches if any(rects_overlap(_wh(h.page), _wh(r)) for r in soffit_pages(2))]


def check_roof():
    """Fails the build when a roof line no longer agrees with the plans it is derived from."""
    rooms, devices = _ceilings()
    v = [x for r in ROOFS for x in roof_violations(r, rooms, devices, penetrations(r), truss_oc=TRUSS_OC)]
    v += ['%s: hatch across a truss' % h.unit for h in HATCHES if not between_trusses(h)]
    v += soffit_violations(B1_ROOF.hatches)
    for r in ROOFS:
        for av in attic_vents(r, penetrations(r)):
            print("ROOF %-18s trusses at %g in, %.0f SF attic: vents %d sq in of %d required; hatch %s; caps %s"
                  % (r.name, TRUSS_OC*12, av.attic.area, round(av.provided), round(av.required),
                     ", ".join(h.unit for h in r.hatches), ", ".join(nm for _x, _y, nm in penetrations(r))))
    assert not v, 'ROOF: ' + '; '.join(v)
