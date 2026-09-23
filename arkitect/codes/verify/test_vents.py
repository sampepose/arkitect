"""OPC Chapter 9 on synthetic systems: the trap arm of Table 909.1, 905.4's rise, the rule
   that keeps a stack carrying an upper floor from venting the floor below it, and 903.2's
   size at the roof.

   The fault 903.2 pins was on the sheet: a note reading "3\" MINIMUM AT THE ROOF LINE"
   over risers labelled 2" VTR, with nothing drawn to say where the pipe got bigger."""
import unittest

from arkitect.codes.ohio import opc_vents as V


class TrapArmTests(unittest.TestCase):

    def test_table_909_1_is_the_printed_table(self):
        self.assertEqual(V.trap_arm_max(1.5), 6.0)
        self.assertEqual(V.trap_arm_max(2.0), 8.0)
        self.assertEqual(V.trap_arm_max(3.0), 12.0)
        self.assertEqual(V.trap_arm_max(4.0), 16.0)
        self.assertEqual(V.trap_arm_max(1.25), 5.0)
        with self.assertRaises(KeyError):
            V.trap_arm_max(2.5)

    def test_an_arm_over_its_row_fails_and_one_on_it_passes(self):
        self.assertEqual(V.trap_arm_violations([V.Arm('LAV', 1.5, 6.0)]), [])
        bad = V.trap_arm_violations([V.Arm('LAV', 1.5, 6.2)])
        self.assertTrue(any('over Table 909.1' in m for m in bad), bad)


class RiseTests(unittest.TestCase):

    def test_a_vent_that_turns_under_the_rim_fails(self):
        rim = 31.0/12
        self.assertEqual(V.dry_vent_rise_violations([('V-A', rim+0.5, rim)]), [])
        bad = V.dry_vent_rise_violations([('V-A', rim+0.4, rim)])
        self.assertTrue(any('905.4' in m for m in bad), bad)


class StackVentTests(unittest.TestCase):

    def test_a_stack_carrying_the_floor_above_cannot_vent_the_floor_below(self):
        drains = [('U3 WC', 2), ('U3 LAV', 2), ('U2 LAV', 1)]
        bad = V.stack_vent_violations([('D', True, drains, [('U2 WC', 1)])])
        self.assertTrue(any('913 takes no water closet' in m for m in bad), bad)

    def test_a_stack_with_nothing_above_the_fixture_is_fine(self):
        drains = [('U2 LAV', 1)]
        self.assertEqual(V.stack_vent_violations([('D', True, drains, [('U2 WC', 1)])]), [])

    def test_without_a_water_closet_it_is_913s_conditions_that_are_missing(self):
        drains = [('U3 SINK', 2)]
        bad = V.stack_vent_violations([('E', False, drains, [('U2 SINK', 1)])])
        self.assertTrue(any('913 waste stack vent' in m for m in bad), bad)

    def test_the_two_facts_the_rule_rests_on(self):
        self.assertTrue(V.WET_VENT_SAME_FLOOR)      # 912: one floor level
        self.assertFalse(V.WASTE_STACK_TAKES_WC)    # 913: no water closet
        self.assertEqual(V.DRY_VENT_RISE, 0.5)      # 905.4: 6"


class WasteStackTests(unittest.TestCase):
    """913: the one arrangement that vents several floors from one pipe, and its price."""

    def test_table_913_4_is_the_printed_table(self):
        self.assertEqual(V.WASTE_STACK[2.0], (2, 4))
        self.assertEqual(V.WASTE_STACK[3.0], (None, 24))
        self.assertEqual(V.WASTE_STACK[1.5], (1, 2))

    def test_a_stack_inside_its_row_passes_and_one_over_it_fails(self):
        self.assertEqual(V.waste_stack_violations([('E', 2.0, False, [2, 2], 4, False)]), [])
        over = V.waste_stack_violations([('E', 2.0, False, [3, 2], 5, False)])
        self.assertEqual(len(over), 2)                     # the branch interval and the total
        self.assertTrue(any('at one branch interval' in m for m in over), over)

    def test_a_water_closet_or_an_offset_disqualifies_it(self):
        wc = V.waste_stack_violations([('C', 3.0, True, [4], 8, False)])
        self.assertTrue(any('no water closet' in m for m in wc), wc)
        off = V.waste_stack_violations([('E', 2.0, False, [2], 4, True)])
        self.assertTrue(any('913.2' in m for m in off), off)


