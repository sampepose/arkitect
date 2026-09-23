"""A-602 — the door and window schedules, and the energy-compliance table."""
from arkitect.lib.draw.page import Sheet
from arkitect.lib.units import fmt, inches
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from src.openings import WIN_GEOM, WIN_HEAD, WIN_W
from arkitect.codes.ohio.rco.egress import EGRESS_MIN_H, EGRESS_MIN_SF, EGRESS_MIN_W
from src.envelope import EXTERIOR_FRAME_WALLS, VR_CLASS, perm_text
from src.exterior import WINDOW_COLOUR
from src import finishes
from src import plumbing as pm
from src.schedules import check_schedule_quantities, window_totals
from arkitect.lib.draw.kit import X0, Y0, Y1, c


# W-A's net clear opening belongs to the product, not the drawing. The schedule cell and
# the notes under the schedule hold every W-A to the minimums in arkitect/codes/ohio/rco/egress.py
# and ask for the data that shows a product meets them. Those two and G-001 note 8 are the
# only places the figures print; everything else on the set cites one of them.
def wa_net_clear():
    return "MIN %s SF, %s W, %s H"%(EGRESS_MIN_SF, inches(EGRESS_MIN_W), inches(EGRESS_MIN_H))


def wa_notes():
    return [
     "W-A: EVERY UNIT SHALL GIVE A NET CLEAR OPENING OF NOT LESS THAN %s SF, %s WIDE AND %s HIGH BY NORMAL OPERATION FROM INSIDE, RCO 310.2.1, IN EVERY SLEEPING ROOM;"
       %(EGRESS_MIN_SF, inches(EGRESS_MIN_W), inches(EGRESS_MIN_H)),
     "THE 5.0 SF GRADE-FLOOR EXCEPTION IS NOT TAKEN. SUBMIT THE MANUFACTURER'S PRODUCT DATA FOR W-A, STATING ITS NET CLEAR OPENING AREA, WIDTH AND HEIGHT, TO THE",
     "BUILDING OFFICIAL BEFORE ORDERING; KEEP IT ON SITE FOR THE FRAMING INSPECTION. DO NOT INSTALL A W-A THAT FAILS ANY MINIMUM OR LACKS THE PRODUCT DATA."]


# The requirement is G-001 note 8's and the product requirement is the window schedule's,
# three inches up this same sheet. The summary carries neither a second time: it says how
# many sleeping rooms there are, which is this project's fact, and points at both homes.
def wa_life_safety():
    return [
     "EMERGENCY ESCAPE AND RESCUE — RCO 310.2:  G-001 NOTE 8. EVERY ONE OF THE TWELVE SLEEPING ROOMS HAS A W-A.",
     "     ITS REQUIRED NET CLEAR OPENING, AND THE PRODUCT DATA THAT SHALL SHOW IT, ARE IN THE WINDOW SCHEDULE NOTES ABOVE."]


# Ohio's 312.2 requires no window fall protection and governs a device only where one is
# provided; the IRC's 24" sill / 72" above grade trigger is not in the Ohio text. A sill
# set below the drawn one is A-001 5b's.
def wa_fall_protection():
    return [
     "     SILLS ARE %s. RCO 312.2 REQUIRES NO WINDOW FALL PROTECTION; A DEVICE OR GUARD, WHERE PROVIDED, SHALL COMPLY WITH ASTM F2090, 312.2.1,"
       %fmt(WIN_GEOM["A"][0]),
     "     AND A LIMITING DEVICE SHALL RELEASE FOR ESCAPE WITHOUT REDUCING THE W-A MINIMUMS, 312.2.2.2. FOR A SILL SET LOWER, SEE A-001 NOTE 5b."]


# The exterior frame walls' interior vapour retarder, RCO 702.7, as A-601 builds it.
def wall_vr_row():
    return ("WALL VAPOR RETARDER, RCO 702.7","CLASS I OR II, INTERIOR SIDE",
            "CLASS %s PRIMER, %s MAX, ON THE GYPSUM OF %s — A-601"%(VR_CLASS, perm_text(), " / ".join(EXTERIOR_FRAME_WALLS)))


# The room finish schedule's columns, and the width its notes may run: the schedule's own.
FINISH_WIDTHS=[3.0,3.0,2.4,3.4,3.0]
FINISH_NOTE_W=sum(FINISH_WIDTHS)*inch


