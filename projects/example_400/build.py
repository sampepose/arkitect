"""400 Oak Ave — what the project writes, in what order, and what must hold first.

A STARTING POINT, not a set. The project began as a verbatim copy of 300 S Elm's model
and sheets (commit 034798e). Building 2 is squeezed onto this lot as the rear ADU
building; Building 1 is the front single-family house, laid out from the designer's mockup. So
the set binds the sheets SHEETS lists, and C-102, the zoning site plan, is its own
11 x 17 document; each checks only what it depends on.

Every other module under src/ is 300's copy, kept as the source each sheet is pulled from
as it comes back. None of them is called from here, so none of their checks runs — a sheet
returns to the set together with the checks that guard it, never without them.

Importing this module draws nothing, writes nothing and prints nothing.
"""
import sys, os, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))        # this project
ROOT = os.path.dirname(os.path.dirname(HERE))            # the repository
for _p in (ROOT, HERE):                                  # arkitect/lib/ and arkitect/codes/, then src/
    if _p not in sys.path:
        sys.path.insert(0, _p)
from arkitect.lib.draw import page
from arkitect.lib.draw.page import PH, PW
from arkitect.lib.model import pipe
from src import levels, project
# W-A, the one egress unit: its frame can host the net clear minimums every product must give
from src.openings import WIN_GEOM, WIN_W
from arkitect.codes.ohio.rco.egress import check_egress_window
# the rear building: its Sage-wall terminations and its RCO 303.1 glazing
from src.building2 import (check_b2_inside, check_b2_terms, check_b2_glazing,
                          stack_bay_violations)
# the house: fit, glazing and escape openings, the stair, the dryer cap
from src.building1 import (check_b1_inside, check_b1_glazing, check_b1_stair, check_b1_dryer,
                           check_b1_vanity)
# the lot: yards, coverage, the rear yard, ADU area and height, parking, walks; and
# the RCO 302.1 imaginary line in the courtyard
from src.sitework import check_site, check_fsd
# RCO 307.1: 15" each side of every water closet, measured as the plans dimension it
from src.clearances import check_clearances, project_plans
from src.finishes import BOARD as WALL_BOARD
# RCO 702.7's vapor retarder, and the one stud bay a drain stands in against UL U305
from src.envelope import check_stack_bay, check_vapor_retarder
# both foundations: footing, strips under the bearing walls, pads, concrete, termites
from src.foundation import check_foundation
from src.framing import check_framing
# RCO 602.10: every exterior wall a braced wall line, from the plans' openings
from src.bracing import check_bracing
# trusses on their bearing walls, attic hatches in their halls between trusses, RCO 806 vents
from src.roof import check_roof
# RCO 401.3: every face's fall, the gutters to CB-1, the one step off each landing, the leaders
from src.grading import check_grading
# meters, outdoor units and the telecom box: on their wall, clear of openings and each other
from src.services import check_services
from src.mechanical import check_mechanical
from src.plumbing import check_plumbing
from src.doors import check_door_swings
from src.mechanical import b2_wall_penetrations
from src.drainage import F_POS as _F_POS, F_SIZE as _F_SIZE, check_drainage
from src.radon import check_radon
# every door has a mark and every sleeping room a W-A; the paint systems
from src.schedules import check_schedules
from src.finishes import check_finishes
# NEC 2023 over every unit's devices, its panel and both services
from src.electrical import check_electrical
from reportlab.pdfgen import canvas

OUT=os.path.join(HERE,project.PDF_OUT)
# C-102 is its own document: the zoning site plan goes to Building and Zoning Services at
# 11 x 17, which is not the set's sheet size.
ZONING_OUT=os.path.join(HERE,project.ZONING_OUT)
# Read by arkitect/lib/export/dxf.py, which may not import a project.
DXF_OUT=os.path.join(HERE,project.DXF_OUT)

# `c` is the per-document canvas every sheet function reads as a global; see
# arkitect/lib/draw/page.py's BuildContext.
c=page.canvas_proxy()

