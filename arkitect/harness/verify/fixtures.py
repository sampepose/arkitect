"""A synthetic intake: an interior 35'-0" x 120'-0" lot with an alley, a house at the
front and one detached ADU behind it. "100 EXAMPLE ST" is invented on purpose -- a test
that scaffolds a plausible real address would put a real parcel's name on a fake set."""
import copy

EXAMPLE = {
    'slug': 'example_100',
    'address': '100 EXAMPLE ST',
    'city_line': 'COLUMBUS, OHIO 43200',
    'parcel': 'TBD',
    'street': 'EXAMPLE STREET',
    'jurisdiction': 'columbus',
    'district': 'R-4',
    'lot': {'width': 35.0, 'depth': 120.0, 'corner': False, 'alley': True, 'alley_width': 20.0,
            'front_line': 20.0, 'survey': False},
    'buildings': [
        {'name': 'BUILDING 1', 'role': 'principal', 'x': 5.0, 'y': 20.0, 'width': 24.0,
         'depth': 36.0, 'storeys': 2,
         'dwellings': [{'name': 'UNIT 1', 'bedrooms': 3}]},
        {'name': 'BUILDING 2', 'role': 'adu', 'x': 5.0, 'y': 74.0, 'width': 22.0,
         'depth': 24.0, 'storeys': 1,
         'dwellings': [{'name': 'UNIT 2', 'bedrooms': 1}]},
    ],
    'parking': {'stalls': 2, 'x0': 0.0, 'width': 18.0, 'depth': 18.0},
    'relief': {'lot_width': 'VARIANCE REQUESTED'},
    'owner': ['EXAMPLE OWNER LLC', '1 EXAMPLE PLAZA', 'COLUMBUS, OH 43200'],
    'contractor': ['EXAMPLE CONTRACTOR LLC'],
    'decisions': {'all_electric': True},
}


def example(**changes):
    """A fresh copy, with top-level keys replaced."""
    d = copy.deepcopy(EXAMPLE)
    d.update(changes)
    return d