# ============================= A-602 SCHEDULES =============================
def sheet_a602():
    sh=Sheet(c,"A-602","Schedules and energy compliance","N/A"); sh.frame()
    x=X0; y=Y1-0.4*inch
    def tbl(title,hdr,widths,rows,x,y,check=None):
        c.setFont("Helvetica-Bold",12); c.drawString(x,y,title); y-=0.10*inch
        c.setLineWidth(0.9); c.line(x,y,x+sum(widths)*inch,y); y-=0.26*inch
        c.setFont("Helvetica-Bold",8.2); xx=x
        for h,w in zip(hdr,widths): c.drawString(xx,y,h); xx+=w*inch
        y-=0.16*inch; c.setFont("Helvetica",8.2)
        for r in rows:
            xx=x
            for v,w in zip(r,widths): c.drawString(xx,y,str(v)); xx+=w*inch
            y-=0.165*inch
        if check: check(rows)
        return y-0.28*inch
    WINDOW_TOTALS=window_totals()
    y=tbl("WINDOW SCHEDULE",["MARK","SIZE","TYPE","U-FACTOR","NET CLEAR OPENING","EGRESS","QTY"],
     [0.8,1.5,2.6,1.1,2.2,1.0,0.7],
     [("W-A","%s x %s"%(fmt(WIN_W["A"]),fmt(WIN_GEOM["A"][1])),"VINYL DOUBLE HUNG, LOW-E","0.30",
       wa_net_clear(),"YES",WINDOW_TOTALS["A"]),
      ("W-C","%s x %s"%(fmt(WIN_W["C"]),fmt(WIN_GEOM["C"][1])),"VINYL SLIDER, LOW-E","0.30",
       "32\" x 45\"  =  10.0 SF","NO",WINDOW_TOTALS["C"]),
      ("W-B","%s x %s"%(fmt(WIN_W["B"]),fmt(WIN_GEOM["B"][1])),"VINYL DOUBLE HUNG, LOW-E","0.30",
       "PER MANUFACTURER","NO",WINDOW_TOTALS["B"])],x,y)
    c.setFont("Helvetica",8.0)
    c.drawString(x,y,"WINDOW QUANTITIES ARE DERIVED FROM A-101, A-102 AND BOTH A-103 PLANS. EVERY SLEEPING ROOM HAS A W-A. WINDOW HEADS ARE %s ABOVE THE RESPECTIVE FLOOR."
                 %fmt(WIN_HEAD["A"]))
    y-=0.17*inch
    c.drawString(x,y,"EVERY WINDOW: %s, NO GRILLES. STREET-FACE TRIM AROUND THEM IS ON THE A-202 ELEVATION NOTES."%WINDOW_COLOUR)
    y-=0.17*inch
    c.drawString(x,y,"BEDROOM SILLS ARE %s, WELL BELOW THE 44\" MAXIMUM. W-B IS THE UNIT 1 KITCHEN WINDOW AND THE UNITS 4 AND 5 BATH WINDOW OVER THE TUB, TEMPERED PER"
                 %fmt(WIN_GEOM["A"][0]))
    y-=0.17*inch
    c.drawString(x,y,"RCO 308.4.5; W-C IS THE %s LIVING WINDOW AND UNIT 5'S KITCHEN WINDOW. BOTH SIT AT A 4'-0\" SILL, ABOVE THE 44\" MAXIMUM OF RCO 310.2.2, SO NEITHER IS AN EGRESS UNIT. NEITHER SERVES A SLEEPING ROOM."
                 %fmt(WIN_W["C"]))
    y-=0.17*inch
    for i,t in enumerate(wa_notes()):
        if i: y-=0.17*inch
        c.drawString(x,y,t)
    y-=0.30*inch
    y=tbl("DOOR SCHEDULE",["MARK","SIZE","TYPE","RATING","HARDWARE","QTY"],
     [0.8,1.6,3.6,1.6,3.2,0.7],
     [("D-1","3'-0\" x 6'-8\"","INSULATED STEEL, HALF GLAZED, EXTERIOR","NONE","ENTRY LOCKSET, DEADBOLT, CLOSER","5"),
      ("D-2","2'-8\" x 6'-8\"","HOLLOW CORE — BEDROOMS / OTHER UNIT BATHS","NONE","PASSAGE OR PRIVACY","16"),
      ("D-4","2'-7\" x 6'-8\"","FULL-WIDTH LOUVERED PAIR — 5'-3\" OPENING, UNITS 2 AND 3","NONE","PASSAGE, NO LATCH","4"),
      ("D-4A","2'-2\" x 6'-8\"","LOUVERED, IN PAIRS — MECH / LAUNDRY, UNITS 4 AND 5","NONE","PASSAGE, NO LATCH","4"),
      ("D-5","3'-0\" TO 7'-2\"","BYPASS — BEDROOM CLOSETS, SIZE TO SUIT OPENING","NONE","BYPASS TRACK, NO LATCH","11"),
      ("D-7","2'-8\" x 6'-8\"","LOUVERED SINGLE — UNIT 1 MECH, OUT-SWING","NONE","PASSAGE","1"),
      ("D-8","2'-6\" x 6'-8\"","HOLLOW CORE — UNIT 1 BATHS","NONE","PRIVACY","2"),
      ("D-9","1'-10\" x 6'-8\"","HOLLOW CORE — UNIT 1 CLOSET / LINEN","NONE","PASSAGE","2"),
      ("D-10","1'-10\" x 6'-6\"","UNIT 1 UNDER-STAIR CLOSET","NONE","PASSAGE","1")]
     ,x,y,check=check_schedule_quantities)
    c.setFont("Helvetica",8.0)
    c.drawString(x,y,"ALL LOUVERED MARKS SERVE A CLOSET-INSTALLED DRYER. D-4, D-4A AND D-7 SHALL DELIVER AT LEAST 100 SQ IN FREE AREA PER CLOSET,")
    y-=0.17*inch
    c.drawString(x,y,"SIZE THE LOUVERED FIELD TO SUIT. FREE AREA AND COMBUSTION AIR: A-001 NOTE 10.")
    y-=0.30*inch
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
      wall_vr_row(),
      ("FLOOR OVER UNCONDITIONED","R-30","NOT APPLICABLE — SLAB ON GRADE"),
      ("SLAB","R-10, 2'-0\" DEPTH","R-10 RIGID AT SLAB EDGE"),
      ("AIR LEAKAGE","5 ACH50, TESTED","BLOWER DOOR EACH UNIT — 5 TESTS"),
      ("DUCT LEAKAGE","PER RCO 1103.3","NOT APPLICABLE — NO DUCTED SYSTEM IN ANY UNIT"),
      ("HEATING / COOLING","--","DUCTLESS AIR-SOURCE HEAT PUMP, ONE SYSTEM PER DWELLING UNIT"),
      ("WATER HEATING","--","ELECTRIC STORAGE, UEF %.2f MINIMUM, ONE PER DWELLING UNIT — P-601 NOTE 6"%pm.WH_UEF)],x,y)
    c.setFont("Helvetica-Bold",11); c.drawString(x,y,"LIFE SAFETY SUMMARY"); y-=0.22*inch
    c.setFont("Helvetica",8.6)
    for t in [*wa_life_safety(),
     *wa_fall_protection(),
     "CEILING HEIGHT: G-001 NOTE 7. FINISHED HEIGHTS AND ASSEMBLY DEPTHS: A-301 HEIGHT SCHEDULE.",
     "ROOM AREA — RCO 304: G-001 NOTE 6. UNIT 1 BEDROOMS ARE APPROXIMATELY 111-124 SF TO STUD FACES; BEDROOM 2 EXCLUDES THE PROJECTING CLOSET.",
     "STAIRS — RCO 311.7:  G-001 NOTE 11. UNIT 1: A-001 NOTE 13. UNITS 3 AND 5: A-001 NOTES 13a AND 13b, A-604. LANDINGS AND STOOPS: C-101 NOTE 5a.",
     "SMOKE AND CARBON MONOXIDE ALARMS:  G-001 NOTES 9 AND 10. LOCATIONS AND WIRING: E-101 AND E-102.",
     "NATURAL LIGHT AND VENTILATION — RCO 303:  EVERY HABITABLE ROOM MEETS THE 8% GLAZING AND 4% OPENABLE AREA OF RCO 303.1 OUTRIGHT.",
     "     BATHROOMS — RCO 303.3: THE UNITS 1, 2 AND 3 BATHS TAKE ITS EXCEPTION, ARTIFICIAL LIGHT AND MECHANICAL VENTILATION EXHAUSTED OUTDOORS;",
     "     THE UNITS 4 AND 5 BATHS HAVE A W-B OVER THE TUB AND ARE ALSO EXHAUSTED OUTDOORS. FAN RATES: M-101 / M-102."]:
        c.drawString(x,y,t); y-=0.165*inch
    assert y>Y0, "A-602's life safety summary runs off the drawing area"
    c.showPage()
