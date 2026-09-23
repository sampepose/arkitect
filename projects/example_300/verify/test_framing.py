"""The floor-framing model: what S-102 draws, checked against the plans it is derived from."""
import os
import sys
import unittest
from arkitect.codes.ohio.rco import floor_checks as floor_checks_shared

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class BayTests(unittest.TestCase):

    def test_building_1_bays_are_the_plan_arrows_and_tile_the_floor(self):
        from src import framing as f
        from arkitect.codes.ohio.rco import floor_checks as rco_floor
        from src.building1 import U23_BEARING_WALL, Y_SEP_BOT, site_x, site_y, W_STUD, D_STUD
        from arkitect.lib.model.regrid import EXT_STUD
        names = [b.name for b in f.B1_FLOOR.bays]
        self.assertEqual(names, ['UNIT 1 F2', 'UNITS 2 / 3 F1, SAGE BAY', 'UNITS 2 / 3 F1, PARCEL BAY'])
        u1 = f.B1_FLOOR.bays[0]
        self.assertAlmostEqual(u1.x0, site_x(0)); self.assertAlmostEqual(u1.x1, site_x(W_STUD))
        self.assertAlmostEqual(u1.y0, site_y(0)); self.assertAlmostEqual(u1.y1, site_y(D_STUD))
        self.assertEqual(u1.run, 'h'); self.assertAlmostEqual(u1.joist, 14/12.0)
        a, b = f.B1_FLOOR.bays[1], f.B1_FLOOR.bays[2]
        self.assertAlmostEqual(a.x1, U23_BEARING_WALL[0]); self.assertAlmostEqual(b.x0, U23_BEARING_WALL[2])
        self.assertAlmostEqual(a.y0, Y_SEP_BOT); self.assertAlmostEqual(a.y1, 48.0-EXT_STUD)
        self.assertAlmostEqual(rco_floor.bay_span(a)+rco_floor.bay_span(b)+(b.x0-a.x1), 26.0-2*EXT_STUD, places=5)

    def test_building_2_bays_meet_on_the_bearing_wall(self):
        from src import framing as f
        from src.building2 import U45_BEARING_WALL
        from arkitect.lib.model.regrid import EXT_STUD
        a, b = f.B2_FLOOR.bays
        self.assertEqual((a.run, b.run), ('v', 'v'))
        self.assertAlmostEqual(a.y1, U45_BEARING_WALL[1]); self.assertAlmostEqual(b.y0, U45_BEARING_WALL[3])
        self.assertAlmostEqual(a.y0, EXT_STUD); self.assertAlmostEqual(b.y1, 28.0-EXT_STUD)
        self.assertAlmostEqual(a.x0, EXT_STUD); self.assertAlmostEqual(a.x1, 26.0-EXT_STUD)

    def test_joist_lines_at_sixteen_inches_inside_the_bay(self):
        from src import framing as f
        b = f.Bay('T', 0.0, 0.0, 10.0, 8.0, 'h', 1.0, ('A', 'B'))
        ls = floor_checks_shared.joist_lines(b, joist_oc=f.JOIST_OC)
        self.assertEqual(len(ls), 5)                                   # 16, 32, 48, 64, 80 inches
        self.assertAlmostEqual(ls[0][1], f.JOIST_OC); self.assertEqual(ls[0][0], 0.0); self.assertEqual(ls[0][2], 10.0)
        v = f.Bay('T', 0.0, 0.0, 8.0, 10.0, 'v', 1.0, ('A', 'B'))
        self.assertEqual(len(floor_checks_shared.joist_lines(v, joist_oc=f.JOIST_OC)), 5)
        self.assertAlmostEqual(floor_checks_shared.joist_lines(v, joist_oc=f.JOIST_OC)[0][0], f.JOIST_OC)

    def test_the_well_sits_in_unit_1s_bay_on_the_stair_wall(self):
        from src import framing as f
        from src.building1 import U1_STAIR_WALL, site_x, site_y, SX, B0, YT
        (w,) = f.B1_FLOOR.wells
        self.assertAlmostEqual(w.x0, site_x(0)); self.assertAlmostEqual(w.x1, site_x(SX))
        self.assertAlmostEqual(w.y0, site_y(B0)); self.assertAlmostEqual(w.y1, site_y(YT))
        self.assertAlmostEqual(w.header_x0, U1_STAIR_WALL[0]); self.assertAlmostEqual(w.header_x1, U1_STAIR_WALL[2])
        self.assertEqual(f.B2_FLOOR.wells, [])
        self.assertEqual(len(f.B2_FLOOR.rated_rims), 2); self.assertEqual(f.B1_FLOOR.rated_rims, [])


