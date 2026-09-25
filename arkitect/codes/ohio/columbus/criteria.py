"""RCO Table 301.2(1) for Columbus: the design criteria, once, as numbers -- the jurisdiction's,
so every set here reads the same figures and a set in another city reads its own.

G-001 prints this table and half a dozen other sheets act on it. Before this module the
figures were typed wherever they were needed: the wind speed in `src/bracing.py`, again
in `src/roof.py` and twice more on G-001; the ground snow load in `src/framing.py` and
again on G-001; the presumed soil bearing in three places and in no model constant at
all, so `check_basis()` -- the one function whose job is Table 403.1(1) -- had nothing to
assert it against.

What made that worse than ordinary duplication is that the wind speed is LOAD-BEARING,
not a caption. The bracing tables in `src/bracing.py` are transcribed from the Vult <=
115 mph, Exposure B column of Table R602.10.3(1) and R602.10.6.4. If the authority having
jurisdiction ever asks for 120, editing G-001's two lines leaves those tables quietly
answering the old question, and the braced-wall lengths printed on S-104 would be the
ones for a building that is not this one. `bracing.py` asserts the column still applies.

Nothing here imports a project, so any project module may import this one.
"""
import math


# Wind, RCO Table 301.2(1). Vult is the ULTIMATE design speed. Its nominal (ASD) speed is RCO
# Table 301.2.1.3's, Vult x sqrt(0.6) rounded, which reproduces every row of the adopted table
# (OAC 4101:8-3-01): 115 mph is 89. CIC-09's 90 mph is the old map's basic speed, not this.
WIND_VULT = 115                  # mph, ultimate
WIND_VASD = int(round(WIND_VULT*math.sqrt(0.6)))     # mph, nominal, Table 301.2.1.3
WIND_EXPOSURE = 'B'              # built-up residential streets on all sides
WIND_EXPOSURE_BASIS = 'BUILT-UP RESIDENTIAL STREETS ON ALL SIDES'

# The one spelling of the wind criterion that the sheets print.
WIND = '%d MPH ULTIMATE, EXPOSURE %s' % (WIND_VULT, WIND_EXPOSURE)

# Snow. The truss designer reads this off S-102 and S-103.
GROUND_SNOW = 20                 # psf

# Winter. Table 301.2(1) gives Franklin County a RANGE, and G-001 prints the range; OPC
# 903.2's frost closure needs a single 97.5-percent value, so the set takes the cold end.
# At 0 F the rule binds and every roof vent is at least 3", which is why the risers show an
# increaser. Pinning a warmer value -- Columbus's 97.5-percent figure is usually quoted
# above 0 F -- would let the 2" stacks go through the roof at 2" and is UNCONFIRMED.
WINTER_DESIGN_LO = 0             # F, the cold end of the table's range: what 903.2 is tested at
WINTER_DESIGN_HI = 10            # F
WINTER_DESIGN = '%d TO %d F' % (WINTER_DESIGN_LO, WINTER_DESIGN_HI)

# Frost. The bottom of a footing below finished grade: CIC-09 and RCO R403.1.4.1.
FROST_DEPTH = 32                 # inches

# Radon. EPA Map of Radon Zones, Franklin County: zone 1, the highest potential, which is why
# a set here shows the passive sub-slab system of IRC Appendix F.
RADON_ZONE = 1

# Soil. Presumed, verified at excavation -- S-101 note 9 says so on the drawing.
# Table 403.1(1)'s footing widths are selected for this value.
SOIL_BEARING = 1500              # psf


def psf(n):
    """1500 -> '1,500 PSF'. The sheets print thousands with a comma."""
    return '%s PSF' % format(n, ',')
