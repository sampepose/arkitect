"""Tests for the tools that re-run a build: lib/verify/trace.py and lib/export/dxf.py.

    python3 lib/verify/run_tests.py       # the project's test command; see that file
    python3 lib/verify/test_trace.py     # just this file, while working on it

The harness is the thing every refactor is checked against, so a harness that reports
success when it should not is worse than having none — every "verified, trace identical"
claim downstream rests on these two properties:

    a failed build must not leave a file that compares equal to the last good run
    a trace must notice a sheet bound on the wrong page, not only drawn differently

Both were false once. The first gave a green light to a build that had crashed; the
second let a stale insert(1, pop(4)) bind A-102 as page 2 of the issued set.

The DXF exporter is here too, and not by filing convenience: it re-runs a build with a
recording canvas exactly as the trace does, so it shares the trace's failure modes.
Adding `page=` to Sheet for the 11 x 17 zoning sheet broke it outright -- back when its
hook restated Sheet's signature -- while the trace kept reporting 9,658 clean calls.
The set built, the trace was green and the exporter was dead for several
commits, because nothing ran it. Now something does.

These are unittest.TestCase methods so that something other than a person typing the
path COLLECTS them. They were plain functions driven by a __main__ block once, which
is a third instance of this file's own subject: run by hand it was green, while
`python3 -m unittest discover -s lib/verify -p 'test_*.py'` matched the filename,
imported the module, found no TestCase, and ran none of the checks below. A harness
nothing runs is the failure mode described three paragraphs up.
"""
import os, re, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRACE = os.path.join(HERE, 'lib', 'verify', 'trace.py')
DXF = os.path.join(HERE, 'lib', 'export', 'dxf.py')
# A real, scaffolded project the engine ships with (phase 1 of the public release): these
# tests check the TOOLS on a real build without borrowing one of the private projects.
BUILD = os.path.join(HERE, 'projects', 'example_100', 'build.py')


# A two-page build, written here rather than borrowed from a project, so these tests
# check the HARNESS and not one lot's build script. The swap line is the only difference
# between the two variants: identical drawing, different binding.
# A build script in the shape lib/buildscript.py expects: it draws nothing at import,
# and exposes build_set(output_path, make_canvas). Written here rather than borrowed
# from a project, so these tests check the TOOLS and not one lot's build.
SYNTH = """
from reportlab.pdfgen import canvas
from lib.draw.page import Sheet, PW, PH

def build_set(output_path=None, make_canvas=None):
    c = (make_canvas or canvas.Canvas)(output_path or %r, pagesize=(PW, PH))
    for no in ('X-001', 'X-002'):
        Sheet(c, no, 'synthetic', 'N/A')
        c.drawString(10, 10, no)
        c.showPage()
    %s
    c.save()
    return output_path
"""


class HarnessTestCase(unittest.TestCase):
    """Shared plumbing: a scratch directory per test, and a check() that reports every
       failing check in a test instead of stopping at the first.

       That last part is deliberate and worth keeping. These tests assert several
       independent properties of one run -- exit code, stderr, what is left on disk --
       and knowing which combination broke is most of the diagnosis. subTest is the
       unittest spelling of the ok/FAIL list this file used to print by hand."""

    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.tmp = scratch.name

    def check(self, name, cond, detail=""):
        with self.subTest(name):
            self.assertTrue(cond, detail)

    def trace(self, dest, build):
        return subprocess.run([sys.executable, TRACE, dest, build],
                              capture_output=True, text=True, cwd=HERE)

    def synth(self, name, swap="pass"):
        path = os.path.join(self.tmp, name)
        with open(path, 'w') as fh:
            fh.write(SYNTH % (os.path.join(self.tmp, name + '.pdf'), swap))
        return path

    def read(self, path):
        """Closed explicitly: unittest runs with warnings enabled, and a screenful of
           ResourceWarning is how a real failure goes unread."""
        with open(path) as fh:
            return fh.read()

    def pages_of(self, trace_file):
        """Every PAGES record in the trace: one tuple of sheet numbers per document."""
        recs = [ln for ln in self.read(trace_file).splitlines() if ln.startswith("PAGES\t")]
        return [eval(r.split("\t", 1)[1]) for r in recs] or None

    def require_build(self):
        if not os.path.exists(BUILD):
            self.skipTest("no build.py")


