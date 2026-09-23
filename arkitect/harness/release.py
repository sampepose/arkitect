"""Is the engine ready to publish? Nothing it tracks and no commit message in its history names
the installation that built it, and the full gate passes.

    arkitect release check [--no-gate] [--rev REV]     # run it inside YOUR workspace

The engine (arkitect/lib/workspace.py's ENGINE) is its own repository and the projects live in
a workspace beside it. The words are the WORKSPACE's: its arkitect.toml's [identity]
private_words, and -- when the workspace is not the engine -- the slug of every project it
holds. So run `check` in the private workspace; run in the engine itself it has no words to
look for and says so.

What is scanned, in the ENGINE:

    files     every file `git ls-files` lists that reads as UTF-8 text, as it stands
    messages  the message of every commit reachable from REV (default HEAD): the history
              that a push of this branch publishes

A word matches as a whole word, case-sensitive (test_identity.py's rule). A commit's author
and committer names and emails are NOT scanned: they are who made the commit, and a person's
commits to the engine are theirs to publish. A name in the message (a trailer, a quotation)
is scanned like any other text.

Nothing is rewritten. `check` reports each file hit (path:line: word) and each message hit
(short hash subject: words) and exits 1 if there is any, or if the gate (`arkitect gate
--full`, run in the engine on its own examples) fails; 2 if the engine is not a git
repository.
"""
import os
import re
import subprocess
import sys

from arkitect.lib import workspace


def words(ws=None):
    """The private words of workspace `ws` (default the one this process found), then its
       projects' slugs when it is not the engine."""
    from arkitect.harness import config
    ws = ws or workspace.WORKSPACE
    out = list(config.get('identity.private_words', root=ws))
    if workspace.separate(ws):
        base = os.path.join(ws, workspace.PROJECTS)
        if os.path.isdir(base):
            out += sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d, 'src')))
    return out


def pattern(ws_words):
    """Whole words, case-sensitive; None when there is nothing to look for."""
    return re.compile(r'\b(%s)\b' % '|'.join(re.escape(w) for w in ws_words)) if ws_words else None


def tracked(root):
    r = subprocess.run(['git', 'ls-files', '-z'], cwd=root, capture_output=True, check=True)
    return [p for p in r.stdout.decode().split('\0') if p]


def texts(root):
    """(path, text) for every tracked file that exists and reads as UTF-8."""
    for rel in tracked(root):
        try:
            with open(os.path.join(root, rel), errors='strict') as fh:
                yield rel, fh.read()
        except (UnicodeDecodeError, OSError):
            continue


def file_hits(root, ws_words):
    """['path:line: word', ...] for every tracked line that names a word."""
    pat = pattern(ws_words)
    if pat is None:
        return []
    out = []
    for rel, text in texts(root):
        for n, line in enumerate(text.splitlines(), 1):
            for w in sorted(set(pat.findall(line))):
                out.append('%s:%d: %s' % (rel, n, w))
    return out


def commits(root, rev='HEAD'):
    """[(full hash, message)] for every commit reachable from `rev`, newest first. The format
       asks for the message (%B) alone: the author and committer are never read."""
    r = subprocess.run(['git', 'log', '--format=%H%x00%B%x1e', rev], cwd=root,
                       capture_output=True, check=True)
    out = []
    for rec in r.stdout.decode('utf-8', errors='replace').split('\x1e'):
        rec = rec.lstrip('\n')
        if rec:
            h, _nul, msg = rec.partition('\0')
            out.append((h, msg))
    return out


def message_hits(root, ws_words, rev='HEAD'):
    """['<short hash> <subject>: word, word', ...] for every commit whose message names one."""
    pat = pattern(ws_words)
    if pat is None:
        return []
    out = []
    for h, msg in commits(root, rev):
        found = sorted(set(pat.findall(msg)))
        if found:
            subject = msg.strip().splitlines()[0] if msg.strip() else ''
            out.append('%s %s: %s' % (h[:10], subject[:72], ', '.join(found)))
    return out


def gate(root):
    """(ok, first line, tail on failure): `arkitect gate --full` in the engine, on its own
       examples, with the engine first on PYTHONPATH and no inherited workspace."""
    g = subprocess.run([sys.executable, '-m', 'arkitect.harness.cli', 'gate', '--full'], cwd=root,
                       capture_output=True, text=True, env=workspace.env(root, engine=root), timeout=3600)
    first = g.stdout.splitlines()[0] if g.stdout.strip() else 'no output'
    tail = '' if g.returncode == 0 else (g.stdout + g.stderr)[-3000:]
    return g.returncode == 0, first, tail


def check(root=None, ws=None, rev='HEAD', run_gate=True):
    """(status, lines): status 0 ready, 1 not, 2 could not look."""
    root = root or workspace.ENGINE
    ws = ws or workspace.WORKSPACE
    if not os.path.exists(os.path.join(root, '.git')):
        return 2, ['%s is not a git repository' % root]
    ws_words = words(ws)
    lines = ['engine: %s' % root,
             'words: %d, from the workspace %s' % (len(ws_words), ws)]
    if not ws_words:
        lines.append('no private words to look for: run this inside your workspace')
    fh = file_hits(root, ws_words)
    mh = message_hits(root, ws_words, rev)
    lines.append('files: %d tracked, %d line(s) name a private word' % (len(tracked(root)), len(fh)))
    lines += ['  ' + x for x in fh]
    lines.append('commit messages: %d reachable from %s, %d name a private word'
                 % (len(commits(root, rev)), rev, len(mh)))
    lines += ['  ' + x for x in mh]
    ok = not fh and not mh
    if run_gate:
        g_ok, first, tail = gate(root)
        lines.append('gate --full: ' + first)
        if tail:
            lines.append(tail)
        ok = ok and g_ok
    else:
        lines.append('gate --full: not run (--no-gate)')
    return (0 if ok else 1), lines


def main(argv):
    if not argv or argv[0] != 'check':
        print(__doc__)
        return 1
    rev = argv[argv.index('--rev') + 1] if '--rev' in argv else 'HEAD'
    status, lines = check(rev=rev, run_gate='--no-gate' not in argv)
    print('\n'.join(lines))
    print('ENGINE RELEASE %s' % {0: 'READY', 1: 'NOT READY', 2: 'NOT CHECKED'}[status])
    return status


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
