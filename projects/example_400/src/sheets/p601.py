"""P-601 — the plumbing riser diagram and plumbing notes. The risers are read from
   src/drainage.py: each stack's branch intervals, and beside them the slab-drained
   fixtures that vent into it. The drainage fixture units and everything below the slabs
   are P-101's; the water supply is P-102 / P-103's."""
from arkitect.lib.draw.page import LAY, Sheet
from arkitect.lib.draw.text import wrap_notes
from arkitect.lib.units import IN, fmt, inches
from arkitect.codes.ohio.opc_drainage import SIZE_IN
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from arkitect.codes.ohio import opc_vents as VENT
from arkitect.codes.ohio.opc_service_entry import entry_for
from arkitect.codes.ohio.opc_service_entry_draw import (service_entry_elevation, service_entry_notes,
                                               service_entry_section)
from arkitect.codes.ohio import opc_vents_draw as DRAW
from src import criteria as crit
from src import drainage as dr
from src import envelope
from src import levels as LV
from src.foundation import (BAR_COVER, EDGE_INSUL_RUN, FTG_BAR, FTG_BAR_DIA,
                            FTG_PROJ, FTG_W, GRAVEL_T, INSUL_T, SLAB_T, WALL_T)
from src.building1 import CHASE
from src import plumbing as pm
from arkitect.lib.draw.kit import X0, X1, Y0, Y1, c

FIX = {'sink': 'KITCHEN SINK', 'wc': 'WC', 'tub': 'TUB', 'shower': 'SHOWER', 'lav': 'LAV', 'wd': 'WASHER STANDPIPE'}
WHAT = {(1, 'A'): "UNIT 1 BATH 2", (1, 'B'): "UNIT 1 BATH 1 DRY VENT",
        (2, 'D'): "UNITS 2 / 3 BATH", (2, 'E'): "UNITS 2 / 3 KITCHEN SINKS", (2, 'F'): "UNITS 2 / 3 LAUNDRY"}
# What vents what, in the words the riser prints. Each is a different arrangement with its
# own requirements, which is why each is drawn its own way: arkitect/codes/ohio/opc_vents.py.
VERTICAL = 'VERTICAL WET VENT, 912.1.1'
HORIZONTAL = 'HORIZONTAL WET VENT, 912.1'
# How far the isometric carries a pipe that leaves the drawing: it runs off at a break, so
# nothing on it reads as a height the model does not hold.
VENT_UP = 1.15                     # ft, each lavatory's vent above its takeoff
STACK_DOWN = 1.35                  # ft, stack A below the branch
NOTE_W = 12.4                      # in: the plumbing notes' column, the isometric taking the rest
SCHED, SCHED_FOOT, SCHED_LEAD = 7.0, 6.6, 0.132   # the trap schedule: readable in the field


INDIVIDUAL = 'INDIVIDUAL VENT'
WASTE = 'WASTE STACK VENT, 913'


def _fmt_size(n):
    return ('%g' % n) if n != int(n) else '%d' % n


def _height(z):
    """A connection's height over its level's finished floor, as the riser prints it."""
    return '%s %s THE FLOOR' % (inches(abs(z)), 'OVER' if z >= -1e-9 else 'UNDER')


def _units_at(b, cell_stack, level):
    """The dwellings this cell draws at a level: the riser's level line names them."""
    out = []
    for st in b.stacks:
        if st.name != cell_stack:
            continue
        out += [u for u, l, _ks in st.serves if l == level]
    for dv in dr.DRY_VENTS:
        if dv.building == b.number and (dv.ties_into == cell_stack
                                        or (dv.ties_into is None and dv.mark[-1] == cell_stack)):
            out += [u for u, l, _ks in dv.serves if l == level]
    return sorted(set(out))


def _hangs(b, st):
    """Every group hanging on a stack, lowest connection first: 912.1.1's vertical wet vent,
       or the two waste stacks, where the stack itself is the vent, 913."""
    waste = st.name in dr.WASTE_STACKS
    if st.name in dr.FLOOR_BRANCHES:              # its group drains into its top through a floor
        return []
    by_level = {}
    for unit, level, conn in dr._conns_on(st):
        by_level.setdefault(level, []).append((unit, conn))
    out = []
    for level in sorted(by_level):
        rows = sorted(by_level[level], key=lambda uc: uc[1].at)
        fixes = [DRAW.Fix(FIX[cn.kind], _height(cn.at-LV.FLOOR_RISE*(level-1))) for _u, cn in rows]
        method = ''
        if not waste:
            method = VERTICAL
        elif level == min(by_level):
            method = WASTE
        out.append(DRAW.Hang(level, method, fixes))
    return out


