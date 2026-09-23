"""A-602 — the window, door and room finish schedules, energy compliance, and the life
safety summary. Quantities are src/schedules.py's, counted from the plans' own lists."""
from lib.draw.page import Sheet
from lib.units import fmt, inches
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from src import finishes, schedules
from src.building1 import b1_glazing
from src import envelope, levels
from src.envelope import EXTERIOR_FRAME_WALLS, VR_CLASS, perm_text
from src.exterior import WINDOW_COLOUR
from src.openings import WIN_FIXED, WIN_GEOM, WIN_HEAD, WIN_W
from codes.ohio.rco.egress import EGRESS_MIN_H, EGRESS_MIN_SF, EGRESS_MIN_W
from lib.draw.kit import X0, X1, Y0, Y1, c

UNITS = 3
_NUM = {7: "SEVEN"}


def wa_net_clear():
    return "MIN %s SF, %s W, %s H"%(EGRESS_MIN_SF, inches(EGRESS_MIN_W), inches(EGRESS_MIN_H))


def wa_notes():
    return [
     "W-A: EVERY UNIT SHALL GIVE A NET CLEAR OPENING OF NOT LESS THAN %s SF, %s WIDE AND %s HIGH BY NORMAL OPERATION FROM INSIDE, RCO 310.2.1, IN EVERY SLEEPING ROOM;"
       %(EGRESS_MIN_SF, inches(EGRESS_MIN_W), inches(EGRESS_MIN_H)),
     "THE 5.0 SF GRADE-FLOOR EXCEPTION IS NOT TAKEN. SUBMIT THE MANUFACTURER'S PRODUCT DATA FOR W-A, STATING ITS NET CLEAR OPENING AREA, WIDTH AND HEIGHT, TO THE",
     "BUILDING OFFICIAL BEFORE ORDERING; KEEP IT ON SITE FOR THE FRAMING INSPECTION. DO NOT INSTALL A W-A THAT FAILS ANY MINIMUM OR LACKS THE PRODUCT DATA."]


def wall_vr_row():
    return ("WALL VAPOR RETARDER, RCO 702.7","CLASS I OR II, INTERIOR SIDE",
            "CLASS %s PRIMER, %s MAX, ON THE GYPSUM OF %s — A-601"%(VR_CLASS, perm_text(), " / ".join(EXTERIOR_FRAME_WALLS)))


def bedroom_areas():
    """(least, most) sleeping-room floor area, SF, from the plans' own polygons."""
    a = [v[1] for k, v in b1_glazing().items() if "BEDROOM" in k]
    from src.building2 import PLAN_B2, OA_B2
    from lib.model import geom
    a += [geom.area(poly[0]) for poly in PLAN_B2.poly(OA_B2)[1:]]
    return min(a), max(a)


FINISH_WIDTHS=[3.0,3.0,2.4,3.4,3.0]
FINISH_NOTE_W=sum(FINISH_WIDTHS)*inch


