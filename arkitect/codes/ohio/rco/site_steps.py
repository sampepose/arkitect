"""RCO 311.7 where a dwelling meets the ground: the one step off every open side of a landing
or stoop, and an exterior stair's bottom riser over a stoop that falls across its flight.

A project hands these its own steps, bands and stairs (arkitect/lib/model/grade.py's records) and the
height it holds a stoop's foot at where no band grades it.
"""
from arkitect.lib.units import IN, inches
from arkitect.lib.model.grade import LANDING_MAX, TOL, edge_points, grade_at, top_at

RISER_MAX       = IN(8.25)            # 311.7.5.1 as Ohio adopts it (the IRC's is 7-3/4")
RISER_VARIATION = IN(0.375)           # 311.7.5.1: the greatest riser over the smallest in a flight
TREAD_PITCH_MAX = 0.02                # 311.7.7: the walking surface of treads and landings


def feet(steps, bands, stoop_step):
    """(step, side, x, y, nosing top, foot grade, held) for every sample of every open side."""
    out = []
    for st in steps:
        for side, (lo, hi) in st.edges.items():
            for nx, ny, fx, fy in edge_points(st.rect, side, lo, hi):
                top = top_at(st, nx, ny)
                foot = grade_at(fx, fy, bands); held = foot is None and st.rect.kind == "stoop"
                out.append((st, side, nx, ny, top, top-stoop_step if held else foot, held))
    return out


def step_summary(steps, bands, stoop_step):
    """(name, top at the face, nosing range, foot range, step range, walk foot) per landing and stoop."""
    rows = []
    fs = feet(steps, bands, stoop_step)
    for st in steps:
        mine = [f for f in fs if f[0] is st and f[5] is not None]
        rng = lambda vals: (min(vals), max(vals))
        walk = [f for f in mine if f[1] == st.walk]
        mid = walk[len(walk)//2]
        rows.append((st.rect.name, st.top, rng([f[4] for f in mine]), rng([f[5] for f in mine]),
                     rng([f[4]-f[5] for f in mine]), (mid[2], mid[3], mid[5], st.walk)))
    return rows


def stair_risers(stairs, steps):
    """(name, pitch, the bottom riser at each foot along the flight's width): the nosing of
       the pitched bottom tread over the stoop's surface beneath it."""
    out = []
    for name, stair, stoop, side in stairs:
        st = next(s for s in steps if s.rect is stoop)
        rs = []
        for nx, ny, _fx, _fy in edge_points(stoop, side):
            w = ((ny if st.face.axis == "x" else nx)-st.face.at)*st.face.sign
            rs.append(stair.stoop_above_grade+stair.riser-w*stair.pitch-top_at(st, nx, ny))
        out.append((name, stair.pitch, rs))
    return out


def stair_violations(stairs, steps):
    v = []
    for name, pitch, rs in stair_risers(stairs, steps):
        if abs(pitch-LANDING_MAX) > TOL:
            v.append("%s: treads and landings pitch %.1f%%, not the stoop's %.1f%%" % (name, 100*pitch, 100*LANDING_MAX))
        if pitch > TREAD_PITCH_MAX+TOL:
            v.append("%s: treads and landings pitch %.1f%%, over the 2%% of 311.7.7" % (name, 100*pitch))
        if max(rs)-min(rs) > RISER_VARIATION+TOL:
            v.append("%s: its bottom riser runs %s to %s across the flight, over 3/8\" apart (311.7.5.1)"
                     % (name, inches(min(rs)), inches(max(rs))))
        if max(rs) > RISER_MAX+TOL:
            v.append("%s: a bottom riser of %s, over %s (311.7.5.1)" % (name, inches(max(rs)), inches(RISER_MAX)))
    return v