def _slabs(b, name):
    """The branches below the slab that this riser vents, each with the dry vent standing in
       it: 912.1's wet vent where it takes a whole group, an individual vent where it takes
       one fixture. `tie` is None where the riser drawn in this cell IS that vent."""
    wet = {g[0].split()[-1]: g for g in dr.horizontal_wet_groups()}
    out = []
    for dv in dr.DRY_VENTS:
        if dv.building != b.number:
            continue
        if dv.ties_into != name and not (dv.ties_into is None and dv.mark[-1] == name):
            continue
        if dv.mark in dr.FLOOR_VENTS:             # a Level 2 vent, drawn in its floor by _floors()
            continue
        group = wet.get(dv.mark)
        if group is not None:
            fixes = [DRAW.Fix(FIX[cn.kind], '') for cn in group[1]]
            method = HORIZONTAL
        else:
            fixes = [DRAW.Fix(FIX[k], '') for _u, _l, ks in dv.serves for k in ks]
            method = INDIVIDUAL
        tie = ('TIES IN %s OVER THE RIM, 905.4' % inches(VENT.DRY_VENT_RISE)
               if dv.ties_into else None)
        out.append(DRAW.Slab(dv.mark, dv.size+'"', method, fixes, tie))
    return out


def _floors(b, name):
    """A group that drains horizontally through a floor into this stack's top: Bath 2, 912.1."""
    if name not in dr.FLOOR_BRANCHES:
        return ()
    mark, _unit, level = dr.FLOOR_BRANCHES[name]
    dv = next(d for d in dr.DRY_VENTS if d.mark == mark)
    group = next(g for g in dr.horizontal_wet_groups() if g[0].split()[-1] == mark)
    # a fixture whose trap stands ON this floor carries its own vent: the lavatories, 909.2
    vents = {}
    for i, vm in dr.BATH2_VENTS.items():
        v = next(d for d in dr.DRY_VENTS if d.mark == vm)
        vents[i] = (v.mark, v.size+'"')
    fixes = [DRAW.Fix(FIX[cn.kind], '', vents.get(i)) for i, cn in enumerate(group[1])]
    return (DRAW.Floor(level, mark, dv.size+'"', HORIZONTAL+', IN THE FLOOR', fixes,
                       'TIES INTO STACK %s IN THE ATTIC, 905.4' % name),)


def _branch_pt(d):
    """The plan point d feet along the Bath 2 branch, in the direction of flow."""
    pts = dr.BATH2_BRANCH
    run = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = abs(b[0]-a[0])+abs(b[1]-a[1])
        if d <= run+seg+1e-9:
            t = 0.0 if seg <= 0 else (d-run)/seg
            return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
        run += seg
    return pts[-1]


def _branch_size(d):
    """The nominal size the branch is in, d feet along it."""
    run = 0.0
    last = 2.0
    for size, length in dr.floor_branch_sections():
        last = float(SIZE_IN[size])
        run += length
        if d <= run+1e-9:
            return last
    return last


