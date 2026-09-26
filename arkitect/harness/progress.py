"""A project's feature list, projects/<slug>/progress.json: what is drawn, what is done,
what comes next -- and every claim in it PROVED by running the build.

    arkitect progress status <slug>          # the list, and what is next
    arkitect progress next <slug>            # the next feature, with what it needs
    arkitect progress verify <slug> [--json] # exit 1 if any claim is false
    arkitect progress set <slug> <id> <pending|drawn|passes> [--note "..."]
    arkitect progress add <slug> <id> "<title>" [--after <id>] [--guard <module>]...
    arkitect progress drop <slug> <id> --note "why this set does not need it"

This is the handoff between sessions (Anthropic's initializer / worker split): the
initializer writes the list with every sheet pending, and each worker session takes the
next one, builds it, and marks it -- through `set`, which refuses a claim the build cannot
prove. The hooks refuse any other write to progress.json, as they do to trace.md5.

WHAT A CLAIM MEANS, and how it is proved. The build is run once under a profiler
(`probe`), which records every sheet it binds and every module of arkitect/codes/ and
arkitect/lib/model/fit.py whose functions it CALLS -- not imports: a rule module imported and never
called proves nothing.

    pending    nothing is claimed
    drawn      the sheet is bound in the build
    passes     drawn, and every guard module the feature lists ran during the build

A feature claimed drawn or passes that the probe cannot confirm is a FALSE CLAIM:
`verify` exits 1 and arkitect/lib/verify/gate.py fails. A sheet bound but still listed pending is
reported, not failed -- the list is behind, which costs nothing but a `set`.
"""
import json
import os
import subprocess
import sys
import tempfile

from arkitect.lib import bytecode, interface, workspace

ENGINE = workspace.ENGINE              # the shared rules a guard names live here
ROOT = workspace.WORKSPACE             # the projects and their feature lists live here
STATUSES = ('pending', 'drawn', 'passes')
WATCHED = (os.path.join(ENGINE, 'arkitect', 'codes') + os.sep, os.path.join(ENGINE, 'arkitect', 'lib', 'model') + os.sep)


def path_for(slug, root=ROOT):
    return os.path.join(root, 'projects', slug, 'progress.json')


def load(slug, root=ROOT):
    with open(path_for(slug, root)) as fh:
        return json.load(fh)


def save(slug, data, root=ROOT):
    """Written whole or not at all."""
    path = path_for(slug, root)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix='.partial')
    with os.fdopen(fd, 'w') as fh:
        json.dump(data, fh, indent=1)
        fh.write('\n')
    os.replace(tmp, path)


# ---------------------------------------------------------------- the probe

def _module_of(filename, root):
    rel = os.path.relpath(filename, root)[:-3]
    parts = rel.split(os.sep)
    if parts[-1] == '__init__':
        parts = parts[:-1]
    return '.'.join(parts)


def _probe_here(build, dest):
    """Run in a fresh process: every document of the build, to scratch, under a profiler."""
    from arkitect.lib import buildscript
    from arkitect.lib.draw import page
    called, bound = set(), []

    class Watch:
        def sheet(s, sh):
            bound.append(sh.no)
    page.observe(Watch())

    def prof(frame, event, _arg):
        if event == 'call':
            f = frame.f_code.co_filename
            if f.startswith(WATCHED) and frame.f_code.co_name != '<module>':
                called.add(f)

    # sys.monitoring (3.12) asks once per code object: the first start of each function is
    # recorded and that function is never reported again, where sys.setprofile ran a Python
    # callback on every one of a build's fourteen million calls. The set is the same: every
    # file under WATCHED one of whose functions started.
    mon = getattr(sys, 'monitoring', None)

    def start(code, _offset):
        if code.co_filename.startswith(WATCHED) and code.co_name != '<module>':
            called.add(code.co_filename)
        return mon.DISABLE

    def watch():
        if mon is None:
            sys.setprofile(prof)
            return
        mon.use_tool_id(mon.PROFILER_ID, 'arkitect-probe')
        mon.register_callback(mon.PROFILER_ID, mon.events.PY_START, start)
        mon.set_events(mon.PROFILER_ID, mon.events.PY_START)

    def unwatch():
        if mon is None:
            sys.setprofile(None)
            return
        mon.set_events(mon.PROFILER_ID, 0)
        mon.register_callback(mon.PROFILER_ID, mon.events.PY_START, None)
        mon.free_tool_id(mon.PROFILER_ID)
    keep = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    try:
        mod = buildscript.load(build)
        with tempfile.TemporaryDirectory() as t:
            watch()
            try:
                for i, doc in enumerate(buildscript.documents(mod)):
                    doc(os.path.join(t, '%02d.pdf' % i))
            finally:
                unwatch()
    finally:
        sys.stdout.close()
        sys.stdout = keep
    with open(dest, 'w') as fh:
        json.dump({'bound': bound, 'ran': sorted(_module_of(f, ENGINE) for f in called)}, fh)