class TraceTests(HarnessTestCase):

    def test_crashed_build_leaves_no_stale_trace(self):
        """The one that matters. Write a good trace, then trace a build that raises, and
           the good trace must not still be sitting there looking like a fresh result."""
        dest = os.path.join(self.tmp, 'trace.txt')
        r = self.trace(dest, BUILD)
        self.check("good build writes a trace", r.returncode == 0 and os.path.exists(dest),
                   r.stderr[-300:])
        good = self.read(dest)
        self.check("the trace is not empty", len(good) > 1000)

        bad = os.path.join(self.tmp, 'broken.py')
        with open(bad, 'w') as fh:
            fh.write("raise RuntimeError('build failed on purpose')\n")   # fails on import
        r = self.trace(dest, bad)
        self.check("failed build exits non-zero", r.returncode != 0, "returncode %s" % r.returncode)
        self.check("failed build says why", 'build failed on purpose' in r.stderr, r.stderr[-300:])
        # The actual regression: the file must be GONE, not merely different. If it survives,
        # the next `diff before.txt after.txt` compares the last good run against itself.
        self.check("failed build leaves no trace file", not os.path.exists(dest),
                   "stale file survived, %d bytes" % (os.path.getsize(dest) if os.path.exists(dest) else 0))
        if os.path.exists(dest):
            self.check("...and at least it is not the stale one", self.read(dest) != good)

    def test_partial_write_does_not_land(self):
        """A build that draws, then fails, must not leave the calls it got through."""
        dest = os.path.join(self.tmp, 'partial.txt')
        half = os.path.join(self.tmp, 'half.py')
        with open(half, 'w') as fh:
            fh.write(
                "from reportlab.pdfgen import canvas\n"
                "def build_set(output_path=None, make_canvas=None):\n"
                "    c = (make_canvas or canvas.Canvas)(output_path or 'x.pdf')\n"
                "    c.drawString(1, 1, 'drew something')\n"
                "    raise RuntimeError('died after drawing')\n")
        r = self.trace(dest, half)
        self.check("build that drew then died exits non-zero", r.returncode != 0)
        self.check("no partial trace is left behind", not os.path.exists(dest))
        leftovers = [f for f in os.listdir(self.tmp) if f.endswith('.partial')]
        self.check("no temporary file is left behind", not leftovers, str(leftovers))

    def test_page_order_is_recorded(self):
        """Drawing order is not binding order, and the trace has to carry the second."""
        dest = os.path.join(self.tmp, 'pages.txt')
        r = self.trace(dest, self.synth('two.py'))
        self.check("synthetic build traces", r.returncode == 0, r.stderr[-300:])
        bound = self.pages_of(dest) if os.path.exists(dest) else None
        self.check("a page tree is recorded", bound is not None)
        if bound is None:
            return
        self.check("one record per document", len(bound) == 1, str(bound))
        self.check("one entry per page", bound[0] == ('X-001', 'X-002'), str(bound))

    def test_page_order_change_is_visible(self):
        """The property the call log alone cannot give: a build whose pages are reordered
           before saving must not trace equal to one whose pages are not."""
        a, b = os.path.join(self.tmp, 'a.txt'), os.path.join(self.tmp, 'b.txt')
        ra = self.trace(a, self.synth('plain.py'))
        rb = self.trace(b, self.synth('swapped.py',
                                      "_p = c._doc.Pages.pages; _p[0], _p[1] = _p[1], _p[0]"))
        self.check("both variants build", ra.returncode == 0 and rb.returncode == 0,
                   (ra.stderr + rb.stderr)[-300:])
        if ra.returncode or rb.returncode:
            return
        A, B = self.read(a).splitlines(), self.read(b).splitlines()
        self.check("a page swap draws identically", A[:-1] == B[:-1],
                   "call logs differ, so the swap changed more than the binding")
        self.check("a page swap changes the trace", A[-1] != B[-1],
                   "%s == %s" % (A[-1][:50], B[-1][:50]))
        self.check("and the record shows the swap",
                   self.pages_of(a) == [('X-001', 'X-002')] and self.pages_of(b) == [('X-002', 'X-001')],
                   "%s / %s" % (self.pages_of(a), self.pages_of(b)))

    def test_each_document_is_traced_on_its_own_paper(self):
        """The page size lives in the canvas CONSTRUCTOR and nowhere else, so until the
           recorder looked at it a sheet on the wrong stock traced identically. Proved:
           building C-102 at (PW, PH) instead of ANSI_B put it on 24 x 18 with the trace
           md5 byte-for-byte equal and every other oracle green.

           Sizes come from the modules that define them, not from numbers typed here, so
           changing the paper deliberately changes this test's expectation with it and
           only an ACCIDENTAL change fails."""
        self.require_build()
        dest = os.path.join(self.tmp, 'paper.txt')
        r = self.trace(dest, BUILD)
        self.check("the real set traces", r.returncode == 0, r.stderr[-300:])
        if r.returncode:
            return
        sizes = [ln.split('\t', 3)[3] for ln in self.read(dest).splitlines()
                 if ln.split('\t', 2)[1:2] == ['Canvas']]
        self.check("one Canvas record per document", len(sizes) == 2, str(sizes))
        if len(sizes) != 2:
            return
        sys.path.insert(0, HERE)
        from lib.draw.page import PW, PH, ANSI_B
        want_set = "(('pagesize', (%r, %r)),)" % (round(float(PW), 6), round(float(PH), 6))
        want_zone = "(('pagesize', (%r, %r)),)" % (round(float(ANSI_B.size[0]), 6),
                                                   round(float(ANSI_B.size[1]), 6))
        self.check("the set is on the set's paper", sizes[0] == want_set,
                   "%s != %s" % (sizes[0], want_set))
        self.check("C-102 is on ANSI B", sizes[1] == want_zone,
                   "%s != %s" % (sizes[1], want_zone))
        self.check("and the two are not the same paper", want_set != want_zone, want_set)

    def test_no_filesystem_path_reaches_the_drawing(self):
        """A drawn set must not depend on where the repository sits on disk.

           The compass was handed to drawImage() as a filename, and reportlab names the
           XObject it embeds by digesting what it is given: an ImageReader by its
           CONTENT, a filename by the FILENAME. So the absolute path of the checkout
           went into the PDF. Built from two directories, the same commit produced two
           different files -- different XObject names and different lengths -- which
           means the deliverable could not be reproduced from its own commit unless the
           repository sat where it was issued from.

           Stated as the general property rather than as 'the compass is an
           ImageReader', because the next asset would have the same problem and a test
           naming the compass would not notice."""
        dest = os.path.join(self.tmp, 'paths.txt')
        r = self.trace(dest, self.synth('asset.py', "from lib import assets; c.drawImage(assets.image('compass.png'), 20, 20, width=40, height=40, mask='auto')"))
        self.check("a build drawing a library image traces", r.returncode == 0, r.stderr[-300:])
        if r.returncode:
            return
        text = self.read(dest)
        bad = [ln for ln in text.splitlines()
               if re.search(r"['\"](?:/Users/|/home/|/var/|/tmp/|[A-Za-z]:\\\\)", ln)]
        self.check("no absolute path is recorded", not bad,
                   "%d record(s), first: %s" % (len(bad), bad[:1]))

    def test_an_image_is_recorded_by_its_content(self):
        """The other half: the trace has to be able to SEE an asset change. While images
           were passed as filenames it recorded the name, so swapping compass.png for a
           different picture left the trace identical -- an oracle blind to the thing it
           was being asked about."""
        dest = os.path.join(self.tmp, 'img.txt')
        r = self.trace(dest, self.synth('asset.py', "from lib import assets; c.drawImage(assets.image('compass.png'), 20, 20, width=40, height=40, mask='auto')"))
        if r.returncode:
            self.check("a build drawing a library image traces", False, r.stderr[-300:])
            return
        imgs = [ln for ln in self.read(dest).splitlines() if "'IMAGE'" in ln]
        self.check("some image is recorded", imgs, 'no IMAGE record in the trace')
        for ln in imgs:
            self.check("it carries a content digest",
                       re.search(r"'IMAGE', '[0-9a-f]{32}'", ln), ln[:120])

    def test_observers_get_the_object_not_the_arguments(self):
        """The tools learn which sheet is drawing by REGISTERING, not by replacing
           Sheet.__init__. That is what makes a new Sheet parameter harmless: an observer
           is handed the finished object and reads attributes off it.

           The old arrangement -- a wrapper restating `def _sh(self, c, no, title, scale,
           notes="")` -- is what `page=` broke, silently, for several commits."""
        sys.path.insert(0, HERE)
        from lib.draw import page
        seen = []
        class W:
            def sheet(s, sh): seen.append(sh)
        w = page.observe(W())
        pp = None
        try:
            sh = page.Sheet(None, "X-001", "t", "N/A", page=page.ANSI_B)
            self.check("the observer was told", len(seen) == 1)
            if seen:
                self.check("it got the Sheet itself", seen[0] is sh)
                # the parameter whose addition broke the DXF export reaches it for free
                self.check("including parameters it never named", seen[0].page is page.ANSI_B)
            # an observer that only wants plans must not be called for sheets, and vice versa
            class P:
                def plan(s, p): seen.append(p)
            pp = page.observe(P())
            page.Sheet(None, "X-002", "t", "N/A")
            self.check("a partial observer is not called for what it skips", len(seen) == 2)
        finally:
            page.unobserve(w)
            if pp is not None:
                page.unobserve(pp)
        # registering a class instead of an instance is the mistake that is easy to make
        try:
            page.observe(W); bad = False
        except AssertionError:
            bad = True
        finally:
            page.unobserve(W)
        self.check("observe() rejects a class", bad)