def bath2_isometric(x, y, w, h):
    """Bath 2's drain, waste and vent in three dimensions, projected from the model's own feet.

       A plan cannot show a vent takeoff's HEIGHT and a riser cannot show where a fixture
       stands, and the fact this group turns on is both at once: each lavatory trap stands
       over the Level 2 floor while the branch that serves it runs INSIDE that floor, so the
       branch is the vent of the closet and the tub and cannot be the vent of either lavatory
       (OPC 909.2). Drawn, that is one look; written, it took a paragraph and was wrong."""
    def zb(d):                       # the branch's crown at d, under the FINISHED floor
        return -(LV.FLOOR_FINISH+dr.floor_branch_crown(d))

    along = dr._branch_along
    ends = [along(p) for p in dr.BATH2_BRANCH]
    conns = [along(at) for _k, at, _s in dr.BATH2_CONNS]
    segs, nodes, labels = [], [], []
    # ---- the branch itself, cut at every vertex and every connection so the size changes
    events = sorted(set([round(v, 9) for v in ends+conns]))
    for d0, d1 in zip(events, events[1:]):
        a = _branch_pt(d0)+(zb(d0),)
        b = _branch_pt(d1)+(zb(d1),)
        segs.append(DRAW.ISeg(a, b, _branch_size((d0+d1)/2.0), 'drain'))
    # ---- each fixture: its trap where it stands, its arm, its fitting and its vent
    vent_tops = []
    for i, k, name, trap, to, at in dr._bath2_legs():
        d = along(at)
        zc = zb(d)
        if i in dr.BATH2_VENTS:                       # a lavatory: its trap stands ON the floor
            dv = next(v for v in dr.DRY_VENTS if v.mark == dr.BATH2_VENTS[i])
            weir = VENT.TRAP_WEIR[k]
            arm = abs(trap[0]-to[0])+abs(trap[1]-to[1])
            tee = weir-arm*VENT.TRAP_ARM[dr.TRAP_SIZE[k]][0]/12.0
            size = dr.TRAP_SIZE[k]
            segs.append(DRAW.ISeg(trap+(weir,), to+(tee,), size, 'drain'))          # the trap arm
            segs.append(DRAW.ISeg(to+(tee,), to+(zc,), size, 'drain'))              # and its drop
            segs.append(DRAW.ISeg(to+(tee,), to+(tee+VENT_UP,), float(SIZE_IN[dv.size]), 'vent'))
            if abs(to[0]-at[0]) > 1e-9 or abs(to[1]-at[1]) > 1e-9:                  # a leg to the branch
                segs.append(DRAW.ISeg(to+(zc,), at+(zc,), size, 'drain'))
                nodes.append(DRAW.INode(at+(zc,), 'wye', 'WYE AND 1/8 BEND', 'd'))
            else:
                # the head's own turn into the branch: the caption names it, because at this
                # scale its point sits under the next lavatory's trap
                nodes.append(DRAW.INode(at+(zc,), 'bend', '', 'r'))
            # the label on the far side of the trap from its vent, which it would otherwise cross
            away = 'r' if (trap[0]-trap[1]) > (to[0]-to[1]) else 'l'
            nodes.append(DRAW.INode(trap+(weir,), 'trap', '%s, ARM %s' % (name, fmt(arm)), away))
            nodes.append(DRAW.INode(to+(tee,), 'tee', '%s %s" SAN TEE' % (dv.mark, dv.size), 'r'))
            vent_tops.append(to+(tee+VENT_UP,))
        elif k == 'wc':                               # its bend hangs in the floor; 909.2 excepts it
            segs.append(DRAW.ISeg(trap+(0.0,), at+(zc,), dr.TRAP_SIZE[k], 'drain'))
            nodes.append(DRAW.INode(trap+(0.0,), 'bend', 'WC — FLANGE ON THE SUBFLOOR', 'u'))
            nodes.append(DRAW.INode(at+(zc,), 'wye', 'CLOSET BEND, WYE', 'r'))
        else:                                         # a tub: its trap is set to the branch
            zt = zc+IN(3.0)
            segs.append(DRAW.ISeg(trap+(0.0,), trap+(zt,), dr.TRAP_SIZE[k], 'drain'))
            segs.append(DRAW.ISeg(trap+(zt,), at+(zc,), dr.TRAP_SIZE[k], 'drain'))
            nodes.append(DRAW.INode(trap+(zt,), 'trap', 'TUB — TRAP IN THE FLOOR', 'l'))
            nodes.append(DRAW.INode(at+(zc,), 'wye', 'WYE AND 1/8 BEND', 'd'))
    # ---- stack A down, and the two vents up
    end = events[-1]
    foot = _branch_pt(end)+(zb(end)-STACK_DOWN,)
    segs.append(DRAW.ISeg(_branch_pt(end)+(zb(end),), foot, _branch_size(end), 'drain'))
    nodes.append(DRAW.INode(foot, 'break', 'STACK A %s" TO THE BUILDING DRAIN, P-101'
                            % _fmt_size(_branch_size(end)), 'l'))
    for p in vent_tops:
        nodes.append(DRAW.INode(p, 'break', '', 'u'))
    labels.append(DRAW.ILabel(vent_tops[0], 'TO STACK A\'S VENT IN THE ATTIC, 905.4', 'r', True))
    # ---- the figures a trade builds to: on the pipe where they are short, under it where
    # they are not. A long string at a point lands wherever the projection puts it.
    secs = dr.floor_branch_sections()
    two = sum(l for z, l in secs if z == '2')
    three = sum(l for z, l in secs if z == '3')
    mid2 = (conns[1]+conns[2])/2.0
    labels.append(DRAW.ILabel(_branch_pt(mid2)+(zb(mid2),), '2" AT 1/4"/FT, %s' % fmt(two), 'l'))
    mid3 = (conns[2]+conns[3])/2.0
    labels.append(DRAW.ILabel(_branch_pt(mid3)+(zb(mid3),), '3" AT 1/8"/FT, %s' % fmt(three), 'd'))
    # This drawing is the GOVERNING DETAIL for how Bath 2's traps are vented, so the caption
    # says what is drawn and nothing else: the rule is note 1y's and P-102 and note 1a cite
    # here rather than explaining it a third and fourth time.
    caption = [
        "THE BRANCH VENTS THE CLOSET AND THE TUB, WHOSE TRAPS HANG IN THIS FLOOR. EACH LAVATORY TRAP STANDS ON IT",
        "AND TAKES ITS OWN DRY VENT OFF A SAN TEE ABOVE ITS WEIR — NOTE 1y. THE HEAD TURNS INTO THE BRANCH ON A LONG",
        "1/4 BEND. THE CROWN IS %s UNDER THE SUBFLOOR AT THE HEAD, TIGHT TO THE TOP CHORD, AND THE BOTTOM %s UNDER"
        % (inches(LV.SUBFLOOR+dr.BRANCH_TOP), inches(dr.floor_branch_bottom())),
        "IT AT STACK A: %s OF THE %s THE CHORDS LEAVE, S-102."
        % (inches(dr.floor_branch_bottom()-LV.SUBFLOOR-dr.BRANCH_TOP), inches(dr.web_clear())),
    ]
    return DRAW.isometric(x, y, w, h, segs, nodes, labels,
                          "ISOMETRIC — BATH 2, UNIT 1 LEVEL 2: DRAIN, WASTE AND VENT",
                          "NOT TO SCALE  ·  ENLARGED PLAN ON P-102  ·  NOTES 1a AND 1x",
                          caption=caption)


