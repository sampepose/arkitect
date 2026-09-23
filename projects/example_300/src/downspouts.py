"""Roof drainage: every eave gutter's downspout, where it comes down and where its water
goes. C-101 locates the leaders, C-103 draws each splash block and its receiver, A-201,
A-202 and A-203 draw the leaders on the faces they come down.

Both roofs are front-to-back gables (src/roof.py), so the gutters are on the Sage and
adjacent-parcel eaves of both buildings: four gutters, each carrying half its roof. Each
is pitched to ONE leader at its rear corner, and every leader discharges onto a splash
block on lawn that drains to one of C-103's concrete gutters or, behind Building 2, to
the alley. None discharges toward S Elm or Sage: roof water concentrated at a leader
is kept off the public sidewalks, as the site gutters are.

The Sage side decides the layout. Building 1's Sage wall behind the Unit 3 top
landing is stair — landing, flight, stoop — so its leader turns the rear corner at the
eave and comes down the rear face, beside the stoop. Building 2's Sage wall has the
Unit 3 walk along its whole length, so its leader is on the rear face too.

Site feet, as src/grading.py: x from the Sage lot line, y from the S Elm lot line.
A leader's position on its wall is also given in page feet ALONG the wall, the frame
src/mechanical.py holds openings and terminations in.
"""
import math
from collections import namedtuple
from arkitect.lib.units import IN, fmt, inches
from src import grading as G, mechanical as M
from arkitect.lib.model import grade as grade
from src.building1 import U3_LAND_LO, U3_STOOP_HI
from src.building2 import U5_LAND_D, U5_LAND_X1, U5_STOOP_X0
from src.drainage import BUILDINGS as DRAIN_BUILDINGS, sewer, water_lines
from src.roof import B1_ROOF, B2_ROOF, EAVE_OVERHANG, dripline
from src.sitework import B2_REAR_Y, SITE_D, SITE_STAIR, SITE_W, SVC_EQUIP, WHEEL_STOPS

TOL = 1e-6

# ---------------- the design ----------------
CORNER     = 1.0          # every leader stands this far in from the corner its gutter drains to
CORNER_MAX = 1.5          # a leader on the face round the corner is still at its gutter's end
LEADER_W   = IN(3)        # the leader's width along its wall
LEADER_D   = IN(2)        # and its depth off it
LEADER_CLR = IN(6)        # clear of every opening on its wall, horizontally, at every level
EQUIP_CLR  = 1.0          # from a wall termination, and from a service box
SPLASH_W, SPLASH_L = 1.0, 2.0   # a precast splash block, run out from the wall
TRENCH_CLR = 3.0          # a splash block from the building sewer, the lateral or a water service, in plan
OUTLET_Z   = IN(6)        # the discharge elbow above grade
SIDEWALK_STREETS = ("S ELM", "SAGE")

# ---------------- sizing, OPC 1106 ----------------
# The RCO sends plumbing to the Ohio Plumbing Code (R2501.1), whose 1106.1 sizes gutters
# and leaders on the 100-year hourly rainfall rate: 2.8 in/h at Columbus, IPC Appendix B
# (NOAA Atlas 14 gives 2.82). A roof's flow is its plan area at that rate, equation 11-1.
RAIN = 2.8                 # inches per hour
GUTTER_IN = 5              # each gutter at least a 5" semicircular section
GUTTER_PITCH = 1/8.0       # inches per foot toward its leader: Table 1106.6 has no 1/16" row under 8"
T1106_6 = {(5, 1/8.0): 74, (6, 1/8.0): 110}                 # gpm
# Table 1106.3 lists no 2 x 3 leader, so the one specified is credited at the 2 x 2 row it
# contains, never at a larger one.
LEADER, LEADER_ROW = '2 x 3', '2 x 2'
T1106_3 = {'2': 30, '2 x 2': 30, '1-1/2 x 2-1/2': 30, '2-1/2': 54, '2-1/2 x 2-1/2': 54,
           '3': 92, '2 x 4': 92, '2-1/2 x 3': 92, '4': 192}  # gpm


def flow(area, rain=None):
    """gpm off `area` SF of roof plan: 1 in/h on 96.23 SF is 1 gpm."""
    return (RAIN if rain is None else rain)*area/96.23


