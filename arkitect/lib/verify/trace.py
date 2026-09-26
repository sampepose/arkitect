"""Record every drawing call build.py makes, so a refactor can be PROVED to change nothing.

The permit set is the product; the code is not. Any restructuring of build.py has to
leave all twelve sheets byte-for-byte identical in content, and "I read it carefully"
is not a test. This runs build.py with the reportlab canvas wrapped in a recorder,
normalises every call to (layer, method, args) with floats rounded to 1e-6, and writes
the whole trace to a file. Two traces that compare equal mean the sheets are identical.

    python3 arkitect/lib/verify/trace.py before.txt     # on the current code
    ...refactor...
    python3 arkitect/lib/verify/trace.py after.txt && diff before.txt after.txt
    python3 arkitect/lib/verify/trace.py t.txt build.py --stdout out.txt --by-sheet sheets.txt --pdf-dir pdfs/

Paths and images are recorded by their CONTENTS, not their identity or their filename,
and the PDF itself is written to a scratch file so a trace run never touches the real
output. An image recorded by filename was both blind and harmful: the trace could not
see the picture change, and reportlab wrote the absolute path of the checkout into the
PDF, so the same commit built from two directories produced two different files. The DXF needs no
separate check: arkitect/lib/export/dxf.py records the same canvas calls through its own proxy,
so an unchanged trace means unchanged DXF geometry. (The DXF file is not byte-stable in
any case — ezdxf stamps it with a timestamp, fresh UUIDs and a non-deterministic object
table — so comparing those files directly is misleading.)

TWO THINGS THIS FILE IS CAREFUL ABOUT, both learned from being wrong:

A FAILED RUN MUST NOT LEAVE A USABLE FILE. The destination is removed before the build
starts and the trace is written to a temporary file in the same directory, renamed over
the destination only after the build has returned. A harness that writes its output at
the end silently keeps the LAST good run's file when the build crashes, and the next
`diff` compares two identical copies of it and reports success for a build that never
happened. That is a green light for nothing at all, and it has happened here.

DRAWING ORDER IS NOT BINDING ORDER. Canvas calls are recorded as they are made, so a
trace is blind to the PDF page tree — a build may reorder `c._doc.Pages.pages` before
saving, and two sets whose pages are drawn identically but bound in different orders
have identical traces. The final record in the file is the page tree AS BOUND, by sheet
number, so a sheet landing on the wrong page is a one-line diff. This was not
hypothetical: a stale `insert(1, pop(4))`, correct when C-101 was drawn fifth, bound
A-102 as page 2 of the issued set and nothing in the harness could see it.
"""
import sys, os, tempfile, hashlib

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, HERE)          # so lib.* and src.* resolve
from reportlab.pdfgen import canvas as _rl
from arkitect.lib.draw import page as sheets
from arkitect.lib import buildscript

CALLS = []
BOUND = []        # one tuple of sheet numbers per document saved, in save() order

def _n(v):
    """Normalise one argument. Floats are rounded so that re-associating the same
       arithmetic — (a+b)+c vs a+(b+c) — does not read as a change to the drawing."""
    if isinstance(v, float):
        r = round(v, 6)
        return 0.0 if r == 0 else r
    if isinstance(v, (list, tuple)):
        return tuple(_n(x) for x in v)
    if isinstance(v, _Path):
        return ('PATH', tuple(v.ops), v.closed)
    if hasattr(v, 'rgb'):                      # reportlab colour
        return ('COLOR',) + tuple(round(x, 6) for x in v.rgb())
    if hasattr(v, 'getRGBData'):               # reportlab ImageReader
        # BY CONTENT, like a path. Two reasons. Its repr carries an id(), so recording
        # the object would make every trace differ from every other and the golden
        # master would be worth nothing. And recording the CONTENT closes a hole the
        # file's own docstring did not know it had: while images were passed as
        # filenames the trace saw the name only, so replacing compass.png with a
        # different picture of the same size left the trace identical.
        try:
            digest = hashlib.md5(v.getRGBData()).hexdigest()
        except Exception as exc:              # unreadable is a fact worth recording
            return ('IMAGE', 'unreadable: %s' % exc.__class__.__name__)
        return ('IMAGE', digest, v.getSize())
    return v

