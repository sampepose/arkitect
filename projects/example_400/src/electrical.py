"""The electrical model: what E-101 and E-102 draw.

400 Oak: the types and the NEC 2023 rules are 300 S Elm's, unchanged; the units, their
devices and the two services below are Oak's -- Unit 1, the house, on E-101, and Units 2
and 3, Building 2's stacked ADUs, on E-102.

Devices are authored here in each unit's own coordinates — the system its furniture
uses — and checked against NEC 2023 (OAC 4101:8-34-01, effective 2024-04-15) before
anything draws. The 220.82 table lives here so P-601 and the E-sheets print one number.
"""


# def nec220_82(: shared, see arkitect/codes/nec/load.py
from arkitect.codes.nec.load import nec220_82


# name, floor area SF, range VA, dryer VA, dishwasher VA, water heater VA, heat pump VA
# at MCA, panel A. The water heater is the storage heater of P-601 note 6: two 4,500 W
# non-simultaneous elements, so 4,500 VA whether the dwelling takes the 40-gallon tank
# or Unit 1's 50-gallon one. It sits in 220.82(B)(3) with the other fastened-in-place
# appliances, not in (C) — there is no electric space heating anywhere in this project.
WH_VA = 4500
# Floor areas from outside dimensions, 220.82(B)(1): the house is two 20' x 33' floors,
# each ADU one. Building 2's kitchens have no dishwasher.
NEC_UNITS = [("UNIT 1",       1320, 12000, 5000, 1200, WH_VA, 7200, 125),
             ("UNITS 2 / 3",   660, 12000, 5000,    0, WH_VA, 4800, 100)]


# ================================ the types: shared, see arkitect/codes/nec/dwelling.py
from arkitect.codes.nec.dwelling import (LUM, Level, OUTLETS, UnitType, WIRE_AMPS, check_unit, ckt, dev, panel_spaces)


# ================================ this project's dwellings ================================
# ================================ shared ================================
def _open_name(labs):
    return labs[0][2] if len(labs) == 1 else ' / '.join(l[2] for l in labs)


def _only(furn, kind):
    return [f[:4] for f in furn if f[4] == kind]


# ================================ Unit 1 ================================
# Building 1's model feet, as F_L1 and F_L2 are authored (pre-mirror: x = 0.5 is the sheet's
# right wall, the 404 Oak side; y runs from Oak to the rear). A-101 draws the same
# rooms. One dwelling over two levels: its rules run over both at once.
from src import building1 as B1