def probe(slug, root=ROOT):
    """{'bound': [sheet numbers], 'ran': [module names]} from one run of the build, or
       raises RuntimeError with the build's stderr if it fails."""
    build = os.path.join(root, 'projects', slug, 'build.py')
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, 'probe.json')
        # checked-hash bytecode: a timestamp .pyc is trusted on size and mtime to the second,
        # so a same-length edit made within a second would be probed as its old code
        bytecode.hash_pycs(ENGINE, root)
        env = workspace.env(root, base=bytecode.env(os.environ))
        r = subprocess.run([sys.executable, '-m', 'arkitect.harness.progress', '_probe', build, out],
                           cwd=root, capture_output=True, text=True, timeout=900, env=env)
        if r.returncode != 0 or not os.path.exists(out):
            raise RuntimeError('the build failed under the probe:\n' + r.stderr[-2000:])
        with open(out) as fh:
            return json.load(fh)


# ---------------------------------------------------------------- claims

def check(feature, found):
    """Why this feature's claim is false, or None."""
    st = feature['status']
    if st not in STATUSES:
        return '%s: status %r is not one of %s' % (feature['id'], st, ', '.join(STATUSES))
    if st == 'pending':
        return None
    if feature['id'] not in found['bound']:
        return '%s is claimed %s but the build does not bind it' % (feature['id'], st)
    if st == 'passes':
        missing = [g for g in feature['guards'] if g not in found['ran']]
        if missing:
            return ('%s is claimed passes but these rules never ran in the build: %s'
                    % (feature['id'], ', '.join(missing)))
    return None


def verify(slug, root=ROOT):
    """{'false': [...], 'behind': [...], 'counts': {...}, 'next': feature id or None}."""
    data = load(slug, root)
    found = probe(slug, root)
    feats = data['features']
    false = [w for w in (check(f, found) for f in feats) if w]
    behind = [f['id'] for f in feats if f['status'] == 'pending' and f['id'] in found['bound']]
    counts = {s: sum(1 for f in feats if f['status'] == s) for s in STATUSES}
    nxt = next((f['id'] for f in feats if f['status'] != 'passes'), None)
    return {'false': false, 'behind': behind, 'counts': counts, 'next': nxt,
            'total': len(feats)}


def status_text(slug, root=ROOT):
    data = load(slug, root)
    lines = ['%s: %s' % (slug, data.get('address', ''))]
    for f in data['features']:
        lines.append('  %-7s %-8s %s%s' % (f['id'], f['status'], f['title'],
                                            ('  -- ' + f['notes']) if f['notes'] else ''))
    return '\n'.join(lines)


def next_text(slug, root=ROOT):
    data = load(slug, root)
    f = next((f for f in data['features'] if f['status'] != 'passes'), None)
    if f is None:
        return 'Every feature passes.'
    return '\n'.join([
        'NEXT: %s  %s  (now %s)' % (f['id'], f['title'], f['status']),
        'Guards that must RUN in this build before it passes:',
        '  ' + ('\n  '.join(f['guards']) or '(none)'),
        'Where another project here draws it (read, adapt, import -- never copy a definition;',
        'arkitect/lib/verify/test_twins.py fails on a copy):',
        '  ' + ('\n  '.join(_refs(f['id'], slug, root)) or '(none in this checkout)'),
        'Then: bind it in build.py, run `python3 arkitect/lib/verify/gate.py`, look at it with',
        '`python3 arkitect/lib/verify/gate.py render --sheets %s`, and mark it:' % f['id'],
        '`arkitect progress set %s %s passes`.' % (slug, f['id']),
    ])


def _refs(fid, slug, root):
    from arkitect.harness import catalog
    return catalog.references(fid, root, exclude=slug)


