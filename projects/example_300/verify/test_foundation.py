"""The foundation model: what S-101 draws, checked against the plans it is derived from."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


from codes.ohio.rco import concrete as rco_concrete

class U1StairWallTests(unittest.TestCase):

    def test_stair_wall_is_the_one_a101_draws(self):
        """The strip under Unit 1's stair wall must sit under the wall plans.py draws:
           x from SX to SX+P, y from LB to YT, through site_x/site_y."""
        from src import building1 as b
        x0, y0, x1, y1 = b.U1_STAIR_WALL
        self.assertAlmostEqual(x0, b.site_x(b.SX), places=9)
        self.assertAlmostEqual(x1, b.site_x(b.SX + b.P), places=9)
        self.assertAlmostEqual(y0, b.site_y(b.LB), places=9)
        self.assertAlmostEqual(y1, b.site_y(b.YT), places=9)
        self.assertAlmostEqual(x1 - x0, 3.5 / 12.0, places=9)   # a 2x4
        self.assertLess(y0, y1)


class DesignBasisTests(unittest.TestCase):

    def test_footing_bears_below_the_columbus_frost_line(self):
        """A 16 x 8 continuous footing with its bottom 32 inches below finished grade —
           CIC-09's frost line, the depth RCO 403.1.4.1 asks for — and an 8 inch wall."""
        from src import foundation as f
        self.assertAlmostEqual(f.FROST_DEPTH, 32.0 / 12.0)
        self.assertAlmostEqual(f.FTG_W, 16.0 / 12.0); self.assertAlmostEqual(f.FTG_T, 8.0 / 12.0)
        self.assertAlmostEqual(f.WALL_T, 8.0 / 12.0)
        self.assertAlmostEqual(f.FTG_PROJ, 4.0 / 12.0)
        self.assertGreaterEqual(f.FTG_W, 12.0 / 12.0)         # Table R403.1(1), two storeys, 1,500 psf

    def test_no_frost_protected_shallow_foundation_remains(self):
        """The FPSF was taken out on purpose; none of its names may come back quietly."""
        from src import foundation as f
        for name in ("frost_row", "403_3_1", "FROST", "FOOTING_DEPTH", "INSUL_R_FROST",
                     "EDGE_INSUL_VERT", "EDGE_INSUL_BELOW", "EDGE_INSUL_HORIZ", "EDGE_W", "AFI"):
            self.assertFalse(hasattr(f, name), name)

    def test_slab_edge_insulation_is_the_energy_codes(self):
        """R-10 for 2 feet, Table 1102.1.2, from a 2 inch XPS at its nominal value; it
           sits on the wall's interior face and must not run below the footing's top."""
        from src import foundation as f
        from src import levels
        self.assertAlmostEqual(f.INSUL_T, 2.0 / 12.0)
        self.assertAlmostEqual(f.INSUL_R_NOM, 10.0)
        self.assertGreaterEqual(f.INSUL_R_NOM, f.ENERGY_R)
        self.assertAlmostEqual(f.EDGE_INSUL_RUN, 2.0)
        self.assertLessEqual(f.EDGE_INSUL_RUN, f.FROST_DEPTH + levels.SLAB_TOP - f.FTG_T)
        f.check_basis()