class CheckTests(unittest.TestCase):

    def test_the_real_floors_pass(self):
        from src import framing as f
        self.assertEqual(f.framing_violations(), [])

    def test_a_bay_that_ends_in_the_air_fails(self):
        from src import framing as f
        floor = f.Floor('T', 26.0, 48.0, [f.Bay('X', 1.0, 1.0, 20.0, 10.0, 'h', 1.0, ('SAGE WALL', 'NOWHERE'))], [], [])
        v = floor_checks_shared.floor_violations(floor, bearing_lines=[(0.0, 0.0, 0.0, 48.0, 'SAGE WALL')], max_span=f.MAX_SPAN, _bearing_lines=f._bearing_lines)
        self.assertTrue(any('does not end on a bearing line' in x for x in v), v)
        self.assertTrue(any('does not tile' in x for x in v), v)

    def test_a_well_outside_its_bay_fails(self):
        from src import framing as f
        bay = f.Bay('X', 0.0, 0.0, 26.0, 20.0, 'h', 1.0, ('A', 'B'))
        floor = f.Floor('T', 26.0, 20.0, [bay], [f.Well(0.0, 15.0, 3.0, 25.0, 3.0, 3.3)], [])
        v = floor_checks_shared.floor_violations(floor, bearing_lines=[(0.0, 0.0, 0.0, 20.0, 'A'), (26.0, 0.0, 26.0, 20.0, 'B')], max_span=f.MAX_SPAN, _bearing_lines=f._bearing_lines)
        self.assertTrue(any('well' in x and 'outside' in x for x in v), v)

    def test_a_span_past_the_depth_fails(self):
        from src import framing as f
        bay = f.Bay('X', 0.0, 0.0, 20.0, 10.0, 'h', 11.875/12.0, ('A', 'B'))
        floor = f.Floor('T', 20.0, 10.0, [bay], [], [])
        v = floor_checks_shared.floor_violations(floor, bearing_lines=[(0.0, 0.0, 0.0, 10.0, 'A'), (20.0, 0.0, 20.0, 10.0, 'B')], max_span=f.MAX_SPAN, _bearing_lines=f._bearing_lines)
        self.assertTrue(any('span' in x for x in v), v)

    def test_a_floor_with_no_outline_sf_compares_against_its_own_generic_rectangle(self):
        from src import framing as f
        from arkitect.lib.model.regrid import EXT_STUD
        bay = f.Bay('X', EXT_STUD, EXT_STUD, 20.0-EXT_STUD, 10.0-EXT_STUD, 'h', 14/12.0, ('A', 'B'))
        floor = f.Floor('T', 20.0, 10.0, [bay], [], [])
        lines = [(EXT_STUD, 0.0, EXT_STUD, 10.0, 'A'), (20.0-EXT_STUD, 0.0, 20.0-EXT_STUD, 10.0, 'B')]
        self.assertEqual(floor_checks_shared.floor_violations(floor, bearing_lines=lines, max_span=f.MAX_SPAN, _bearing_lines=f._bearing_lines), [])

    def test_a_floor_short_of_its_own_outline_fails_to_tile(self):
        from src import framing as f
        from arkitect.lib.model.regrid import EXT_STUD
        bay = f.Bay('X', EXT_STUD, EXT_STUD, 18.0-EXT_STUD, 10.0-EXT_STUD, 'h', 14/12.0, ('A', 'C'))
        floor = f.Floor('T', 20.0, 10.0, [bay], [], [])
        lines = [(EXT_STUD, 0.0, EXT_STUD, 10.0, 'A'), (20.0-EXT_STUD, 0.0, 20.0-EXT_STUD, 10.0, 'B'),
                 (18.0-EXT_STUD, 0.0, 18.0-EXT_STUD, 10.0, 'C')]
        v = floor_checks_shared.floor_violations(floor, bearing_lines=lines, max_span=f.MAX_SPAN, _bearing_lines=f._bearing_lines)
        self.assertEqual(len(v), 1, v)
        self.assertIn('does not tile', v[0])


