"""The grading model: what C-103 draws, held to RCO 401.3 face by face. Each rule the
checker enforces is broken once here, so a checker that stopped looking would fail."""
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

from lib.model import grade
from codes.ohio.rco import site_steps


def _swap(bands, i, **kw):
    out = list(bands); out[i] = out[i]._replace(**kw); return out


class RealModelTests(unittest.TestCase):

    def test_the_real_model_passes(self):
        from src import grading as g
        self.assertEqual(g.grading_violations(), [])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            g.check_grading()
        self.assertIn("401.3 EXCEPTION", out.getvalue())

    def test_the_code_figures(self):
        from lib.units import IN
        from src import grading as g
        self.assertEqual((g.FALL, g.FALL_RUN, g.IMPERVIOUS_MIN), (IN(6), 10.0, 0.02))
        self.assertEqual((grade.LANDING_MAX, g.RISER_MAX, g.WALK_MAX), (0.02, IN(8.25), 0.05))
        self.assertEqual(g.STOOP_STEP, IN(7.25))          # the stoop's height: 1" under an 8-1/4" floor
        self.assertEqual(g.LAWN_MAX, 1.0/3.0)

    def test_g1_is_narrow_and_clear_of_the_unit_3_stoop(self):
        """The courtyard holds the stoop, G-1 and the walk only if G-1 is narrow and reads
           its line from the stoop: midway left a 10-1/4" drop off the stoop's corner."""
        from src import grading as g
        self.assertEqual((g.G1.w, g.G2.w, g.G3.w), (g.COURT_W, g.GUTTER_W, g.GUTTER_W))
        self.assertLess(g.COURT_W, g.GUTTER_W)
        self.assertAlmostEqual(g.G1.box()[1]-g.U3_STOOP.y1, g.GUTTER_STOOP_CLR)
        self.assertGreaterEqual(g.U45_WALK.y0-g.G1.box()[3], g.GUTTER_WALK_CLR-1e-9)
        # and every bank in that yard is mowable
        for b in g.BANDS:
            if b.to != "G-1": continue
            for s in grade.stations(b):
                pts = b.section(s)
                for (d0, g0, _a), (d1, g1, k) in zip(pts, pts[1:]):
                    if k == "lawn" and d1 > d0:
                        self.assertLessEqual((g0-g1)/(d1-d0), g.LAWN_MAX+1e-9, "%s at %s" % (b.face.side, s))

    def test_every_landing_and_stoop_has_its_step(self):
        """The designer's point: the step off each stoop is checked and held, not left to the lawn."""
        from lib.units import IN
        from src import grading as g
        self.assertEqual(g.step_violations(), [])
        rows = {r[0]: r for r in site_steps.step_summary(g.STEPS, g.BANDS, g.STOOP_STEP)}
        self.assertEqual(set(rows), {"UNIT 1 LANDING", "UNIT 2 LANDING", "UNIT 3 STOOP", "UNIT 5 STOOP", "UNIT 4 LANDING"})
        for name, _top, _nose, _foot, step, _walk in rows.values():
            self.assertGreater(step[0], 0.0, name)
            self.assertLessEqual(step[1], g.RISER_MAX+1e-9, name)
        for name in ("UNIT 3 STOOP", "UNIT 5 STOOP"):
            self.assertAlmostEqual(rows[name][4][0], IN(7.25), msg=name)
            self.assertAlmostEqual(rows[name][2][0], g.STOOP_TOP-3.5*grade.LANDING_MAX, msg=name)   # the nosing, +6-3/8"
        # past Building 1's rear wall no band reaches: those feet are held
        held = [f for f in site_steps.feet(g.STEPS, g.BANDS, g.STOOP_STEP) if f[6]]
        self.assertTrue(held and all(f[0].rect is g.U3_STOOP for f in held))

    def test_the_stairs_pitch_with_their_stoops(self):
        """The designer's choice: treads and landings fall as the stoop does, so the bottom riser is
           the same at both stringers: 121" over 15, 8-1/16"."""
        from lib.units import IN
        from src import grading as g
        self.assertEqual(site_steps.stair_violations(g.STAIRS, g.STEPS), [])
        self.assertEqual([n for n, _p, _r in site_steps.stair_risers(g.STAIRS, g.STEPS)], ["UNIT 3 STAIR", "UNIT 5 STAIR"])
        for name, pitch, rs in site_steps.stair_risers(g.STAIRS, g.STEPS):
            self.assertEqual(pitch, grade.LANDING_MAX, name)
            self.assertAlmostEqual(min(rs), IN(121/15.0), msg=name)
            self.assertAlmostEqual(max(rs), IN(121/15.0), msg=name)

    def test_a_level_stair_over_a_pitched_stoop_fails(self):
        """The condition the designer had fixed: a level bottom tread over the stoop's 2% cross-fall."""
        from lib.model.stairs import ExteriorStair
        from src import grading as g
        s = g.U3_STAIR
        level = ExteriorStair(s.risers, s.treads, s.tread, s.width, s.landing_len, s.landing_depth,
                              s.stoop_above_grade, s.deck, s.framing, 0.0)
        v = site_steps.stair_violations([("UNIT 3 STAIR", level, g.U3_STOOP, "y0")], g.STEPS)
        for needle in ("not the stoop's", "over 3/8\" apart", "over 8-1/4\""):
            self.assertTrue(any(needle in x for x in v), "%r not in %r" % (needle, v))

    def test_the_room_each_face_has(self):
        """The reviewer's point: 6'-0" on the parcel side, 8'-0" on Sage."""
        from src import grading as g
        self.assertEqual((g.PARCEL_OPEN, g.SAFF_OPEN, g.COURT_OPEN, g.FRONT_OPEN, g.REAR_OPEN),
                         (6.0, 8.0, 12.0, 20.0, 18.0))

    def test_every_short_face_says_how_it_complies(self):
        from src import grading as g
        m = {(f.building, f.side): g.face_summary(f)[2] for f in g.FACES}
        for b in ("BUILDING 1", "BUILDING 2"):
            self.assertTrue(m[(b, "ADJACENT-PARCEL FACE")].startswith("401.3 EXCEPTION"))
            self.assertTrue(m[(b, "SAGE FACE")].startswith('6" TO THE SAGE LOT LINE'))
        self.assertTrue(m[("BUILDING 1", "FACE TO BUILDING 2")].startswith("401.3 EXCEPTION"))
        self.assertTrue(m[("BUILDING 2", "FACE TO BUILDING 1")].startswith("401.3 EXCEPTION"))
        self.assertTrue(m[("BUILDING 1", "S ELM FACE")].startswith('6" IN 10\'-0"'))

    def test_nothing_goes_onto_the_adjacent_parcel(self):
        from src import grading as g
        for gt in g.GUTTERS:
            self.assertLessEqual(gt.box()[2], g.SITE_W-g.GUTTER_LOT_CLR+1e-9)

    def test_no_gutter_discharges_onto_a_street(self):
        """Public Service takes no concentrated flow across the S Elm sidewalk: G-3 ends
           at the inlet on the lot, and the lawn past it rises to the lot line."""
        from src import grading as g
        self.assertEqual(g.G3.to, g.INLET.mark)
        self.assertEqual(g.G3.b, g.INLET.at)
        self.assertTrue(all(gt.to not in g.STREETS for gt in g.GUTTERS))
        self.assertGreater(g.INLET.at[1], g.INLET.size/2.0)
        self.assertGreater(g.FRONT_LOT, g.INLET.rim+g.GUTTER_DEPTH)

    def test_the_curb_outlet(self):
        """Standard Drawing 2320: 3" pipes at 1.56%, as many as the 10-year flow needs and
           no more, under the sidewalk with cover, falling to the curb."""
        from lib.units import IN
        from src import grading as g
        self.assertEqual((g.STD2320_D, g.STD2320_SLOPE), (IN(3), 0.0156))
        o = g.outlet()
        self.assertEqual(o['area'], sum(g.tributary()))
        self.assertGreaterEqual(o['pipes']*o['q_pipe'], o['flow'])
        self.assertLess((o['pipes']-1)*o['q_pipe'], o['flow'])
        self.assertLess(o['crown_lot'], g.FRONT_LOT)
        self.assertLess(o['invert_curb'], o['invert_inlet'])
        self.assertEqual(g.outlet_violations(), [])

    def test_the_sewer_crossing(self):
        """G-1 is the only gutter over the building sewer, and it leaves cover."""
        from src import grading as g
        xs = g.sewer_crossings()
        self.assertEqual([m for m, _p, _f, _c in xs], ["G-1"])
        self.assertGreater(xs[0][3], g.GUTTER_DEPTH)

    def test_signed(self):
        from lib.units import IN
        self.assertEqual((grade.signed(IN(5.5)), grade.signed(0.0), grade.signed(-IN(6))), ('+5-1/2"', '0"', '-6"'))

    def test_grade_along_a_step(self):
        pts = [(0.0, 0.5, None), (3.0, 0.44, "landing"), (3.0, -0.2, "step"), (8.0, -0.4, "walk")]
        self.assertAlmostEqual(grade.grade_along(pts, 3.0), -0.2)
        self.assertAlmostEqual(grade.grade_along(pts, 5.5), -0.3)


