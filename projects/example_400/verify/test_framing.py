"""400 Oak's floor framing: check_framing() passes, both floors are 14" open-web floor trusses, and the
   checks fire when a bay outgrows its joist, stops short of a bearing line, or a header
   leaves its table row."""
import importlib
import unittest

from lib.units import IN
from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    fresh()
    leave()


def fresh():
    from src import framing
    return importlib.reload(framing)


class FramingTests(unittest.TestCase):

    def tearDown(self):
        fresh()

    def test_the_framing_passes(self):
        fresh().check_framing()

    def test_both_floors_are_14_inch_joists(self):
        from src import levels
        self.assertEqual((levels.F1_JOIST, levels.F2_JOIST), (IN(14.0), IN(14.0)))
        f = fresh()
        self.assertEqual({b.joist for fl in f.FLOORS for b in fl.bays}, {IN(14.0)})

    def test_the_trusses_stand_at_24_inches_and_every_bay_fits_that_spacing(self):
        """The designer, 2026-09-19. MAX_SPAN is Alpine's 4x2 floor truss table at 40 psf live / 55 total,
           L/480, 24" o.c.: 14" deep spans 19'-9", and Building 2's rear bay is 19'-7-1/8".
           The spacing is also why F2's ceiling board is 5/8"."""
        from src import levels
        f = fresh()
        self.assertEqual(f.JOIST_OC, IN(24))
        self.assertLessEqual(f.JOIST_OC, f.F1_MAX_JOIST_OC)
        self.assertAlmostEqual(f.MAX_SPAN[IN(14.0)], 19.75)
        for fl in f.FLOORS:
            for b in fl.bays:
                self.assertLessEqual(f.bay_span(b), f.MAX_SPAN[b.joist])
        self.assertEqual(levels.F2_GYPSUM, IN(.625))

    def test_a_bay_past_its_depths_span_fails(self):
        f = fresh()
        rear = max(f.B2_FLOOR.bays, key=f.bay_span)
        self.assertLess(f.bay_span(rear), f.MAX_SPAN[IN(14.0)])
        f.MAX_SPAN[IN(14.0)] = 18.0
        self.assertTrue(any('span past' in v for v in f.floor_violations(f.B2_FLOOR, max_span=f.MAX_SPAN, _bearing_lines=f._bearing_lines)))

    def test_f1_is_ul_l528_and_what_leaves_it(self):
        """Read from UL Product iQ's text of L528: trusses 24" o.c. and 12" deep at the limits,
           channels at 16", one 5/8" Type C layer, nothing in the cavity, and no fan or recessed
           luminaire in the membrane."""
        from src import levels
        f = fresh()
        self.assertEqual(levels.F1_LISTING, 'UL DESIGN L528')
        self.assertEqual(f.f1_listing_violations(), [])
        self.assertEqual((f.F1_MAX_JOIST_OC, f.F1_MIN_TRUSS_DEPTH, f.F1_MAX_CHANNEL_OC), (IN(24), IN(12), IN(16)))
        for kw, word in ((dict(joist_oc=IN(25)), 'o.c. exceed'), (dict(depth=IN(11.875)), 'deep are under'),
                         (dict(chord_w=IN(2.5)), 'nominal 2x4'), (dict(layers=2), 'one 5/8'),
                         (dict(board='TYPE X'), 'Type X is not an alternate'), (dict(channel_oc=IN(24)), 'channels at'),
                         (dict(insulation='R-11 BATTS'), 'has none'),
                         (dict(ceiling_devices=['rec']), 'recessed luminaire'), (dict(ceiling_devices=['fanc']), 'soffit')):
            bad = f.f1_listing_violations(**kw)
            self.assertTrue(any(word in v for v in bad), (kw, bad))

    def test_unit_2s_fan_and_bath_light_hang_in_the_soffit(self):
        from src import electrical as e, building2 as b2
        from codes.nec import dwelling as nec_dwelling
        in_soffit = [d.kind for d in e.LEVEL_U2.devices if d.mount == 'c' and nec_dwelling._room_at((d.x, d.y), e.LEVEL_U2) in b2.U2_SOFFIT_ROOMS]
        self.assertIn('fanc', in_soffit)
        elsewhere = [d.kind for d in e.LEVEL_U2.devices if d.mount == 'c' and nec_dwelling._room_at((d.x, d.y), e.LEVEL_U2) not in b2.U2_SOFFIT_ROOMS]
        self.assertNotIn('rec', elsewhere); self.assertNotIn('fanc', elsewhere); self.assertNotIn('fan', elsewhere)

    def test_every_header_fits_over_its_opening(self):
        """Found 2026-09-18: three table headers were deeper than the room between their 8'-0"
           window heads and the double top plate, and nothing measured it."""
        f = fresh()
        self.assertEqual(f.header_violations(), [])
        for h in f.HEADERS:
            if h.load_case != 'NON-BEARING':
                self.assertLessEqual(f.header_depth(h.size), h.room+1e-9, h.tag)
        self.assertEqual(sorted(h.tag for h in f.HEADERS if h.size == f.LVL), ['H13', 'H20', 'H4'])
        self.assertEqual({h.tag: h.table_size for h in f.HEADERS if h.size == f.LVL},
                         {'H4': '2-2x12', 'H13': '3-2x10', 'H20': '3-2x10'})

    def test_the_tables_header_put_back_does_not_fit(self):
        f = fresh()
        h4 = next(h for h in f.HEADERS if h.tag == 'H4')
        bad = f.header_violations([h4._replace(size=h4.table_size)])
        self.assertTrue(any('deep and only 6"' in v for v in bad), bad)

    def test_the_room_is_read_from_the_heads_and_the_plates(self):
        """Level 1: the plate less an 8'-0" head less the double top plate is 6"; Level 2's is 9";
           over a 6'-8" door it is 22". Raise a window's head and its header stops fitting."""
        f = fresh()
        rooms = {round(h.room*12, 3) for h in f.HEADERS}
        self.assertEqual(rooms, {6.0, 9.0, 22.0, 25.0})
        h11 = next(h for h in f.HEADERS if h.tag == 'H11')          # a 2-2x6 in 6" of room
        key = f._key(h11.building, h11.level, h11.openings[0])
        keep = f._HEAD[key]; f._HEAD[key] = keep+1.0/12.0            # the head 1" higher
        try:
            self.assertTrue(any(v.startswith('H11') for v in f.header_violations()))
        finally:
            f._HEAD[key] = keep

    def test_an_lvl_where_the_tables_header_fits_fails(self):
        f = fresh()
        h5 = next(h for h in f.HEADERS if h.tag == 'H5')
        bad = f.header_violations([h5._replace(size=f.LVL)])
        self.assertTrue(any('where the table' in v for v in bad), bad)

    def test_the_lvl_is_checked_against_this_sets_loads(self):
        f = fresh()
        self.assertEqual(f.lvl_violations('ROOF, CEILING AND ONE CLEAR-SPAN FLOOR', 'BUILDING 1', 3.0), [])
        self.assertEqual(f.lvl_violations('ROOF AND CEILING', 'BUILDING 2', 5.0), [])
        self.assertTrue(f.lvl_violations('ROOF, CEILING AND ONE CLEAR-SPAN FLOOR', 'BUILDING 1', 8.0))

    def test_a_bay_off_its_bearing_line_fails(self):
        f = fresh()
        b = f.B2_FLOOR.bays[1]
        fl = f.B2_FLOOR._replace(bays=[f.B2_FLOOR.bays[0], b._replace(y0=b.y0+1.0)])
        bad = f.floor_violations(fl, max_span=f.MAX_SPAN, _bearing_lines=f._bearing_lines)
        self.assertTrue(any('bearing line' in v for v in bad), bad)

    def test_a_well_off_the_stair_wall_fails(self):
        f = fresh()
        w = f.B1_FLOOR.wells[0]
        fl = f.B1_FLOOR._replace(wells=[w._replace(header_x0=w.header_x0+3.0, header_x1=w.header_x1+3.0)])
        bad = f.floor_violations(fl, max_span=f.MAX_SPAN, _bearing_lines=f._bearing_lines)
        self.assertTrue(any('well header' in v for v in bad), bad)

    def test_a_header_off_its_row_fails(self):
        f = fresh()
        i = next(i for i, h in enumerate(f.HEADERS) if h.load_case != 'NON-BEARING')
        f.HEADERS[i] = f.HEADERS[i]._replace(size='2-2x4')
        self.assertTrue(any('table says' in v for v in f.header_violations()))

    def test_the_portal_opening_is_scheduled_at_the_portal_header(self):
        """S-104 note 9's CS-PF header governs over Table 602.7 at the opening the portal
           frame stands beside, so S-102 prints it. Unit 2's entry, Building 2's courtyard
           wall at Level 1: the gravity table asks 2-2x6 and the portal asks 3" x 11-1/4"."""
        from codes.ohio.rco.bracing import PORTAL_HEADER, header_depth, portal_header_size
        f = fresh()
        pf = [h for h in f.HEADERS if f.is_portal(h.building, h.level, h.wall, h.width)]
        self.assertEqual(len(pf), 1, [h.tag for h in pf])
        h = pf[0]
        self.assertEqual((h.building, h.level, h.wall), ('BUILDING 2', 1, 'COURTYARD WALL'))
        self.assertEqual(h.size, portal_header_size())
        self.assertEqual(h.row, '602.10.6.4')
        self.assertEqual(h.table_size, '2-2x6')          # what the gravity table alone would have said
        self.assertGreaterEqual(header_depth(h.size), PORTAL_HEADER[1]-1e-9)
        self.assertGreaterEqual(h.room, header_depth(h.size)-1e-9)   # and it fits over the door

    def test_a_portal_header_under_the_figure_fails(self):
        """The gravity table's own answer, scheduled over the portal, is caught — the
           defect this check was added for."""
        f = fresh()
        i = next(i for i, h in enumerate(f.HEADERS) if f.is_portal(h.building, h.level, h.wall, h.width))
        f.HEADERS[i] = f.HEADERS[i]._replace(size='2-2x6')
        self.assertTrue(any('CS-PF portal' in v for v in f.header_violations()), f.header_violations())

    def test_the_portal_header_is_not_deeper_than_the_figure(self):
        """S-104 note 9 reads "not less than the S-102 header", and detail 4 draws the
           figure's depth, so the schedule may not outgrow it either — the guard that was
           already in src/bracing.py, now with something on the other side of it."""
        from codes.ohio.rco.bracing import PORTAL_HEADER, header_depth
        f = fresh()
        for h in f.HEADERS:
            if f.is_portal(h.building, h.level, h.wall, h.width):
                self.assertLessEqual(header_depth(h.size), PORTAL_HEADER[1]+1e-9, h.tag)

    def test_the_bearing_wall_openings_are_scheduled(self):
        f = fresh()
        brg = [h for h in f.HEADERS if h.wall == f.B2_BEARING_WALL and h.level == 1]
        from src.building2 import D4A, U45_HALL_OPEN
        self.assertEqual(sorted(round(h.width, 4) for h in brg), sorted([round(U45_HALL_OPEN, 4), round(2*D4A, 4)]))
        self.assertTrue(all(h.load_case == 'ONE FLOOR ONLY' for h in brg))


if __name__ == '__main__':
    unittest.main()
