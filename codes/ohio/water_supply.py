"""Sizing a water supply in Ohio: OPC Table 604.5 and IPC Appendix E.

Ohio adopts IPC chapters 2 to 15 by reference and not the appendices; Appendix E's Tables
E103.3(2) and E201.1 are the accepted engineering practice OPC 604.1 asks for. One
transcription for every project, pinned by codes/verify/test_water_supply.py.

    WSFU, BATH_GROUP   Table E103.3(2), private occupancy: (cold, hot, total)
    MIN_SUPPLY         Table 604.5, minimum fixture supply
    E201_1, LENGTHS    Table E201.1 by static pressure range and developed length
    row_for()          the first row that carries a load: (meter, pipe)
"""
# ================================ the tables ================================
# Table E103.3(2), LOAD VALUES ASSIGNED TO FIXTURES, private occupancy: (cold, hot, total)
# water supply fixture units. Transcribed from the table's text and pinned by
# lib/verify/test_plumbing.py; never retype them from a summary.
WSFU = {
    'tub':  (1.0, 1.0, 1.4),      # bathtub, faucet
    'shower': (1.0, 1.0, 1.4),    # shower head
    'lav':  (0.5, 0.5, 0.7),      # lavatory, faucet
    'wc':   (2.2, 0.0, 2.2),      # water closet, flush tank
    'sink': (1.0, 1.0, 1.4),      # kitchen sink, faucet
    'dw':   (0.0, 1.4, 1.4),      # dishwashing machine, automatic
    'wd':   (1.0, 1.0, 1.4),      # washing machine, 8 lb, automatic
}
BATH_GROUP = (2.7, 1.5, 3.6)      # bathroom group, flush tank: a wc, a lav and a tub or a shower together
FIXTURE_KINDS = tuple(WSFU)       # what the tally counts
SUPPLY_KINDS = FIXTURE_KINDS+('wh',)   # what a home run reaches: the fixtures and the heater

# Table 604.5, minimum size of the fixture supply, inches; every home run here is 1/2".
MIN_SUPPLY = {'lav': '3/8', 'wc': '3/8', 'tub': '1/2', 'shower': '1/2', 'sink': '1/2', 'dw': '1/2', 'wd': '1/2'}
PIPES = ('3/8', '1/2', '3/4', '1', '1-1/4', '1-1/2', '2')

# Table E201.1, MINIMUM SIZE OF WATER METERS, MAINS AND DISTRIBUTION PIPING BASED ON
# WATER SUPPLY FIXTURE UNIT VALUES: (meter and service, distribution pipe, the maximum
# WSFU at each maximum developed length). The rows the buildings can use; the larger
# meters are not transcribed. Minimum size for building supply is 3/4-inch pipe.
LENGTHS = (40, 60, 80, 100, 150, 200, 250, 300, 400, 500)
E201_1 = {
    '40 TO 49': [
        ('3/4', '1/2',   (3, 2.5, 2, 1.5, 1.5, 1, 1, 0.5, 0.5, 0.5)),
        ('3/4', '3/4',   (9.5, 9.5, 8.5, 7, 5.5, 4.5, 3.5, 3, 2.5, 2)),
        ('3/4', '1',     (32, 32, 32, 26, 18, 13.5, 10.5, 9, 7.5, 6)),
        ('1',   '1',     (32, 32, 32, 32, 21, 15, 11.5, 9.5, 7.5, 6.5)),
        ('3/4', '1-1/4', (32, 32, 32, 32, 32, 32, 32, 27, 21, 16.5)),
        ('1',   '1-1/4', (80, 80, 80, 80, 65, 52, 42, 35, 26, 20)),
    ],
    '50 TO 60': [
        ('3/4', '1/2',   (3, 3, 2.5, 2, 1.5, 1, 1, 1, 0.5, 0.5)),
        ('3/4', '3/4',   (9.5, 9.5, 9.5, 8.5, 6.5, 5, 4.5, 4, 3, 2.5)),
        ('3/4', '1',     (32, 32, 32, 32, 25, 18.5, 14.5, 12, 9.5, 8)),
        ('1',   '1',     (32, 32, 32, 32, 30, 22, 16.5, 13, 10, 8)),
        ('3/4', '1-1/4', (32, 32, 32, 32, 32, 32, 32, 32, 29, 24)),
        ('1',   '1-1/4', (80, 80, 80, 80, 80, 68, 57, 48, 35, 28)),
    ],
    'OVER 60': [
        ('3/4', '1/2',   (3, 3, 3, 2.5, 2, 1.5, 1.5, 1, 1, 0.5)),
        ('3/4', '3/4',   (9.5, 9.5, 9.5, 9.5, 7.5, 6, 5, 4.5, 3.5, 3)),
        ('3/4', '1',     (32, 32, 32, 32, 32, 24, 19.5, 15.5, 11.5, 9.5)),
        ('1',   '1',     (32, 32, 32, 32, 32, 28, 28, 17, 12, 9.5)),
        ('3/4', '1-1/4', (32, 32, 32, 32, 32, 32, 32, 32, 32, 30)),
        ('1',   '1-1/4', (80, 80, 80, 80, 80, 80, 69, 60, 46, 36)),
    ],
}


def pipe_size(v):
    return PIPES.index(v)


def _column(length_ft):
    for i, L in enumerate(LENGTHS):
        if length_ft <= L: return i
    raise ValueError('developed length %.0f ft is off Table E201.1' % length_ft)


def row_for(wsfu, length_ft, pressure, meter=None):
    """The first Table E201.1 row that carries `wsfu` at `length_ft`: the smallest
       meter, then the smallest pipe. With `meter` given, the smallest pipe on that
       meter — a branch is sized on the building's meter, not its own. `pressure` is a key of
       E201_1, the static pressure range at the main."""
    col = _column(length_ft)
    rows = E201_1[pressure]
    for m, pipe, maxima in rows:
        if meter is not None and m != meter: continue
        if maxima[col] >= wsfu: return m, pipe
    raise ValueError('no transcribed Table E201.1 row carries %.1f WSFU at %.0f ft' % (wsfu, length_ft))
