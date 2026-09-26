"""Every project's DXF export actually runs.

The exporter is the one deliverable nothing else touches: the trace records a build's
canvas calls and stays green whether or not arkitect/lib/export/dxf.py can write a file, the sheet
tests read strings, and pyflakes reads imports. CLAUDE.md records the exporter being dead
for several commits for exactly that reason, and it happened again -- a project's ducted Unit 1
put its supply registers on M-HVAC-DUCT, no colour was declared for that layer, and the
exporter's own assert stopped it writing anything at all. Nothing said so, because nothing
ran it.

So run it, once per project, as a subprocess to a scratch path -- dxf.py does its work at
module scope, and a second import in one process would not repeat it. Exit status and
stderr are both read: `dxf.py >/dev/null 2>&1 && echo rebuilt` is the false green this
repository has already produced once.
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EXPORT = os.path.join(HERE, 'arkitect', 'lib', 'export', 'dxf.py')
PROJECTS = sorted(d for d in os.listdir(os.path.join(HERE, 'projects'))
                  if os.path.isfile(os.path.join(HERE, 'projects', d, 'build.py')))


class DxfExportTests(unittest.TestCase):

    def _export(self, project):
        build = os.path.join(HERE, 'projects', project, 'build.py')
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, project+'.dxf')
            r = subprocess.run([sys.executable, EXPORT, build, out],
                               capture_output=True, text=True, cwd=HERE)
            self.assertEqual(r.returncode, 0,
                             '%s DXF export failed:\n%s' % (project, r.stderr[-600:]))
            self.assertTrue(os.path.exists(out), '%s DXF wrote no file' % project)
            return os.path.getsize(out)

    def test_every_project_here_exports_its_dxf(self):
        self.assertTrue(PROJECTS, 'no project to export')
        # each export is its own process: run them at once, then read every one
        import concurrent.futures as cf
        with cf.ThreadPoolExecutor(len(PROJECTS)) as pool:
            runs = dict(zip(PROJECTS, pool.map(self._export, PROJECTS)))
        for p in PROJECTS:
            with self.subTest(p):
                self.assertGreater(runs[p], 0)

    def test_every_layer_a_symbol_uses_has_a_colour(self):
        """The assert above only fires for a layer some project actually DRAWS. A symbol
           added for a sheet neither project draws yet would still land in the DXF the day
           it is used, so hold the whole symbol vocabulary to the colour table."""
        sys.path.insert(0, HERE)
        from arkitect.lib.symbols import mechanical
        import re
        with open(EXPORT) as f:
            colors = set(re.findall(r"'([A-Z]-[A-Z0-9-]+)':", f.read()))
        for kind, layer in sorted(mechanical.LAYER.items()):
            self.assertIn(layer, colors,
                          "symbol %r draws on %s, which arkitect/lib/export/dxf.py gives no colour"
                          % (kind, layer))


if __name__ == '__main__':
    unittest.main()
