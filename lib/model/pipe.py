"""What a pipe actually measures across, as opposed to what it is called.

A nominal size is a name, not a dimension, and the two differ by enough to matter once a
drawing dimensions concrete around a pipe: a "1-1/2 inch" Sch 40 PVC sleeve is 1.900 in
across, not 1.5, so cover taken off the nominal size is 0.2 in optimistic top and bottom.
That is exactly the error a review found in the water service entry's footing cover.

Two families, and a size means different things in each:

  CTS  copper tube size -- copper water tube to ASTM B88 and PEX to ASTM F876 -- where the
       outside diameter is the nominal size plus 1/8 in, by definition of the series. It is
       derived here rather than tabulated because that IS the rule: 1 in CTS is 1.125 in.
  IPS  iron pipe size -- Sch 40 PVC to ASTM D1785, and the DWV sizes of D2665 -- where the
       outside diameter is tabulated and follows no formula.

Feet out, as everything in the model is feet. Nothing here cites a code section: an outside
diameter is a product dimension, so it sits in lib/ and not in codes/.
"""
from lib.units import IN
from lib.model.drains import _nominal

# Iron pipe size, Sch 40, ASTM D1785 -- outside diameters in INCHES, transcribed, not
# derived. Read them; do not retype them from a summary.
IPS_OD_IN = {'1/2': 0.840, '3/4': 1.050, '1': 1.315, '1-1/4': 1.660, '1-1/2': 1.900,
             '2': 2.375, '2-1/2': 2.875, '3': 3.500, '4': 4.500}

CTS_OVER_NOMINAL = IN(0.125)      # the copper tube series: OD is the name plus 1/8 in

# A FITTING IS NOT A PIPE, which is the same mistake as a nominal size not being a dimension,
# one level up. A hub stands proud of the pipe it receives all round, so the widest thing in a
# wall on a DWV line is never the straight run: at a washer connection it is the sanitary tee.
# A cavity, a bored plate or a chase has to clear THAT.
#
# UNSOURCED, and deliberately generous. ASTM D3311 gives the DWV fitting patterns and D2665
# the pipe; neither is in hand here, and published hub diameters vary between makers. So this
# is an ALLOWANCE the set builds to, not a transcribed dimension -- over-estimating is the
# safe direction for a clearance, the same call CLADDING_T makes for a yard. Where a
# fabricated dimension matters, take it from the fitting actually submitted.
SOCKET_OVER_PIPE = IN(0.5)        # how far a hub stands proud of the pipe it receives, EACH SIDE


def fitting_od(size, series='IPS', socket=SOCKET_OVER_PIPE):
    """The outside diameter a FITTING on this pipe measures across, in feet: the pipe plus one
       hub each side. This is the figure a clearance is taken from, not od()."""
    return od(size, series)+2*socket


def od(size, series):
    """A pipe's outside diameter in FEET. `series` is 'CTS' or 'IPS'."""
    if series == 'CTS':
        return IN(_nominal(size))+CTS_OVER_NOMINAL
    if series == 'IPS':
        assert size in IPS_OD_IN, 'no Sch 40 outside diameter for a %r pipe' % (size,)
        return IN(IPS_OD_IN[size])
    raise AssertionError('unknown pipe series %r: CTS or IPS' % (series,))
