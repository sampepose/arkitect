"""The gate: every oracle this repository trusts, run as one command that cannot report a
green it did not earn.

    python3 arkitect/lib/verify/gate.py                    # fast tier, every project, against HEAD
    python3 arkitect/lib/verify/gate.py --full             # and arkitect/lib/verify/run_tests.py
    python3 arkitect/lib/verify/gate.py --base main        # against another commit
    python3 arkitect/lib/verify/gate.py --base main --expect-unchanged    # a refactor's proof
    python3 arkitect/lib/verify/gate.py --project oak_42 --json
    python3 arkitect/lib/verify/gate.py accept             # write trace.md5 where the drawing moved
    python3 arkitect/lib/verify/gate.py render --sheets A-101,P-601 [--clip 0,0,12,9] [--dpi 150]
    python3 arkitect/lib/verify/gate.py render --moved     # what moved against HEAD, base and current

Exit status: 0 passed, 1 failed, 2 the gate could not run something it needed. Never 0
for an oracle that did not run.

WHY IT EXISTS. CLAUDE.md lists eight oracles and three false greens this repository has
actually produced -- an `echo` after a command whose stderr went to /dev/null, a test
runner that collected nothing, an import blocker Python ignored -- and every one of them
read as success. Eight separate commands are eight chances to run one wrong. This runs
them the one way, reads every exit status and keeps every stderr, and says in one place
what moved:

    per project   the build and its trace (arkitect/lib/verify/trace.py), against trace.md5
                  what the build PRINTS, against the base -- the model checks only print
                  which SHEETS moved, against the base (trace.py --by-sheet)
                  arkitect/lib/verify/sheet_text.py's findings
                  arkitect/lib/export/dxf.py, to a scratch file: exit status and stderr
                  the vocabulary diff: every code citation and dimension the base's
                  sheets print that the current sheets print nowhere
    the repo      pyflakes over every build, src, lib and codes
                  arkitect/lib/verify/twins.py's total against test_twins.CEILING
                  --full: arkitect/lib/verify/run_tests.py

A drawing that moved is not a failure. A drawing that moved while trace.md5 still holds
the old digest is: review what moved, then `python3 arkitect/lib/verify/gate.py accept`, the one
sanctioned way to write trace.md5 (the hooks refuse any other).

THE BASE is a commit (HEAD unless --base), exported with `git archive` into
.verify-cache/ and built there by the CURRENT tools, copied in over the base's own.
A projects repository that uses this engine from outside it (arkitect/lib/workspace.py) is measured
the same way, its base being two exports: the projects at --base and the engine at
--engine-base, or the live engine without it:

    cd ../arkitect-projects && python3 ../arkitect/lib/verify/gate.py --base main
    python3 ../arkitect/lib/verify/gate.py --engine-base main --expect-unchanged   # an engine change

Either way the base must be measured exactly the way the working tree is, or a tool change
reads as a drawing change. The cache is keyed by the base commit AND the tools, so the second run
against the same base costs nothing. Nothing is written inside the checkout but that
ignored directory, and the deliverables are never touched.
"""
import argparse
import atexit
import concurrent.futures as cf
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from arkitect.lib import workspace                                   # noqa: E402

# ROOT is the engine this gate belongs to; WORKSPACE holds the projects it measures, their
# trace.md5, ledger, review files and cache. They are one directory unless a projects
# repository uses this engine from outside it (arkitect/lib/workspace.py).
WORKSPACE = workspace.WORKSPACE
SEPARATE = workspace.separate(WORKSPACE)
CACHE = os.path.join(WORKSPACE, '.verify-cache')
PY = sys.executable
TIMEOUT = 900

# The files that MEASURE, copied over the base's own before it is built: the gate itself
# (its _text helper runs in the tree it measures), the recorder, sheet_text, the build
# loader they all call (buildscript.build_arg is newer than some bases), and the workspace
# the gate imports.
TOOLS = ('arkitect/lib/verify/gate.py', 'arkitect/lib/verify/trace.py', 'arkitect/lib/verify/sheet_text.py', 'arkitect/lib/buildscript.py',
         'arkitect/lib/workspace.py')

# What a sheet states that a trim must not lose without meaning to: a code citation, or a
# dimension a trade builds to. CLAUDE.md "Drawing notes" calls this the VOCABULARY diff.
_CITE = re.compile(r"\b(?:RCO|OPC|NEC|IRC|IPC|IMC|IBC|OAC|C\.C\.|UL|ASTM|ASSE|NFPA|ACI|ESR|TABLE)"
                   r"\s+[A-Z]?\d[\w.()/-]*")
_DIM = re.compile(r"\d+'-\d+(?:-\d+/\d+)?\"|\b\d+(?:-\d+/\d+)?\"")


def engine_version(root=ROOT):
    """The running engine's version, read from arkitect/__init__.py as TEXT -- not imported: a
       .pyc is trusted on size and mtime to the second, so '1.0.0' rewritten as '1.1.0' within a
       second would import as the old one (see _PYCACHE). None for an engine older than versions."""
    p = os.path.join(root, 'arkitect', '__init__.py')
    m = re.search(r"^__version__ = ['\"]([^'\"]+)['\"]", _read(p), re.M) if os.path.exists(p) else None
    return m.group(1) if m else None