class HeaderTests(unittest.TestCase):

    def test_every_opening_in_a_loaded_wall_is_scheduled(self):
        from src import framing as f
        tags = [h.tag for h in f.HEADERS]
        self.assertEqual(tags, ['H%d' % (i+1) for i in range(len(tags))])
        # one row per CONDITION: no two rows share (building, level, wall, load case, width)
        self.assertEqual(len(tags), len({(h.building, h.level, h.wall, h.load_case, round(h.width, 2)) for h in f.HEADERS}))
        self.assertLessEqual(len(tags), 30)
        # and every opening is covered by a row
        self.assertEqual(sum(len(h.openings) for h in f.HEADERS), len(f._openings()))
        cases = {(h.building, h.level, h.wall, h.load_case, round(h.width, 2)) for h in f.HEADERS}
        self.assertIn(('BUILDING 1', 1, 'UNITS 2 AND 3 BEARING WALL', 'ONE FLOOR ONLY', 2.67), cases)
        self.assertIn(('BUILDING 2', 1, 'UNITS 4 AND 5 BEARING WALL', 'ONE FLOOR ONLY', 5.0), cases)
        self.assertIn(('BUILDING 1', 1, 'SAGE WALL', 'ROOF, CEILING AND ONE CLEAR-SPAN FLOOR', 3.0), cases)     # Unit 1 W-A
        self.assertIn(('BUILDING 1', 1, 'SAGE WALL', 'ROOF, CEILING AND ONE CENTER-BEARING FLOOR', 3.0), cases) # Unit 2's door and W-A
        self.assertIn(('BUILDING 1', 2, 'ADJACENT-PARCEL WALL', 'ROOF AND CEILING', 3.0), cases)
        self.assertIn(('BUILDING 1', 1, 'REAR WALL', 'NON-BEARING', 5.0), cases)                                   # W-C
        self.assertIn(('BUILDING 2', 1, 'COURTYARD WALL', 'ROOF, CEILING AND ONE CENTER-BEARING FLOOR', 3.0), cases)
        self.assertIn(('BUILDING 2', 2, 'REAR WALL', 'NON-BEARING', 3.0), cases)
        self.assertIn(('BUILDING 2', 1, 'ADJACENT-PARCEL WALL', 'ROOF AND CEILING', 5.0), cases)
        for h in f.HEADERS:
            if h.load_case == 'NON-BEARING':
                self.assertEqual(h.size, 'PER 602.7.4')
            else:
                self.assertTrue(h.size.startswith(('2-2x', '3-2x')) or h.size == f.LVL, h)       # an LVL where the table's does not fit
        self.assertEqual(f.header_violations(), [])


if __name__ == "__main__":
    unittest.main()


