"""The radon model: every gravel area a strip divides on exactly one riser, every riser
and lateral clear of what is below the slab, every roof exit out of the W4 band and clear
of the openings. Each rule the checker enforces is broken once here, so a checker that
stopped looking would fail."""
import io
import os
import sys
import contextlib
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from src import radon as R          # noqa: E402
from src import foundation as F     # noqa: E402
from codes import irc_appendix_f as irc_appendix_f_shared


def _swap(i, **kw):
    rs = list(R.RISERS)
    rs[i] = rs[i]._replace(**kw)
    return rs


def _has(v, text):
    return any(text in x for x in v)


class RealModelTests(unittest.TestCase):

    def test_the_real_model_passes(self):
        self.assertEqual(R.radon_violations(), [])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            R.check_radon()
        self.assertIn('RR-3', out.getvalue())

    def test_the_strips_divide_the_gravel(self):
        """W4's strip and the Units 2 / 3 strip run wall to wall in Building 1, Building 2's
           strip does; the Unit 1 stair wall strip stops short at both ends and divides nothing."""
        self.assertEqual(len(irc_appendix_f_shared.areas(F.B1, f=R.F)), 3)
        self.assertEqual(len(irc_appendix_f_shared.areas(F.B2, f=R.F)), 2)

    def test_one_riser_per_side_of_w4(self):
        self.assertEqual([(r.mark, r.serves, r.stack) for r in R.RISERS],
                         [('RR-1', 'UNIT 1', 'B'), ('RR-2', 'UNITS 2 AND 3', 'C'), ('RR-3', 'UNITS 4 AND 5', 'D')])

    def test_the_exits_are_roof_penetrations(self):
        from src import roof
        names = [n for r in roof.ROOFS for _x, _y, n in roof.penetrations(r)]
        for r in R.RISERS:
            self.assertIn('%s RADON VENT' % r.mark, names)

    def test_rr1_steps_out_of_the_w4_band_in_the_attic(self):
        from src.roof import B1_ROOF
        from codes.ohio.rco.attic_ventilation import VENT_CLR
        rr1 = R.RISERS[0]
        self.assertNotEqual(rr1.pos, rr1.exit)
        self.assertAlmostEqual(rr1.exit[1], B1_ROOF.w4_band[0]-VENT_CLR)


class BrokenModelTests(unittest.TestCase):

    def test_an_area_without_a_lateral(self):
        self.assertTrue(_has(R.radon_violations(_swap(1, laterals=[])), 'on 0 vent pipes'))

    def test_an_area_on_two_pipes(self):
        rs = _swap(2, laterals=R.RISERS[2].laterals*2)
        self.assertTrue(_has(R.radon_violations(rs), 'on 2 vent pipes'))

    def test_a_riser_not_beside_its_stack(self):
        x, y = R.RISERS[0].pos
        self.assertTrue(_has(R.radon_violations(_swap(0, pos=(x, y-1.0), exit=(x, y-1.0))), 'beside stack B'))

    def test_a_tee_on_a_drain(self):
        """Stack B's own foot."""
        st = [s for s in R._B1.stacks if s.name == 'B'][0]
        rs = _swap(0, stack='B', pos=st.pos, exit=(st.pos[0], 18.0))
        self.assertTrue(_has(R.radon_violations(rs), 'its tee is'))

    def test_a_lateral_through_w4(self):
        r = R.RISERS[1]
        w4 = [s for s in F.B1.strips if s[4] == 'W4'][0]
        lat = R.Lateral([r.pos, (r.pos[0], w4[1]-2.0)], 'W4')
        self.assertTrue(_has(R.radon_violations(_swap(1, laterals=[lat])), 'crosses W4'))

    def test_a_lateral_that_misses_its_strip(self):
        r = R.RISERS[1]
        lat = R.Lateral([r.pos, (r.pos[0]+2.0, r.pos[1])], r.laterals[0].strip)
        self.assertTrue(_has(R.radon_violations(_swap(1, laterals=[lat])), 'does not cross'))

    def test_a_lateral_across_the_building_drain(self):
        """RR-3's lateral stepped west of the collector crosses the 4" drain behind the strip."""
        r = R.RISERS[2]
        lat = R.Lateral([r.pos, (14.0, r.pos[1]), (14.0, r.laterals[0].path[-1][1])], r.laterals[0].strip)
        self.assertTrue(_has(R.radon_violations(_swap(2, laterals=[lat])), 'its lateral crosses the'))

    def test_an_exit_in_the_w4_band(self):
        self.assertTrue(_has(R.radon_violations(_swap(0, exit=R.RISERS[0].pos)), 'W4 band'))

    def test_an_offset_too_long(self):
        x, y = R.RISERS[2].pos
        self.assertTrue(_has(R.radon_violations(_swap(2, exit=(x, y-5.0))), 'in the attic, over'))

    def test_an_exit_on_a_bath_cap(self):
        from src import roof
        cap = [(x, y) for x, y, n in roof.penetrations(roof.B2_ROOF) if 'ROOF CAP' in n][0]
        self.assertTrue(_has(R.radon_violations(_swap(2, exit=cap)), 'ROOF CAP'))

    def test_an_exit_through_a_hatch(self):
        from src import roof
        h = [h for h in roof.B2_ROOF.hatches][0]
        centre = ((h.page[0]+h.page[2])/2.0, (h.page[1]+h.page[3])/2.0)
        self.assertTrue(_has(R.radon_violations(_swap(2, exit=centre)), 'attic hatch'))

    def test_an_exit_near_the_adjacent_parcel(self):
        x, y = R.RISERS[2].pos
        self.assertTrue(_has(R.radon_violations(_swap(2, exit=(25.0, y))), 'from the adjacent parcel'))

    def test_a_low_termination(self):
        old = R.ROOF_ABOVE
        try:
            R.ROOF_ABOVE = -15.0
            v = R.radon_violations()
        finally:
            R.ROOF_ABOVE = old
        self.assertTrue(_has(v, 'below the exhaust point'))
        self.assertTrue(_has(v, 'above grade'))

    def test_a_thin_retarder(self):
        old = F.RETARDER_MIL
        try:
            F.RETARDER_MIL = 4
            v = R.radon_violations()
        finally:
            F.RETARDER_MIL = old
        self.assertTrue(_has(v, 'retarder'))


class NotesTests(unittest.TestCase):

    def test_the_notes_cite_the_slab_sections_not_the_crawl_space_one(self):
        from src.fireblocking import FB
        text = ' '.join(R.notes_text(FB, 4.0))
        self.assertIn('AF103.6.1', text)
        self.assertIn('AF103.6.2', text)
        self.assertNotIn('AF103.5', text)
        self.assertIn('RADON REDUCTION SYSTEM', text)

    def test_the_schedule_prints_the_model(self):
        rows = R.schedule_rows()
        self.assertEqual([r[0] for r in rows], [r.mark for r in R.RISERS])
        self.assertTrue(all(r[-1].startswith('+') for r in rows))


if __name__ == '__main__':
    unittest.main()
