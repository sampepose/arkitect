"""The document being drawn: its canvas, its current layer, its observers.

One document is one PDF being built — the permit set, or the zoning sheet. What it owns
is per-document rather than module-level state, so two of them can be drawn at once;
the long comment below says why that mattered and what it fixed.

This is a module of its own because BOTH arkitect/lib/draw/page.py (the sheet) and
arkitect/lib/draw/plan.py (the plan drawn inside it) need it, and plan.py cannot reach it through
page.py: page.py re-exports PlanDraw, so an import back the other way is a cycle that
breaks whichever of the two is imported first. Nothing here knows about paper sizes or
rooms. Every name is re-exported from arkitect/lib/draw/page.py, which is where the rest of the
project has always read them from.
"""
import contextlib, contextvars
from reportlab.lib.colors import Color

# The greys and the poche the whole set draws in. They live beside the layer rather
# than beside the sheet because a plan uses them and a sheet frame does not.
GREY = Color(.45,.45,.45); LGREY = Color(.72,.72,.72); POCHE = Color(.15,.15,.15)


# ---------------- the document being drawn ----------------
# Everything ONE document owns used to be a module-level slot: the canvas in build.py,
# the current layer, the observers and the title block here. Each had a LIFETIME —
# bound when a document opened, cleared when it closed — which is what stopped a
# half-built canvas from being left in place for whatever ran next.
#
# A lifetime is not isolation. One slot means one document at a time for the whole
# process, and build_set() and build_zoning_sheet() could only ever run one after the
# other. Of the four, the canvas was the one that ASSERTED on overlap; CURLAYER changes
# on nearly every sheet and is read by both recording tools, so two documents drawing at
# once would have interleaved layers into each other's DXF silently.
#
# The slots become fields of a BuildContext, and the context is held in a ContextVar
# rather than a module attribute. Threads begin with an empty context and asyncio tasks
# copy-then-isolate, so two documents in flight never see each other's canvas or layer.
class BuildContext:
    """One document being drawn: its canvas, its current layer, its observers, its
       title block. Made by document(), reachable through current()."""
    def __init__(s, canvas, titleblock=(), observers=()):
        s.canvas = canvas
        s.layer = "A-ANNO"
        s.titleblock = titleblock
        s.observers = list(observers)
    def __repr__(s):
        return "<BuildContext %r layer=%s>" % (s.canvas, s.layer)


_CUR = contextvars.ContextVar('buildcontext', default=None)


def current():
    """The document being drawn in this thread, or None outside a drawing() block."""
    return _CUR.get()


@contextlib.contextmanager
def document(canvas, titleblock=(), observers=None):
    """Make `canvas` the document being drawn, for the length of this block.

    A context manager rather than an open/close pair: the pair was public, had exactly
    one caller, and left the try/finally that makes closing exception-safe in the
    project — one file away from the state it guards, and one file away from the
    assertion below. Getting that wrong leaves a dead context in the ContextVar and the
    next document in this thread fails to open, which is a confusing way to learn that
    a sheet raised.

    Nesting is still a bug and still asserts. What is allowed is two documents in
    DIFFERENT threads: that is the point of the ContextVar, and arkitect/lib/verify/test_trace.py
    draws the set and the zoning sheet at the same time to prove it."""
    assert _CUR.get() is None, (
        "a document is already being drawn in this thread; %r is still open"
        % (_CUR.get(),))
    ctx = BuildContext(canvas, titleblock,
                       DEFAULT_OBSERVERS if observers is None else observers)
    token = _CUR.set(ctx)
    try:
        yield ctx
    finally:
        _CUR.reset(token)


class _CanvasProxy:
    """Stands in for the canvas of whichever document this thread is drawing.

    build.py names the canvas `c` in some 610 drawing calls across 41 sheet functions.
    Threading a real object through all of them would reindent most of that file for no
    change any trace can see, so the NAME stays module-level and what it RESOLVES to
    becomes per-document: `c.line(...)` on two threads reaches two different canvases.

    Outside a document this raises rather than returning None's AttributeError, because
    "no document is open" says what is actually wrong."""
    __slots__ = ()
    def __getattr__(s, n):
        ctx = _CUR.get()
        if ctx is None:
            raise RuntimeError("no document is open: %r was reached outside a "
                               "drawing() block" % (n,))
        return getattr(ctx.canvas, n)
    def __repr__(s):
        ctx = _CUR.get()
        return "<canvas of %r>" % (ctx.canvas,) if ctx else "<canvas: no document open>"