CONCURRENT = r'''
import os, re, sys, threading
sys.path.insert(0, %(HERE)r)
from lib import buildscript
from lib.draw import page

mod = buildscript.load(%(BUILD)r)
docs = buildscript.documents(mod)
tmp = %(TMP)r

def norm(b):
    """reportlab stamps a timestamp and a RANDOM /ID into every file, so two builds of
       the same drawing never match byte for byte. Everything else does, and the /ID is
       written as `/ID \n[<..><..>]` -- the newline is why an obvious regex misses it."""
    b = re.sub(rb'/CreationDate \([^)]*\)', b'/CreationDate ()', b)
    b = re.sub(rb'/ModDate \([^)]*\)', b'/ModDate ()', b)
    b = re.sub(rb'/ID\s*\[[^]]*\]', b'/ID []', b)
    return b

def build_all(tag, parallel):
    out, err, layers = {}, {}, {}
    def one(d):
        try:
            p = os.path.join(tmp, '%%s-%%s.pdf' %% (tag, d.__name__))
            d(p)
            with open(p, 'rb') as fh:
                out[d.__name__] = norm(fh.read())
        except BaseException as e:
            err[d.__name__] = '%%s: %%s' %% (type(e).__name__, e)
        # whatever this thread left behind: with a per-document layer there is nothing
        layers[d.__name__] = page.current_layer()
    if parallel:
        ts = [threading.Thread(target=one, args=(d,)) for d in docs]
        for t in ts: t.start()
        for t in ts: t.join()
    else:
        for d in docs: one(d)
    return out, err, layers

seq, seq_err, seq_lay = build_all('seq', False)
par, par_err, par_lay = build_all('par', True)

print('DOCS', len(docs))
print('ERR', sorted(seq_err.items()), sorted(par_err.items()))
print('SAME', sorted(n for n in seq if seq[n] == par.get(n)))
print('DIFF', sorted(n for n in seq if seq[n] != par.get(n)))
print('LAYERS', sorted(set(list(seq_lay.values()) + list(par_lay.values()))))
'''


