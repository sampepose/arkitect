"""100 EXAMPLE ST — the lot and what stands on it, read from intake.json: the ONE definition of
the program. Change the program in intake.json and run `python3 -m harness.intake
projects/example_100/intake.json` before anything else; the build's zoning check reads this.

Coordinates are codes/columbus/fit.py's: feet, x from the LEFT side lot line looking from
EXAMPLE STREET, y from the front lot line toward the rear.
"""
import json
import os

from codes.columbus.fit import Massing

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "intake.json")) as _fh:
    INTAKE = json.load(_fh)
MASSING = Massing.from_intake(INTAKE)