def read_digest(path):
    """(digest, engine version) from a trace.md5: `<md5> engine=<version>`, or a bare `<md5>`
       from before versions were recorded. (None, None) when there is no file. Every reader
       that only wants the digest takes the first word, so the second is invisible to it."""
    if not os.path.exists(path):
        return None, None
    words = _read(path).split()
    version = next((w[len('engine='):] for w in words[1:] if w.startswith('engine=')), None)
    return (words[0] if words else None), version


def write_digest(path, digest):
    """The one writer of trace.md5 (accept): the digest, and the engine that drew it."""
    v = engine_version()
    with open(path, 'w') as fh:
        fh.write(digest + (' engine=%s' % v if v else '') + '\n')


def projects(root=WORKSPACE):
    """Every project: a directory under projects/ holding a build.py."""
    base = os.path.join(root, 'projects')
    if not os.path.isdir(base):
        return []
    return sorted(d for d in os.listdir(base)
                  if os.path.isfile(os.path.join(base, d, 'build.py')))


# Every process the gate starts compiles into a bytecode cache of its own, made fresh for this
# run. Python trusts a .pyc whose source has the same size and mtime (to the second), so a file
# rewritten within a second by an edit of the same length -- one constant for another -- ran
# as its OLD code, and the gate measured a build that no longer existed. A test that swapped
# 'PER D-912' for 'DOOR D-4A' found it (arkitect/lib/verify/test_gate.py).
_PYCACHE = tempfile.mkdtemp(prefix='gate-pycache-')
atexit.register(shutil.rmtree, _PYCACHE, True)
_ENV = dict(os.environ, PYTHONPYCACHEPREFIX=_PYCACHE)


def _run(cmd, cwd=WORKSPACE, engine=ROOT):
    """(ran, returncode, stdout, stderr). ran is False only when the command could not
       be started or timed out -- which the gate treats as its own failure, never a pass.
       The process's workspace is `cwd` and its engine `engine` (arkitect/lib/workspace.py)."""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT,
                           env=workspace.env(cwd, engine, _ENV))
    except (OSError, subprocess.SubprocessError) as exc:
        return False, None, '', '%s: %s' % (exc.__class__.__name__, exc)
    return True, r.returncode, r.stdout, r.stderr


def _tail(text, n=40):
    return '\n'.join(text.rstrip().splitlines()[-n:])


def _read(path):
    with open(path) as fh:
        return fh.read()


def _md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------- one project, one tree

def measure(tree, slug, out, dxf=True, text=True, claims=False, engine=None):
    """Run a project's per-project oracles in `tree` (the workspace, or an exported base)
       with the tools of `engine` (default `tree`: one directory holds both) and leave their
       files in `out`. Returns the result dict; every oracle carries `ran` and `ok`."""
    engine = engine or tree
    os.makedirs(out, exist_ok=True)
    build = os.path.join(tree, 'projects', slug, 'build.py')
    f = lambda name: os.path.join(out, name)
    jobs = {
        'trace': [PY, os.path.join(engine, 'arkitect', 'lib', 'verify', 'trace.py'), f('trace.txt'), build,
                  '--stdout', f('stdout.txt'), '--by-sheet', f('sheets.txt'),
                  '--pdf-dir', f('pdf')],
    }
    if text:
        jobs['sheet_text'] = [PY, os.path.join(engine, 'arkitect', 'lib', 'verify', 'gate.py'), '_text',
                              build, f('text.json')]
    if dxf:
        jobs['dxf'] = [PY, os.path.join(engine, 'arkitect', 'lib', 'export', 'dxf.py'), build, f('floor.dxf')]
    # A project with a feature list (arkitect/harness/progress.py) has every claim in it proved by
    # its build. Run as a command, so arkitect/lib/ never imports arkitect/harness/.
    has_list = os.path.exists(os.path.join(tree, 'projects', slug, 'progress.json'))
    if claims and has_list:
        jobs['progress'] = [PY, '-m', 'arkitect.harness.progress', 'verify', slug, '--json']
    with cf.ThreadPoolExecutor(len(jobs)) as pool:
        done = {k: pool.submit(_run, cmd, tree, engine) for k, cmd in jobs.items()}
        runs = {k: fut.result() for k, fut in done.items()}

    res = {}
    ran, code, _o, err = runs['trace']
    ok = ran and code == 0 and os.path.exists(f('trace.txt'))
    res['trace'] = {'ran': ran, 'ok': ok}
    if ok:
        res['trace']['digest'] = _md5(f('trace.txt'))
        with open(f('trace.txt')) as fh:
            res['trace']['calls'] = sum(1 for ln in fh if not ln.startswith('PAGES\t'))
    else:
        res['trace']['stderr'] = _tail(err)

    if text:
        ran, code, _o, err = runs['sheet_text']
        st = {'ran': ran and code in (0, 1) and os.path.exists(f('text.json'))}
        if st['ran']:
            st['findings'] = json.loads(_read(f('text.json')))['findings']
            st['ok'] = not st['findings']
        else:
            st['ok'] = False
            st['stderr'] = _tail(err)
        res['sheet_text'] = st

    if dxf:
        ran, code, _o, err = runs['dxf']
        ok = ran and code == 0 and os.path.exists(f('floor.dxf'))
        res['dxf'] = {'ran': ran, 'ok': ok}
        if not ok:
            res['dxf']['stderr'] = _tail(err)
        if os.path.exists(f('floor.dxf')):
            os.remove(f('floor.dxf'))           # 4 MB nobody reads; its exit status was the point
    if 'progress' in runs:
        ran, code, out_, err = runs['progress']
        try:
            v = json.loads(out_)
            res['progress'] = dict(v, ran=True, ok=not v['false'])
        except ValueError:
            res['progress'] = {'ran': False, 'ok': False, 'stderr': _tail(err)}
    return res