class SidecarTests(HarnessTestCase):
    """--stdout and --by-sheet, which lib/verify/gate.py reads. The trace is the oracle
       the committed trace.md5 pins, so the first thing to prove is that asking for the
       sidecars leaves it byte-identical."""

    def run_with(self, build, *flags):
        dest = os.path.join(self.tmp, 'trace-%d.txt' % len(os.listdir(self.tmp)))
        r = subprocess.run([sys.executable, TRACE, dest, build] + list(flags),
                           capture_output=True, text=True, cwd=HERE)
        return r, dest

    def test_the_sidecars_leave_the_trace_alone(self):
        build = self.synth('plain.py')
        r1, bare = self.run_with(build)
        out, sheets = os.path.join(self.tmp, 'o.txt'), os.path.join(self.tmp, 's.txt')
        r2, full = self.run_with(build, '--stdout', out, '--by-sheet', sheets)
        self.check("both runs succeed", r1.returncode == 0 and r2.returncode == 0,
                   (r1.stderr + r2.stderr)[-300:])
        self.check("the trace is byte-identical", self.read(bare) == self.read(full))
        self.check("both sidecars are written", os.path.exists(out) and os.path.exists(sheets))

    def test_pdf_dir_keeps_the_pdfs_and_not_the_trace(self):
        build = self.synth('plain.py')
        pdfs = os.path.join(self.tmp, 'pdfs')
        r1, bare = self.run_with(build)
        r2, kept = self.run_with(build, '--pdf-dir', pdfs)
        self.check("both runs succeed", r1.returncode == 0 and r2.returncode == 0,
                   (r1.stderr + r2.stderr)[-300:])
        self.check("the trace is byte-identical", self.read(bare) == self.read(kept))
        self.check("the PDF is kept, numbered in write order",
                   os.listdir(pdfs) == ['00-build_set.pdf'] if os.path.isdir(pdfs) else False,
                   str(os.listdir(pdfs)) if os.path.isdir(pdfs) else 'no dir')

    def test_by_sheet_names_the_sheet_that_moved(self):
        a, b = os.path.join(self.tmp, 'a.s'), os.path.join(self.tmp, 'b.s')
        self.run_with(self.synth('plain.py'), '--by-sheet', a)
        # drawn after the loop, so it lands on the last sheet opened: X-002
        self.run_with(self.synth('more.py', "c.drawString(1, 1, 'extra')"), '--by-sheet', b)
        A = dict((ln.split('\t')[0], ln) for ln in self.read(a).splitlines())
        B = dict((ln.split('\t')[0], ln) for ln in self.read(b).splitlines())
        self.check("every sheet is listed", set(A) == {'(document)', 'X-001', 'X-002'}, str(A))
        self.check("X-001 did not move", A.get('X-001') == B.get('X-001'))
        self.check("X-002 moved", A.get('X-002') != B.get('X-002'))

    def test_stdout_is_captured_and_kept_on_failure(self):
        path = os.path.join(self.tmp, 'talks.py')
        with open(path, 'w') as fh:
            fh.write("def build_set(output_path=None, make_canvas=None):\n"
                     "    print('MODEL TABLE ROW')\n"
                     "    raise AssertionError('check failed')\n")
        out = os.path.join(self.tmp, 'o.txt')
        with open(out, 'w') as fh:
            fh.write('stale')
        r, dest = self.run_with(path, '--stdout', out)
        self.check("the failed build exits non-zero", r.returncode != 0)
        self.check("what it printed reaches stderr", 'MODEL TABLE ROW' in r.stderr, r.stderr[-300:])
        self.check("no stale stdout file survives", not os.path.exists(out))
        self.check("no trace survives", not os.path.exists(dest))