class WetVentTests(unittest.TestCase):
    """912: the two arrangements, on synthetic groups. Each has its own requirements, and
       each check is written so that the arrangement a project claims is the one measured."""

    def _bath(self, **kw):
        """A vertical wet vent that passes: the closet lowest, the rest over it."""
        conns = [V.Conn('WC', 'wc', 3, -1.0, 3.0), V.Conn('TUB', 'tub', 2, -0.5, 3.0),
                 V.Conn('LAV', 'lav', 1, 1.33, 3.0)]
        g = dict(name='STACK X', size=3.0, conns=conns, vent_from=1.33)
        g.update(kw)
        return [(g['name'], g['size'], g['conns'], g['vent_from'])]

    def test_table_912_3_is_the_printed_table(self):
        self.assertEqual(V.WET_VENT[1.5], 1)
        self.assertEqual(V.WET_VENT[2.0], 4)
        self.assertEqual(V.WET_VENT[3.0], 12)
        self.assertEqual(V.wet_vent_min_size(1), 1.5)
        self.assertEqual(V.wet_vent_min_size(4), 2.0)
        self.assertEqual(V.wet_vent_min_size(12), 3.0)
        with self.assertRaises(ValueError):
            V.wet_vent_min_size(13)

    def test_a_vertical_wet_vent_the_code_allows_passes(self):
        self.assertEqual(V.vertical_wet_violations(self._bath()), [])

    def test_a_fixture_below_the_water_closet_fails(self):
        conns = [V.Conn('WC', 'wc', 3, -0.5, 3.0), V.Conn('TUB', 'tub', 2, -1.0, 3.0),
                 V.Conn('LAV', 'lav', 1, 1.33, 3.0)]
        bad = V.vertical_wet_violations(self._bath(conns=conns))
        self.assertTrue(any('connects below the water closet' in m for m in bad), bad)

    def test_two_fixtures_at_one_elevation_fail(self):
        conns = [V.Conn('WC', 'wc', 3, -1.0, 3.0), V.Conn('TUB', 'tub', 2, 1.33, 3.0),
                 V.Conn('LAV', 'lav', 1, 1.33, 3.0)]
        bad = V.vertical_wet_violations(self._bath(conns=conns))
        self.assertTrue(any('independently' in m for m in bad), bad)

    def test_something_draining_in_above_the_group_takes_its_dry_vent_away(self):
        """912.2.2 wants the dry vent at the most upstream fixture drain: a fixture
           connecting higher up makes the pipe over the group a drain, not a vent."""
        bad = V.vertical_wet_violations(self._bath(vent_from=4.0))
        self.assertTrue(any('912.2.2' in m for m in bad), bad)

    def test_a_vertical_wet_vent_is_sized_on_its_load(self):
        bad = V.vertical_wet_violations(self._bath(size=1.5))
        self.assertTrue(any('Table 912.3' in m for m in bad), bad)
        self.assertTrue(any('water closet' in m for m in bad), bad)

    def _group(self, conns=None, dry='LAV', extras=()):
        conns = conns or [V.Conn('LAV', 'lav', 1, 0.0, 2.0), V.Conn('WC', 'wc', 3, 3.0, 3.0),
                          V.Conn('TUB', 'tub', 2, 5.5, 3.0)]
        return [('V-X', conns, dry, list(extras))]

    def test_a_horizontal_wet_vent_the_code_allows_passes(self):
        self.assertEqual(V.horizontal_wet_violations(self._group()), [])

    def test_the_dry_vent_may_not_stand_past_one_fixture(self):
        bad = V.horizontal_wet_violations(self._group(dry='TUB'))
        self.assertTrue(any('912.2.1 allows one' in m for m in bad), bad)

    def test_the_dry_vent_may_not_stand_at_a_water_closet(self):
        conns = [V.Conn('WC', 'wc', 3, 0.0, 3.0), V.Conn('LAV', 'lav', 1, 3.0, 3.0)]
        bad = V.horizontal_wet_violations(self._group(conns=conns, dry='WC'))
        self.assertTrue(any('at a water closet' in m for m in bad), bad)

    def test_anything_else_on_the_branch_fails(self):
        bad = V.horizontal_wet_violations(self._group(extras=[('KITCHEN SINK', 2.0)]))
        self.assertTrue(any('discharges into the wet vent' in m for m in bad), bad)
        self.assertEqual(V.horizontal_wet_violations(self._group(extras=[('KITCHEN SINK', 9.0)])), [])

    def test_a_section_under_table_912_3_or_under_the_closets_3_fails(self):
        conns = [V.Conn('LAV', 'lav', 1, 0.0, 2.0), V.Conn('WC', 'wc', 3, 3.0, 2.0),
                 V.Conn('TUB', 'tub', 2, 5.5, 2.0)]
        bad = V.horizontal_wet_violations(self._group(conns=conns))
        self.assertTrue(any('carries a water closet at 2"' in m for m in bad), bad)
        big = [V.Conn('LAV', 'lav', 1, 0.0, 1.5), V.Conn('TUB', 'tub', 2, 3.0, 1.5)]
        over = V.horizontal_wet_violations(self._group(conns=big, dry='LAV'))
        self.assertTrue(any("over Table 912.3's 1" in m for m in over), over)

    def test_only_bathroom_group_fixtures_may_be_wet_vented(self):
        conns = [V.Conn('SINK', 'sink', 2, 0.0, 2.0), V.Conn('WC', 'wc', 3, 3.0, 3.0)]
        bad = V.horizontal_wet_violations(self._group(conns=conns, dry='SINK'))
        self.assertTrue(any('not a bathroom group fixture' in m for m in bad), bad)


