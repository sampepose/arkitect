"""400 Oak's drainage: the model passes, the tables are the code's, every fixture drains
   once, the sewer stays covered, and the rules fire."""
import unittest

from projects.example_400.verify import enter, leave
from arkitect.codes.ohio import opc_drainage as opc_drainage_shared
from arkitect.codes.ohio import opc_separation


def setUpModule():
    enter()


def tearDownModule():
    leave()


class DrainageTests(unittest.TestCase):

    def test_every_below_slab_fixture_has_its_own_dry_vent(self):
        """The reviewer's comment of 2026-09-20: a stack that carries the level above is not
           a vent for the level below. 912 wet vents one floor and 913's waste stack vent
           takes no water closet, so each Level 1 group keeps its own dry vent."""
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        self.assertEqual(d.vent_violations(), [])
        self.assertEqual(sorted(v.mark for v in d.DRY_VENTS),
                         ['V-A', 'V-B', 'V-C', 'V-D', 'V-E', 'V-F'])
        for dv in d.DRY_VENTS:                       # a vent stands at a lavatory or a sink
            self.assertIn(dv.at_fixture, ('lav', 'sink', 'wd'))
            self.assertNotEqual(dv.at_fixture, 'wc')
        # every arm is inside Table 909.1, and the check bites when one is not
        for _b, a in d.trap_arms():
            self.assertLessEqual(a.length, V.trap_arm_max(a.size), a.name)
        self.assertTrue(V.trap_arm_violations([V.Arm('X', 1.5, 6.5)]))

    def test_a_vent_that_ties_in_too_low_fails(self):
        """905.4: the tie stands 6" over the highest flood rim on the stack."""
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        self.assertEqual(V.dry_vent_rise_violations(d.vent_ties()), [])
        low = [(m, rim+0.2, rim) for m, _tie, rim in d.vent_ties()]
        self.assertTrue(V.dry_vent_rise_violations(low))

    def test_the_model_passes(self):
        from src import drainage as d
        d.check_drainage()



    def test_the_tallies_and_the_drains_agree(self):
        from src import drainage as d
        from arkitect.codes.ohio import opc_drainage as opc_drainage
        from arkitect.lib.model import drains as drains
        self.assertEqual([d.building_dfu(b) for b in d.BUILDINGS], [15, 18])
        for b in d.BUILDINGS:
            self.assertEqual(opc_drainage.run_dfu(b, drains.exit_run(b)), d.building_dfu(b))
        self.assertEqual(d.total_dfu(), 33)

    def test_one_exit_each_through_the_south_wall(self):
        from src import drainage as d
        from arkitect.lib.model import drains as drains
        for b in d.BUILDINGS:
            self.assertAlmostEqual(drains.exit_pen(b).pos[0], b.W)

    def test_water_and_sewer_never_meet(self):
        from src import drainage as d
        for b in d.BUILDINGS:
            self.assertEqual(opc_separation.water_crossings(b, d.GROUND), [])
            self.assertEqual(opc_separation.site_crossings(b, d.GROUND), [])
            self.assertIsNone(d.service_sleeve(b))
            self.assertGreaterEqual(d.service_to_sewer(b), 4*opc_separation.SEWER_SEP)

    def test_the_sewer_stays_covered_to_dana(self):
        from src import drainage as d
        cover, _at = d.sewer_cover()
        self.assertGreaterEqual(cover, d.SEWER_COVER_MIN)
        keep = d.COVER
        d.COVER = 1.0                                 # 300's 12": the lot's fall to Oak uncovers the pipe
        try:
            self.assertTrue(any('of earth over it' in v for v in d.drainage_violations()))
        finally:
            d.COVER = keep

    def test_the_exits_pass_the_wall_above_the_footing(self):
        from src import drainage as d
        for b in d.BUILDINGS:
            self.assertGreater(d.below_grade(opc_drainage_shared.exit_invert(b, cover=d.COVER)), d.FOOTING_TOP)

    def test_the_sink_branch_crosses_the_bearing_strip_square(self):
        from src import drainage as d
        got = opc_separation.strip_crossings(d.BUILDING_2, d.GROUND)
        self.assertEqual([(r.size, nm) for r, nm, _p in got], [('2', 'UNITS 2 AND 3 BEARING WALL')])

    def test_stacks_a_and_e_stand_in_the_chases_the_plans_draw(self):
        from src import drainage as d, building1 as b1, building2 as b2, mechanical as m
        self.assertIn(b1.STACK_A_CHASE, b1.F_L1)
        self.assertIn(b2.STACK_E_CHASE, b2.F_B2)                 # one list, both levels
        for pos, box in ((d.A_POS, d._CHASE), (d.E_POS, d._E_CHASE)):
            self.assertTrue(box[0] < pos[0] < box[0]+box[2] and box[1] < pos[1] < box[1]+box[3])
        # neither chase stands across a window of its wall
        for n, wall, box in ((1, 'SOUTH WALL', d._CHASE), (2, 'NORTH WALL', d._E_CHASE)):
            for op in m.WALLS[n][wall].openings:
                self.assertTrue(box[1]+box[3] <= op.lo or op.hi <= box[1], (wall, op.name))

    def test_a_stack_at_a_window_fails(self):
        """Where Stack E first stood: behind the sinks, under the kitchen window of both units."""
        from src import drainage as d
        from arkitect.lib.model import drains as drains
        self.assertEqual(d.stack_violations(), [])
        keep = d.BUILDING_2.stacks[1]
        d.BUILDING_2.stacks[1] = keep._replace(pos=(keep.pos[0], drains._cy(d.U2_KS)))
        try:
            bad = d.stack_violations()
            self.assertTrue(any('stack E' in v and 'L1 W-B' in v for v in bad) and any('L2 W-B' in v for v in bad), bad)
        finally:
            d.BUILDING_2.stacks[1] = keep

    def test_a_washer_drain_on_the_dryer_duct_fails(self):
        from src import drainage as d, mechanical as m
        self.assertEqual(d.laundry_violations(), [])
        duct = next(t for t in m.TERMS[2]['NORTH WALL'] if t.mark == 'DR-2')
        keep = d.BUILDING_2.stacks[2]
        d.BUILDING_2.stacks[2] = keep._replace(pos=(keep.pos[0], duct.along+0.1))
        try:
            self.assertTrue(any('dryer duct' in v for v in d.laundry_violations()))
        finally:
            d.BUILDING_2.stacks[2] = keep

    def test_a_slab_fixture_with_no_vent_fails(self):
        from src import drainage as d
        keep = list(d.DRY_VENTS)
        d.DRY_VENTS[:] = [v for v in keep if v.mark != 'V-A']       # the kitchen sink loses its vent
        try:
            self.assertTrue(any('nothing vents' in v for v in d.vent_violations()))
        finally:
            d.DRY_VENTS[:] = keep

    def test_the_riser_diagram_is_the_models(self):
        from src import drainage as d
        from src.sheets import p601
        self.assertEqual(len(p601.risers()), sum(len(b.stacks) for b in d.BUILDINGS))
        vent = [r for r in p601.risers() if r[2]]
        self.assertEqual([r[0][:6] for r in vent], ['VENT B'])


