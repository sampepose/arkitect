"""P-601 — the plumbing riser diagram and plumbing notes. The drainage fixture units and
   everything below the slabs are P-101's; the water supply is P-102 / P-103's; the
   dwelling and service load calculations are E-101 / E-102's."""
from arkitect.lib.draw.page import GREY, LAY, Sheet
from arkitect.lib.units import fmt, inches
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from arkitect.codes.ohio import opc_vents as VENT
from src import criteria as crit
from src import drainage as dr
from src import levels
from src import plumbing as pm
from src.foundation import (BAR_COVER, EDGE_INSUL_RUN, FTG_BAR, FTG_BAR_DIA, FTG_PROJ,
                            FTG_W, GRAVEL_T, INSUL_T, SLAB_T, WALL_T)
from arkitect.codes.ohio.opc_service_entry import entry_for
from arkitect.codes.ohio.opc_service_entry_draw import (service_entry_elevation, service_entry_notes,
                                               service_entry_section)
from src.mirror import BED_SIDE, LIVE_SIDE
from arkitect.lib.draw.kit import X0, X1, Y0, Y1, c


# ============================= P-601 PLUMBING RISER =============================
def _vent_notes():
    """Notes 1v, 1w and 1x, wrapped to the column P-601's assert holds them to."""
    from arkitect.lib.draw.text import wrap_notes
    out = []
    for t in (
        "1v. VENTING, OPC CHAPTER 9. A FIXTURE MARKED * DRAINS BELOW THE SLAB, P-101, AND IS VENTED BY THE DRY VENT DRAWN BESIDE "
        "ITS STACK, NOT BY THE STACK: A STACK THAT CARRIES THE LEVEL ABOVE IS NOT A VENT FOR THE LEVEL BELOW. 912 WET VENTS TWO "
        "BATHROOM GROUPS ON ONE FLOOR LEVEL, AND 913'S WASTE STACK VENT TAKES NO WATER CLOSET, WHICH B, C AND D EACH CARRY. SO "
        "EVERY LEVEL 1 FIXTURE ON THEM KEEPS ITS OWN DRY VENT — V-A THE UNIT 1 KITCHEN, V-L ITS LAUNDRY, V-B ITS BATH 1, V-C "
        "UNIT 2'S BATH, V-K UNIT 2'S KITCHEN, V-D UNIT 4'S BATH — RISING IN ITS GROUP'S WALL TO %s OVER THE HIGHEST FLOOD RIM IT "
        "VENTS, 905.4, AND TYING INTO THAT STACK'S VENT ABOVE EVERY FIXTURE ON IT." % inches(VENT.DRY_VENT_RISE),
        "1w. STACKS E AND F ARE 913 WASTE STACK VENTS: NEITHER TAKES A WATER CLOSET, NEITHER OFFSETS BETWEEN ITS LOWEST AND "
        "HIGHEST FIXTURE CONNECTION, 913.2, EACH CARRIES A STACK VENT OF ITS OWN SIZE THROUGH THE ROOF, 913.3, AND THE LOAD IS "
        "INSIDE TABLE 913.4: %s." % _waste_text(),
        "1x. TRAP ARMS AS DRAWN, TABLE 909.1: %s." % _arm_text(),
    ):
        lines = wrap_notes([t], 12.1*inch, 8.0, indent="     ")
        out += [ln for ln in lines if ln]
    return out


def _arm_text():
    """Every trap arm the model measures, with Table 909.1's maximum for that trap."""
    from src import drainage as dr
    out = []
    for _b, a in dr.trap_arms():
        nm = a.name.replace('BUILDING 1 ', '').replace('BUILDING 2 ', '').replace('UNIT ', 'U')
        out.append('%s %s' % (nm, fmt(a.length)))
    caps = ', '.join('%g" %s' % (sz, fmt(VENT.trap_arm_max(sz)))
                     for sz in sorted({a.size for _b, a in dr.trap_arms()}))
    return '; '.join(out)+' — AGAINST '+caps


