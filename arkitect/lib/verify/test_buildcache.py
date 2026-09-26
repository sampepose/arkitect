"""Tests for arkitect/lib/verify/buildcache.py and the recording trace.py keeps with it.

A kept recording stands in for a build, so every test here is about when it must NOT: an edit
the mtime cannot see, a build that fails, a part that fails, a build outside a workspace's
projects/, the switch that turns it off. The demo build appends to a log outside the workspace,
so a test counts the builds that actually ran.
"""
import os, shutil, subprocess, sys, tempfile, unittest
from unittest import mock

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, HERE)
from arkitect.lib.verify import buildcache, sheet_text

TRACE = os.path.join(HERE, 'arkitect', 'lib', 'verify', 'trace.py')
DXF = os.path.join(HERE, 'arkitect', 'lib', 'export', 'dxf.py')

BUILD = """
from reportlab.pdfgen import canvas
from arkitect.lib.draw.page import Sheet, PW, PH

def build_set(output_path=None, make_canvas=None):
    open(%(log)r, 'a').write('x')
    print('MODEL CHECK: ok')
    %(before)s
    c = (make_canvas or canvas.Canvas)(output_path or 'x.pdf', pagesize=(PW, PH))
    for no, text in (('X-001', %(one)r), ('X-002', 'TWO')):
        Sheet(c, no, 'synthetic', 'N/A')
        c.drawString(100, 100, text)
        c.showPage()
    c.save()
    return output_path

DOCUMENTS = (build_set,)
"""