def by_sheet(path):
    """{sheet: (records, md5)} from a --by-sheet file."""
    out = {}
    for ln in _read(path).splitlines():
        no, n, h = ln.split('\t')
        out[no] = (int(n), h)
    return out


def moved(base_sheets, cur_sheets):
    """[{sheet, change, before, after}] for every sheet that is not byte-identical."""
    out = []
    for no in sorted(set(base_sheets) | set(cur_sheets)):
        a, b = base_sheets.get(no), cur_sheets.get(no)
        if a == b:
            continue
        change = 'added' if a is None else 'removed' if b is None else 'changed'
        out.append({'sheet': no, 'change': change,
                    'before': a[0] if a else 0, 'after': b[0] if b else 0})
    return out


def vocabulary(text_json):
    """Every citation and dimension a project's sheets print, as one set."""
    words = set()
    for flat in json.loads(_read(text_json))['text'].values():
        words.update(m.strip() for m in _CITE.findall(flat))
        words.update(_DIM.findall(flat))
    return words


# ---------------------------------------------------------------- the base

def _git(*args, cwd=WORKSPACE):
    ran, code, out, err = _run(['git'] + list(args), cwd)
    if not ran or code != 0:
        raise RuntimeError('git %s: %s' % (' '.join(args), (err or out).strip()))
    return out.strip()


def _tools_key():
    h = hashlib.md5()
    for rel in TOOLS:
        h.update(open(os.path.join(ROOT, rel), 'rb').read())
    return h.hexdigest()[:10]


def _engine_state():
    """What the LIVE engine is, for a base measured with it: its HEAD and a digest of its
       uncommitted changes. A base built by one engine must not be reused by another."""
    head = _git('rev-parse', 'HEAD', cwd=ROOT)
    diff = _git('diff', 'HEAD', cwd=ROOT)
    return head[:12] + hashlib.md5(diff.encode()).hexdigest()[:6]