CIRCUITS_U1 = [
    ckt(1,  'LEVEL 1 LIGHTING, ALARMS, BATH FANS, ENTRY',      15, 1, '#14', 'AFCI',      'ltg'),
    ckt(2,  'LIVING RECEPTACLES, EXTERIOR',                    20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(3,  'LEVEL 2 RECEPTACLES AND LIGHTING',                20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(4,  'BATHROOM RECEPTACLES, BATHS 1 AND 2',             20, 1, '#12', 'GFCI',      'bath'),
    ckt(5,  'KITCHEN SMALL APPLIANCE 1',                       20, 1, '#12', 'AFCI/GFCI', 'sa'),
    ckt(6,  'KITCHEN SMALL APPLIANCE 2',                       20, 1, '#12', 'AFCI/GFCI', 'sa'),
    ckt(7,  'LAUNDRY',                                         20, 1, '#12', 'AFCI/GFCI', 'laundry'),
    ckt(8,  'DISHWASHER',                                      20, 1, '#12', 'AFCI/GFCI', 'dw'),
    ckt(9,  'REFRIGERATOR',                                    20, 1, '#12', 'AFCI/GFCI', 'dw'),
    ckt(10, 'RANGE',                                           50, 2, '#6',  '—',         'range'),
    ckt(11, 'DRYER',                                           30, 2, '#10', '—',         'dryer'),
    ckt(12, 'HEAT PUMP HP-1: MCA 30 A, MOCP 40 A',             40, 2, '#10', '—',         'hp', mca=30, mocp=40),
    ckt(13, 'WATER HEATER',                                    30, 2, '#10', '—',         'wh'),
]

_KIT, _RB, _REAR = B1.Y_KIT, B1.Y_RB, B1.Y_REAR
_RUN0 = B1.RUN0
_fr = next(f for f in B1.F_L1 if f[4] == 'fridge')
_ctr = [f for f in B1.F_L1 if f[4] == 'counter' and f[1] > B1.Y_FOOT_RISER+5.0]   # the two beside the fridge
_ENTRY_MID = (B1.D_ENTRY[0]+B1.D_ENTRY[2]/2.0, B1.D_ENTRY[1])

E_U1_L1 = [
    # --- Living: the front wall, the right wall to the counter, the stair wall
    dev(15.6, 1.7, 'dup', 'e', 2), dev(15.6, 9.8, 'dup', 'e', 2),
    dev(0.5, 9.0, 'dup', 'w', 2), dev(0.5, 2.0, 'dup', 'w', 2),       # past 6'-0" of the sink, 210.8
    dev(6.0, 0.5, 'dup', 'n', 2), dev(10.8, 0.5, 'dup', 'n', 2),
    dev(8.0, 4.5, 'lt', 'c', 1, 'A'), dev(8.0, 10.0, 'lt', 'c', 1, 'A'), dev(11.8, 0.5, 'sw', 'n', 1, 'A'),
    dev(8.0, 12.6, 'sd', 'c', 1), dev(9.4, 12.6, 'co', 'c', 1),
    dev(B1.U1_AHU[1][0], B1.U1_AHU[1][1], 'ahu', 'c', 12),   # concealed in the hall soffit, M-101
    dev(B1.X_SW, 9.0, 'tstat', 'e', 12),             # zone 1's thermostat, on the stair wall in the open living space
    # --- Kitchen: the right-wall run -- its two counter spaces either side of the sink,
    #     the dishwasher and the range; the left wall and the rear wall to the hall; the
    #     fridge between its two counters on the mech wall, a receptacle over each
    dev(0.5, _RUN0+0.65, 'gfci', 'w', 5), dev(0.5, _RUN0+4.8, 'gfci', 'w', 6),
    dev(0.5, _RUN0+4.3, 'dw', 'w', 8), dev(0.5, _RUN0+7.05, 'range', 'w', 10),
    dev(0.5, _KIT-1.3, 'gfci', 'w', 5),
    dev(19.5, 18.0, 'gfci', 'e', 6), dev(16.5, _KIT, 'gfci', 's', 6),
    dev(_ctr[0][0]+_ctr[0][2]/2.0, _KIT, 'gfci', 's', 5), dev(_ctr[1][0]+_ctr[1][2]/2.0, _KIT, 'gfci', 's', 6),
    dev(_fr[0]+_fr[2]/2.0, _KIT, 'fridge', 's', 9),
    dev(12.5, 18.5, 'rec', 'c', 1, 'B'), dev(12.5, 22.0, 'rec', 'c', 1, 'B'), dev(4.5, 21.0, 'rec', 'c', 1, 'B'),
    dev(19.5, 15.0, 'sw', 'e', 1, 'B'),
    # --- The stair: a luminaire over the flight, three-way at its foot and its top landing
    dev(17.75, 12.0, 'lt', 'c', 1, 'S'), dev(19.5, 15.6, 'sw3', 'e', 1, 'S'),
    # --- Bath 1: the vanity against the left wall by the front, the shower beyond it
    dev(16.8, _RB, 'gfci', 'n', 4),
    dev(15.4, 27.0, 'rec', 'c', 1, 'C'), dev(14.4, 28.9, 'sw', 'w', 1, 'C'),
    dev(16.0, 30.8, 'fan', 'c', 1, 'F'), dev(14.4, 29.4, 'sw', 'w', 1, 'F'),
    # --- Hall
    dev(12.25, 27.2, 'lt', 'c', 1, 'H'), dev(14.0, 26.2, 'sw', 'e', 1, 'H'),
    # --- Mechanical / laundry: behind the W/D, the dryer on the pantry wall, the heater on
    #     the rear wall, the panel on the pantry wall by the door
    dev(6.2, _REAR, 'gfci', 's', 7), dev(5.1, 31.0, 'dryer', 'w', 11), dev(9.3, _REAR, 'wh', 's', 13),
    dev(7.0, 29.25, 'lt', 'c', 1, 'M'), dev(10.1, 28.9, 'sw', 'e', 1, 'M'),
    dev(5.1, 27.2, 'panel', 'w'),
    # --- Exterior: the entry luminaire beside the door, switched inside; a receptacle at
    #     the front and one on the rear wall, 210.52(E)(1)
    dev(11.7, 0.5, 'ext', 's', 1, 'X'), dev(11.5, 0.5, 'sw', 'n', 1, 'X'), dev(11.2, 0.5, 'wp', 's', 2),
    dev(15.5, _REAR, 'wp', 'n', 2),
    # --- The back door: its luminaire outside beside the jamb, switched in the hall
    dev(13.9, _REAR, 'ext', 'n', 1, 'Y'), dev(14.0, 31.4, 'sw', 'e', 1, 'Y'),
]

_BR2 = B1.BR2_CL
def _bath2(y):
    """Bath 2 is laid out on its hall wall: y reflected front to back across the room."""
    return B1.Y_BR2+B1.PARTITION+B1.Y_FR1-y
E_U1_L2 = [
    # --- Hall: the landing, the corridor beside the well, the cross-hall. Over 10'-0", so a
    #     receptacle, 210.52(H)
    dev(6.0, B1.Y_HALL, 'dup', 's', 3),
    dev(14.0, 8.0, 'lt', 'c', 3, 'H'), dev(4.0, 17.4, 'lt', 'c', 3, 'H'), dev(12.4, 4.3, 'sw', 'w', 3, 'H'),
    dev(14.0, 10.5, 'sd', 'c', 1), dev(14.0, 12.0, 'co', 'c', 1), dev(11.0, 17.4, 'sd', 'c', 1),
    dev(17.75, 8.0, 'lt', 'c', 1, 'S'), dev(19.5, 2.0, 'sw3', 'e', 1, 'S'),
    # --- Bedroom 2
    dev(12.0, 6.0, 'dup', 'e', 3), dev(5.0, B1.Y_BR2, 'dup', 's', 3), dev(0.5, 3.0, 'dup', 'w', 3),
    dev(6.0, 0.5, 'dup', 'n', 3), dev(10.5, 0.5, 'dup', 'n', 3),
    dev(9.4, 3.2, 'lt', 'c', 3, 'D'), dev(12.0, 4.3, 'sw', 'e', 3, 'D'),
    dev(10.8, 7.2, 'sd', 'c', 1),
    # --- Bath 2: the double vanity on the hall wall, the tub across the right-wall end; the
    #     door at the Bedroom 2 end, its switches past its swing
    dev(_BR2[0]+0.9, _bath2(B1.Y_BR2+0.4), 'gfci', 's', 4),
    dev(6.5, _bath2(14.6), 'rec', 'c', 3, 'I'), dev(10.0, _bath2(14.6), 'rec', 'c', 3, 'I'),
    dev(12.0, _bath2(12.2), 'sw', 'e', 3, 'I'),
    dev(3.5, _bath2(14.6), 'fanc', 'c', 1, 'G'), dev(12.0, _bath2(11.8), 'sw', 'e', 1, 'G'),
    # --- Bedroom 1
    dev(5.8, 20.4, 'dup', 'e', 3), dev(9.8, 26.5, 'dup', 'e', 3), dev(5.0, _REAR, 'dup', 's', 3),
    dev(0.5, 26.0, 'dup', 'w', 3), dev(0.5, 21.0, 'dup', 'w', 3),
    dev(3.0, 21.6, 'lt', 'c', 3, 'E'), dev(4.6, B1.Y_BRR, 'sw', 'n', 3, 'E'),
    dev(1.8, 30.8, 'sd', 'c', 1),
    # --- Bedroom 3
    dev(14.2, 20.4, 'dup', 'w', 3), dev(19.5, 23.0, 'dup', 'e', 3), dev(19.5, 30.0, 'dup', 'e', 3),
    dev(14.0, _REAR, 'dup', 's', 3), dev(10.2, 27.0, 'dup', 'w', 3),
    dev(17.0, 21.6, 'lt', 'c', 3, 'J'), dev(15.3, B1.Y_BRR, 'sw', 'n', 3, 'J'),
    dev(18.2, 30.8, 'sd', 'c', 1),
    dev(B1.U1_AHU[2][0], B1.U1_AHU[2][1], 'ahu', 'c', 12),   # concealed in the cross-hall soffit, M-101
    dev(12.0, B1.Y_HALL, 'tstat', 's', 12),          # zone 2's thermostat, on the bedrooms' partition
    # --- In the attic over Bedroom 3, beside radon riser RR-1: the box for a future fan, S-103 R7.
    #     src/radon.py holds it within reach of the riser.
    dev(11.2, 29.15, 'jbox', 'c', 3),       # ahead of the north W-B, beside the drop to HP-1
]


def _stair(rooms):
    """The model's unnamed flight and well are the stair, so 210.70(A)(2)(c) applies."""
    return [r[:4]+("STAIR" if not r[4] else r[4],) for r in rooms]


LEVEL_U1_L1 = Level(
    'UNIT 1 LEVEL 1', E_U1_L1,
    rooms=_stair(B1.L1_ROOMS),
    polys=[(pts, _open_name(labs)) for pts, labs in B1.OA_L1],
    # the doors, the hall's cased opening, and the foot of the stair, where the flight
    # opens onto the kitchen and there is no wall
    doors=[d[:4] for d in B1.L1_DOORS]+[o[:4] for o in B1.L1_OPS]+[(B1.X_SW, B1.Y_FOOT_RISER, 19.5-B1.X_SW, 'h')],
    ext_req=[(_ENTRY_MID[0], _ENTRY_MID[1], 'the entry door'),
             (B1.D_REAR[0]+B1.D_REAR[2]/2.0, _REAR, 'the rear door')],
    counters=_only(B1.F_L1, 'counter'), dividers=_only(B1.F_L1, 'range')+_only(B1.F_L1, 'sink'),
    kitchens=[(0.5, B1.Y_FOOT_RISER, 19.0, _KIT-B1.Y_FOOT_RISER)],
    lavs=_only(B1.F_L1, 'lav'), wds=_only(B1.F_L1, 'wd'), sinks=_only(B1.F_L1, 'sink'))

LEVEL_U1_L2 = Level(
    'UNIT 1 LEVEL 2', E_U1_L2,
    rooms=_stair(B1.L2_ROOMS),
    polys=[(pts, _open_name(labs)) for pts, labs in B1.OA_L2],
    doors=[d[:4] for d in B1.L2_DOORS]+[o[:4] for o in B1.L2_OPS],
    lavs=_only(B1.F_L2, 'lav'))

UNIT_1 = UnitType('UNIT 1', 125, [LEVEL_U1_L1, LEVEL_U1_L2], CIRCUITS_U1)


# ============================ Units 2 and 3 ============================
# Building 2's model feet, F_B2's: the courtyard face y 0.5, the rear wall y 32.5; x 0.5
# is the 404 Oak side (the living room's), x 19.5 the 396 Oak side (the kitchen's and
# the mechanical / laundry room's). Unit 2 is Level 1, Unit 3 Level 2, the same plan; the
# entry door and its luminaire are in the same place on both, Unit 3's on its landing.
# Unit 2 alone owes a receptacle at the back, at grade, 210.52(E)(1).
from src import building2 as B2

CIRCUITS_U23 = [
    ckt(1,  'LIGHTING, ALARMS, BATH FAN, ENTRY',               15, 1, '#14', 'AFCI',      'ltg'),
    ckt(2,  'LIVING / DINING RECEPTACLES, EXTERIOR',           20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(3,  'BEDROOMS 1 AND 2, RECEPTACLES AND LIGHTING',      20, 1, '#12', 'AFCI',      'rcpt'),
    ckt(4,  'BATHROOM RECEPTACLE',                             20, 1, '#12', 'GFCI',      'bath'),
    ckt(5,  'KITCHEN SMALL APPLIANCE 1',                       20, 1, '#12', 'AFCI/GFCI', 'sa'),
    ckt(6,  'KITCHEN SMALL APPLIANCE 2',                       20, 1, '#12', 'AFCI/GFCI', 'sa'),
    ckt(7,  'LAUNDRY',                                         20, 1, '#12', 'AFCI/GFCI', 'laundry'),
    ckt(8,  'REFRIGERATOR',                                    20, 1, '#12', 'AFCI/GFCI', 'dw'),
    ckt(9,  'RANGE',                                           50, 2, '#6',  '—',         'range'),
    ckt(10, 'DRYER',                                           30, 2, '#10', '—',         'dryer'),
    ckt(11, 'HEAT PUMP HP-2 / HP-3: MCA 20 A, MOCP 25 A',      25, 2, '#12', '—',         'hp', mca=20, mocp=25),
    ckt(12, 'WATER HEATER',                                    30, 2, '#10', '—',         'wh'),
]

_D2 = B2.B2doors[0]
_D2_MID = (_D2[0]+_D2[2]/2.0, _D2[1])
E_B2 = [
    # --- Living, on the 157 side: the courtyard wall past the door, the side wall, the
    #     bearing wall
    dev(6.0, B2.Y_BEAR, 'dup', 's', 2), dev(0.5, 9.0, 'dup', 'w', 2), dev(0.5, 1.5, 'dup', 'w', 2),
    dev(3.6, 4.5, 'lt', 'c', 1, 'A'), dev(5.4, 0.5, 'sw', 'n', 1, 'A'),
    dev(0.5, 10.0, 'head', 'w', 11),                 # past the W-C, over HP-2 / HP-3
    dev(4.5, B2.Y_BEAR, 'tstat', 's', 11),           # the wall control, off the bath wall, RCO 1103.1
    # --- Kitchen and dining, on the 147 side: the courtyard run with the range, the fridge
    #     before it, the side run with the sink, the corner between them, the dining wall
    dev(8.2, 0.5, 'fridge', 'n', 8), dev(14.25, 0.5, 'range', 'n', 9),
    dev(11.4, 0.5, 'gfci', 'n', 5), dev(16.5, 0.5, 'gfci', 'n', 6),
    dev(19.5, 1.2, 'gfci', 'e', 5), dev(19.5, 7.6, 'gfci', 'e', 6), dev(19.5, 11.0, 'gfci', 'e', 6),
    # surface luminaires, not recessed: Unit 2's ceiling is the rated F1 membrane and UL L528 lists no
    # recessed luminaire (src/framing.py); Unit 3 takes the same fixture
    dev(12.5, 4.5, 'lt', 'c', 1, 'B'), dev(16.0, 7.0, 'lt', 'c', 1, 'B'), dev(12.3, B2.Y_BEAR, 'sw', 's', 1, 'B'),
    # --- Hall, 9'-4" long: no receptacle, 210.52(H)
    dev(10.0, 14.5, 'lt', 'c', 1, 'H'), dev(11.7, 13.4, 'sw', 'e', 1, 'H'),
    dev(10.0, 20.6, 'sd', 'c', 1), dev(10.0, 21.6, 'co', 'c', 1),
    # --- Bath: the lavatory on the rear partition, its receptacle on the hall wall beside it
    dev(7.9, 17.4, 'gfci', 'e', 4),
    dev(5.8, 14.0, 'rec', 'c', 1, 'C'), dev(7.9, 16.2, 'sw', 'e', 1, 'C'),
    dev(4.2, 16.4, 'fanc', 'c', 1, 'F'), dev(7.9, 16.6, 'sw', 'e', 1, 'F'),
    # --- Mechanical / laundry: behind the W/D, the dryer and the heater on the side wall
    dev(17.9, 12.9, 'gfci', 'n', 7), dev(19.5, 14.0, 'dryer', 'e', 10), dev(12.9, B2.Y_MID1, 'wh', 's', 12),
    dev(15.0, 15.6, 'lt', 'c', 1, 'M'), dev(12.1, 13.6, 'sw', 'w', 1, 'M'),
    dev(19.5, 15.8, 'panel', 'e'),
    # --- Bedroom 1, the 157 side
    dev(9.8, 24.6, 'dup', 'e', 3), dev(4.0, B2.Y_REAR, 'dup', 's', 3),
    dev(0.5, 27.0, 'dup', 'w', 3), dev(0.5, 19.8, 'dup', 'w', 3), dev(5.0, B2.Y_BR, 'dup', 'n', 3),
    dev(4.0, 24.8, 'lt', 'c', 3, 'D'), dev(7.9, 22.2, 'sw', 'e', 3, 'D'),
    dev(4.0, 21.0, 'sd', 'c', 1), dev(0.5, 24.65, 'head', 'w', 11),      # just past the W-A, toward HP-2 / HP-3
    # --- Bedroom 2, the 147 side
    dev(10.2, 25.9, 'dup', 'w', 3), dev(15.0, B2.Y_BR, 'dup', 'n', 3),
    dev(19.5, 24.0, 'dup', 'e', 3), dev(19.5, 30.0, 'dup', 'e', 3), dev(16.0, B2.Y_REAR, 'dup', 's', 3),
    dev(16.0, 24.8, 'lt', 'c', 3, 'E'), dev(12.1, 22.2, 'sw', 'w', 3, 'E'),
    dev(16.0, 21.0, 'sd', 'c', 1), dev(10.2, 23.7, 'head', 'w', 11),     # on the bedrooms' partition: the north wall is 20'-0" from the outdoor units
    # --- Exterior, on the courtyard face beside the door: the luminaire, switched inside,
    #     and a receptacle
    dev(1.5, 0.5, 'ext', 's', 1, 'X'), dev(1.7, 0.5, 'sw', 'n', 1, 'X'), dev(5.6, 0.5, 'wp', 's', 2),
]
# Unit 2 alone: the back of the dwelling, at grade, between the reach-ins
E_U2_ONLY = [dev(10.0, B2.Y_REAR, 'wp', 'n', 2)]
# Unit 3 alone: in the attic over Bedroom 1, beside radon riser RR-2, the box for a future fan, S-103 R7
E_U3_ONLY = [dev(2.4, 19.9, 'jbox', 'c', 1)]


def _b2_level(name, devices, ext_req):
    return Level(name, devices,
                 rooms=[r[:5] for r in B2.B2U],
                 polys=[(pts, _open_name(labs)) for pts, labs in B2.OA_B2],
                 doors=[d[:4] for d in B2.B2doors]+[o[:4] for o in B2.B2op],
                 ext_req=ext_req,
                 counters=_only(B2.F_B2, 'counter'), dividers=_only(B2.F_B2, 'range')+_only(B2.F_B2, 'sink'),
                 kitchens=[(B2.X_SPLIT, 0.5, 19.5-B2.X_SPLIT, B2.Y_BEAR-0.5)],
                 lavs=_only(B2.F_B2, 'lav'), wds=_only(B2.F_B2, 'wd'), sinks=_only(B2.F_B2, 'sink'))


LEVEL_U2 = _b2_level('UNIT 2', E_B2+E_U2_ONLY,
                     [(_D2_MID[0], _D2_MID[1], 'the entry door'), (10.0, B2.Y_REAR, 'the rear wall')])
LEVEL_U3 = _b2_level('UNIT 3', E_B2+E_U3_ONLY, [(_D2_MID[0], _D2_MID[1], 'the entry door')])
UNIT_23 = UnitType('UNITS 2 / 3', 100, [LEVEL_U2, LEVEL_U3], CIRCUITS_U23, stacked=True)

UNIT_TYPES = [UNIT_1, UNIT_23]


# ================================ the services ================================
# One utility service per building. Building 1 is a one-family dwelling: one meter, its
# breaker the service disconnect, the house panel fed from it. Building 2 is a two-family
# dwelling: a two-position meter bank, each position's breaker that unit's service
# disconnect (230.71). Both are one- and two-family dwellings, so every service
# disconnect is marked for 230.85. No house meter: nothing on either lot is common.
MARKING = 'EMERGENCY DISCONNECT, SERVICE DISCONNECT'
SERVICES = [
    dict(name='BUILDING 1', mark='EM-1', building=1, units=[NEC_UNITS[0]], house_va=0,
         positions=[('U1', NEC_UNITS[0][7], 'UNIT 1')], marking=MARKING),
    dict(name='BUILDING 2', mark='EM-2', building=2, units=[NEC_UNITS[1], NEC_UNITS[1]], house_va=0,
         positions=[('U2', NEC_UNITS[1][7], 'UNIT 2'), ('U3', NEC_UNITS[1][7], 'UNIT 3')], marking=MARKING),
]
HOUSE_VA = 0


# def _demand_220_45(: shared, see arkitect/codes/nec/load.py
from arkitect.codes.nec.load import feeders, service_loads


def check_services():
    from src.foundation import B1 as F1, B2 as F2
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
        if len(s['units']) <= 2 and 'EMERGENCY' not in s['marking']:
            bad.append('%s: a one- or two-family dwelling marks its disconnects per 230.85' % s['name'])
        if len(s['positions']) > 6:
            bad.append('%s: more than six disconnects, 230.71' % s['name'])
    for b in (F1, F2):
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
        if amps and amps[0] > ut.panel_a + 1e-9:
            bad.append('%s: NEC 220.82 load %.1f A exceeds its %d A panel' % (ut.name, amps[0], ut.panel_a))
        used, spaces = panel_spaces(ut.circuits)
        if used > spaces:
            bad.append('%s: %d poles in a %d-space panel' % (ut.name, used, spaces))
        print("ELECTRICAL %-12s %2d receptacles, %2d luminaires, %d SD, %d CO, %2d circuits, %d poles in a %d-space panel, %.0f A of %d"
              % (ut.name, n(OUTLETS), n(LUM+('ext',)), n(('sd',)), n(('co',)), len(ut.circuits), used, spaces,
                 amps[0], ut.panel_a))
    for sv in SERVICES:
        std, opt, gov, size = service_loads(sv)
        print("SERVICE %s building %d: %s %.0f A; %s %.0f A; %s governs -> %d A service, %s"
              % (sv['mark'], sv['building'], std['method'], std['amps'], opt['method'], opt['amps'],
                 'the optional method' if gov is opt else 'the standard method', size, feeders(sv)[-1][3]))
    bad += check_services()
    assert not bad, "electrical:\n  " + "\n  ".join(bad)