class VentingArrangementTests(unittest.TestCase):
    """The three arrangements this set uses, each measured against its own requirements --
       the reviewer's comment of 2026-09-20 that P-601 described one system and drew another."""

    def test_unit_2s_bath_is_a_horizontal_wet_vent_below_the_slab(self):
        """Its lavatory drops through the slab AT the lavatory, and its drain from there
           carries the closet and then the tub: 912.1, in the direction of flow."""
        from src import drainage as d
        lav = [p for p in d.BUILDING_2.pens
               if p.kind == 'drop' and any('lav' in ks for _u, _l, ks in p.serves)]
        self.assertEqual(len(lav), 1)
        stack_d = next(st for st in d.BUILDING_2.stacks if st.name == 'D')
        self.assertEqual([l for _u, l, _ks in stack_d.serves], [2])   # Unit 3 alone
        group = next(g for g in d.horizontal_wet_groups() if g[0].endswith('V-D'))
        self.assertEqual([cn.kind for cn in group[1]], ['lav', 'wc', 'tub'])
        self.assertEqual(group[2], 'UNIT 2 LAV')          # the dry vent stands at the head
        self.assertEqual(group[3], [])                    # nothing else is on that branch
        self.assertEqual([cn.size for cn in group[1]], [2.0, 3.0, 3.0])

    def test_stack_d_discharges_downstream_of_that_group(self):
        """912.1: any additional fixture discharges downstream of the wet vent. Unit 3's
           bath is on stack D, and its foot comes into the drain past the tub."""
        from src import drainage as d
        from arkitect.lib.model import runs
        group = next(g for g in d.horizontal_wet_groups() if g[0].endswith('V-D'))
        walk = d._walk(d.BUILDING_2, d.LAV2)
        line = d._flow_line(walk)
        foot = next(p for p in d.BUILDING_2.pens if p.kind == 'stack' and p.serves == 'D')
        self.assertGreater(d._join_at(d.BUILDING_2, line, foot.pos),
                           max(cn.at for cn in group[1]))
        self.assertGreater(runs.length([d.D_POS, (d.D_FOOT_X, d.D_POS[1])]), 0)

    def test_the_level_2_groups_are_vertical_wet_vents_with_the_closet_lowest(self):
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        groups = d.vertical_wet_groups()
        self.assertEqual([g[0].split()[3].rstrip(',') for g in groups], ['D'])     # Bath 2 is 912.1, below
        for _name, _size, conns, _vent in groups:
            wc = min(cn.at for cn in conns if cn.kind == 'wc')
            self.assertTrue(all(cn.at >= wc for cn in conns))
            self.assertEqual(len({round(cn.at, 6) for cn in conns}), len(conns))
        self.assertEqual(V.vertical_wet_violations(groups), [])

    def test_raising_the_closet_over_the_tub_fails_the_build(self):
        from src import drainage as d
        keep = d.CONN_Z['wc']
        d.CONN_Z['wc'] = d.CONN_Z['tub']+1.0
        try:
            self.assertTrue(any('connects below the water closet' in v for v in d.vent_violations()))
        finally:
            d.CONN_Z['wc'] = keep

    def test_e_and_f_are_913_waste_stack_vents_and_their_offsets_are_below_both(self):
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        got = d.waste_stacks()
        self.assertEqual([n for n, *_r in got], ['E', 'F'])
        for name, size, wc, by, total, offset in got:
            self.assertFalse(wc)                          # 913 takes no water closet
            self.assertFalse(offset)                      # 913.2: none between the connections
            self.assertEqual((max(by), total), (2, 4))
        # E is exactly on Table 913.4's 2" row; F is 3" because it takes the washers, OPC 406.2
        self.assertEqual({n: size for n, size, *_r in got}, {'E': 2.0, 'F': 3.0})
        self.assertEqual(V.waste_stack_violations(got), [])

    def test_every_washer_drains_into_3_inches_and_a_2_inch_stack_f_fails(self):
        """OPC 406.2: a washer's fixture drain connects to a 3\" or larger branch or stack.
           Table 913.4 would let stack F carry both washers at 2\"; 406.2 does not."""
        from src import drainage as d
        from arkitect.codes.ohio.opc_drainage import washer_connections, washer_violations
        self.assertEqual(len(washer_connections(d.BUILDINGS)), 3)
        self.assertEqual(washer_violations(d.BUILDINGS), [])
        b2 = d.BUILDINGS[1]
        i = next(i for i, s in enumerate(b2.stacks) if s.name == 'F')
        keep = b2.stacks[i]
        b2.stacks[i] = keep._replace(size='2')
        try:
            self.assertEqual(len([v for v in washer_violations(d.BUILDINGS) if 'OPC 406.2' in v]), 2)
        finally:
            b2.stacks[i] = keep

    def test_an_offset_between_the_connections_fails(self):
        """STACK_OFFSET_Z is where the stack turns to its foot: at the slab, under every
           connection. Lift it between them and 913.2 fails the build."""
        from src import drainage as d
        keep = d.STACK_OFFSET_Z
        d.STACK_OFFSET_Z = d.levels.FLOOR_RISE/2.0
        try:
            self.assertTrue(any('913.2' in v for v in d.vent_violations()))
        finally:
            d.STACK_OFFSET_Z = keep

    def test_dropping_the_913_claim_brings_the_stack_vent_rule_back(self):
        from src import drainage as d
        keep = d.WASTE_STACKS
        d.WASTE_STACKS = ('F',)
        try:
            self.assertTrue(any('913 waste stack vent may do that' in v for v in d.vent_violations()))
        finally:
            d.WASTE_STACKS = keep

    def test_the_riser_draws_what_the_model_says(self):
        """Every connection, trap and vent on the sheet comes from src/drainage.py."""
        from src import drainage as d
        from src.sheets import p601
        cells = {cell.title.split()[1]: cell for cell in p601.risers()}
        stack_a = cells['A']
        self.assertEqual(stack_a.hangs, [])                           # nothing connects to it above a floor
        self.assertEqual([(fl.mark, [fx.label for fx in fl.fixes]) for fl in stack_a.floors],
                         [('V-E', ['LAV', 'LAV', 'WC', 'TUB'])])      # in the floor, in the direction of flow
        self.assertEqual([sl.mark for sl in stack_a.slabs], ['V-A'])
        self.assertEqual([fx.label for sl in cells['D'].slabs for fx in sl.fixes],
                         ['LAV', 'WC', 'TUB'])                        # in the direction of flow
        self.assertIsNotNone(cells['E'].span)                         # the 913.2 bracket
        self.assertIn('913.2', cells['E'].note)
        self.assertEqual(sum(len(sl.fixes) for cell in cells.values() for sl in cell.slabs)
                         + sum(len(fl.fixes) for cell in cells.values() for fl in cell.floors),
                         len(d.trap_arm_rows()))                      # one trap drawn per arm

    def test_bath_2_is_a_horizontal_wet_vent_in_the_level_2_floor(self):
        """A reviewer found Bath 2's lavatories modelled as connecting to stack A 16" and 20"
           over the floor while note 1a sent the branches through the floor trusses. Stack A
           stands under the tub, 6'-8" and 9'-8" from the lavatories: nothing vertical stands
           at them, so the group is 912.1's horizontal wet vent in the floor, V-E at its head."""
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        g = next(g for g in d.horizontal_wet_groups() if g[0].endswith('V-E'))
        _name, conns, head, extras = g
        self.assertEqual([c.kind for c in conns], ['lav', 'lav', 'wc', 'tub'])
        self.assertEqual((head, conns[0].at, extras), ('UNIT 1 LAV', 0.0, []))
        self.assertEqual([c.size for c in conns], [2.0, 2.0, 3.0, 3.0])
        self.assertEqual(V.horizontal_wet_violations([g]), [])
        # the lavatories are too far from the stack for any arrangement hanging on it
        for f in d._LAVS2:
            self.assertGreater(abs(f.x+f.w/2.0-d.A_POS[0]), V.trap_arm_max(1.5))
        # and it fits the floor: shallow the trusses and the build says so
        self.assertLessEqual(d.floor_branch_bottom(), d.levels.F2_DEPTH-d.TRUSS_CHORD)
        keep = d.levels.F2_DEPTH
        d.levels.F2_DEPTH = d.floor_branch_bottom()
        try:
            self.assertTrue(any('into the bottom chord' in v for v in d.vent_violations()))
        finally:
            d.levels.F2_DEPTH = keep

    def test_web_clear_is_both_chords(self):
        """The clear depth between the chords is the truss less BOTH of them, and the depth
           the gate measures is neither that nor the same datum. The sheet printed the gate's
           figure as the clear depth once (a 14" truss reading 13-1/4" between its chords),
           which is the subfloor and one chord counted as pipe space."""
        from src import drainage as d
        from arkitect.lib.units import inches
        self.assertEqual(d.web_clear(), d.levels.F2_JOIST-2*d.TRUSS_CHORD)
        self.assertEqual(inches(d.web_clear()), '11"')
        self.assertGreater(d.levels.F2_DEPTH-d.TRUSS_CHORD, d.web_clear())
        # what the branch uses of that clear depth, which is what P-102 prints
        used = d.floor_branch_bottom()-d.levels.SUBFLOOR-d.BRANCH_TOP
        self.assertLess(used, d.web_clear())
        self.assertEqual((inches(used), inches(d.web_clear())), ('5-3/4"', '11"'))


