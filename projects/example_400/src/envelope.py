"""The interior vapor retarder of the exterior frame walls, RCO 702.7.

   Climate zone 5 takes a Class I or II vapor retarder on the interior side of frame
   walls. Both exterior frame walls in the set — W1 and W1R — take one Class II
   product: a vapor retarder primer on the interior gypsum. It is the one retarder that
   serves them both: in W1R it adds no layer between the studs and the 5/8" Type X of
   UL U305. A-601 prints it in each row and in a note, A-602 in the energy table;
   check_vapor_retarder() holds the rows to it.

   It also holds what FILLS those cavities, because one of them has a drain standing in it
   and the batt the schedule names does not fit behind it."""
from arkitect.codes import ul_u305 as u305
from arkitect.lib.model import fit
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.lib.units import IN, inches

CLIMATE_ZONE = 5                     # G-001 'Climate zone 5A'; A-602's energy table

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

# ---------------- what fills the cavity, and the ONE bay a drain stands in ----------------
# The assembly schedule fills these walls with a batt as deep as the cavity. Stack F stands
# in one of those cavities (P-601 note 1aa), and a 3" DWV pipe is 3-1/2" across, so that bay
# has 2" left and the batt the schedule names is 5-1/2" thick. The two drawings each looked
# right alone and no code table is broken by either, which is why this went unseen: only the
# ROOM says so. `arkitect/lib/model/fit.py`'s cavity_violations() is the check, and the bay below is
# what A-601 prints beside the W1 / W1R rows so the section and the schedule agree.
STUD_CAVITY = EXT_STUD               # 2x6, stud face to stud face -- the grid's, not a copy
STUD_OC = IN(16)                     # what the W1 / W1R rows print, and what a bay is wide
STUD_T = IN(1.5)                     # a stud, flat dimension
CAVITY_BATT = IN(5.5)                # the scheduled batt: the whole cavity
CAVITY_BATT_R = 21
# THE BAY IS PART OF A RATED WALL, so what fills it and what carries its board are the
# listing's business, not the drafter's. `arkitect/codes/ul_u305.py` has the design; two things follow
# from it and neither is obvious from a sheet:
#
#   * the fill is a BATT, Item 5, the one cavity option that both permits a PARTIAL fill and
#     ties to no board item. Every foamed plastic in U305 is "for use with" a particular board
#     item, and each of those is an alternate to Item 3 that re-specifies how the gypsum is
#     applied and fastened over the WHOLE wall. Insulating one bay is not worth that.
#   * the bay is DEEPER FRAMING, not furring. U305 attaches its board to the studs or to steel
#     members; it has no wood furring item, so a bay furred out in wood with the board on the
#     furring is not the design.
STACK_BAY_FILL = IN(2.0)             # what goes behind a stack instead, in that bay only
STACK_BAY_FILL_ITEM = '5'            # UL U305's cavity insulation item
STACK_BAY_MATERIAL = 'MINERAL WOOL BATT'
STACK_BAY_R = 8                      # the least installed R that 2" is scheduled to give
STACK_BAY_STUD = '2x8'               # the bay's own studs, deeper than the wall's 2x6
BOARD_ITEM = '3A'                    # how W1R's gypsum is fastened: screws to the studs


def stack_bay_depth():
    """The deepened bay's whole depth: its own studs, not the wall's."""
    return fit.lumber_depth(STACK_BAY_STUD)


def stack_bay_projection():
    """How far that bay stands proud of the wall's interior face, INTO THE ROOM. A-102 draws
       and dimensions it, A-601 sections it, P-601 note 1aa names it: one figure, derived from
       the stud, so the plans and the detail cannot drift apart."""
    return stack_bay_depth()-STUD_CAVITY


def stack_bay_clear_width():
    """The insulated width of that bay: one stud spacing less one stud."""
    return STUD_OC-STUD_T


def stack_bay_area(height):
    """The wall area standing at the bay's reduced R, over a wall `height` tall -- the clear
       cavity between its studs. This is the figure the energy documentation carries, so it is
       derived here and A-602 prints it rather than a drafter estimating one."""
    return stack_bay_clear_width()*height


def stack_bay_text():
    """The sentence A-601 prints so its schedule and the stack-bay section do not disagree."""
    return ('IN THE ONE BAY A DRAIN STANDS IN, IN PLACE OF THE BATT: %s MINIMUM %s, R-%d '
            'MINIMUM INSTALLED, FRICTION-FITTED AGAINST THE SHEATHING — %s ITEM %s. THAT BAY '
            'IS FRAMED %s, GYPSUM ON THE STUDS, ITEM %s'
            % (inches(STACK_BAY_FILL), STACK_BAY_MATERIAL, STACK_BAY_R, u305.DESIGN,
               STACK_BAY_FILL_ITEM, STACK_BAY_STUD, BOARD_ITEM))


def stack_bay_fills():
    """What `u305.fill_violations()` measures: the bay's fill, the board item this wall uses,
       and that it is a PARTIAL fill."""
    return [('W1R STACK BAY', STACK_BAY_FILL_ITEM, BOARD_ITEM, True)]


def check_stack_bay(plan_violations=()):
    """The bay a drain stands in, against the listing it stands inside — and against the ROOM
       it stands in, which is what `plan_violations` carries: the caller passes the plan's own
       findings (`building2.stack_bay_violations()`) because a deepened wall is a plan fact as
       much as a section one, and this module cannot import the plan without a cycle.
       Prints one line."""
    v = u305.fill_violations(stack_bay_fills())
    v += u305.board_attachment_violations([('W1R', BOARD_ITEM)])
    v += list(plan_violations)
    assert not v, '; '.join(v)
    f = u305.CAVITY_FILLS[STACK_BAY_FILL_ITEM]
    print('W1R STACK BAY  %s Item %s, %s: "%s" R-%d min at %s, board Item %s'
          % (u305.DESIGN, STACK_BAY_FILL_ITEM, f.material, f.condition, STACK_BAY_R,
             inches(STACK_BAY_FILL), BOARD_ITEM))


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
