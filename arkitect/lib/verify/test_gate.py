"""Tests for arkitect/lib/verify/gate.py, on throwaway repositories rather than either project.

The gate's whole claim is that it cannot report a green it did not earn, so most of
these break something on purpose and check the gate says so: a build that raises, a DXF
exporter that exits 1, a drawing that moved under an old trace.md5, a citation a sheet
stopped printing. Each test makes a git repository in a temporary directory holding a
copy of arkitect/lib/ and one synthetic two-sheet project, commits it as the base, and runs that
copy's gate.py -- the gate measures the tree it sits in.
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, HERE)
from arkitect.lib.verify import gate


BUILD = """
from reportlab.pdfgen import canvas
from arkitect.lib.draw.page import Sheet, PW, PH

def build_set(output_path=None, make_canvas=None):
    print('MODEL CHECK: %(printed)s')
    %(before)s
    c = (make_canvas or canvas.Canvas)(output_path or 'x.pdf', pagesize=(PW, PH))
    for no, text in (('X-001', %(one)r), ('X-002', %(two)r)):
        Sheet(c, no, 'synthetic', 'N/A')
        c.drawString(100, 100, text)
        c.showPage()
    c.save()
    return output_path

DOCUMENTS = (build_set,)
"""
PLAIN = dict(printed='ok', before='pass', one='SEE RCO 311.3', two='TWO')


_TEMPLATE = []


class GateTestCase(unittest.TestCase):
    """Each test gets its own copy of one committed repository: arkitect/lib/, the demo
       project, its accepted trace.md5, and the base the gate filed for that commit. The
       first test in a process builds it (an accept and a gate run are a second of
       processes); the rest copy it, .git and all, without its bytecode. The copy's base is
       the template's own commit measured by the same tools, the cache's key, so a test
       that changes either gets a base of its own; one that needs none cached deletes it."""

    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = os.path.join(t.name, 'repo')
        if not _TEMPLATE:
            keep = tempfile.mkdtemp(prefix='gate-template-')
            import atexit
            atexit.register(shutil.rmtree, keep, True)
            built, self.root = self.root, os.path.join(keep, 'repo')
            self.build_template()
            _TEMPLATE.append(self.root)
            self.root = built
        shutil.copytree(_TEMPLATE[0], self.root, symlinks=True,
                        ignore=shutil.ignore_patterns('__pycache__'))

    def build_template(self):
        shutil.copytree(os.path.join(HERE, 'arkitect', 'lib'), os.path.join(self.root, 'arkitect', 'lib'),
                        ignore=shutil.ignore_patterns('__pycache__', '.DS_Store'))
        os.makedirs(os.path.join(self.root, 'projects', 'demo'))
        self.write_build(**PLAIN)
        with open(os.path.join(self.root, '.gitignore'), 'w') as fh:
            fh.write('.verify-cache/\n__pycache__/\n')
        self.git('init', '-q')
        self.accept_quietly()
        self.commit('base')
        code, r = self.report()                  # clean at its commit: files that base
        self.assertEqual(code, 0, r['failures'] + r['errors'])

    def git(self, *args):
        r = subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t'] + list(args),
                           cwd=self.root, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def commit(self, msg):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', msg)

    def write_build(self, **kw):
        with open(os.path.join(self.root, 'projects', 'demo', 'build.py'), 'w') as fh:
            fh.write(BUILD % dict(PLAIN, **kw))

    def run_gate(self, *args):
        r = subprocess.run([sys.executable, os.path.join(self.root, 'arkitect', 'lib', 'verify', 'gate.py')]
                           + list(args), cwd=self.root, capture_output=True, text=True)
        return r

    def report(self, *args):
        r = self.run_gate('--json', *args)
        try:
            return r.returncode, json.loads(r.stdout)
        except ValueError:
            self.fail('no JSON (exit %s): %s' % (r.returncode, (r.stdout + r.stderr)[-600:]))

    def accept_quietly(self):
        # the first accept has no base commit yet; it must still write the digest
        r = self.run_gate('accept')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class GateTests(GateTestCase):

    def test_a_clean_tree_passes(self):
        code, r = self.report()
        self.assertEqual(code, 0, r['failures'] + r['errors'])
        self.assertTrue(r['ok'])
        self.assertEqual(r['projects']['demo']['sheets_moved'], [])
        self.assertEqual(r['projects']['demo']['stdout_diff'], '')

    def test_a_moved_drawing_fails_until_accepted_and_names_its_sheet(self):
        self.write_build(two='TWO, CHANGED')
        code, r = self.report()
        self.assertEqual(code, 1)
        self.assertEqual([m['sheet'] for m in r['projects']['demo']['sheets_moved']], ['X-002'])
        self.assertTrue(any('X-002' in f and 'accept' in f for f in r['failures']), r['failures'])
        a = self.run_gate('accept')
        self.assertEqual(a.returncode, 0, a.stderr)
        self.assertIn('Sheets moved: demo X-002', a.stdout)
        code, r = self.report()
        self.assertEqual(code, 0, r['failures'] + r['errors'])

    def test_a_build_that_raises_fails_and_says_why(self):
        self.write_build(before="raise AssertionError('the model check failed')")
        code, r = self.report()
        self.assertEqual(code, 1)
        self.assertTrue(any('the model check failed' in f for f in r['failures']), r['failures'])

    def test_accept_writes_nothing_for_a_build_that_raises(self):
        md5 = os.path.join(self.root, 'projects', 'demo', 'trace.md5')
        before = gate._read(md5)
        self.write_build(before="raise RuntimeError('broken')")
        a = self.run_gate('accept')
        self.assertNotEqual(a.returncode, 0)
        self.assertEqual(gate._read(md5), before)

    def test_a_missing_digest_fails(self):
        os.remove(os.path.join(self.root, 'projects', 'demo', 'trace.md5'))
        code, r = self.report()
        self.assertEqual(code, 1)
        self.assertTrue(any('no trace.md5' in f for f in r['failures']), r['failures'])

    def test_a_dead_dxf_exporter_fails(self):
        with open(os.path.join(self.root, 'arkitect', 'lib', 'export', 'dxf.py'), 'w') as fh:
            fh.write("import sys\nsys.exit('exporter is broken')\n")
        code, r = self.report()
        self.assertEqual(code, 1)
        self.assertFalse(r['projects']['demo']['dxf']['ok'])
        self.assertIn('exporter is broken', r['projects']['demo']['dxf']['stderr'])

    def test_a_dxf_that_cannot_be_written_fails_alone(self):
        # the exporter records the build and then refuses to write, as its layer-colour
        # assert does: the one build still measured the trace, and only the DXF fails
        with open(os.path.join(self.root, 'arkitect', 'lib', 'export', 'dxf.py'), 'w') as fh:
            fh.write("class Proxy:\n"
                     "    def __init__(s, real): s._r = real\n"
                     "    def __getattr__(s, n): return getattr(s._r, n)\n"
                     "def write(out):\n"
                     "    raise AssertionError('a layer with no colour')\n")
        code, r = self.report()
        self.assertEqual(code, 1)
        demo = r['projects']['demo']
        self.assertTrue(demo['trace']['ok'])
        self.assertEqual(demo['trace']['digest'], demo['trace']['committed'])
        self.assertFalse(demo['dxf']['ok'])
        self.assertIn('a layer with no colour', demo['dxf']['stderr'])
        self.assertTrue(any('DXF exporter failed' in f for f in r['failures']), r['failures'])

    def test_a_citation_no_sheet_prints_any_more_is_listed(self):
        self.write_build(one='SEE X-002')
        _code, r = self.report()
        self.assertIn('RCO 311.3', r['projects']['demo']['vocab_lost'])

    def test_a_printed_figure_that_changes_is_a_diff(self):
        self.write_build(printed='changed')
        self.run_gate('accept')                  # the drawing did not move; nothing to write
        code, r = self.report()
        self.assertEqual(code, 0, r['failures'] + r['errors'])
        self.assertIn('+MODEL CHECK: changed', r['projects']['demo']['stdout_diff'])
        code, r = self.report('--expect-unchanged')
        self.assertEqual(code, 1)

    def test_pyflakes_finds_what_an_edit_adds_to_a_file_it_passed_before(self):
        # the gate keeps pyflakes' clean verdicts by content: the same file edited is new bytes
        code, r = self.report()
        self.assertEqual(code, 0, r['failures'] + r['errors'])
        self.assertTrue(r['pyflakes']['ok'])
        self.write_build(before='import os')
        code, r = self.report()
        self.assertEqual(code, 1)
        self.assertFalse(r['pyflakes']['ok'])
        self.assertIn("'os' imported but unused", r['pyflakes']['output'])
        self.assertIn('build.py', r['pyflakes']['output'])
        # flagged once is never kept as clean: the same bytes are flagged again
        self.assertIn("'os' imported but unused", self.report()[1]['pyflakes']['output'])

    def test_expect_unchanged_fails_on_a_moved_sheet_even_when_accepted(self):
        self.write_build(one='SEE RCO 311.3 NOW')
        self.run_gate('accept')
        code, _r = self.report('--expect-unchanged')
        self.assertEqual(code, 1)

    def test_a_sheet_text_finding_fails(self):
        self.write_build(two='SEE X-009')             # a sheet the build never draws
        self.run_gate('accept')
        code, r = self.report()
        self.assertEqual(code, 1)
        self.assertTrue(any('X-009' in f for f in r['failures']), r['failures'])

    def test_a_sheet_printing_a_decision_id_fails(self):
        self.write_build(two='PER D-912')                 # internal vocabulary on a sheet
        self.run_gate('accept')
        code, r = self.report()
        self.assertEqual(code, 1)
        self.assertTrue(any('D-912 on X-002' in f for f in r['failures']), r['failures'])
        self.write_build(two='DOOR D-4A')                 # a door mark is not a decision id
        self.run_gate('accept')
        self.assertEqual(self.report()[0], 0)

    def builds_logged_by(self, untracked=None):
        """How many times the demo build ran during one gate run: it appends to a log
           outside the checkout, so the log leaves the tree clean."""
        log = os.path.join(os.path.dirname(self.root), 'builds.log')
        self.write_build(before='open(%r, "a").write("x")' % log)
        self.accept_quietly()
        self.commit('logs its builds')
        if untracked:
            open(os.path.join(self.root, untracked), 'w').close()
        shutil.rmtree(os.path.join(self.root, '.verify-cache'), ignore_errors=True)
        open(log, 'w').close()
        code, r = self.report()
        self.assertEqual(code, 0, r['failures'] + r['errors'])
        return len(gate._read(log)), r

    def test_a_clean_checkout_is_its_own_base(self):
        # one build serves the trace, sheet_text and the DXF exporter; the base is not built
        n, r = self.builds_logged_by()
        self.assertEqual(n, 1)
        self.assertEqual(r['projects']['demo']['sheets_moved'], [])
        # and what it filed is the base the next, dirty, run is measured against
        self.write_build(two='TWO, CHANGED', before='pass')
        code, r = self.report()
        self.assertEqual(code, 1)
        self.assertEqual([m['sheet'] for m in r['projects']['demo']['sheets_moved']], ['X-002'])

    def test_a_dirty_checkout_builds_its_base(self):
        # the current tree once, and the base once for its trace and sheet_text together
        n, _r = self.builds_logged_by(untracked='untracked.txt')
        self.assertEqual(n, 2)

    def test_an_export_attribute_builds_the_base(self):
        # export-ignore makes `git archive` differ from the checkout: no project at the base
        with open(os.path.join(self.root, '.gitattributes'), 'w') as fh:
            fh.write('projects/demo/build.py export-ignore\n')
        n, r = self.builds_logged_by()
        self.assertEqual(n, 1)
        self.assertTrue(r['projects']['demo']['new_at_base'])

    def test_an_edit_of_the_same_size_and_mtime_is_measured(self):
        # the gate's bytecode cache outlives a run; a timestamp pyc would run the old build
        build = os.path.join(self.root, 'projects', 'demo', 'build.py')
        self.assertEqual(self.report()[0], 0)
        st = os.stat(build)
        self.write_build(two='TWX')
        os.utime(build, ns=(st.st_atime_ns, st.st_mtime_ns))
        code, r = self.report()
        self.assertEqual(code, 1)
        self.assertEqual([m['sheet'] for m in r['projects']['demo']['sheets_moved']], ['X-002'])

    def test_an_unknown_base_is_an_error_not_a_pass(self):
        code, r = self.report('--base', 'no-such-ref')
        self.assertEqual(code, 2)
        self.assertTrue(r['errors'])

    def test_no_project_is_an_error_not_a_pass(self):
        shutil.rmtree(os.path.join(self.root, 'projects', 'demo'))
        code, r = self.report()
        self.assertEqual(code, 2)
        self.assertIn('no project was measured', r['errors'])


class RenderTests(GateTestCase):

    def test_render_names_its_files_by_sheet_outside_the_checkout(self):
        out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, out, True)
        r = self.run_gate('render', '--sheets', 'X-002', '--out', out, '--dpi', '20')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(os.listdir(os.path.join(out, 'demo'))), ['X-002.pdf', 'X-002.png'])

    def test_render_refuses_the_checkout(self):
        r = self.run_gate('render', '--out', os.path.join(self.root, 'renders'))
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.root, 'renders')))

    def test_render_moved_draws_both_sides(self):
        self.write_build(two='TWO, CHANGED')
        out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, out, True)
        r = self.run_gate('render', '--moved', '--out', out, '--dpi', '20')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(f for f in os.listdir(os.path.join(out, 'demo')) if f.endswith('.png')),
                         ['X-002.base.png', 'X-002.png'])


class UnitTests(unittest.TestCase):

    def test_moved_names_added_removed_and_changed(self):
        a = {'A': (1, 'x'), 'B': (2, 'y'), 'C': (3, 'z')}
        b = {'A': (1, 'x'), 'B': (2, 'Y'), 'D': (4, 'w')}
        self.assertEqual([(m['sheet'], m['change']) for m in gate.moved(a, b)],
                         [('B', 'changed'), ('C', 'removed'), ('D', 'added')])



class EngineVersionTests(GateTestCase):
    """trace.md5 records the engine that drew it; another engine is an upgrade proposed, never applied unseen."""

    def set_version(self, v):
        with open(os.path.join(self.root, 'arkitect', '__init__.py'), 'w') as fh:
            fh.write('__version__ = %r\n' % v)

    def digest_line(self):
        return gate._read(os.path.join(self.root, 'projects', 'demo', 'trace.md5')).split()

    def test_accept_records_the_engine_that_drew_it(self):
        self.set_version('1.0.0')
        self.accept_quietly()
        self.assertEqual(self.digest_line()[1:], ['engine=1.0.0'])

    def test_a_new_engine_that_moves_nothing_is_proposed_not_applied(self):
        self.set_version('1.0.0')
        self.accept_quietly()
        self.commit('pinned')
        self.set_version('1.1.0')
        code, rep = self.report()
        self.assertEqual(code, 0, rep['failures'] + rep['errors'])
        self.assertEqual(rep['projects']['demo']['engine'],
                         {'recorded': '1.0.0', 'running': '1.1.0', 'upgrade': 'proposed'})
        self.assertEqual(self.digest_line()[1:], ['engine=1.0.0'])       # nothing written unseen
        self.accept_quietly()
        self.assertEqual(self.digest_line()[1:], ['engine=1.1.0'])

    def test_a_new_engine_that_moves_a_sheet_says_so(self):
        self.set_version('1.0.0')
        self.accept_quietly()
        self.commit('pinned')
        self.set_version('1.1.0')
        self.write_build(two='THREE')
        code, rep = self.report()
        self.assertEqual(code, 1)
        self.assertTrue(any('under engine 1.1.0, accepted under 1.0.0' in f for f in rep['failures']),
                        rep['failures'])

if __name__ == '__main__':
    unittest.main()
