"""The local web UI's server: the page, and a JSON API over the workspace's own tools.

    arkitect web [--port 8765] [--host 127.0.0.1] [--no-open]

Every route that reads runs a `--json` tool of the CLI (docs/interface.md) or reads a file the
workspace already holds; every route that writes runs the command a person would type -- `gate
accept`, `decisions set`, `review set`, `git commit` of named paths -- in the workspace, and
answers with what that command printed. Nothing a drawing depends on lives only here: the cache
is renders and indexes, rebuilt from the tree whenever it changes, and it lives OUTSIDE the
checkout (~/.cache/arkitect/web/), where `gate render` insists a render goes.

It binds to 127.0.0.1 and has no accounts: it is one person's, on their own machine (the hosted
service, docs/hosted-service.md, is where accounts and sandboxes come in).
"""
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from arkitect.lib import workspace

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
DPI = 100                               # a sheet in the viewer: 24" x 18" is 2400 x 1800 px
SLUG = re.compile(r'^[a-z][a-z0-9_]*$')
SHEET = re.compile(r'^[A-Z]{1,2}-\d{3}[A-Za-z]?$')
DID = re.compile(r'^D-\d{3,}$')
RID = re.compile(r'^R-\d{3,}$')
DELIVERABLE = re.compile(r'.+-(permit-set|zoning-site-plan)\.pdf$|.+-floor-plans\.dxf$')


# ---------------------------------------------------------------- running the tools

def _env(ws):
    return dict(os.environ, ARKITECT_WORKSPACE=ws, PYTHONDONTWRITEBYTECODE='1')


def tool(ws, *args, timeout=900):
    """(exit status, stdout, stderr) of `arkitect <args>`, run in the workspace."""
    r = subprocess.run([sys.executable, '-m', 'arkitect.harness.cli'] + list(args), cwd=ws,
                       env=_env(ws), capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def tool_json(ws, *args, timeout=900):
    """A --json tool's object, or a RuntimeError naming what it printed on stderr."""
    code, out, err = tool(ws, *args, timeout=timeout)
    try:
        return json.loads(out)
    except ValueError:
        raise RuntimeError('arkitect %s exited %d: %s' % (' '.join(args), code, (err or out)[-2000:]))


def git(ws, *args, check=True):
    r = subprocess.run(['git'] + list(args), cwd=ws, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError('git %s: %s' % (' '.join(args), (r.stderr or r.stdout).strip()))
    return r.stdout


def projects(ws):
    """Every project slug: a directory of projects/ with a build.py."""
    root = os.path.join(ws, 'projects')
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root)
                  if SLUG.match(d) and os.path.isfile(os.path.join(root, d, 'build.py')))


def changed(ws):
    """[{path, state}] for every path git reports changed, tracked or not."""
    out = []
    for ln in git(ws, 'status', '--porcelain', '--untracked-files=all').splitlines():
        if len(ln) > 3:
            out.append({'path': ln[3:].split(' -> ')[-1], 'state': ln[:2].strip() or '?'})
    return out


def state_key(ws, slug=None):
    """What a cached index or render is valid for: the commit, the engine, and every change in
       the tree under the project (or the workspace) that is not committed yet."""
    from arkitect.lib import interface
    head = git(ws, 'rev-parse', 'HEAD', check=False).strip()
    where = ['projects/%s' % slug] if slug else []
    dirty = git(ws, 'status', '--porcelain', '--untracked-files=all', '--', *where, check=False)
    h = hashlib.sha1()
    h.update((head + (interface.engine_version() or '') + dirty).encode())
    for ln in dirty.splitlines():
        p = os.path.join(ws, ln[3:].split(' -> ')[-1])
        if os.path.isfile(p):
            with open(p, 'rb') as fh:
                h.update(hashlib.sha1(fh.read()).digest())
    return h.hexdigest()[:16]


# ---------------------------------------------------------------- the cache