def risers():
    """One Cell per stack, built from src/drainage.py: what hangs on it and at what height,
       what drains below the slab beside it, which arrangement vents each, and -- for the two
       waste stacks -- the span 913.2 allows no offset in."""
    out = []
    for b in dr.BUILDINGS:
        for st in b.stacks:
            waste = st.name in dr.WASTE_STACKS
            levels = {}
            for lv in (1, 2):
                who = _units_at(b, st.name, lv)
                levels[lv] = 'LEVEL %d%s' % (lv, ' — '+', '.join(who) if len(who) == 1 else '')
            # OPC 903.2: the size at the ROOF, which at this winter design temperature is
            # not the size of the pipe below it. Where they differ the increaser is drawn.
            roof = VENT.roof_size(st.size, crit.WINTER_DESIGN_LO)
            vtr = roof+'" VTR'+(' — %s" STACK VENT, 913.3' % st.size if waste else '')
            increaser = ('%s" x %s" INCREASER, NOTE 1d' % (st.size, roof)
                         if roof != st.size else '')
            note = ''
            if waste:
                foot = next(p for p in b.pens if p.mark == st.foot)
                note = ('OFFSET %s TO THE FOOT, AT THE SLAB: UNDER EVERY CONNECTION, 913.2'
                        % inches(abs(foot.pos[0]-st.pos[0])))
            out.append(DRAW.Cell(
                title='%s %s — %s' % ('VENT' if st.foot is None else 'STACK', st.name,
                                      WHAT[(b.number, st.name)]),
                size=st.size+'"', vent_only=st.foot is None, vtr=vtr, levels=levels,
                hangs=_hangs(b, st), slabs=_slabs(b, st.name),
                span='NO OFFSET, 913.2' if waste else None, note=note,
                foot='TO THE DRAIN, P-101' if st.foot is not None else '',
                increaser=increaser, floors=_floors(b, st.name)))
    return out


def _vent_notes():
    """Notes 1v to 1z: what vents what, and what each arrangement requires. Every figure is
       src/drainage.py's, and the riser above draws what each sentence describes."""
    stacks = [(b, st) for b in dr.BUILDINGS for st in b.stacks]
    vertical = ['STACK %s' % st.name for b, st in stacks
                if st.foot is not None and st.name not in dr.WASTE_STACKS and st.serves
                and st.name not in dr.FLOOR_BRANCHES]
    waste = [n for n, *_r in dr.waste_stacks()]
    wet, order = [], []
    for name, conns, head, _extras in dr.horizontal_wet_groups():
        mark = name.split()[-1]
        sizes = []
        for cn in conns:
            if not sizes or sizes[-1] != cn.size:
                sizes.append(cn.size)
        order.append('%s %s' % (mark, ', '.join(FIX[cn.kind] for cn in conns)))
        wet.append('%s %s, %d DFU' % (mark, ' THEN '.join('%g"' % z for z in sizes),
                                      sum(cn.dfu for cn in conns)))
    single = ['%s %s' % (dv.mark, ', '.join(FIX[k] for _u, _l, ks in dv.serves for k in ks))
              for dv in dr.individual_vents()]
    return [
        "1v. VENTING, OPC CHAPTER 9. BUILD EACH ARRANGEMENT AS THE RISER AND THE ISOMETRIC DRAW IT. EVERY DRY VENT "
        "RISES NOT LESS THAN %s ABOVE THE FLOOD LEVEL RIM OF THE HIGHEST FIXTURE IT VENTS BEFORE IT TURNS OR JOINS "
        "ANOTHER VENT, 905.4. TRAP ARMS: THE SCHEDULE ABOVE." % inches(VENT.DRY_VENT_RISE),
        "1w. VERTICAL WET VENT, 912.1.1 — %s, UNIT 3'S BATH. EACH FIXTURE DRAIN CONNECTS INDEPENDENTLY AT THE HEIGHT "
        "DRAWN, THE WATER CLOSET LOWEST; THE STACK CARRIED FULL SIZE OVER THE HIGHEST CONNECTION IS THAT GROUP'S DRY "
        "VENT, 912.2.2." % ' AND THE ONE ON '.join(vertical),
        "1x. HORIZONTAL WET VENT, 912.1 — %s. EACH FIXTURE DRAIN CONNECTS INDEPENDENTLY IN THE ORDER DRAWN, ONLY THE "
        "BATHROOM GROUP CONNECTS TO THAT BRANCH, AND EVERY OTHER FIXTURE DISCHARGES DOWNSTREAM OF IT. THE DRY VENT "
        "STANDS AT THE MOST UPSTREAM FIXTURE, 912.2.1. SECTIONS ARE SIZED ON THE LOAD INTO EACH, TABLE 912.3: %s."
        % (', '.join(m.split()[0] for m in order), '; '.join(wet)),
        "1y. INDIVIDUAL VENT — %s, EACH VENTED ON ITS OWN TRAP ARM. A TRAP THAT STANDS ON A FLOOR IS NOT VENTED BY A "
        "BRANCH INSIDE THAT FLOOR, 909.2: SEE THE ISOMETRIC FOR BATH 2'S TWO LAVATORIES."
        % ' AND '.join(single),
        "1z. WASTE STACK VENT, 913 — %s. NEITHER TAKES A WATER CLOSET; NEITHER OFFSETS BETWEEN ITS LOWEST AND ITS "
        "HIGHEST FIXTURE CONNECTION, 913.2; EACH CARRIES A STACK VENT "
        "OF ITS OWN SIZE THROUGH THE ROOF, 913.3; AND THE LOAD IS INSIDE TABLE 913.4 — %s."
        % ('STACKS '+' AND '.join(waste), VENT.waste_stack_text(dr.waste_stacks())),
    ]