class _Path:
    """Wraps a reportlab path so its contents land in the trace, not its id()."""
    def __init__(s, real):
        s._r = real; s.ops = []; s.closed = False
    def moveTo(s, x, y):  s.ops.append(('m', _n(x), _n(y))); return s._r.moveTo(x, y)
    def lineTo(s, x, y):  s.ops.append(('l', _n(x), _n(y))); return s._r.lineTo(x, y)
    def curveTo(s, *a):   s.ops.append(('c',) + tuple(_n(v) for v in a)); return s._r.curveTo(*a)
    def close(s):         s.closed = True; return s._r.close()
    def __getattr__(s, n): return getattr(s._r, n)

# The page tree, recovered while it is still possible to. Pages are appended to
# c._doc.Pages.pages by showPage in DRAW order, so the page object finished by the Nth
# showPage is pages[-1] at that moment; binding order is whatever that list holds at
# save(). Matching the two by object identity is what survives an arbitrary reordering.
PAGES = []          # (sheet number, id of page object) in DRAW order
_CUR = [None]       # sheet number currently being drawn

# Where each sheet's calls start in CALLS: (index, sheet number), in draw order. Read only
# by --by-sheet, which is how arkitect/lib/verify/gate.py names the sheets a change moved; the
# trace itself is written from CALLS alone and does not change with it.
MARKS = []

class _Watch:
    """Which sheet is being drawn. Registered rather than patched in: the class says so
       itself, which is both simpler and immune to Sheet gaining a parameter."""
    def sheet(s, sh):
        _CUR[0] = sh.no
        MARKS.append((len(CALLS), sh.no))
sheets.observe(_Watch())



class _Rec:
    def __init__(s, real, args=(), kw=None):
        object.__setattr__(s, '_r', real)
        # THE CONSTRUCTOR IS A DRAWING CALL. build.py's drawing() sets the paper size
        # there and nothing downstream ever mentions it again, so a canvas built on the
        # wrong stock drew an identical trace: C-102 came out on 24 x 18 instead of the
        # 11 x 17 G-001 note 15 promises, with the trace md5 byte-for-byte equal, the
        # tests green, check_model() stdout identical and pyflakes clean. Five oracles
        # agreeing about a sheet issued on the wrong paper, because this was the one
        # call the recorder was handed and did not look at.
        #
        # The filename is dropped. It is a scratch path in a fresh temporary directory
        # on every run, so recording it would make every trace differ from every other
        # and the oracle would be worth nothing.
        MARKS.append((len(CALLS), '(document)'))
        CALLS.append((sheets.current_layer(), 'Canvas',
                      tuple(_n(v) for v in args[1:]),
                      tuple(sorted((kk, _n(vv)) for kk, vv in (kw or {}).items()))))
    def beginPath(s):
        return _Path(s._r.beginPath())
    def showPage(s):
        # recorded exactly as __getattr__ would, so the call body does not change
        CALLS.append((sheets.current_layer(), 'showPage', (), ()))
        r = s._r.showPage()
        PAGES.append((_CUR[0], id(s._r._doc.Pages.pages[-1])))
        return r
    def save(s):
        CALLS.append((sheets.current_layer(), 'save', (), ()))
        # One record per DOCUMENT, not one flat list: a build may write more than one
        # file (a set and an 11 x 17 zoning sheet, say), and a flat
        # list would let a sheet move between them without changing the trace.
        drawn = {i: no for no, i in PAGES}
        BOUND.append(tuple(drawn.get(id(p), '?') for p in s._r._doc.Pages.pages))
        return s._r.save()
    def drawPath(s, p, *a, **k):
        CALLS.append((sheets.current_layer(), 'drawPath',
                      (_n(p),) + tuple(_n(v) for v in a),
                      tuple(sorted((kk, _n(vv)) for kk, vv in k.items()))))
        return s._r.drawPath(p._r if isinstance(p, _Path) else p, *a, **k)
    def __getattr__(s, name):
        attr = getattr(s._r, name)
        if not callable(attr):
            return attr
        def wrapped(*a, **k):
            CALLS.append((sheets.current_layer(), name,
                          tuple(_n(v) for v in a),
                          tuple(sorted((kk, _n(vv)) for kk, vv in k.items()))))
            return attr(*a, **k)
        return wrapped

