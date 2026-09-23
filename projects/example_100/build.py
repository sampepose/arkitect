"""100 EXAMPLE ST — what the project writes, in what order, and what must hold first.

Scaffolded by harness/scaffold.py from intake.json on 2026-09-22. The set grows one feature
at a time: `python3 -m harness.progress next example_100`. Importing this module draws nothing,
writes nothing and prints nothing.
"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))        # this project
ROOT = os.path.dirname(os.path.dirname(HERE))            # the repository
for _p in (ROOT, HERE):                                  # lib/ and codes/, then src/
    if _p not in sys.path:
        sys.path.insert(0, _p)
from codes.columbus import fit
from codes.columbus.zoning_sheets import cover_sheet, zoning_site_plan
from lib.buildkit import documents
from src import project, sitework

_CHECKED = False


def check_model():
    """What the sheets depend on, checked before a line is drawn."""
    global _CHECKED
    if not __debug__:
        raise SystemExit("refusing to build: python -O removes every assert, and every "
                         "model check here is one.")
    if _CHECKED:
        return
    fit.check(sitework.MASSING)
    _CHECKED = True


# The set in binding order; G-001's index lists it, and C-102, bound separately.
INDEX = [("G-001", "COVER SHEET"), ("C-102", "ZONING SITE PLAN — 11 x 17, ISSUED SEPARATELY")]
SHEETS = (cover_sheet(sitework.INTAKE, sitework.MASSING, INDEX),)

# Read by lib/export/dxf.py, which may not import a project.
DXF_OUT = os.path.join(HERE, project.DXF_OUT)

DOCUMENTS = documents(project.TITLEBLOCK, check_model, SHEETS, os.path.join(HERE, project.PDF_OUT),
                      zoning_site_plan(sitework.INTAKE, sitework.MASSING),
                      os.path.join(HERE, project.ZONING_OUT))
build_set, build_zoning_sheet = DOCUMENTS


if __name__ == "__main__":
    for _doc in DOCUMENTS:
        print("saved", _doc())