def _trap_schedule(x, y, width):
    """TRAP ARMS: every fixture whose trap stands away from its vent, the arm as drawn and
       Table 909.1's maximum for that trap. The figures are src/drainage.py's."""
    c.setFillColor(black); c.setFont("Helvetica-Bold", 8.0)
    c.drawString(x, y, "TRAP ARMS — OPC TABLE 909.1"); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= 0.13*inch
    cols = (0.0, 0.95, 1.30, 1.66, 2.02)
    c.setFont("Helvetica-Bold", SCHED)
    for k, t in enumerate(('FIXTURE', 'TRAP', 'ARM', 'MAX', 'VENT')):
        c.drawString(x+cols[k]*inch, y, t)
    y -= SCHED_LEAD*inch
    c.setFont("Helvetica", SCHED)
    for _b, mark, a in dr.trap_arm_rows():
        nm = a.name.replace('BUILDING ', 'B').replace('UNIT ', 'U')
        for k, t in enumerate((nm, '%g"' % a.size, "%.1f'" % a.length,
                               "%.0f'" % VENT.trap_arm_max(a.size), mark)):
            c.drawString(x+cols[k]*inch, y, t)
        y -= SCHED_LEAD*inch
    c.setFont("Helvetica", SCHED_FOOT)
    c.drawString(x, y-0.02*inch, "MEASURED TRAP TO VENT, THE BRANCH")
    c.drawString(x, y-0.12*inch, "TURNING SQUARE. 905.4: EACH VENT")
    c.drawString(x, y-0.22*inch, "RISES %s OVER THE RIM IT VENTS." % inches(VENT.DRY_VENT_RISE))
    return y-0.22*inch
    return y-0.34*inch


