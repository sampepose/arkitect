"""NEC 2023 walked over a dwelling built for the test: each rule arkitect/codes/nec/dwelling.py enforces,
shown to pass on a compliant room and to fail, by name, when the room is broken.

These lived in one project's tests and used nothing of that project. They cover every project
that hands its rooms to check_unit()."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from arkitect.codes.nec import dwelling as nec_dwelling


def _room(devices, doors=(), polys=None, rooms=(), ext_req=(), counters=(), dividers=(),
          kitchens=(), lavs=(), wds=(), sinks=(), sep_y=None, circuits=None, name='T'):
    """A synthetic unit type: one level, one 12 x 10 living room unless told otherwise."""
    polys = polys if polys is not None else [([(0, 0), (12, 0), (12, 10), (0, 10)], 'LIVING')]
    circuits = circuits or [nec_dwelling.ckt(1, 'LIGHTING', 15, 1, '#14', 'AFCI', 'ltg'),
                            nec_dwelling.ckt(2, 'RECEPTACLES', 20, 1, '#12', 'AFCI', 'rcpt')]
    lv = nec_dwelling.Level(name, list(devices), rooms=list(rooms), polys=polys, doors=list(doors),
                 ext_req=list(ext_req), counters=list(counters), dividers=list(dividers),
                 kitchens=list(kitchens), lavs=list(lavs), wds=list(wds), sinks=list(sinks), sep_y=sep_y)
    return nec_dwelling.UnitType(name, 100, [lv], circuits)


def _has(violations, *needles):
    return any(all(n in v for n in needles) for v in violations)


class CheckerTests(unittest.TestCase):
    """Each rule on a synthetic room, so a rule that goes quiet is caught."""

    # a 12 x 10 room with a 3' door on the north wall at x 4..7: the wall line runs
    # from the door's east jamb round the room to its west jamb, one run of 41'
    DOOR = [(4, 0, 3, 'h')]

    def LIGHT(self):
        """A switched luminaire and a smoke alarm: what every room needs besides receptacles."""
        from arkitect.codes.nec.dwelling import dev
        return [dev(6, 5, 'lt', 'c', 1, 'A'), dev(7.3, 0, 'sw', 'n', 1, 'A'), dev(6, 5, 'sd', 'c', 1)]

    def test_210_52A_walks_the_wall_line_between_openings(self):
        ok = [nec_dwelling.dev(9.5, 0, 'dup', 'n', 2), nec_dwelling.dev(12, 5, 'dup', 'e', 2), nec_dwelling.dev(9, 10, 'dup', 's', 2),
              nec_dwelling.dev(3, 10, 'dup', 's', 2), nec_dwelling.dev(0, 5, 'dup', 'w', 2), nec_dwelling.dev(2, 0, 'dup', 'n', 2)]
        v = nec_dwelling.check_unit(_room(ok+self.LIGHT(), doors=self.DOOR))
        self.assertFalse(_has(v, '210.52(A)'), v)
        # drop the north-wall receptacle at x 9: the run from the jamb at 7 to (12, 5) is 10'
        bad = [d for d in ok if not (d.x == 9 and d.y == 10)]
        v = nec_dwelling.check_unit(_room(bad+self.LIGHT(), doors=self.DOOR))
        self.assertTrue(_has(v, '210.52(A)', 'LIVING'), v)

    def test_210_52A_a_short_wall_needs_none_and_a_counter_is_not_walked(self):
        # the 1.5' return beside the door is under 2'; the counter on the south wall is
        # covered by (C), so the walk skips it
        devs = [nec_dwelling.dev(9.5, 0, 'dup', 'n', 2), nec_dwelling.dev(12, 5, 'dup', 'e', 2), nec_dwelling.dev(0, 5, 'dup', 'w', 2),
                nec_dwelling.dev(1.5, 0, 'dup', 'n', 2), nec_dwelling.dev(11, 10, 'dup', 's', 2)]   # the 2' past the counter
        devs += [nec_dwelling.dev(x, 10, 'gfci', 's', 2) for x in (1.5, 5.0, 8.5)]
        v = nec_dwelling.check_unit(_room(devs[:-4]+devs[-3:]+self.LIGHT(), doors=[(2.0, 0, 3, 'h')], counters=[(0, 8, 10, 2)]))
        self.assertTrue(_has(v, '210.52(A)', "7'-0\""), v)                # without it: 7' to the run end
        v = nec_dwelling.check_unit(_room(devs+self.LIGHT(), doors=[(2.0, 0, 3, 'h')], counters=[(0, 8, 10, 2)]))
        self.assertFalse(_has(v, '210.52(A)'), v)

    def test_210_52A_a_doubled_back_closet_edge_is_not_wall_and_a_far_face_door_still_cuts(self):
        # a 12 x 10 room whose closet notch (x 10..12, y 0..6) is drawn as a spike along
        # y = 0, the way Building 1's Bedroom 1 is; the door is authored on the far face
        # of a 0.4' wall, at y = -0.4
        poly = [([(12, 0), (0, 0), (0, 10), (12, 10), (12, 6), (10, 6), (10, 0)], 'BEDROOM 1')]
        devs = [nec_dwelling.dev(1.5, 0, 'dup', 'n', 2), nec_dwelling.dev(8.5, 0, 'dup', 'n', 2), nec_dwelling.dev(0, 5, 'dup', 'w', 2),
                nec_dwelling.dev(6, 10, 'dup', 's', 2), nec_dwelling.dev(12, 8, 'dup', 'e', 2), nec_dwelling.dev(6, 5, 'lt', 'c', 1, 'A'),
                nec_dwelling.dev(12, 9.5, 'sw', 'e', 1, 'A'), nec_dwelling.dev(6, 5, 'sd', 'c', 1), nec_dwelling.dev(20, 5, 'sd', 'c', 1), nec_dwelling.dev(20, 5, 'co', 'c', 1)]
        v = nec_dwelling.check_unit(_room(devs, polys=poly, doors=[(4, -0.4, 3, 'h'), (10, 0, 6, 'v')]))
        self.assertFalse(_has(v, '210.52(A)'), v)
        # without the far-face door the north wall is one 12' run with its receptacles 7' apart — fine —
        # but the spike has no receptacle and would fail as a 2' run if it were walked
        v = nec_dwelling.check_unit(_room(devs, polys=poly, doors=[(10, 0, 6, 'v')]))
        self.assertFalse(_has(v, '210.52(A)'), v)

    def test_210_8_the_kitchen_zone_of_an_open_plan(self):
        liv = [([(0, 0), (24, 0), (24, 10), (0, 10)], 'KITCHEN / LIVING / DINING')]
        cks = [nec_dwelling.ckt(1, 'LTG', 15, 1, '#14', 'AFCI', 'ltg'), nec_dwelling.ckt(2, 'RCPT', 20, 1, '#12', 'AFCI', 'rcpt'),
               nec_dwelling.ckt(3, 'SA', 20, 1, '#12', 'AFCI/GFCI', 'sa')]
        devs = self.LIGHT() + [nec_dwelling.dev(x, 0, 'dup', 'n', 2) for x in (2, 9.5, 14)] + [nec_dwelling.dev(x, 10, 'dup', 's', 2) for x in (4, 10, 16, 22)] + \
               [nec_dwelling.dev(0, 5, 'dup', 'w', 2), nec_dwelling.dev(24, 5, 'dup', 'e', 2), nec_dwelling.dev(22, 0, 'gfci', 'n', 3)]
        v = nec_dwelling.check_unit(_room(devs, polys=liv, doors=self.DOOR, circuits=cks, kitchens=[(16, 0, 8, 10)]))
        self.assertTrue(_has(v, '210.8', "22'-0\", 10'-0\""), v)            # the dup at (22, 10) is in the kitchen
        self.assertFalse(_has(v, '210.8', "16'-0\", 10'-0\""), v)           # at (16, 10) it stands off into the living side
        self.assertFalse(_has(v, '210.11(C)(1)'), v)                        # the SA receptacle at (22, 0) is in the kitchen

    def test_210_52H_a_hall_ten_feet_or_longer_needs_one(self):
        hall = [([(0, 0), (3, 0), (3, 12), (0, 12)], 'HALL')]
        devs = [nec_dwelling.dev(1.5, 6, 'lt', 'c', 1, 'A'), nec_dwelling.dev(0, 1, 'sw', 'w', 1, 'A')]
        v = nec_dwelling.check_unit(_room(devs, polys=hall))
        self.assertTrue(_has(v, '210.52(H)'), v)
        self.assertFalse(_has(v, '210.52(A)'), v)          # not walked
        v = nec_dwelling.check_unit(_room(devs+[nec_dwelling.dev(0, 6, 'dup', 'w', 2)], polys=hall))
        self.assertFalse(_has(v, '210.52(H)'), v)
        short = [([(0, 0), (3, 0), (3, 8), (0, 8)], 'HALL')]
        v = nec_dwelling.check_unit(_room(devs, polys=short))
        self.assertFalse(_has(v, '210.52(H)'), v)

    def test_210_52C_counters_every_24_inches_split_by_the_range_and_the_sink(self):
        base = self.LIGHT() + [nec_dwelling.dev(x, 0, 'dup', 'n', 2) for x in (2, 9.5)] + \
               [nec_dwelling.dev(12, 5, 'dup', 'e', 2), nec_dwelling.dev(0, 5, 'dup', 'w', 2)]
        kit = [([(0, 0), (12, 0), (12, 10), (0, 10)], 'KITCHEN')]
        cks = [nec_dwelling.ckt(1, 'LTG', 15, 1, '#14', 'AFCI', 'ltg'), nec_dwelling.ckt(2, 'RCPT', 20, 1, '#12', 'AFCI/GFCI', 'rcpt'),
               nec_dwelling.ckt(3, 'SA', 20, 1, '#12', 'AFCI/GFCI', 'sa')]
        counter = [(0, 8, 12, 2)]; rng = [(4, 8, 2.5, 2)]     # 0..4 and 6.5..12 are the two spaces
        v = nec_dwelling.check_unit(_room(base, polys=kit, doors=self.DOOR, counters=counter, dividers=rng, circuits=cks))
        self.assertTrue(_has(v, '210.52(C)'), v)
        good = base + [nec_dwelling.dev(2, 10, 'gfci', 's', 3), nec_dwelling.dev(8, 10, 'gfci', 's', 3), nec_dwelling.dev(11, 10, 'gfci', 's', 3)]
        v = nec_dwelling.check_unit(_room(good, polys=kit, doors=self.DOOR, counters=counter, dividers=rng, circuits=cks))
        self.assertFalse(_has(v, '210.52(C)'), v)
        # 2' at 8 and 3' at 11 leaves 3' between: fine; take the 8 away and 11 is 4.5' from 6.5
        v = nec_dwelling.check_unit(_room(good[:-2]+good[-1:], polys=kit, doors=self.DOOR, counters=counter, dividers=rng, circuits=cks))
        self.assertTrue(_has(v, '210.52(C)'), v)

    def test_210_52D_E_F_lavatory_exterior_and_laundry(self):
        base = self.LIGHT() + [nec_dwelling.dev(x, 0, 'dup', 'n', 2) for x in (2, 9.5)] + \
               [nec_dwelling.dev(12, 5, 'dup', 'e', 2), nec_dwelling.dev(0, 5, 'dup', 'w', 2), nec_dwelling.dev(6, 10, 'dup', 's', 2)]
        cks = [nec_dwelling.ckt(1, 'LTG', 15, 1, '#14', 'AFCI', 'ltg'), nec_dwelling.ckt(2, 'RCPT', 20, 1, '#12', 'AFCI', 'rcpt'),
               nec_dwelling.ckt(3, 'LAUNDRY', 20, 1, '#12', 'AFCI/GFCI', 'laundry')]
        bath = ([(0, 0), (12, 0), (12, 10), (0, 10)], 'BATH')
        v = nec_dwelling.check_unit(_room(base, polys=[bath], doors=self.DOOR, lavs=[(1, 8, 2, 1.5)], circuits=cks))
        self.assertTrue(_has(v, '210.52(D)'), v)
        v = nec_dwelling.check_unit(_room(base+[nec_dwelling.dev(0, 7, 'gfci', 'w', 2)], polys=[bath], doors=self.DOOR, lavs=[(1, 8, 2, 1.5)], circuits=cks))
        self.assertFalse(_has(v, '210.52(D)'), v)
        v = nec_dwelling.check_unit(_room(base, doors=self.DOOR, ext_req=[(5.5, 0, 'the entry door')], circuits=cks))
        self.assertTrue(_has(v, '210.52(E)', 'entry door'), v)
        v = nec_dwelling.check_unit(_room(base+[nec_dwelling.dev(8, 0, 'wp', 's', 2)], doors=self.DOOR, ext_req=[(5.5, 0, 'the entry door')], circuits=cks))
        self.assertFalse(_has(v, '210.52(E)'), v)
        v = nec_dwelling.check_unit(_room(base, doors=self.DOOR, wds=[(10, 8, 2.3, 2.5)], circuits=cks))
        self.assertTrue(_has(v, '210.52(F)'), v)
        v = nec_dwelling.check_unit(_room(base+[nec_dwelling.dev(12, 8, 'gfci', 'e', 3)], doors=self.DOOR, wds=[(10, 8, 2.3, 2.5)], circuits=cks))
        self.assertFalse(_has(v, '210.52(F)'), v)
        # a laundry receptacle on the general circuit does not count
        v = nec_dwelling.check_unit(_room(base+[nec_dwelling.dev(12, 8, 'gfci', 'e', 2)], doors=self.DOOR, wds=[(10, 8, 2.3, 2.5)], circuits=cks))
        self.assertTrue(_has(v, '210.52(F)'), v)

    def test_210_70_every_room_lit_and_switched_stairs_at_both_levels_doors_lit(self):
        rc = [nec_dwelling.dev(x, 0, 'dup', 'n', 2) for x in (2, 9.5)] + [nec_dwelling.dev(12, 5, 'dup', 'e', 2), nec_dwelling.dev(0, 5, 'dup', 'w', 2), nec_dwelling.dev(6, 10, 'dup', 's', 2)]
        v = nec_dwelling.check_unit(_room(rc+[nec_dwelling.dev(6, 5, 'sd', 'c', 1)], doors=self.DOOR))
        self.assertTrue(_has(v, '210.70', 'no luminaire'), v)
        v = nec_dwelling.check_unit(_room(rc+[nec_dwelling.dev(6, 5, 'sd', 'c', 1), nec_dwelling.dev(6, 5, 'lt', 'c', 1, 'A')], doors=self.DOOR))
        self.assertTrue(_has(v, '210.70', 'no switch'), v)
        v = nec_dwelling.check_unit(_room(rc+self.LIGHT(), doors=self.DOOR, rooms=[(20, 0, 2, 6, 'CL.')]))
        self.assertFalse(_has(v, '210.70'), v)                      # closets need none
        stair = [([(0, 0), (12, 0), (12, 10), (0, 10)], 'LIVING'), ([(14, 0), (17.5, 0), (17.5, 10), (14, 10)], 'STAIR')]
        st = rc + self.LIGHT() + [nec_dwelling.dev(15.75, 5, 'lt', 'c', 1, 'S'), nec_dwelling.dev(14, 1, 'sw', 'w', 1, 'S')]
        v = nec_dwelling.check_unit(_room(st, polys=stair, doors=self.DOOR))
        self.assertTrue(_has(v, '210.70(A)(2)', 'stair'), v)
        st[-1] = nec_dwelling.dev(14, 1, 'sw3', 'w', 1, 'S'); st.append(nec_dwelling.dev(14, 9, 'sw3', 'w', 1, 'S'))
        v = nec_dwelling.check_unit(_room(st, polys=stair, doors=self.DOOR))
        self.assertFalse(_has(v, '210.70(A)(2)'), v)
        v = nec_dwelling.check_unit(_room(rc+self.LIGHT(), doors=self.DOOR, ext_req=[(5.5, 0, 'the entry door')]))
        self.assertTrue(_has(v, '210.70(A)(2)(b)'), v)
        lit = rc + self.LIGHT() + [nec_dwelling.dev(8, 0, 'ext', 's', 1, 'X'), nec_dwelling.dev(7.6, 0, 'sw', 'n', 1, 'X'), nec_dwelling.dev(8.5, 0, 'wp', 's', 2)]
        v = nec_dwelling.check_unit(_room(lit, doors=self.DOOR, ext_req=[(5.5, 0, 'the entry door')]))
        self.assertFalse(_has(v, '210.70(A)(2)(b)'), v)

    def test_alarms_in_and_outside_every_sleeping_room(self):
        polys = [([(0, 0), (12, 0), (12, 10), (0, 10)], 'BEDROOM 1'), ([(12.3, 0), (24, 0), (24, 10), (12.3, 10)], 'LIVING')]
        devs = [nec_dwelling.dev(18, 5, 'lt', 'c', 1, 'A'), nec_dwelling.dev(12.3, 1, 'sw', 'w', 1, 'A'),
                nec_dwelling.dev(6, 5, 'lt', 'c', 1, 'B'), nec_dwelling.dev(12, 1, 'sw', 'e', 1, 'B')]
        devs += [nec_dwelling.dev(x, 0, 'dup', 'n', 2) for x in (2, 8, 14, 20)] + [nec_dwelling.dev(x, 10, 'dup', 's', 2) for x in (4, 10, 16, 22)]
        devs += [nec_dwelling.dev(0, 5, 'dup', 'w', 2), nec_dwelling.dev(24, 5, 'dup', 'e', 2), nec_dwelling.dev(12, 3, 'dup', 'e', 2), nec_dwelling.dev(12.3, 3, 'dup', 'w', 2)]
        doors = [(12.15, 5, 2.67, 'v')]
        v = nec_dwelling.check_unit(_room(devs, polys=polys, doors=doors))
        self.assertTrue(_has(v, '314', 'BEDROOM 1'), v)
        self.assertTrue(_has(v, '314', 'outside'), v)
        self.assertTrue(_has(v, '315'), v)
        devs += [nec_dwelling.dev(6, 7, 'sd', 'c', 1), nec_dwelling.dev(14, 5, 'sd', 'c', 1), nec_dwelling.dev(15, 5, 'co', 'c', 1)]
        v = nec_dwelling.check_unit(_room(devs, polys=polys, doors=doors))
        self.assertFalse(_has(v, 'R31'), v)

    def test_fans_w4_gfci_and_circuit_use(self):
        kit = [([(0, 0), (12, 0), (12, 10), (0, 10)], 'KITCHEN')]
        cks = [nec_dwelling.ckt(1, 'LTG', 15, 1, '#14', 'AFCI', 'ltg'), nec_dwelling.ckt(2, 'SA 1', 20, 1, '#12', 'AFCI/GFCI', 'sa'),
               nec_dwelling.ckt(3, 'FRIDGE', 20, 1, '#12', 'AFCI', 'dw'), nec_dwelling.ckt(4, 'RCPT', 20, 1, '#12', 'AFCI', 'rcpt')]
        devs = self.LIGHT() + [nec_dwelling.dev(x, 0, 'gfci', 'n', 2) for x in (2, 9.5)] + \
               [nec_dwelling.dev(12, 5, 'gfci', 'e', 2), nec_dwelling.dev(0, 5, 'gfci', 'w', 2), nec_dwelling.dev(6, 10, 'gfci', 's', 2)]
        v = nec_dwelling.check_unit(_room(devs+[nec_dwelling.dev(3, 10, 'dup', 's', 4)], polys=kit, doors=self.DOOR, circuits=cks))
        self.assertTrue(_has(v, '210.8', 'dup'), v)                      # a plain duplex in a kitchen
        v = nec_dwelling.check_unit(_room(devs+[nec_dwelling.dev(11, 0, 'fridge', 'n', 3)], polys=kit, doors=self.DOOR, circuits=cks))
        self.assertTrue(_has(v, '210.8', 'fridge'), v)                   # on a circuit without GFCI
        cks[2] = nec_dwelling.ckt(3, 'FRIDGE', 20, 1, '#12', 'AFCI/GFCI', 'dw')
        v = nec_dwelling.check_unit(_room(devs+[nec_dwelling.dev(11, 0, 'fridge', 'n', 3)], polys=kit, doors=self.DOOR, circuits=cks))
        self.assertFalse(_has(v, '210.8'), v)
        # a sink in a living room pulls the 6' rule with it
        liv = [([(0, 0), (12, 0), (12, 10), (0, 10)], 'LIVING')]
        plain = self.LIGHT() + [nec_dwelling.dev(x, 0, 'dup', 'n', 4) for x in (2, 9.5)] + [nec_dwelling.dev(12, 5, 'dup', 'e', 4), nec_dwelling.dev(0, 5, 'dup', 'w', 4), nec_dwelling.dev(6, 10, 'dup', 's', 4)]
        v = nec_dwelling.check_unit(_room(plain, polys=liv, doors=self.DOOR, sinks=[(9, 7, 2, 2)], circuits=cks))
        self.assertTrue(_has(v, '210.8', "6'-0\""), v)
        # but not through a wall: a sink in the next room pulls nothing
        two = liv + [([(12.4, 0), (20, 0), (20, 10), (12.4, 10)], 'BATH')]
        v = nec_dwelling.check_unit(_room(plain, polys=two, doors=self.DOOR, sinks=[(12.4, 4, 2, 2)], circuits=cks))
        self.assertFalse(_has(v, '210.8', "6'-0\""), v)
        v = nec_dwelling.check_unit(_room(devs+[nec_dwelling.dev(2, 5, 'lt', 'c', 2, 'B'), nec_dwelling.dev(0, 7, 'sw', 'w', 2, 'B')], polys=kit, doors=self.DOOR, circuits=cks))
        self.assertTrue(_has(v, '210.11(C)(1)'), v)                      # a light on a small-appliance circuit
        # the north wall becomes the separation: everything on it moves to the chase face
        w5 = [d._replace(mount='w5') for d in devs if d.y == 0 and d.kind != 'sw'] + \
             [d for d in devs if not (d.y == 0)] + [nec_dwelling.dev(0, 1, 'sw', 'w', 1, 'A')]
        v = nec_dwelling.check_unit(_room(w5+[nec_dwelling.dev(6, 0, 'gfci', 'n', 2)], polys=kit, doors=self.DOOR, circuits=cks, sep_y=0.0))
        self.assertTrue(_has(v, 'W4', "6'-0\""), v)
        v = nec_dwelling.check_unit(_room(w5+[nec_dwelling.dev(6, 0, 'gfci', 'w5', 2)], polys=kit, doors=self.DOOR, circuits=cks, sep_y=0.0))
        self.assertFalse(_has(v, 'W4'), v)
        # fans: every bath has one, on its own switch, and a unit has exactly one continuous fan
        bath = [(14, 0, 5, 8, 'BATH')]
        bd = devs + [nec_dwelling.dev(16.5, 4, 'rec', 'c', 1, 'C'), nec_dwelling.dev(14, 1, 'sw', 'w', 1, 'C'), nec_dwelling.dev(19, 4, 'gfci', 'e', 4)]
        v = nec_dwelling.check_unit(_room(bd, polys=kit, rooms=bath, doors=self.DOOR+[(14, 2, 2.67, 'v')], circuits=cks))
        self.assertTrue(_has(v, 'BATH', 'no exhaust fan'), v)
        self.assertTrue(_has(v, 'continuous'), v)
        bd += [nec_dwelling.dev(16.5, 6, 'fanc', 'c', 1, 'C')]
        v = nec_dwelling.check_unit(_room(bd, polys=kit, rooms=bath, doors=self.DOOR+[(14, 2, 2.67, 'v')], circuits=cks))
        self.assertTrue(_has(v, 'fan', 'shares'), v)
        bd[-1] = nec_dwelling.dev(16.5, 6, 'fanc', 'c', 1, 'F'); bd.append(nec_dwelling.dev(14, 1.5, 'sw', 'w', 1, 'F'))
        v = nec_dwelling.check_unit(_room(bd, polys=kit, rooms=bath, doors=self.DOOR+[(14, 2, 2.67, 'v')], circuits=cks))
        self.assertFalse(_has(v, 'fan'), v)
        self.assertFalse(_has(v, 'continuous'), v)

    def test_ohio_210_8a_leaves_the_240_v_outlets_alone(self):
        """RCO 3401.1 narrows 210.8(A) to 125 V 15 and 20 A receptacles: a range, a dryer and a
           water heater on unprotected 2-pole circuits in a kitchen pass; a duplex does not."""
        kit = [([(0, 0), (12, 0), (12, 10), (0, 10)], 'KITCHEN')]
        cks = [nec_dwelling.ckt(1, 'LTG', 15, 1, '#14', 'AFCI', 'ltg'), nec_dwelling.ckt(2, 'SA 1', 20, 1, '#12', 'AFCI/GFCI', 'sa'),
               nec_dwelling.ckt(3, 'RANGE', 50, 2, '#6', '—', 'range'), nec_dwelling.ckt(4, 'DRYER', 30, 2, '#10', '—', 'dryer'),
               nec_dwelling.ckt(5, 'WATER HEATER', 30, 2, '#10', '—', 'wh'), nec_dwelling.ckt(6, 'RCPT', 20, 1, '#12', 'AFCI', 'rcpt')]
        devs = self.LIGHT() + [nec_dwelling.dev(x, 0, 'gfci', 'n', 2) for x in (2, 9.5)] + \
               [nec_dwelling.dev(12, 5, 'gfci', 'e', 2), nec_dwelling.dev(0, 5, 'gfci', 'w', 2), nec_dwelling.dev(6, 10, 'gfci', 's', 2)] + \
               [nec_dwelling.dev(4, 10, 'range', 's', 3), nec_dwelling.dev(8, 10, 'dryer', 's', 4), nec_dwelling.dev(11, 10, 'wh', 's', 5)]
        v = nec_dwelling.check_unit(_room(devs, polys=kit, doors=self.DOOR, circuits=cks))
        self.assertFalse(_has(v, '210.8'), v)
        v = nec_dwelling.check_unit(_room(devs+[nec_dwelling.dev(3, 10, 'dup', 's', 6)], polys=kit, doors=self.DOOR, circuits=cks))
        self.assertTrue(_has(v, '210.8', 'dup'), v)

    def test_circuits_wire_heat_pumps_and_unused(self):
        self.assertTrue(nec_dwelling.wire_ok('#12', 20)); self.assertFalse(nec_dwelling.wire_ok('#12', 30)); self.assertTrue(nec_dwelling.wire_ok('#6', 50))
        hp = nec_dwelling.ckt(9, 'HEAT PUMP', 40, 2, '#10', 'GFCI', 'hp', mca=30, mocp=40)
        self.assertEqual(nec_dwelling.hp_violations(hp), [])
        self.assertTrue(nec_dwelling.hp_violations(nec_dwelling.ckt(9, 'HP', 40, 2, '#12', 'GFCI', 'hp', mca=30, mocp=40)))   # wire under MCA
        self.assertTrue(nec_dwelling.hp_violations(nec_dwelling.ckt(9, 'HP', 30, 2, '#10', 'GFCI', 'hp', mca=30, mocp=40)))   # breaker is not the MOCP
        self.assertTrue(nec_dwelling.hp_violations(nec_dwelling.ckt(9, 'HP', 40, 2, '#10', 'GFCI', 'hp')))                    # no nameplate
        v = nec_dwelling.hp_violations(nec_dwelling.ckt(9, 'HP', 40, 2, '#10', '—', 'hp', mca=30, mocp=40))
        self.assertEqual(v, [])                                                                         # listed HVAC: 210.8(F) Exception No. 2
        cks = [nec_dwelling.ckt(1, 'LTG', 15, 1, '#14', 'AFCI', 'ltg'), nec_dwelling.ckt(2, 'RCPT', 20, 1, '#14', 'AFCI', 'rcpt'),
               nec_dwelling.ckt(3, 'SPARE', 20, 1, '#12', 'AFCI', 'spare'), nec_dwelling.ckt(4, 'RANGE', 50, 2, '#6', '—', 'range')]
        rc = self.LIGHT() + [nec_dwelling.dev(x, 0, 'dup', 'n', 2) for x in (2, 9.5)] + [nec_dwelling.dev(12, 5, 'dup', 'e', 2), nec_dwelling.dev(0, 5, 'dup', 'w', 2), nec_dwelling.dev(6, 10, 'dup', 's', 2)]
        v = nec_dwelling.check_unit(_room(rc, doors=self.DOOR, circuits=cks))
        self.assertTrue(_has(v, 'circuit 2', '#14'), v)                  # 20 A on #14
        self.assertTrue(_has(v, 'circuit 4', 'no device'), v)            # a range circuit with nothing on it
        self.assertFalse(_has(v, 'circuit 3'), v)                        # spares are allowed to be empty
        v = nec_dwelling.check_unit(_room(rc+[nec_dwelling.dev(6, 0, 'dup', 'n', 9)], doors=self.DOOR, circuits=cks))
        self.assertTrue(_has(v, 'circuit 9', 'does not exist'), v)
        v = nec_dwelling.check_unit(_room(rc+[nec_dwelling.dev(6, 0, 'dup', 'n', 4)], doors=self.DOOR, circuits=cks))
        self.assertTrue(_has(v, 'individual', 'circuit 4'), v)           # a duplex on the range circuit


if __name__ == '__main__':
    unittest.main()
