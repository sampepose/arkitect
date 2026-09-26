"""Read every string a build draws, and find the ones a reviewer would trip on.

The trace proves a drawing did not change; it cannot say the drawing was ever right. Two
faults got through every oracle on two projects at once: a note printed on top of a detail's
label after the detail grew, and notes citing sheets and note numbers that might not exist.
Neither is a model rule. Both are visible in nothing but the text a sheet draws and where.

This runs a project's build through a recording canvas — the way arkitect/lib/verify/trace.py and
arkitect/lib/export/dxf.py do, so no PDF reader is needed — and keeps, per sheet, every string with
its box on the page. Then:

    overlaps(page)          pairs of black, unrotated strings printed over one another
    sheet_references(...)   sheet numbers cited that the build does not bind
    note_references(...)    'X-000 NOTE 4a' citations whose note the cited sheet never prints

    python3 arkitect/lib/verify/sheet_text.py projects/<name>/build.py

A box is the string's advance width by its font's ascent and descent, which is what ink a
reader sees to within a point. Rotated text is kept but never compared: its box on the page
is not its ink. Grey text is kept but never compared: a greyed background plan under an
overlay's labels is this set's drawing convention, not a collision.
"""
import math, os, re, sys, tempfile
from collections import namedtuple

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path: sys.path.insert(0, HERE)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as _rl
from arkitect.lib.draw import page as sheets
from arkitect.lib import buildscript

Text = namedtuple('Text', 'x0 y0 x1 y1 text size black level')
SHEET = re.compile(r'\b([A-Z]{1,2}-\d{3})\b')
# a note label is a number and up to two letters — and never the start of a dimension: 10'-0"
_LABEL = r'\d+[a-z]{0,2}(?![\'"\d])'
NOTE = re.compile(r'\b([A-Z]{1,2}-\d{3}) NOTES? ((?:%s)(?:(?:,| AND| TO) %s)*)' % (_LABEL, _LABEL))
_CUR = [None]


class _Watch:
    def sheet(s, sh): _CUR[0] = sh.no
sheets.observe(_Watch())


def _mul(m, n):
    a, b, c, d, e, f = m; A, B, C, D, E, F = n
    return (A*a+B*c, A*b+B*d, C*a+D*c, C*b+D*d, E*a+F*c+e, E*b+F*d+f)


class Recorder:
    """A canvas that draws as its real one does and remembers every string."""
    def __init__(s, real):
        object.__setattr__(s, '_r', real)
        s.pages = {}; s._ctm = (1, 0, 0, 1, 0, 0); s._stack = []
        s._font = ('Helvetica', 10.0); s._black = True; s._items = []

    def saveState(s): s._stack.append((s._ctm, s._font, s._black)); return s._r.saveState()
    def restoreState(s):
        if s._stack: s._ctm, s._font, s._black = s._stack.pop()
        return s._r.restoreState()
    def translate(s, dx, dy): s._ctm = _mul(s._ctm, (1, 0, 0, 1, dx, dy)); return s._r.translate(dx, dy)
    def scale(s, x, y): s._ctm = _mul(s._ctm, (x, 0, 0, y, 0, 0)); return s._r.scale(x, y)
    def rotate(s, deg):
        t = math.radians(deg); s._ctm = _mul(s._ctm, (math.cos(t), math.sin(t), -math.sin(t), math.cos(t), 0, 0))
        return s._r.rotate(deg)
    def setFont(s, name, size, *a, **k): s._font = (name, float(size)); return s._r.setFont(name, size, *a, **k)
    def setFillColor(s, col, *a, **k):
        try: rgb = col.rgb()
        except Exception: rgb = None
        s._black = rgb is not None and max(rgb) < 0.05
        return s._r.setFillColor(col, *a, **k)

    def _keep(s, x, y, text, anchor):
        name, size = s._font
        w = pdfmetrics.stringWidth(text, name, size)
        x0 = x-(w if anchor == 'r' else w/2.0 if anchor == 'c' else 0.0)
        asc, desc = pdfmetrics.getAscentDescent(name, size)
        a, b, c, d, e, f = s._ctm
        level = abs(b) < 1e-6 and abs(c) < 1e-6 and a > 0 and d > 0
        X0, Y0 = a*x0+c*(y+desc)+e, b*x0+d*(y+desc)+f
        X1, Y1 = a*(x0+w)+c*(y+asc*0.72)+e, b*(x0+w)+d*(y+asc*0.72)+f      # cap height, not the font's ascent
        s._items.append(Text(min(X0, X1), min(Y0, Y1), max(X0, X1), max(Y0, Y1), text, size*abs(d or 1), s._black, level))

    def drawString(s, x, y, text, *a, **k): s._keep(x, y, text, 'l'); return s._r.drawString(x, y, text, *a, **k)
    def drawRightString(s, x, y, text, *a, **k): s._keep(x, y, text, 'r'); return s._r.drawRightString(x, y, text, *a, **k)
    def drawCentredString(s, x, y, text, *a, **k): s._keep(x, y, text, 'c'); return s._r.drawCentredString(x, y, text, *a, **k)
    def showPage(s):
        s.pages.setdefault(_CUR[0], []).extend(s._items); s._items = []
        s._ctm = (1, 0, 0, 1, 0, 0); s._stack = []
        return s._r.showPage()
    def __getattr__(s, name): return getattr(s._r, name)
    def __setattr__(s, name, value):
        if name.startswith('_') or name == 'pages': object.__setattr__(s, name, value)
        else: setattr(s._r, name, value)


