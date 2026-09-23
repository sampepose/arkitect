"""arkitect/lib/interface.py: every --json output leads with the same four keys, and the tools
docs/interface.md lists print it."""
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path: sys.path.insert(0, HERE)
from arkitect.lib import interface, workspace

FIRST = ['schema', 'kind', 'engine', 'workspace']


class EnvelopeTests(unittest.TestCase):

    def test_the_four_keys_come_first_and_cannot_be_overridden(self):
        e = interface.envelope('gate', {'ok': True, 'schema': 99, 'kind': 'x'}, ws='/w')
        self.assertEqual(list(e)[:4], FIRST)
        self.assertEqual((e['schema'], e['kind'], e['workspace'], e['ok']),
                         (interface.SCHEMA, 'gate', '/w', True))

    def test_the_engine_is_the_package_version(self):
        from arkitect import __version__
        self.assertEqual(interface.engine_version(), __version__)

    def test_the_document_states_the_schema_in_force(self):
        with open(os.path.join(HERE, 'docs', 'interface.md')) as fh:
            self.assertIn('now **%d**' % interface.SCHEMA, fh.read())


class ToolTests(unittest.TestCase):
    """Each tool, run as a person would, prints one object in the envelope."""

    def run_json(self, *args):
        env = dict(os.environ, PYTHONPATH=HERE)
        env.pop(workspace.ENV, None)
        r = subprocess.run([sys.executable, '-m', 'arkitect.harness.cli'] + list(args) + ['--json'],
                           cwd=HERE, capture_output=True, text=True, env=env, timeout=600)
        try:
            out = json.loads(r.stdout)
        except ValueError:
            self.fail('%s printed no JSON (exit %s): %s' % (args, r.returncode, (r.stdout + r.stderr)[-400:]))
        self.assertEqual(list(out)[:4], FIRST, args)
        self.assertEqual(out['workspace'], HERE)
        return out

    def test_progress(self):
        out = self.run_json('progress', 'status', 'example_100')
        self.assertEqual(out['kind'], 'progress')
        self.assertEqual(sum(out['counts'].values()), out['total'])

    def test_decisions(self):
        self.assertEqual(self.run_json('decisions', 'pending')['kind'], 'decisions')

    def test_review(self):
        self.assertEqual(self.run_json('review', 'list', 'example_100')['findings'], [])

    def test_every_kind_is_documented(self):
        with open(os.path.join(HERE, 'docs', 'interface.md')) as fh:
            doc = fh.read()
        for kind in ('gate', 'progress', 'decisions', 'review'):
            self.assertRegex(doc, r'## `%s`' % re.escape(kind))


if __name__ == '__main__':
    unittest.main()