# ---------------- the gutters ----------------
# Each gutter runs the eave's full length, rake to rake, and carries half its roof in plan
# to the dripline: the overhangs are roof (src/roof.py). `rakes` are how far the eave runs
# past each end of its wall, in the order extent() gives the wall's ends.
Eave = namedtuple("Eave", "name face length area rakes")


def _eave(name, face, roof):
    x0, y0, x1, y1 = dripline(roof)
    return Eave(name, face, y1-y0, (y1-y0)*(roof.W/2.0+EAVE_OVERHANG), (-y0, y1-roof.D))


EAVES = [_eave("BUILDING 1 SAGE EAVE", G.F_B1_SAFF, B1_ROOF),
         _eave("BUILDING 1 ADJACENT-PARCEL EAVE", G.F_B1_PARCEL, B1_ROOF),
         _eave("BUILDING 2 SAGE EAVE", G.F_B2_SAFF, B2_ROOF),
         _eave("BUILDING 2 ADJACENT-PARCEL EAVE", G.F_B2_PARCEL, B2_ROOF)]

# ---------------- gutter guards ----------------
# Not a code item: OPC 1106 sizes the gutter, not what covers it. Every eave is about
# +20'-10" and nobody will clean it, so each gutter carries a guard its full length. A
# guard that sheds water over the lip in a downpour defeats the gutter, so its published
# rating is held to the lot's short-duration intensity (grading's 10-year 5-minute
# figure, the storm a mesh actually sees), not only 1106.1's hourly rate. Fastened
# below the drip edge: the eave's shingle-over intake vent (S-103 note 7) is at the roof
# edge, and a guard slid under the shingles would cover it and void the shingles.
GUARD = "STAINLESS STEEL MICRO-MESH ON AN ALUMINUM FRAME"
GUARD_RATE_MIN = max(RAIN, G.RAIN_I)      # in/h, the least published rating accepted
GUARDED = tuple(e.name for e in EAVES)     # the full length of every eave gutter


def guard_violations(guarded=None, rate_min=None):
    guarded = GUARDED if guarded is None else guarded
    rate_min = GUARD_RATE_MIN if rate_min is None else rate_min
    v = ["%s: no gutter guard" % e.name for e in EAVES if e.name not in guarded]
    if rate_min < max(RAIN, G.RAIN_I)-TOL:
        v.append("gutter guard rated to %.2f in/h, under the %.2f in/h of the lot" % (rate_min, max(RAIN, G.RAIN_I)))
    return v


# ---------------- the leaders ----------------
Downspout = namedtuple("Downspout", "mark eave face s")
DOWNSPOUTS = [
    Downspout("DS-1", EAVES[0], G.F_B1_REAR, G.B1X0+CORNER),      # round the rear corner, out of the Unit 3 stair
    Downspout("DS-2", EAVES[1], G.F_B1_PARCEL, G.B1Y1-CORNER),
    Downspout("DS-3", EAVES[2], G.F_B2_REAR, G.B2X0+CORNER),      # round the rear corner, off the Unit 3 walk
    Downspout("DS-4", EAVES[3], G.F_B2_PARCEL, G.B2Y1-CORNER),
]

# The stairs, stoop to top landing, as C-101 draws them. (x0, y0, x1, y1)
STAIRS = {"UNIT 3 STAIR": (SITE_STAIR[0], G.B1Y0+U3_LAND_LO, SITE_STAIR[1], G.B1Y0+U3_STOOP_HI),
          "UNIT 5 STAIR": (G.B2X0+U5_STOOP_X0, G.B2Y0-U5_LAND_D, G.B2X0+U5_LAND_X1, G.B2Y0)}

# grading's face names and mechanical's wall names for the same wall
WALL_NAME = {"SAGE FACE": "SAGE WALL", "ADJACENT-PARCEL FACE": "ADJACENT-PARCEL WALL",
             "S ELM FACE": "S ELM WALL", "FACE TO BUILDING 2": "REAR WALL",
             "FACE TO BUILDING 1": "COURTYARD WALL", "REAR FACE": "REAR WALL"}


def _bldg(face):
    return 1 if face.building == "BUILDING 1" else 2


def _origin(face):
    return (G.B1X0, G.B1Y0) if _bldg(face) == 1 else (G.B2X0, G.B2Y0)


