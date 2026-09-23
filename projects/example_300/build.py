"""300 S Elm Ave — what the project writes, in what order, and what must hold first.

Three jobs and no fourth:

    DOCUMENTS         the files this project produces
    build_set() and build_zoning_sheet()
                      the binding order of each, which is the one place the whole set
                      can be seen at once, and where its file goes
    check_model()     the model checks that run before a line is drawn

The drawing itself is src/sheets/ — one module per sheet, or per group that shares its
drawing. A renderer knows nothing about which document it belongs to, what order the set
is bound in, or where the file goes; a renderer that reached for any of those would be
taking on the job this file exists to hold.

Importing this module draws nothing, writes nothing and prints nothing.
"""
import sys, os, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))        # this project
ROOT = os.path.dirname(os.path.dirname(HERE))            # the repository
for _p in (ROOT, HERE):                                  # lib/ and codes/, then src/
    if _p not in sys.path:
        sys.path.insert(0, _p)
# drawing primitives
from lib.draw import page
from lib.draw.page import DA, PH, PW
from src import project
from lib.units import fmt
# the sheet mirror and the fixed Units 2/3 reflection
# Unit 1's anchors, Units 2 and 3, the Unit 3 stair, the terminations
from src.building1 import (check_u23_beds, check_u23_terms, check_u3_stair_clear,
                           check_u3_stair_inside, check_unit1_stair, GL_MIN,
                           U2_LANDING_DROP, U2_LANDING_MAX)
from src.clearances import check_clearances, project_plans
from src.finishes import BOARD as WALL_BOARD
from src.foundation import check_foundation
from src.framing import check_framing
from src.electrical import check_electrical
from src.roof import check_roof
from src.radon import check_radon
from src.mechanical import check_mechanical
from src.plumbing import check_plumbing
from src.drainage import check_drainage
from src.grading import check_grading
from src.downspouts import check_downspouts
from src.bracing import check_bracing
from src.fireblocking import check_fireblocking
# W-A, the one egress unit: its frame can host the net clear minimums every product must give
from src.openings import WIN_GEOM, WIN_W
from codes.ohio.rco.egress import check_egress_window
from src.sitework import check_fsd, check_height, check_setbacks, check_wheel_stops
# the separation in section: W4A and W4B, their tiers, rims and fireblocks, A-603
from src.separation import check_w4
# the interior vapour retarder every exterior frame wall takes, RCO 702.7
from src.envelope import check_vapor_retarder
# what the elevations draw on a face: caps and service equipment
from src.faces import check_faces
# the street faces' trim, Unit 1's door surround and the equipment screening shrubs
from src.exterior import check_exterior
# the interior paint systems A-602's room finish schedule names
from src.finishes import check_finishes
# Units 4 and 5: the Sage-wall terminations and the RCO 303.1 glazing
from src.building2 import check_b2_terms, check_b2_glazing
# Unit 1's plans, which build.py draws directly; the building MODEL is above.
# Units 4 and 5, and the Unit 5 stair
# service equipment, the side street yard, the site clearances
from src import levels
from reportlab.pdfgen import canvas

OUT=os.path.join(HERE,"300-S-Elm-permit-set.pdf")
# C-102 is its own document: G-001 note 15 requires the zoning site plan at 11 x 17,
# which is not this set's sheet size, and Building and Zoning Services takes it on its
# own. It is listed in the G-001 index because it is part of the submittal.
ZONING_OUT=os.path.join(HERE,"300-S-Elm-zoning-site-plan.pdf")
# Read by lib/export/dxf.py, which loads this module to re-run the build and otherwise
# has no name for the project's tracked DXF deliverable -- it may not import a project.
# Without this it falls back to deriving a name from the build script's own path, which
# writes a throwaway build.dxf next to this file instead of the file the set ships.
DXF_OUT=os.path.join(HERE,project.DXF_OUT)
# The canvas is made by build_set(), not at import. Importing this module defines the
# sheets and nothing else: it opens no file, draws nothing and prints nothing, so a test
# or a tool can import it to read the model, and the output path is an argument rather
# than a constant.
#
# `c` is a stand-in, not a canvas. Every sheet function reads it as a global — some 610
# drawing calls across 41 functions — and each read resolves to the canvas of the
# document THIS THREAD is drawing. So the name stays where every sheet already expects
# it while the thing behind it is per-document, and build_set() and build_zoning_sheet()
# can run at the same time. See lib/draw/page.py's BuildContext for why that is a
# ContextVar and not a module attribute with a lifetime.
c=page.canvas_proxy()
X0,Y0,X1,Y1=DA
DW,DH=X1-X0,Y1-Y0
Q=18.0      # 1/4"=1'-0"  -> 18 pt per foot
E=9.0       # 1/8"=1'-0"


