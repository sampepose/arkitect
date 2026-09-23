"""Interior finishes: the paint systems A-602's room finish schedule names.

Section 8 inspections (HUD NSPIRE) look at the CONDITION of paint, never its sheen, so the
systems are chosen for turnover maintenance. A voucher unit is patched and repainted more
often than it is scrubbed: walls a patch blends into (eggshell), gloss only where water,
grease or hands demand it, and a scrub rating on every wall and trim system so a low sheen
is not a cheap one. The spec is docs/superpowers/specs/2026-09-16-a602-paint-finishes-design.md.
"""
from collections import namedtuple

from arkitect.lib.units import IN, inches

Paint = namedtuple("Paint", "tag sheen mpi scrub mildew where")

# The board on a stud face, A-601 W2. ONE definition, because two readers need the same
# number: the schedule cell below prints it, and RCO 307.1's water closet dimension
# deducts it from the stud face the rest of the plan is dimensioned to. A plan drawn to
# stud faces and a clearance measured to a finished surface must not answer to two
# different thicknesses.
BOARD = IN(0.5)

SCRUB_MIN = 1000        # cycles, ASTM D2486, every wall and trim system
MILDEW_RATING = 10      # ASTM D3273, the wet-room system

PAINT = {
    "PT-1": Paint("PT-1", "EGGSHELL", 3, SCRUB_MIN, False, "walls"),
    "PT-2": Paint("PT-2", "SEMI-GLOSS", 5, SCRUB_MIN, True, "walls and ceilings"),
    "PT-3": Paint("PT-3", "FLAT", 1, None, False, "ceilings"),
    "PT-4": Paint("PT-4", "SEMI-GLOSS ENAMEL", 5, SCRUB_MIN, False, "trim"),
}

# GA-214 finish level under each surface: gloss over Level 4 shows every joint.
GYP_LEVEL = 4
GYP_LEVEL_GLOSS = 5
LEVEL_5_ROOMS = ("BATHROOMS",)

Room = namedtuple("Room", "name floor base wall ceiling wet")

# A-602's rows, top to bottom. Floor and base are unchanged from the schedule's typed text.
ROOMS = (
    Room("LIVING / DINING", "LUXURY VINYL PLANK", "4\" VINYL", "PT-1", "PT-3", False),
    Room("BEDROOMS", "LUXURY VINYL PLANK", "4\" VINYL", "PT-1", "PT-3", False),
    Room("KITCHEN", "LUXURY VINYL PLANK", "4\" VINYL", "PT-1", "PT-3", False),
    Room("BATHROOMS", "LUXURY VINYL PLANK", "4\" VINYL", "PT-2", "PT-2", True),
    Room("HALLS AND STAIRS", "LUXURY VINYL PLANK", "4\" VINYL", "PT-1", "PT-3", False),
    Room("MECHANICAL / LAUNDRY", "SEALED CONCRETE OR LVP", "NONE", "PT-2", "PT-2", True),
)

# A-001 note 3: kitchens open to living / dining and halls are cased openings, so these
# spaces share wall planes and one wall system — a sheen change would stop mid-wall.
OPEN_SPACES = ("LIVING / DINING", "KITCHEN", "HALLS AND STAIRS")

TRIM = "PT-4"
TRIM_WHERE = "INTERIOR DOORS, FRAMES, CASINGS, STAIR STRINGERS, HANDRAILS AND GUARDS"


def cell(tag):
    return "%s GYP, %s %s" % (inches(BOARD), tag, PAINT[tag].sheen)


def schedule_rows():
    return [(r.name, r.floor, r.base, cell(r.wall), cell(r.ceiling)) for r in ROOMS]


def level(room):
    return GYP_LEVEL_GLOSS if room.name in LEVEL_5_ROOMS else GYP_LEVEL


