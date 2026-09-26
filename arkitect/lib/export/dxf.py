"""Emit the floor plans as model-space DXF by recording what build.py draws.

The PDF and the DXF come out of the same code path, so they cannot drift.
Model units are INCHES; 1 drawing unit = 1 inch, true size.
"""
import sys, math, os, tempfile
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, HERE)          # so lib.* and src.* resolve
import ezdxf
from reportlab.pdfgen import canvas as _rlcanvas
from arkitect.lib.draw import page as sheets
from arkitect.lib import buildscript

ENT=[]                      # (frame, layer, kind, payload) in MODEL INCHES
TX={'p':None,'i':-1}        # active PlanDraw transform and frame index
FRAMES=[]                   # (sheet, W, D) per frame
FONT={'size':7.0,'bold':False}
SHEET={'no':None}
# The sheets whose plan frames are exported. P-601 is not here: it is the riser
# diagram and schedules and announces no plan, so listing it only suggested it
# had one. C-102 announces a plan and is deliberately excluded -- it is drawn
# turned 76 degrees so true north is up, and its geometry would land rotated
# against every other frame in the model-space row.
WANT={"C-101","C-103","A-101","A-102","A-103","S-101","S-102","S-103","S-104","M-101","M-102","E-101","E-102","P-101","P-102","P-103"}

CTM=[[1.0,0.0,0.0,1.0,0.0,0.0]]          # a,b,c,d,e,f — canvas transform stack
def _mul(m,n):
    a,b,c,d,e,f=m; A,B,C,D,E,F=n
    return [a*A+c*B, b*A+d*B, a*C+c*D, b*C+d*D, a*E+c*F+e, b*E+d*F+f]
def _rot():
    a,b=CTM[-1][0],CTM[-1][1]
    return math.degrees(math.atan2(b,a))

def _m(x,y):
    """page points -> model inches, using the active PlanDraw and the live transform"""
    p=TX['p']
    if p is None: return None
    a,b,c,d,e,f=CTM[-1]
    x,y = a*x+c*y+e, b*x+d*y+f
    fx=(x-p.ox)/p.sc                 # feet, plan x
    fy=p.D-(y-p.oy)/p.sc             # feet, plan y (y down)
    return (fx*12.0, -fy*12.0)       # inches, y flipped so plan reads upright in CAD

def _lay(): return sheets.current_layer()
M=8.0                                   # keep only what sits within 8 ft of the plan —
                                        # enough for the outermost dimension ring at 7.2 ft,
                                        # and short of the context notes at 10.5 ft
def _inside(pt):
    p=TX['p']; fx=pt[0]/12.0; fy=-pt[1]/12.0
    return -M<=fx<=p.W+M and -M<=fy<=p.D+M
def _emit(kind,*pay):
    if TX['p'] is None or SHEET['no'] not in WANT: return
    pts=[q for q in pay if isinstance(q,tuple) and len(q)==2 and
         all(isinstance(v,(int,float)) for v in q)]
    if pts and not any(_inside(q) for q in pts): return
    ENT.append((TX['i'],_lay(),kind,pay))

class Path:
    def __init__(s): s.pts=[]; s.closed=False
    def moveTo(s,x,y): s.pts.append(('m',x,y))
    def lineTo(s,x,y): s.pts.append(('l',x,y))
    def close(s): s.closed=True