class GeometryTests(unittest.TestCase):

    def _inside(self, r, W, D):
        x0, y0, x1, y1 = r[:4]
        return x0 >= -1e-9 and y0 >= -1e-9 and x1 <= W + 1e-9 and y1 <= D + 1e-9

    def _touches(self, r, W, D):
        """One edge of the pad lies on a perimeter line. (The Unit 3 stoop shares the
           Sage face and also passes the rear wall; that still counts.)"""
        x0, y0, x1, y1 = r[:4]
        return (abs(x1) < 1e-9 or abs(x0 - W) < 1e-9 or abs(y1) < 1e-9 or abs(y0 - D) < 1e-9)

    def test_strips_lie_inside_and_pads_lie_against(self):
        from src import foundation as f
        for b in f.BUILDINGS:
            for s in b.strips:
                self.assertTrue(self._inside(s, b.W, b.D), (b.name, s))
            for p in b.pads:
                self.assertFalse(self._inside(p, b.W, b.D), (b.name, p))
                self.assertTrue(self._touches(p, b.W, b.D), (b.name, p))

    def test_building_1_strips_are_w4_and_the_stair_wall(self):
        from src import foundation as f
        from src.building1 import Y_SEP_TOP, Y_SEP_BOT, U1_STAIR_WALL
        names = [s[4] for s in f.B1.strips]
        self.assertEqual(names, ["W4", "UNIT 1 STAIR WALL", "UNITS 2 AND 3 BEARING WALL"])
        w4 = f.B1.strips[0]
        self.assertAlmostEqual((w4[1] + w4[3]) / 2.0, (Y_SEP_TOP + Y_SEP_BOT) / 2.0)
        self.assertAlmostEqual(w4[3] - w4[1], f.STRIP_W)
        self.assertAlmostEqual(w4[0], 0.0); self.assertAlmostEqual(w4[2], f.B1.W)
        st = f.B1.strips[1]
        wx0, wy0, wx1, wy1 = U1_STAIR_WALL
        self.assertAlmostEqual((st[0] + st[2]) / 2.0, (wx0 + wx1) / 2.0)
        self.assertAlmostEqual(st[2] - st[0], f.STRIP_W)
        self.assertAlmostEqual(st[1], wy0); self.assertAlmostEqual(st[3], wy1)

    def test_units_2_3_strip_is_the_wall_the_joist_bays_meet_on(self):
        """The floor of Units 2/3 is two F1 joist bays (drawn on S-102); the wall
           between them bears, and the strip sits under it for the grouping's full depth."""
        from src import foundation as f
        from src import building1 as b
        from lib.model.regrid import EXT_STUD
        bays = sorted((j[0], j[2]) for j in b._B1_JOISTS)
        self.assertEqual(len(bays), 2)
        wx0, wy0, wx1, wy1 = b.U23_BEARING_WALL
        # final sheet x runs opposite to the reflected model x
        self.assertAlmostEqual(wx0, b.B1_W - b.PLAN_L1.x(bays[1][0], 30.0))
        self.assertAlmostEqual(wx1, b.B1_W - b.PLAN_L1.x(bays[0][1], 30.0))
        self.assertAlmostEqual(wx1 - wx0, 3.5 / 12.0, places=5)     # regridded: snapped to 1e-6
        self.assertAlmostEqual(wy0, b.Y_SEP_BOT); self.assertAlmostEqual(wy1, 48.0 - EXT_STUD)
        st = f.B1.strips[2]
        self.assertAlmostEqual((st[0] + st[2]) / 2.0, (wx0 + wx1) / 2.0)
        self.assertAlmostEqual(st[1], wy0); self.assertAlmostEqual(st[3], wy1)

    def test_building_2_strip_is_the_wall_its_joist_bays_meet_on(self):
        """Building 2's floor is two F1 bays spanning courtyard to rear on the bearing
           wall between the living space and the bedrooms; the strip runs the full
           width under it, like W4's."""
        from src import foundation as f
        from src import building2 as b
        bays = sorted((j[0], j[2]) for j in b._B2_JOISTS)
        self.assertEqual(len(bays), 2)
        self.assertTrue(all(j[4] == 'v' for j in b._B2_JOISTS))
        wx0, wy0, wx1, wy1 = b.U45_BEARING_WALL
        self.assertAlmostEqual(wy0, b.PLAN_B2.y(bays[0][1]))
        self.assertAlmostEqual(wy1, b.PLAN_B2.y(bays[1][0]))
        self.assertAlmostEqual(wy1 - wy0, 3.5 / 12.0, places=5)
        self.assertAlmostEqual(wx0, 0.0); self.assertAlmostEqual(wx1, b.B2_W)
        self.assertEqual([s[4] for s in f.B2.strips], ["UNITS 4 AND 5 BEARING WALL"])
        st = f.B2.strips[0]
        self.assertAlmostEqual((st[1] + st[3]) / 2.0, (wy0 + wy1) / 2.0)
        self.assertAlmostEqual(st[0], wx0); self.assertAlmostEqual(st[2], wx1)
        self.assertEqual([p[4] for p in f.B2.pads], ["UNIT 4 LANDING", "UNIT 5 STOOP"])

    def test_pads_are_where_c101_draws_them(self):
        """The same rectangles C-101 draws, shifted from site to sheet coordinates."""
        from src import foundation as f
        from src.building1 import ENTRY_LEFT, PLAN_L1, U2_ENTRY, U3_FLIGHT_HI, U3_STOOP_HI, U3_STAIR_W
        from src.building2 import U5_DOOR_X0, U5_STOOP_X0, U5_FLIGHT_X0, U5_LAND_D
        pads = {p[4]: p[:4] for b in f.BUILDINGS for p in b.pads}
        u2y = PLAN_L1.y(U2_ENTRY[1]) + U2_ENTRY[2] / 2.0 - 1.5
        self.assertEqual(pads["UNIT 1 LANDING"], (ENTRY_LEFT, -3.0, ENTRY_LEFT + 3.0, 0.0))
        self.assertEqual(pads["UNIT 2 LANDING"], (-3.0, u2y, 0.0, u2y + 3.0))
        self.assertEqual(pads["UNIT 3 STOOP"], (-U3_STAIR_W, U3_FLIGHT_HI, 0.0, U3_STOOP_HI))
        self.assertEqual(pads["UNIT 4 LANDING"], (U5_DOOR_X0, -U5_LAND_D, U5_DOOR_X0 + 3.0, 0.0))
        self.assertEqual(pads["UNIT 5 STOOP"], (U5_STOOP_X0, -U5_LAND_D, U5_FLIGHT_X0, 0.0))

    def test_unit4_landing_is_under_the_unit5_top_landing(self):
        """A-103 and S-101: Unit 4's door and pad stand against the courtyard face under the
        7'-0" top landing, never out beside the stair where C-101 once drew them, and the
        pad reaches the top landing's edge so its step lands on the walk beside the stair."""
        from src import foundation as f
        from src.building2 import U5_LAND_D, U5_LAND_LEN, U5_LAND_X0, U5_LAND_X1, U5_RUN
        x0, y0, x1, y1 = {p[4]: p[:4] for p in f.B2.pads}["UNIT 4 LANDING"]
        self.assertAlmostEqual(U5_LAND_LEN, 7.0)
        self.assertAlmostEqual(U5_RUN, 10.0 + 9.5 / 12.0)
        self.assertEqual((x0, x1), (21.0, 24.0))
        self.assertTrue(U5_LAND_X0 <= x0 and x1 <= U5_LAND_X1)
        self.assertTrue(abs(y0 + U5_LAND_D) < 1e-9 and y1 == 0.0)

    def test_check_foundation_passes_and_prints(self):
        import io, contextlib
        from src import foundation as f
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            f.check_foundation()
        self.assertIn("FOUNDATION", out.getvalue())
        self.assertIn("CONCRETE — TABLE 402.2, SEVERE WEATHERING", out.getvalue())