# ============================= A-602 SCHEDULES =============================
def sheet_a602():
    sh=Sheet(c,"A-602","Schedules and energy compliance","N/A"); sh.frame()
    x=X0; y=Y1-0.4*inch
    # Building 2's exterior wall, slab top to roof plate: the height the stack bay runs, and
    # so the height its reduced-R area is taken over.
    B2_WALL_H = levels.ROOF_PLATE-levels.SLAB_TOP

    def tbl(title,hdr,widths,rows,x,y,check=None):
        c.setFont("Helvetica-Bold",12); c.drawString(x,y,title); y-=0.10*inch
        c.setLineWidth(0.9); c.line(x,y,x+sum(widths)*inch,y); y-=0.26*inch
        c.setFont("Helvetica-Bold",8.2); xx=x
        for h,w in zip(hdr,widths): c.drawString(xx,y,h); xx+=w*inch
        y-=0.16*inch; c.setFont("Helvetica",8.2)
        for r in rows:
            xx=x
            for i,(v,w) in enumerate(zip(r,widths)):
                # A cell runs into the next column, or off the sheet from the last one.
                # Nothing measured that until an energy exception became the longest cell
                # on this table.
                room = (X1-xx) if i == len(widths)-1 else w*inch
                assert stringWidth(str(v),"Helvetica",8.2) <= room, \
                    "A-602 %r cell overruns its column: %r" % (title[:20], str(v)[:60])
                c.drawString(xx,y,str(v)); xx+=w*inch
            y-=0.165*inch
        if check: check(rows)
        return y-0.28*inch
    WINDOW_TOTALS=schedules.window_totals(); DOOR_TOTALS=schedules.door_totals()
    assert set(WINDOW_TOTALS) == set(WIN_W), "A-602 schedules marks the plans do not use, or misses one"
    y=tbl("WINDOW SCHEDULE",["MARK","SIZE","TYPE","U-FACTOR","NET CLEAR OPENING","EGRESS","QTY"],
     [0.8,1.5,2.6,1.1,2.2,1.0,0.7],
     [("W-A","%s x %s"%(fmt(WIN_W["A"]),fmt(WIN_GEOM["A"][1])),"VINYL DOUBLE HUNG, LOW-E","0.30",
       wa_net_clear(),"YES",WINDOW_TOTALS["A"]),
      ("W-C","%s x %s"%(fmt(WIN_W["C"]),fmt(WIN_GEOM["C"][1])),"VINYL SLIDER, LOW-E","0.30",
       "PER MANUFACTURER","NO",WINDOW_TOTALS["C"]),
      ("W-B","%s x %s"%(fmt(WIN_W["B"]),fmt(WIN_GEOM["B"][1])),"VINYL DOUBLE HUNG, LOW-E","0.30",
       "PER MANUFACTURER","NO",WINDOW_TOTALS["B"]),
      ("W-D","%s x %s"%(fmt(WIN_W["D"]),fmt(WIN_GEOM["D"][1])),"VINYL FIXED, LOW-E","0.30",
       "NONE — FIXED","NO",WINDOW_TOTALS["D"])],x,y)
    assert WIN_FIXED == ("D",)
    c.setFont("Helvetica",8.0)
    for t in ["WINDOW QUANTITIES ARE COUNTED FROM THE A-101 AND A-102 PLANS. EVERY SLEEPING ROOM HAS A W-A. WINDOW HEADS ARE %s ABOVE THE RESPECTIVE FLOOR."%fmt(WIN_HEAD["A"]),
              "EVERY WINDOW: %s, NO GRILLES; CASED PER A-201 / A-202 NOTE 5."%WINDOW_COLOUR,
              "W-A SILLS ARE %s, BELOW THE 44\" MAXIMUM OF RCO 310.2.2. W-B, W-C AND W-D SIT AT A %s SILL, ABOVE IT: NONE IS AN EGRESS UNIT, AND EVERY ROOM THAT HAS ONE ALSO HAS A W-A"%(fmt(WIN_GEOM["A"][0]),fmt(WIN_GEOM["B"][0])),
              "OR IS NOT A SLEEPING ROOM. W-D IS THE FIXED UNIT OVER THE UNIT 1 STAIR. SAFETY GLAZING, RCO 308.4: THE UNIT 1 LANDING W-A AT THE HEAD OF THE STAIR, A-101, AND THE GLAZING IN EVERY DOOR."]:
        c.drawString(x,y,t); y-=0.17*inch
    for i,t in enumerate(wa_notes()):
        if i: y-=0.17*inch
        c.drawString(x,y,t)
    y-=0.30*inch
    y=tbl("DOOR SCHEDULE",["MARK","SIZE","TYPE","RATING","HARDWARE","QTY"],
     [0.8,1.6,4.6,1.2,2.8,0.7],
     [(mk,size,kind,"NONE",hw,DOOR_TOTALS[mk]) for mk,(size,kind,hw) in schedules.DOORS.items()],x,y)
    c.setFont("Helvetica",8.0)
    for t in ["DOOR QUANTITIES ARE COUNTED FROM THE A-101 AND A-102 PLANS; D-4A COUNTS LEAVES. THE HALL OPENING IN EACH OF UNITS 2 AND 3 IS CASED, WITHOUT A DOOR.",
              "%s EACH SERVE A ROOM WITH A CLOTHES DRYER IN IT AND SHALL DELIVER AT LEAST 100 SQ IN OF FREE AREA, OR THE DRYER MAKER'S LARGER OPENING, RCO M1502.1 — SIZE THE LOUVERED FIELD TO SUIT."%" AND ".join(schedules.LOUVERED),
              "FREE AREA AND COMBUSTION AIR: A-001 NOTE 10. D-1 AT UNIT 1 IS THE REQUIRED EGRESS DOOR, RCO 311.2; D-2 IS NOT."]:
        c.drawString(x,y,t); y-=0.17*inch
    y-=0.13*inch
    y=tbl("ROOM FINISH SCHEDULE",["ROOM","FLOOR","BASE","WALLS","CEILING"],
     FINISH_WIDTHS,finishes.schedule_rows(),x,y)
    c.setFont("Helvetica",8.0)
    for t in finishes.notes():
        assert stringWidth(t,"Helvetica",8.0)<=FINISH_NOTE_W, "A-602 finish note runs past its schedule: "+t[:40]
        c.drawString(x,y,t); y-=0.17*inch
    y-=0.30*inch
    y=tbl("ENERGY COMPLIANCE — RCO TABLE 1102.1.2, CLIMATE ZONE 5, PRESCRIPTIVE PATH",
     ["COMPONENT","REQUIRED","PROVIDED"],[5.0,4.0,6.4],
     [("FENESTRATION U-FACTOR","0.30 MAXIMUM","0.30 — SEE WINDOW SCHEDULE"),
      ("GLAZED FENESTRATION SHGC","NOT REGULATED IN CZ5","--"),
      ("CEILING","R-49","R-49 BLOWN, ENERGY HEEL TRUSS"),
      ("WOOD FRAME WALL","R-20, OR R-13 + R-5","R-21 IN 2x6 — W1 AND W1R"),
      # A-601 insulates ONE bay at R-8, where stack F's fittings leave 2" behind them. The
      # prescriptive row above cannot carry that, so the exception is stated here with the
      # path that does carry it, and the area is derived rather than estimated.
      ("   EXCEPTION: ONE STUD BAY","TOTAL UA ALTERNATIVE, RCO CH. 11",
       "R-%d WHERE STACK F STANDS, %.0f SF — A-601. INCLUDED IN THE ENERGY COMPLIANCE "
       "DOCUMENTATION SUBMITTED WITH THE PERMIT"
       % (envelope.STACK_BAY_R, envelope.stack_bay_area(B2_WALL_H))),
      wall_vr_row(),
      ("FLOOR OVER UNCONDITIONED","R-30","NOT APPLICABLE — SLAB ON GRADE"),
      ("SLAB","R-10, 2'-0\" DEPTH","R-10 RIGID AT SLAB EDGE"),
      ("AIR LEAKAGE","5 ACH50, TESTED","BLOWER DOOR EACH UNIT — %d TESTS"%UNITS),
      ("DUCT LEAKAGE","PER RCO 1103.3","UNIT 1'S DUCTS AND AIR HANDLERS ARE COMPLETELY INSIDE THE THERMAL ENVELOPE, 1103.3.3 EXCEPTION; UNITS 2 AND 3 ARE DUCTLESS"),
      ("HEATING / COOLING","--","AIR-SOURCE HEAT PUMP, ONE SYSTEM PER DWELLING: UNIT 1 DUCTED IN TWO ZONES, UNITS 2 AND 3 DUCTLESS"),
      ("WATER HEATING","--","ELECTRIC STORAGE, ONE PER DWELLING UNIT")],x,y)
    c.setFont("Helvetica-Bold",11); c.drawString(x,y,"LIFE SAFETY SUMMARY"); y-=0.22*inch
    c.setFont("Helvetica",8.6)
    lo,hi=bedroom_areas(); beds=len(schedules.sleeping_rooms())
    # Each rule has one home. The escape opening's is G-001 note 8 and, for what the
    # product shall give, this sheet's own window schedule notes; ceiling height, room
    # area, stairs and the alarms are G-001 notes 7, 6, 11 and 9 / 10. The summary
    # carries only this project's own facts and points at each home.
    for t in ["EMERGENCY ESCAPE AND RESCUE — RCO 310.2:  G-001 NOTE 8. EVERY ONE OF THE %s SLEEPING ROOMS HAS A W-A."%_NUM[beds],
     "     ITS REQUIRED NET CLEAR OPENING, AND THE PRODUCT DATA THAT SHALL SHOW IT, ARE IN THE WINDOW SCHEDULE NOTES ABOVE.",
     "     W-A SILLS ARE %s. RCO 312.2 REQUIRES NO WINDOW FALL PROTECTION; A DEVICE OR GUARD, WHERE PROVIDED, SHALL COMPLY WITH ASTM F2090, 312.2.1,"%fmt(WIN_GEOM["A"][0]),
     "     AND A LIMITING DEVICE SHALL RELEASE FOR ESCAPE WITHOUT REDUCING THE W-A MINIMUMS, 312.2.2.2.",
     "CEILING HEIGHT: G-001 NOTE 7. FINISHED HEIGHTS AND ASSEMBLY DEPTHS: A-301 HEIGHT SCHEDULE.",
     "ROOM AREA — RCO 304: G-001 NOTE 6. THE SLEEPING ROOMS ARE %.0f TO %.0f SF TO STUD FACES, NET OF THEIR CLOSETS."%(lo,hi),
     "STAIRS — RCO 311.7:  G-001 NOTE 11. UNIT 1: A-101. UNIT 3: A-603. LANDINGS AND STOOPS: C-103.",
     "SMOKE AND CARBON MONOXIDE ALARMS:  G-001 NOTES 9 AND 10. LOCATIONS AND WIRING: E-101 AND E-102.",
     "NATURAL LIGHT AND VENTILATION — RCO 303:  EVERY HABITABLE ROOM MEETS THE 8% GLAZING AND 4% OPENABLE AREA OF RCO 303.1 OUTRIGHT; W-D, FIXED, IS NOT COUNTED.",
     "     BATHROOMS — RCO 303.3: EVERY BATHROOM TAKES ITS EXCEPTION, ARTIFICIAL LIGHT AND MECHANICAL VENTILATION EXHAUSTED OUTDOORS, 50 CFM INTERMITTENT OR",
     "     20 CFM CONTINUOUS, RCO TABLE M1505.4.4."]:
        assert stringWidth(t,"Helvetica",8.6) <= 15.6*inch, "A-602 life safety line overruns: %r" % t[:40]
        c.drawString(x,y,t); y-=0.165*inch
    assert y>Y0, "A-602's life safety summary runs off the drawing area"
    c.showPage()
