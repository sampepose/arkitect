"""The local web UI's server: its reads answer from the workspace's own tools, its writes refuse
what the CLI would refuse, and nothing reaches it from another origin.

Runs against a scratch copy of the engine's own workspace (its example projects), with the cache
in a scratch directory, so no test writes into the checkout or ~/.cache.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arkitect.web import server                        # noqa: E402


def _copy_workspace(dest):
    """A git repository holding a copy of the engine's example projects: a workspace."""
    shutil.copytree(os.path.join(HERE, 'projects'), os.path.join(dest, 'projects'),
                    ignore=shutil.ignore_patterns('__pycache__', '*.pdf', '*.dxf'))
    with open(os.path.join(dest, '.gitignore'), 'w') as fh:     # as a workspace's own does
        fh.write('__pycache__/\n*.pyc\n')
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@example.com',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@example.com')
    for args in (['init', '-q'], ['add', '.gitignore', 'projects'], ['commit', '-q', '-m', 'the examples']):
        subprocess.run(['git'] + args, cwd=dest, check=True, env=env, capture_output=True)
    return env


@unittest.skipUnless(shutil.which('git'), 'needs git')
class ServerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.t = tempfile.mkdtemp(prefix='arkitect-web-')
        cls.ws = os.path.join(cls.t, 'ws')
        os.makedirs(cls.ws)
        cls.env = _copy_workspace(cls.ws)
        cls.keep = {k: os.environ.get(k) for k in ('GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL',
                                                   'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL')}
        os.environ.update({k: cls.env[k] for k in cls.keep})
        cls.srv = server.make_server(cls.ws, port=0, cache=os.path.join(cls.t, 'cache'))
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = 'http://127.0.0.1:%d' % cls.srv.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        for k, v in cls.keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(cls.t, True)

    def call(self, path, body=None, headers=None):
        data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        h = {'Content-Type': 'application/json'} if body is not None else {}
        h.update(headers or {})
        req = urllib.request.Request(self.base + path, data=data, headers=h,
                                     method='POST' if body is not None else 'GET')
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.status, r.read(), r.headers.get('Content-Type', '')
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers.get('Content-Type', '')

    def js(self, path, body=None, headers=None):
        code, raw, _ = self.call(path, body, headers)
        return code, json.loads(raw)

    # -- reads

    def test_the_page_and_its_assets_are_served(self):
        code, raw, ctype = self.call('/')
        self.assertEqual(code, 200)
        self.assertIn(b'/app.js', raw)
        for asset in ('/app.js', '/app.css'):
            self.assertEqual(self.call(asset)[0], 200, asset)

    def test_a_path_out_of_the_static_directory_is_not_served(self):
        code, raw, _ = self.call('/../server.py')
        self.assertNotIn(b'ThreadingHTTPServer', raw)

    def test_the_workspace_lists_its_projects_and_its_history(self):
        code, ws = self.js('/api/workspace')
        self.assertEqual(code, 200)
        self.assertEqual(os.path.realpath(ws['workspace']), os.path.realpath(self.ws))
        self.assertIn('example_100', [p['slug'] for p in ws['projects']])
        self.assertEqual(ws['commits'][0]['subject'], 'the examples')
        self.assertEqual(ws['changed'], [])
        self.assertIsNone(ws['gate'])                  # nothing has run the gate from here

    def test_a_projects_sheet_index_is_its_builds_own(self):
        code, p = self.js('/api/projects/example_100')
        self.assertEqual(code, 200, p)
        nos = [s['no'] for s in p['sheets']]
        self.assertIn('G-001', nos)
        self.assertTrue(all(s['title'] and s['doc'] for s in p['sheets']))
        self.assertTrue(p['address'])
        again = self.js('/api/projects/example_100')[1]
        self.assertEqual(again['key'], p['key'])       # cached for the same tree

    def test_the_index_is_a_subprocess_of_its_own(self):
        # never in this process: a project's `src` would stay in sys.modules for every later test
        r = subprocess.run([sys.executable, '-m', 'arkitect.web.index', 'projects/example_100/build.py'],
                           cwd=self.ws, capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(r.returncode, 0, r.stderr)
        ix = json.loads(r.stdout)
        self.assertEqual(ix['sheets'][0]['page'], 1)
        self.assertEqual(len({s['no'] for s in ix['sheets']}), len(ix['sheets']))

    def test_the_decisions_are_the_ledgers_json(self):
        code, d = self.js('/api/decisions')
        self.assertEqual(code, 200)
        self.assertEqual(d['kind'], 'decisions')

    def test_an_unknown_project_or_route_is_404(self):
        self.assertEqual(self.call('/api/projects/nowhere_1')[0], 404)
        self.assertEqual(self.call('/api/projects/example_100/sheet/../../x.png')[0], 404)
        self.assertEqual(self.call('/api/nothing')[0], 404)

    # -- writes

    def test_a_write_must_be_json_from_this_origin(self):
        code, _raw, _ = self.call('/api/gate', body=b'full=1', headers={'Content-Type': 'application/x-www-form-urlencoded'})
        self.assertEqual(code, 403)
        code, _ = self.js('/api/gate', {}, headers={'Origin': 'https://elsewhere.example'})
        self.assertEqual(code, 403)

    def test_a_confirmation_needs_words_and_a_discard_a_changed_path(self):
        code, r = self.js('/api/decisions/D-001/confirm', {'quote': '  '})
        self.assertEqual(code, 400)
        self.assertIn('your words', r['error'])
        code, r = self.js('/api/discard', {'paths': ['projects/example_100/build.py']})
        self.assertEqual(code, 400)                    # nothing changed: nothing to discard
        code, r = self.js('/api/accept', {'message': 'x', 'paths': [], 'looked': False})
        self.assertEqual(code, 400)
        self.assertIn('looked', r['error'])

    def test_a_discard_restores_a_changed_tracked_file(self):
        p = os.path.join(self.ws, 'projects', 'example_100', 'intake.json')
        with open(p) as fh:
            before = fh.read()
        with open(p, 'a') as fh:
            fh.write('\n')
        code, r = self.js('/api/discard', {'paths': ['projects/example_100/intake.json']})
        self.assertEqual(code, 200, r)
        with open(p) as fh:
            self.assertEqual(fh.read(), before)


class CacheTests(unittest.TestCase):

    def test_the_cache_is_outside_the_workspace(self):
        root = server.cache_root('/some/where/my-projects', home='/home/x')
        self.assertTrue(root.startswith('/home/x/.cache/arkitect/web/my-projects-'))


if __name__ == '__main__':
    unittest.main()