def _export(repo, sha, dest):
    """`git archive` of `repo` at `sha`, extracted into `dest`."""
    os.makedirs(dest)
    p = subprocess.Popen(['git', 'archive', '--format=tar', sha], cwd=repo,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with tarfile.open(fileobj=p.stdout, mode='r|') as tar:
        tar.extractall(dest, filter=_no_absolute_links)
    if p.wait() != 0:
        raise RuntimeError('git archive %s: %s' % (sha[:12], p.stderr.read().decode()))


def _no_absolute_links(member, path):
    """tarfile's 'data' filter, less the links it refuses outright: a projects repository
       commits .claude/skills and .claude/agents as absolute links to its engine, and a base
       build needs neither."""
    if member.issym() and os.path.isabs(member.linkname):
        return None
    return tarfile.data_filter(member, path)


def baseline(ref, slugs, engine_ref=None):
    """(sha, {slug: dir}) for the base commit, built once per (commit, tools) and cached.
       A slug the base does not have maps to None. Raises RuntimeError if the base cannot
       be exported or built.

       With the projects in a repository of their own (arkitect/lib/workspace.py), the base is TWO
       exports: the workspace at `ref`, and the engine at `engine_ref` -- or the live
       engine, when that is None, which is how a project's change is measured. An engine
       change is measured against its old self with `engine_ref` and `ref` HEAD."""
    sha = _git('rev-parse', '--verify', ref + '^{commit}')
    key = '%s-%s' % (sha[:12], _tools_key())
    if SEPARATE:
        esha = (_git('rev-parse', '--verify', engine_ref + '^{commit}', cwd=ROOT)[:12]
                if engine_ref else 'live' + _engine_state())
        key = '%s-e%s-%s' % (sha[:12], esha, _tools_key())
    elif engine_ref:
        raise RuntimeError('--engine-base needs a workspace outside the engine; here one '
                           'commit holds both, so --base is the base')
    final = os.path.join(CACHE, key)
    want = [s for s in slugs if not os.path.exists(os.path.join(final, s, 'DONE'))]
    if want:
        os.makedirs(CACHE, exist_ok=True)
        work = tempfile.mkdtemp(prefix=key + '.', dir=CACHE)
        tree = os.path.join(work, 'tree')
        try:
            _export(WORKSPACE, sha, tree)
            engine = tree
            if SEPARATE:
                engine = ROOT
                if engine_ref:
                    engine = os.path.join(work, 'engine')
                    _export(ROOT, engine_ref, engine)
            if engine != ROOT:
                for rel in TOOLS:
                    shutil.copyfile(os.path.join(ROOT, rel), os.path.join(engine, rel))
            present = [s for s in want
                       if os.path.isfile(os.path.join(tree, 'projects', s, 'build.py'))]
            with cf.ThreadPoolExecutor(max(1, len(present))) as pool:
                results = dict(zip(present, pool.map(
                    lambda s: measure(tree, s, os.path.join(work, s), dxf=False, engine=engine),
                    present)))
            for s in want:
                d = os.path.join(work, s)
                os.makedirs(d, exist_ok=True)
                if s not in results:
                    status = 'absent'
                elif results[s]['trace']['ok'] and results[s]['sheet_text']['ran']:
                    status = 'ok'
                else:
                    raise RuntimeError('%s does not build at %s:\n%s' % (
                        s, sha[:12], results[s]['trace'].get('stderr') or
                        results[s]['sheet_text'].get('stderr', '')))
                with open(os.path.join(d, 'DONE'), 'w') as fh:
                    fh.write(status)
            shutil.rmtree(tree)
            os.makedirs(final, exist_ok=True)
            for s in want:
                dest = os.path.join(final, s)
                if not os.path.exists(dest):
                    try:
                        os.rename(os.path.join(work, s), dest)
                    except OSError:
                        pass                     # another gate run landed it first
        finally:
            shutil.rmtree(work, ignore_errors=True)
    out = {}
    for s in slugs:
        d = os.path.join(final, s)
        out[s] = d if _read(os.path.join(d, 'DONE')) == 'ok' else ABSENT
    return sha, out


# baseline()'s answer for a project the base commit does not have: every sheet is new.
ABSENT = 'absent'


def _base_sheets(bdir):
    return {} if bdir == ABSENT else by_sheet(os.path.join(bdir, 'sheets.txt'))


# ---------------------------------------------------------------- the whole gate

# A decision's id (decisions/, arkitect/harness/decisions.py). Door marks are D-1, D-4A: never three digits.
DECISION_ID = re.compile(r'\bD-\d{3}\b')


def _decisions():
    """{status: count} over decisions/*.md, read from each front matter's status line --
       a regex, not arkitect/harness/decisions.py, so arkitect/lib/ imports nothing from arkitect/harness/."""
    d = os.path.join(WORKSPACE, 'decisions')
    counts = {}
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else ():
        if f.endswith('.md'):
            m = re.search(r'^status: (\w+)$', _read(os.path.join(d, f)), re.M)
            k = m.group(1) if m else 'unreadable'
            counts[k] = counts.get(k, 0)+1
    return counts


def _review(slugs):
    """{slug: {severity: open count}} from each project's review.json (arkitect/harness/review.py)."""
    out = {}
    for s in slugs:
        p = os.path.join(WORKSPACE, 'projects', s, 'review.json')
        if os.path.exists(p):
            counts = {}
            for f in json.loads(_read(p)).get('findings', []):
                if f.get('status') == 'open':
                    counts[f['severity']] = counts.get(f['severity'], 0)+1
            out[s] = counts
    return out


def _pyflakes():
    targets = []
    for s in projects():
        targets += [os.path.join('projects', s, 'build.py'), os.path.join('projects', s, 'src')]
    # the engine's layers, by absolute path when the projects live outside it
    targets += [t if not SEPARATE else os.path.join(ROOT, t)
                for t in ('arkitect', os.path.join('.claude', 'hooks'))]
    # a path pyflakes cannot find is its own error, not a finding
    targets = [t for t in targets if os.path.exists(os.path.join(WORKSPACE, t))]
    ran, code, out, err = _run([PY, '-m', 'pyflakes'] + targets)
    if ran and 'No module named pyflakes' in err:
        ran = False
    return {'ran': ran, 'ok': ran and code == 0,
            'output': _tail(out + err) if (not ran or code) else ''}


def _twins():
    try:
        from arkitect.lib.verify import twins, test_twins
        total = twins.total(twins.survey(os.path.join(WORKSPACE, 'projects')))
        ceiling = test_twins.ceiling(WORKSPACE)
        return {'ran': True, 'ok': total <= ceiling, 'total': total, 'ceiling': ceiling}
    except Exception as exc:
        return {'ran': False, 'ok': False, 'error': '%s: %s' % (exc.__class__.__name__, exc)}


def _tests():
    ran, code, out, err = _run([PY, os.path.join(ROOT, 'arkitect', 'lib', 'verify', 'run_tests.py')])
    lines = [ln for ln in out.splitlines() if ln.startswith(('PASSED:', 'FAILED:'))]
    last = lines[-1] if lines else ''
    ok = ran and code == 0 and last.startswith('PASSED:')
    res = {'ran': ran and bool(last), 'ok': ok, 'summary': last}
    if not ok:
        res['output'] = _tail(err + out, 60)
    return res


def gate(base='HEAD', only=None, full=False, expect_unchanged=False, engine_base=None):
    """Run everything; return the report dict."""
    slugs = [s for s in projects() if not only or s in only]
    report = {'ok': True, 'tier': 'full' if full else 'fast', 'base': base,
              'projects': {}, 'failures': [], 'errors': []}
    if only and set(only) - set(slugs):
        report['errors'].append('no such project: %s' % ', '.join(sorted(set(only) - set(slugs))))

    scratch = tempfile.mkdtemp(prefix='gate-')
    try:
        with cf.ThreadPoolExecutor(4) as pool:
            cur_f = {s: pool.submit(measure, WORKSPACE, s, os.path.join(scratch, s), claims=True, engine=ROOT)
                     for s in slugs}
            flakes_f = pool.submit(_pyflakes)
            tests_f = pool.submit(_tests) if full else None
            try:
                sha, bases = baseline(base, slugs, engine_base)
                report['base'] = '%s %s' % (base, sha[:12]) + (
                    ', engine %s' % engine_base if engine_base else '')
            except Exception as exc:
                bases = {}
                msg = 'base %s could not be built: %s' % (base, exc)
                # against HEAD the base only NAMES what moved; asked for explicitly, it is the point
                (report['errors'] if base != 'HEAD' or engine_base
                 else report.setdefault('notes', [])).append(msg)
            cur = {s: f.result() for s, f in cur_f.items()}
            report['pyflakes'] = flakes_f.result()
            report['tests'] = tests_f.result() if tests_f else {'ran': None, 'ok': None,
                                                                'summary': 'not run (fast tier)'}
        report['twins'] = _twins()
        report['decisions'] = _decisions()
        report['review'] = _review(slugs)

        for s in slugs:
            res = cur[s]
            p = report['projects'][s] = res
            here = os.path.join(scratch, s)
            md5_file = os.path.join(WORKSPACE, 'projects', s, 'trace.md5')
            committed, recorded = read_digest(md5_file)
            res['trace']['committed'] = committed
            p['engine'] = {'recorded': recorded, 'running': engine_version()}
            bdir = bases.get(s)
            if res['trace']['ok'] and bdir:
                p['new_at_base'] = bdir == ABSENT
                p['sheets_moved'] = moved(_base_sheets(bdir),
                                          by_sheet(os.path.join(here, 'sheets.txt')))
                a = [] if bdir == ABSENT else _read(os.path.join(bdir, 'stdout.txt')).splitlines()
                b = _read(os.path.join(here, 'stdout.txt')).splitlines()
                p['stdout_diff'] = '\n'.join(difflib.unified_diff(a, b, 'base', 'current',
                                                                  lineterm='', n=0))
                if res['sheet_text']['ran'] and bdir != ABSENT:
                    lost = vocabulary(os.path.join(bdir, 'text.json')) - \
                           vocabulary(os.path.join(here, 'text.json'))
                    p['vocab_lost'] = sorted(lost)
            else:
                p['sheets_moved'] = None             # unknown: no base to name them against

            # -------------------------------------------------- what fails, per project
            if not res['trace']['ran']:
                report['errors'].append('%s: the trace could not be started' % s)
                continue
            if not res['trace']['ok']:
                # sheet_text and the exporter run the same build, so they fail with it; the
                # build's own stderr is the one diagnosis worth printing
                report['failures'].append('%s: the build failed\n%s' % (s, res['trace'].get('stderr', '')))
                continue
            if not res['sheet_text']['ran'] or not res.get('dxf', {}).get('ran', True):
                report['errors'].append('%s: an oracle could not run\n%s' % (
                    s, res['sheet_text'].get('stderr', '') or res.get('dxf', {}).get('stderr', '')))
            if committed is None:
                report['failures'].append('%s: no trace.md5 committed' % s)
            elif res['trace']['digest'] != committed:
                names = ', '.join(m['sheet'] for m in p['sheets_moved'] or []) or 'sheets unknown'
                eng = p['engine']
                under = (' -- under engine %s, accepted under %s' % (eng['running'], eng['recorded'] or 'none')
                         if eng['recorded'] != eng['running'] else '')
                report['failures'].append(
                    '%s: the drawing moved (%s) and trace.md5 still holds the old digest%s. '
                    'Review what moved, then run: arkitect gate accept' % (s, names, under))
            elif p['engine']['recorded'] != p['engine']['running']:
                # the same drawing under another engine: an upgrade the owner has not yet taken.
                # Nothing is applied unseen; accept records it.
                p['engine']['upgrade'] = 'proposed'
            if res['sheet_text']['ran']:
                with open(os.path.join(here, 'text.json')) as fh:
                    flat = json.load(fh)['text']
                ids = sorted({(no, m) for no, t in flat.items() for m in DECISION_ID.findall(t)})
                if ids:
                    report['failures'].append(
                        '%s: a sheet prints a decision id, which is this repository\'s vocabulary '
                        'and means nothing to a plan reviewer: %s' % (
                            s, ', '.join('%s on %s' % (m, no) for no, m in ids)))
            if res['sheet_text']['ran'] and not res['sheet_text']['ok']:
                report['failures'].append('%s: sheet_text finds %d problem(s):\n  %s' % (
                    s, len(res['sheet_text']['findings']), '\n  '.join(res['sheet_text']['findings'])))
            pg = res.get('progress')
            if pg and not pg['ran']:
                report['errors'].append('%s: progress.json could not be verified\n%s'
                                        % (s, pg.get('stderr', '')))
            elif pg and pg['false']:
                report['failures'].append('%s: progress.json claims what the build does not '
                                          'prove:\n  %s' % (s, '\n  '.join(pg['false'])))
            if 'dxf' in res and res['dxf']['ran'] and not res['dxf']['ok']:
                report['failures'].append('%s: the DXF exporter failed\n%s' % (s, res['dxf'].get('stderr', '')))
            if expect_unchanged and (p.get('sheets_moved') or p.get('stdout_diff')):
                report['failures'].append('%s: --expect-unchanged, but %s' % (s, ' and '.join(
                    w for w, c in (('sheets moved', p.get('sheets_moved')),
                                   ('the build prints differently', p.get('stdout_diff'))) if c)))
            if expect_unchanged and p.get('sheets_moved') is None:
                report['errors'].append('%s: --expect-unchanged needs a base to compare with' % s)

        # ------------------------------------------------------ what fails, repo-wide
        if not report['pyflakes']['ran']:
            report['errors'].append('pyflakes could not run: %s' % report['pyflakes']['output'])
        elif not report['pyflakes']['ok']:
            report['failures'].append('pyflakes:\n' + report['pyflakes']['output'])
        if not report['twins']['ran']:
            report['errors'].append('twins could not run: %s' % report['twins']['error'])
        elif not report['twins']['ok']:
            report['failures'].append('twins: %d copied lines against a ceiling of %d' % (
                report['twins']['total'], report['twins']['ceiling']))
        if full:
            if not report['tests']['ran']:
                report['errors'].append('run_tests.py did not report a result:\n%s'
                                        % report['tests'].get('output', ''))
            elif not report['tests']['ok']:
                report['failures'].append('tests: %s\n%s' % (report['tests']['summary'],
                                                             report['tests'].get('output', '')))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    if not slugs:
        report['errors'].append('no project was measured')
    report['ok'] = not report['failures'] and not report['errors']
    return report


def summary(r):
    """The report as a person reads it."""
    out = ['gate (%s) against %s: %s' % (r['tier'], r['base'],
                                         'PASSED' if r['ok'] else
                                         'ERROR' if r['errors'] else 'FAILED')]
    for s, p in r['projects'].items():
        t = p['trace']
        if t['ok']:
            same = 'matches' if t['digest'] == t['committed'] else 'DIFFERS from'
            out.append('  %-10s build ok, %d calls, digest %s %s trace.md5'
                       % (s, t['calls'], t['digest'][:8], same))
            eng = p.get('engine') or {}
            if eng.get('upgrade') == 'proposed':
                out.append('             engine %s -> %s: no sheet moved; `arkitect gate accept` takes the upgrade'
                           % (eng['recorded'] or 'none', eng['running']))
        else:
            out.append('  %-10s build FAILED' % s)
        st = p['sheet_text']
        out.append('             sheet_text %s, dxf %s' % (
            ('%d finding(s)' % len(st['findings'])) if st['ran'] else 'did not run',
            'ok' if p.get('dxf', {}).get('ok') else 'FAILED'))
        m = p.get('sheets_moved')
        out.append('             sheets moved: %s' % (
            'unknown (no base)' if m is None else
            'every sheet: the project is new since the base' if p.get('new_at_base') else
            ', '.join('%s (%s)' % (x['sheet'], x['change']) for x in m) or 'none'))
        d = p.get('stdout_diff')
        if d is not None:
            n = sum(1 for ln in d.splitlines() if ln[:1] in '+-' and ln[:3] not in ('+++', '---'))
            out.append('             build output: %s' % ('%d line(s) differ' % n if n else 'unchanged'))
        pg = p.get('progress')
        if pg and pg.get('ran'):
            out.append('             progress: %d passes, %d drawn, %d pending of %d; next %s' % (
                pg['counts']['passes'], pg['counts']['drawn'], pg['counts']['pending'],
                pg['total'], pg['next'] or '-- every feature passes'))
        if p.get('vocab_lost'):
            out.append('             printed before, printed nowhere now: %s' % ', '.join(p['vocab_lost']))
    fl, tw, te = r['pyflakes'], r['twins'], r['tests']
    out.append('  pyflakes %s; twins %s; tests %s' % (
        'ok' if fl['ok'] else 'FAILED' if fl['ran'] else 'did not run',
        ('%d <= %d' % (tw['total'], tw['ceiling'])) if tw['ran'] else 'did not run',
        te['summary'] or ('FAILED' if te['ran'] else 'did not run')))
    for s, c in sorted((r.get('review') or {}).items()):
        if c:
            out.append('  review %s: %s open (arkitect review next %s)' % (
                s, ', '.join('%d %s' % (c[k], k) for k in ('blocker', 'major', 'minor') if k in c), s))
    dc = r.get('decisions') or {}
    if dc:
        out.append('  decisions: %d open for the designer, %d waiting on others, %d confirmed '
                   '(arkitect decisions pending)'
                   % (dc.get('open', 0), dc.get('waiting', 0), dc.get('confirmed', 0)))
    for n in r.get('notes', []):
        out.append('  note: ' + n)
    for label, items in (('FAILURES', r['failures']), ('ERRORS', r['errors'])):
        if items:
            out.append(label + ':')
            out += ['  - ' + i.replace('\n', '\n    ') for i in items]
    return '\n'.join(out)


# ---------------------------------------------------------------- accept

def accept(base='HEAD', only=None):
    """Write trace.md5 for every project whose drawing moved, and say which sheets moved,
       in the words a commit message wants. The ONE sanctioned writer of trace.md5:
       .claude/hooks refuses an edit or a shell redirect onto it, because a digest updated
       to make a test pass is a test that no longer tests anything. Returns (lines, ok)."""
    slugs = [s for s in projects() if not only or s in only]
    scratch = tempfile.mkdtemp(prefix='gate-accept-')
    lines, moved_names, ok = [], [], True
    try:
        with cf.ThreadPoolExecutor(max(1, len(slugs))) as pool:
            cur = dict(zip(slugs, pool.map(
                lambda s: measure(WORKSPACE, s, os.path.join(scratch, s), dxf=False, text=False,
                                  engine=ROOT),
                slugs)))
        try:
            _sha, bases = baseline(base, slugs)
        except Exception as exc:
            bases = {}
            lines.append('note: base %s could not be built, so the sheets cannot be named: %s'
                         % (base, exc))
        for s in slugs:
            t = cur[s]['trace']
            if not t['ok']:
                ok = False
                lines.append('%s: the build failed; nothing written\n%s' % (s, t.get('stderr', '')))
                continue
            path = os.path.join(WORKSPACE, 'projects', s, 'trace.md5')
            old, recorded = read_digest(path)
            running = engine_version()
            if old == t['digest']:
                if recorded == running:
                    lines.append('%s: trace.md5 already matches the drawing (%s)' % (s, old[:8]))
                else:
                    write_digest(path, t['digest'])
                    lines.append('%s: the drawing is unchanged; engine %s -> %s recorded'
                                 % (s, recorded or 'none', running))
                    moved_names.append('%s none (engine %s -> %s)' % (s, recorded or 'none', running))
                continue
            write_digest(path, t['digest'])
            names = None
            if bases.get(s):
                names = [m['sheet'] for m in moved(_base_sheets(bases[s]),
                                                   by_sheet(os.path.join(scratch, s, 'sheets.txt')))]
            lines.append('%s: trace.md5 %s -> %s; sheets moved against %s: %s' % (
                s, (old or 'none')[:8], t['digest'][:8], base,
                ', '.join(names) if names else 'none' if names == [] else 'unknown'))
            moved_names.append('%s %s' % (s, ', '.join(names) if names else '(sheets unknown)'))
        if moved_names:
            lines.append('For the commit message -- Sheets moved: ' + '; '.join(moved_names))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return lines, ok


# ---------------------------------------------------------------- render

def _out_dir(out):
    """Where renders go: `out`, else the background job's own tmp, else a fresh temp
       directory. Never inside the checkout: a render is something to LOOK at, and the
       checkout's PDFs are deliverables only the merger regenerates."""
    if out is None:
        job = os.environ.get('CLAUDE_JOB_DIR')
        if job and os.path.isdir(os.path.join(job, 'tmp')):
            out = tempfile.mkdtemp(prefix='render-', dir=os.path.join(job, 'tmp'))
        else:
            out = tempfile.mkdtemp(prefix='gate-render-')
    real = os.path.realpath(out)
    for root in {os.path.realpath(ROOT), os.path.realpath(WORKSPACE)}:
        if real == root or real.startswith(root + os.sep):
            raise ValueError('refusing to render inside the checkout (%s); pass --out elsewhere' % out)
    os.makedirs(out, exist_ok=True)
    return out


def _bound(measured_dir):
    """{sheet: (pdf path, page index)} from a measured directory: the trace's PAGES
       records name each document's pages in bound order, and --pdf-dir numbered the
       PDFs in the same write order."""
    recs = [ln.split('\t', 1)[1] for ln in _read(os.path.join(measured_dir, 'trace.txt')).splitlines()
            if ln.startswith('PAGES\t')]
    pdfdir = os.path.join(measured_dir, 'pdf')
    pdfs = sorted(os.listdir(pdfdir)) if os.path.isdir(pdfdir) else []
    if len(recs) != len(pdfs):
        raise RuntimeError('%d documents traced but %d PDFs kept in %s' % (len(recs), len(pdfs), pdfdir))
    out = {}
    for rec, pdf in zip(recs, pdfs):
        for i, no in enumerate(eval(rec)):        # a tuple of sheet numbers trace.py wrote
            out.setdefault(no, (os.path.join(pdfdir, pdf), i))
    return out


def render(only=None, sheets=None, moved_only=False, base='HEAD', dpi=None, clip=None, out=None):
    """Draw sheets to single-page PDFs and PNGs outside the checkout; return the paths.
       `clip` is (x0, y0, x1, y1) in inches from the sheet's top left."""
    try:
        import pymupdf
    except ImportError:
        raise RuntimeError('rendering needs PyMuPDF: python3 -m pip install -r requirements.txt')
    dpi = dpi or (200 if clip else 100)
    slugs = [s for s in projects() if not only or s in only]
    out = _out_dir(out)
    scratch = tempfile.mkdtemp(prefix='gate-render-')
    written = []
    try:
        with cf.ThreadPoolExecutor(max(1, len(slugs))) as pool:
            cur = dict(zip(slugs, pool.map(lambda s: measure(
                WORKSPACE, s, os.path.join(scratch, s), dxf=False, text=False, engine=ROOT), slugs)))
        bases = baseline(base, slugs)[1] if moved_only else {}
        wanted = set(sheets or ())
        for s in slugs:
            if not cur[s]['trace']['ok']:
                raise RuntimeError('%s does not build:\n%s' % (s, cur[s]['trace'].get('stderr', '')))
            here = os.path.join(scratch, s)
            pages = _bound(here)
            if moved_only:
                if not bases.get(s):
                    raise RuntimeError('%s has no base at %s to compare with' % (s, base))
                names = [m['sheet'].split('#')[0] for m in moved(
                    _base_sheets(bases[s]), by_sheet(os.path.join(here, 'sheets.txt')))]
                names = [n for n in names if n != '(document)']
            elif wanted:
                names = [n for n in pages if n in wanted]
            else:
                names = list(pages)
            sources = [('', pages)]
            if moved_only and bases[s] != ABSENT:
                sources.append(('.base', _bound(bases[s])))
            for no in names:
                for suffix, where in sources:
                    if no not in where:
                        continue                  # added or removed: only one side has it
                    pdf, i = where[no]
                    dest = os.path.join(out, s)
                    os.makedirs(dest, exist_ok=True)
                    stem = os.path.join(dest, no + suffix)
                    with pymupdf.open(pdf) as doc:
                        one = pymupdf.open()
                        one.insert_pdf(doc, from_page=i, to_page=i)
                        one.save(stem + '.pdf')
                        one.close()
                        page = doc[i]
                        rect = pymupdf.Rect(*(v * 72 for v in clip)) if clip else None
                        page.get_pixmap(dpi=dpi, clip=rect).save(stem + '.png')
                    written += [stem + '.pdf', stem + '.png']
        missing = wanted - {os.path.basename(p).split('.')[0] for p in written}
        if missing:
            raise RuntimeError('no such sheet: %s' % ', '.join(sorted(missing)))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return out, written


# ---------------------------------------------------------------- helpers run in a tree

def _text(build, dest):
    """Subcommand `_text`: sheet_text's findings and every sheet's flat text, as JSON.
       Runs in the tree it measures, so the tree's own lib draws."""
    from arkitect.lib.verify import sheet_text
    pages = sheet_text.read(build)
    data = {'findings': sheet_text.findings(pages),
            'text': {str(no): sheet_text._flat(items) for no, items in pages.items()}}
    with open(dest, 'w') as fh:
        json.dump(data, fh)


def main(argv):
    if argv[:1] == ['_text']:
        _text(*argv[1:3])
        return 0
    if argv[:1] == ['render']:
        ap = argparse.ArgumentParser(prog='gate.py render')
        ap.add_argument('--project', action='append')
        ap.add_argument('--sheets', help='A-101,P-601 (default: every sheet)')
        ap.add_argument('--moved', action='store_true',
                        help='only the sheets that moved against --base, base and current')
        ap.add_argument('--base', default='HEAD')
        ap.add_argument('--dpi', type=int)
        ap.add_argument('--clip', help='x0,y0,x1,y1 in inches from the top left')
        ap.add_argument('--out')
        a = ap.parse_args(argv[1:])
        clip = tuple(float(v) for v in a.clip.split(',')) if a.clip else None
        try:
            out, written = render(a.project, a.sheets.split(',') if a.sheets else None,
                                  a.moved, a.base, a.dpi, clip, a.out)
        except Exception as exc:
            print('render failed: %s' % exc, file=sys.stderr)
            return 1
        pngs = [p for p in written if p.endswith('.png')]
        if pngs:
            print('\n'.join(pngs))
        elif a.moved:
            print('nothing to render: no sheet moved against %s' % a.base)
        print('%d file(s) in %s' % (len(written), out), flush=True)
        return 0
    if argv[:1] == ['accept']:
        ap = argparse.ArgumentParser(prog='gate.py accept')
        ap.add_argument('--base', default='HEAD')
        ap.add_argument('--project', action='append')
        a = ap.parse_args(argv[1:])
        lines, ok = accept(a.base, a.project)
        print('\n'.join(lines), flush=True)
        return 0 if ok else 1
    ap = argparse.ArgumentParser(prog='gate.py', description=__doc__.split('\n')[0])
    ap.add_argument('--base', default='HEAD')
    ap.add_argument('--project', action='append')
    ap.add_argument('--full', action='store_true')
    ap.add_argument('--expect-unchanged', action='store_true')
    ap.add_argument('--engine-base', help='with the projects outside the engine: build the base '
                    'with the engine at this commit (default: the live engine)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    try:
        r = gate(a.base, a.project, a.full, a.expect_unchanged, a.engine_base)
    except Exception as exc:
        print('gate could not run: %s: %s' % (exc.__class__.__name__, exc), file=sys.stderr)
        return 2
    if a.json:
        from arkitect.lib import interface      # here, not at the top: the gate is copied into
        interface.emit('gate', r)               # older engines to measure a base, and they lack it
    else:
        print(summary(r), flush=True)
    return 0 if r['ok'] else 2 if r['errors'] else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
