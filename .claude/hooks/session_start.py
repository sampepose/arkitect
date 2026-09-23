"""SessionStart hook: tell a new session where it stands before it trusts anything.

Several sessions commit to main at once (CLAUDE.md "Concurrency"), so a figure measured an
hour ago may already be stale. What this prints goes into Claude's context: the branch,
the last five commits, and -- off main -- how far main has moved since the branch was cut.
Cheap on purpose: git only, no build.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402


def _git(root, *args):
    r = subprocess.run(['git'] + list(args), cwd=root, capture_output=True, text=True, timeout=20)
    return r.stdout.strip() if r.returncode == 0 else ''


def shared_lines(root):
    """In a projects repository, the engine's skills and agents linked if this checkout has
       none (a fresh clone or worktree): they are local links, never committed."""
    if os.path.isdir(os.path.join(root, 'arkitect', 'lib')) or not os.path.isdir(os.path.join(root, 'projects')):
        return []                               # the engine itself, or not a workspace
    try:
        sys.path.insert(0, hooklib.ENGINE)
        from arkitect.harness import hooks
        made = hooks.link_shared(root)
    except Exception as exc:                    # a hook that fails to start helps nobody
        return ['Could not link the engine\'s skills and agents: %s' % exc]
    return (['Linked the engine\'s %s into .claude/; restart the session to load them.'
             % ' and '.join(os.path.basename(m) for m in made)] if made else [])


def progress_lines(root):
    """One line per project with a feature list: the handoff from the last session. Read
       from progress.json alone -- no build -- so a session starts in a second; the gate is
       what proves the claims."""
    out = []
    base = os.path.join(root, 'projects')
    for slug in sorted(os.listdir(base)) if os.path.isdir(base) else ():
        path = os.path.join(base, slug, 'progress.json')
        if not os.path.exists(path):
            continue
        try:
            with open(path) as fh:
                feats = json.load(fh)['features']
        except (OSError, ValueError, KeyError):
            out.append('%s: progress.json unreadable' % slug)
            continue
        done = sum(1 for f in feats if f['status'] == 'passes')
        nxt = next((f for f in feats if f['status'] != 'passes'), None)
        out.append('%s: %d of %d features pass; next %s' % (
            slug, done, len(feats), '%s %s (arkitect progress next %s)'
            % (nxt['id'], nxt['title'], slug) if nxt else '-- none, every feature passes'))
    return out


def decision_lines(root):
    """How many decisions wait on the designer: the ledger in decisions/, read by its status lines."""
    d = os.path.join(root, 'decisions')
    if not os.path.isdir(d):
        return []
    counts = {}
    for f in os.listdir(d):
        if f.endswith('.md'):
            with open(os.path.join(d, f)) as fh:
                m = re.search(r'^status: (\w+)$', fh.read(), re.M)
            if m:
                counts[m.group(1)] = counts.get(m.group(1), 0)+1
    return ['Decisions: %d open for the designer, %d waiting on others (arkitect decisions '
            'pending). A new call among code-legal options is recorded with '
            '`arkitect decisions new`, and cited by its id.'
            % (counts.get('open', 0), counts.get('waiting', 0))]


def review_lines(root):
    """Open plan-review findings per project (arkitect/harness/review.py), by severity."""
    out = []
    base = os.path.join(root, 'projects')
    for slug in sorted(os.listdir(base)) if os.path.isdir(base) else ():
        p = os.path.join(base, slug, 'review.json')
        if not os.path.exists(p):
            continue
        try:
            with open(p) as fh:
                opn = [f for f in json.load(fh)['findings'] if f['status'] == 'open']
        except (OSError, ValueError, KeyError):
            out.append('%s: review.json unreadable' % slug)
            continue
        if opn:
            by = {}
            for f in opn:
                by[f['severity']] = by.get(f['severity'], 0)+1
            out.append('%s: %d open review finding(s) (%s); arkitect review next %s'
                       % (slug, len(opn), ', '.join('%d %s' % (by[k], k) for k in
                                                     ('blocker', 'major', 'minor') if k in by), slug))
    return out


def main():
    data = hooklib.read_input()
    root = hooklib.repo_root(data.get('cwd'))
    if not root:
        return 0
    branch = _git(root, 'rev-parse', '--abbrev-ref', 'HEAD')
    lines = ['Checkout: %s (branch %s)' % (root, branch or '?'),
             'Last commits:', _git(root, 'log', '--oneline', '-5')]
    if branch and branch != 'main':
        ahead = _git(root, 'rev-list', '--count', 'HEAD..main')
        if ahead and ahead != '0':
            lines.append('main has %s commit(s) this branch does not: re-measure before trusting '
                         'an earlier figure.' % ahead)
    lines += shared_lines(root)
    lines += progress_lines(root)
    lines += decision_lines(root)
    lines += review_lines(root)
    lines.append('Check work with `arkitect gate`; the Stop hook runs it when a turn ends.')
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
