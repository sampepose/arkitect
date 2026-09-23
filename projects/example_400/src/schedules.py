"""The quantities A-602's schedules print, counted from the MODEL once — never while
drawing, since Building 2's one plan is drawn for two units and the house's for every
trade sheet.

Windows carry their mark in the opening lists. Doors do not, so each door is CLASSIFIED
here from where it stands and how wide it is; a door the classifier cannot place stops the
build rather than going unscheduled.
"""
from collections import Counter, OrderedDict
from arkitect.lib.draw.sheets import is_closet
from arkitect.lib.model.regrid import PARTITION
from src import building1 as B1, building2 as B2

# mark -> (size, type, hardware)
DOORS = OrderedDict([
    ("D-1",  ("3'-0\" x 6'-8\"", "INSULATED STEEL, HALF GLAZED, EXTERIOR — THE THREE ENTRIES", "ENTRY LOCKSET, DEADBOLT")),
    ("D-2",  ("2'-8\" x 6'-8\"", "INSULATED STEEL, HALF GLAZED, EXTERIOR — UNIT 1 BACK DOOR", "ENTRY LOCKSET, DEADBOLT")),
    ("D-3",  ("2'-8\" x 6'-8\"", "HOLLOW CORE — BEDROOMS, BATHROOMS", "PRIVACY")),
    ("D-4",  ("2'-8\" x 6'-8\"", "LOUVERED SINGLE — UNIT 1 MECHANICAL / LAUNDRY", "PASSAGE")),
    ("D-4A", ("2'-2\" x 6'-8\"", "LOUVERED, IN PAIRS — MECHANICAL / LAUNDRY, UNITS 2 AND 3", "PASSAGE, NO LATCH")),
    ("D-5",  ("4'-0\" / 6'-0\"", "BYPASS — BEDROOM CLOSETS, SIZE TO SUIT THE OPENING", "BYPASS TRACK, NO LATCH")),
    ("D-6",  ("2'-6\" x 6'-8\"", "HOLLOW CORE — UNIT 1 COAT CLOSET UNDER THE STAIR", "PASSAGE")),
    ("D-7",  ("2'-0\" x 6'-8\"", "HOLLOW CORE — UNIT 1 PANTRY", "PASSAGE")),
])
LOUVERED = ("D-4", "D-4A")          # each serves a room with a dryer in it, RCO M1502


def _b1_mark(d):
    x, y, w, o = d[:4]
    if "ext" in d[5:]:
        return "D-1" if w >= 3.0 else "D-2"
    if o == 'v' and abs(x-(B1.X_SW+PARTITION/2.0)) < 1e-6: return "D-6"          # on the stair wall: the coat closet
    if o == 'v' and abs(x-(B1.X_HALL0-PARTITION/2.0)) < 1e-6: return "D-4"       # the hall's mechanical side
    if abs(w-B1.D_PANTRY_W) < 1e-6: return "D-7"                              # the pantry, off the kitchen
    if abs(w-2.67) < 1e-6: return "D-3"
    raise ValueError("Unit 1 door %r has no mark" % (d,))


def _b2_mark(d):
    x, y, w, o = d[:4]
    if "ext" in d[5:]: return "D-1"
    if abs(w-B2.D4A) < 1e-6: return "D-4A"
    if abs(w-2.67) < 1e-6: return "D-3"
    raise ValueError("Building 2 door %r has no mark" % (d,))


def door_totals():
    n = Counter()
    for m in B1.LEVEL.values():
        n.update(_b1_mark(d) for d in m['doors'])
        n["D-5"] += sum(1 for o in m['openings'] if is_closet(o, m['rooms']))
    for _unit in (2, 3):
        n.update(_b2_mark(d) for d in B2.B2doors)
        n["D-5"] += sum(1 for o in B2.B2op if is_closet(o, B2.B2U))
    tagged = Counter(mk for lv in B1.LEVEL for _x, _y, mk in door_tags(1, lv))
    tagged.update(mk for _unit in (2, 3) for _x, _y, mk in door_tags(2, 1))
    assert tagged == n, "the plans tag %s and A-602 schedules %s" % (dict(tagged), dict(n))
    assert set(n) == set(DOORS), "door marks scheduled and counted differ: %s" % sorted(set(n) ^ set(DOORS))
    return n


TAG_OFF = 0.95                      # a door's tag off its wall line, on the side its leaf does not swing to


def door_tags(building, level):
    """[(model x, model y, mark)] for one plan: every door and every closet's bypass pair,
       the marks door_totals() counts, so A-101 / A-102 tag exactly what A-602 schedules."""
    if building == 1:
        m = B1.LEVEL[level]; doors, ops, rooms, mark = m['doors'], m['openings'], m['rooms'], _b1_mark
    else:
        doors, ops, rooms, mark = B2.B2doors, B2.B2op, B2.B2U, _b2_mark
    out = []
    for d in doors:
        x, y, w, o, swing = d[:5]
        out.append((x+w/2.0, y-swing*TAG_OFF, mark(d)) if o == 'h' else (x-swing*TAG_OFF, y+w/2.0, mark(d)))
    for op in ops:
        if is_closet(op, rooms):
            x, y, w, o = op[:4]
            # the tag stands outside the closet, in the room the doors open to
            cl = next(r for r in rooms if str(r[4]).startswith("CL.") and is_closet(op, [r]))
            if o == 'h': out.append((x+w/2.0, y+(TAG_OFF if y > cl[1]+cl[3]/2.0 else -TAG_OFF), "D-5"))
            else: out.append((x+(TAG_OFF if x > cl[0]+cl[2]/2.0 else -TAG_OFF), y+w/2.0, "D-5"))
    return out


def window_totals():
    n = Counter(w[4] for m in B1.LEVEL.values() for w in m['wins'])
    n.update(w[4] for lv in (1, 2) for w in B2.b2_wins(lv))
    return n


def sleeping_rooms():
    """Every sleeping room, with the marks of its windows: each needs a W-A."""
    out = {("UNIT 1", k): v[2] for k, v in B1.b1_glazing().items() if "BEDROOM" in k}
    for unit in ("UNIT 2", "UNIT 3"):
        for k in B2.GL_U45:
            if k.startswith("br"):
                out[(unit, "BEDROOM "+k[2:])] = None          # Building 2's bedrooms each have two W-As, building2.B2win
    return out


def check_schedules():
    d, w = door_totals(), window_totals()
    print("SCHEDULES  doors %s;  windows %s" % (", ".join("%s %d" % (k, d[k]) for k in DOORS), ", ".join("W-%s %d" % (k, w[k]) for k in sorted(w))))
    for (unit, room), marks in sleeping_rooms().items():
        assert marks is None or "A" in marks, "%s %s has no W-A, RCO 310.1" % (unit, room)
    b2_side_a = [x for x in B2.B2win if x[4] == "A" and x[3] == 'v']
    assert len(b2_side_a) == 2 and len([x for x in B2.B2_REAR_WIN if x[4] == "A"]) == 2, "Building 2's bedrooms no longer have two W-As each"
