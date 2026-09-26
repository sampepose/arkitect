"""The records a sheet is drawn from: one level of a building, and its geometry."""


# ---------------- one level of one building, as a plan sheet needs it ----------------
class PlanLevel:
    """Everything a plan sheet draws for one level of one building.

    plan_sheet used to take twenty-six parameters, which is what happens when a call
    site has to assemble a whole level out of loose names: the two Building 1 calls
    passed eighteen arguments each, twelve of them identical, and nothing checked that
    the pair stayed in step. A level is one thing, so it is one object, built by the
    module that owns the building and handed to the sheet that draws it.

    THE MODEL, which the building owns:
        plan            the regrid that maps model coordinates to the sheet
        W, D            the building's overall size in plan feet
        rooms           room rectangles, punched white out of the poche
        openareas       polygons for the spaces that are not rectangles
        doors, wins     the level's opening lists, shared with the elevations
        openings        cased openings and bypass closet fronts
        furn            fittings and appliances
        joists          span arrows
        sep             y of the unit separation, where the plan splits
        sep_rows        the rows that wall draws as, from sep: solid, open, solid ... (feet)

    THE ANNOTATION, which the sheet adds:
        dims            overall dimension lines
        chains          interior dimension strings
        fixed_chains    strings authored in final sheet coordinates, not regridded
        notes, tags     text on the plan, and the wall-type tags
        units           the unit identification boxes
        ctx             the four context strings around the plan

    DIMENSION COVERAGE:
        full_dims       closet depths, bypass-leaf widths and the RCO 307.1 water
                        closet dimension, as well as room overalls. Building 1's
                        levels take all four; Building 2's take room overalls only.
                        That is a GAP, not a decision — Units 4 and 5 have two closets
                        and a water closet like everyone else — but it is what the
                        issued set shows, so it is a field rather than a silent
                        difference between two code paths.
        wall_finish     the thickness of the finish on a stud face, for the ONE
                        dimension RCO 307.1 measures to a finished surface rather than
                        to the stud faces every other string on the plan runs between.
                        The project supplies it, as it supplies `captions`.
    THE DRAWN EXTRAS, which are neither:
    THE PROJECT'S OWN DRAWING, at the three moments where it has to happen. Each is a
    callable taking the PlanDraw, and each moment exists for a reason:

        over_plan       after the room labels, before any annotation. Anything drawn
                        here is under the dimension strings — which is where a stair
                        belongs, because a stair drawn after them gets their label
                        masks cut into it.
        captions        the two caption lines each clearance kind prints; supplied by
                        the project because the citation belongs to a jurisdiction.
        over_dims       after the dimension strings, before the notes. For drawing
                        that must NOT be masked by the strings and must not be
                        covered by the notes.
        over_all        last thing on the sheet, over the title block's own drawing.
        overlay         a callable taking the PlanDraw, or None. When set, the level is
                        drawn as the BACKGROUND of a trade plan: the plan and the
                        over_dims hook in grey, no dimension strings, chains, notes,
                        joist arrows or tags; then this runs with the real pen and draws
                        the trade's work on it.
        labels_last     with an overlay: the rooms' grey captions drawn again after it,
                        each line on a white ground, so a trade line crossing a room
                        cannot strike its name or size.
        marks_last      the window marks drawn after everything else on the plan (the
                        overlay included), each on a white ground, so a stair tread,
                        a fixture or a trade line cannot strike one.
        room_dim_skip   room names whose overall strings room_dims() leaves out, beyond its
                        defaults (a bath whose tag already prints its size).
        closet_dims     with full_dims: the closet depth strings. False leaves each
                        closet's size to its room tag, where the string would print
                        on another line (a soffit's edge).
        net_wording     room name -> what its net area label says was deducted
                        (net_areas()), for a room whose notch is not a closet alone.
                        None: every net figure says NET OF CLOSET.

        stair_side      how far to shift the REAR context label clear of an exterior
                        stair that runs past the rear wall, in plan feet. 0 if nothing
                        does.
        pos             an explicit page position
    """

    def __init__(s, plan, W, D, rooms, doors, wins, openings, dims, notes,
                 openareas=None, furn=None, joists=(), sep=None, chains=(),
                 fixed_chains=(), tags=None, units=None, ctx=None,
                 pos=None, full_dims=True, wall_finish=0.0,
                 over_plan=None, over_dims=None, over_all=None, stair_side=0.0,
                 overlay=None, captions=None, sep_rows=None, labels_last=False,
                 marks_last=False, closet_dims=True, room_dim_skip=(),
                 net_wording=None):
        s.plan, s.W, s.D = plan, W, D
        s.rooms, s.openareas = rooms, openareas
        s.doors, s.wins, s.openings, s.furn = doors, wins, openings, furn
        s.joists, s.sep, s.sep_rows = joists, sep, sep_rows
        s.dims, s.chains, s.fixed_chains = dims, chains, fixed_chains
        s.notes, s.tags, s.units, s.ctx = notes, tags, units, ctx
        s.pos = pos
        s.full_dims = full_dims
        s.wall_finish = wall_finish
        s.over_plan, s.over_dims, s.over_all = over_plan, over_dims, over_all
        s.stair_side = stair_side
        s.overlay = overlay
        s.captions = captions
        s.labels_last = labels_last
        s.marks_last = marks_last
        s.closet_dims = closet_dims
        s.room_dim_skip = tuple(room_dim_skip)
        s.net_wording = dict(net_wording or {})