class F1ListingTests(unittest.TestCase):
    """F1 is ICC-ES ESR-1153 Assembly F (Figure 3F), the report's only single-layer
       floor-ceiling that needs no suspended grid. The model carries its build-up and
       check_f1_listing() holds the framing to the listing."""

    def test_build_up_is_one_five_eighths_type_c_on_rc1(self):
        from src import levels
        from arkitect.lib.units import IN
        self.assertEqual(levels.F1_LISTING, 'ICC-ES ESR-1153 ASSEMBLY F')
        self.assertEqual(levels.F1_LAYERS, 1)
        self.assertEqual(levels.F1_BOARD, 'TYPE C')
        self.assertAlmostEqual(levels.F1_LAYER, IN(0.625))
        self.assertAlmostEqual(levels.F1_GYPSUM, IN(0.625))
        self.assertAlmostEqual(levels.F1_CHANNEL, IN(0.5))
        self.assertAlmostEqual(levels.F1_CHANNEL_OC, IN(16))
        self.assertAlmostEqual(levels.F1_INSUL_T, IN(1.5))
        self.assertEqual(levels.F1_INSUL_PCF, 2.5)
        self.assertAlmostEqual(levels.F1_FLANGE_W, IN(3.5))
        # the single layer lifts the Units 2 / 4 ceiling to 8'-10"; nothing else moves
        self.assertAlmostEqual((levels.F1_CEILING-levels.FF1)*12, 106.0)
        self.assertAlmostEqual((levels.FF2-levels.F1_CEILING)*12, 14.0)
        self.assertAlmostEqual(levels.F1_PLATE*12, 115.375)   # the floor at +8-1/4", the designer 2026-09-18
        self.assertAlmostEqual(levels.FLOOR_RISE*12, 120.0)

    def test_the_model_is_inside_the_listing(self):
        from src import framing as f
        self.assertEqual(f.f1_listing_violations(), [])

    def test_each_limit_fails_when_exceeded(self):
        from src import framing as f
        from arkitect.lib.units import IN
        cases = [dict(joist_oc=IN(32)), dict(flange_w=IN(1.75)), dict(layers=2),
                 dict(layer=IN(0.5)), dict(board='TYPE X'), dict(channel_oc=IN(24)),
                 dict(insul_t=IN(1.0)), dict(insul_pcf=1.5)]
        for kw in cases:
            with self.subTest(**{k: str(v) for k, v in kw.items()}):
                self.assertTrue(f.f1_listing_violations(**kw), kw)

    def test_type_x_is_not_an_alternate(self):
        """Assembly B took generic Type X to ASTM C1396; Assembly F names Type C only.
           A substitution that would have passed the old checker must fail this one."""
        from src import framing as f
        v = f.f1_listing_violations(board='TYPE X')
        self.assertEqual(len(v), 1)
        self.assertIn('not an alternate', v[0])

    def test_channels_keep_no_24_inch_allowance(self):
        """Assembly B allowed 24" channels where the joists were at 16"; Assembly F
           states 16" flat. Joists at 16" do not buy the wider spacing any more."""
        from src import framing as f
        from arkitect.lib.units import IN
        self.assertTrue(f.f1_listing_violations(channel_oc=IN(24), joist_oc=IN(16)))



class HeaderFitTests(unittest.TestCase):
    """Found on 400 Oak and here on 2026-09-18: four table headers were deeper than the room
       between their 8'-0" window heads and the double top plate, and nothing measured it."""

    def test_every_header_fits_over_its_opening(self):
        from src import framing as f
        self.assertEqual(f.header_violations(), [])
        for h in f.HEADERS:
            if h.load_case != 'NON-BEARING':
                self.assertLessEqual(f.header_depth(h.size), h.room+1e-9, h.tag)
        self.assertEqual({h.tag: h.table_size for h in f.HEADERS if h.size == f.LVL},
                         {'H1': '2-2x12', 'H3': '2-2x12', 'H15': '3-2x10', 'H21': '3-2x10'})

    def test_the_room_differs_by_the_plate_a_wall_stops_under(self):
        """6" under Unit 1's F2, 8-1/8" under F1, 9" on Level 2."""
        from src import framing as f
        rooms = {(h.unit if h.level == 1 else 'L2', round(h.room*12, 3)) for h in f.HEADERS if h.load_case != 'NON-BEARING'}
        self.assertIn(('UNIT 1', 6.0), rooms); self.assertIn(('ANY', 8.125), rooms); self.assertIn(('L2', 9.0), rooms)

    def test_the_tables_header_put_back_does_not_fit(self):
        from src import framing as f
        h1 = next(h for h in f.HEADERS if h.tag == 'H1')
        bad = f.header_violations([h1._replace(size=h1.table_size)])
        self.assertTrue(any('deep and only 6"' in v for v in bad), bad)

    def test_an_lvl_where_the_tables_header_fits_fails(self):
        from src import framing as f
        h4 = next(h for h in f.HEADERS if h.tag == 'H4')
        self.assertTrue(any('where the table' in v for v in f.header_violations([h4._replace(size=f.LVL)])))

    def test_the_lvl_carries_this_sets_loads(self):
        from src import framing as f
        self.assertEqual(f.lvl_violations('ROOF, CEILING AND ONE CLEAR-SPAN FLOOR', 'BUILDING 1', 3.0), [])
        self.assertEqual(f.lvl_violations('ROOF AND CEILING', 'BUILDING 2', 5.0), [])
        self.assertTrue(f.lvl_violations('ROOF, CEILING AND ONE CLEAR-SPAN FLOOR', 'BUILDING 1', 8.0))


if __name__ == "__main__":
    unittest.main()