class ClaimedWasteStackTests(unittest.TestCase):
    """The interlock: a stack venting the floors on it is a defect UNLESS the set claims it
       under 913 and holds it to 913's conditions."""

    def _stacks(self):
        drains = [('U2 SINK', 1), ('U3 SINK', 2)]
        return [('E', False, drains, drains)]

    def test_unclaimed_it_is_a_violation(self):
        bad = V.stack_vent_violations(self._stacks())
        self.assertTrue(any('913 waste stack vent may do that' in m for m in bad), bad)

    def test_claimed_it_is_913s_to_judge(self):
        self.assertEqual(V.stack_vent_violations(self._stacks(), claimed_913=('E',)), [])

    def test_the_sentence_a_sheet_prints_carries_the_table(self):
        t = V.waste_stack_text([('E', 2.0, False, [2, 2], 4, False)])
        self.assertEqual(t, 'E 2" CARRIES 2 DFU AT A BRANCH INTERVAL OF 2 AND 4 IN ALL OF 4')


if __name__ == '__main__':
    unittest.main()


class FrostClosureTests(unittest.TestCase):
    """903.2: at or under 0 F, a roof or wall vent is 3" and the increase is made not less
       than a foot inside the thermal envelope."""

    def test_the_rule_binds_at_or_under_zero(self):
        self.assertTrue(V.frost_closure(0))
        self.assertTrue(V.frost_closure(-10))
        self.assertFalse(V.frost_closure(5))

    def test_a_small_vent_is_increased_and_a_big_one_is_not(self):
        self.assertEqual(V.roof_size('2', 0), '3')
        self.assertEqual(V.roof_size('1-1/2', 0), '3')
        self.assertEqual(V.roof_size('3', 0), '3')
        self.assertEqual(V.roof_size('4', 0), '4')      # never reduced to the minimum

    def test_a_warm_design_temperature_leaves_the_size_alone(self):
        self.assertEqual(V.roof_size('2', 5), '2')
        self.assertEqual(V.roof_size('3', 5), '3')

    def test_the_increase_is_made_inside_the_envelope(self):
        self.assertEqual(V.INCREASE_INSIDE, 1.0)
        self.assertEqual(V.FROST_CLOSURE_SIZE, '3')

    def test_a_two_inch_vent_drawn_at_two_inches_is_caught(self):
        v = V.roof_vent_violations([('STACK E', '2', '2')], 0)
        self.assertEqual(len(v), 1)
        self.assertIn('903.2', v[0])
        self.assertIn('STACK E', v[0])

    def test_the_same_vent_drawn_increased_passes(self):
        self.assertEqual(V.roof_vent_violations([('STACK E', '3', '2')], 0), [])

    def test_nothing_is_asked_of_it_in_a_warm_climate(self):
        self.assertEqual(V.roof_vent_violations([('STACK E', '2', '2')], 5), [])