# ---------------- the geometry, and which coordinate space it is in ----------------
class Geometry:
    """The twelve lists a plan is drawn from, and which space their numbers are in.

    A level's geometry passes through three spaces on its way to a sheet, and the same
    twelve names mean something different in each:

        'model'   as authored — plan feet on the building's own grid
        'regrid'  moved onto the stud-to-stud 1/8 in grid
        'sheet'   mirrored, so the side street is on the left of the page

    This exists because the two transforms used to exchange bare 11-tuples, in two
    different orders — chains was position 10 leaving the regrid and position 8 entering
    the mirror — and nothing checked. Getting one wrong does not raise: rooms and
    openareas are both lists of tuples, so swapping them draws the rooms as poche holes
    and the open areas as rooms. Fields are keyword-only for the same reason.

    `space` is not decoration. mirrored() refuses geometry that has not been regridded,
    which is the assertion that would have caught a reordering.
    """
    FIELDS = ('rooms','openareas','doors','wins','openings',
              'dims','notes','tags','furn','chains','joists')

    def __init__(s, *, space, **kw):
        s.space = space
        for f in s.FIELDS:
            setattr(s, f, kw.pop(f, None))
        assert not kw, "Geometry got fields it does not carry: %s" % sorted(kw)

    def replace(s, *, space=None, **kw):
        """A copy with some fields changed. Unknown field names raise rather than land
           silently in the wrong slot."""
        bad = set(kw) - set(s.FIELDS)
        assert not bad, "no such geometry field: %s" % sorted(bad)
        out = {f: getattr(s, f) for f in s.FIELDS}
        out.update(kw)
        return Geometry(space=space or s.space, **out)

    @classmethod
    def from_level(cls, lv):
        """The level as authored. openareas and furn may be None on a level that has
           none; the regrid wants empty lists, so they are normalized here."""
        return cls(space='model',
                   rooms=lv.rooms, openareas=lv.openareas or [], doors=lv.doors,
                   wins=lv.wins, openings=lv.openings, dims=lv.dims, notes=lv.notes,
                   tags=lv.tags, furn=lv.furn or [],
                   chains=lv.chains, joists=lv.joists)

    def regridded(s, plan, regrid_all):
        """Onto the stud-to-stud grid. Joists are mapped by the caller, before this, so
           that their stated span is the clear distance between the MAPPED faces."""
        assert s.space == 'model', "already regridded: %s" % s.space
        (rooms, openareas, doors, wins, openings, dims, notes, tags,
         furn, chains) = regrid_all(
            plan, s.rooms, s.openareas, s.doors, s.wins, s.openings,
            s.dims, s.notes, s.tags, s.furn, s.chains)
        return s.replace(space='regrid', rooms=rooms, openareas=openareas, doors=doors,
                         wins=wins, openings=openings, dims=dims, notes=notes, tags=tags,
                         furn=furn, chains=chains)

    def mirrored(s, W, mirror_everything):
        """Onto the page. Refuses model geometry, because a mirror applied to unregridded
           coordinates lands everything at its pre-framing position."""
        assert s.space == 'regrid', "mirror wants regridded geometry, got %s" % s.space
        (rooms, openareas, doors, wins, openings, dims, notes, tags,
         chains, joists) = mirror_everything(
            W, s.rooms, s.openareas, s.doors, s.wins, s.openings, s.dims,
            s.notes, s.tags, s.chains, s.joists)
        return s.replace(space='sheet', rooms=rooms, openareas=openareas, doors=doors,
                         wins=wins, openings=openings, dims=dims, notes=notes, tags=tags,
                         chains=chains, joists=joists)
