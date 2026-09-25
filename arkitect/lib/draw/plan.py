"""A plan: rooms, walls, doors, windows and dimensions, drawn in feet.

A PlanDraw is the drawing surface for one plan at one scale. It is given an origin on
the sheet (ox, oy, in page points), a scale `sc` in POINTS PER FOOT, and the plan's
overall size in feet — W across, D deep. X() and Y() are the only places model feet
become page points, and Y counts DOWN from the top of the plan, which is how a plan is
dimensioned and read. Everything else here is one symbol drawn in those coordinates: a
door leaf and its swing, a window set into the wall thickness, a running dimension
string, a room and its label.

It is separate from arkitect/lib/draw/page.py because a plan is not the sheet it sits on.
page.py owns the sheet — the paper size, the drawing area, the title block and the
border — all of which exist whether or not anything is drawn inside the frame, and one
sheet can carry several plans (or none at all, as the text sheets do). Held together,
the plan was half of page.py by line count and buried the sheet.

The class is re-exported from arkitect/lib/draw/page.py, where it used to live, so the many
sheets that say `from arkitect.lib.draw.page import PlanDraw` keep working unchanged.
"""
import math
import random
from arkitect.lib.units import fmt
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white
from reportlab.pdfbase import pdfmetrics
# arkitect/lib/draw/context.py owns the document being drawn: the layer the next line lands on,
# the observers a recording tool registers, and the greys and poche the whole set draws
# in. Taken from there and NOT from page.py, which re-exports the same names: page.py
# imports this module to re-export PlanDraw, so importing it back would be a cycle, and
# whichever of the two was imported first would raise.
from arkitect.lib.draw.context import GREY, POCHE, LAY, _announce, current_layer