def plumbing_notes():
    _PAN = " AND ".join(pm.WH_PAN_UNITS)
    _T1 = pm.WH_TANKS['UNIT 1']; _T2 = pm.WH_TANKS['UNITS 2 / 3']
    _WHA, _WHP, _WHW = pm.WH_CIRCUIT
    n = sum(len(b.stacks) for b in dr.BUILDINGS)
    drains = sum(1 for b in dr.BUILDINGS for s in b.stacks if s.foot is not None)
    assert (n, drains, len(dr.DRY_VENTS)) == (5, 4, 6), "P-601 note 1 counts five stacks, one a vent, and six dry vents"
    return [
     "1.  FIVE STACKS AND SIX DRY VENTS, DRAWN ABOVE. STACK A TAKES UNIT 1'S BATH 2 AND VENT B ITS BATH 1 AND ITS "
     "LAUNDRY; STACK D TAKES UNIT 3'S BATH, AND STACKS E AND F THE UNITS 2 / 3 KITCHEN SINKS AND WASHERS. UNIT 2'S "
     "BATH DRAINS BELOW THE SLAB, P-101. EACH BUILDING HAS ONE 4\" BUILDING DRAIN THROUGH ITS SOUTH WALL TO THE ONE "
     "4\" BUILDING SEWER, C-101.",
     *_vent_notes(),
     "1a. STACK A STANDS IN THE FURRED CHASE DRAWN ON A-101, %s SQUARE, AT THE FRONT END OF UNIT 1'S KITCHEN RUN, AND "
     "V-A RISES IN THE SAME CHASE BESIDE IT. BATH 2 DRAINS TO ITS TOP ON ONE BRANCH THROUGH THE FLOOR TRUSSES' OPEN "
     "WEBS, S-102 — A HORIZONTAL WET VENT, NOTE 1x. V-E STANDS IN BATH 2'S HALL PARTITION BEHIND THE FAR LAVATORY "
     "AND V-F BEHIND THE NEAR ONE; NO LAVATORY DRAIN RUNS IN A WALL AND NO CHASE IS NEEDED. THE ISOMETRIC DRAWS THE "
     "GROUP AND HOW EACH TRAP IS VENTED; P-102 DRAWS IT ENLARGED IN PLAN. ABOVE THAT FLOOR STACK A'S VENT OFFSETS "
     "INTO THAT SAME PARTITION." % inches(CHASE),
     "1aa. STACK E STANDS IN THE CHASE DRAWN ON A-102 AT THE BACK OF EACH KITCHEN COUNTER, PAST THE WINDOW OVER THE "
     "SINKS, INSIDE THAT WALL'S INSULATION AND ITS RATED MEMBRANE, A-601. STACK F, 3\" BECAUSE IT TAKES THE WASHERS "
     "(OPC 406.2), STANDS IN THE NORTH WALL'S STUD CAVITY BEHIND THE WASHERS, CLEAR OF THE DRYER DUCT (M-102), "
     "WITH THE CAVITY INSULATION BETWEEN IT AND THE SHEATHING, OPC 305.4. THAT BAY IS FRAMED %s AND PROJECTS %s "
     "INTO THE ROOM, A-102; THE STACK IS SET SO ITS FITTINGS, NOT ITS PIPE, CLEAR THE INSULATION. SEE THE SECTION "
     "ON A-601. STRAP EACH TOP PLATE IT PASSES, RCO 602.6.1. STACK D IS IN "
     "THE PARTITION BEHIND THE WATER CLOSETS AND V-D IN THE SAME WALL, BESIDE THE LAVATORY IT STANDS AT. V-B STANDS "
     "IN BATH 1'S FRONT PARTITION BESIDE THE LAVATORY AND V-C IN THE MECHANICAL ROOM'S HALL PARTITION BEHIND THE "
     "WASHER." % (envelope.STACK_BAY_STUD, inches(envelope.stack_bay_projection())),
     "1b. EVERY FLOOR IS OPEN-WEB WOOD FLOOR TRUSSES, S-102: BRANCHES, WATER LINES AND LINE SETS PASS THROUGH THE "
     "OPEN WEBS IN ANY DIRECTION. NEVER CUT, NOTCH OR DRILL A CHORD, A WEB OR A TRUSS PLATE; A TRUSS THAT HAS BEEN "
     "CUT IS REPAIRED ONLY TO THE TRUSS MANUFACTURER'S SEALED DETAIL. KEEP PIPING CLEAR OF THE BEARINGS.",
     "1c. EACH STACK OF BUILDING 2 CROSSES THE RATED F1 FLOOR-CEILING ONCE, FIRESTOPPED: A-601. UNIT 3'S TRAP ARMS "
     "AND BRANCHES ARE ABOVE THE F1 MEMBRANE, WHICH NOTHING ELSE PIERCES.",
     f"1d. VENTS THROUGH THE ROOF, LOCATED PER S-103 NOTE 9, 10'-0\" FROM OR 3'-0\" ABOVE ANY OPENING, OPC 903. AT THE "
     f"{crit.WINTER_DESIGN} WINTER DESIGN TEMPERATURE OF G-001, OPC 903.2 MAKES EVERY VENT THROUGH A ROOF OR WALL "
     f"{VENT.FROST_CLOSURE_SIZE}\" MINIMUM: INCREASE A SMALLER VENT AT THE INCREASER DRAWN, NOT LESS THAN "
     f"{fmt(VENT.INCREASE_INSIDE)} INSIDE THE THERMAL ENVELOPE. AN AIR ADMITTANCE VALVE SUBSTITUTED FOR A VENT "
     f"REQUIRES AHJ APPROVAL BEFORE ROUGH-IN.",
     "2.  PENETRATIONS OF W1R, W3 AND THE F1 CEILING: A-601. NO WATER PIPING IN AN EXTERIOR WALL'S STUD CAVITY; "
     "STACK F IS THE ONE DRAIN IN ONE, NOTE 1aa.",
     "3.  VERIFY STACK CENTERLINES AGAINST THE TRUSS LAYOUT BEFORE FABRICATION: A STACK STANDS BETWEEN TRUSSES, "
     "NEVER THROUGH A CHORD.",
     "4.  SUPPLY PIPING PEX, HOME RUN FROM MANIFOLDS IN EACH UNIT'S MECHANICAL / LAUNDRY ROOM; SHUTOFFS AT EACH UNIT "
     "AND EACH FIXTURE. THE SERVICE, THE SUPPLIES, THE MANIFOLDS AND EVERY HOME RUN ARE DRAWN AND SIZED ON P-102 "
     "AND P-103.",
     "5.  WATER METERING — BASIS SHOWN: ONE TAP AND ONE DPU METER FOR THE LOT, A SUBMETER FOR EACH DWELLING UNIT. "
     "VERIFY WITH COLUMBUS DPU WHETHER INDIVIDUAL WATER ACCOUNTS MAY BE SERVED THROUGH SUBMETERS OR REQUIRE SEPARATE "
     "TAPS, AND THE METER SETTING. SEWER PERMIT DESK, 614-645-7490.",
     f"6.  WATER HEATING: ONE ELECTRIC STORAGE WATER HEATER IN EACH DWELLING UNIT, STANDING ON THE FLOOR OF ITS "
     f"MECHANICAL / LAUNDRY ROOM WHERE DRAWN. UNIT 1 {_T1[0]} GALLONS, {inches(_T1[1])} DIAMETER; UNITS 2 AND 3 "
     f"{_T2[0]} GALLONS, {inches(_T2[1])} DIAMETER. THESE DIAMETERS ARE MAXIMA (PANEL WORKING SPACE). "
     f"{inches(pm.WH_CLR)} MINIMUM EACH SIDE. UNIFORM ENERGY FACTOR {pm.WH_UEF:.2f} OR BETTER, A-602. TWO "
     f"{pm.WH_ELEMENT_W:,} W NON-SIMULTANEOUS ELEMENTS AT {pm.WH_VOLTS} V. PROVIDE {inches(pm.WH_WORK)} x "
     f"{inches(pm.WH_WORK)} WORKING SPACE AT THE CONTROL SIDE, RCO M1305.1; THE MANUFACTURER'S GREATER CLEARANCE "
     f"GOVERNS. NO VENT; NO COMBUSTION AIR OPENING, A-001 NOTE 10. {pm.HEATER_CONN}\" COLD IN AND "
     f"{pm.HEATER_CONN}\" HOT OUT WITH FULL-PORT ISOLATION VALVES, A COLD-SIDE EXPANSION TANK, AND A DRAIN VALVE AT "
     f"THE BASE.",
     f"6a. SET EACH THERMOSTAT TO {pm.WH_STORE_F} F AND FIT AN {pm.WH_TMV_STD} THERMOSTATIC MIXING VALVE AT THE TANK "
     f"OUTLET, BLENDING TO {pm.WH_DELIVER_F} F BEFORE THE MANIFOLDS. AN ASSE 1070 POINT-OF-USE DEVICE IS NOT A "
     f"SUBSTITUTE FOR IT. PIPE ITS COLD PORT FROM THE COLD LINE THAT FEEDS THE TANK, WITH SERVICE VALVES AND UNIONS "
     f"BOTH SIDES. THE TUB AND SHOWER VALVES ARE SEPARATELY LIMITED TO {pm.WH_DELIVER_F} F UNDER OPC 424.3, P-102 "
     f"NOTE 9. VERIFY THE DELIVERED TEMPERATURE AT THE FURTHEST FIXTURE AT COMMISSIONING AND RECORD IT.",
     f"7.  WATER HEATER PAN AND RELIEF: {_PAN} STANDS OVER ANOTHER DWELLING AND TAKES A GALVANIZED OR PLASTIC PAN "
     f"UNDER ITS HEATER, RCO P2801.6, AT LEAST {inches(pm.WH_PAN_MARGIN)} LARGER IN DIAMETER THAN THE TANK, WITH A "
     f"{pm.WH_PAN_DRAIN}\" INDIRECT DRAIN RUN FULL SIZE THROUGH THE NORTH WALL AND DOWN ITS FACE, TURNED DOWN AND "
     f"SCREENED BETWEEN {inches(pm.WH_TP_LO)} AND {inches(pm.WH_TP_HI)} ABOVE GRADE, P2801.6.2. THE HEATERS ON SLAB "
     f"TAKE NO PAN. EVERY HEATER TAKES A TEMPERATURE AND PRESSURE RELIEF VALVE DISCHARGING FULL SIZE, DOWNWARD, TO "
     f"THE OUTSIDE AT THE SAME HEIGHT, RCO P2804: NO TRAP, NO VALVE, NO THREADED END, AND NOT INTO THE PAN OR ITS "
     f"DRAIN. EACH HEATER IS FED BY ITS OWN {_WHA} A {_WHP}-POLE {_WHW} CIRCUIT FROM THE DWELLING'S PANEL, E-101 AND "
     f"E-102, WITH A DISCONNECT WITHIN SIGHT.",
     "8.  MECHANICAL / LAUNDRY ROOMS: UNIT 1'S HAS ONE LOUVERED DOOR FROM THE HALL, UNITS 2 AND 3'S A LOUVERED PAIR "
     "FROM THE KITCHEN, A-602. EACH HOLDS A STACKED WASHER / DRYER, THE STORAGE WATER HEATER, THE UNIT PANEL AND THE "
     "WATER MANIFOLDS; THE UNITS 2 AND 3 ROOMS STACK.",
     "9.  ALL WORK BY A CONTRACTOR HOLDING AN OHIO OCILB PLUMBING LICENSE AND REGISTERED WITH THE CITY OF COLUMBUS. "
     "TRADE PERMIT OBTAINED SEPARATELY AFTER ISSUANCE OF THE BUILDING PERMIT.",
    ]


