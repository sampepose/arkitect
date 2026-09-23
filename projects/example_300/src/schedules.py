"""The opening lists, and the quantities the A-602 schedules are built from.

Not a renderer and not a sheet: this is what the building HAS. A-602 prints it, the
elevations draw from the same lists, and check_schedule_quantities() in build.py holds
the printed schedule against it. Keeping it out of any one sheet is what stops the
elevations and the schedule disagreeing about a window.
"""
from src.building1 import L1_DOORS, L1_WINS, L2_DOORS, L2_WINS, PLAN_L1, PLAN_L2, U23_OPENINGS
from src.building1 import ENTRY_LEFT, ENTRY_WIDTH, U1_BYPASS_DOORS, windows
from src.building2 import B2U, B2doors, B2op, PLAN_B2, b2_wins
from lib.draw.sheets import is_closet
from lib.model.regrid import EXT_STUD


# ---------------- the schedules' quantities ----------------
# Counted from the MODEL, once, here — not while drawing. Building 2's one level is
# drawn twice and Unit 1's plans are drawn twice, so anything tallied during a drawing
# pass counts the sheet rather than the building. B1 below is the per-level opening
# lists including Unit 1's; b2_wins(level) is Building 2's, whose two units are identical
# but for Unit 5's kitchen W-C, so each level is counted from its own list.
def window_totals():
    """W-A / W-B / W-C quantities for the A-602 schedule, from the opening lists."""
    from collections import Counter
    n=Counter(w[4] for _,ws,_ in B1 for w in ws)
    n.update(w[4] for lv in (1, 2) for w in b2_wins(lv))
    return n


def bypass_total():
    """D-5 quantity: every bypass closet front in the project, from three sources.

    This is the one schedule number that was in doubt. A drawing-time counter used to
    report 8 against the schedule's 11, and that looked like the schedule being wrong.
    It was not: the counter incremented on p.bypass(), which draws the fronts in Units
    2/3 and 4/5, and never saw Unit 1's three — Unit 1's plans are in their own
    coordinate system and draw theirs with their own primitive. 4 + 4 + 3 = 11, and the
    schedule has been right all along.
    """
    return (len(U23_OPENINGS)*2                                    # Units 2 and 3
            + sum(1 for o in B2op if is_closet(o,B2U))*2           # Units 4 and 5
            + U1_BYPASS_DOORS)                                     # Unit 1, Part 1


def check_schedule_quantities(doors):
    """The A-602 door quantities are typed. Check the ones the model can account for.

    They have to be typed, because a door mark is not in the model: the marks are
    drawn as text beside each leaf, and two marks can share a size (D-2 and D-7 are
    both 2'-8", D-9 and D-10 both 1'-10"), so nothing in the geometry says which is
    which. What the model CAN count is the bypass fronts and the exterior doors, and
    those are checked here — the rest of the table is a hand-maintained list whose
    numbers this cannot defend.
    """
    typed = {m:int(q) for m,_sz,_ty,_r,_hw,q in doors}
    derived = {"D-5": bypass_total(),
               "D-1": sum(1 for _l,_w,ds in B1 for d in ds if "ext" in d[5:])
                      + sum(1 for d in B2doors if "ext" in d[5:])*2}
    for mark,n in sorted(derived.items()):
        assert typed[mark]==n, ("A-602 says %s x%d; the model holds %d"
                                %(mark,typed[mark],n))
    print("A-602 QUANTITIES: windows %s derived; doors typed, %s checked against the model"
          %(dict(sorted(window_totals().items())),
            ", ".join("%s=%d"%(m,n) for m,n in sorted(derived.items()))))

# The regridded opening lists every elevation is generated from, so no elevation can
# drift from the plan it belongs to. Built here rather than inside A-201 because
# A-202 and A-301 read them too.
# the elevations are generated from the plans' own window and door lists, so they have
# to read the regridded ones or they would show the openings at their old positions
B1=[(1,[PLAN_L1.span(w) for w in L1_WINS],[PLAN_L1.span(d) for d in L1_DOORS]),
    (2,[PLAN_L2.span(w) for w in L2_WINS],[PLAN_L2.span(d) for d in L2_DOORS])]
# Unit 1 is authored directly in final sheet coordinates; normalize wall selectors
# for the legacy face filter while retaining exact along-wall opening positions.
for _lv,_ws,_ds in B1:
    for _x,_y,_ln,_o,_mk in windows(_lv):
        _ws.append((26-_x-_ln,EXT_STUD,_ln,_o,_mk) if _o=='h' else
                   (26-EXT_STUD if _x<13 else EXT_STUD,_y,_ln,_o,_mk))
    if _lv==1:
        _ds.append((26-ENTRY_LEFT-ENTRY_WIDTH,EXT_STUD,3.0,'h',-1,'ext'))
B2=[(1,[PLAN_B2.span(w) for w in b2_wins(1)],[PLAN_B2.span(d) for d in B2doors]),
    (2,[PLAN_B2.span(w) for w in b2_wins(2)],[PLAN_B2.span(d) for d in B2doors])]

# Where the two rows of elevations sit on a sheet. A-201, A-202 and A-203 share them.
# --- row geometry. An elevation is 6.29" tall to the ridge plus 0.66" of title
# --- below it, so two rows fit the 16.5" drawing area with room to spare.