_CHECKED = False


def check_model():
    """What the sheets depend on, checked before a line is drawn. The Unit 3 stair
       check runs inside sheet_a102() itself, as it does on 300."""
    global _CHECKED
    if not __debug__:
        raise SystemExit(
            "refusing to build: python was run with -O (or PYTHONOPTIMIZE is set), "
            "which removes every assert statement, and every model check here is one.")
    if _CHECKED:
        return
    levels.check()
    check_egress_window(win_geom=WIN_GEOM, win_w=WIN_W)
    check_b2_inside()
    check_b2_terms()
    check_b2_glazing()
    check_b1_inside()
    check_b1_glazing()
    check_b1_stair()
    check_b1_dryer()
    check_b1_vanity()
    check_site()
    check_fsd()
    check_clearances(project_plans(), WALL_BOARD)
    check_foundation()
    check_framing()
    check_bracing()
    check_roof()
    check_grading()
    check_elevations()
    check_services()
    check_mechanical()
    check_plumbing()
    check_drainage()
    check_radon()
    check_schedules()
    check_finishes()
    check_electrical()
    check_vapor_retarder()
    check_door_swings()
    check_stack_bay(stack_bay_violations(_F_POS[1], pipe.fitting_od(_F_SIZE),
                                        b2_wall_penetrations()))
    _CHECKED = True


from src.sheets.g001 import SEPARATE, SHEET_INDEX, sheet_g001
from src.sheets.c101 import sheet_c101
from src.sheets.c103 import sheet_c103
from src.sheets.a001 import sheet_a001
from src.sheets.a101 import sheet_a101
from src.sheets.a102 import sheet_a102
from src.sheets.elevations import check_elevations, sheet_a201, sheet_a202
from src.sheets.a301 import sheet_a301
from src.sheets.a601 import sheet_a601
from src.sheets.a602 import sheet_a602
from src.sheets.a603 import sheet_a603
from src.sheets.c102 import sheet_c102
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


# The set in binding order. G-001's index lists these, and C-102, bound separately.
SHEETS = (sheet_g001, sheet_c101, sheet_c103, sheet_a001, sheet_a101, sheet_a102, sheet_a201, sheet_a202, sheet_a301, sheet_a601, sheet_a602, sheet_a603, sheet_s101, sheet_s102, sheet_s103, sheet_s104, sheet_m101, sheet_m102, sheet_e101, sheet_e102, sheet_p101, sheet_p102, sheet_p103, sheet_p601)
assert ['%s-%s' % (f.__name__[6].upper(), f.__name__[7:]) for f in SHEETS] == \
    [n for n, _t in SHEET_INDEX if n not in SEPARATE], "G-001's sheet index is not the set build_set binds"


@contextlib.contextmanager
def drawing(path, size, make_canvas=None):
    """Open ONE document for the length of this block, and close it after."""
    cv = (make_canvas or canvas.Canvas)(path, pagesize=size)
    with page.document(cv, titleblock=project.TITLEBLOCK):
        yield cv
        cv.save()


def build_set(output_path=None, make_canvas=None):
    """Check the model, draw the sheets in binding order, write the PDF. Returns the path."""
    path = output_path or OUT
    with drawing(path, (PW,PH), make_canvas):
        check_model()
        for sheet in SHEETS:
            sheet()
    return path


def build_zoning_sheet(output_path=None, make_canvas=None):
    """Check the model, draw C-102, write it. Returns the path."""
    path = output_path or ZONING_OUT
    with drawing(path, page.ANSI_B.size, make_canvas):
        check_model()
        sheet_c102()
    return path


# Every file this project writes. A tool that re-runs the build reads this; see
# arkitect/lib/buildscript.py.
DOCUMENTS = (build_set, build_zoning_sheet)


if __name__ == "__main__":
    print("saved", build_set())
    print("saved", build_zoning_sheet())