class MutationTests(unittest.TestCase):

    def setUp(self):
        from src import grading as g
        self.g = g
        self.front = next(i for i, b in enumerate(g.BANDS) if b.face == g.F_B1_FRONT and b.to == "S ELM")
        self.saff = next(i for i, b in enumerate(g.BANDS) if b.face == g.F_B1_SAFF)
        self.parcel = next(i for i, b in enumerate(g.BANDS) if b.face == g.F_B1_PARCEL)

    def fails(self, needle, bands=None, gutters=None, paved=None):
        v = self.g.grading_violations(bands, gutters, paved)
        self.assertTrue(any(needle in x for x in v), "%r not in %r" % (needle, v[:4]))

    def test_five_inches_in_ten_feet_fails(self):
        from lib.units import IN
        g = self.g
        sec = lambda s: [(0.0, 0.0, None), (10.0, -IN(5), "lawn"), (20.0, g.FRONT_LOT, "lawn")]
        self.fails("under the 6\"", _swap(g.BANDS, self.front, section=sec))

    def test_five_inches_to_the_safford_line_fails(self):
        from lib.units import IN
        g = self.g
        sec = lambda s: [(0.0, 0.0, None), (8.0, -IN(5), "lawn")]
        self.fails("under the 6\"", _swap(g.BANDS, self.saff, section=sec))

    def test_draining_onto_the_neighbour_fails(self):
        g = self.g
        sec = lambda s: [(0.0, 0.0, None), (6.0, -0.5, "lawn")]
        self.fails("neither a street", _swap(g.BANDS, self.parcel, section=sec, to="ADJACENT PARCEL"))

    def test_grade_below_the_frost_datum_fails(self):
        g = self.g
        sec = lambda s: [(0.0, -0.1, None), (8.0, -0.6, "lawn")]
        self.fails("grade at the foundation", _swap(g.BANDS, self.saff, section=sec))

    def test_a_flat_walk_fails(self):
        g = self.g
        sec = lambda s: [(0.0, 0.0, None), (3.0, -0.03, "walk"), (8.0, g.SAFFORD_LOT, "lawn")]
        self.fails("under the 2%", _swap(g.BANDS, self.saff, section=sec))

    def test_a_steep_walk_fails(self):
        g = self.g
        sec = lambda s: [(0.0, 0.0, None), (8.0, -0.6, "walk")]
        self.fails("steeper than 1 in 20", _swap(g.BANDS, self.saff, section=sec))

    def test_a_steep_landing_fails(self):
        g = self.g
        sec = lambda s: [(0.0, 0.45, None), (3.0, 0.45-0.09, "landing"), (3.0, -0.2, "step"), (8.0, -0.375, "walk")]
        self.fails("not 2%", _swap(g.BANDS, self.saff, section=sec))

    def test_a_tall_step_fails(self):
        from lib.units import IN
        g = self.g
        sec = lambda s: [(0.0, 0.45, None), (3.0, 0.39, "landing"), (3.0, 0.39-IN(8.5), "step"), (8.0, 0.39-IN(8.5)-0.12, "walk")]
        self.fails("311.7.5.1", _swap(g.BANDS, self.saff, section=sec))

    def test_a_stoop_dropping_to_the_face_grade_fails(self):
        """The Unit 3 stoop's foot left on the Sage lawn's line — the 6"-in-8'-0" grade
           the designer read — is a step the checker now sees, once the stoop is flat."""
        g = self.g
        i = next(i for i, b in enumerate(g.BANDS) if b.face == g.F_B1_SAFF and b.s0 == g.U3_STOOP.y0)
        d = g.B1X0-g.U3_STOOP.x0
        sec = lambda s: [(0.0, g.STOOP_TOP, None), (d, g.STOOP_TOP, "stoop"),
                         (d, g.SAFFORD_LOT*d/g.SAFF_OPEN-0.2, "step"), (g.SAFF_OPEN, g.SAFFORD_LOT-0.2, "lawn")]
        self.fails("a step of", _swap(g.BANDS, i, section=sec))

    def test_a_tall_step_off_a_side_fails(self):
        """A step off the SIDE of a landing — square to no face, so only feet() sees it."""
        g = self.g
        i = next(i for i, b in enumerate(g.BANDS) if b.face == g.F_B2_FRONT and b.s0 == g.U5_STOOP.x1)
        off = abs(g.COURT_Y-g.F_B2_FRONT.at)
        def sec(s):
            fl = g.G1.grade_at(*grade.point(g.F_B2_FRONT, s, off))
            return [(0.0, g.G0, None), (3.0, g.G0-0.75, "lawn"),
                    (off-g.G1.w/2.0, fl+g.GUTTER_DEPTH, "lawn"), (off, fl, "gutter")]
        self.fails("UNIT 4 LANDING x0 side", _swap(g.BANDS, i, section=sec))

    def test_the_unit_3_walk_head_agrees_with_its_section(self):
        g = self.g
        i = next(i for i, b in enumerate(g.BANDS) if b.face == g.F_B2_SAFF)
        sec = lambda s: [(0.0, 0.0, None), (8.0-g.U3_WALK.x0, -0.1, "walk"), (8.0, g.SAFFORD_LOT, "lawn")]
        self.fails("not level with its section", _swap(g.BANDS, i, section=sec))

    def test_a_cliff_of_lawn_fails(self):
        """Holding ground beside a stoop with nowhere to fall made a 333% bank, and nothing
           in the checker saw it."""
        g = self.g
        sec = lambda s: [(0.0, 0.0, None), (1.0, -0.04, "lawn"), (1.2, -0.5, "lawn"), (8.0, g.SAFFORD_LOT-0.2, "lawn")]
        self.fails("steeper than the 3:1", _swap(g.BANDS, self.saff, section=sec))

    def test_a_section_off_its_gutter_fails(self):
        g = self.g
        sec = lambda s: [(0.0, 0.0, None), (3.0, -0.5, "lawn"), (4.0, -0.6, "gutter")]
        self.fails("ends off G-3", _swap(g.BANDS, self.parcel, section=sec))

    def test_a_gap_in_the_bands_fails(self):
        g = self.g
        self.fails("not banded", [b for i, b in enumerate(g.BANDS) if i != self.saff])

    def test_a_flat_gutter_fails(self):
        g = self.g
        g2 = g.Gutter("G-2", g.G2.a, g.G2.b, g.G2.start, "G-3", slope=0.004)
        self.fails("under 0.5%", gutters=[g.G1, g2, g.G3])

    def test_a_gutter_on_the_lot_line_fails(self):
        g = self.g
        g3 = g.Gutter("G-3", (g.SITE_W-0.5, g.COURT_Y), (g.SITE_W-0.5, 0.0), g.G3.start, "S ELM")
        self.fails("adjacent-parcel lot line", gutters=[g.G1, g.G2, g3])

    def test_a_gutter_arriving_low_fails(self):
        g = self.g
        g3 = g.Gutter("G-3", g.G3.a, g.G3.b, g.G3.start+0.1, "S ELM")
        self.fails("arrives below the head of G-3", gutters=[g.G1, g.G2, g3])

    def test_a_gutter_going_nowhere_fails(self):
        g = self.g
        g3 = g.Gutter("G-3", g.G3.a, g.G3.b, g.G3.start, "ADJACENT PARCEL")
        self.fails("never reaches an inlet", gutters=[g.G1, g.G2, g3])

    def test_a_gutter_onto_the_sidewalk_fails(self):
        """The design as first issued: G-3 run out to the S Elm lot line."""
        g = self.g
        g3 = g.Gutter("G-3", g.G3.a, (g.GX, 0.0), g.G3.start, "S ELM")
        self.fails("concentrated flow onto the S ELM right-of-way", gutters=[g.G1, g.G2, g3])

    def test_a_gutter_short_of_its_inlet_fails(self):
        g = self.g
        g3 = g.Gutter("G-3", g.G3.a, (g.GX, g.INLET.at[1]+3.0), g.G3.start, g.INLET.mark)
        self.fails("does not end at inlet", gutters=[g.G1, g.G2, g3])

    def test_an_inlet_the_lawn_does_not_rise_from_fails(self):
        """An inlet whose rim stands at the lot-line grade lets the gutter run on past it."""
        g = self.g
        inlet = g.INLET._replace(rim=g.FRONT_LOT)
        g3 = g.Gutter("G-3", g.G3.a, g.G3.b, g.FRONT_LOT+g.GUTTER_SLOPE*g.G3.length, g.INLET.mark)
        v = g.gutter_violations([g.G1, g.G2, g3], inlets=[inlet])
        self.assertTrue(any("does not rise to the S ELM lot line" in x for x in v), v[:4])

    def test_a_gutter_through_paving_fails(self):
        g = self.g
        pad = g.Rect("PARKING PAD", "pad", 30.0, 60.0, 40.0, 70.0)
        self.fails("runs through the PARKING PAD", paved=[pad])

    def test_too_few_curb_pipes_fails(self):
        g = self.g
        v = g.outlet_violations(pipes=g.outlet()['pipes']-1)
        self.assertTrue(any("under the" in x and "cfs" in x for x in v), v)

    def test_a_flat_curb_pipe_fails(self):
        v = self.g.outlet_violations(slope=0.01)
        self.assertTrue(any("Standard Drawing 2320" in x and "1.56%" in x for x in v), v)

    def test_a_small_curb_pipe_fails(self):
        from lib.units import IN
        v = self.g.outlet_violations(d=IN(2))
        self.assertTrue(any('3" minimum' in x for x in v), v)

    def test_a_curb_pipe_without_cover_fails(self):
        g = self.g
        v = g.outlet_violations(walk=g.outlet()["crown_lot"])
        self.assertTrue(any("no cover under the S ELM sidewalk" in x for x in v), v)

    def test_a_gutter_over_a_cleanout_fails(self):
        g = self.g
        was = list(g.CLEANOUTS)
        try:
            g.CLEANOUTS[:] = was+[(g.GX, 40.0)]
            self.fails("over the cleanout")
        finally:
            g.CLEANOUTS[:] = was