class StackInCavityTests(unittest.TestCase):
    """Stack F stands in an exterior wall's stud cavity and A-601 fills that wall with a batt
       as deep as the cavity. Both were true and they did not fit; only the ROOM said so."""

    def test_stack_f_is_the_one_drain_in_a_cavity(self):
        from src import drainage as d
        self.assertEqual(d.CAVITY_STACKS, ('F',))
        self.assertEqual([r.name for r in d.cavity_runs()], ['STACK F'])
        self.assertEqual(d.cavity_violations(), [])

    def test_the_bay_is_measured_at_the_fitting_and_closes_with_deeper_studs(self):
        from src import drainage as d
        from arkitect.lib.model import fit
        from arkitect.lib.units import inches
        r = d.cavity_runs()[0]
        self.assertEqual(inches(r.od), '3-1/2"')          # a "3 inch" stack, outside
        self.assertEqual(inches(r.fitting), '4-1/2"')     # and its hub, which governs
        self.assertGreater(r.fitting, r.od)
        self.assertEqual((inches(r.depth), inches(r.added)), ('5-1/2"', '1-3/4"'))
        self.assertEqual(inches(fit.cavity_depth(r)), '7-1/4"')       # a 2x8 bay
        self.assertEqual(inches(r.fill), '2"')
        self.assertEqual(inches(fit.cavity_clear(r)), '3/4"')

    def test_without_the_deeper_studs_the_fitting_does_not_fit(self):
        """A reviewer, 2026-09-21: 2" + 3-1/2" is the whole 2x6, which "accommodates straight
           pipe, but leaves no allowance for the larger outside dimensions of coupling hubs
           and sanitary tees". The bay is 1" short at the hub, and says so."""
        from src import drainage as d
        from arkitect.lib.model import fit
        from arkitect.lib.units import inches
        bare = [r._replace(added=0.0) for r in d.cavity_runs()]
        self.assertEqual(inches(fit.cavity_deepening_needed(bare[0])), '1"')
        v = fit.cavity_violations(bare)
        self.assertEqual(len(v), 1)
        self.assertIn('STACK F', v[0])

    def test_the_stack_stands_where_the_fill_behind_its_fitting_says(self):
        """Its centreline is one fill plus half a hub in from the exterior stud face, so the
           foam behind the WIDEST part of the line is the foam the schedule names."""
        from src import drainage as d
        from src import envelope as E
        from arkitect.lib.model import pipe
        from arkitect.lib.units import inches
        self.assertAlmostEqual(d.F_POS[0], E.STACK_BAY_FILL+pipe.fitting_od(d.F_SIZE)/2.0)
        self.assertEqual(inches(d.F_POS[0]), '4-1/4"')
        back_of_fitting = d.F_POS[0]-pipe.fitting_od(d.F_SIZE)/2.0
        self.assertAlmostEqual(back_of_fitting, E.STACK_BAY_FILL)

    def test_the_scheduled_batt_would_not_fit_behind_it(self):
        """The reviewer's finding, in the model: this is why the bay has its own fill."""
        from src import drainage as d
        from src import envelope as E
        from arkitect.lib.model import fit
        bad = [r._replace(fill=E.CAVITY_BATT, fill_name='R-%d BATT' % E.CAVITY_BATT_R)
               for r in d.cavity_runs()]
        v = fit.cavity_violations(bad)
        self.assertEqual(len(v), 1)
        self.assertIn('STACK F', v[0])
        self.assertIn('R-21 BATT', v[0])

    def test_making_the_stack_bigger_fails_the_build(self):
        from src import drainage as d
        from arkitect.lib.model import pipe
        keep = list(d.BUILDINGS[1].stacks)
        i = next(j for j, s in enumerate(keep) if s.name == 'F')
        d.BUILDINGS[1].stacks[i] = keep[i]._replace(size='4')
        try:
            v = d.cavity_violations()
            self.assertEqual(len(v), 1, v)
            self.assertIn('STACK F', v[0])
            self.assertGreater(pipe.od('4', 'IPS'), pipe.od('3', 'IPS'))
        finally:
            d.BUILDINGS[1].stacks[i] = keep[i]

    def test_the_a601_rows_read_the_same_batt_the_check_measures(self):
        from src import envelope as E
        from src.sheets.a601 import wall_rows
        for row in wall_rows().values():
            self.assertIn('R-%d' % E.CAVITY_BATT_R, row)


