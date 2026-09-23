"""arkitect/harness/engine.py writes the one-line .pth that makes the engine importable elsewhere."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from arkitect.harness import engine
from arkitect.lib import workspace


class LinkTests(unittest.TestCase):

    def setUp(self):
        self.site = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.site, True)

    def test_link_names_this_engine_and_unlink_takes_it_away(self):
        self.assertIsNone(engine.linked(self.site))
        engine.link(user_site=os.path.join(self.site, 'deep'))
        self.assertEqual(engine.linked(os.path.join(self.site, 'deep')), workspace.ENGINE)
        engine.unlink(os.path.join(self.site, 'deep'))
        self.assertIsNone(engine.linked(os.path.join(self.site, 'deep')))

    def test_python_reads_the_line_as_a_path(self):
        engine.link(user_site=self.site)
        code = 'import site, sys; site.addsitedir(%r); import arkitect.lib; print(arkitect.lib.__file__)' % self.site
        r = subprocess.run([sys.executable, '-S', '-c', code], cwd=self.site,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.strip().startswith(workspace.ENGINE))


if __name__ == '__main__':
    unittest.main()
