"""The interior vapor retarder of the exterior frame walls, RCO 702.7.

   Climate zone 5 takes a Class I or II vapor retarder on the interior side of frame
   walls. Both exterior frame walls in the set — W1 and W1R — take one Class II
   product: a vapor retarder primer on the interior gypsum. It is the one retarder that
   serves them both: in W1R it adds no layer between the studs and the 5/8" Type X of
   UL U305. A-601 prints it in each row and in a note, A-602 in the energy table;
   check_vapor_retarder() holds the rows to it.

   It also carries what each of those walls stands OUTSIDE its studs, which is what a
   yard and a fire separation distance are measured to (RCO 202) and what every
   dimension on the set is not (G-001 note 5, face of stud)."""
from lib.units import IN
from codes.ohio.rco.bracing import GYP_SHEATHING_T, SHEATHING_T

CLIMATE_ZONE = 5                   # G-001 'Climate zone 5A'; A-602's energy table

# RCO 702.7: Class I or II on the interior side of frame walls in these zones.
VR_ZONES = (5, 6, 7, 8)
VR_REQUIRED = ('I', 'II')

# Vapour retarder class by its permeance, ASTM E96 Procedure A (desiccant): (above, not over).
VR_CLASS_PERMS = {'I': (0.0, 0.1), 'II': (0.1, 1.0), 'III': (1.0, 10.0)}

VR_CLASS = 'II'
VR_PERM = 1.0                        # the primer's rating, not over
VR_MATERIAL = 'VAPOR RETARDER PRIMER'

# Every exterior frame wall type on A-601; A-001 note 2 names them.
EXTERIOR_FRAME_WALLS = ('W1', 'W1R')


def vr_layer():
    """The layer as each wall row ends: the interior finish's last item."""
    return 'CLASS %s %s' % (VR_CLASS, VR_MATERIAL)


def perm_text():
    return '%.1f PERM' % VR_PERM


def check_vapor_retarder():
    """RCO 702.7 against the model: the product's rating is its class, and the class is
       one the climate zone accepts. Prints one line."""
    lo, hi = VR_CLASS_PERMS[VR_CLASS]
    assert lo < VR_PERM <= hi, "a %s perm product is not Class %s" % (VR_PERM, VR_CLASS)
    if CLIMATE_ZONE in VR_ZONES:
        assert VR_CLASS in VR_REQUIRED, \
            "RCO 702.7: climate zone %d frame walls need Class I or II, not Class %s" % (CLIMATE_ZONE, VR_CLASS)
    print("VAPOR RETARDER  climate zone %d, RCO 702.7: Class %s, %s max, interior of %s"
          % (CLIMATE_ZONE, VR_CLASS, perm_text(), ' / '.join(EXTERIOR_FRAME_WALLS)))


def check_wall_rows(assemblies):
    """A-601's rows as {type: assembly}: every exterior frame wall ends with the layer."""
    for t in EXTERIOR_FRAME_WALLS:
        assert t in assemblies, "A-601 has no %s row" % t
        assert assemblies[t].endswith(' / ' + vr_layer()), \
            "A-601's %s row does not end with its vapor retarder, RCO 702.7" % t


# ---------------- what each exterior wall carries OUTSIDE its studs ----------------
# A yard and a fire separation distance are both measured to the outside face of the
# wall (RCO 202), and every dimension on this set is to the face of the stud (G-001
# note 5). The difference is this build-up, and until it was written down nothing in
# either model knew the two faces were not the same place.
#
# The layers are A-601's, in its order, outside the studs. The sheathing thicknesses are
# the ones codes/ohio/rco/bracing.py already nails through, so a wall cannot be sheathed
# one way for bracing and another way for a setback.
#
# CLADDING_T is the set's own allowance and is the agent's call, unconfirmed by the designer: the
# vinyl siding A-601 schedules carries no thickness, and a standard profile stands about
# 3/4" off the sheathing at the butt. It is used only to MEASURE A YARD, where a figure
# that is too large is the safe direction, so an over-estimate cannot make a wall pass.
CLADDING_T = IN(0.75)                # vinyl siding over the WRB, butt to sheathing

# Outside the stud face, by wall type. W1R adds UL U305's exterior Type X gypsum under
# the OSB, so it stands a further 5/8" into its yard than W1 does.
BUILD_OUT = {'W1':  SHEATHING_T+CLADDING_T,
             'W1R': GYP_SHEATHING_T+SHEATHING_T+CLADDING_T}


def build_out(wall):
    """The assembly's thickness outside the face of the stud, for a wall type on A-601."""
    assert wall in BUILD_OUT, 'no exterior build-out recorded for wall type %r' % wall
    return BUILD_OUT[wall]
