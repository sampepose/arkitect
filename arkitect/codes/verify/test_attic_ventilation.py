"""RCO 806.2 on a roof built for the test: where the slots stop, and what they give."""
import os
import sys
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from arkitect.codes.ohio.rco import attic_ventilation as V


def _roof(band=None, gables=((0.0, 'FRONT'), (30.0, 'REAR'))):
    """20 ft across, ridge at 10, one attic 30 ft along the ridge."""
    return SimpleNamespace(W=20.0, ridge_x=10.0, gables=list(gables), w4_band=band,
                           attics=[V._attic('ATTIC', 20.0, 0.0, 30.0)])


class AtticVentilationTests(unittest.TestCase):

    def test_the_requirement_is_one_150th_of_the_attic_floor(self):
        a = V._attic('ATTIC', 20.0, 0.0, 30.0)
        self.assertEqual((a.area, a.nfa), (600.0, 4.0))

    def test_slots_stop_short_of_each_gable(self):
        (v,) = V.attic_vents(_roof(), [])
        self.assertAlmostEqual(v.eave_lf, 2*28.0); self.assertAlmostEqual(v.ridge_lf, 28.0)
        self.assertAlmostEqual(v.intake, 56*9.0); self.assertAlmostEqual(v.exhaust, 28*18.0)
        self.assertAlmostEqual(v.required, 4.0*144); self.assertGreater(v.provided, v.required)

    def test_an_end_that_is_not_a_gable_takes_the_slot_to_it(self):
        (v,) = V.attic_vents(_roof(gables=((0.0, 'FRONT'),)), [])
        self.assertAlmostEqual(v.ridge_lf, 29.0)

    def test_a_penetration_near_a_slots_line_breaks_that_slot_only(self):
        (v,) = V.attic_vents(_roof(), [(10.5, 15.0, 'STACK')])
        self.assertAlmostEqual(v.ridge_lf, 26.0); self.assertAlmostEqual(v.eave_lf, 56.0)
        (far,) = V.attic_vents(_roof(), [(5.0, 15.0, 'CAP')])          # 5 ft from both lines
        self.assertAlmostEqual(far.ridge_lf, 28.0); self.assertAlmostEqual(far.eave_lf, 56.0)

    def test_a_band_where_no_vent_may_be_cut_breaks_all_three(self):
        (v,) = V.attic_vents(_roof(band=(10.0, 12.0)), [])
        self.assertAlmostEqual(v.ridge_lf, 26.0); self.assertAlmostEqual(v.eave_lf, 52.0)
        kinds = sorted(r.kind for r in V.vent_runs(_roof(band=(10.0, 12.0)), []))
        self.assertEqual(kinds, ['EAVE']*4+['RIDGE']*2)

    def test_cut_takes_an_interval_out_of_spans(self):
        self.assertEqual(V._cut([(0, 10)], 4, 6), [(0, 4), (6, 10)])
        self.assertEqual(V._cut([(0, 10)], -1, 3), [(3, 10)])
        self.assertEqual(V._cut([(0, 10)], 12, 14), [(0, 10)])
        self.assertEqual(V._cut([(0, 10)], -1, 11), [])


if __name__ == '__main__':
    unittest.main()
