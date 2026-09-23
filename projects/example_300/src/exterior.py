"""The street faces' exterior finish, and the screening of the service equipment.

The designer's picks of 2026-09-16, from a list of low-cost ways to make the buildings look better:

  * TRIM on the three street faces — Building 1's S Elm and Sage faces and Building 2's
    Sage face: flat casings round every window and door, a head casing with a drip cap, a
    frieze board under the eaves, and cedar-look shake siding in Building 1's S Elm gable.
    The other faces keep the siding manufacturer's standard trim.
  * A FLAT DOOR SURROUND at Unit 1's S Elm entry: pilasters and a crosshead on the wall,
    nothing projecting. A canopy was offered and not taken: the door starts 11" from the
    Sage corner, which already stands inside the street-corner vision triangle, so any
    canopy over it would grow that variance and project into the 20'-0" front yard.
  * BLACK window frames on every window, and no grilles.
  * SHRUBS BESIDE THE EQUIPMENT, never in front of it. `SHRUBS` is placed here by rule, one
    at each end of each group of boxes on a wall, and an end with no legal place is dropped
    and printed, not forced: most of the parcel yards are 3'-6" of lawn between the wall and
    the concrete gutter, and several groups stand close to windows.

Sizes are the set's own, not a product's. Page feet along a wall as src/mechanical.py and
src/faces.py measure it; site feet as src/grading.py.
"""
import math
from collections import namedtuple
from arkitect.lib.units import IN, fmt

# ---------------- the trim package ----------------
# (building, wall) as src/mechanical.py names walls.
STREET_FACES = ((1, 'S ELM WALL'), (1, 'SAGE WALL'), (2, 'SAGE WALL'))
CASING_W     = IN(3.5)       # 1x4 flat casing, sides and sill
HEAD_CASING  = IN(5.5)       # 1x6 head casing
HEAD_EAR     = IN(0.75)      # the head casing runs past each side casing
DRIP_CAP     = IN(1.5)       # metal drip cap over the head casing
FRIEZE       = IN(7.25)      # 1x8 frieze board under the soffit
CORNER_BOARD = IN(3.5)       # 1x4 each side of a street-face corner
TRIM_MATERIAL = 'CELLULAR PVC'
GABLE_ACCENT = {('BUILDING 1', 'S ELM AVENUE'): 'CEDAR-LOOK SHAKE SIDING'}
SHAKE_COURSE = IN(7)         # exposure, as the elevation draws the courses

# ---------------- Unit 1's door surround ----------------
SURROUND_UNIT      = 'UNIT 1'
SURROUND_PILASTER  = IN(4.5)
SURROUND_CROSSHEAD = IN(9.25)    # 1x10 crosshead
SURROUND_CAP_EAR   = IN(1.5)     # the crosshead's cap past each pilaster
SIDING_MIN         = IN(2)       # siding left between the pilaster and the corner board

# ---------------- windows ----------------
WINDOW_COLOUR = 'BLACK EXTERIOR FRAME AND SASH'
WINDOW_GRILLES = None

# ---------------- screening ----------------
SHRUB_D     = IN(24)         # maintained diameter
SHRUB_H_MAX = IN(42)         # maintained height
SHRUB_OFF   = IN(3)          # the shrub's edge off the siding
SHRUB_SPECIES = 'DWARF EVERGREEN'
# Clear zones round each box: (in front, each side). A meter bank keeps 3'-0" in front for
# the utility; an outdoor unit keeps 2'-0" in front and 1'-0" each side for its airflow.
BOX_CLEAR = {'EM': (IN(36), IN(3)), 'HP': (IN(24), IN(12))}
CAP_CLR     = IN(36)         # a shrub stays this far along the wall from a wall cap
CAP_Z_MAX   = 8.0            # ... that is below this: a dryer or range hood cap, not a bath fan's at ~10'-0"
GROUP_GAP   = IN(30)         # boxes this close on a wall screen as one group

Shrub = namedtuple('Shrub', 'group end bldg wall along x y')
Box = namedtuple('Box', 'mark lo hi depth')


def _kind(mark):
    return mark.split('-')[0]


def groups():
    """[(bldg, wall, [Box])] — each wall's boxes, in runs no more than GROUP_GAP apart. A box
       is (mark, lo, hi, depth) along the wall; no height is needed, so HP-1 counts too."""
    from src.faces import _wall_of_box
    from src.sitework import SVC_EQUIP
    by_wall = {}
    for e in SVC_EQUIP:
        bldg, wall, along = _wall_of_box(e)
        by_wall.setdefault((bldg, wall), []).append(Box(e[0], along, along+e[4], e[3]))
    out = []
    for (bldg, wall), boxes in sorted(by_wall.items()):
        boxes.sort(key=lambda b: b.lo)
        run = [boxes[0]]
        for b in boxes[1:]:
            if b.lo-run[-1].hi <= GROUP_GAP+1e-9:
                run.append(b)
            else:
                out.append((bldg, wall, run)); run = [b]
        out.append((bldg, wall, run))
    return out


def _boxes(bldg, wall):
    return [box for b, w, run in groups() if (b, w) == (bldg, wall) for box in run]