def extent(face):
    """A face's two ends, in site feet along it."""
    if _bldg(face) == 1:
        return (G.B1X0, G.B1X1) if face.axis == "x" else (G.B1Y0, G.B1Y1)
    return (G.B2X0, G.B2X1) if face.axis == "x" else (G.B2Y0, G.B2Y1)


def along(face, s):
    """A site station on a face as page feet along its wall, mechanical's frame."""
    ox, oy = _origin(face)
    return s-(ox if face.axis == "x" else oy)


def _rect(face, s, w, d0, d1):
    """The site rectangle `w` wide centered on station s, from d0 to d1 out from the face."""
    (ax, ay), (bx, by) = grade.point(face, s-w/2.0, d0), grade.point(face, s+w/2.0, d1)
    return (min(ax, bx), min(ay, by), max(ax, bx), max(ay, by))


def _band(face, s, bands):
    return next((b for b in bands if b.face == face and b.s0-TOL <= s <= b.s1+TOL), None)


def gutter_run(d):
    """The length of gutter that drains to the leader: from the far end of its eave to the
       point on the eave line nearest the leader. None if the leader is not at its eave —
       on the eave face, or on a face meeting it within CORNER_MAX of the corner."""
    e = d.eave.face
    lo, hi = extent(e)
    if d.face == e:
        p = d.s
    elif d.face.building == e.building and d.face.axis != e.axis and abs(d.s-e.at) <= CORNER_MAX+TOL:
        p = d.face.at
    else:
        return None
    return max(p-(lo-d.eave.rakes[0]), hi+d.eave.rakes[1]-p)


def _seg_rect_dist(a, b, r):
    """Plan distance from segment ab to rectangle r; 0 if they meet."""
    x0, y0, x1, y1 = r
    # Liang-Barsky: does the segment enter the rectangle?
    t0, t1 = 0.0, 1.0
    dx, dy = b[0]-a[0], b[1]-a[1]
    hit = True
    for p, q in ((-dx, a[0]-x0), (dx, x1-a[0]), (-dy, a[1]-y0), (dy, y1-a[1])):
        if abs(p) < TOL:
            if q < 0: hit = False; break
        else:
            t = q/p
            if p < 0: t0 = max(t0, t)
            else: t1 = min(t1, t)
    if hit and t0 <= t1+TOL:
        return 0.0
    def pt_rect(px, py):
        return math.hypot(max(x0-px, 0.0, px-x1), max(y0-py, 0.0, py-y1))
    def pt_seg(px, py):
        L2 = dx*dx+dy*dy
        t = 0.0 if L2 < TOL else max(0.0, min(1.0, ((px-a[0])*dx+(py-a[1])*dy)/L2))
        return math.hypot(px-(a[0]+t*dx), py-(a[1]+t*dy))
    return min([pt_rect(*a), pt_rect(*b)]+[pt_seg(px, py) for px in (x0, x1) for py in (y0, y1)])


def trenches():
    """What is buried outside the buildings, as (name, site polyline): the building sewer,
       Building 2's lateral and each building's water service."""
    sw = sewer()
    out = [("BUILDING SEWER", sw["route"]), ("BUILDING 2 LATERAL", sw["lateral"])]
    for b in DRAIN_BUILDINGS:
        path = dict(water_lines(b))["SERVICE"]
        out.append(("%s WATER SERVICE" % b.name, [(b.site[0]+p[0], b.site[1]+p[1]) for p in path]))
    return out


Discharge = namedtuple("Discharge", "d wall along run band to splash length onto_gutter outlet_z")


def discharge(d, bands=None, gutters=None):
    """Everything a sheet prints of one leader, and what the checker measures."""
    bands = bands or G.BANDS
    gutters = {g.mark: g for g in (gutters or G.GUTTERS)}
    band = _band(d.face, d.s, bands)
    to = band.to if band else None
    length, onto = SPLASH_L, False
    if to in gutters:
        edge = gutters[to].off(*grade.point(d.face, d.s, 0.0))-gutters[to].w/2.0
        if edge < SPLASH_L-TOL:
            length, onto = max(0.0, edge), True
    z = math.ceil(OUTLET_Z*12.0-1e-6)/12.0                 # to the inch above
    return Discharge(d, WALL_NAME[d.face.side], along(d.face, d.s), gutter_run(d), band, to,
                     _rect(d.face, d.s, SPLASH_W, 0.0, length), length, onto, z)


