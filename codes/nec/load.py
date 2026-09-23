"""NEC 2023 Article 220, the load on a dwelling and on the service that carries it, and the
feeders from a meter bank.

    nec220_82()               220.82, the optional method for one dwelling unit
    service_load_standard()   220 Part III
    service_load_220_82/84/85 the optional method a service of one, three to five, or two
                              dwellings takes
    service_loads()           (standard, optional, governing, service rating)
    feeders()                 each meter position's feeder, then the service conductors

`units` are rows of (name, floor area SF, range VA, dryer VA, dishwasher VA, water heater
VA, heat pump VA at MCA, panel A); a service is a dict with `units`, `house_va`,
`positions` [(position, rating A, name)] and `mark`. The two projects' copies had drifted
— one had no single-dwelling service, the other no house feeder — and this is their union.
"""
from codes.nec.dwelling import STD_RATINGS, WIRE_AMPS, egc_min


def nec220_82(area, rng, dry, dw, wh, hp):
    """NEC 220.82 optional method, one dwelling unit. Floor area from outside dimensions."""
    gen = 3.0*area                   # 220.82(B)(1), 3 VA per square foot
    sa = 2*1500                      # 220.82(B)(2), two small-appliance circuits
    ldy = 1500                       # 220.82(B)(2), laundry
    sub = gen+sa+ldy+rng+dry+dw+wh   # 220.82(B)(3), the fastened-in-place appliances
    rem = 0.4*max(sub-10000.0, 0.0)  # 220.82(B): first 10 kVA at 100 %, the rest at 40 %
    return dict(gen=gen, sa=sa, ldy=ldy, rng=rng, dry=dry, dw=dw, wh=wh, sub=sub,
                first=min(sub, 10000.0), rem=rem, hp=hp,
                tot=min(sub, 10000.0)+rem+hp, amps=(min(sub, 10000.0)+rem+hp)/240.0)


def _demand_220_45(va):
    """Table 220.45, dwelling units: the first 3 kVA at 100 %, the next 117 kVA at 35 %."""
    return min(va, 3000.0) + 0.35*min(max(va-3000.0, 0.0), 117000.0) + 0.25*max(va-120000.0, 0.0)


RANGES_220_55_C = {0: 0, 1: 8000, 2: 11000, 3: 14000, 4: 17000, 5: 20000}   # 12 kW or less


def service_load_standard(units, house_va):
    """NEC 220 Part III, 2023 numbering, for a service carrying `units` (rows of NEC_UNITS)."""
    ltg = sum(3.0*u[1] + 3000 + 1500 for u in units)       # 220.41 general lighting, 220.52 small appliance and laundry
    d = dict(lighting=_demand_220_45(ltg))
    d['ranges'] = RANGES_220_55_C[len([u for u in units if u[2]])]         # Table 220.55 column C
    d['dryers'] = sum(max(u[3], 5000) for u in units)                     # 220.54, four or fewer at 100 %
    # 220.53: the fastened-in-place appliances other than ranges, dryers and the space
    # conditioning of 220.60 — the dishwashers and the storage water heaters. Four or more
    # of them on one service take 75 %.
    fixed = [u[4] for u in units if u[4]] + [u[5] for u in units if u[5]]
    d['appliances'] = sum(fixed) * (0.75 if len(fixed) >= 4 else 1.0)     # 220.53
    d['hvac'] = sum(u[6] for u in units)                                  # 220.60, the heat pumps at MCA
    d['motor'] = 0.25*max(u[6] for u in units)                            # 220.50, the largest motor
    d['house'] = house_va
    d['va'] = sum(d[k] for k in ('lighting', 'ranges', 'dryers', 'appliances', 'hvac', 'motor', 'house'))
    d['amps'] = d['va']/240.0
    d['method'] = 'NEC 220 PART III'
    return d


def _connected_220_84(u):
    return 3.0*u[1] + 3000 + 1500 + u[2] + u[3] + u[4] + u[5] + u[6]


def service_load_220_82(units, house_va):
    """One dwelling unit: the optional method of 220.82 is the service's."""
    assert len(units) == 1
    r = nec220_82(*units[0][1:7])
    return dict(va=r['tot']+house_va, amps=(r['tot']+house_va)/240.0, method='NEC 220.82')


def service_load_220_84(units, house_va):
    """The multifamily optional method: three to five units at 45 % of the connected load,
       the house load by Part III added."""
    assert 3 <= len(units) <= 5
    va = 0.45*sum(_connected_220_84(u) for u in units) + house_va
    return dict(va=va, amps=va/240.0, method='NEC 220.84, %d UNITS AT 45 %%' % len(units))


def service_load_220_85(units, house_va):
    """Two units on one service: 220.84 as if three identical units, the larger unit taken."""
    assert len(units) == 2
    big = max(units, key=_connected_220_84)
    va = 0.45*3*_connected_220_84(big) + house_va
    return dict(va=va, amps=va/240.0, method='NEC 220.85 (TWO UNITS: 220.84 FOR THREE UNITS EACH EQUAL TO THE LARGER, AT 45 %)')


def service_size(amps):
    """The standard rating at or above the load, 240.6(A)."""
    for r in STD_RATINGS:
        if r >= amps-1e-9: return r
    raise ValueError('no standard rating carries %.0f A' % amps)


OPTIONAL_METHOD = {1: service_load_220_82, 2: service_load_220_85}     # three to five: 220.84


def service_loads(s):
    """(standard, optional, governing, service rating). A one-dwelling service is never
       smaller than the panel it feeds, nor than 230.79(C)'s 100 A."""
    std = service_load_standard(s['units'], s['house_va'])
    opt = OPTIONAL_METHOD.get(len(s['units']), service_load_220_84)(s['units'], s['house_va'])
    gov = opt if opt['va'] < std['va'] else std
    size = service_size(gov['amps'])
    if len(s['units']) == 1:
        size = max(size, s['positions'][0][1], 100)
    return std, opt, gov, size


# Table 310.12(A): a feeder to an individual dwelling unit at 83 % of its rating, copper.
UNIT_FEEDER_310_12 = {100: '#4', 125: '#2', 150: '#1', 175: '#1/0', 200: '#2/0'}
GEC_CEE = '#4'      # 250.66(B): to a concrete-encased electrode, no larger than #4 Cu is required


def _by_310_16(amps):
    """The smallest copper conductor of Table 310.16, 75 °C, at or above the load."""
    for w, a in sorted(WIRE_AMPS.items(), key=lambda kv: kv[1]):
        if a >= amps: return w
    raise ValueError(amps)


def feeders(s):
    """(position, name, ocpd, conductor, wires, neutral, egc) per meter position, then the
       service-entrance conductors last. A unit's feeder (position 'U…') takes 310.12(B); a house
       feeder and the service conductors do not qualify and take Table 310.16 at 100 %."""
    out = []
    for pos, a, name in s['positions']:
        wire = UNIT_FEEDER_310_12[a] if pos.startswith('U') else _by_310_16(a)
        out.append((pos, name, a, wire, 4, 'ISOLATED FROM GROUND AT THE PANEL', egc_min(a)))
    size = service_loads(s)[3]
    out.append(('SERVICE', s['mark'], size, _by_310_16(size), 3, 'BONDED AT THE SERVICE DISCONNECT', '—'))
    return out