class WeirTests(unittest.TestCase):
    """909.2: the vent connection is not below the weir of the trap it vents. The datum is
       one height per group, positive up, so a fixture on a floor and a branch inside that
       floor are on the same scale."""

    def test_table_909_1_never_falls_further_than_the_trap_is_wide(self):
        """Why an arm inside Table 909.1 needs no separate 909.2 fall check: on every row the
           slope times the maximum length lands at or under the trap's own size."""
        for size in sorted(V.TRAP_ARM):
            self.assertLessEqual(V.table_909_1_fall(size), size+1e-9,
                                 'Table 909.1 row %g" falls further than the trap is wide' % size)
        # the three small rows sit exactly on it, which is what makes the pairing deliberate
        self.assertAlmostEqual(V.table_909_1_fall(1.25), 1.25)
        self.assertAlmostEqual(V.table_909_1_fall(1.5), 1.5)
        self.assertAlmostEqual(V.table_909_1_fall(2.0), 2.0)

    def test_a_lavatory_vented_from_a_branch_in_the_floor_below_it_is_caught(self):
        """The defect a plan cannot show: the trap stands 18" over its floor and its vent is
           the branch 9" under that floor, so the connection is 2'-3" below the weir."""
        w = V.Weir('BATH 2 LAV 2', 'lav', 1.5, 18.0/12, -9.0/12)
        v = V.weir_violations([w])
        self.assertEqual(len(v), 1)
        self.assertIn('909.2', v[0])
        self.assertIn('BATH 2 LAV 2', v[0])

    def test_the_same_lavatory_vented_in_its_own_wall_passes(self):
        """A vent standing at the fixture tees off at the trap arm, so the connection is under
           the weir only by the arm's fall -- inside the drain's diameter."""
        weir = 18.0/12
        fall = 6.0*0.25/12                      # Table 909.1's longest 1-1/2" arm, 1-1/2"
        self.assertEqual(V.weir_violations([V.Weir('LAV', 'lav', 1.5, weir, weir-fall)]), [])

    def test_one_more_inch_of_fall_than_the_drain_is_wide_fails(self):
        weir = 18.0/12
        ok = V.Weir('LAV', 'lav', 1.5, weir, weir-V.weir_fall_max(1.5))
        bad = ok._replace(vent_at=ok.vent_at-1.0/12)
        self.assertEqual(V.weir_violations([ok]), [])
        self.assertEqual(len(V.weir_violations([bad])), 1)

    def test_a_water_closet_is_excepted_by_the_section(self):
        self.assertEqual(V.WEIR_EXEMPT, ('wc',))
        self.assertEqual(V.weir_violations([V.Weir('WC', 'wc', 3.0, 0.0, -9.0/12)]), [])

    def test_a_trap_hung_in_the_floor_is_not_measured_here(self):
        """A tub's trap and a closet bend are set to the pipe they drain to, so there is no
           fixed weir height to measure and TRAP_WEIR deliberately carries none."""
        for kind in ('tub', 'shower', 'wc'):
            self.assertNotIn(kind, V.TRAP_WEIR)
            self.assertEqual(V.weir_violations([V.Weir(kind.upper(), kind, 2.0, 1.0, -2.0)]), [])
        for kind in ('lav', 'sink', 'wd'):
            self.assertIn(kind, V.TRAP_WEIR)

    def test_the_limit_is_the_drains_own_diameter(self):
        self.assertAlmostEqual(V.weir_fall_max(1.5), 1.5/12)
        self.assertAlmostEqual(V.weir_fall_max(3.0), 3.0/12)
