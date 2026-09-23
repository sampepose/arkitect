"""The electrical model: what E-101 and E-102 draw, and the loads P-601 prints.

Devices are authored here in each unit's own coordinates — the system its furniture
uses — and checked against NEC 2023 (OAC 4101:8-34-01, effective 2024-04-15) before
anything draws. The 220.82 table lives here so P-601 and the E-sheets print one number.
"""


# def nec220_82(: shared, see codes/nec/load.py
from codes.nec.load import nec220_82


# name, floor area SF, range VA, dryer VA, dishwasher VA, water heater VA, heat pump VA
# at MCA, panel A. The water heater is the storage heater of P-601 note 6: two 4,500 W
# non-simultaneous elements, so 4,500 VA whether the dwelling takes the 40-gallon tank
# or Unit 1's 50-gallon one. It sits in 220.82(B)(3) with the other fastened-in-place
# appliances, not in (C) — there is no electric space heating anywhere in this project.
WH_VA = 4500
NEC_UNITS = [("UNIT 1",      1248, 12000, 5000, 1200, WH_VA, 7200, 125),
             ("UNITS 2 / 3",  624, 12000, 5000, 1200, WH_VA, 4800, 100),
             ("UNITS 4 / 5",  728, 12000, 5000,    0, WH_VA, 4800, 100)]


# ================================ the types: shared, see codes/nec/dwelling.py
from codes.nec.dwelling import (LUM, Level, OUTLETS, UnitType, WIRE_AMPS, check_unit, ckt, dev, panel_spaces)


# ================================ this project's dwellings ================================
# ============================ Units 2 and 3 ============================
# In the reflected model feet F_U23 is authored in: the bedrooms at x 0.5–11.5, the
# bath, kitchen and mechanical closet at x 11.9–25.5, the W4 line at y 24.45, the rear
# wall at y 47.5. The live wall (x 25.5) faces Sage. Drawn twice — Unit 2 on Level 1,
# Unit 3 on Level 2 — so one list serves both, and the exterior receptacle beside the
# door serves Unit 2's grade entry and Unit 3's landing.
from src.building1 import (F_U23, L1_DOORS, L1_OPENINGS, LIVE_WALL_X, OA_U23, U23, U2_ENTRY,
                           U3_LAND_HI, U3_LAND_LO)