def cache_root(ws, home=None):
    """~/.cache/arkitect/web/<workspace>: outside every checkout, one per workspace."""
    base = os.path.join(home, '.cache') if home else (
        os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~'), '.cache'))
    tag = hashlib.sha1(os.path.realpath(ws).encode()).hexdigest()[:10]
    return os.path.join(base, 'arkitect', 'web', '%s-%s' % (os.path.basename(os.path.realpath(ws)), tag))


class Cache:
    """Indexes and renders under cache_root(), keyed by state_key()."""

    def __init__(self, ws, root=None):
        self.ws = ws
        self.root = root or cache_root(ws)
        self.locks = {}
        self.guard = threading.Lock()

    def lock(self, name):
        with self.guard:
            return self.locks.setdefault(name, threading.Lock())

    def index(self, slug):
        """The project's sheet index (arkitect/web/index.py), built once per tree state."""
        key = state_key(self.ws, slug)
        path = os.path.join(self.root, slug, key, 'index.json')
        with self.lock('index:' + slug):
            if not os.path.exists(path):
                r = subprocess.run([sys.executable, '-m', 'arkitect.web.index',
                                    os.path.join('projects', slug, 'build.py')],
                                   cwd=self.ws, env=_env(self.ws), capture_output=True, text=True,
                                   timeout=900)
                if r.returncode != 0:
                    raise RuntimeError('%s does not build:\n%s' % (slug, r.stderr[-3000:]))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as fh:
                    fh.write(r.stdout)
        with open(path) as fh:
            return dict(json.load(fh), key=key)

    def renders(self, slug):
        """The directory holding every sheet of the project as <no>.png, rendering it once
           per tree state (one build, `gate render`)."""
        key = state_key(self.ws, slug)
        d = os.path.join(self.root, slug, key, 'sheets')
        with self.lock('render:' + slug):
            if not os.path.isdir(os.path.join(d, slug)):
                tmp = d + '.tmp'
                shutil.rmtree(tmp, ignore_errors=True)
                code, out, err = tool(self.ws, 'gate', 'render', '--project', slug,
                                      '--dpi', str(DPI), '--out', tmp)
                if code != 0:
                    raise RuntimeError('render %s exited %d:\n%s' % (slug, code, (err or out)[-3000:]))
                os.replace(tmp, d)
        return os.path.join(d, slug)

    def moved(self, slug):
        """The sheets that moved against HEAD, as <no>.png and <no>.base.png."""
        key = state_key(self.ws, slug)
        d = os.path.join(self.root, slug, key, 'moved')
        with self.lock('moved:' + slug):
            if not os.path.isdir(d):
                tmp = d + '.tmp'
                shutil.rmtree(tmp, ignore_errors=True)
                code, out, err = tool(self.ws, 'gate', 'render', '--moved', '--project', slug,
                                      '--dpi', str(DPI), '--out', tmp)
                if code != 0 and 'nothing to render' not in (out + err):
                    raise RuntimeError('render --moved %s exited %d:\n%s' % (slug, code, (err or out)[-3000:]))
                os.makedirs(tmp, exist_ok=True)
                os.replace(tmp, d)
        return os.path.join(d, slug)


# ---------------------------------------------------------------- jobs

class Jobs:
    """Long commands (the gate, a render) run on a thread; the page polls for the result."""

    def __init__(self):
        self.jobs = {}
        self.guard = threading.Lock()

    def start(self, kind, fn):
        jid = uuid.uuid4().hex[:12]
        job = {'id': jid, 'kind': kind, 'status': 'running', 'started': time.time(),
               'finished': None, 'result': None, 'error': None}
        with self.guard:
            self.jobs[jid] = job

        def run():
            try:
                job['result'] = fn()
                job['status'] = 'done'
            except Exception as exc:                  # a job's failure is its result, shown
                job['error'] = '%s: %s' % (exc.__class__.__name__, exc)
                job['status'] = 'failed'
            job['finished'] = time.time()
        threading.Thread(target=run, daemon=True).start()
        return job

    def get(self, jid):
        return self.jobs.get(jid)

    def running(self, kind):
        return next((j for j in self.jobs.values() if j['kind'] == kind and j['status'] == 'running'), None)


# ---------------------------------------------------------------- the API

class App:
    def __init__(self, ws, cache=None):
        self.ws = ws
        self.cache = Cache(ws, cache)
        self.jobs = Jobs()
        self.last_gate_path = os.path.join(self.cache.root, 'gate-latest.json')

    # -- reads

    def last_gate(self):
        if os.path.exists(self.last_gate_path):
            with open(self.last_gate_path) as fh:
                return json.load(fh)
        return None

    def workspace(self):
        from arkitect.lib import interface
        head = git(self.ws, 'rev-parse', '--short', 'HEAD', check=False).strip()
        branch = git(self.ws, 'rev-parse', '--abbrev-ref', 'HEAD', check=False).strip()
        dirty = changed(self.ws)
        out = []
        for slug in projects(self.ws):
            pdir = os.path.join(self.ws, 'projects', slug)
            digest = ''
            tp = os.path.join(pdir, 'trace.md5')
            if os.path.exists(tp):
                with open(tp) as fh:
                    digest = fh.read().split()[0] if fh else ''
            files = sorted(f for f in os.listdir(pdir) if DELIVERABLE.match(f))
            out.append({'slug': slug, 'digest': digest, 'deliverables': files,
                        'has_review': os.path.exists(os.path.join(pdir, 'review.json'))})
        return {'engine': interface.engine_version(), 'schema': interface.SCHEMA,
                'workspace': self.ws, 'branch': branch, 'head': head, 'changed': dirty,
                'designer': _designer(self.ws), 'projects': out, 'commits': self.commits(),
                'gate': self.last_gate()}

    def commits(self, n=12):
        raw = git(self.ws, 'log', '-%d' % n, '--format=%h%x1f%s%x1f%b%x1e', check=False)
        out = []
        for rec in raw.split('\x1e'):
            parts = rec.strip('\n').split('\x1f')
            if len(parts) < 3:
                continue
            sha, subj, body = parts
            m = re.search(r'Sheets moved:\s*(.+?)(?:\n\n|\Z)', body, re.S)
            out.append({'sha': sha, 'subject': subj,
                        'moved': ' '.join(m.group(1).split()) if m else None})
        return out

    def project(self, slug):
        idx = self.cache.index(slug)
        findings = self.review(slug)['findings'] if self.has_review(slug) else []
        by_sheet = {}
        for f in findings:
            by_sheet.setdefault(f['sheet'], []).append(f)
        for s in idx['sheets']:
            fs = by_sheet.get(s['no'], [])
            s['findings'] = len(fs)
            s['open'] = sum(1 for f in fs if f['status'] == 'open')
        return dict(idx, slug=slug, has_review=self.has_review(slug))

    def has_review(self, slug):
        return os.path.exists(os.path.join(self.ws, 'projects', slug, 'review.json'))

    def review(self, slug):
        return tool_json(self.ws, 'review', 'list', slug, '--json')

    def decisions(self, status=None, project=None):
        args = ['decisions', 'list', '--json']
        if status:
            args += ['--status', status]
        if project:
            args += ['--project', project]
        return tool_json(self.ws, *args)

    def decision(self, did):
        recs = tool_json(self.ws, 'decisions', 'show', did, '--json').get('decisions') or []
        if not recs:
            raise ValueError('no decision %s' % did)
        return recs[0]

    def about(self, path):
        return tool_json(self.ws, 'decisions', 'about', path, '--json')

    def sheet_decisions(self, slug, no):
        """The decisions about the modules that draw a sheet: every file of src/sheets/ that
           names the sheet's number, then `decisions about` for each, one record per id."""
        d = os.path.join(self.ws, 'projects', slug, 'src', 'sheets')
        mods = []
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if f.endswith('.py'):
                with open(os.path.join(d, f)) as fh:
                    text = fh.read()
                if re.search(r'''['"]%s['"]''' % re.escape(no), text):
                    mods.append('projects/%s/src/sheets/%s' % (slug, f))
        seen, out = set(), []
        for m in mods:
            for rec in self.about(m).get('decisions', []):
                if rec['id'] not in seen:
                    seen.add(rec['id'])
                    out.append(rec)
        return {'modules': mods, 'decisions': out}

    # -- jobs

    def run_gate(self, full=False):
        kind = 'gate-full' if full else 'gate'
        busy = self.jobs.running('gate') or self.jobs.running('gate-full')
        if busy:
            return busy

        def go():
            args = ['gate', '--json'] + (['--full'] if full else [])
            res = tool_json(self.ws, *args)
            res['ran_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
            res['tree'] = state_key(self.ws)
            os.makedirs(self.cache.root, exist_ok=True)
            with open(self.last_gate_path, 'w') as fh:
                json.dump(res, fh)
            return res
        return self.jobs.start(kind, go)

    def run_render(self, slug, moved=False):
        kind = ('moved:' if moved else 'render:') + slug
        return self.jobs.running(kind) or self.jobs.start(
            kind, lambda: {'dir': (self.cache.moved if moved else self.cache.renders)(slug)})

    # -- writes: each the command a person would type

    def accept(self, message, paths, looked):
        """`gate accept`, then a commit of the named paths and the digests it wrote."""
        if not looked:
            raise ValueError('say you looked at every moved sheet first')
        if not message.strip():
            raise ValueError('the commit message is empty')
        code, out, err = tool(self.ws, 'gate', 'accept')
        if code != 0:
            raise RuntimeError('gate accept exited %d:\n%s' % (code, (err or out)[-3000:]))
        now = {c['path'] for c in changed(self.ws)}
        digests = sorted(p for p in now if p.endswith('/trace.md5'))
        chosen = sorted(set(paths) | set(digests))
        stray = [p for p in chosen if p not in now]
        if stray:
            raise ValueError('not changed, so not committed: %s' % ', '.join(stray))
        git(self.ws, 'add', '--', *chosen)
        git(self.ws, 'commit', '-q', '-m', message)
        return {'accept': out.strip(), 'committed': chosen,
                'head': git(self.ws, 'rev-parse', '--short', 'HEAD').strip()}

    def discard(self, paths):
        """`git restore` of named tracked paths: the working-tree change to them is gone."""
        tracked = {c['path'] for c in changed(self.ws) if c['state'] != '??'}
        bad = [p for p in paths if p not in tracked]
        if bad or not paths:
            raise ValueError('only changed tracked paths can be discarded: %s' % ', '.join(bad or ['none']))
        git(self.ws, 'restore', '--staged', '--worktree', '--', *paths)
        return {'discarded': sorted(paths)}

    def confirm(self, did, quote):
        """`decisions set D-nnn confirmed --quote ...`, committed alone."""
        if not quote.strip():
            raise ValueError('a confirmation needs your words')
        code, out, err = tool(self.ws, 'decisions', 'set', did, 'confirmed', '--quote', quote)
        if code != 0:
            raise ValueError((err or out).strip())
        path = 'decisions/%s.md' % did
        git(self.ws, 'add', '--', path)
        title = self.decision(did).get('title', '')
        git(self.ws, 'commit', '-q', '-m', '%s confirmed: %s' % (did, title[:120]))
        return {'confirmed': did, 'printed': out.strip(),
                'head': git(self.ws, 'rev-parse', '--short', 'HEAD').strip()}

    def set_finding(self, slug, rid, status, note=None):
        """`review set <slug> R-nnn <status> [--note ...]`, committed alone."""
        args = ['review', 'set', slug, rid, status] + (['--note', note] if note else [])
        code, out, err = tool(self.ws, *args)
        if code != 0:
            raise ValueError((err or out).strip())
        path = 'projects/%s/review.json' % slug
        git(self.ws, 'add', '--', path)
        git(self.ws, 'commit', '-q', '-m', '%s %s: %s' % (slug, rid, status))
        return {'finding': rid, 'status': status, 'printed': out.strip(),
                'head': git(self.ws, 'rev-parse', '--short', 'HEAD').strip()}


def _designer(ws):
    try:
        from arkitect.harness import config
        return config.get('designer.name', root=ws)
    except Exception:
        return None


# ---------------------------------------------------------------- HTTP

class Handler(BaseHTTPRequestHandler):
    app = None                                   # set by serve()

    def log_message(self, fmt, *args):           # quiet: the page shows what matters
        pass

    def _send(self, code, body, ctype='application/json'):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def _file(self, path, download=None):
        if not os.path.isfile(path):
            return self._send(404, {'error': 'not found'})
        ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        with open(path, 'rb') as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-cache')      # the page follows the engine it is served by
        if download:
            self.send_header('Content-Disposition', 'attachment; filename="%s"' % download)
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get('Content-Length') or 0)
        if not n:
            return {}
        return json.loads(self.rfile.read(n).decode())

    def _guard(self):
        """A write must come from this page: same origin, JSON body. A page elsewhere on the
           web cannot post JSON cross-origin without a preflight this server never answers."""
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            raise PermissionError('writes take application/json')
        origin = self.headers.get('Origin')
        host = self.headers.get('Host', '')
        if origin and urlparse(origin).netloc != host:
            raise PermissionError('cross-origin write refused')

    def do_GET(self):
        self._route('GET')

    def do_POST(self):
        self._route('POST')

    def _route(self, method):
        app = self.app
        url = urlparse(self.path)
        parts = [unquote(p) for p in url.path.strip('/').split('/') if p]
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if method == 'GET' and (not parts or parts[0] != 'api'):
                rel = '/'.join(parts) or 'index.html'
                if '..' in rel.split('/'):
                    return self._send(404, {'error': 'not found'})
                path = os.path.join(STATIC, rel)
                return self._file(path if os.path.isfile(path) else os.path.join(STATIC, 'index.html'))
            api = parts[1:]
            if method == 'POST':
                self._guard()
                body = self._body()
            if method == 'GET':
                return self._get(app, api, q)
            return self._post(app, api, body)
        except PermissionError as exc:
            return self._send(403, {'error': str(exc)})
        except (ValueError, KeyError) as exc:
            return self._send(400, {'error': str(exc)})
        except Exception as exc:
            return self._send(500, {'error': '%s: %s' % (exc.__class__.__name__, exc),
                                    'trace': traceback.format_exc()[-2000:]})

    def _get(self, app, api, q):
        n = len(api)
        if api == ['workspace']:
            return self._send(200, app.workspace())
        if api == ['gate']:
            return self._send(200, {'gate': app.last_gate(), 'tree': state_key(app.ws)})
        if n == 2 and api[0] == 'jobs':
            job = app.jobs.get(api[1])
            return self._send(200, job) if job else self._send(404, {'error': 'no such job'})
        if api == ['changes']:
            return self._send(200, {'changed': changed(app.ws)})
        if api == ['decisions']:
            return self._send(200, app.decisions(q.get('status'), q.get('project')))
        if n == 2 and api[0] == 'decisions' and DID.match(api[1]):
            return self._send(200, app.decision(api[1]))
        if api == ['about'] and q.get('path'):
            return self._send(200, app.about(q['path']))
        if n >= 2 and api[0] == 'projects' and SLUG.match(api[1]) and api[1] in projects(app.ws):
            slug = api[1]
            if n == 2:
                return self._send(200, app.project(slug))
            if n == 3 and api[2] == 'review':
                return self._send(200, app.review(slug))
            if n == 4 and api[2] == 'decisions' and SHEET.match(api[3]):
                return self._send(200, app.sheet_decisions(slug, api[3]))
            if n == 4 and api[2] == 'sheet':
                no, base = api[3], False
                if no.endswith('.png'):
                    no = no[:-4]
                if no.endswith('.base'):
                    no, base = no[:-5], True
                if not SHEET.match(no):
                    return self._send(404, {'error': 'no such sheet'})
                if base or q.get('moved'):
                    d = app.cache.moved(slug)
                    return self._file(os.path.join(d, no + ('.base' if base else '') + '.png'))
                return self._file(os.path.join(app.cache.renders(slug), no + '.png'))
            if n == 4 and api[2] == 'file' and DELIVERABLE.match(api[3]):
                return self._file(os.path.join(app.ws, 'projects', slug, api[3]), download=api[3])
        return self._send(404, {'error': 'no such route'})

    def _post(self, app, api, body):
        if api == ['gate']:
            return self._send(202, app.run_gate(bool(body.get('full'))))
        if len(api) == 3 and api[0] == 'projects' and api[2] in ('render', 'moved') and api[1] in projects(app.ws):
            return self._send(202, app.run_render(api[1], moved=api[2] == 'moved'))
        if api == ['accept']:
            return self._send(200, app.accept(body.get('message', ''), body.get('paths', []),
                                              bool(body.get('looked'))))
        if api == ['discard']:
            return self._send(200, app.discard(body.get('paths', [])))
        if len(api) == 3 and api[0] == 'decisions' and DID.match(api[1]) and api[2] == 'confirm':
            return self._send(200, app.confirm(api[1], body.get('quote', '')))
        if (len(api) == 4 and api[0] == 'projects' and api[1] in projects(app.ws)
                and RID.match(api[2]) and api[3] in ('fixed', 'open', 'wontfix', 'rejected')):
            return self._send(200, app.set_finding(api[1], api[2], api[3], body.get('note')))
        return self._send(404, {'error': 'no such route'})


def make_server(ws, host='127.0.0.1', port=8765, cache=None):
    handler = type('Bound', (Handler,), {'app': App(ws, cache)})
    return ThreadingHTTPServer((host, port), handler)


def main(argv):
    opt = lambda f, d: argv[argv.index(f)+1] if f in argv else d
    port = int(opt('--port', '8765'))
    host = opt('--host', '127.0.0.1')
    ws = workspace.WORKSPACE
    if not os.path.isdir(os.path.join(ws, 'projects')):
        print('no projects/ in %s: run arkitect web inside your workspace' % ws, file=sys.stderr)
        return 2
    srv = make_server(ws, host, port)
    url = 'http://%s:%d/' % (host, srv.server_address[1])
    print('arkitect web: %s  (workspace %s)  -- Ctrl-C stops it' % (url, ws))
    if '--no-open' not in argv:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