class RecordingTests(unittest.TestCase):

    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.tmp = t.name
        self.ws = os.path.join(t.name, 'ws')
        self.log = os.path.join(t.name, 'builds.log')
        os.makedirs(os.path.join(self.ws, 'projects', 'demo'))
        self.build = os.path.join(self.ws, 'projects', 'demo', 'build.py')
        self.write(one='ONE')
        # recordings of its own, so every count here is this test's
        env = mock.patch.dict(os.environ, {'XDG_CACHE_HOME': os.path.join(t.name, 'cache')})
        env.start()
        self.addCleanup(env.stop)

    def write(self, **kw):
        with open(self.build, 'w') as fh:
            fh.write(BUILD % dict(dict(log=self.log, before='pass', one='ONE'), **kw))

    def env(self, **extra):
        env = dict(os.environ, PYTHONPATH=HERE)
        env.pop('ARKITECT_WORKSPACE', None)
        env.pop('ARKITECT_BUILD_CACHE', None)
        env.update(extra)
        return env

    def trace(self, *flags, build=None, **env):
        out = os.path.join(self.tmp, 'trace.txt')
        r = subprocess.run([sys.executable, TRACE, out, build or self.build] + list(flags),
                           cwd=self.ws, capture_output=True, text=True, env=self.env(**env))
        text = None
        if os.path.exists(out):
            with open(out) as fh:
                text = fh.read()
        return r, text

    def builds(self):
        if not os.path.exists(self.log):
            return 0
        with open(self.log) as fh:
            return len(fh.read())

    def test_the_second_request_is_served_and_says_the_same(self):
        a, ta = self.trace()
        b, tb = self.trace()
        self.assertEqual((a.returncode, b.returncode), (0, 0), a.stderr + b.stderr)
        self.assertEqual(self.builds(), 1)
        self.assertEqual(ta, tb)
        self.assertEqual(a.stdout, b.stdout)

    def test_an_edit_of_the_same_size_and_mtime_is_built_again(self):
        _r, before = self.trace()
        st = os.stat(self.build)
        self.write(one='ONX')                                   # same length
        os.utime(self.build, ns=(st.st_atime_ns, st.st_mtime_ns))
        _r, after = self.trace()
        self.assertEqual(self.builds(), 2)
        self.assertIn("'ONX'", after)
        self.assertNotEqual(before, after)

    def test_a_build_that_fails_is_never_kept(self):
        self.write(before="raise AssertionError('the model check failed')")
        for _ in range(2):
            r, text = self.trace()
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('the model check failed', r.stderr)
            self.assertIsNone(text)
        self.assertEqual(self.builds(), 2)

    def test_a_part_that_fails_is_never_kept(self):
        # a DXF exporter that cannot import: the trace is good, the recording is not whole
        engine = os.path.join(self.tmp, 'engine')
        shutil.copytree(os.path.join(HERE, 'arkitect'), os.path.join(engine, 'arkitect'),
                        ignore=shutil.ignore_patterns('__pycache__'))
        with open(os.path.join(engine, 'arkitect', 'lib', 'export', 'dxf.py'), 'w') as fh:
            fh.write("raise SystemExit('exporter is broken')\n")
        tool = os.path.join(engine, 'arkitect', 'lib', 'verify', 'trace.py')
        for _ in range(2):
            out = os.path.join(self.tmp, 't.txt')
            r = subprocess.run([sys.executable, tool, out, self.build, '--dxf',
                                os.path.join(self.tmp, 'f.dxf')], cwd=self.ws, capture_output=True,
                               text=True, env=dict(self.env(), PYTHONPATH=engine))
            self.assertEqual(r.returncode, 3, r.stderr)
            self.assertIn('exporter is broken', open(os.path.join(self.tmp, 'f.dxf.err')).read())
        self.assertEqual(self.builds(), 2)

    def test_a_build_outside_a_workspaces_projects_is_never_kept(self):
        loose = os.path.join(self.tmp, 'loose.py')
        shutil.copyfile(self.build, loose)
        for _ in range(2):
            r, _t = self.trace(build=loose)
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.builds(), 2)

    def test_the_switch_turns_it_off(self):
        for _ in range(2):
            r, _t = self.trace(ARKITECT_BUILD_CACHE='off')
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.builds(), 2)

    def test_every_part_served_is_the_part_built(self):
        parts = lambda d: ['--stdout', os.path.join(d, 'stdout.txt'), '--by-sheet',
                           os.path.join(d, 'sheets.txt'), '--text', os.path.join(d, 'text.json'),
                           '--pages', os.path.join(d, 'pages.json')]
        built, served = os.path.join(self.tmp, 'built'), os.path.join(self.tmp, 'served')
        os.makedirs(built)
        os.makedirs(served)
        a, ta = self.trace(*parts(built), ARKITECT_BUILD_CACHE='off')
        self.trace()                                           # records it
        b, tb = self.trace(*parts(served))
        self.assertEqual(self.builds(), 2)
        self.assertEqual(ta, tb)
        for f in ('stdout.txt', 'sheets.txt', 'text.json', 'pages.json'):
            with open(os.path.join(built, f)) as x, open(os.path.join(served, f)) as y:
                self.assertEqual(x.read(), y.read(), f)

    def test_sheet_text_recorded_is_read(self):
        prev = os.getcwd()
        os.chdir(self.ws)
        self.addCleanup(os.chdir, prev)
        want = sheet_text.read(self.build)
        self.assertEqual(sheet_text.recorded(self.build), want)
        self.assertEqual(sheet_text.recorded(self.build), want)      # served, the same

    def test_a_copy_of_the_tree_elsewhere_is_served_its_recording(self):
        _r, a = self.trace()
        copy = os.path.join(self.tmp, 'elsewhere', 'ws')
        shutil.copytree(self.ws, copy)
        out = os.path.join(self.tmp, 'copy.txt')
        r = subprocess.run([sys.executable, TRACE, out, os.path.join(copy, 'projects', 'demo', 'build.py')],
                           cwd=copy, capture_output=True, text=True, env=self.env())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.builds(), 1)
        with open(out) as fh:
            self.assertEqual(fh.read(), a)

    def test_a_build_that_prints_where_it_is_is_never_kept(self):
        self.write(before='print(__file__)')
        for _ in range(2):
            r, _t = self.trace()
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.builds(), 2)

    def test_what_pythonpath_adds_is_in_the_key(self):
        extra = os.path.join(self.tmp, 'extra')
        os.makedirs(extra)
        with open(os.path.join(extra, 'helper.py'), 'w') as fh:
            fh.write('WORD = 1\n')
        path = os.pathsep.join([HERE, extra])
        self.trace(PYTHONPATH=path)
        self.trace(PYTHONPATH=path)
        self.assertEqual(self.builds(), 1)
        with open(os.path.join(extra, 'helper.py'), 'w') as fh:
            fh.write('WORD = 2\n')
        self.trace(PYTHONPATH=path)
        self.assertEqual(self.builds(), 2)

    def test_the_key_is_content(self):
        k = buildcache.key(self.build, HERE, self.ws)
        self.assertEqual(buildcache.key(self.build, HERE, self.ws), k)
        with open(os.path.join(self.ws, 'notes.txt'), 'w') as fh:    # any file the build could read
            fh.write('x')
        self.assertNotEqual(buildcache.key(self.build, HERE, self.ws), k)
        with open(os.path.join(self.ws, 'x.pdf'), 'w') as fh:         # an output it never reads
            fh.write('x')
        k2 = buildcache.key(self.build, HERE, self.ws)
        with open(os.path.join(self.ws, 'x.pdf'), 'w') as fh:
            fh.write('y')
        self.assertEqual(buildcache.key(self.build, HERE, self.ws), k2)


if __name__ == '__main__':
    unittest.main()