def _site(bldg, wall, along, out):
    """A point `out` feet off a side wall's face, `along` feet along it, in site feet."""
    from src.sitework import SITE_BLDG
    bx, by, W, _D = SITE_BLDG[bldg-1][:4]
    if wall == 'ADJACENT-PARCEL WALL':
        return bx+W+out, by+along
    if wall == 'SAGE WALL':
        return bx-out, by+along
    raise ValueError('no screening on the %s' % wall.lower())


def _circle_rect(cx, cy, r, x0, y0, x1, y1):
    dx = max(x0-cx, 0.0, cx-x1); dy = max(y0-cy, 0.0, cy-y1)
    return math.hypot(dx, dy) < r-1e-9


def violations(bldg, wall, along, boxes=None):
    """Why a shrub centered `along` a wall at the standard offset may not stand there."""
    from src import downspouts as DS, grading as G
    from src.mechanical import TERMS, WALLS
    from src.sitework import LOT_W, SITE_D, VISION, VISION_ST
    r = SHRUB_D/2.0; out = SHRUB_OFF+r
    cx, cy = _site(bldg, wall, along, out)
    bad = []
    for op in WALLS[bldg][wall].openings:
        if op.zlo >= CAP_Z_MAX:          # a Level 2 opening: nothing a shrub can reach
            continue
        low = op.zlo < SHRUB_H_MAX+IN(6)
        if (low or 'W-A' in op.name or 'DOOR' in op.name) and along+r > op.lo+1e-9 and along-r < op.hi-1e-9:
            bad.append('in front of %s' % op.name)
    for t in TERMS[bldg].get(wall, []):
        if t.z < CAP_Z_MAX and abs(t.along-along) < CAP_CLR+r-1e-9:
            bad.append('within %s of %s' % (fmt(CAP_CLR), t.mark))
    for b in (_boxes(bldg, wall) if boxes is None else boxes):
        front, side = BOX_CLEAR[_kind(b.mark)]
        if along+r > b.lo-side+1e-9 and along-r < b.hi+side-1e-9 and SHRUB_OFF < b.depth+front:
            bad.append('in %s\'s clear zone' % b.mark)
    if not (r <= cx <= LOT_W-r and r <= cy <= SITE_D-r):
        bad.append('off the lot')
    for rect in G.PAVED:
        if _circle_rect(cx, cy, r, rect.x0, rect.y0, rect.x1, rect.y1): bad.append('on the %s' % rect.name.lower())
    for g in G.GUTTERS:
        if _circle_rect(cx, cy, r, *g.box()): bad.append('on %s' % g.mark)
    for d in DS.DOWNSPOUTS:
        if _circle_rect(cx, cy, r, *DS.discharge(d).splash): bad.append("on %s's splash block" % d.mark)
    for nm, rect in DS.STAIRS.items():
        if _circle_rect(cx, cy, r, *rect): bad.append('under the %s' % nm.lower())
    # the two clear vision triangles: S Elm / Sage at the front, Sage / alley at the rear
    if (cx+cy-r*math.sqrt(2.0)) < VISION_ST or (cx+(SITE_D-cy)-r*math.sqrt(2.0)) < VISION:
        bad.append('in a clear vision triangle')
    return bad


def place():
    """(SHRUBS, DROPPED): a shrub at each end of each group where one may stand, and the
       ends where none may, with the reasons."""
    shrubs, dropped = [], []
    r = SHRUB_D/2.0
    for bldg, wall, run in groups():
        marks = '/'.join(b.mark for b in run)
        lo, hi = run[0], run[-1]
        for end, along in (('LOW', lo.lo-BOX_CLEAR[_kind(lo.mark)][1]-r),
                           ('HIGH', hi.hi+BOX_CLEAR[_kind(hi.mark)][1]+r)):
            bad = violations(bldg, wall, along)
            if bad:
                dropped.append((marks, end, bad))
            else:
                x, y = _site(bldg, wall, along, SHRUB_OFF+r)
                shrubs.append(Shrub(marks, end, bldg, wall, along, x, y))
    return shrubs, dropped


SHRUBS, DROPPED = place()


def door_surround_fits(door_hi, face_w):
    """Siding left between Unit 1's pilaster and the corner board, in feet."""
    return face_w-CORNER_BOARD-(door_hi+SURROUND_PILASTER)


def check_exterior():
    """From build.check_model(): every placed shrub stands where the rules allow, and the
       door surround leaves siding between itself and the corner board. Prints what it holds
       and every equipment end left unscreened."""
    from src.building1 import ENTRY_LEFT
    bad = [(s.group, s.end, violations(s.bldg, s.wall, s.along)) for s in SHRUBS]
    bad = [b for b in bad if b[2]]
    assert not bad, 'SCREENING: %s' % bad
    left = door_surround_fits(26.0-ENTRY_LEFT, 26.0)
    assert left >= SIDING_MIN-1e-9, "Unit 1's door surround leaves %s of siding at the corner board" % fmt(left)
    print('EXTERIOR: street-face trim on %s; Unit 1 surround leaves %s of siding at the corner board'
          % (', '.join('building %d %s' % (b, w.lower()) for b, w in STREET_FACES), fmt(left)))
    print('SCREENING: %d shrubs' % len(SHRUBS))
    for s in SHRUBS:
        print('   SS  %-14s %-4s end   site x %s y %s' % (s.group, s.end, fmt(s.x), fmt(s.y)))
    for marks, end, why in DROPPED:
        print('   --  %-14s %-4s end   none: %s' % (marks, end, '; '.join(sorted(set(why)))))