# Two optional sidecars, written only after the build has returned, like the trace:
#   --stdout FILE     what the build printed. The model checks only PRINT, so this is
#                     the second oracle, and one build now serves both.
#   --by-sheet FILE   one line per sheet drawn: sheet, record count, md5 of its records.
#                     Says WHICH sheets a change moved; the trace says only that one did.
# Neither changes a byte of the trace itself.
def _flag(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 >= len(sys.argv):
            sys.exit("trace.py: %s needs a file" % name)
        val = sys.argv[i + 1]
        del sys.argv[i:i + 2]
        return val
    return None
STDOUT_TO = _flag('--stdout')
BY_SHEET_TO = _flag('--by-sheet')
# --pdf-dir DIR keeps the PDFs the recorded build wrote, named NN-<document>.pdf in the
# order the documents were written -- the order of the PAGES records -- so a tool can look
# at the sheets it just traced without drawing them twice. The file name never reaches the
# drawing (see _Rec.__init__), so this cannot change the trace.
PDF_DIR = _flag('--pdf-dir')
# Two more, so arkitect/lib/verify/gate.py builds a project ONCE for three oracles instead of once
# for each: the same build also drives sheet_text.py's Recorder and dxf.py's Proxy, stacked
# UNDER this file's recorder, which stays outermost and so sees exactly the calls the build
# makes -- the trace cannot tell they are there.
#   --text FILE   sheet_text's findings and every sheet's flat text, as JSON
#   --dxf FILE    the floor plans DXF, as arkitect/lib/export/dxf.py writes it
# Written after the trace and its sidecars. One that fails leaves no FILE, its traceback in
# FILE.err, and exit status 3: the trace is good and a part of the run is not.
TEXT_TO = _flag('--text')
DXF_TO = _flag('--dxf')
PART_FAILED = 3

# The project to trace, always named: python3 arkitect/lib/verify/trace.py out.txt <build.py>
BUILD = buildscript.build_arg(sys.argv[2] if len(sys.argv) > 2 else None, 'trace.py',
                              'python3 arkitect/lib/verify/trace.py <out.txt> <projects/<slug>/build.py>')
dest = sys.argv[1]

# Before anything can fail. A stale trace from the last good run is worse than no trace:
# it compares equal and reports success for a build that did not happen. The sidecars
# likewise.
for _stale in (dest, STDOUT_TO, BY_SHEET_TO, TEXT_TO, DXF_TO,
               TEXT_TO and TEXT_TO + '.err', DXF_TO and DXF_TO + '.err'):
    if _stale and os.path.exists(_stale):
        os.remove(_stale)

import traceback
_FAILED = {}                      # a part's file -> why it could not be written
_RECS = []                        # sheet_text Recorders, one per document
_dxf = None
if TEXT_TO:
    from arkitect.lib.verify import sheet_text
if DXF_TO:
    # the exporter failing to import is the exporter's failure, not the build's: record it
    # and build on without it, as a separate `dxf.py` run would have failed alone
    #
    # By PATH, the exporter beside this file, as `python3 <engine>/arkitect/lib/export/dxf.py`
    # always meant: imported by name, a regular `arkitect` package earlier on sys.path wins
    # over this engine's when this engine's is a namespace package (a scratch repository
    # holding only arkitect/lib/, as test_gate makes), and a broken exporter went unseen.
    try:
        import importlib.util
        _spec = importlib.util.spec_from_file_location(
            '_arkitect_dxf_beside_trace', os.path.join(HERE, 'arkitect', 'lib', 'export', 'dxf.py'))
        _dxf = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_dxf)
    except BaseException:
        _dxf = None
        _FAILED[DXF_TO] = traceback.format_exc()