class ModelCheckTests(HarnessTestCase):
    """Every document checks the model before it draws, not just the set.

       C-102 is its own document and the only one that goes to the Board of Zoning
       Adjustment on its own, and for a long time it drew with nothing checked. It was
       never caught because DOCUMENTS lists build_set() first, so a full run happened to
       check before the zoning sheet drew -- the hole only opened for a tool rebuilding
       that one document, which is exactly what DOCUMENTS' per-document scratch path is
       for."""

    def run_py(self, src):
        return subprocess.run([sys.executable, '-c', src],
                              capture_output=True, text=True,
                              cwd=os.path.dirname(BUILD))

    def test_the_zoning_sheet_checks_the_model_first(self):
        """Compared against check_model()'s own output rather than a line quoted here:
           a check that is reworded or added stays covered, and this test cannot go
           stale against the report it is pinning."""
        self.require_build()
        want = self.run_py('import build; build.check_model()')
        self.check("check_model runs", want.returncode == 0, want.stderr[-400:])
        expected = [ln for ln in want.stdout.splitlines() if ln.strip()]
        self.check("check_model prints a report", len(expected) > 10, repr(expected[:3]))

        out = os.path.join(self.tmp, 'zoning.pdf')
        got = self.run_py('import build; build.build_zoning_sheet(%r)' % out)
        self.check("the zoning sheet builds alone", got.returncode == 0, got.stderr[-400:])
        printed = [ln for ln in got.stdout.splitlines() if ln.strip()]

        missing = [ln for ln in expected if ln not in printed]
        self.check("it printed every model check first", not missing,
                   "%d check line(s) never ran, first: %r" % (len(missing), missing[:1]))
        self.check("and it wrote its document", os.path.exists(out), out)

    def test_it_refuses_to_run_with_assertions_disabled(self):
        """Every model check in this project is an assert, so -O removes all of them at
           once. What made that dangerous was not the likelihood -- nobody types -O --
           but that the failure is total and reads as success: the report still prints
           in full, and pyflakes, the tests and the trace all stay green on a set built
           with nothing checked."""
        self.require_build()
        got = subprocess.run([sys.executable, '-O', '-c', 'import build; build.check_model()'],
                             capture_output=True, text=True, cwd=os.path.dirname(BUILD))
        self.check("it refuses", got.returncode != 0, got.stdout[-300:])
        said = got.stdout + got.stderr
        self.check("it says why", '-O' in said, said[-300:])

        ok = subprocess.run([sys.executable, '-c', 'import build; build.check_model()'],
                            capture_output=True, text=True, cwd=os.path.dirname(BUILD))
        self.check("and without -O it still checks", ok.returncode == 0, ok.stderr[-300:])

    def test_the_report_is_not_printed_twice_in_one_run(self):
        """Both documents call check_model(); the model is module-level and immutable,
           so the second call has nothing to check and must not print the report again.
           Build stdout is one of the oracles -- two copies of it would make every
           future diff of a failing run ambiguous about which document failed."""
        self.require_build()
        want = self.run_py('import build; build.check_model()')
        first = next((ln for ln in want.stdout.splitlines() if ln.strip()), None)
        self.check("there is a first check line", first is not None, repr(want.stdout[:200]))

        both = self.run_py(
            'import build, tempfile, os\n'
            'd = tempfile.mkdtemp()\n'
            'for doc in build.DOCUMENTS:\n'
            '    doc(os.path.join(d, doc.__name__ + ".pdf"))\n')
        self.check("both documents build", both.returncode == 0, both.stderr[-400:])
        if first is not None:
            self.check("the report printed once", both.stdout.count(first) == 1,
                       "%d copies of %r" % (both.stdout.count(first), first))