_CHECKED = False


def check_model():
    """Everything the model must satisfy before a single line is drawn.

    These used to run at import, which is why importing build.py printed a page of
    check output. They are about the MODEL and not about any sheet, so they run once,
    first — in the same order and therefore in the same place in the build's output as
    before.

    EVERY document calls this, not just build_set(). C-102 is its own document and the
    only one that goes to the Board of Zoning Adjustment on its own, and it drew for a
    long time with nothing checked: it was safe only because DOCUMENTS happens to list
    build_set() first and a full run therefore happened to check before it. A tool
    rebuilding the zoning sheet alone — which is the whole reason DOCUMENTS takes a
    scratch path per document — got no check_fsd(), no site clearances, no wheel stops
    and no grading.

    The model is module-level and does not change once imported, so the second document
    in a process has nothing new to check and _CHECKED keeps it from printing the report
    a second time. The flag is set only after every check has passed, so a failure never
    marks the model checked for whatever draws next."""
    global _CHECKED
    if not __debug__:
        raise SystemExit(
            "refusing to build: python was run with -O (or PYTHONOPTIMIZE is set), "
            "which removes every assert statement. Every model check in this project "
            "is an assert, so without this guard the report they print would come out "
            "in full, reading exactly like a checked build, having checked nothing. "
            "Run python3 without -O.")
    if _CHECKED:
        return
    levels.check()
    check_unit1_stair()
    assert U2_LANDING_DROP<=U2_LANDING_MAX+1e-9, "Unit 2 landing is too far below its threshold"
    check_u3_stair_inside()
    check_u23_terms()
    check_u3_stair_clear()
    check_u23_beds()
    check_egress_window(win_geom=WIN_GEOM, win_w=WIN_W)
    assert GL_MIN >= 8.0, "a Units 2/3 habitable space is under the 8 percent of RCO 303.1"
    assert GL_MIN/2.0 >= 4.0, "openable area under the 4 percent of RCO 303.1"
    check_b2_terms()
    check_b2_glazing()
    check_foundation()
    check_framing()
    check_electrical()
    check_mechanical()
    check_plumbing()
    check_drainage()
    check_roof()
    check_radon()
    check_grading()
    check_downspouts()
    check_bracing()
    check_height()
    check_setbacks()
    check_fsd()
    check_fireblocking()
    check_w4()
    check_vapor_retarder()
    check_faces()
    check_wheel_stops()
    check_exterior()
    check_finishes()
    check_clearances(project_plans(), WALL_BOARD)
    _CHECKED = True


fmt_in = lambda v: fmt(v).split("-",1)[1] if 0<v<1 else fmt(v)   # margins read in inches


# The renderers, in the order the set is bound. One module per sheet, or per group
# that shares its drawing; none of them knows about any of the others.
from src.sheets.g001 import sheet_g001
from src.sheets.c101 import sheet_c101
from src.sheets.c102 import sheet_c102
from src.sheets.c103 import sheet_c103
from src.sheets.a001 import sheet_a001
from src.sheets.plans import sheet_a101, sheet_a102, sheet_a103
from src.sheets.elevations import sheet_a201, sheet_a202, sheet_a203
from src.sheets.a301 import sheet_a301
from src.sheets.a601 import sheet_a601
from src.sheets.a602 import sheet_a602
from src.sheets.a603 import sheet_a603
from src.sheets.a604 import sheet_a604
from src.sheets.s101 import sheet_s101
from src.sheets.s102 import sheet_s102
from src.sheets.s103 import sheet_s103
from src.sheets.s104 import sheet_s104
from src.sheets.m101 import sheet_m101
from src.sheets.m102 import sheet_m102
from src.sheets.e101 import sheet_e101
from src.sheets.e102 import sheet_e102
from src.sheets.p101 import sheet_p101
from src.sheets.p102 import sheet_p102
from src.sheets.p103 import sheet_p103
from src.sheets.p601 import sheet_p601