class Proxy:
    def __init__(s,real): s._r=real
    def __getattr__(s,n): return getattr(s._r,n)
    # ---- geometry ----
    def line(s,x1,y1,x2,y2):
        a,b=_m(x1,y1),_m(x2,y2)
        if a: _emit('L',a,b)
        return s._r.line(x1,y1,x2,y2)
    def rect(s,x,y,w,h,fill=0,stroke=1):
        if stroke:
            c=[_m(x,y),_m(x+w,y),_m(x+w,y+h),_m(x,y+h)]
            if c[0]:
                for i in range(4): _emit('L',c[i],c[(i+1)%4])
        return s._r.rect(x,y,w,h,fill=fill,stroke=stroke)
    def roundRect(s,x,y,w,h,r,fill=0,stroke=1):
        if stroke:
            c=[_m(x,y),_m(x+w,y),_m(x+w,y+h),_m(x,y+h)]
            if c[0]:
                for i in range(4): _emit('L',c[i],c[(i+1)%4])
        return s._r.roundRect(x,y,w,h,r,fill=fill,stroke=stroke)
    def circle(s,x,y,r,fill=0,stroke=1):
        cc=_m(x,y); p=TX['p']
        if cc: _emit('C',cc,r/p.sc*12.0)
        return s._r.circle(x,y,r,fill=fill,stroke=stroke)
    def ellipse(s,x1,y1,x2,y2,fill=0,stroke=1):
        cc=_m((x1+x2)/2.0,(y1+y2)/2.0); p=TX['p']
        if cc:
            _emit('E',cc,abs(x2-x1)/2.0/p.sc*12.0,abs(y2-y1)/2.0/p.sc*12.0)
        return s._r.ellipse(x1,y1,x2,y2,fill=fill,stroke=stroke)
    def arc(s,x1,y1,x2,y2,startAng=0,extent=90):
        cc=_m((x1+x2)/2.0,(y1+y2)/2.0); p=TX['p']
        if cc:
            r=abs(x2-x1)/2.0/p.sc*12.0
            # page y is up, model y is down-flipped -> mirror the angles
            a0=-(startAng+extent); a1=-startAng
            _emit('A',cc,r,a0,a1)
        return s._r.arc(x1,y1,x2,y2,startAng=startAng,extent=extent)
    # ---- transform ----
    def saveState(s): CTM.append(list(CTM[-1])); return s._r.saveState()
    def restoreState(s):
        if len(CTM)>1: CTM.pop()
        return s._r.restoreState()
    def translate(s,dx,dy):
        CTM[-1]=_mul(CTM[-1],[1,0,0,1,dx,dy]); return s._r.translate(dx,dy)
    def rotate(s,deg):
        r=math.radians(deg); co,si=math.cos(r),math.sin(r)
        CTM[-1]=_mul(CTM[-1],[co,si,-si,co,0,0]); return s._r.rotate(deg)
    def scale(s,sx,sy):
        CTM[-1]=_mul(CTM[-1],[sx,0,0,sy,0,0]); return s._r.scale(sx,sy)
    def beginPath(s): return Path()
    def drawPath(s,pth,fill=0,stroke=1,**k):
        if stroke and pth.pts:
            pts=[_m(x,y) for (_,x,y) in pth.pts]
            if pts[0]:
                for i in range(len(pts)-1): _emit('L',pts[i],pts[i+1])
                if pth.closed: _emit('L',pts[-1],pts[0])
        rp=s._r.beginPath()
        for (op,x,y) in pth.pts:
            (rp.moveTo if op=='m' else rp.lineTo)(x,y)
        if pth.closed: rp.close()
        return s._r.drawPath(rp,fill=fill,stroke=stroke,**k)
    # ---- text ----
    def setFont(s,name,size,*a,**k):
        FONT['size']=size; FONT['bold']='Bold' in name
        return s._r.setFont(name,size,*a,**k)
    def _txt(s,x,y,t,just):
        a=_m(x,y); p=TX['p']
        if a and t: _emit('T',a,t,FONT['size']/p.sc*12.0,just,FONT['bold'],_rot())
    def drawString(s,x,y,t,**k):        s._txt(x,y,t,0); return s._r.drawString(x,y,t,**k)
    def drawCentredString(s,x,y,t,**k): s._txt(x,y,t,1); return s._r.drawCentredString(x,y,t,**k)
    def drawRightString(s,x,y,t,**k):   s._txt(x,y,t,2); return s._r.drawRightString(x,y,t,**k)

# ---- hooks -------------------------------------------------------------
# What sheet are we on, and which plan is live. Registered, not patched in — the
# classes announce themselves, so this reads their attributes and cannot fall out of
# step with their constructors. See arkitect/lib/draw/page.py.
class _Watch:
    def sheet(s, sh):
        SHEET['no']=sh.no; TX['p']=None; TX['i']=-1
        del CTM[1:]; CTM[0]=[1.0,0.0,0.0,1.0,0.0,0.0]
    def plan(s, p):
        TX['p']=p
        if SHEET['no'] in WANT:
            FRAMES.append((SHEET['no'],p.W,p.D)); TX['i']=len(FRAMES)-1
        else:
            TX['i']=-1
    def plan_end(s, _):
        TX['p']=None; TX['i']=-1