class BuildContextTests(HarnessTestCase):

    def test_two_documents_draw_at_once(self):
        """The claim the BuildContext makes, tested rather than asserted.

           A project can write two files -- a full set and an 11 x 17 zoning sheet. They used to be forced into single file because the canvas, the current
           layer, the observers and the title block were one module-level slot each.
           Building both at once had to raise; now it has to produce the same two files as
           building them one after the other.

           Run in a SUBPROCESS: it builds the real set four times and starts threads, and
           the other tests in this file should not inherit either."""
        self.require_build()
        src = CONCURRENT % {'HERE': HERE, 'BUILD': BUILD, 'TMP': self.tmp}
        r = subprocess.run([sys.executable, '-c', src], capture_output=True, text=True, cwd=HERE)
        self.check("the concurrent build runs", r.returncode == 0, r.stderr.strip()[-400:])
        if r.returncode:
            return
        got = dict(l.split(' ', 1) for l in r.stdout.strip().splitlines()
                   if l.split(' ', 1)[0] in ('DOCS', 'ERR', 'SAME', 'DIFF', 'LAYERS'))
        self.check("there is more than one document to overlap", got.get('DOCS') == '2',
                   got.get('DOCS', '?'))
        self.check("neither ordering raises", got.get('ERR') == '[] []', got.get('ERR', '?'))
        self.check("every document is byte-identical built concurrently",
                   got.get('DIFF') == '[]', "differed: " + got.get('DIFF', '?'))
        self.check("and there were documents to compare",
                   got.get('SAME') == "['build_set', 'build_zoning_sheet']", got.get('SAME', '?'))
        # A document that owns its layer leaves the process-level one untouched, so every
        # thread reads back the default. Under the old module-level CURLAYER this came back
        # as whatever sheet finished last.
        self.check("no document leaves its layer behind", got.get('LAYERS') == "['A-ANNO']",
                   got.get('LAYERS', '?'))