def set_status(slug, fid, status, note=None, root=ROOT):
    """Change one feature's status, refusing a claim the build does not prove."""
    data = load(slug, root)
    feat = next((f for f in data['features'] if f['id'] == fid), None)
    if feat is None:
        raise ValueError('%s has no feature %s' % (slug, fid))
    if status not in STATUSES:
        raise ValueError('status must be one of %s' % ', '.join(STATUSES))
    trial = dict(feat, status=status)
    if status != 'pending':
        why = check(trial, probe(slug, root))
        if why:
            raise ValueError('refused: ' + why)
    feat['status'] = status
    if note is not None:
        feat['notes'] = note
    save(slug, data, root)
    return feat


def add_feature(slug, fid, title, after=None, guards=(), root=ROOT):
    """A sheet this set needs that the catalog did not list (an exterior stair detail sheet, A-604, say), pending."""
    import importlib
    data = load(slug, root)
    if any(f['id'] == fid for f in data['features']):
        raise ValueError('%s already lists %s' % (slug, fid))
    for g in guards:
        importlib.import_module(g)             # a guard that is not a module can never run
    feat = {'id': fid, 'title': title, 'status': 'pending', 'guards': list(guards),
            'notes': ''}
    ids = [f['id'] for f in data['features']]
    at = ids.index(after)+1 if after in ids else len(ids)
    data['features'].insert(at, feat)
    save(slug, data, root)
    return feat


def drop_feature(slug, fid, note, root=ROOT):
    """A catalog sheet this set does not need (a set with no exterior stair has no A-604). The reason is required
       and kept, so the list says why a sheet is missing rather than just missing it."""
    if not note:
        raise ValueError('say why: --note "..."')
    data = load(slug, root)
    feat = next((f for f in data['features'] if f['id'] == fid), None)
    if feat is None:
        raise ValueError('%s has no feature %s' % (slug, fid))
    data['features'].remove(feat)
    data.setdefault('dropped', []).append({'id': fid, 'title': feat['title'], 'why': note})
    save(slug, data, root)


def _opt(argv, flag):
    return [argv[i+1] for i, a in enumerate(argv[:-1]) if a == flag]


def main(argv):
    if argv[:1] == ['_probe']:
        _probe_here(argv[1], argv[2])
        return 0
    if len(argv) < 2 or argv[0] not in ('status', 'next', 'verify', 'set', 'add', 'drop'):
        print(__doc__)
        return 1
    cmd, slug = argv[0], argv[1]
    if cmd in ('status', 'next') and '--json' in argv:
        v = verify(slug)
        interface.emit('progress', dict(v, project=slug, features=load(slug)['features']))
        return 1 if v['false'] else 0
    if cmd == 'status':
        print(status_text(slug))
        v = verify(slug)
        print('\n%(passes)d passes, %(drawn)d drawn, %(pending)d pending' % v['counts'])
        for w in v['false']:
            print('FALSE CLAIM: ' + w)
        return 1 if v['false'] else 0
    if cmd == 'next':
        print(next_text(slug))
        return 0
    if cmd == 'verify':
        v = verify(slug)
        if '--json' in argv:
            interface.emit('progress', dict(v, project=slug))
        else:
            for w in v['false']:
                print('FALSE CLAIM: ' + w)
            for b in v['behind']:
                print('bound but listed pending: %s (arkitect progress set %s %s drawn)'
                      % (b, slug, b))
            print('%(passes)d passes, %(drawn)d drawn, %(pending)d pending of %(total)d; next: %(next)s'
                  % dict(v['counts'], total=v['total'], next=v['next']))
        return 1 if v['false'] else 0
    if cmd in ('add', 'drop'):
        try:
            if cmd == 'add':
                after = _opt(argv, '--after')
                add_feature(slug, argv[2], argv[3], after[0] if after else None, _opt(argv, '--guard'))
            else:
                note = _opt(argv, '--note')
                drop_feature(slug, argv[2], note[0] if note else None)
        except (ValueError, ImportError, IndexError) as exc:
            print(exc, file=sys.stderr)
            return 1
        print('%s: %s %s' % (slug, 'added' if cmd == 'add' else 'dropped', argv[2]))
        return 0
    if cmd == 'set':
        note = argv[argv.index('--note')+1] if '--note' in argv else None
        try:
            f = set_status(slug, argv[2], argv[3], note)
        except (ValueError, RuntimeError) as exc:
            print(exc, file=sys.stderr)
            return 1
        print('%s is %s' % (f['id'], f['status']))
        return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