def canvas_proxy():
    """The stand-in build.py binds once as `c`."""
    return _CanvasProxy()


def live_canvas(c):
    """The real canvas behind `c`, which may be the proxy.

    A Sheet resolves it once, at construction, so the Sheet is bound to the document
    that MADE it. Holding the proxy instead would mean a Sheet kept past its own
    document quietly drew onto the next one — where against the old module-level `c`
    it would have failed loudly on None."""
    if isinstance(c, _CanvasProxy):
        ctx = _CUR.get()
        assert ctx is not None, "a Sheet was made with no document open"
        return ctx.canvas
    return c


# ---------------- watching a build draw ----------------
# A tool that re-runs a build to record what it draws — arkitect/lib/export/dxf.py for the DXF,
# arkitect/lib/verify/trace.py for the golden master — has to know which sheet is being drawn and
# which PlanDraw is active. Both used to learn that by REPLACING Sheet.__init__ and
# PlanDraw.__init__ with a wrapper of their own, and every such wrapper is a second copy
# of a signature that nothing keeps in step. Adding `page=` to Sheet broke the DXF
# exporter outright and left it dead for several commits, because its copy said
# `def _sh(self, c, no, title, scale, notes="")` and nobody had reason to look.
#
# The classes announce themselves instead. An observer implements whichever of
# sheet(Sheet) / plan(PlanDraw) it cares about and gets the OBJECT, so it reads
# attributes rather than re-deriving arguments, and a new parameter reaches it for free.
#
# Registration happens in two places because the tools register at IMPORT, before any
# document exists: observe() with nothing being drawn records a DEFAULT, and each
# document starts with a copy of the defaults. Once a document is open, observe() and
# unobserve() act on that document alone, so a tool that registers mid-build cannot
# leak into the next one and two concurrent documents keep separate lists.
DEFAULT_OBSERVERS = []

def _registry():
    """Where observe() puts things: the document being drawn, if there is one."""
    ctx = _CUR.get()
    return DEFAULT_OBSERVERS if ctx is None else ctx.observers

def observe(o):
    """Register an observer. Pass an INSTANCE — a class registers unbound methods,
       which fail on the first announcement.

       With no document open this registers a default that every later document
       inherits; that is what arkitect/lib/verify/trace.py and arkitect/lib/export/dxf.py do at import."""
    assert not isinstance(o, type), "observe() takes an instance, not a class: %r" % (o,)
    _registry().append(o)
    return o

def unobserve(o):
    r = _registry()
    if o in r:
        r.remove(o)

def _announce(what, obj):
    for o in _registry():
        fn = getattr(o, what, None)
        if fn is not None:
            fn(obj)


# The layer the next line lands on. This is the slot that made concurrency unsafe
# rather than merely impossible: the canvas asserted on overlap, but CURLAYER changed on
# nearly every sheet and was read by both recording tools, so two documents drawing at
# once would have tagged each other's geometry with no complaint from anything.
#
# It also leaked BETWEEN documents. CURLAYER was module-level and never reset, so C-102
# opened on whatever layer the permit set's last sheet happened to leave — A-ANNO-IDEN,
# the title block's — and its frame was recorded under it. Per-document state starts
# each document at A-ANNO, which is what the first sheet of the set already got.
_LAYER_OUTSIDE = ["A-ANNO"]     # LAY() called with no document open

def LAY(n):
    ctx = _CUR.get()
    if ctx is None:
        _LAYER_OUTSIDE[0] = n
    else:
        ctx.layer = n

def current_layer():
    """The layer of the document being drawn. The recording tools read this."""
    ctx = _CUR.get()
    return _LAYER_OUTSIDE[0] if ctx is None else ctx.layer