def _waste_text():
    """E and F's load, by branch interval and in all, against Table 913.4."""
    from src import drainage as dr
    out = []
    for name, size, _wc, by, total, _off in dr.waste_stacks():
        per, cap = VENT.WASTE_STACK[size]
        out.append('%s %g" %d DFU AT A BRANCH INTERVAL OF %s AND %d IN ALL OF %d'
                   % (name, size, max(by), 'NO LIMIT' if per is None else str(per), total, cap))
    return '; '.join(out)


def sheet_p601():
    sh=Sheet(c,"P-601","Plumbing riser diagram","NOT TO SCALE"); sh.frame()
    x=X0; y=Y1-0.4*inch
    c.setFont("Helvetica-Bold",14); c.drawString(x,y,"PLUMBING RISER DIAGRAM — DRAIN, WASTE AND VENT"); y-=0.10*inch
    c.setLineWidth(0.9); c.line(x,y,x+15.4*inch,y)
    def riser(ox,oy,title,levels,stackname,k=1.0,size='3"',vent_to=None,dry=(),waste=False):
        c.setFont("Helvetica-Bold",8.6); c.drawString(ox,oy+3.9*inch,title)
        c.setStrokeColor(black); c.setLineWidth(2.0)
        c.line(ox+1.6*k*inch,oy,ox+1.6*k*inch,oy+3.6*inch)              # stack
        c.setFont("Helvetica",7.5)
        # OPC 903.2: what goes through the ROOF is not always the pipe below it. A vent
        # that ties into another stack in the attic never reaches a roof and is unchanged.
        tie = dr.ATTIC_TIES.get(stackname)
        assert (tie is not None) == bool(vent_to) and (tie or vent_to) in (vent_to, None), \
            'P-601: stack %s draws a tie the model does not hold' % stackname
        roof = size if tie else VENT.roof_size(size.rstrip('"'), crit.WINTER_DESIGN_LO)+'"'
        c.drawString(ox+1.7*k*inch,oy+3.65*inch,roof+(' VENT TO '+vent_to if vent_to else ' VTR'))
        c.line(ox+1.55*k*inch,oy+3.6*inch,ox+1.65*k*inch,oy+3.75*inch)
        if roof != size:
            iy = oy+3.32*inch
            c.setLineWidth(0.9); c.line(ox+1.45*k*inch,iy,ox+1.75*k*inch,iy)
            c.setFont("Helvetica",6.0)
            c.drawString(ox+1.8*k*inch,iy-2,'%s x %s INCREASER, NOTE 1d' % (size, roof))
            c.setFont("Helvetica",7.5); c.setLineWidth(2.0)
        c.drawString(ox+1.7*k*inch,oy+1.9*inch,size+' STACK  ('+stackname+')')
        if waste:
            c.setFont("Helvetica-Bold",6.4)
            c.drawString(ox+1.7*k*inch,oy+1.74*inch,'913 WASTE STACK VENT')
            c.setFont("Helvetica",7.5)
        for i,(lv,fixtures) in enumerate(levels):
            yy=oy+0.6*inch+i*1.35*inch
            c.setLineWidth(0.7); c.setStrokeColor(GREY)
            c.line(ox,yy,ox+3.4*k*inch,yy)
            c.setStrokeColor(black); c.setFont("Helvetica-Bold",8)
            c.drawString(ox,yy+4,lv)
            c.setFont("Helvetica",7.5)
            for j,f in enumerate(fixtures):
                fy=yy+0.22*inch+j*0.19*inch
                side = 1 if dry else (-1 if j%2==0 else 1)   # a dry vent takes the left
                c.setLineWidth(1.0)
                c.line(ox+1.6*k*inch,fy,ox+1.6*k*inch+side*0.9*k*inch,fy)
                c.circle(ox+1.6*k*inch+side*0.9*k*inch,fy,2.5,fill=1)
                if side<0: c.drawRightString(ox+1.6*k*inch-0.95*k*inch,fy-2.5,f)
                else: c.drawString(ox+1.6*k*inch+0.95*k*inch,fy-2.5,f)
        # the dry vents beside it: dashed, up to a tie above every fixture on the stack
        for n,(mark,vsize,vrows,tie) in enumerate(dry):
            vx = ox+(1.6-0.40*(n+1))*k*inch
            ty = oy+2.95*inch-n*0.17*inch
            c.setStrokeColor(black); c.setLineWidth(1.4); c.setDash(4,2.5)
            c.line(vx,oy+0.40*inch,vx,ty); c.line(vx,ty,ox+1.6*k*inch,ty)
            c.setDash(); c.setLineWidth(0.8); c.circle(ox+1.6*k*inch,ty,2.2,fill=1)
            c.setFont("Helvetica-Bold",6.4); c.drawString(ox,ty+3.5,'%s  %s' % (mark,tie))
            c.setFont("Helvetica",7.2)
            for li,fixtures in vrows:
                yy = oy+0.6*inch+li*1.35*inch-n*0.58*inch
                for j,f in enumerate(fixtures):
                    fy = yy+0.22*inch+j*0.19*inch
                    c.setLineWidth(1.0); c.setDash(3,2)
                    c.line(vx,fy,vx-0.52*k*inch,fy)
                    c.setDash(); c.circle(vx-0.52*k*inch,fy,2.5,fill=1)
                    c.drawRightString(vx-0.59*k*inch,fy-2.5,f+' *')
        c.setLineWidth(1.6); c.setStrokeColor(black)
        c.line(ox+1.6*k*inch,oy,ox+3.0*k*inch,oy)
        c.setFont("Helvetica",7.5); c.drawString(ox+3.05*k*inch,oy-3,'4" TO SEWER')
    # Six risers across the 19.1" drawing width: 3.1" pitch, drawn at 0.8, titles short
    # enough to clear the next column.
    RX=lambda i: X0+(0.2+3.1*i)*inch; RY=Y1-5.6*inch
    TIE = 'DRY VENT — TIES IN HERE, %s OVER THE RIM' % inches(VENT.DRY_VENT_RISE)
    riser(RX(0), RY, "VENT A — UNIT 1 KITCHEN DRY VENT",
          [],"A",0.8,'2"',vent_to='B',
          dry=[("V-A",'2"',[(0,["KITCHEN SINK","DISHWASHER"])],'DRY VENT TO B IN THE ATTIC')])
    riser(RX(1), RY, "STACK B — UNIT 1 BATHS",
          [("LEVEL 1 — BATH 1",["LAV"]),
           ("LEVEL 2 — BATH 2",["LAV","WC","TUB"])],"B",0.8,
          dry=[("V-B",'2"',[(0,["WC","TUB"])],TIE),
               ("V-L",'2"',[(0,["WASHER STANDPIPE"])],TIE)])
    riser(RX(2), RY, "STACK C — UNITS 2/3 KITCHEN + BATH",
          [("LEVEL 1 — UNIT 2",["LAV"]),
           ("LEVEL 2 — UNIT 3",["KITCHEN SINK","DISHWASHER","LAV","WC","TUB"])],"C",0.8,
          dry=[("V-C",'2"',[(0,["WC","TUB"])],TIE),
               ("V-K",'2"',[(0,["KITCHEN SINK","DISHWASHER"])],TIE)])
    riser(RX(3), RY, "STACK D — UNITS 4/5 BATH",
          [("LEVEL 1 — UNIT 4",["LAV"]),
           ("LEVEL 2 — UNIT 5",["LAV","WC","TUB"])],"D",0.8,
          dry=[("V-D",'2"',[(0,["WC","TUB"])],TIE)])
    riser(RX(4), RY, "STACK E — UNITS 2/3 LAUNDRY, REAR WALL",
          [("LEVEL 1 — UNIT 2",["WASHER STANDPIPE"]),
           ("LEVEL 2 — UNIT 3",["WASHER STANDPIPE"])],"E",0.8,'2"',waste=True)
    riser(RX(5), RY, "STACK F — UNITS 4/5 KITCHEN + LAUNDRY",
          [("LEVEL 1 — UNIT 4",["WASHER STANDPIPE","KITCHEN SINK"]),
           ("LEVEL 2 — UNIT 5",["WASHER STANDPIPE","KITCHEN SINK"])],"F",0.8,waste=True)
    y=Y1-6.15*inch     # the riser block ends well above this; take back the slack
    # These two blocks had already outgrown the sheet: the last electrical note fell
    # about 25 pt below the frame before note 1c was rewritten. The lines are too long
    # to set in two columns, so the block is set one size down instead, which leaves
    # room for the corrected joist reasoning and about 30 pt spare.
    P101_NOTE, P101_LEAD = 8.0, 0.132*inch
    c.setFont("Helvetica-Bold",12); c.drawString(x,y,"PLUMBING NOTES"); y-=0.24*inch
    c.setFont("Helvetica",P101_NOTE)
    # Notes 6 and 7 print the heater the water model carries, so P-102, P-103, A-001,
    # A-602 and the E-sheets all quote one set of figures.
    _PAN = " AND ".join(pm.WH_PAN_UNITS)
    _T1 = pm.WH_TANKS['UNIT 1']
    _T2 = pm.WH_TANKS['UNITS 2 / 3']
    assert pm.WH_TANKS['UNITS 4 / 5'] == _T2, "P-601 note 6 says the four flats take one size"
    _WHA, _WHP, _WHW = pm.WH_CIRCUIT
    PNOTES = [
     *_vent_notes(),
     "1.  SIX STACKS, ONE PER BATH GROUP PLUS A LAUNDRY STACK IN EACH STACKED PAIR. STACK B SERVES UNIT 1'S TWO BATHS; KITCHEN VENT A AND THE",
     "     LAUNDRY DRY VENT JOIN B IN THE ATTIC. STACK C SERVES THE UNITS 2 AND 3 BATH GROUP AND THEIR TWO KITCHEN SINKS, NOTE 1e.",
     "     STACK D SERVES THE UNITS 4 AND 5 BATH GROUP ALONE. STACK E IS THE UNITS 2 AND 3 LAUNDRY STACK ON THE REAR WALL OF BUILDING 1,",
     "     NOTE 1c; STACK F THE UNITS 4 AND 5 KITCHEN AND LAUNDRY STACK ON THE SAGE WALL OF BUILDING 2, NOTE 1b. ALL SIX END ON THE ONE",
     "     4\" BUILDING SEWER TO THE 8\" ALLEY MAIN, C-101. EVERYTHING BELOW EITHER SLAB — THE DRAINS, THE STACK FEET, THE PENETRATIONS — IS ON P-101.",
     "1a. UNIT 1 BATHS STACK EXACTLY: 61\" x 85\" TO STUD FACES, 60\" x 84\" FINISHED, WITH TUB, WC AND LAVATORY ALIGNED ON ONE 2x6 WET WALL.",
     "     STACK B RISES IN THAT WALL AT THE TUB DRAIN, 86-1/2\" FROM THE SAGE INTERIOR STUD FACE: THE WALL SHARED WITH THE LEVEL 1",
     "     MECHANICAL ROOM, SO NO DRAIN RUNS IN A BEDROOM WALL. UPPER BRANCHES RUN PARALLEL TO THE F2 JOISTS.",
     "1aa.THOSE CLOSET BRANCHES ARE 3\" AND SHALL RUN IN THE WALL OR PARALLEL TO THE JOISTS. EVERY FLOOR IN THIS PROJECT IS PREFABRICATED",
     "     I-JOISTS — F1 11-7/8\", F2 14\", A-601 — AND RCO 502.8.2 PERMITS A HOLE IN ONE ONLY WHERE THE MANUFACTURER'S HOLE CHART ALLOWS IT.",
     "     SIZE AND LOCATE EVERY CROSSING OFF THE SELECTED SERIES' CHART AND THE SHOP LAYOUT, CLEAR OF BEARINGS, HANGERS AND WEB STIFFENERS.",
     "     DO NOT CUT, NOTCH OR DRILL A FLANGE. WHERE THE REQUIRED ROUTING CANNOT COMPLY WITH THE CHART, PROVIDE A SOFFIT OVER THE LEVEL 1 HALL;",
     "     DO NOT MODIFY A JOIST WITHOUT THE SUPPLIER'S ENGINEERED DETAIL. CONFIRM JOIST DIRECTION AND DEPTH BEFORE FRAMING.",
     "1b. UNIT 1 LAUNDRY AND HEATER ARE ON LEVEL 1 BESIDE THE SAGE STAIR. LAUNDRY STANDPIPE DRAINS UNDER THE SLAB, P-101.",
     "     A 2\" LAUNDRY DRY VENT RISES IN THE STAIR WALL AND JOINS STACK B IN THE ATTIC; ONE 3\" ROOF VENT SERVES UNIT 1.",
     "     IN UNITS 4 AND 5 THE MECHANICAL CLOSET STANDS IN THE SAGE CORNER OF THE KITCHEN, ONE DIRECTLY ABOVE THE OTHER, WITH THE KITCHEN",
     "     SINK ON THE SAME WALL: A 3\" STACK F IN THAT WALL TAKES BOTH SINKS AND BOTH WASHER STANDPIPES STRAIGHT",
     "     DOWN TO THE SLAB, AS STACK E DOES FOR UNITS 2 AND 3. STACK D, IN THE BATH'S ADJACENT-PARCEL WALL BEHIND THE BEDROOM 1 CLOSET, TAKES",
     "     THE BATH GROUP ALONE, SO NO DRAIN RUNS IN A BEDROOM WALL AND EACH STACK CROSSES THE TYPE F1 FLOOR-CEILING AT ONE FIRESTOPPED POINT.",
     "1c. UNITS 2 AND 3 LAUNDRIES SHALL DRAIN TO STACK E AS DRAWN; DO NOT REROUTE TO STACK C. THE TWO MECHANICAL CLOSETS STAND ONE DIRECTLY",
     "     ABOVE THE OTHER ON THE REAR WALL; A 2\" STACK IN THAT WALL TAKES BOTH WASHER STANDPIPES STRAIGHT DOWN TO THE SLAB AND OUT TO THE",
     "     BUILDING DRAIN, CROSSING THE TYPE F1 FLOOR-CEILING AT ONE FIRESTOPPED POINT. STACK C CARRIES ONLY THE KITCHEN AND THE BATH GROUP.",
     "1d. VENT STACK E THROUGH THE ROOF IN THE REAR WALL, CLEAR OF THE DRYER TERMINATION OF A-001 NOTE 16a. AN AIR ADMITTANCE",
     "     VALVE SUBSTITUTED AT A LAUNDRY STANDPIPE REQUIRES AHJ APPROVAL BEFORE ROUGH-IN.",
     f"     AT THE {crit.WINTER_DESIGN} WINTER DESIGN TEMPERATURE OF G-001, OPC 903.2 MAKES EVERY VENT THROUGH A ROOF OR WALL {VENT.FROST_CLOSURE_SIZE}\" MINIMUM:",
     f"     INCREASE A SMALLER VENT AT THE INCREASER DRAWN, NOT LESS THAN {fmt(VENT.INCREASE_INSIDE)} INSIDE THE THERMAL ENVELOPE.",
     "1e. UNIT 1'S KITCHEN SINK IS ON THE ADJACENT-PARCEL WALL; ITS 2\" DRAIN RUNS UNDER THE SLAB TO THE BUILDING DRAIN, P-101. VENT A TIES TO B IN ATTIC.",
     f"     UNITS 2 AND 3 SINKS ARE ON THE {LIVE_SIDE} WALL. UNIT 2'S DRAINS BELOW THE SLAB TO THE BUILDING DRAIN, P-101. UNIT 3'S BRANCHES ABOUT 7 FT",
     "     ALONG THE SEPARATION RUN TO STACK C, PARALLEL TO THE JOISTS PER THE SPAN ARROWS ON S-102: A 2\" LINE AT 1/4\" PER FOOT NEEDS 1-3/4\" OF FALL.",
     "     VERIFY THE REQUIRED FALL BEFORE FRAMING. IF THE DRAWN ROUTE CANNOT ACHIEVE 1/4\" PER FOOT, SUBMIT A REVISED ROUTING OR STACK",
     "     DETAIL FOR APPROVAL BEFORE ROUGH-IN.",
     "2.  W4: A-001 NOTE 4. ALL SERVICES RUN IN THE W5 FURRED CHASE ON THE UNIT SIDE.",
     "2a. BUILDING 1 ROOF VENTS: OFFSET STACKS B / C WITHIN THEIR OWN UNIT ATTICS SO ROOF PENETRATIONS ARE AT LEAST 4'-0\" FROM W4.",
     "     KEEP ALL ROOF OPENINGS OUT OF THE PROTECTED SHEATHING BANDS; SEE A-601 / A-301, RCO 302.2.4 EXCEPTION.",
     "3.  ALL BATHROOM PAIRS STACK. UNIT 1 USES ITS INTERIOR 2x6 WET WALL; UNITS 2/3 AND 4/5 USE THEIR EXISTING SEPARATION-SIDE CHASES.",
     "     UNIT 1 KITCHEN AND LAUNDRY DRAIN UNDER THE SLAB, P-101. UNITS 2/3 LAUNDRY USES STACK E, UNITS 4/5 KITCHEN AND LAUNDRY STACK F.",
     "     ALL SIX STACKS END ON ONE 4\" BUILDING SEWER TO THE 8\" ALLEY MAIN, C-101.",
     "     VERIFY STACK CENTERLINES AND JOIST SHOP DRAWINGS BEFORE FRAMING.",
     "4.  SUPPLY PIPING PEX, HOME RUN FROM A MANIFOLD IN EACH UNIT'S MECHANICAL CLOSET; SHUTOFFS AT EACH UNIT AND EACH FIXTURE. THE SERVICES, THE",
     "     TRUNKS, THE MANIFOLDS AND EVERY HOME RUN ARE DRAWN AND SIZED ON P-102 AND P-103.",
     "5.  PROVIDE SEPARATE WATER AND ELECTRIC METERING FOR EACH DWELLING UNIT. VERIFY WITH COLUMBUS DPU WHETHER INDIVIDUAL WATER ACCOUNTS MAY BE",
     "     SERVED THROUGH SUBMETERS ON ONE TAP PER BUILDING OR REQUIRE SEPARATE TAPS. SEWER PERMIT DESK, 614-645-7490.",
     "6.  WATER HEATING: ONE ELECTRIC STORAGE WATER HEATER IN EACH DWELLING UNIT, STANDING ON THE FLOOR OF THE MECHANICAL CLOSET IN ITS OWN BAY.",
     f"     UNIT 1 {_T1[0]} GALLONS, {fmt(_T1[1])} DIAMETER, FOR ITS FOUR BEDROOMS AND TWO BATHS; UNITS 2 TO 5 {_T2[0]} GALLONS, {fmt(_T2[1])} DIAMETER.",
     f"     THESE DIAMETERS ARE MAXIMA (PANEL WORKING SPACE). {fmt(pm.WH_CLR)} MINIMUM EACH SIDE.",
     f"     UNIFORM ENERGY FACTOR {pm.WH_UEF:.2f} OR BETTER, A-602. TWO {pm.WH_ELEMENT_W:,} W",
     f"     NON-SIMULTANEOUS ELEMENTS AT {pm.WH_VOLTS} V. PROVIDE {fmt(pm.WH_WORK)} x {fmt(pm.WH_WORK)} WORKING SPACE AT THE CONTROL SIDE PER RCO M1305.1; THE",
     "     MANUFACTURER'S GREATER CLEARANCE GOVERNS. NO VENT AND NO CONDENSATE; NO COMBUSTION AIR OPENING, A-001 NOTE 10.",
     f"     {pm.HEATER_CONN}\" COLD IN AND {pm.HEATER_CONN}\" HOT OUT WITH FULL-PORT ISOLATION VALVES, A COLD-SIDE EXPANSION TANK, AND A DRAIN VALVE AT THE BASE.",
     f"6a. SET EACH THERMOSTAT TO {pm.WH_STORE_F} F AND FIT A {pm.WH_TMV_STD} THERMOSTATIC MIXING VALVE AT THE TANK OUTLET, BLENDING",
     f"     TO {pm.WH_DELIVER_F} F BEFORE THE DWELLING'S MANIFOLDS. THE VALVE SERVES THE WATER DISTRIBUTION SYSTEM, {pm.WH_TMV_STD}; AN ASSE 1070 POINT-OF-USE",
     "     DEVICE AT A FIXTURE IS NOT A SUBSTITUTE FOR IT. PIPE ITS COLD PORT FROM THE SAME COLD LINE THAT FEEDS THE TANK, WITH SERVICE VALVES AND",
     "     UNIONS BOTH SIDES SO THE VALVE CAN BE REMOVED WITHOUT DRAINING THE TANK.",
     f"     THE TUB AND SHOWER VALVES ARE SEPARATELY LIMITED TO {pm.WH_DELIVER_F} F UNDER OPC 424.3, P-102 NOTE 9, DOWNSTREAM OF IT.",
     "     VERIFY THE DELIVERED TEMPERATURE AT THE FURTHEST FIXTURE AT COMMISSIONING AND RECORD IT.",
     f"7.  WATER HEATER PANS AND RELIEF: {_PAN} STAND OVER ANOTHER DWELLING, SO EACH TAKES A GALVANIZED OR PLASTIC PAN UNDER ITS HEATER, RCO P2801.6,",
     f"     AT LEAST {fmt(pm.WH_PAN_MARGIN)} LARGER IN DIAMETER THAN THE TANK, WITH A {pm.WH_PAN_DRAIN}\" INDIRECT DRAIN RUN FULL SIZE TO DAYLIGHT — UNIT 3 THROUGH THE REAR",
     "     WALL, UNIT 5 THROUGH THE SAGE WALL — TURNED DOWN AND SCREENED, P2801.6.2. THE HEATERS ON SLAB TAKE NO PAN.",
     f"     EVERY HEATER TAKES A TEMPERATURE AND PRESSURE RELIEF VALVE DISCHARGING FULL SIZE, DOWNWARD, TO THE OUTSIDE BETWEEN {fmt(pm.WH_TP_LO)} AND",
     f"     {fmt(pm.WH_TP_HI)} ABOVE FINISHED GRADE, RCO P2804: NO TRAP, NO VALVE, NO THREADED END, AND NOT INTO THE PAN OR ITS DRAIN.",
     f"     EACH HEATER IS FED BY ITS OWN {_WHA} A {_WHP}-POLE {_WHW} CIRCUIT FROM THE DWELLING'S PANEL, E-101 AND E-102, WITH A DISCONNECT WITHIN SIGHT.",
     "8.  UNIT 1 MECHANICAL ROOM HAS ONE OUT-SWINGING LOUVERED DOOR; OTHER MECHANICAL CLOSETS HAVE LOUVERED PAIRS. EVERY ONE IS ENTERED FROM A HALL",
     "     OR THE OPEN LIVING SPACE, NEVER THROUGH A BATHROOM. THE UNITS 2 AND 3 CLOSETS STACK ONE ABOVE THE OTHER ON THE REAR WALL AND DRAIN ON",
     "     STACK E, NOTE 1c AND A-001 NOTE 16a; THE UNITS 4 AND 5 CLOSETS STACK ON THE SAGE WALL AND DRAIN ON STACK F, NOTE 1b. EACH HOLDS ONLY",
     "     A STACKED WASHER / DRYER AND A STORAGE WATER HEATER, NOTE 6.",
     f"     THE LAUNDRY IS IN THE {LIVE_SIDE} CORNER AND THE HEATER IN THE {BED_SIDE}-END BAY; STACK E AND THE DRYER TERMINATION ARE LOCATED ACCORDINGLY, A-202.",
     "     IN UNITS 4 AND 5 THE W/D STANDS IN THE CORNER AGAINST THE BEARING WALL AND THE HEATER BEYOND THE PANEL ON THE SAGE WALL; STACK F AND THE",
     "     DRYER TERMINATION ARE LOCATED ACCORDINGLY, A-103.",
     "9.  ALL WORK BY A CONTRACTOR HOLDING AN OHIO OCILB PLUMBING LICENSE AND REGISTERED WITH THE CITY OF COLUMBUS. TRADE PERMIT OBTAINED SEPARATELY",
     "     AFTER ISSUANCE OF THE BUILDING PERMIT.",
    ]
    # The plumbing notes are one line each and nothing wrapped them, so a note long
    # enough to run past the load-table column printed off the sheet in silence. The
    # mixing-valve note of 2026-09-15 came within half an inch of doing it.
    _PW = max(pdfmetrics.stringWidth(t, "Helvetica", P101_NOTE) for t in PNOTES)
    assert _PW <= 12.2*inch, ("P-601 plumbing note runs past its column: the widest is"
                              " %.2f in of 12.20 — %r" % (_PW/inch, max(PNOTES, key=lambda t: pdfmetrics.stringWidth(t, "Helvetica", P101_NOTE))[:70]))
    for t in PNOTES:
        c.drawString(x,y,t); y-=P101_LEAD
    y-=0.20*inch
    # The water service entry, in the column the notes leave: the notes are held to
    # _PW of 12.2 in from X0, so this column starts clear of the widest of them.
    ex0 = X0+12.55*inch
    assert ex0 >= X0+_PW+0.2*inch, "P-601: the plumbing notes reach the service-entry column"
    e = entry_for(dr.BUILDING_1, dr.GROUND)
    assert entry_for(dr.BUILDING_2, dr.GROUND) == e, \
        "P-601 draws one service entry: the two buildings no longer take the same service"
    ew = X1-ex0
    ey = Y1-6.15*inch
    c.setFont("Helvetica-Bold",12); c.drawString(ex0, ey, "WATER SERVICE ENTRY"); ey -= 0.24*inch
    ey = service_entry_section(ey, ex0, X1, e, wall_t=WALL_T, ftg_proj=FTG_PROJ,
                               insul_t=INSUL_T, edge_insul_run=EDGE_INSUL_RUN, slab_t=SLAB_T,
                               bar_cover=BAR_COVER, bar_dia=FTG_BAR_DIA, bar=FTG_BAR,
                               gravel_t=GRAVEL_T, slab_top=levels.SLAB_TOP, grade=levels.GRADE,
                               water_sheets='P-102 AND P-103', sheet='P-601',
                               max_h=4.2*inch)
    ey = service_entry_elevation(ey, ex0, X1, e, ftg_w=FTG_W, bar=FTG_BAR, sheet='P-601')
    ey = service_entry_notes(ex0, ey, ew, e, gravel_t=GRAVEL_T,
                             bar=FTG_BAR, water_sheets='P-102 AND P-103', layer='P-ANNO-TEXT')
    assert ey >= Y0, "P-601 service entry runs off the sheet by %.2f in" % ((Y0-ey)/inch)
    LAY('P-DOMW-HOTW')   # the layer this sheet left current before the block above:
    c.showPage()         # the next document's first record draws on it, as S-101 does
