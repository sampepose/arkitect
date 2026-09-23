"""What every jurisdiction's zoning fit reads and answers in, whatever the city.

A MASSING is the lot and what stands on it -- each building's footprint and where it stands,
the dwellings in each, the parking pad and any other structure -- read from an intake.json.
A fit answers with one ROW per rule: what is required, what the massing provides, whether it
meets it, and the section. The rules and their figures are the jurisdiction's
(arkitect/codes/<state>/<city>/fit.py, docs/jurisdictions.md); the shapes are shared, so the
intake, the scaffold and the day-one sheets print any city's rows the same way.

COORDINATES, in feet: x across the lot from the LEFT side lot line looking from the street,
y from the front lot line toward the rear. A corner lot names which side the side street is on.
"""
from collections import namedtuple

MEETS = 'MEETS'
FAILS = 'DOES NOT MEET'
RELIEF = 'RELIEF STATED'
NOT_CHECKED = 'NOT CHECKED'

# One rule's answer. `ok` is True, False or None (not checked); `status` is what prints.
Row = namedtuple('Row', 'rule label required provided ok status citation note')


class Massing:
    """The lot and what stands on it, from plain dicts (an intake.json's `lot`,
       `buildings`, `structures` and `parking`)."""

    def __init__(s, lot, buildings, structures=(), parking=None, relief=None):
        s.lot = dict(lot)
        s.buildings = [dict(b) for b in buildings]
        s.structures = [dict(t) for t in structures]
        s.parking = dict(parking) if parking else None
        s.relief = dict(relief or {})
        s.W, s.D = float(s.lot['width']), float(s.lot['depth'])
        s.area = s.W*s.D
        s.principal = [b for b in s.buildings if b['role'] == 'principal']
        s.adus = [b for b in s.buildings if b['role'] == 'adu']
        assert len(s.principal) == 1, 'a massing has exactly one principal building'
        s.P = s.principal[0]

    @classmethod
    def from_intake(cls, d):
        """From an intake.json's dict: the one conversion every caller uses."""
        return cls(d['lot'], d['buildings'], d.get('structures') or (), d.get('parking'),
                   d.get('relief'))

    # --- derived geometry
    def rear_line(s):
        return s.P['y']+s.P['depth']

    def rear_yard(s):
        return (s.D-s.rear_line())*s.W

    def side_distance(s, r, side):
        """A rectangle's distance to the left or right side lot line."""
        return r['x'] if side == 'left' else s.W-(r['x']+r['width'])

    def principal_dwellings(s):
        return len(s.P['dwellings'])

    def adu_dwellings(s):
        return sum(len(b['dwellings']) for b in s.adus)

    def dwelling_area(s, b, d):
        """(area, estimated): the dwelling's own figure if the intake has one, else its
           share of the building's gross floor area -- an ESTIMATE, and the row says so."""
        if d.get('area_sf'):
            return float(d['area_sf']), False
        return b['width']*b['depth']*b.get('storeys', 1)/len(b['dwellings']), True
