"""UL Design No. U305, the 1-hour bearing wood-stud wall projects build on.

One project's unit separation is two of these back to back and another's rated exterior wall
is one, so the design's own conditions belong here rather than in any project. Read from UL Product iQ's text of the design dated
May 09, 2025 (BXUV.U305, profile e=14888), transcribed item by item -- not from a summary of
it, and not from a supplier's description of it.

WHAT THIS MODULE IS FOR. A drawing can name a material that the listing does not carry, and
nothing on the sheet will contradict it: the wall is still 2x6, the board is still 5/8" Type X,
the rating still prints 1 HOUR. That is what happened here (a plan reviewer, 2026-09-21):

    "Identify the applicable UL U305 foam option and matching gypsum installation
     requirements. U305 does permit particular spray foams, but ties them to specific board
     and fastening provisions. Generic 'closed-cell spray polyurethane foam' does not identify
     that combination."

He is right, and the tie is the point. EVERY foamed plastic in U305 is "For use with" one
gypsum board item, and each of those items is an alternate to Item 3 that changes how the
board is applied and fastened over the WHOLE wall -- vertically, joints centered on studs and
staggered one cavity side to side, particular screws, and for one option two layers. Choosing a
foam to insulate a single stud bay re-specifies the gypsum everywhere.

Item 5 does not tie to anything, and it permits a PARTIAL fill in as many words. That is why a
batt is the right thing to put behind a pipe in a rated cavity and a foam is not.

THE ATTACHMENT IS PART OF THE LISTING TOO. The board is fastened to the STUDS (Items 3, 3A) or
to steel furring channels or resilient channels (Items 6, 6A to 6H, 7). There is no wood
furring item. Furring a bay out in wood and hanging the board on that is not this design.
"""
from collections import namedtuple

DESIGN = 'UL DESIGN U305'
READ = 'UL Product iQ, design dated May 09, 2025'
BEARING_WALL_RATING = '1 HR'

# Item 1, verbatim. A project using a deeper stud is taking the larger-than-listed-studs
# allowance of Guide BXUV, which is a general allowance and not part of this design's text.
STUDS = 'Nom 2 by 4 in. spaced 16 in. OC max, effectively firestopped.'
STUD_NOMINAL = '2x4'
STUD_OC_MAX_IN = 16.0

# What may attach the gypsum board. Wood furring is deliberately absent: it is absent from the
# design.
BOARD_TO_STUDS = ('3', '3A')
BOARD_TO_STEEL = ('6', '6A', '6B', '6C', '6D', '6E', '6F', '6G', '6H', '7')

# A cavity insulation option: the item, what it is, whether the design lets it PARTIALLY fill
# the cavity, the board item it is tied to (None where it is tied to none), and the design's
# own words for the condition.
Fill = namedtuple('Fill', 'item material partial board_item condition')

CAVITY_FILLS = {
    '5': Fill('5', 'GLASS FIBER OR MINERAL WOOL', True, None,
              'Glass fiber or mineral wool insulation. Placed to completely or partially fill '
              'the stud cavities.'),
    '5A': Fill('5A', 'SPRAY APPLIED CELLULOSE', False, None,
               'The fiber is applied with water to completely fill the enclosed cavity.'),
    '5B': Fill('5B', 'SPRAY APPLIED CELLULOSE', False, None,
               'Applied to completely fill the enclosed cavity.'),
    '5F': Fill('5F', 'SPRAY APPLIED GRANULATED MINERAL FIBER', False, None,
               'Applied with adhesive, at a minimum density of 4.0 pcf, to completely fill the '
               'enclosed cavity.'),
    '5G': Fill('5G', 'SPRAY APPLIED CELLULOSE FIBER', False, None,
               'Applied with water to completely fill the enclosed stud cavity.'),
    '5H': Fill('5H', 'SPRAY APPLIED FOAMED PLASTIC', True, '3R',
               'Optional - For use with Item 3R. Spray applied, foamed plastic insulation, at '
               'any thickness from partial fill to completely filling stud cavity.'),
    '5J': Fill('5J', 'SPRAY APPLIED FOAMED PLASTIC', True, '3U',
               'Optional, Not Shown - For use with Item 3U.'),
    '5K': Fill('5K', 'SPRAY APPLIED FOAMED PLASTIC', True, '3V',
               'Optional, Not Shown - For use with Item 3V.'),
    '5L': Fill('5L', 'SPRAY APPLIED FOAMED PLASTIC', True, '3W',
               'Optional, Not Shown - For use with Item 3W.'),
    '5M': Fill('5M', 'SPRAY APPLIED FOAMED PLASTIC', True, '3X',
               'Optional, Not Shown - For use with Item 3X.'),
}