class PlanDraw:
    """Draws a plan given rooms in feet. sc = points per foot."""
    def __init__(s,c,ox,oy,sc,W,D):
        s.c=c; s.ox=ox; s.oy=oy; s.sc=sc; s.W=W; s.D=D
        _announce('plan', s)
    def X(s,v): return s.ox+v*s.sc
    def Y(s,v): return s.oy+(s.D-v)*s.sc      # y down in plan coords
    def shell(s):
        LAY("A-WALL")
        c=s.c; c.setFillColor(POCHE); c.setStrokeColor(black); c.setLineWidth(1.4)
        c.rect(s.X(0),s.Y(s.D),s.W*s.sc,s.D*s.sc,fill=1,stroke=1)
    def concrete(s,x0,y0,x1,y1,clear=()):
        """Concrete stipple inside a rectangle in plan feet: fine dots with the odd small
           aggregate triangle, the usual symbol for a poured walk or slab on a site plan.

           The spacing is in POINTS, not feet, so the texture reads the same on paper at
           1/16" as at 1/8". The dots are jittered, but from a generator seeded by the
           rectangle itself, so a rebuild draws the same texture and the trace stays put.
           `clear` is page-point boxes left bare, so a label on the walk is not drawn
           through; build them with vlabel_box() from the label's own text and position.
           Grey, so text that crosses a walk without a clear box still reads over it.

           On its own pattern layer, and the caller's layer put back afterwards: a site
           plan's walks came out as ~3,000 DXF entities on A-ANNO-TEXT, the layer the
           sheet happened to be on, where nobody could freeze the texture and keep the text."""
        _was=current_layer(); LAY("C-PVMT-PATT")
        x0,x1=sorted((x0,x1)); y0,y1=sorted((y0,y1))
        c=s.c; rng=random.Random("%.4f %.4f %.4f %.4f"%(x0,y0,x1,y1))
        edge=0.9/s.sc                       # keep the texture off the outline
        nx=max(1,int((x1-x0-2*edge)*s.sc/4.2)); ny=max(1,int((y1-y0-2*edge)*s.sc/4.2))
        cw=(x1-x0-2*edge)/nx; ch=(y1-y0-2*edge)/ny
        c.saveState(); c.setFillColor(GREY); c.setStrokeColor(GREY); c.setLineWidth(0.25)
        for i in range(nx):
            for j in range(ny):
                # draw every random number whether or not the mark is kept, so a clear
                # box changes which marks are drawn and not where the others fall
                px=s.X(x0+edge+(i+rng.random())*cw); py=s.Y(y0+edge+(j+rng.random())*ch)
                tri=rng.random()<0.12; a=rng.random()*2*math.pi; rr=0.2+0.18*rng.random()
                if any(bx0-1<=px<=bx1+1 and by0-1<=py<=by1+1 for bx0,by0,bx1,by1 in clear):
                    continue
                if tri:
                    r=0.85
                    t=c.beginPath(); t.moveTo(px+r*math.cos(a),py+r*math.sin(a))
                    for k in (1,2):
                        t.lineTo(px+r*math.cos(a+k*2.0944),py+r*math.sin(a+k*2.0944))
                    t.close(); c.drawPath(t,fill=0,stroke=1)
                else:
                    c.circle(px,py,rr,fill=1,stroke=0)
        c.restoreState(); LAY(_was)
    def vlabel_box(s,x,y,txt,font,size,pad=1.2):
        """The page box a label covers when drawn with drawCentredString(0,0,txt) after
           translate(X(x),Y(y)) and rotate(90): its length runs up the page and its
           ascent to the left of the baseline."""
        w=pdfmetrics.stringWidth(txt,font,size); px,py=s.X(x),s.Y(y)
        return (px-0.8*size-pad, py-w/2-pad, px+0.25*size+pad, py+w/2+pad)
    def poly(s,pts,labels):
        LAY("A-WALL")
        c=s.c; c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.5)
        p=c.beginPath(); p.moveTo(s.X(pts[0][0]),s.Y(pts[0][1]))
        for (x,y) in pts[1:]: p.lineTo(s.X(x),s.Y(y))
        p.close(); c.drawPath(p,fill=1,stroke=1)
        c.setFillColor(black)
        for (lx,ly,nm,dm,ar) in labels:
            c.setFont("Helvetica-Bold",7.2); c.drawCentredString(s.X(lx),s.Y(ly)+5,nm)
            c.setFont("Helvetica",6.2); c.drawCentredString(s.X(lx),s.Y(ly)-3.5,dm)
            c.setFont("Helvetica",6.2); c.drawCentredString(s.X(lx),s.Y(ly)-11,ar)

    def rooms(s,rooms):
        LAY("A-WALL")
        c=s.c
        for r in rooms:
            x,y,w,h=r[:4]
            c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.5)
            c.rect(s.X(x),s.Y(y+h),w*s.sc,h*s.sc,fill=1,stroke=1)
    def labels(s,rooms,ground=False):
        """Each room's name, size and area at its middle; with `ground`, each line on a
           white ground, for captions drawn again over a trade's work."""
        LAY("A-ANNO-IDEN")
        c=s.c
        def put(font,size,x,y,t):
            c.setFont(font,size)
            if ground:
                wd=pdfmetrics.stringWidth(t,font,size)
                c.setFillColor(white); c.rect(x-wd/2-1.0,y-size*0.25,wd+2.0,size*1.05,fill=1,stroke=0)
                c.setFillColor(black)
            c.drawCentredString(x,y,t)
        for r in rooms:
            if "nolabel" in r[6:]:
                continue
            x,y,w,h=r[:4]; name=r[4]
            if not name: continue
            off=r[5] if len(r)>5 else (0.0,0.0)
            cx=s.X(x+w/2+off[0]); cy=s.Y(y+h/2+off[1])
            compact = len(r)>6 and r[6] == "compact"
            small = w*s.sc<52 or h*s.sc<30 or compact
            c.setFillColor(black)
            if small:
                put("Helvetica-Bold",5.6,cx,cy-2,name)
            else:
                put("Helvetica-Bold",7.2,cx,cy+5,name)
                put("Helvetica",6.2,cx,cy-3.5,f"{fmt(w)} x {fmt(h)}")
                put("Helvetica",6.2,cx,cy-11,f"{w*h:.0f} SF")
    def door(s,x,y,ln,o,swing=1,ext=False,far=False):
        """Hinge at (x,y). o='h': opening runs +x, leaf swings +y*swing.
                            o='v': opening runs +y, leaf swings +x*swing.
           far=True hangs the leaf on the OTHER jamb, so the open door folds back
           toward that end of the wall instead of standing out into the room."""
        LAY("A-DOOR")
        c=s.c; t=0.62*s.sc; R=ln*s.sc
        c.setFillColor(white); c.setStrokeColor(white)
        if o=="h": c.rect(s.X(x),s.Y(y)-t/2,R,t,fill=1,stroke=0)
        else:      c.rect(s.X(x)-t/2,s.Y(y+ln),t,R,fill=1,stroke=0)
        c.setStrokeColor(black); c.setLineWidth(1.3 if ext else 1.0)
        if o=="h":
            px,py = s.X(x+ln) if far else s.X(x), s.Y(y)
            c.line(px,py,px,py+swing*R)
            c.setLineWidth(0.4); c.setStrokeColor(GREY)
            if far: a0 = 90 if swing>0 else 180
            else:   a0 =  0 if swing>0 else -90
            c.arc(px-R,py-R,px+R,py+R, a0, 90)
        else:
            px,py = s.X(x), (s.Y(y+ln) if far else s.Y(y))
            c.line(px,py,px+swing*R,py)
            c.setLineWidth(0.4); c.setStrokeColor(GREY)
            if far: a0 =  0 if swing>0 else 90
            else:   a0 = -90 if swing>0 else 180
            c.arc(px-R,py-R,px+R,py+R, a0, 90)
        c.setStrokeColor(black)

    def opening(s,x,y,ln,o):
        LAY("A-DOOR")
        c=s.c; c.setFillColor(white); c.setStrokeColor(white); t=0.55*s.sc
        if o=="h": c.rect(s.X(x),s.Y(y)-t/2,ln*s.sc,t,fill=1,stroke=0)
        else:      c.rect(s.X(x)-t/2,s.Y(y+ln),t,ln*s.sc,fill=1,stroke=0)
        c.setStrokeColor(black); c.setLineWidth(0.7)
        if o=="h":
            c.line(s.X(x),s.Y(y)-t/2,s.X(x),s.Y(y)+t/2); c.line(s.X(x+ln),s.Y(y)-t/2,s.X(x+ln),s.Y(y)+t/2)
        else:
            c.line(s.X(x)-t/2,s.Y(y),s.X(x)+t/2,s.Y(y)); c.line(s.X(x)-t/2,s.Y(y+ln),s.X(x)+t/2,s.Y(y+ln))
    def bypass(s,x,y,ln,o,pt=0.13,off=0.15):
        """Bypass (sliding) closet door, type D-5: two panels on separate tracks, each
           half the opening, offset from one another so they read as passing. Drawn over
           the cased opening, not instead of it — the opening is still the hole in the
           wall."""
        s.opening(x,y,ln,o)
        LAY("A-DOOR")
        c=s.c; h=ln/2.0
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.7)
        for a,d in ((0.0,-off),(h,off)):
            if o=="v": c.rect(s.X(x+d)-pt*s.sc/2, s.Y(y+a+h), pt*s.sc, h*s.sc, fill=1, stroke=1)
            else:      c.rect(s.X(x+a), s.Y(y+d)-pt*s.sc/2, h*s.sc, pt*s.sc, fill=1, stroke=1)

    def window(s,x,y,ln,o,mark=""):
        """Two lines and nothing else, sitting IN the wall.

           The opening is given on the room face, the way doors and cased openings are,
           because that is the face everything else is dimensioned to. But a door swings
           about that face while a window fills the wall, so the symbol has to be moved
           into it: the wall runs from the given face to the building edge, and the unit
           is centered on that thickness. Drawn on the face instead, half the unit sat
           inside the room and a strip of poche was left outside it."""
        LAY("A-GLAZ")
        c=s.c
        near = (y < s.D/2) if o=="h" else (x < s.W/2)
        t   = (y if near else s.D-y) if o=="h" else (x if near else s.W-x)
        ext = (0.0 if near else s.D) if o=="h" else (0.0 if near else s.W)
        inw = 1.0 if near else -1.0            # from the exterior face inward
        # the unit is set to the exterior face, not centred in the wall: its outer line
        # sits on that face and the inner one falls 0.4 of the wall behind it
        f0, f1 = ext, ext + inw*0.4*t
        cx,cy = (x, ext+inw*t/2) if o=="h" else (ext+inw*t/2, y)
        T=t*s.sc
        # punch a shade wider than the wall. The room outline and the shell edge run
        # along the two faces, straight through the opening; a punch that stops exactly
        # on them leaves both standing and the window reads as four lines, not two.
        # Either side of the wall is white anyway — room within, paper without.
        c.setFillColor(white); c.setStrokeColor(white); m=1.0
        if o=="h": c.rect(s.X(x),s.Y(cy)-T/2-m,ln*s.sc,T+2*m,fill=1,stroke=0)
        else:      c.rect(s.X(cx)-T/2-m,s.Y(y+ln),T+2*m,ln*s.sc,fill=1,stroke=0)
        # The FILL goes back to black with the stroke, and not only the stroke: the two
        # lines take the stroke, but the mark below is text and text prints in the fill,
        # which the punch above left white. Every window tag in the set was drawn white
        # on white — in the PDF, never on the paper — until someone noticed one unit's
        # windows did not match the others' and this turned up under it.
        c.setStrokeColor(black); c.setFillColor(black); c.setLineWidth(0.6)
        if o=="h":
            for fy in (f0,f1): c.line(s.X(x),s.Y(fy),s.X(x+ln),s.Y(fy))
            if mark:
                c.setFont("Helvetica",5.2); c.drawCentredString(s.X(x+ln/2),s.Y(cy)+T/2+3,mark)
        else:
            for fx in (f0,f1): c.line(s.X(fx),s.Y(y),s.X(fx),s.Y(y+ln))
            if mark:
                c.setFont("Helvetica",5.2); c.drawString(s.X(cx)+T/2+2,s.Y(y+ln/2),mark)
    def dim(s,a,b,o,at,txt=None,sd=1,mask=False):
        """dimension between a and b along o ('h' horizontal run at y=at, 'v' vertical at x=at).
           sd is the side of the line the figure sits on: +1 is above a horizontal run and
           left of a vertical one, -1 the other side — for a string that runs inside an
           outline, so the figure reads toward the middle and not into the wall.
           mask=True paints the figure's ground white first, as dimchain's mask does, for a
           string drawn across a fixture: the outline stops under the number."""
        LAY("A-ANNO-DIMS")
        c=s.c; c.setStrokeColor(black); c.setLineWidth(0.5); c.setFillColor(black)
        _cap=6.4*0.72                                      # Helvetica cap height at 6.4 pt
        if o=="h":
            y=s.Y(at); c.line(s.X(a),y,s.X(b),y)
            for xv in (a,b): c.line(s.X(xv)-3,y-3,s.X(xv)+3,y+3)
            c.setFont("Helvetica",6.4)
            if mask: s._dim_mask(s.X((a+b)/2),y+3 if sd>0 else y-3-_cap,txt or fmt(b-a))
            c.drawCentredString(s.X((a+b)/2),y+3 if sd>0 else y-3-_cap,txt or fmt(b-a))
        else:
            x=s.X(at); c.line(x,s.Y(a),x,s.Y(b))
            for yv in (a,b): c.line(x-3,s.Y(yv)-3,x+3,s.Y(yv)+3)
            c.saveState(); c.translate(x-3 if sd>0 else x+3+_cap,s.Y((a+b)/2)); c.rotate(90)
            if mask: s._dim_mask(0,0,txt or fmt(b-a))
            c.setFont("Helvetica",6.4); c.drawCentredString(0,0,txt or fmt(b-a)); c.restoreState()
    def _dim_mask(s,x,y,txt,size=6.4,pad=1.0):
        """A white ground under a centred figure whose baseline is at (x, y): from just under
           the baseline to the cap height, so the dimension line under it is left alone."""
        c=s.c; w=pdfmetrics.stringWidth(txt,"Helvetica",size)
        c.saveState(); c.setFillColor(white)
        c.rect(x-w/2.0-pad,y-0.5,w+2*pad,size*0.72+1.5,fill=1,stroke=0)
        c.restoreState(); c.setFillColor(black)
    def dimchain(s,cs,o,at,sd=1,minlab=0.0,mask=False,labat=None,size=5.8,row=0.155*inch):
        """Running dimension string: a tick at every coordinate in cs, every segment
           labeled. A segment too narrow to hold its own label keeps it — the label
           moves out to the next free row with a leader back to the segment, so no
           dimension is silently dropped. sd is +1 or -1, the side of the string the
           labels sit on (away from the building).

           A segment no longer than `minlab` is a partition, not a space. It keeps its
           ticks — the wall is still located — but takes no label. Printing them would
           add nothing (every partition is the same thickness, and it is scheduled on
           A-601) and would make the string lie: 0.40 ft prints as 0'-5", so five
           partitions accumulate a full inch of rounding against the overall. This holds
           whether the two faces are one wall or two walls a partition apart: the number
           printed is 3-1/2" either way, and 3-1/2" tells the reader nothing.

           mask=True paints the label background out first. Strings that run inside the
           plan cross rooms and furniture, and the numbers are unreadable over them
           otherwise. labat slides the label along the string to a given position
           instead of centring it on the segment — for the dimensions that have to cross
           a piece of furniture, so the number itself does not sit on top of it."""
        LAY("A-ANNO-DIMS")
        if len(cs)<2: return
        c=s.c; c.setFillColor(black)
        P=(lambda v:(s.X(v),s.Y(at))) if o=="h" else (lambda v:(s.X(at),s.Y(v)))
        faces=[v for (v,_e) in cs]
        # witness lines first, so the dimension line sits over them
        c.setStrokeColor(GREY); c.setLineWidth(0.3)
        for (v,e) in cs:
            a=(s.X(v),s.Y(e)) if o=="h" else (s.X(e),s.Y(v))
            b=P(v)
            dx,dy = a[0]-b[0], a[1]-b[1]
            L=(dx*dx+dy*dy)**0.5
            if L > 2:
                # run it a little past the wall rather than dead onto it. An extension
                # line that stops exactly on the face lands on the inside corner where
                # two walls meet and reads as falling short of the wall it marks.
                k=(L+4.0)/L
                c.line(b[0]+dx*k, b[1]+dy*k, b[0], b[1])
        c.setStrokeColor(black); c.setLineWidth(0.5)
        # segment by segment, skipping the ones that carry no label. A partition keeps
        # its ticks so the wall is still located, but drawing the line across the gap
        # between them implies a dimension that is not there.
        for i in range(len(faces)-1):
            a,b=faces[i],faces[i+1]
            if b-a <= minlab+1e-6: continue
            (x0,y0)=P(a); (x1,y1)=P(b)
            c.line(x0,y0,x1,y1)
        for v in faces:
            px,py=P(v); c.line(px-3,py-3,px+3,py+3)
        cs=faces
        c.setFont("Helvetica",size)
        # u = position along the string, in page points
        U=(lambda pt: pt[0]) if o=="h" else (lambda pt: pt[1])
        taken={}                                     # row -> [(u0,u1), ...]
        for i in range(len(cs)-1):
            a,b=cs[i],cs[i+1]
            if b-a <= minlab+1e-6:
                continue
            t=fmt(b-a); w=pdfmetrics.stringWidth(t,"Helvetica",size)
            pa,pb=P(a),P(b)
            ua,ub=U(pa),U(pb); mid=(ua+ub)/2.0
            span=abs(ub-ua)
            if labat is not None and len(cs)==2:
                q=P(labat); mid=U(q)
            r=0 if span>=w+4 else None
            if r is None:                            # find the nearest free outer row
                r=1
                while any(not(mid+w/2+3<lo or mid-w/2-3>hi) for (lo,hi) in taken.get(r,[])): r+=1
            taken.setdefault(r,[]).append((mid-w/2,mid+w/2))
            base = pa[1] if o=="h" else pa[0]     # the string, across its own axis
            outp = base + sd*(3+r*row)               # near edge of the label zone
            if r:
                c.setLineWidth(0.3)
                if o=="h": c.line(mid,base,mid,outp)
                else:      c.line(base,mid,outp,mid)
                c.setLineWidth(0.5)
            by = outp if sd>0 else outp-size
            if mask:
                c.setFillColor(white)
                if o=="h": c.rect(mid-w/2-1.5,by-1.5,w+3,size+2,fill=1,stroke=0)
                else:      c.rect(by-1.5,mid-w/2-1.5,size+2,w+3,fill=1,stroke=0)
                c.setFillColor(black)
            if o=="h":
                c.drawCentredString(mid,by,t)
            else:
                c.saveState(); c.translate(outp+size if sd>0 else outp,mid); c.rotate(90)
                c.drawCentredString(0,0,t); c.restoreState()

    def note(s,x,y,txt,size=6.2,anchor="c",bold=False,rev=False):
        """rev=True reverses the type out in white. For notes that label a wall and so
           sit on its poche, where black on black is simply invisible."""
        LAY("A-ANNO-TEXT")
        c=s.c; c.setFillColor(white if rev else black)
        c.setFont("Helvetica-Bold" if bold else "Helvetica",size)
        if anchor=="c": c.drawCentredString(s.X(x),s.Y(y),txt)
        elif anchor=="l": c.drawString(s.X(x),s.Y(y),txt)
        else: c.drawRightString(s.X(x),s.Y(y),txt)
        c.setFillColor(black)
    def vnote(s,x,y,txt,sub="",size=9.0):
        """Text rotated 90 deg CCW, centered on plan point (x,y). For street names
           written along the side of a building. Optional smaller second line.

           LAY() like every other method here. Without it the text inherited whichever
           layer ran last, so one side street's name was filed once as A-ANNO-TEXT, from C-101,
           and twenty-two times as E-ANNO-TEXT from the greyed electrical backgrounds --
           the same architectural label under two disciplines depending on which sheet
           happened to draw it."""
        LAY("A-ANNO-TEXT")
        c=s.c; c.saveState(); c.translate(s.X(x),s.Y(y)); c.rotate(90)
        c.setFillColor(black); c.setFont("Helvetica-Bold",size)
        c.drawCentredString(0,0,txt)
        if sub:
            c.setFont("Helvetica",size*0.76); c.drawCentredString(0,-size*1.25,sub)
        c.restoreState()
    def unitbracket(s,x,y0,y1,name,sub,tick=5):
        """Bracket down the left of the sheet spanning y0..y1, with a boxed unit tag."""
        LAY("A-ANNO-TEXT")
        from reportlab.lib.units import inch as _in
        c=s.c; bx=s.X(x); ya,yb=s.Y(y0),s.Y(y1)
        c.setStrokeColor(black); c.setLineWidth(1.0)
        c.line(bx,ya,bx,yb); c.line(bx,ya,bx+tick,ya); c.line(bx,yb,bx+tick,yb)
        ym=(ya+yb)/2.0; w,h=2.10*_in,0.46*_in
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1.1)
        c.rect(bx-8-w,ym-h/2,w,h,fill=1,stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold",12)
        c.drawString(bx-8-w+8,ym+4,name)
        c.setFont("Helvetica",6.8); c.drawString(bx-8-w+8,ym-9,sub)
    def unitbox(s,x,y,name,sub,w=1.85,h=0.44):
        """Boxed unit tag centered on a plan point."""
        LAY("A-ANNO-IDEN")
        from reportlab.lib.units import inch as _in
        c=s.c; px,py=s.X(x),s.Y(y); W,H=w*_in,h*_in
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1.1)
        c.rect(px-W/2,py-H/2,W,H,fill=1,stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold",12)
        c.drawString(px-W/2+8,py+3,name)
        c.setFont("Helvetica",7.0); c.drawString(px-W/2+8,py-9,sub)