def finish_violations():
    """Every way the systems can contradict the rooms they are put in."""
    bad = []
    rooms = {r.name: r for r in ROOMS}
    for r in ROOMS:
        for surface, tag in (("wall", r.wall), ("ceiling", r.ceiling)):
            p = PAINT.get(tag)
            if p is None:
                bad.append("%s %s: no system %s" % (r.name, surface, tag)); continue
            if surface not in p.where:
                bad.append("%s %s: %s is not a %s system" % (r.name, surface, tag, surface))
            if r.wet and not p.mildew:
                bad.append("%s %s: a wet room needs the mildew-resistant system" % (r.name, surface))
            if surface == "wall" and (p.scrub or 0) < SCRUB_MIN:
                bad.append("%s wall: %s is under %d scrub cycles" % (r.name, tag, SCRUB_MIN))
            if p.mpi >= 5 and r.name not in LEVEL_5_ROOMS and not r.wet:
                bad.append("%s %s: gloss over Level %d in a finished room" % (r.name, surface, GYP_LEVEL))
    walls = {rooms[n].wall for n in OPEN_SPACES}
    if len(walls) != 1:
        bad.append("open spaces take different wall systems: %s" % ", ".join(sorted(walls)))
    if PAINT[TRIM].mpi < 5 or (PAINT[TRIM].scrub or 0) < SCRUB_MIN:
        bad.append("trim system %s is not a scrubbable gloss enamel" % TRIM)
    return bad


def check_finishes():
    bad = finish_violations()
    assert not bad, "finishes: " + "; ".join(bad)
    print("FINISHES  %s; walls %d+ scrub cycles ASTM D2486, wet rooms mildew-resistant, open spaces one wall system"
          % (", ".join("%s %s" % (t, p.sheen) for t, p in PAINT.items()), SCRUB_MIN))


def notes():
    """The lines A-602 prints under the schedule."""
    p1, p2, p3, p4 = (PAINT[t] for t in ("PT-1", "PT-2", "PT-3", "PT-4"))
    return [
     "PAINT:  %s %s, MPI GLOSS LEVEL %d.  %s %s, MPI GLOSS LEVEL %d, MILDEW-RESISTANT, RATED %d BY ASTM D3273.  %s %s, MPI GLOSS LEVEL %d."
       % (p1.tag, p1.sheen, p1.mpi, p2.tag, p2.sheen, p2.mpi, MILDEW_RATING, p3.tag, p3.sheen, p3.mpi),
     "     %s %s, MPI GLOSS LEVEL %d, ON %s."
       % (p4.tag, p4.sheen, p4.mpi, TRIM_WHERE),
     "     %s, %s AND %s: NOT FEWER THAN %s SCRUB CYCLES, ASTM D2486. SUBMIT THE MANUFACTURER'S PRODUCT DATA SHOWING EVERY RATING BEFORE PAINTING."
       % (p1.tag, p2.tag, p4.tag, "{:,}".format(SCRUB_MIN)),
     "     ONE MANUFACTURER'S PRODUCT LINE AND ONE COLOR FOR EACH SYSTEM IN ALL THREE UNITS. LEAVE ONE UNOPENED GALLON OF EACH SYSTEM AND COLOR WITH THE OWNER.",
     "     ONE COAT OF PRIMER AND TWO FINISH COATS; ON W1 AND W1R THE A-601 VAPOR RETARDER PRIMER IS THE PRIMER.",
     "     BOARD: 1/2\" GYPSUM EXCEPT WHERE A-601 SCHEDULES ANOTHER, WHOSE BOARD GOVERNS: W1R, W3, F1, AND THE 5/8\" CEILINGS OF F2 AND R1; CEMENT BOARD AT TUBS AND SHOWERS.",
     "     GYPSUM FINISH GA-214 LEVEL %d; LEVEL %d ON BATHROOM WALLS AND CEILINGS. KITCHENS: %s, CONSISTENT WITH THE ADJOINING OPEN LIVING / DINING AREA."
       % (GYP_LEVEL, GYP_LEVEL_GLOSS, p1.tag),
    ]