# The board items the foamed plastics tie to, and what each one changes about the board. Every
# one of them is "As an alternate to Item 3", so it governs the whole wall, not one bay.
BOARD_ITEMS = {
    '3': '5/8 in. thick, nailed 7 in. OC with 6d cement coated nails 1-7/8 in. long.',
    '3A': '5/8 in. thick, 1-1/4 in. long Type W coarse thread screws spaced a max 8 in. OC.',
    '3R': 'For use with Item 5H. 1-5/8 in. long Type W screws at 8 in. OC, as the base layer.',
    '3U': 'For use with Item 5J. Applied VERTICALLY, vertical joints centered over studs and '
          'staggered one stud cavity on opposite sides, nailed 7 in. OC with 6d nails.',
    '3V': 'For use with Item 5K. Applied VERTICALLY, joints centered over studs and staggered '
          'one stud cavity on opposite sides, 1-5/8 in. Type W screws at 8 in. OC.',
    '3W': 'For use with Item 5L. Applied VERTICALLY, joints centered over studs and staggered '
          'one stud cavity on opposite sides, 1-1/4 in. Type W screws at 8 in. OC.',
    '3X': 'For use with Item 5M. TWO LAYERS applied vertically, joints staggered, inner layer '
          '1-1/4 in. and outer layer 1-7/8 in. Type W screws at 8 in. OC.',
}

# Item 5's mineral wool makers and types, for a project that schedules one.
MINERAL_WOOL = ('ROCKWOOL Type AFB or Acoustical Fire Batts (min. density 1.69 pcf)',
                'THERMAFIBER / OWENS CORNING Type SAFB or SAFB FF',
                'ROCK WOOL MANUFACTURING CO Delta Board')


def partial_fill_items():
    """The items whose own text lets the cavity be filled only part way. A pipe in a cavity
       leaves room for nothing else, so this is the shortlist for one."""
    return tuple(sorted(k for k, f in CAVITY_FILLS.items() if f.partial))


def untied_items():
    """The items that carry no board condition -- the ones that can be chosen for one bay
       without re-specifying the gypsum on the whole wall."""
    return tuple(sorted(k for k, f in CAVITY_FILLS.items() if f.board_item is None))


def fill_violations(fills):
    """Each (name, fill item, board item in use, partial fill?) against the design.

       Three ways a cavity fill leaves U305, and a drawing shows none of them: naming a
       material the design does not carry, filling part of a cavity with something the design
       only lists at a complete fill, and naming a foam without the board item it is tied to."""
    v = []
    for name, item, board, partial in fills:
        f = CAVITY_FILLS.get(item)
        if f is None:
            v.append('%s: %s has no cavity insulation Item %s; %s'
                     % (name, DESIGN, item, ', '.join(sorted(CAVITY_FILLS))))
            continue
        if partial and not f.partial:
            v.append('%s: %s Item %s is listed only at a complete fill -- "%s"'
                     % (name, DESIGN, item, f.condition))
        if f.board_item is not None and board != f.board_item:
            v.append('%s: %s Item %s is for use with board Item %s, and this wall is board '
                     'Item %s. That board item is an alternate to Item 3 and governs the whole '
                     'wall: %s' % (name, DESIGN, item, f.board_item, board,
                                   BOARD_ITEMS.get(f.board_item, '')))
    return v


def board_attachment_violations(walls):
    """Each (name, how the board is attached) against the design. `how` is the item claimed.

       There is no wood furring item in U305. A bay furred out in wood with the board hung on
       the furring is not this design, however ordinary the detail looks."""
    ok = BOARD_TO_STUDS+BOARD_TO_STEEL
    return ['%s: the board is attached by "%s", which is no item of %s; it attaches to the '
            'studs (%s) or to steel members (%s)'
            % (name, how, DESIGN, ', '.join(BOARD_TO_STUDS), ', '.join(BOARD_TO_STEEL))
            for name, how in walls if how not in ok]
