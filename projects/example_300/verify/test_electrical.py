"""The electrical model: the 220.82 table, the device symbols, the checker and the units."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _has(violations, *needles):
    return any(all(n in v for n in needles) for v in violations)


class Nec220_82Tests(unittest.TestCase):

    def test_the_table_and_the_method_give_p601s_figures(self):
        """The three amperes P-601 prints now that every dwelling heats its water
           electrically: 107, 93, 92, on the panels the set already had."""
        from src.electrical import NEC_UNITS, WH_VA
        from codes.nec.load import nec220_82
        got = {nm: round(nec220_82(a, r, d, w, wh, h)['amps']) for nm, a, r, d, w, wh, h, p in NEC_UNITS}
        self.assertEqual(got, {"UNIT 1": 107, "UNITS 2 / 3": 93, "UNITS 4 / 5": 92})
        self.assertEqual([p for *_r, p in NEC_UNITS], [125, 100, 100])
        self.assertEqual([u[5] for u in NEC_UNITS], [WH_VA]*3)

    def test_the_heater_is_an_other_load_not_space_heating(self):
        """4,500 VA belongs in 220.82(B)(3) with the fastened-in-place appliances. Put
           in (C) instead it would ride at 100 % and Unit 1 would pass its 125 A panel."""
        from src.electrical import NEC_UNITS, WH_VA
        from codes.nec.load import nec220_82
        u = NEC_UNITS[0]
        with_wh = nec220_82(*u[1:7])
        without = nec220_82(u[1], u[2], u[3], u[4], 0, u[6])
        self.assertAlmostEqual(with_wh['sub']-without['sub'], WH_VA, places=6)
        self.assertAlmostEqual(with_wh['tot']-without['tot'], 0.4*WH_VA, places=6)

    def test_the_panels_have_room_for_the_new_circuit(self):
        """The water heater added a 2-pole circuit to every dwelling. Unit 1 needs 24
           spaces, not the 20 the other four take."""
        from src.electrical import CIRCUITS_U1, CIRCUITS_U23, CIRCUITS_U45
        from codes.nec.dwelling import PANEL_MIN, panel_spaces
        self.assertEqual(panel_spaces(CIRCUITS_U1), (22, 24))
        self.assertEqual(panel_spaces(CIRCUITS_U23), (18, 20))
        self.assertEqual(panel_spaces(CIRCUITS_U45), (17, 20))
        self.assertEqual(PANEL_MIN, 20)

    def test_every_dwelling_has_one_water_heater_circuit(self):
        from src.electrical import CIRCUITS_U1, CIRCUITS_U23, CIRCUITS_U45
        for ckts in (CIRCUITS_U1, CIRCUITS_U23, CIRCUITS_U45):
            wh = [c for c in ckts if c.kind == 'wh']
            self.assertEqual(len(wh), 1)
            self.assertEqual((wh[0].amps, wh[0].poles, wh[0].wire), (30, 2, '#10'))
            self.assertEqual(wh[0].desc, 'WATER HEATER')
            # 210.12 is a 120 V 15/20 A rule and 210.8(A), as RCO 3401.1 modifies it, a 125 V
            # 15/20 A receptacle rule: a hardwired 2-pole 30 A circuit takes neither.
            self.assertEqual(wh[0].prot, '—')


class RealUnitsTests(unittest.TestCase):
    """The authored lists against the model's own rooms: a moved wall fails here."""

    def test_units_2_3_pass(self):
        from src import electrical as e
        from codes.nec import dwelling as nec_dwelling
        self.assertEqual(nec_dwelling.check_unit(e.UNIT_23), [])

    def test_units_4_5_pass(self):
        from src import electrical as e
        from codes.nec import dwelling as nec_dwelling
        self.assertEqual(nec_dwelling.check_unit(e.UNIT_45), [])

    def test_unit_1_passes_on_both_levels(self):
        from src import electrical as e
        from codes.nec import dwelling as nec_dwelling
        self.assertEqual(nec_dwelling.check_unit(e.UNIT_1), [])
        # the stair is switched from both levels, and its Level 2 switch is in the hall list
        self.assertEqual(sum(1 for lv in e.UNIT_1.levels for d in lv.devices if d.kind == 'sw3' and d.tag == 'S'), 2)
        # nothing on the W4 line but chase-face devices
        from src.building1 import Y_SEP_TOP
        on_w4 = [d for lv in e.UNIT_1.levels for d in lv.devices if abs(d.y-Y_SEP_TOP) < 0.05]
        self.assertTrue(on_w4 and all(d.mount == 'w5s' for d in on_w4))

    def test_the_house_lists_pass_and_carry_only_exterior_devices(self):
        from src import electrical as e
        from codes.nec import dwelling as nec_dwelling
        for h in (e.HOUSE_1, e.HOUSE_2):
            self.assertEqual(nec_dwelling.check_unit(h), [])
            self.assertEqual({d.kind for lv in h.levels for d in lv.devices}, {'ext', 'wp'})
        bad = nec_dwelling.UnitType('H', 60, [nec_dwelling.Level('H', e.E_HOUSE_1+[nec_dwelling.dev(1, 1, 'dup', 'n', 'H2')])], e.CIRCUITS_HOUSE)
        self.assertTrue(_has(nec_dwelling.check_unit(bad), 'house list'))

    def test_the_services(self):
        from src import electrical as e
        from codes.nec import load as nec_load
        b1, b2 = e.SERVICES
        std, opt, gov, size = nec_load.service_loads(b1)
        # by hand: lighting 3*(1248+624+624)+3*4500 = 20988 -> 3000+0.35*17988 = 9295.8; three ranges 14000;
        # dryers 15000; three dishwashers and three water heaters is SIX appliances, so
        # 220.53's 75 % applies where it did not before: (3600+13500)*0.75 = 12825;
        # heat pumps 16800; 25 % of the largest 1800; house 1500
        self.assertAlmostEqual(std['va'], 9295.8+14000+15000+12825+16800+1800+1500, places=1)
        self.assertAlmostEqual(opt['va'], 0.45*(38144+2*33872)+1500, places=1)
        self.assertIs(gov, opt); self.assertEqual(size, 225)
        # two water heaters is under four, so Building 2's stay at 100 %
        std, opt, gov, size = nec_load.service_loads(b2)
        self.assertAlmostEqual(std['va'], (3000+0.35*(13368-3000))+11000+10000+9000+9600+1200+1500, places=1)
        self.assertAlmostEqual(opt['va'], 0.45*3*32984+1500, places=1)
        self.assertIs(gov, opt); self.assertEqual(size, 200)
        self.assertIn('EMERGENCY', b2['marking']); self.assertNotIn('EMERGENCY', b1['marking'])
        self.assertEqual(nec_load.service_size(179.5), 200); self.assertEqual(nec_load.service_size(200), 200)
        f1 = nec_load.feeders(b1)
        # the service entrance grew with the service: 200 A #3/0 -> 225 A #4/0
        self.assertEqual([(p, w) for p, _n, _a, w, *_r in f1], [('U1', '#2'), ('U2', '#4'), ('U3', '#4'), ('H', '#6'), ('SERVICE', '#4/0')])
        self.assertEqual([r[4] for r in f1], [4, 4, 4, 4, 3])
        self.assertEqual([r[6] for r in f1], ['#6', '#8', '#8', '#10', '—'])
        self.assertEqual(nec_load.feeders(b2)[-1][3], '#3/0')       # 175 A #2/0 -> 200 A #3/0
        self.assertEqual(nec_load.GEC_CEE, '#4')
        self.assertEqual(e.check_services(), [])

    def test_no_heat_pump_range_or_dryer_circuit_carries_gfci(self):
        """The designer, 2026-09-19: Ohio's minimum. RCO 3401.1 adds 210.8(F) Exception No. 2 for listed
           HVAC equipment and narrows 210.8(A) to 125 V 15/20 A receptacles."""
        from src import electrical as e
        from codes.nec import dwelling as nec_dwelling
        hps = [c for cks in (e.CIRCUITS_U1, e.CIRCUITS_U23, e.CIRCUITS_U45) for c in cks if c.kind == 'hp']
        self.assertEqual(len(hps), 3)
        self.assertEqual([c.prot for c in hps], ['—']*3)
        for cks in (e.CIRCUITS_U1, e.CIRCUITS_U23, e.CIRCUITS_U45):
            self.assertEqual([c.prot for c in cks if c.kind in ('range', 'dryer')], ['—', '—'])
        self.assertNotIn('range', nec_dwelling.PROTECT); self.assertNotIn('dryer', nec_dwelling.PROTECT)

    def test_note_4_asks_no_gfci_breaker_and_no_compatibility_submittal(self):
        from src.sheets.e_common import NOTES
        n4 = NOTES[3]
        self.assertTrue(n4.startswith('4.  HEAT PUMPS'), n4)
        self.assertIn('2-POLE BREAKER AT THE NAMEPLATE MOCP', n4)
        self.assertNotIn('GFCI', n4)
        self.assertIn('210.8 AS RCO 3401.1 MODIFIES THEM', NOTES[1])
        self.assertNotIn('RANGE AND DRYER', NOTES[1])
        for arguing in ('OHIO MINIMUM', 'EXCEPTION', 'EXCEED', 'NOT REQUIRED'):   # AEP OHIO is the utility
            self.assertNotIn(arguing, ' '.join(NOTES))

    def test_the_walk_is_live_on_the_real_rooms(self):
        """Take one receptacle away from each unit type and the walk says so."""
        from src import electrical as e
        from codes.nec import dwelling as nec_dwelling
        for ut, gone in ((e.UNIT_23, (0.5, 42.0)), (e.UNIT_45, (0.5, 12.0))):
            lv = ut.levels[-1]
            kept = [d for d in lv.devices if not (d.x == gone[0] and d.y == gone[1] and d.kind == 'dup')]
            self.assertEqual(len(kept), len(lv.devices)-1)
            lv2 = nec_dwelling.Level(lv.name, kept, lv.rooms, lv.polys, lv.doors, lv.ext_req, lv.counters,
                          lv.dividers, lv.kitchens, lv.lavs, lv.wds, lv.sinks, lv.sep_y)
            v = nec_dwelling.check_unit(nec_dwelling.UnitType(ut.name, ut.panel_a, [lv2], ut.circuits, ut.stacked))
            self.assertTrue(_has(v, '210.52(A)'), v)


if __name__ == "__main__":
    unittest.main()
