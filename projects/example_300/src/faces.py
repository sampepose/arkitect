"""What stands on a drawn elevation face, read from the models that place it.

The elevations typed each face's wall caps beside its elev() call, so a cap the mechanical
model placed on a wall nobody typed never appeared: Building 1's adjacent-parcel wall
carries RH-1, EF-1A and EF-2, and A-202 drew none of them, nor any of the four boxes C-101
puts on that wall. This module lists, for one wall, the terminations src/mechanical.py
places and the service equipment src/sitework.py places at the heights SVC_Z gives it.

Positions are feet ALONG the wall in page feet — the axis mechanical.Wall measures its
openings on — and heights are feet above finished grade. An elevation maps `along` with
the same flip face() applies to its openings.

check_faces() holds what the drawing shows: no box covers a cap, an opening or another
box, and an outdoor unit stands clear of grade.
"""
import math
import re
from collections import namedtuple
from arkitect.lib.units import IN, fmt
from src.mechanical import TERMS, WALLS
from arkitect.codes.ohio.rco.mechanical import CAP_R
from src.sitework import SITE_BLDG, SVC_EQUIP, SVC_Z

HP_GRADE_MIN = IN(4)       # C-101 note 5b

# A box on the wall: along the wall lo..hi, above grade zlo..zhi, and the meter positions
# it holds (none for an outdoor unit).
Box = namedtuple('Box', 'mark lo hi zlo zhi positions what')

# The faces whose equipment an elevation draws: each building's adjacent-parcel wall,
# A-202 and A-203. A-201's faces carry no box but HP-1, which is not drawn.
DRAWN_BOXES = ((1, 'ADJACENT-PARCEL WALL'), (2, 'ADJACENT-PARCEL WALL'))


def face_terms(bldg, wall):
    """The wall caps src/mechanical.py places on this wall."""
    return list(TERMS[bldg].get(wall, []))


BOX_OFF_WALL = IN(3)       # C-101 stands the meter banks 2.4" off the face, on their backboards


def _wall_of_box(e):
    """(building, wall, along) of a SVC_EQUIP row, from its site rectangle."""
    mark, x, y, d, l, _what = e
    for b, (bx, by, W, D) in enumerate(s[:4] for s in SITE_BLDG):
        if not (by-1e-6 <= y and y+l <= by+D+1e-6): continue
        if -1e-6 <= x-(bx+W) <= BOX_OFF_WALL: return b+1, 'ADJACENT-PARCEL WALL', y-by
        if -1e-6 <= bx-(x+d) <= BOX_OFF_WALL: return b+1, 'SAGE WALL', y-by
    raise ValueError('%s stands on no building wall' % mark)


def face_boxes(bldg, wall):
    out = []
    for e in SVC_EQUIP:
        b, w, along = _wall_of_box(e)
        if (b, w) != (bldg, wall): continue
        mark, _x, _y, _d, l, what = e
        if mark not in SVC_Z:
            raise KeyError('%s on the %s has no height in SVC_Z' % (mark, wall.lower()))
        zlo, h = SVC_Z[mark]
        m = re.search(r'(\d+) POSITIONS', what)
        n = int(m.group(1)) if m else 0
        out.append(Box(mark, along, along+l, zlo, zlo+h, n, what))
    return out


def _gap(p, q):
    """The clear gap in the wall plane between two boxes, negative when they overlap."""
    return max(q.lo-p.hi, p.lo-q.hi, q.zlo-p.zhi, p.zlo-q.zhi)


def face_violations():
    bad, lines = [], []
    for e in SVC_EQUIP:
        _wall_of_box(e)
    for bldg, wall in DRAWN_BOXES:
        boxes, terms = face_boxes(bldg, wall), face_terms(bldg, wall)
        lines.append('ELEVATION FACE  BUILDING %d %s: %d caps, %d boxes' % (bldg, wall, len(terms), len(boxes)))
        for i, bx in enumerate(boxes):
            for op in WALLS[bldg][wall].openings:
                if max(op.lo-bx.hi, bx.lo-op.hi, op.zlo-bx.zhi, bx.zlo-op.zhi) < 0:
                    bad.append('%s covers %s' % (bx.mark, op.name))
            for t in terms:
                dx = max(bx.lo-t.along, 0.0, t.along-bx.hi); dz = max(bx.zlo-t.z, 0.0, t.z-bx.zhi)
                if math.hypot(dx, dz) < CAP_R-1e-9: bad.append('%s covers the %s cap' % (bx.mark, t.mark))
            for other in boxes[i+1:]:
                if _gap(bx, other) < 0: bad.append('%s and %s overlap' % (bx.mark, other.mark))
            if bx.mark.startswith('HP-') and bx.zlo < HP_GRADE_MIN-1e-9:
                bad.append('%s is %s above grade, under %s' % (bx.mark, fmt(bx.zlo), fmt(HP_GRADE_MIN)))
            lines.append('   %-5s %s .. %s along, +%s .. +%s' % (bx.mark, fmt(bx.lo), fmt(bx.hi), fmt(bx.zlo), fmt(bx.zhi)))
        for t in terms:
            lines.append('   %-5s cap at %s along, +%s' % (t.mark, fmt(t.along), fmt(t.z)))
    return bad, lines


def check_faces():
    """From build.check_model(): what an elevation draws on a face stands clear, or the
       build stops with the item named."""
    bad, lines = face_violations()
    assert not bad, 'ELEVATION FACES:\n  '+'\n  '.join(bad)
    for ln in lines:
        print(ln)