# ============================= the set =============================
@contextlib.contextmanager
def drawing(path, size, make_canvas=None):
    """Open ONE document for the length of this block, and close it after.

    `c` stays spelled `c` deliberately. Threading a context object through every sheet
    would mean rewriting some 2,500 drawing calls across 619 lines of this file, and
    the trace can only prove the DRAWING did not change — not that a comment stayed
    attached to the line it explains, and the comments here are the record of which
    permit defect each rule exists to prevent.

    What was fragile was never the name. It was first that `c` had no LIFETIME: it was
    assigned at the top of a build and left bound afterwards, so a sheet that raised
    left a half-built canvas in place for whatever ran next. It was then that a lifetime
    is not ISOLATION: one module slot is one document at a time for the whole process,
    so this assertion fired on any overlap rather than the two documents simply working.

    Now the canvas belongs to a BuildContext held in a ContextVar. It is still bound
    only inside this block and still cleared even if a sheet raises, and nesting two
    documents in one thread still asserts — but build_set() and build_zoning_sheet() on
    two threads are two contexts and draw independently."""
    cv = (make_canvas or canvas.Canvas)(path, pagesize=size)
    with page.document(cv, titleblock=project.TITLEBLOCK):
        yield cv
        cv.save()


def build_set(output_path=None, make_canvas=None):
    """Check the model, draw the twenty-seven sheets in binding order, write the PDF.

    Returns the path written. The order of the calls below is the order the sheets are
    BOUND in, and it has to match the index on G-001 — a reviewer turning past A-202
    expecting A-301 and finding A-601 concludes a sheet is missing. Nothing reorders the
    page tree afterwards: this body is the sheet index, and it is the only thing that
    decides. A stale insert(1, pop(4)) here once bound A-102 as page 2 of the issued set.

    Saving is not a sheet's job either. c.save() used to be the last two lines INSIDE the
    last sheet function, which worked only for as long as that function happened to be
    called last — reorder the set and it wrote a partial one, silently, because a save
    after nine sheets is a valid nine-page PDF.
    """
    path = output_path or OUT
    with drawing(path, (PW,PH), make_canvas):
        check_model()
        sheet_g001()
        sheet_c101()
        sheet_c103()
        sheet_a001()
        sheet_a101()
        sheet_a102()
        sheet_a103()
        sheet_a201()
        sheet_a202()
        sheet_a203()
        sheet_a301()
        sheet_a601()
        sheet_a602()
        sheet_a603()
        sheet_a604()
        sheet_s101()
        sheet_s102()
        sheet_s103()
        sheet_s104()
        sheet_m101()
        sheet_m102()
        sheet_e101()
        sheet_e102()
        sheet_p101()
        sheet_p102()
        sheet_p103()
        sheet_p601()
    return path


def build_zoning_sheet(output_path=None, make_canvas=None):
    """Draw C-102 and write it. Its own 11 x 17 document, per G-001 note 15.

    Same canvas global as the set, because C-102 draws through the same helpers; the
    drawing() block is what keeps the two documents from overlapping."""
    path = output_path or ZONING_OUT
    with drawing(path, page.ANSI_B.size, make_canvas):
        check_model()
        sheet_c102()
    return path


# Every file this project writes, in the order it writes them. A tool that re-runs the
# build reads this rather than the __main__ block below, so it can hand each function a
# scratch path and its own canvas; see lib/buildscript.py.
DOCUMENTS = (build_set, build_zoning_sheet)


if __name__ == "__main__":
    # Deliberately NOT sys.argv[1]. lib/export/dxf.py and lib/verify/trace.py run this
    # file with exec() and __name__ == "__main__", under THEIR argv — so reading argv
    # here means `python3 lib/export/dxf.py build.py out.dxf` writes the PDF over
    # build.py. The output path is a parameter of build_set(), which is where a caller
    # that wants one already is.
    print("saved", build_set())
    print("saved", build_zoning_sheet())
