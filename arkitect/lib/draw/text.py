"""Text on a page: feet-and-inches formatting, and sheets of note text."""
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import black
from arkitect.lib.draw.page import DA, Sheet

_X0, _Y0, _X1, _Y1 = DA


def table(c,x,y,title,rows=(),width=4.6*inch,size=8,lead=0.165*inch,
          title_size=9.5,gap=0.20*inch):
    """Heading, a 0.7 pt rule under it, then label/value rows. Returns the y it ended at.

    G-001's data blocks, C-101's zoning table and C-102's zoning table were three
    hand-rolled copies of this; they differ only in type size, leading, column width
    and the gap under the heading, so those are the parameters. The call ORDER here is
    load-bearing — bold font, heading, line width, rule, body font, then the rows —
    because arkitect/lib/verify/trace.py compares the drawing calls one for one.

    `rows` is optional: a heading and its rule with body text that is not a two-column
    table (C-102's notes column) passes no rows and gets the body font set for it, so
    a bare heading needs no second helper.
    """
    c.setFont("Helvetica-Bold",title_size); c.drawString(x,y,title)
    c.setLineWidth(0.7); c.line(x,y-4,x+width,y-4)
    y-=gap; c.setFont("Helvetica",size)
    for a,b in rows:
        c.drawString(x,y,a); c.drawRightString(x+width,y,b); y-=lead
    return y



def wrap_notes(lines,width,size,font="Helvetica",indent="     "):
    """Re-flow hand-written note lines into a narrower column.

    A note starts on a line whose first character is not a space; the lines under it
    are its continuations. Each note is joined back into one string and re-broken on
    the given width, with the label kept on the first line and `indent` on the rest.
    A-001's notes are deliberately NOT put through this — they are lifted verbatim from
    the sheets they replaced and the line breaks are part of that — but a block being
    moved into a column it was not written for has to be re-set or it runs off the edge.
    """
    notes=[]
    for ln in lines:
        if ln.startswith(" ") and notes: notes[-1]+=" "+ln.strip()
        else: notes.append(ln.rstrip())
    out=[]
    for note in notes:
        if not note.strip(): out.append(""); continue
        head,_,rest = note.partition(" ")
        words=rest.split()
        line=head+" "*max(1,len(indent)-len(head)) if len(head)<len(indent) else head+" "
        cur=line
        for w in words:
            trial=cur+w+" "
            if pdfmetrics.stringWidth(trial.rstrip(),font,size)>width and cur.strip()!=head.strip():
                out.append(cur.rstrip()); cur=indent+w+" "
            else: cur=trial
        out.append(cur.rstrip())
    return out


def _wrap_line(t,width,size,font="Helvetica",indent="     "):
    """One written line, broken only where it overruns `width`. A continuation keeps the
       note's indent, so a note's own sub-lines (3b's plates, then its ceilings) stay
       separate lines and only the overflow of each wraps."""
    if pdfmetrics.stringWidth(t,font,size)<=width: return [t]
    lead_ws=len(t)-len(t.lstrip(" ")); first=t[:lead_ws]
    words=t.split(); out=[]; cur=first+words[0]
    for w in words[1:]:
        if pdfmetrics.stringWidth(cur+" "+w,font,size)>width:
            out.append(cur); cur=indent+w
        else: cur+=" "+w
    out.append(cur)
    return out


def _split_at_note(lines):
    """Two columns, cut where a new numbered note starts, so the longer column is as
       short as it can be (which, on the wrapped lines, is what sets the type size)."""
    cut=min((i for i in range(1,len(lines)) if not lines[i].startswith(" ")),
            key=lambda i: (max(i,len(lines)-i), abs(i-len(lines)/2.0)))
    return [lines[:cut],lines[cut:]]


def textsheet(c,no,title,heading,lines,size=8.2,lead=0.146*inch,cols=1,fill=False,
              max_size=11.0,lead_ratio=1.35,measure=None):
    """A full-width sheet of note text.

       Without `fill`, the lines are set exactly as written: the line COUNT is fixed, so
       only the setting can give, and the widest line fixes the type. One column fits
       the leading to the sheet but not the type, which is how A-001 came to be set
       8.2 pt on 6.8 pt: at 169 lines the ascenders and descenders collide. cols=2 splits
       the block at a note boundary, shrinks the type until the longest line fits a
       column, and puts the leading back to a readable multiple of it.

       With `fill` (two columns, or one capped at `measure`), the widest line no longer decides: each written line
       wraps where it overruns its column, and the type is the largest size, up to
       `max_size` in 0.1 pt steps, at which the wrapped columns still fit the sheet's
       height at `lead_ratio` leading. A-001 was trimmed until it used half the sheet;
       this is what lets the type take the other half."""
    sh=Sheet(c,no,title,"N/A"); sh.frame()
    top=_Y1-0.63*inch
    if fill:
        assert cols in (1,2), "textsheet: fill sets one column or two"
        # One column is for a short sheet: `measure` caps its width, since a line the
        # whole 19 in of the sheet is too long to read back from.
        gut=0.34*inch if cols==2 else 0.0
        colw=(_X1-_X0-gut)/2.0 if cols==2 else min(_X1-_X0, measure or _X1-_X0)
        room=top-_Y0
        best=None
        s=max_size
        while s>=7.0-1e-9:
            wrapped=[w for t in lines for w in _wrap_line(t,colw,s)]
            blocks=_split_at_note(wrapped) if cols==2 else [wrapped]
            if max(len(b) for b in blocks)*s*lead_ratio<=room:
                best=(s,blocks); break
            s=round(s-0.1,1)
        assert best, "textsheet: even at 7 pt the notes do not fit — trim them"
        size,blocks=best; lead=size*lead_ratio
    elif cols<2:
        blocks=[list(lines)]; colw=_X1-_X0; gut=0.0
    else:
        # break where a new numbered note starts, as near the middle as one can be found
        cut=min((i for i in range(1,len(lines)) if not lines[i].startswith(" ")),
                key=lambda i: abs(i-len(lines)/2.0))
        blocks=[list(lines[:cut]),list(lines[cut:])]; gut=0.34*inch; colw=(_X1-_X0-gut)/2.0
    if not fill:
        widest=max([pdfmetrics.stringWidth(t,"Helvetica",size) for t in lines]+[1.0])
        if widest>colw: size=size*colw/widest
        assert size>=7.0, "textsheet: the widest line drives the type below 7 pt — wrap it"
        lead=min(lead,(top-_Y0)/max(max(len(b) for b in blocks),1),size*1.55)
    y=_Y1-0.35*inch
    c.setFillColor(black); c.setFont("Helvetica-Bold",max(11,round(size*1.3,1)) if fill else 11)
    c.drawString(_X0,y,heading)
    c.setLineWidth(0.8); c.line(_X0,y-5,_X1,y-5)
    c.setFont("Helvetica",size)
    for i,block in enumerate(blocks):
        yy=top; xx=_X0+i*(colw+gut)
        for t in block:
            c.drawString(xx,yy,t); yy-=lead
    c.showPage()