class AccessTests(unittest.TestCase):
    """Every landing steps down to a walk, and no walk goes under a stair: C-101 note 5a."""

    def setUp(self):
        from src import grading as g
        self.g = g

    def test_the_real_paving_passes(self):
        self.assertEqual(self.g.access_violations(), [])

    def test_unit_4_steps_onto_the_walk_beside_the_stair(self):
        g = self.g
        self.assertAlmostEqual(g.U4_LANDING.y0, g.U5_STOOP.y0)
        self.assertAlmostEqual(g.U45_WALK.y1, g.U4_LANDING.y0)
        self.assertGreaterEqual(grade._touch(g.U4_LANDING, g.U45_WALK), g.ACCESS_MIN)
        self.assertAlmostEqual(g.U45_WALK.x0, g.U3_WALK.x1)

    def test_g1_clears_the_walk_and_the_cleanout(self):
        g = self.g
        x0, y0, x1, y1 = g.G1.box()
        self.assertLess(y1, g.U45_WALK.y0)
        self.assertGreater(y0-g.CO_R, max(cy for cx, cy in g.CLEANOUTS if x0 <= cx <= x1 and cy < y0))

    def test_the_walk_under_the_unit_5_flight_fails(self):
        g = self.g
        old = g.U45_WALK._replace(y0=g.B2Y0-3.0, y1=g.B2Y0, x1=g.U4_LANDING.x0)
        v = g.access_violations([old if r is g.U45_WALK else r for r in g.PAVED])
        self.assertTrue(any("runs under the UNIT 5 FLIGHT" in x for x in v), v)

    def test_a_landing_with_no_walk_fails(self):
        g = self.g
        v = g.access_violations([r for r in g.PAVED if r is not g.U45_WALK])
        self.assertIn("UNIT 4 LANDING: steps down onto no walk", v)

    def test_a_stray_walk_fails(self):
        g = self.g
        v = g.access_violations(g.PAVED+[g.Rect("STRAY WALK", "walk", 20.0, 40.0, 23.0, 45.0)])
        self.assertIn("STRAY WALK: joins no other paving", v)


if __name__ == "__main__":
    unittest.main(verbosity=2)