class StackAEndsAtItsBranchTests(unittest.TestCase):
    """a recorded decision: stack A's top is under Bath 2's tub, so a vent of its own would leave it sideways
       inside the Level 2 floor below every rim in the room (905.4). It ends at the branch; V-E,
       the branch's head vent, rises in the partition through the roof, and V-F and V-A join it
       in the attic."""

    def test_stack_a_has_no_roof_vent_and_v_e_has_one(self):
        from src import drainage as dr
        self.assertEqual(dr.vent_violations(), [])
        self.assertIn('A', dr.ENDS_AT_BRANCH)
        marks = [m for m, _roof, _below in dr.roof_vent_list()]
        self.assertNotIn('BUILDING 1 stack A', marks)
        self.assertIn('BUILDING 1 vent V-E', marks)
        joins = {d.mark: d.ties_into for d in dr.DRY_VENTS if d.mark in ('V-A', 'V-E', 'V-F')}
        self.assertEqual(joins, {'V-A': 'V-E', 'V-E': None, 'V-F': 'V-E'})
        for mark, z, rim in dr.vent_ties():
            if mark in ('V-A', 'V-F'):
                self.assertGreaterEqual(z, rim+6.0/12-1e-9)

    def test_the_head_vent_tied_back_into_stack_a_fails_the_build(self):
        from src import drainage as dr
        keep = list(dr.DRY_VENTS)
        try:
            dr.DRY_VENTS[:] = [d._replace(ties_into='A') if d.mark == 'V-E' else d for d in keep]
            v = dr.vent_violations()
            self.assertTrue(any("head vent does not go through the roof" in x for x in v), v)
            self.assertTrue(any("does not reach the roof itself" in x for x in v), v)
        finally:
            dr.DRY_VENTS[:] = keep