sheets.observe(_Watch())


# ---- write DXF ---------------------------------------------------------
def write(out):
    """Write what the recording holds (ENT, FRAMES) to `out`. arkitect/lib/verify/trace.py calls it
       after a build it recorded through Proxy, so the gate builds a project once, not twice."""
    doc=ezdxf.new('R2010',setup=True)
    doc.header['$INSUNITS']=1          # inches
    doc.header['$MEASUREMENT']=0       # imperial
    # A colour per layer. This table used to cover the A, C and M layers only, and the
    # exporter writes whatever layer the drawing set -- so when the electrical, plumbing and
    # structural sheets gained their own layers, 2,966 entities were written to layer names
    # that appeared in no LAYER record. ezdxf's own auditor reports 0 errors for that: the
    # entities are valid and simply have no colour and nothing to freeze or plot them by,
    # which is the entire point of layering them. The assertion below is what keeps the two
    # lists together from now on.
    COLOR={'A-WALL':7,'A-DOOR':3,'A-GLAZ':4,'A-FLOR-STRS':6,'A-FURN':8,
           'A-ANNO-IDEN':2,'A-ANNO-TEXT':2,'A-ANNO-DIMS':1,'A-ANNO':2,
           'C-PVMT-PATT':8,             # concrete stipple on walks, PlanDraw.concrete()
           'M-HVAC-EQPM':5,'M-EXHS-DUCT':30,'M-HVAC-DUCT':30,'M-HVAC-PIPE':4,'M-ANNO-TEXT':2,   # M-101 / M-102
           # E-101 / E-102
           'E-POWR':5,'E-LITE':6,'E-ALRM':1,'E-ANNO-TEXT':2,
           # P-101 / P-102 / P-103 / P-601
           'P-SANR-FIXT':4,'P-SANR-UNDR':4,'P-DOMW-COLD':5,'P-DOMW-HOTW':1,
           'P-DOMW-UNDR':5,'P-EQPM':3,'P-ANNO-TEXT':2,'P-ANNO-DIMS':1,
           # S-101 .. S-104
           'S-FNDN':7,'S-FNDN-RADN':3,'S-FRAM':6,'S-ANNO-TEXT':2}
    drawn=sorted({lay for (_fi,lay,_kind,_pay) in ENT})
    missing=[n for n in drawn if n not in COLOR]
    assert not missing, (
        "the DXF writes %d layer(s) with no colour and no LAYER record: %s. Add them to "
        "COLOR -- an entity on an undeclared layer is valid DXF and invisible to the "
        "auditor, so nothing else will tell you." % (len(missing), ", ".join(missing)))
    for n,col in COLOR.items():
        if n not in doc.layers: doc.layers.add(n,color=col)
    msp=doc.modelspace()

    # lay every plan out in a row in model space, 20 ft apart
    OFF=[]; run=0.0
    for (sh,W,D) in FRAMES:
        OFF.append(run); run += (W+20.0)*12.0
    JUST={0:'LEFT',1:'CENTER',2:'RIGHT'}
    for (fi,lay,kind,pay) in ENT:
        dx=OFF[fi]
        if kind=='L':
            (a,b)=pay; msp.add_line((a[0]+dx,a[1]),(b[0]+dx,b[1]),dxfattribs={'layer':lay})
        elif kind=='C':
            (c0,r)=pay; msp.add_circle((c0[0]+dx,c0[1]),r,dxfattribs={'layer':lay})
        elif kind=='E':
            (c0,rx,ry)=pay
            major=(rx,0) if rx>=ry else (0,ry)
            ratio=(ry/rx) if rx>=ry else (rx/ry)
            msp.add_ellipse((c0[0]+dx,c0[1]),major_axis=major,ratio=max(ratio,1e-3),
                            dxfattribs={'layer':lay})
        elif kind=='A':
            (c0,r,a0,a1)=pay
            msp.add_arc((c0[0]+dx,c0[1]),r,a0,a1,dxfattribs={'layer':lay})
        elif kind=='T':
            (a,t,h,just,bold,rot)=pay
            e=msp.add_text(t,dxfattribs={'layer':lay,'height':h,'rotation':rot,
                                         'style':'Standard'})
            e.set_placement((a[0]+dx,a[1]), align=ezdxf.enums.TextEntityAlignment[JUST[just]])
    for i,(sh,W,D) in enumerate(FRAMES):
        t=msp.add_text(sh,dxfattribs={'layer':'A-ANNO-TEXT','height':18.0})
        t.set_placement((OFF[i],36.0),align=ezdxf.enums.TextEntityAlignment.LEFT)
    doc.saveas(out)