def _canvas(*a, **k):
    """The real canvas, under the DXF Proxy, under the text Recorder, under this recorder."""
    c = _rl.Canvas(*a, **k)
    if _dxf is not None:
        c = _dxf.Proxy(c)
    if TEXT_TO:
        c = sheet_text.Recorder(c)
        _RECS.append(c)
    return _Rec(c, a, k)

# Import the build and call what it writes, rather than exec'ing its __main__ block:
# the tool decides where the files go and which canvas draws them. Importing must not
# draw anything — build.py's build_set() documents that contract.
import io
_out = sys.stdout
_printed = io.StringIO()
sys.stdout = _printed if STDOUT_TO else open(os.devnull, 'w')
try:
    _mod = buildscript.load(BUILD)
    with tempfile.TemporaryDirectory() as _tmp:
        if PDF_DIR:
            os.makedirs(PDF_DIR, exist_ok=True)
        for _i, _doc in enumerate(buildscript.documents(_mod)):
            _doc(os.path.join(PDF_DIR or _tmp, '%02d-%s.pdf' % (_i, _doc.__name__)),
                 make_canvas=_canvas)
except BaseException:
    # What the build printed before it failed is the diagnosis -- a model check prints
    # its table and then asserts -- so a captured run hands it to stderr, never drops it.
    if STDOUT_TO:
        sys.stderr.write(_printed.getvalue())
    raise
finally:
    sys.stdout = _out


def _whole(path, write):
    """Write beside the destination and rename onto it, so the file only ever appears
       whole."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), suffix='.partial')
    try:
        with os.fdopen(fd, 'w') as f:
            write(f)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _trace(f):
    for layer, name, a, k in CALLS:
        f.write("%s\t%s\t%r\t%r\n" % (layer, name, a, k))
    # Last, and deliberately not drawing calls: the page tree of each document
    # written, as BOUND, in the order the documents were saved.
    for doc in BOUND:
        f.write("PAGES\t%r\n" % (doc,))


def _by_sheet(f):
    """Each stretch of CALLS between two marks belongs to the mark that opens it. A
       sheet number seen twice (two documents may each draw one) is kept apart by '#n'."""
    seen = {}
    ends = [i for i, _ in MARKS[1:]] + [len(CALLS)]
    for (start, no), end in zip(MARKS, ends):
        seen[no] = seen.get(no, 0) + 1
        key = no if seen[no] == 1 else '%s#%d' % (no, seen[no])
        h = hashlib.md5()
        for layer, name, a, k in CALLS[start:end]:
            h.update(("%s\t%s\t%r\t%r\n" % (layer, name, a, k)).encode())
        f.write("%s\t%d\t%s\n" % (key, end - start, h.hexdigest()))


_whole(dest, _trace)
if STDOUT_TO:
    _whole(STDOUT_TO, lambda f: f.write(_printed.getvalue()))
if BY_SHEET_TO:
    _whole(BY_SHEET_TO, _by_sheet)
print("%s: %d drawing calls; %s"
      % (dest, len(CALLS),
         "; ".join("%d pages bound %s" % (len(d), " ".join(d)) for d in BOUND) or "no document saved"))


def _text(f):
    """What sheet_text.read() collects, in its order, and what `gate.py _text` wrote from it."""
    import json
    pages = {}
    for r in _RECS:
        for no, items in r.pages.items():
            pages.setdefault(no, []).extend(items)
    json.dump({'findings': sheet_text.findings(pages),
               'text': {str(no): sheet_text._flat(items) for no, items in pages.items()}}, f)


if TEXT_TO:
    try:
        _whole(TEXT_TO, _text)
    except BaseException:
        _FAILED[TEXT_TO] = traceback.format_exc()
if DXF_TO and _dxf is not None:
    _part = DXF_TO + '.partial'
    try:
        _dxf.write(_part)                  # ezdxf writes in place: only a whole file is renamed
        os.replace(_part, DXF_TO)
    except BaseException:
        _FAILED[DXF_TO] = traceback.format_exc()
        if os.path.exists(_part):
            os.remove(_part)
for _path, _why in sorted(_FAILED.items()):
    _whole(_path + '.err', lambda f, why=_why: f.write(why))
    sys.stderr.write(_why)
if _FAILED:
    sys.exit(PART_FAILED)