class Bath2WeirTests(unittest.TestCase):
    """OPC 909.2 on Bath 2: both lavatory traps stand over the Level 2 floor and the branch
       runs inside it, so the branch cannot be their vent. Each has one in the partition
       behind it. Nothing measured this before 2026-09-20 -- the model held no weir at all."""

    def test_the_group_passes_909_2_as_drawn(self):
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        self.assertEqual(V.weir_violations(d.bath2_weirs()), [])
        self.assertEqual([w.name for w in d.bath2_weirs()],
                         ['UNIT 1 L2 LAV', 'UNIT 1 L2 LAV 2', 'UNIT 1 L2 WC', 'UNIT 1 L2 TUB'])

    def test_each_lavatory_has_its_own_vent_above_its_weir(self):
        """The vent connects under the weir only by the fall of its own trap arm, which is what
           909.2 permits -- not by the depth of the floor it stands on."""
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        self.assertEqual(d.BATH2_VENTS, {0: 'V-E', 1: 'V-F'})
        for w in d.bath2_weirs():
            if w.kind != 'lav':
                continue
            self.assertGreater(w.vent_at, 0.0, '%s is vented from under its own floor' % w.name)
            self.assertLessEqual(w.weir-w.vent_at, V.weir_fall_max(w.size)+1e-9, w.name)

    def test_venting_the_near_lavatory_off_the_branch_fails_the_build(self):
        """The arrangement the set carried until 2026-09-20: the near lavatory dropping into the
           branch with the branch as its vent. Its PLAN trap arm is inches long, so Table 909.1
           passed it and every oracle was green. Only 909.2 can see it, and now does."""
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        keep = dict(d.BATH2_VENTS)
        d.BATH2_VENTS.pop(1)
        try:
            v = V.weir_violations(d.bath2_weirs())
            self.assertEqual(len(v), 1, v)
            self.assertIn('LAV 2', v[0])
            self.assertIn('909.2', v[0])
            self.assertTrue(any('909.2' in x for x in d.vent_violations()))
            arms = [a for _b, _m, a in d.trap_arm_rows() if a.name.endswith('LAV 2')]
            self.assertEqual(len(arms), 1)
            self.assertEqual(V.trap_arm_violations(arms), [])
        finally:
            d.BATH2_VENTS.clear()
            d.BATH2_VENTS.update(keep)

    def test_the_closet_and_the_tub_are_vented_by_the_branch(self):
        """Their bend or trap hangs in the floor and is set to the branch, so the section does
           not measure them: the closet is excepted outright and the tub carries no weir."""
        from src import drainage as d
        from arkitect.codes.ohio import opc_vents as V
        for w in d.bath2_weirs():
            if w.kind in ('wc', 'tub'):
                self.assertLess(w.vent_at, 0.0)
                self.assertEqual(V.weir_violations([w]), [])

    def test_the_branch_crown_falls_from_the_head_to_the_stack(self):
        from src import drainage as d
        total = sum(l for _s, l in d.floor_branch_sections())
        self.assertAlmostEqual(d.floor_branch_crown(0.0), d.levels.SUBFLOOR+d.BRANCH_TOP)
        self.assertGreater(d.floor_branch_crown(total), d.floor_branch_crown(0.0))
        for a in range(0, int(total)):
            self.assertLessEqual(d.floor_branch_crown(a), d.floor_branch_crown(a+1))


if __name__ == '__main__':
    unittest.main()
