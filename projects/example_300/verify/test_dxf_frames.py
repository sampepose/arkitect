"""300's DXF: every plan sheet framed, and a plausible number of entities.

Moved here from arkitect/lib/verify/test_trace.py in phase 1 of the public release. That the exporter
RUNS is the engine's claim (arkitect/lib/verify/test_dxf.py runs it on every project); WHICH sheets
300 frames, and how much it draws, is this project's."""
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BUILD = os.path.join(HERE, 'projects', 'example_300', 'build.py')
from arkitect.lib import workspace                                    # noqa: E402  the engine, wherever it is
DXF = os.path.join(workspace.ENGINE, 'arkitect', 'lib', 'export', 'dxf.py')

FRAMED = ['C-101', 'C-103', 'A-101', 'A-102', 'A-103', 'A-103', 'S-101', 'S-101', 'S-102', 'S-102',
          'S-103', 'S-103', 'S-104', 'S-104', 'S-104', 'S-104', 'M-101', 'M-101', 'M-102', 'M-102',
          'E-101', 'E-101', 'E-102', 'E-102', 'P-101', 'P-101', 'P-102', 'P-102', 'P-103', 'P-103']


class DxfFrameTests(unittest.TestCase):

    def test_every_plan_sheet_is_framed_with_a_plausible_drawing(self):
        with tempfile.TemporaryDirectory() as t:
            out = os.path.join(t, 'out.dxf')
            r = subprocess.run([sys.executable, DXF, BUILD, out], capture_output=True, text=True,
                               cwd=HERE)
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            self.assertGreater(os.path.getsize(out), 100000)
        m = re.search(r"recorded (\d+) entities in (\d+) plan frames: (\[.*\])", r.stdout)
        self.assertIsNotNone(m, r.stdout[-200:])
        self.assertEqual(eval(m.group(3)), FRAMED)
        self.assertGreater(int(m.group(1)), 2000)


if __name__ == '__main__':
    unittest.main()
