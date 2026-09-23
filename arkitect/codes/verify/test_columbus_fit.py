"""arkitect/codes/ohio/columbus/fit.py on synthetic lots. Both projects hold it to their own zoning
tables (each project's verify/test_zoning_fit.py); these pin how it behaves at the edges
a new address will find first."""
import unittest

from arkitect.codes.ohio.columbus import fit as F


def lot(**kw):
    base = {'width': 40.0, 'depth': 126.0, 'corner': False, 'alley': True, 'alley_width': 20.0,
            'front_line': 20.0}
    base.update(kw)
    return base


def house(**kw):
    b = {'name': 'BUILDING 1', 'role': 'principal', 'x': 5.0, 'y': 20.0, 'width': 26.0,
         'depth': 40.0, 'storeys': 2, 'dwellings': [{'name': 'UNIT 1'}]}
    b.update(kw)
    return b


def adu(n=1, **kw):
    b = {'name': 'BUILDING 2', 'role': 'adu', 'x': 5.0, 'y': 75.0, 'width': 24.0,
         'depth': 24.0, 'storeys': n, 'dwellings': [{'name': 'UNIT %d' % (i+2)} for i in range(n)]}
    b.update(kw)
    return b


PAD = {'stalls': 2, 'x0': 0.0, 'width': 18.0, 'depth': 18.0}


def rows(**kw):
    m = F.Massing(kw.pop('lot', lot()), kw.pop('buildings', [house(), adu()]),
                  kw.pop('structures', ()), kw.pop('parking', PAD), kw.pop('relief', None))
    return {r.rule: r for r in F.fit(m)}


class FitTests(unittest.TestCase):

    def test_a_plain_program_on_a_40_foot_lot(self):
        r = rows()
        self.assertEqual(r['lot_width'].status, F.FAILS)            # 40 < 50: C.C. 3332.05
        self.assertEqual(r['rear_yard'].status, F.MEETS)
        self.assertEqual(r['side_yard'].required, '3\'-0"')        # a lot 40 ft or less
        self.assertNotIn('street_vision', r)                          # interior lot

    def test_stated_relief_is_not_a_pass(self):
        r = rows(relief={'lot_width': 'VARIANCE REQUESTED'})
        self.assertEqual(r['lot_width'].status, F.RELIEF)
        self.assertIs(r['lot_width'].ok, False)
        self.assertIn('VARIANCE REQUESTED', r['lot_width'].note)

    def test_heights_are_not_checked_until_modelled(self):
        r = rows()
        self.assertIsNone(r['height'].ok)
        self.assertEqual(r['height'].status, F.NOT_CHECKED)
        r = rows(buildings=[house(height=23.0), adu(height=20.0)])
        self.assertEqual(r['adu_height'].status, F.MEETS)
        r = rows(buildings=[house(height=20.0), adu(height=22.0)])
        self.assertEqual(r['adu_height'].status, F.FAILS)           # taller than the principal

    def test_one_adu_takes_45_percent_two_take_55(self):
        self.assertEqual(rows(buildings=[house(), adu(1)])['adu_share'].required, '45% MAX')
        self.assertEqual(rows(buildings=[house(), adu(2)])['adu_share'].required, '55% MAX')

    def test_an_adu_forward_of_the_rear_wall_fails(self):
        self.assertEqual(rows(buildings=[house(), adu(y=50.0)])['adu_in_rear'].status, F.FAILS)

    def test_an_area_the_intake_does_not_give_is_an_estimate(self):
        self.assertIn('ESTIMATE', rows()['adu_area'].note)
        b = [house(dwellings=[{'name': 'UNIT 1', 'area_sf': 1800}]),
             adu(dwellings=[{'name': 'UNIT 2', 'area_sf': 600}])]
        self.assertEqual(rows(buildings=b)['adu_area'].note, '')

    def test_parking_counts_principal_dwellings_only(self):
        b = [house(dwellings=[{'name': 'U1'}, {'name': 'U2'}]), adu(2)]
        self.assertEqual(rows(buildings=b)['parking'].required, '4 (ADUs EXEMPT)')

    def test_a_narrow_alley_needs_maneuvering_relief(self):
        self.assertEqual(rows(lot=lot(alley_width=16.0))['maneuvering'].status, F.FAILS)
        deeper = dict(PAD, depth=22.0)
        self.assertEqual(rows(lot=lot(alley_width=16.0), parking=deeper)['maneuvering'].status,
                         F.MEETS)

    def test_a_corner_lot_checks_the_triangles_and_the_side_street(self):
        r = rows(lot=lot(corner=True, side_street='left', side_street_line=8.0),
                 buildings=[house(x=8.0, y=20.0), adu(x=8.0)],
                 parking=dict(PAD, x0=10.0))
        self.assertEqual(r['street_vision'].status, F.FAILS)        # 8 + 20 < 30
        self.assertEqual(r['side_street'].status, F.MEETS)
        self.assertEqual(r['alley_vision'].status, F.MEETS)
        self.assertEqual(r['parking_setback'].status, F.MEETS)

    def test_a_missing_front_line_is_not_checked(self):
        self.assertEqual(rows(lot=lot(front_line=None))['front_yard'].status, F.NOT_CHECKED)

    def test_every_unverified_figure_says_so(self):
        for rule in ('density', 'side_yard', 'coverage', 'stall_depth'):
            self.assertEqual(F.CITE[rule], 'SECTION UNVERIFIED', rule)


if __name__ == '__main__':
    unittest.main()