def sheet_p601():
    sh = Sheet(c, "P-601", "Plumbing riser diagram", "NOT TO SCALE"); sh.frame()
    x = X0; y = Y1-0.4*inch
    c.setFillColor(black); c.setFont("Helvetica-Bold", 14); c.drawString(x, y, "PLUMBING RISER DIAGRAM — DRAIN, WASTE AND VENT"); y -= 0.10*inch
    c.setLineWidth(0.9); c.line(x, y, x+15.4*inch, y)
    RY = Y1-5.32*inch
    for i, cell in enumerate(risers()):
        DRAW.riser(X0+(0.1+3.20*i)*inch, RY, cell)
    below = _trap_schedule(X0+16.8*inch, RY+4.4*inch, 2.5*inch)
    lo = DRAW.legend(X0+16.8*inch, min(RY+2.5*inch, below-0.30*inch), 2.5*inch)
    assert lo >= RY, "P-601's riser legend runs under the riser band"
    y = Y1-5.60*inch
    SIZE, LEAD = 8.0, 0.132*inch
    c.setFont("Helvetica-Bold", 12); c.drawString(x, y, "PLUMBING NOTES"); y -= 0.24*inch
    c.setFont("Helvetica", SIZE)
    # The notes are PARAGRAPHS and the column wraps them, so the block re-flows when the
    # isometric beside it takes its width -- a hand-broken line only fits the width it was
    # broken to, and this one has been two widths in a day.
    notes = [ln for ln in wrap_notes(plumbing_notes(), NOTE_W*inch, SIZE, indent="     ") if ln]
    wide = max(notes, key=lambda t: pdfmetrics.stringWidth(t, "Helvetica", SIZE))
    assert pdfmetrics.stringWidth(wide, "Helvetica", SIZE) <= NOTE_W*inch, \
        "P-601 plumbing note runs past its column: %r" % wide[:70]
    ny = y
    for t in notes:
        c.drawString(x, ny, t); ny -= LEAD
    # The isometric stands in the block the notes no longer fill. It is the drawing that
    # answers "the actual bathroom connections remain schematic" (2026-09-20), so it replaces
    # narrative rather than standing beside it: notes 1v to 1z are the paragraphs it retired.
    ix = x+(NOTE_W+0.35)*inch
    iso_h = 5.30*inch
    bath2_isometric(ix, y-iso_h, X1-ix, iso_h)
    y = min(ny, y-iso_h-0.18*inch)
    # The water service entry, in the band the notes leave at the foot of the sheet. The
    # same section 300's P-601 draws, from arkitect/lib/draw/plumbing_kit.py: both slabs sit on the
    # same 32" footing and neither can take the service through its wall.
    e = entry_for(dr.BUILDING_1, dr.GROUND)
    assert entry_for(dr.BUILDING_2, dr.GROUND) == e, \
        "P-601 draws one service entry: the two buildings no longer take the same service"
    ey = y-0.34*inch
    c.setFillColor(black); c.setFont("Helvetica-Bold", 12)
    c.drawString(x, ey, "WATER SERVICE ENTRY"); ey -= 0.24*inch
    a0, a1 = X0, X0+6.0*inch                      # detail 1 and its labels
    b0, b1 = X0+6.2*inch, X0+12.4*inch            # detail 2 and its labels
    n0 = X0+12.7*inch                             # the notes, two columns in this band
    lo = service_entry_section(ey, a0, a1, e, wall_t=WALL_T, ftg_proj=FTG_PROJ,
                               insul_t=INSUL_T, edge_insul_run=EDGE_INSUL_RUN, slab_t=SLAB_T,
                               bar_cover=BAR_COVER, bar_dia=FTG_BAR_DIA, bar=FTG_BAR,
                               gravel_t=GRAVEL_T, slab_top=LV.SLAB_TOP, grade=LV.GRADE,
                               water_sheets='P-102 AND P-103', sheet='P-601',
                               max_h=ey-Y0-0.95*inch)
    lo = min(lo, service_entry_elevation(ey, b0, b1, e, ftg_w=FTG_W, bar=FTG_BAR,
                                         sheet='P-601'))
    lo = min(lo, service_entry_notes(n0, ey, X1-n0, e, gravel_t=GRAVEL_T,
                                     bar=FTG_BAR, water_sheets='P-102 AND P-103', layer='P-ANNO-TEXT',
                                     cols=2, located='S-101'))
    assert lo >= Y0, "P-601 service entry runs off the sheet by %.2f in" % ((Y0-lo)/inch)
    LAY('P-DOMW-HOTW')   # the layer this sheet left current before the block above:
    c.showPage()         # the next document's first record draws on it, as S-101 does
