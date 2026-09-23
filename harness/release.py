"""The public engine, made from this repository: what ships, what does not, and proof that
what ships works on its own.

    python3 -m harness.release list              # every tracked path, and whether it ships
    python3 -m harness.release snapshot <dir>    # the public snapshot, a fresh git repository
    python3 -m harness.release check             # snapshot to a scratch directory, then run
                                                 # the full suite and the gate THERE

The private repository holds everything: the engine, the private
projects, their ledgers and history. The public one is a SNAPSHOT of the
engine with fresh history -- never a filtered copy of this history, because one
missed path in a history rewrite is public forever.

    release/private.txt   paths that never ship (a line ending in / is a directory, anything
                          else a glob on the tracked path); release/ itself never ships
    release/public/       files the snapshot gets in place of private ones (its README,
                          CLAUDE.md, decisions/README.md), copied over the top

`check` is the test of phase 1: a checkout with no private project in it passes the whole
suite, and nothing that ships names a private project or a word of harness/config.py's
[identity] private_words -- a mention is a failure, listed by file.
"""
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIVATE = os.path.join('release', 'private.txt')
PUBLIC = os.path.join('release', 'public')


def patterns(root=ROOT):
    """The private patterns, release/ always among them."""
    out = ['release/']
    p = os.path.join(root, PRIVATE)
    if os.path.exists(p):
        with open(p) as fh:
            out += [ln.strip() for ln in fh if ln.strip() and not ln.lstrip().startswith('#')]
    return out


def is_private(path, pats):
    for pat in pats:
        if pat.endswith('/'):
            if path == pat[:-1] or path.startswith(pat):
                return True
        elif fnmatch.fnmatchcase(path, pat):
            return True
    return False


def tracked(root=ROOT):
    r = subprocess.run(['git', 'ls-files', '-z'], cwd=root, capture_output=True, check=True)
    return [p for p in r.stdout.decode().split('\0') if p]


def split(root=ROOT):
    """(shipped, withheld): every tracked path, by whether the public snapshot gets it."""
    pats = patterns(root)
    ship, hold = [], []
    for p in tracked(root):
        (hold if is_private(p, pats) else ship).append(p)
    return ship, hold


def snapshot(dest, root=ROOT):
    """Write the public engine into `dest` (which must not exist): every shipped path as it
       stands in the working tree, release/public/ over the top, committed once as a fresh
       git repository. Returns the list of paths written."""
    if os.path.exists(dest):
        raise ValueError('%s exists; the snapshot writes a fresh directory' % dest)
    ship, _hold = split(root)
    written = []
    for p in ship:
        src = os.path.join(root, p)
        if not os.path.exists(src):
            continue                            # deleted in the working tree, not yet committed
        os.makedirs(os.path.dirname(os.path.join(dest, p)) or dest, exist_ok=True)
        shutil.copy2(src, os.path.join(dest, p))
        written.append(p)
    pub = os.path.join(root, PUBLIC)
    for d, _dirs, files in os.walk(pub):
        for f in files:
            if f == '.DS_Store':
                continue
            rel = os.path.relpath(os.path.join(d, f), pub)
            os.makedirs(os.path.dirname(os.path.join(dest, rel)) or dest, exist_ok=True)
            shutil.copy2(os.path.join(d, f), os.path.join(dest, rel))
            if rel not in written:
                written.append(rel)
    git = ['git', '-c', 'user.name=arkitect release', '-c', 'user.email=release@localhost']
    for cmd in (['init', '-q'], ['add', '-A'], ['commit', '-q', '-m', 'arkitect: public snapshot']):
        subprocess.run(git + cmd, cwd=dest, check=True, capture_output=True)
    return sorted(written)


def names(root=ROOT):
    """The private projects' slugs, from release/private.txt's project lines."""
    return sorted(m.group(1) for m in (re.match(r'projects/([a-z0-9_]+)/$', p) for p in patterns(root)) if m)


def mentions(dest, words):
    """{word: [files in dest that mention it]}."""
    out = {w: [] for w in words}
    for d, dirs, files in os.walk(dest):
        dirs[:] = [x for x in dirs if x not in ('.git', '__pycache__', '.verify-cache')]
        for f in files:
            p = os.path.join(d, f)
            try:
                with open(p, errors='strict') as fh:
                    text = fh.read()
            except (UnicodeDecodeError, OSError):
                continue
            for w in words:
                if re.search(r'\b%s\b' % re.escape(w), text):
                    out[w].append(os.path.relpath(p, dest))
    return out


def check(root=ROOT, keep=False):
    """Snapshot, then run the full suite and the gate in it. Returns (ok, lines)."""
    work = tempfile.mkdtemp(prefix='arkitect-public-')
    dest = os.path.join(work, 'arkitect')
    lines = []
    try:
        written = snapshot(dest, root)
        lines.append('snapshot: %d files in %s' % (len(written), dest))
        env = dict(os.environ, PYTHONPYCACHEPREFIX=os.path.join(work, 'pycache'))
        t = subprocess.run([sys.executable, os.path.join('lib', 'verify', 'run_tests.py')], cwd=dest,
                           capture_output=True, text=True, env=env, timeout=3600)
        summary = [ln for ln in t.stdout.splitlines() if ln.startswith(('PASSED:', 'FAILED:'))]
        tests_ok = t.returncode == 0 and bool(summary) and summary[-1].startswith('PASSED:')
        lines.append('tests: %s' % (summary[-1] if summary else 'no result'))
        if not tests_ok:
            lines.append((t.stderr + t.stdout)[-3000:])
        g = subprocess.run([sys.executable, os.path.join('lib', 'verify', 'gate.py')], cwd=dest,
                           capture_output=True, text=True, env=env, timeout=3600)
        lines.append('gate: ' + (g.stdout.splitlines()[0] if g.stdout else 'no output'))
        if g.returncode != 0:
            lines.append((g.stdout + g.stderr)[-3000:])
        from harness import config
        found = mentions(dest, names(root) + list(config.get('identity.private_words', root=root)))
        hit = {w: fs for w, fs in found.items() if fs}
        if not hit:
            lines.append('private words: none of %d found' % len(found))
        for w, fs in hit.items():
            lines.append('still mentions %s: %d file(s) -- %s' % (
                w, len(fs), ', '.join(sorted(fs)[:8]) + (' ...' if len(fs) > 8 else '')))
        return tests_ok and g.returncode == 0 and not any(found.values()), lines
    finally:
        if keep:
            lines.append('kept: %s' % dest)
        else:
            shutil.rmtree(work, ignore_errors=True)


def main(argv):
    if not argv or argv[0] not in ('list', 'snapshot', 'check'):
        print(__doc__)
        return 1
    if argv[0] == 'list':
        ship, hold = split()
        print('ships %d, withheld %d' % (len(ship), len(hold)))
        for p in hold:
            print('  withheld  ' + p)
        return 0
    if argv[0] == 'snapshot':
        if len(argv) < 2:
            print('snapshot needs a directory', file=sys.stderr)
            return 1
        print('%d files written to %s' % (len(snapshot(argv[1])), argv[1]))
        return 0
    ok, lines = check(keep='--keep' in argv)
    print('\n'.join(lines))
    print('PUBLIC SNAPSHOT %s' % ('PASSES' if ok else 'FAILS'))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