def roof_to(target, dss=None, bands=None, gutters=None):
    """SF of roof plan whose leaders' water reaches `target` — a gutter, an inlet or a lot
       line — following each splash block's receiver down the gutters it discharges into."""
    gl = {g.mark: g for g in (gutters or G.GUTTERS)}
    total = 0.0
    for d in (DOWNSPOUTS if dss is None else dss):
        to, seen = discharge(d, bands, list(gl.values())).to, set()
        while to != target and to in gl and to not in seen:
            seen.add(to); to = gl[to].to
        if to == target:
            total += d.eave.area
    return total


def _terms(bldg):
    seen = {}
    for lv in M.LEVELS:
        if lv.bldg != bldg: continue
        for t in lv.terms:
            if t.wall != "ROOF": seen[t.mark] = t
    return list(seen.values())


def downspout_violations(dss=None, bands=None, gutters=None, paved=None, rain=None, roof_cap=None, stops=None):
    dss = DOWNSPOUTS if dss is None else dss
    bands = bands or G.BANDS
    paved = G.PAVED if paved is None else paved
    gl = list(gutters or G.GUTTERS)
    v = []
    # 1. every eave gutter drains to exactly one leader, at its end, and carries its roof
    for e in EAVES:
        n = [d for d in dss if d.eave == e]
        if len(n) != 1:
            v.append("%s: %d leaders, not one" % (e.name, len(n)))
        q = flow(e.area, rain)
        if q > T1106_6[(GUTTER_IN, GUTTER_PITCH)]+TOL:
            v.append("%s: %.1f gpm, over the %d gpm of Table 1106.6" % (e.name, q, T1106_6[(GUTTER_IN, GUTTER_PITCH)]))
        if q > T1106_3[LEADER_ROW]+TOL:
            v.append("%s: %.1f gpm, over the %d gpm of Table 1106.3's %s row" % (e.name, q, T1106_3[LEADER_ROW], LEADER_ROW))
    for d in dss:
        x = discharge(d, bands, gl)
        who = "%s (%s)" % (d.mark, d.eave.name)
        lo, hi = extent(d.face)
        if not (lo+LEADER_W/2.0-TOL <= d.s <= hi-LEADER_W/2.0+TOL):
            v.append("%s: the leader is off its face" % who); continue
        if x.run is None:
            v.append("%s: the leader is not at the end of its gutter" % who)
        # 2. openings, terminations and service boxes on its wall
        walls = M.b1_walls() if _bldg(d.face) == 1 else M.b2_walls()
        for op in walls[x.wall].openings:
            gap = max(op.lo-(x.along+LEADER_W/2.0), (x.along-LEADER_W/2.0)-op.hi)
            if gap < LEADER_CLR-TOL:
                v.append("%s: %s from the %s, under %s" % (who, inches(max(gap, 0.0)), op.name, inches(LEADER_CLR)))
        for t in _terms(_bldg(d.face)):
            if t.wall == x.wall and abs(t.along-x.along) < EQUIP_CLR-TOL:
                v.append("%s: within %s of %s" % (who, fmt(EQUIP_CLR), t.mark))
        leader = _rect(d.face, d.s, LEADER_W, 0.0, LEADER_D)
        for m, bx, by, bd, bl, _desc in SVC_EQUIP:
            r = (bx, by, bx+bd, by+bl)
            if math.hypot(max(r[0]-leader[2], 0.0, leader[0]-r[2]), max(r[1]-leader[3], 0.0, leader[1]-r[3])) < EQUIP_CLR-TOL:
                v.append("%s: within %s of %s" % (who, fmt(EQUIP_CLR), m))
        # 3. the stairs
        for nm, r in STAIRS.items():
            for what, rr in (("leader", leader), ("splash block", x.splash)):
                if grade._overlaps(rr, r):
                    v.append("%s: the %s is under the %s" % (who, what, nm))
        # 4. what the splash block lands on
        sx0, sy0, sx1, sy1 = x.splash
        if sx0 < -TOL or sy0 < -TOL or sx1 > SITE_W+TOL or sy1 > SITE_D+TOL:
            v.append("%s: the splash block leaves the lot" % who)
        for r in paved:
            if grade._overlaps(x.splash, (r.x0, r.y0, r.x1, r.y1)):
                v.append("%s: the splash block is on the %s" % (who, r.name))
        for g in gl:
            if grade._overlaps(x.splash, g.box()):
                v.append("%s: the splash block is in %s" % (who, g.mark))
        for m, bx, by, bd, bl, _desc in SVC_EQUIP:
            if grade._overlaps(x.splash, (bx, by, bx+bd, by+bl)):
                v.append("%s: the splash block is under %s" % (who, m))
        for cx, cy in G.CLEANOUTS:
            if sx0-G.CO_R < cx < sx1+G.CO_R and sy0-G.CO_R < cy < sy1+G.CO_R:
                v.append("%s: the splash block is on the cleanout at %s, %s" % (who, fmt(cx), fmt(cy)))
        # 5. the trenches
        for nm, path in trenches():
            gap = min(_seg_rect_dist(a, b, x.splash) for a, b in zip(path, path[1:]))
            if gap < TRENCH_CLR-TOL:
                v.append("%s: the splash block is %s from the %s, under %s" % (who, fmt(gap), nm, fmt(TRENCH_CLR)))
        # 6. lawn under the block, and where the lawn drains
        for s in (max(lo, d.s-SPLASH_W/2.0), d.s, min(hi, d.s+SPLASH_W/2.0)):
            b = _band(d.face, s, bands)
            if b is None:
                v.append("%s: no grading band at %s" % (who, fmt(s))); continue
            pts = b.section(s)
            for (d0, _g0, _a), (d1, _g1, kind) in zip(pts, pts[1:]):
                if d0 < x.length-TOL and d1 > d0+TOL and kind != "lawn":
                    v.append("%s: the splash block is on %s, not lawn" % (who, kind)); break
        if x.to is None:
            v.append("%s: its face is not graded there" % who)
        elif x.to in SIDEWALK_STREETS:
            v.append("%s: it discharges toward the %s sidewalk" % (who, x.to))
        # 7. the wheel stops, and the strip between each and Building 2's rear wall
        for i, (wx0, wy0, wx1, wy1) in enumerate(WHEEL_STOPS if stops is None else stops):
            if grade._overlaps(x.splash, (wx0, wy0, wx1, wy1)):
                v.append("%s: the splash block is on wheel stop %d" % (who, i+1))
            elif grade._overlaps(x.splash, (wx0, B2_REAR_Y, wx1, wy0)):
                v.append("%s: the splash block is in the clear strip behind wheel stop %d" % (who, i+1))
    # 8. each inlet's outlet is sized on grading.tributary(): no leader may send it more roof
    cap = G.tributary()[1] if roof_cap is None else roof_cap
    for inlet in G.INLETS:
        r = roof_to(inlet.mark, dss, bands, gl)
        if r > cap+TOL:
            v.append("%s: the leaders send it %s SF of roof, over the %s SF its outlet is sized for"
                     % (inlet.mark, "{:,.0f}".format(r), "{:,.0f}".format(cap)))
    return v