def read(build_path):
    """{sheet number: [Text]} for every sheet a project's build draws, all documents."""
    out = {}; recs = []
    def make(*a, **k):
        r = Recorder(_rl.Canvas(*a, **k)); recs.append(r); return r
    keep = sys.stdout; sys.stdout = open(os.devnull, 'w')
    try:
        mod = buildscript.load(build_path)
        with tempfile.TemporaryDirectory() as tmp:
            for doc in buildscript.documents(mod):
                doc(os.path.join(tmp, doc.__name__+'.pdf'), make_canvas=make)
    finally:
        sys.stdout.close(); sys.stdout = keep
    for r in recs:
        for no, items in r.pages.items(): out.setdefault(no, []).extend(items)
    return out


def recorded(build_path):
    """read()'s answer from the build's recording: arkitect/lib/verify/trace.py --pages, in a
       process of its own, which serves a project's build from the recording the gate or
       another test already made of it (arkitect/lib/verify/buildcache.py) and records it
       otherwise. The same Text tuples read() returns, and more hermetic than a build in this
       process, which sees whatever another test left patched in it."""
    import json, subprocess
    from arkitect.lib import workspace
    build = os.path.abspath(build_path)
    parts = build.split(os.sep)
    # started in the build's workspace, as the gate starts a tool there
    ws = os.sep.join(parts[:-3]) if len(parts) > 3 and parts[-3] == 'projects' else os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'pages.json')
        r = subprocess.run([sys.executable, os.path.join(HERE, 'arkitect', 'lib', 'verify', 'trace.py'),
                            os.path.join(tmp, 'trace.txt'), build, '--pages', out],
                           cwd=ws, capture_output=True, text=True, env=workspace.env(ws, HERE))
        if r.returncode != 0 or not os.path.exists(out):
            raise RuntimeError('the build did not record: %s\n%s' % (build_path, r.stderr[-3000:]))
        with open(out) as fh:
            return {no: [Text(*t) for t in items] for no, items in json.load(fh)}


def overlaps(items, share=0.25, least=6.0, shortest=3):
    """[(area, text, text)] for black, level strings of `shortest` characters or more whose
       boxes share over `share` of the smaller one and over `least` square points."""
    its = [t for t in items if t.black and t.level and len(t.text.strip()) >= shortest]
    hits = []
    for i, a in enumerate(its):
        for b in its[i+1:]:
            w = min(a.x1, b.x1)-max(a.x0, b.x0); h = min(a.y1, b.y1)-max(a.y0, b.y0)
            if w <= 0 or h <= 0: continue
            small = min((a.x1-a.x0)*(a.y1-a.y0), (b.x1-b.x0)*(b.y1-b.y0))
            if w*h > least and w*h > share*small:
                hits.append((round(w*h, 1), a.text.strip(), b.text.strip()))
    return sorted(hits, reverse=True)


def _flat(items):
    return ' '.join(t.text for t in items)


def sheet_references(pages):
    """[(citing sheet, cited sheet)] where the cited sheet is one the build never draws."""
    # only a discipline the set binds: GA-214 is a Gypsum Association document, not a sheet
    mine = {str(no).split('-')[0] for no in pages}
    return sorted({(no, ref) for no, items in pages.items() for ref in SHEET.findall(_flat(items))
                   if ref not in pages and ref.split('-')[0] in mine})


def note_references(pages):
    """[(citing sheet, cited sheet, note)] where the cited sheet draws no string that begins
       with that note's label."""
    bad = set()
    for no, items in pages.items():
        for sheet, notes in NOTE.findall(_flat(items)):
            if sheet not in pages: continue
            starts = [t.text.lstrip() for t in pages[sheet]]
            for k in re.findall(_LABEL, notes):
                if not any(st.startswith(k+'.') for st in starts):       # '13a.UNIT 3...' has no space after it
                    bad.add((no, sheet, k))
    return sorted(bad)


def findings(pages):
    """Every finding as the one line this tool prints for it. arkitect/lib/verify/gate.py reads
       these, so the command line and the gate cannot disagree about what counts."""
    out = []
    for no in sorted(pages, key=str):
        for area, a, b in overlaps(pages[no]):
            out.append('%s  overlap %.0f sq pt: %r / %r' % (no, area, a[:60], b[:60]))
    for no, ref in sheet_references(pages):
        out.append('%s  cites %s, which the build does not draw' % (no, ref))
    for no, sheet, k in note_references(pages):
        out.append('%s  cites %s NOTE %s, which %s does not print' % (no, sheet, k, sheet))
    return out


if __name__ == '__main__':
    build = buildscript.build_arg(sys.argv[1] if len(sys.argv) > 1 else None, 'sheet_text.py',
                                  'python3 arkitect/lib/verify/sheet_text.py <projects/<slug>/build.py>')
    pages = read(build)
    found = findings(pages)
    for line in found:
        print(line)
    print('%d sheets, %d findings' % (len(pages), len(found)))
    sys.exit(1 if found else 0)
