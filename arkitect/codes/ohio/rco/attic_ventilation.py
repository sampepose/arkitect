"""RCO 806.2, attic ventilation: the eave and ridge slots an attic's roof can take and
what they give against the 1/150 it needs.

A project hands vent_runs() / attic_vents() its Roof record and its roof penetrations; the
slots stop short of a gable, at any band of the roof where no vent may be cut, and either
side of a penetration near their line.
"""
from collections import namedtuple
from arkitect.lib.units import IN


VENT_RATIO = 150            # RCO R806.2: net free area 1/150 of the attic floor


EAVE_NFA   = 9.0            # sq in per foot, the least a shingle-over eave intake vent may be rated, note 7


RIDGE_NFA  = 18.0           # sq in per foot, the least a ridge vent may be rated, note 7


SLOT_STOP  = IN(12)         # a vent slot stops this far short of a gable end


VENT_CLR   = IN(12)         # a roof penetration this close to a slot's line breaks the slot this far either side


Attic = namedtuple('Attic', 'name y0 y1 area nfa')                    # y0, y1: its extent along the ridge; sf, sf


Run   = namedtuple('Run', 'kind attic x y0 y1')                       # a vent slot along page y at page x


AtticVent = namedtuple('AtticVent', 'attic eave_lf ridge_lf intake exhaust provided required')   # lf, lf, sq in


def _attic(name, W, y0, y1):
    area = W*(y1-y0)
    return Attic(name, y0, y1, area, area/VENT_RATIO)


def _cut(spans, lo, hi):
    """spans with the interval lo..hi taken out."""
    out = []
    for a, b in spans:
        if hi <= a or lo >= b:
            out.append((a, b)); continue
        if lo > a: out.append((a, lo))
        if hi < b: out.append((hi, b))
    return out


def vent_runs(roof, pens):
    """Each attic's eave and ridge slots: its extent along the ridge, SLOT_STOP short of
       a gable end, less the W4 band, less VENT_CLR either side of any penetration
       within VENT_CLR of the slot's line."""
    ends = [y for y, _nm in roof.gables]
    at_end = lambda y: any(abs(y-g) < 1e-9 for g in ends)
    runs = []
    for a in roof.attics:
        lo = a.y0+(SLOT_STOP if at_end(a.y0) else 0.0)
        hi = a.y1-(SLOT_STOP if at_end(a.y1) else 0.0)
        for kind, x in (('EAVE', 0.0), ('RIDGE', roof.ridge_x), ('EAVE', roof.W)):
            spans = [(lo, hi)] if hi > lo else []
            if roof.w4_band:
                spans = _cut(spans, *roof.w4_band)
            for px, py, _nm in pens:
                if abs(px-x) < VENT_CLR:
                    spans = _cut(spans, py-VENT_CLR, py+VENT_CLR)
            runs += [Run(kind, a.name, x, y0, y1) for y0, y1 in spans if y1-y0 > 1e-9]
    return runs


def attic_vents(roof, pens):
    """Per attic: the eave and ridge slot lengths, the intake and exhaust they give at
       the stated ratings, their sum and 806.2's requirement, all in sq in."""
    runs = vent_runs(roof, pens); out = []
    for a in roof.attics:
        eave = sum(u.y1-u.y0 for u in runs if u.attic == a.name and u.kind == 'EAVE')
        ridge = sum(u.y1-u.y0 for u in runs if u.attic == a.name and u.kind == 'RIDGE')
        out.append(AtticVent(a, eave, ridge, eave*EAVE_NFA, ridge*RIDGE_NFA,
                             eave*EAVE_NFA+ridge*RIDGE_NFA, a.nfa*144.0))
    return out