def height(v):
    """A height above grade as a sheet prints it: 6", 2'-4"."""
    return inches(v) if v < 1.0-TOL else fmt(v)


def check_downspouts():
    """One leader at the end of each eave gutter, clear of the openings, terminations,
       stairs, paving and trenches, onto lawn that drains to a site gutter or the alley."""
    print("ROOF DRAINAGE — ONE LEADER PER EAVE GUTTER, SPLASH BLOCK TO GRADE:")
    for inlet in G.INLETS:
        print("   %s receives %s SF of roof from the leaders; its outlet is sized for %s SF (grading.tributary())"
              % (inlet.mark, "{:,.0f}".format(roof_to(inlet.mark)), "{:,.0f}".format(G.tributary()[1])))
    for d in DOWNSPOUTS:
        x = discharge(d)
        print("   %s  %-31s %4.0f SF %4.1f gpm  %s of gutter   leader on %s %s at %s   outlet +%s   %s splash to %s%s"
              % (d.mark, d.eave.name, d.eave.area, flow(d.eave.area), fmt(x.run) if x.run is not None else "?",
                 d.face.building, d.face.side, fmt(d.s), height(x.outlet_z),
                 fmt(x.length), x.to, " (onto its concrete)" if x.onto_gutter else ""))
    print("   GUTTER GUARDS: %s, ALL %d EAVE GUTTERS, RATED NOT LESS THAN %.2f IN/H" % (GUARD, len(GUARDED), GUARD_RATE_MIN))
    v = downspout_violations() + guard_violations()
    assert not v, "downspouts: %s" % v[:6]
