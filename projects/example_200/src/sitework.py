"""200 EXAMPLE AVE — the lot and what stands on it, read from intake.json: the ONE definition of
the program. Change the program in intake.json and run `arkitect intake
projects/example_200/intake.json` before anything else; the build's zoning check reads this.

Coordinates are arkitect/codes/massing.py's: feet, x from the LEFT side lot line looking from
EXAMPLE AVENUE, y from the front lot line toward the rear.
"""
import json
import os

from arkitect.codes.massing import Massing

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "intake.json")) as _fh:
    INTAKE = json.load(_fh)
MASSING = Massing.from_intake(INTAKE)