def main(argv):
    # The project to record, and where its DXF goes, always named, so the same exporter
    # serves any project: arkitect dxf <build.py> [<out.dxf>]
    BUILD = buildscript.build_arg(argv[1] if len(argv) > 1 else None, 'dxf.py',
                                  'python3 arkitect/lib/export/dxf.py <projects/<slug>/build.py> [<out.dxf>]')
    # Import the build and call what it writes, rather than exec'ing its __main__ block.
    # The PDFs go to a scratch directory: this tool exports a DXF and must not rewrite the
    # project's deliverables on the way past, which the __main__ block made it do.
    _mod = buildscript.load(BUILD)
    # Resolve the output path before doing any work. A build script that defines no
    # DXF_OUT and is given no explicit path used to fall back to deriving one from the
    # build script's own path (build.py -> build.dxf) -- exactly the shape *.dxf's
    # .gitignore rule swallows with no error, which is the trap DXF_OUT exists to close.
    # A project that forgets to define it must fail loudly, not write a file nothing
    # tracked will ever see.
    if len(argv) > 2:
        OUT = argv[2]
    else:
        OUT = getattr(_mod, 'DXF_OUT', None)
        if OUT is None:
            sys.exit(
                "arkitect/lib/export/dxf.py: %s defines no DXF_OUT, and no output path was given.\n"
                "Fix one of:\n"
                "  - pass the output path as the second argument:\n"
                "      python3 arkitect/lib/export/dxf.py %s <out.dxf>\n"
                "  - define DXF_OUT in the build script, e.g.:\n"
                "      DXF_OUT = os.path.join(HERE, '<project>-floor-plans.dxf')\n"
                % (BUILD, BUILD))
    # The same build already recorded whole (arkitect/lib/verify/buildcache.py) is served from
    # its recording: what the build printed, the DXF it wrote, and the line this prints of it.
    from arkitect.lib import workspace as _ws
    from arkitect.lib.verify import buildcache
    if buildcache.usable(BUILD, HERE, _ws.WORKSPACE):
        hit = buildcache.found(buildcache.key(BUILD, HERE, _ws.WORKSPACE), _ws.WORKSPACE)
        kept = ('stdout.txt', 'floor.dxf', 'dxf-summary.txt')
        if hit and all(os.path.exists(os.path.join(hit, p)) for p in kept):
            import shutil
            with open(os.path.join(hit, 'stdout.txt')) as fh:
                sys.stdout.write(fh.read())
            with open(os.path.join(hit, 'dxf-summary.txt')) as fh:
                print(fh.read())
            shutil.copyfile(os.path.join(hit, 'floor.dxf'), OUT)
            print("saved",OUT, "%.1f KB"%(os.path.getsize(OUT)/1024))
            return
    with tempfile.TemporaryDirectory() as _tmp:
        for _doc in buildscript.documents(_mod):
            _doc(os.path.join(_tmp, _doc.__name__+'.pdf'),
                 make_canvas=lambda *a,**k: Proxy(_rlcanvas.Canvas(*a,**k)))
    print("recorded %d entities in %d plan frames: %s"%(len(ENT),len(FRAMES),[f[0] for f in FRAMES]))
    write(OUT)
    print("saved",OUT, "%.1f KB"%(os.path.getsize(OUT)/1024))


if __name__ == '__main__':
    main(sys.argv)