CIRCUITS_U23 = [
    ckt(1,  'LIVING / KITCHEN LIGHTING, ALARMS, BATH FAN',    15, 1, '#14', 'AFCI',      'ltg'),
    ckt(2,  'LIVING / DINING RECEPTACLES',                    20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(3,  'BEDROOMS 1 AND 2, RECEPTACLES AND LIGHTING',     20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(4,  'BATHROOM RECEPTACLE',                            20, 1, '#12', 'GFCI',      'bath'),
    ckt(5,  'KITCHEN SMALL APPLIANCE 1',                      20, 1, '#12', 'AFCI/GFCI', 'sa'),
    ckt(6,  'KITCHEN SMALL APPLIANCE 2',                      20, 1, '#12', 'AFCI/GFCI', 'sa'),
    ckt(7,  'LAUNDRY',                                        20, 1, '#12', 'AFCI/GFCI', 'laundry'),
    ckt(8,  'DISHWASHER',                                     20, 1, '#12', 'AFCI/GFCI', 'dw'),
    ckt(9,  'REFRIGERATOR',                                   20, 1, '#12', 'AFCI/GFCI', 'dw'),
    ckt(10, 'RANGE',                                          50, 2, '#6',  '—',         'range'),
    ckt(11, 'DRYER',                                          30, 2, '#10', '—',         'dryer'),
    ckt(12, 'HEAT PUMP HP-2 / HP-3: MCA 20 A, MOCP 25 A',     25, 2, '#12', '—',         'hp', mca=20, mocp=25),
    ckt(13, 'WATER HEATER',                                   30, 2, '#10', '—',         'wh'),
    ckt(14, 'ENTRY LUMINAIRE',                                15, 1, '#14', 'AFCI',      'ltg'),
]

# (x, y, kind, mount, circuit, tag). 'w5' is the chase face along the W4 line.
E_U23 = [
    # --- Bedroom 1: x 0.5–11.5, y 24.45–35.75; the bed heads on the chase wall
    dev(1.5, 24.45, 'dup', 'w5', 3), dev(8.5, 24.45, 'dup', 'w5', 3),
    dev(0.5, 30.5, 'dup', 'w', 3), dev(7.0, 35.75, 'dup', 's', 3), dev(11.5, 32.2, 'dup', 'e', 3),
    dev(5.5, 30.0, 'lt', 'c', 3, 'A'), dev(11.5, 35.0, 'sw', 'e', 3, 'A'),
    dev(5.5, 32.5, 'sd', 'c', 1), dev(0.5, 33.5, 'head', 'w', 12),
    # --- Bedroom 2: x 0.5–11.5, y 36.15–47.5; its closet notch at x 9.5–11.5, y 40.6–47.5
    dev(9.0, 36.15, 'dup', 'n', 3), dev(1.5, 36.15, 'dup', 'n', 3),
    dev(0.5, 42.0, 'dup', 'w', 3), dev(5.0, 47.5, 'dup', 's', 3), dev(11.5, 40.0, 'dup', 'e', 3),
    dev(5.5, 42.0, 'lt', 'c', 3, 'B'), dev(11.5, 39.6, 'sw', 'e', 3, 'B'),
    dev(5.5, 44.5, 'sd', 'c', 1), dev(0.5, 40.0, 'head', 'w', 12),       # ahead of the rear W-A, not across it
    # --- Bath: x 11.9–16.9, y 24.45–31.55; the lavatory at the door end of the east wall
    dev(16.9, 29.0, 'gfci', 'e', 4),
    dev(14.4, 28.6, 'rec', 'c', 1, 'C'), dev(15.4, 31.55, 'sw', 's', 1, 'C'),
    dev(14.4, 26.2, 'fanc', 'c', 1, 'F'), dev(15.9, 31.55, 'sw', 's', 1, 'F'),
    # --- Kitchen, on the chase: counter 19.8–25.5 with the range at 20.2–22.7, fridge 17.3–19.8
    dev(24.1, 24.45, 'gfci', 'w5', 5), dev(21.45, 24.45, 'range', 'w5', 10), dev(18.5, 24.45, 'fridge', 'w5', 9),
    # --- and on the live wall: counter y 26.45–32.2, sink 27.7–30.2 in it, dishwasher under 30.2–32.2
    dev(25.5, 27.0, 'gfci', 'e', 6), dev(25.5, 31.5, 'gfci', 'e', 5), dev(25.5, 30.6, 'dw', 'e', 8),
    dev(17.3, 29.0, 'gfci', 'w', 6),
    dev(21.0, 26.7, 'rec', 'c', 1, 'D'), dev(24.0, 29.6, 'rec', 'c', 1, 'D'), dev(17.3, 31.5, 'sw', 'w', 1, 'D'),
    # --- Living / dining: the door in the live wall at y 32.51–35.51
    dev(13.2, 31.95, 'dup', 'n', 2), dev(11.9, 41.5, 'dup', 'w', 2),
    dev(17.55, 46.0, 'dup', 'w', 2), dev(21.5, 47.5, 'dup', 's', 2),
    dev(25.5, 44.0, 'dup', 'e', 2), dev(25.5, 38.0, 'dup', 'e', 2),
    dev(19.5, 36.5, 'lt', 'c', 1, 'E'), dev(19.5, 42.0, 'lt', 'c', 1, 'E'), dev(25.5, 36.3, 'sw', 'e', 1, 'E'),
    dev(13.5, 36.0, 'sd', 'c', 1), dev(13.5, 38.2, 'co', 'c', 1),
    dev(25.5, 41.0, 'head', 'e', 12),
    dev(11.9, 39.0, 'tstat', 'w', 12),                 # the wall control on the bedroom partition, RCO 1103.1
    # --- Mechanical closet: x 11.9–17.15, y 44.3–47.5; W/D at the east end, heater on the rear wall
    dev(16.2, 47.5, 'gfci', 's', 7), dev(14.4, 47.5, 'dryer', 's', 11), dev(12.6, 47.5, 'wh', 's', 13),
    dev(14.5, 45.7, 'lt', 'c', 1, 'G'), dev(11.9, 46.5, 'sw', 'w', 1, 'G'),
    dev(11.9, 45.05, 'panel', 'w'),
    # --- Exterior, on the live wall: the entry luminaire beside the door, switched inside;
    #     the receptacle on the landing side of the jamb
    dev(25.5, 31.3, 'ext', 'w', 14, 'X'), dev(25.5, 35.9, 'sw', 'e', 14, 'X'), dev(25.5, 32.2, 'wp', 'w', 2),
]


def _f23(kind):
    return [f[:4] for f in F_U23 if f[4] == kind]


def _open_name(labs):
    return labs[0][2] if len(labs) == 1 else ' / '.join(l[2] for l in labs)


def _u23_level():
    door_mid = (LIVE_WALL_X, U2_ENTRY[1]+U2_ENTRY[2]/2.0)
    return Level('UNITS 2 / 3', E_U23,
                 rooms=[r[:5] for r in U23],
                 polys=[(pts, _open_name(labs)) for pts, labs in OA_U23],
                 doors=[d[:4] for d in L1_DOORS]+list(L1_OPENINGS),
                 ext_req=[(door_mid[0], door_mid[1], 'the entry door'),
                          (LIVE_WALL_X, (U3_LAND_LO+U3_LAND_HI)/2.0, "the Unit 3 landing")],
                 counters=_f23('counter'), dividers=_f23('range')+_f23('sink'),
                 kitchens=[(17.3, 24.45, 25.5-17.3, 31.95-24.45)],
                 lavs=_f23('lav'), wds=_f23('wd'), sinks=_f23('sink'), sep_y=24.45)


LEVEL_U23 = _u23_level()
UNIT_23 = UnitType('UNITS 2 / 3', 100, [LEVEL_U23], CIRCUITS_U23, stacked=True)


# ============================ Units 4 and 5 ============================
# Building 2's model feet, F_B2's: the courtyard face is y 0.5, the rear wall y 27.5,
# Sage x 25.5 (the mechanical closet's wall) and the adjacent parcel x 0.5. The
# living room is on the parcel side, the kitchen and dining on Sage's, the bedrooms
# behind the bearing wall at y 15.0–15.4. Unit 4 is Level 1, Unit 5 Level 2, the same
# plan; Unit 4 alone owes a rear receptacle at grade, 210.52(E)(1).
from src.building2 import B2U, B2doors, B2op, F_B2, OA_B2, U5_LAND_X0, U5_LAND_X1, B2_W

CIRCUITS_U45 = [
    ckt(1,  'LIVING / KITCHEN / HALL LIGHTING, ALARMS, BATH FAN', 15, 1, '#14', 'AFCI',      'ltg'),
    ckt(2,  'LIVING / DINING RECEPTACLES',                        20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(3,  'BEDROOMS 1 AND 2, RECEPTACLES AND LIGHTING',         20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(4,  'BATHROOM RECEPTACLE',                                20, 1, '#12', 'GFCI',      'bath'),
    ckt(5,  'KITCHEN SMALL APPLIANCE 1',                          20, 1, '#12', 'AFCI/GFCI', 'sa'),
    ckt(6,  'KITCHEN SMALL APPLIANCE 2',                          20, 1, '#12', 'AFCI/GFCI', 'sa'),
    ckt(7,  'LAUNDRY',                                            20, 1, '#12', 'AFCI/GFCI', 'laundry'),
    ckt(8,  'REFRIGERATOR',                                       20, 1, '#12', 'AFCI/GFCI', 'dw'),
    ckt(9,  'RANGE',                                              50, 2, '#6',  '—',         'range'),
    ckt(10, 'DRYER',                                              30, 2, '#10', '—',         'dryer'),
    ckt(11, 'HEAT PUMP HP-4 / HP-5: MCA 20 A, MOCP 25 A',         25, 2, '#12', '—',         'hp', mca=20, mocp=25),
    ckt(12, 'WATER HEATER',                                       30, 2, '#10', '—',         'wh'),
    ckt(13, 'ENTRY LUMINAIRE',                                    15, 1, '#14', 'AFCI',      'ltg'),
]

E_U45 = [
    # --- Living, parcel side: the entry door at x 2.01–5.01 on the courtyard wall, W-A beside it
    dev(9.5, 0.5, 'dup', 'n', 2), dev(0.5, 2.0, 'dup', 'w', 2), dev(0.5, 5.5, 'dup', 'w', 2),
    dev(0.5, 12.0, 'dup', 'w', 2), dev(6.0, 15.0, 'dup', 's', 2), dev(18.5, 15.0, 'dup', 's', 2),
    dev(6.0, 4.5, 'lt', 'c', 1, 'A'), dev(6.0, 11.0, 'lt', 'c', 1, 'A'), dev(1.6, 0.5, 'sw', 'n', 1, 'A'),
    dev(0.5, 10.0, 'head', 'w', 11),                 # past the 5'-0" W-C, not across it
    dev(21.7, 12.0, 'tstat', 'e', 11),               # the wall control on the mech closet's face, RCO 1103.1
    # --- Kitchen and dining, Sage side: counter 15.8–25.5 on the courtyard wall with the
    #     range at 20.5–23.0, the fridge 12.7–15.7; the Sage counter y 2.5–8.5, sink 3.25–5.75
    dev(16.8, 0.5, 'gfci', 'n', 5), dev(19.6, 0.5, 'gfci', 'n', 6), dev(24.2, 0.5, 'gfci', 'n', 5),
    dev(21.75, 0.5, 'range', 'n', 9), dev(14.2, 0.5, 'fridge', 'n', 8),
    dev(25.5, 7.1, 'gfci', 'e', 6), dev(23.5, 9.1, 'gfci', 's', 6),
    dev(19.0, 4.5, 'rec', 'c', 1, 'B'), dev(23.0, 7.0, 'rec', 'c', 1, 'B'), dev(21.7, 9.6, 'sw', 'e', 1, 'B'),
    # --- Mechanical closet: x 22.1–25.5, y 9.5–15.0; the W/D across the top, the heater and
    #     the panel on the Sage wall, the louvered pair on the closet's west wall
    dev(23.5, 9.5, 'gfci', 'n', 7), dev(24.6, 9.5, 'dryer', 'n', 10), dev(24.0, 15.0, 'wh', 's', 12),
    dev(23.8, 12.6, 'lt', 'c', 1, 'M'), dev(22.1, 14.7, 'sw', 'w', 1, 'M'),
    dev(25.25, 12.4, 'panel', 'e'),
    # --- Hall: x 10.5–15.5, y 15.4–18.9, open to the living room; under 10', no receptacle
    dev(13.0, 17.0, 'lt', 'c', 1, 'H'), dev(11.5, 18.9, 'sw', 's', 1, 'H'),
    dev(12.2, 16.3, 'sd', 'c', 1), dev(13.8, 16.3, 'co', 'c', 1),
    # --- Bath: x 10.5–15.5, y 19.3–27.5; the lavatory at the door end of the west wall, facing
    #     the door strip, its receptacle on that wall at the counter's end; the tub across the rear
    dev(10.5, 21.0, 'gfci', 'w', 4),
    dev(13.0, 21.0, 'rec', 'c', 1, 'C'), dev(13.0, 24.0, 'rec', 'c', 1, 'C'), dev(15.5, 19.9, 'sw', 'e', 1, 'C'),
    dev(13.0, 22.6, 'fanc', 'c', 1, 'F'), dev(15.5, 20.5, 'sw', 'e', 1, 'F'),
    # --- Bedroom 1, parcel side: x 0.5–10.1, y 15.4–27.5; closet notch x 8.1–10.1, y 21.1–27.5
    dev(3.0, 15.4, 'dup', 'n', 3), dev(8.0, 15.4, 'dup', 'n', 3), dev(0.5, 21.0, 'dup', 'w', 3),
    dev(4.0, 27.5, 'dup', 's', 3), dev(10.1, 19.8, 'dup', 'e', 3),
    dev(5.0, 21.0, 'lt', 'c', 3, 'D'), dev(10.1, 19.0, 'sw', 'e', 3, 'D'),
    dev(5.0, 19.0, 'sd', 'c', 1), dev(0.5, 18.5, 'head', 'w', 11),
    # --- Bedroom 2, Sage side: x 15.9–25.5, y 15.4–27.5; closet notch x 15.9–17.9, y 21.1–27.5
    dev(18.0, 15.4, 'dup', 'n', 3), dev(23.0, 15.4, 'dup', 'n', 3), dev(25.5, 21.0, 'dup', 'e', 3),
    dev(22.0, 27.5, 'dup', 's', 3), dev(15.9, 19.8, 'dup', 'w', 3),
    dev(21.0, 21.0, 'lt', 'c', 3, 'E'), dev(15.9, 19.0, 'sw', 'w', 3, 'E'),
    dev(21.0, 19.0, 'sd', 'c', 1), dev(25.5, 18.5, 'head', 'e', 11),
    # --- Exterior, on the courtyard face beside the door: the luminaire, switched inside, and
    #     the receptacle in the jamb space at the landing's end
    dev(1.3, 0.5, 'ext', 's', 13, 'X'), dev(1.2, 0.5, 'sw', 'n', 1, 'X'), dev(1.85, 0.5, 'wp', 's', 2),
]
# Unit 4 alone: the rear receptacle at grade, behind Bedroom 2's closet
E_U4_ONLY = [dev(16.8, 27.5, 'wp', 'n', 2)]


def _f45(kind):
    return [f[:4] for f in F_B2 if f[4] == kind]


def _u45_level(name, devices, ext_req):
    return Level(name, devices,
                 rooms=[r[:5] for r in B2U],
                 polys=[(pts, _open_name(labs)) for pts, labs in OA_B2],
                 doors=[d[:4] for d in B2doors]+[o[:4] for o in B2op],
                 ext_req=ext_req,
                 counters=_f45('counter'), dividers=_f45('range')+_f45('sink'),
                 kitchens=[(12.7, 0.5, 25.5-12.7, 9.1-0.5)],
                 lavs=_f45('lav'), wds=_f45('wd'), sinks=_f45('sink'), sep_y=None)


_B2_DOOR = B2doors[0]
_B2_DOOR_MID = (_B2_DOOR[0]+_B2_DOOR[2]/2.0, _B2_DOOR[1])
_U5_LAND_MID = (B2_W-(U5_LAND_X0+U5_LAND_X1)/2.0, 0.5)     # the landing's centre on the wall, model x
LEVEL_U4 = _u45_level('UNIT 4', E_U45+E_U4_ONLY,
                      [(_B2_DOOR_MID[0], _B2_DOOR_MID[1], 'the entry door'), (13.0, 27.5, 'the rear wall')])
LEVEL_U5 = _u45_level('UNIT 5', E_U45,
                      [(_B2_DOOR_MID[0], _B2_DOOR_MID[1], 'the entry door'), (_U5_LAND_MID[0], _U5_LAND_MID[1], 'the top landing')])
UNIT_45 = UnitType('UNITS 4 / 5', 100, [LEVEL_U4, LEVEL_U5], CIRCUITS_U45, stacked=True)



# ================================ Unit 1 ================================
# The study's own inches, from the Sage stud face and the S Elm stud face, turned
# into the page feet the study is drawn in by site_x / site_y (no mirror). Sage is
# the page's left, S Elm its top, the adjacent parcel its right and W4 its bottom
# (y = site_y(D_STUD)): a device on that line is on the chase face, mount 'w5s'.
from src.building1 import (B0, B1, BR_X, BX0, BX1, BY1, CS, DEM0, DEM1, D_STUD, ENTRY_LEFT, ENTRY_WIDTH, FZ, KX,
                           LB, MX0, MX1, NX, PK0, R0, SX, W_STUD, YT, Y_SEP_TOP, site_x, site_y)
from lib.units import IN


def _u1(xi, yi, kind, mount, circuit=None, tag=''):
    """A Unit 1 device at the study's inches."""
    return dev(site_x(IN(xi)), site_y(IN(yi)), kind, mount, circuit, tag)


# The adjacent-parcel stud face in the study's inches. A device on that wall is written
# against this rather than a number, so it follows the wall: how thick the side walls
# are is building1's business, not this file's.
PARCEL = W_STUD * 12.0


def _pts(*pairs):
    """Study feet to page feet, for a polygon."""
    return [(site_x(x), site_y(y)) for x, y in pairs]


def _rect(x, y, w, h, name=None):
    r = (site_x(x), site_y(y), w, h)
    return r+(name,) if name else r


def _door(x, y, ln, o):
    return (site_x(x), site_y(y), ln, o)


CIRCUITS_U1 = [
    ckt(1,  'LEVEL 1 LIGHTING, STAIR, ALARMS, BATH 1 FAN',      15, 1, '#14', 'AFCI',      'ltg'),
    ckt(2,  'LIVING / DINING / ENTRY RECEPTACLES',              20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(3,  'BEDROOM 1, RECEPTACLES AND LIGHTING',              20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(4,  'BATH 1 RECEPTACLE',                                20, 1, '#12', 'GFCI',      'bath'),
    ckt(5,  'KITCHEN SMALL APPLIANCE 1',                        20, 1, '#12', 'AFCI/GFCI', 'sa'),
    ckt(6,  'KITCHEN SMALL APPLIANCE 2',                        20, 1, '#12', 'AFCI/GFCI', 'sa'),
    ckt(7,  'LAUNDRY',                                          20, 1, '#12', 'AFCI/GFCI', 'laundry'),
    ckt(8,  'DISHWASHER',                                       20, 1, '#12', 'AFCI/GFCI', 'dw'),
    ckt(9,  'REFRIGERATOR',                                     20, 1, '#12', 'AFCI/GFCI', 'dw'),
    ckt(10, 'RANGE',                                            50, 2, '#6',  '—',         'range'),
    ckt(11, 'DRYER',                                            30, 2, '#10', '—',         'dryer'),
    ckt(12, 'HEAT PUMP HP-1: MCA 30 A, MOCP 40 A',              40, 2, '#10', '—',         'hp', mca=30, mocp=40),
    ckt(13, 'WATER HEATER',                                     30, 2, '#10', '—',         'wh'),
    ckt(14, 'ENTRY LUMINAIRE',                                  15, 1, '#14', 'AFCI',      'ltg'),
    ckt(15, 'LEVEL 2 LIGHTING, HALL, BATH 2, ALARMS',           15, 1, '#14', 'AFCI',      'ltg'),
    ckt(16, 'BEDROOMS 2 AND 3, RECEPTACLES AND LIGHTING',       20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(17, 'BEDROOM 4, RECEPTACLES AND LIGHTING',              20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(18, 'BATH 2 RECEPTACLE',                                20, 1, '#12', 'GFCI',      'bath'),
]

E_U1_L1 = [
    # --- Living / dining / entry: the door at x 5.75–41.75 on S Elm, windows at 63.25–99.25 and 201.75–237.75
    _u1(101.75, 0, 'dup', 'n', 2), _u1(171.75, 0, 'dup', 'n', 2), _u1(246.75, 0, 'gfci', 'n', 6),
    _u1(101.75, 161.5, 'dup', 's', 2), _u1(45.25, 120, 'dup', 'w', 2), _u1(0, 40, 'dup', 'w', 2),
    _u1(131.75, 60, 'lt', 'c', 1, 'A'), _u1(131.75, 120, 'lt', 'c', 1, 'A'), _u1(44.75, 0, 'sw', 'n', 1, 'A'),
    _u1(178.75, 150, 'sd', 'c', 1), _u1(166.75, 150, 'co', 'c', 1),
    _u1(151.75, 0, 'head', 'n', 12),
    _u1(216.5, 164.9, 'tstat', 's', 12),    # the wall control on Bedroom 1's front wall, RCO 1103.1
    # --- Kitchen: the counter down the parcel wall y 15–137.5 (range 15–45, dishwasher 45–69,
    #     sink 69–105, corner 105–137.5), the fridge at x 221.25–257.25 and the pantry base
    #     257.25–301 on the wall at y 161.5
    _u1(PARCEL, 30, 'range', 'e', 10), _u1(PARCEL, 50, 'dw', 'e', 8), _u1(PARCEL, 60, 'gfci', 'e', 5),
    _u1(PARCEL, 121, 'gfci', 'e', 6), _u1(PARCEL, 152, 'gfci', 'e', 5), _u1(277.75, 161.5, 'gfci', 's', 6),
    _u1(238.75, 161.5, 'fridge', 's', 9),
    _u1(259.75, 40, 'rec', 'c', 1, 'K'), _u1(259.75, 110, 'rec', 'c', 1, 'K'), _u1(PARCEL, 142, 'sw', 'e', 1, 'K'),
    # --- Stair, in its enclosure x 0–41.75 from y 74.75 to 241.25: lit, switched at both levels
    _u1(21.75, 150, 'lt', 'c', 1, 'S'), _u1(41.75, 82, 'sw3', 'e', 1, 'S'),
    # --- Mechanical strip and the laundry nook: the panel on the stair wall, the heater on
    #     the wet wall, the W/D against Sage under the Level 2 landing
    _u1(45.25, 181, 'panel', 'w'), _u1(88.25, 226, 'wh', 'e', 13),
    _u1(0, 260, 'gfci', 'w', 7), _u1(0, 252, 'dryer', 'w', 11),
    _u1(66.75, 220, 'lt', 'c', 1, 'M'), _u1(21.75, 256, 'lt', 'c', 1, 'M'), _u1(45.25, 168, 'sw', 'w', 1, 'M'),
    # --- Bath 1: x 93.75–154.75, y 165–250; the lavatory in the NW corner, the tub at the south end
    _u1(93.75, 192, 'gfci', 'w', 4),
    _u1(123.75, 195, 'rec', 'c', 1, 'C'), _u1(123.75, 235, 'rec', 'c', 1, 'C'), _u1(109.75, 165, 'sw', 'n', 1, 'C'),
    _u1(123.75, 215, 'fanc', 'c', 1, 'F'), _u1(114.75, 165, 'sw', 'n', 1, 'F'),
    # --- Bedroom 1: x 158.25–301, y 165–278.5; the bed heads on the parcel wall; W4 behind
    _u1(246.75, 165, 'dup', 'n', 3), _u1(PARCEL, 240, 'dup', 'e', 3), _u1(231.75, 278.5, 'dup', 'w5s', 3),
    _u1(171.75, 278.5, 'dup', 'w5s', 3), _u1(158.25, 210, 'dup', 'w', 3),
    _u1(228.75, 220, 'lt', 'c', 3, 'D'), _u1(201.75, 165, 'sw', 'n', 3, 'D'),
    _u1(228.75, 200, 'sd', 'c', 1), _u1(PARCEL, 258, 'head', 'e', 12),     # past the W-A and the receptacle: a head cannot hang over an 8'-0" window head
    # --- Exterior, on S Elm beside the door: the luminaire, switched inside; the receptacle
    _u1(45.75, 0, 'ext', 's', 14, 'X'), _u1(48.75, 0, 'sw', 'n', 14, 'X'), _u1(53.75, 0, 'wp', 's', 2),
]

E_U1_L2 = [
    # --- Bedroom 2, Sage side: x 0–148.75, y 0–121 with its closet at x 0–55, y 94.5–121
    #     (it stands against the Sage wall and moved out with it); the door at x 102.75–134.75
    #     on the hall wall; the bed heads on the demising wall
    _u1(26.75, 0, 'dup', 'n', 16), _u1(101.75, 0, 'dup', 'n', 16), _u1(148.75, 10, 'dup', 'e', 16),
    _u1(148.75, 95, 'dup', 'e', 16), _u1(79.75, 121, 'dup', 's', 16), _u1(0, 80, 'dup', 'w', 16),
    _u1(74.75, 60, 'lt', 'c', 16, 'A'), _u1(141.75, 121, 'sw', 's', 16, 'A'),
    _u1(74.75, 40, 'sd', 'c', 15), _u1(126.75, 0, 'head', 'n', 12),
    # --- Bedroom 3, parcel side: x 152.25–301, y 0–121; door 155.75–187.75, closet bypass 254.75–298
    _u1(176.75, 0, 'dup', 'n', 16), _u1(261.75, 0, 'dup', 'n', 16), _u1(PARCEL, 40, 'dup', 'e', 16),
    _u1(PARCEL, 110, 'dup', 'e', 16), _u1(221.75, 121, 'dup', 's', 16), _u1(152.25, 95, 'dup', 'w', 16),
    _u1(152.25, 10, 'dup', 'w', 16),
    _u1(225.75, 60, 'lt', 'c', 16, 'B'), _u1(191.75, 121, 'sw', 's', 16, 'B'),
    _u1(225.75, 40, 'sd', 'c', 15), _u1(281, 0, 'head', 'n', 12),          # on the S Elm wall past its W-A: the parcel wall here is window
    # --- Hall: the band y 124.5–161.5, the strip x 45.25–88.25 down to W4, the landing x 0–45.25
    _u1(71.75, 124.5, 'dup', 'n', 15),
    _u1(121.75, 143, 'lt', 'c', 15, 'H'), _u1(66.75, 200, 'lt', 'c', 15, 'H'), _u1(21.75, 262, 'lt', 'c', 15, 'H'),
    _u1(49.75, 124.5, 'sw', 'n', 15, 'H'), _u1(88.25, 246, 'sw3', 'e', 1, 'S'),
    _u1(136.75, 143, 'sd', 'c', 15), _u1(106.75, 143, 'co', 'c', 15),
    # --- Bath 2, over Bath 1
    _u1(93.75, 192, 'gfci', 'w', 18),
    _u1(123.75, 195, 'rec', 'c', 15, 'C2'), _u1(123.75, 235, 'rec', 'c', 15, 'C2'), _u1(109.75, 165, 'sw', 'n', 15, 'C2'),
    _u1(123.75, 215, 'fan', 'c', 15, 'F2'), _u1(114.75, 165, 'sw', 'n', 15, 'F2'),
    # --- Bedroom 4, over Bedroom 1; its closet bypass at x 203.75–247.75 on the hall wall
    _u1(271.75, 165, 'dup', 'n', 17), _u1(PARCEL, 240, 'dup', 'e', 17), _u1(231.75, 278.5, 'dup', 'w5s', 17),
    _u1(171.75, 278.5, 'dup', 'w5s', 17), _u1(158.25, 210, 'dup', 'w', 17),
    _u1(228.75, 220, 'lt', 'c', 17, 'D'), _u1(201.75, 165, 'sw', 'n', 17, 'D'),
    _u1(228.75, 200, 'sd', 'c', 15), _u1(PARCEL, 258, 'head', 'e', 12),     # past the W-A and the receptacle: a head cannot hang over an 8'-0" window head
]

_I = IN
LEVEL_U1_L1 = Level(
    'UNIT 1 LEVEL 1', E_U1_L1,
    rooms=[_rect(BX0, R0, BX1-BX0, BY1-R0, 'BATH 1'), _rect(BX0, PK0, BX1-BX0, D_STUD-PK0, 'CLOSET'),
           _rect(BR_X, R0, W_STUD-BR_X, D_STUD-R0, 'BEDROOM 1')],
    polys=[(_pts((0, 0), (W_STUD, 0), (W_STUD, B1), (MX0, B1), (MX0, LB), (0, LB)), 'LIVING / DINING / KITCHEN'),
           (_pts((0, LB), (SX, LB), (SX, YT), (0, YT)), 'STAIR'),
           (_pts((MX0, R0), (MX1, R0), (MX1, D_STUD), (0, D_STUD), (0, YT), (MX0, YT)), 'MECH / LAUNDRY')],
    doors=[_door(_I(5.75), 0, ENTRY_WIDTH, 'h'), _door(_I(47.75), R0, _I(34), 'h'), _door(BX1-_I(35.5), R0, _I(32), 'h'),
           _door(_I(161.75), R0, _I(34), 'h'), _door(BR_X, PK0+_I(1), D_STUD-PK0-_I(2), 'v'),
           _door(MX0, YT-_I(24), _I(24), 'v'), _door(0, LB, MX0, 'h')],
    ext_req=[(ENTRY_LEFT+ENTRY_WIDTH/2.0, site_y(0), 'the entry door')],
    counters=[_rect(W_STUD-_I(24), _I(15), _I(24), _I(122.5)), _rect(KX+_I(36), B1-_I(24), W_STUD-KX-_I(36), _I(24))],
    dividers=[_rect(W_STUD-_I(24), _I(15), _I(24), _I(30)), _rect(W_STUD-_I(24), _I(69), _I(24), _I(36))],
    kitchens=[_rect(KX, 0, W_STUD-KX, B1)],
    lavs=[_rect(BX0+_I(.5), R0+_I(.5), _I(21), _I(24))], wds=[_rect(_I(4), D_STUD-_I(31.5), _I(32), _I(27))],
    sinks=[_rect(W_STUD-_I(24), _I(69), _I(24), _I(36))], sep_y=Y_SEP_TOP)

LEVEL_U1_L2 = Level(
    'UNIT 1 LEVEL 2', E_U1_L2,
    rooms=[_rect(DEM1, 0, W_STUD-DEM1, FZ, 'BEDROOM 3'), _rect(BX0, R0, BX1-BX0, BY1-R0, 'BATH 2'),
           _rect(BX0, PK0, BX1-BX0, D_STUD-PK0, 'LINEN'), _rect(BR_X, R0, W_STUD-BR_X, D_STUD-R0, 'BEDROOM 4'),
           _rect(NX+_I(3.5), B0, CS-NX-_I(3.5), B1-B0, 'CLOSET'), _rect(CS+_I(3.5), B0, W_STUD-CS-_I(3.5), B1-B0, 'CLOSET')],
    polys=[(_pts((0, 0), (DEM0, 0), (DEM0, FZ), (_I(55), FZ), (_I(55), _I(94.5)), (0, _I(94.5))), 'BEDROOM 2'),
           (_pts((MX0, B0), (NX, B0), (NX, B1), (MX1, B1), (MX1, D_STUD), (0, D_STUD), (0, YT), (MX0, YT)), 'HALL')],
    doors=[_door(_I(102.75), FZ, _I(32), 'h'), _door(_I(7.25), _I(94.5), _I(44), 'h'), _door(_I(155.75), FZ, _I(32), 'h'),
           _door(CS+_I(5), FZ, W_STUD-_I(3)-CS-_I(5), 'h'), _door(BX1-_I(35.5), R0, _I(32), 'h'),
           _door(_I(161.75), R0, _I(34), 'h'), _door(_I(203.75), R0, _I(44), 'h'), _door(MX1, PK0+_I(1), D_STUD-PK0-_I(2), 'v')],
    lavs=[_rect(BX0+_I(.5), R0+_I(.5), _I(21), _I(24))], sep_y=Y_SEP_TOP)

UNIT_1 = UnitType('UNIT 1', 125, [LEVEL_U1_L1, LEVEL_U1_L2], CIRCUITS_U1)


# ================================ the house loads ================================
# Page feet on each building's perimeter. Common site lighting on a photocell — the
# courtyard walk between the buildings from Building 1's rear wall, the walk to the
# parking from Building 2's — and one receptacle beside each meter bank.
from src.sitework import SVC_B1, SVC_B2, SITE_BLDG
_B1_SITE = SITE_BLDG[0]
_B2_SITE = SITE_BLDG[1]
_EM1 = next(e for e in SVC_B1 if e[0] == 'EM-1')
_EM3 = next(e for e in SVC_B2 if e[0] == 'EM-3')

CIRCUITS_HOUSE = [ckt('H1', 'SITE LIGHTING, PHOTOCELL CONTROLLED', 15, 1, '#14', 'AFCI', 'house'),
                  ckt('H2', 'COMMON RECEPTACLE AT THE METER BANK', 20, 1, '#12', 'GFCI', 'house')]
E_HOUSE_1 = [dev(13.0, 48.0, 'ext', 'n', 'H1'),
             dev(26.0, _EM1[2]+_EM1[4]-_B1_SITE[1]+1.0, 'wp', 'w', 'H2')]
E_HOUSE_2 = [dev(13.0, 28.0, 'ext', 'n', 'H1'),
             dev(26.0, _EM3[2]+_EM3[4]-_B2_SITE[1]+1.0, 'wp', 'w', 'H2')]
HOUSE_1 = UnitType('BUILDING 1 HOUSE', 60, [Level('BUILDING 1 HOUSE', E_HOUSE_1)], CIRCUITS_HOUSE)
HOUSE_2 = UnitType('BUILDING 2 HOUSE', 60, [Level('BUILDING 2 HOUSE', E_HOUSE_2)], CIRCUITS_HOUSE)
HOUSE_VA = 1500          # each house panel: the lighting at 180 VA an outlet plus the receptacle

UNIT_TYPES = [UNIT_1, UNIT_23, UNIT_45, HOUSE_1, HOUSE_2]


# ================================ the services ================================
# One utility service per building, into a meter bank whose positions are the unit and
# house meters, each position's breaker that meter's service disconnect (230.71). The
# service load is NEC 220 Part III, with the multifamily optional method 220.84 (three
# or more units) or 220.85 (two units) taken instead where it comes out less.
SERVICES = [
    dict(name='BUILDING 1', mark='EM-1', building=1, units=[NEC_UNITS[0], NEC_UNITS[1], NEC_UNITS[1]],
         house_va=HOUSE_VA,
         positions=[('U1', 125, 'UNIT 1'), ('U2', 100, 'UNIT 2'), ('U3', 100, 'UNIT 3'), ('H', 60, 'BUILDING 1 HOUSE')],
         marking='SERVICE DISCONNECT'),                                   # 230.70(B)
    dict(name='BUILDING 2', mark='EM-3', building=2, units=[NEC_UNITS[2], NEC_UNITS[2]],
         house_va=HOUSE_VA,
         positions=[('U4', 100, 'UNIT 4'), ('U5', 100, 'UNIT 5'), ('H', 60, 'BUILDING 2 HOUSE')],
         marking='EMERGENCY DISCONNECT, SERVICE DISCONNECT'),             # 230.85, a two-family dwelling
]


# def _demand_220_45(: shared, see codes/nec/load.py
from codes.nec.load import feeders, service_loads


def check_services():
    from src.foundation import B1, B2
    bad = []
    for s in SERVICES:
        std, opt, gov, size = service_loads(s)
        if size < gov['amps']:
            bad.append('%s: %d A service under its %.0f A load' % (s['name'], size, gov['amps']))
        for pos, name, a, wire, wires, neutral, egc in feeders(s):
            need = 0.83*a if pos.startswith('U') else a
            if WIRE_AMPS[wire] < need-1e-9:
                bad.append('%s %s: %s carries less than %.0f A' % (s['name'], pos, wire, need))
            if pos != 'SERVICE' and wires != 4:
                bad.append('%s %s: not a 4-wire feeder' % (s['name'], pos))
        if s['building'] == 2 and 'EMERGENCY' not in s['marking']:
            bad.append('%s: a two-family building marks its disconnects per 230.85' % s['name'])
        if len(s['positions']) > 6:
            bad.append('%s: more than six disconnects, 230.71' % s['name'])
    for b in (B1, B2):
        if 2*(b.W+b.D) < 20.0:
            bad.append('%s: footing under 20 ft, no concrete-encased electrode' % b.name)
    return bad


def check_electrical():
    """Every unit type against every rule; prints one line each and asserts."""
    bad = []
    for ut in UNIT_TYPES:
        v = check_unit(ut); bad += v
        n = lambda kinds: sum(1 for lv in ut.levels for d in lv.devices if d.kind in kinds)
        amps = [nec220_82(*u[1:7])['amps'] for u in NEC_UNITS if u[0] == ut.name]
        load = '%.0f A of %d' % (amps[0], ut.panel_a) if amps else '%d A house panel' % ut.panel_a
        if amps and amps[0] > ut.panel_a + 1e-9:
            bad.append('%s: NEC 220.82 load %.1f A exceeds its %d A panel' % (ut.name, amps[0], ut.panel_a))
        # The spaces rule is a DWELLING panel's; a house panel carries two circuits off
        # the meter bank and is sized by the bank, not by this.
        room = ''
        if amps:
            used, spaces = panel_spaces(ut.circuits)
            if used > spaces:
                bad.append('%s: %d poles in a %d-space panel' % (ut.name, used, spaces))
            room = '%d poles in a %d-space panel, ' % (used, spaces)
        print("ELECTRICAL %-16s %2d receptacles, %2d luminaires, %d SD, %d CO, %2d circuits, %s%s"
              % (ut.name, n(OUTLETS), n(LUM+('ext',)), n(('sd',)), n(('co',)), len(ut.circuits), room, load))
    for sv in SERVICES:
        std, opt, gov, size = service_loads(sv)
        print("SERVICE %s building %d: %s %.0f A; %s %.0f A; %s governs -> %d A service, %s"
              % (sv['mark'], sv['building'], std['method'], std['amps'], opt['method'], opt['amps'],
                 'the optional method' if gov is opt else 'the standard method', size, feeders(sv)[-1][3]))
    bad += check_services()
    assert not bad, "electrical:\n  " + "\n  ".join(bad)