class DxfExportTests(HarnessTestCase):

    def test_dxf_export_runs(self):
        """End to end, on the real build. This is the test that would have caught the
           `_sh() got an unexpected keyword argument 'page'` break the moment it landed."""
        self.require_build()
        out = os.path.join(self.tmp, 'out.dxf')
        r = subprocess.run([sys.executable, DXF, BUILD, out],
                           capture_output=True, text=True, cwd=HERE)
        self.check("the exporter exits cleanly", r.returncode == 0, r.stderr.strip()[-300:])
        if r.returncode:
            return
        self.check("it writes a DXF", os.path.exists(out) and os.path.getsize(out) > 0,
                   "%d bytes" % (os.path.getsize(out) if os.path.exists(out) else 0))
        m = re.search(r"recorded (\d+) entities in (\d+) plan frames: (\[.*\])", r.stdout)
        self.check("it reports what it recorded", m is not None, r.stdout.strip()[-200:])
        # Which sheets a project frames, and how many entities, is that project's claim
        # (in projects/<slug>/verify/test_dxf_frames.py); a day-one project has none.

    def test_it_refuses_to_write_without_a_named_output(self):
        """A build script that defines no DXF_OUT, given no explicit output path either,
           used to derive one silently from its own path (build.py -> build.dxf) -- the
           exact shape *.dxf's own .gitignore rule swallows with no error, and the trap
           DXF_OUT exists to close. Every later project that forgets to define it
           must fail loudly instead, not write a file nothing tracked will ever see."""
        path = self.synth('nodxfout.py')            # SYNTH defines build_set, no DXF_OUT
        would_be = os.path.splitext(path)[0] + '.dxf'
        r = subprocess.run([sys.executable, DXF, path], capture_output=True, text=True,
                           cwd=HERE)
        self.check("it refuses", r.returncode != 0, "exit %d" % r.returncode)
        said = r.stdout + r.stderr
        self.check("it names DXF_OUT", 'DXF_OUT' in said, said[-400:])
        self.check("it names the explicit-path remedy too", 'lib/export/dxf.py' in said,
                   said[-400:])
        self.check("it wrote no DXF file", not os.path.exists(would_be), would_be)


if __name__ == '__main__':
    unittest.main(verbosity=2)