class ConcreteTests(unittest.TestCase):
    """RCO Table 402.2 at the severe weathering potential of Table 301.2(1)."""

    def test_the_set_specifies_what_sam_asked(self):
        """Severe weathering; the slab 3,000 as S-101 gave it; the footings and walls
           3,000 air-entrained; stoops, landings, walks and pad 3,500 air-entrained."""
        from src import foundation as f
        self.assertEqual(f.WEATHERING, "SEVERE")
        self.assertEqual((f.FOOTINGS.psi, f.FOOTINGS.air), (3000, "AE"))
        self.assertEqual((f.WALLS.psi, f.WALLS.air, f.WALLS.row), (3000, "AE", rco_concrete.VERTICAL_EXPOSED))
        self.assertEqual((f.SLAB.psi, f.SLAB.air), (3000, "c"))
        self.assertEqual((f.FLATWORK.psi, f.FLATWORK.air, f.FLATWORK.row), (3500, "AE", rco_concrete.PORCH_STEPS))
        for word in ("STOOPS", "LANDINGS", "WALKS", "PARKING PAD"):
            self.assertIn(word, f.FLATWORK.element)
        self.assertEqual(f.concrete_violations(), [])

    def test_a_weaker_or_plain_mix_fails(self):
        from src import foundation as f
        self.assertTrue(f.concrete_violations((f.FLATWORK._replace(psi=3000),)))
        self.assertTrue(f.concrete_violations((f.WALLS._replace(air="c"),)))
        self.assertTrue(f.concrete_violations((f.SLAB._replace(air=""),)))
        self.assertTrue(f.concrete_violations((f.WALLS._replace(row=rco_concrete.NOT_EXPOSED),)))
        self.assertEqual(f.concrete_violations((f.SLAB._replace(psi=2500),)), [])

    def test_every_paved_kind_and_gutter_has_a_strength(self):
        """src/grading.py's paving and gutters all fall under FLATWORK's row: a new kind
           of site concrete fails the build rather than being poured to nothing."""
        from src import foundation as f
        from src import grading as g
        self.assertEqual(g.concrete_violations(), [])
        for r in g.PAVED:
            self.assertIn(r.kind, f.FLATWORK_KINDS, r.name)
        self.assertIn("gutter", f.FLATWORK_KINDS)
        bad = g.Rect("A NEW APRON", "apron", 0.0, 0.0, 1.0, 1.0)
        self.assertTrue(g.concrete_violations(paved=[bad]))

    def test_g001_weathering_is_the_models(self):
        import inspect
        from src.sheets import g001
        self.assertIn('("Weathering",WEATHERING)', inspect.getsource(g001))


if __name__ == "__main__":
    unittest.main()
