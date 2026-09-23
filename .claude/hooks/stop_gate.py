"""Stop hook: a turn does not end on uncommitted work the gate has not passed.

The policy is arkitect/harness/config.py's [hooks] table. By default a new installation is ADVISED,
never held: the turn ends and the problem is shown ("advise" for both). The stricter setting
this repository's designer runs, option C:

    no change in the checkout                  let the turn end, silently
    gate GREEN, changes uncommitted            green_uncommitted = "block": BLOCK, every
                                               session -- commit now, by name, saying which
                                               sheets moved ("advise" shows it, "off" allows)
    gate RED                                   red = "block-unattended": BLOCK a session
                                               nobody watches (a background job, a worktree);
                                               in an attended one, let the turn end with the
                                               failures shown -- the person there may have
                                               asked "what breaks if..." ("block", "advise",
                                               "off" also)

and whatever the policy:
    a worktree's deliverables dirty            BLOCK: restore them; the merger regenerates
    a PDF dirty whose drawing did not move     BLOCK: it is reportlab's timestamp; restore it

Three blocks in a row and the turn ends anyway, with the reason shown: a gate that cannot
be satisfied must not trap a session in a loop. The count resets whenever a turn ends.

The gate's report is cached against the state of the tree (HEAD, the diff, the untracked
files), so a second stop on an unchanged tree costs a `git diff`, not a build.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402

MAX_BLOCKS = 3
GATE_TIMEOUT = 240
DELIVERABLE = ('.pdf', '.dxf')


def _git(root, *args):
    r = subprocess.run(['git'] + list(args), cwd=root, capture_output=True, timeout=60)
    return r.stdout if r.returncode == 0 else b''


def changes(root):
    """Every path `git status` reports, tracked or untracked (ignored files excluded)."""
    out = _git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    paths, items = [], out.split(b'\0')
    i = 0
    while i < len(items):
        entry = items[i].decode('utf-8', 'replace')
        i += 1
        if len(entry) < 4:
            continue
        xy, path = entry[:2], entry[3:]
        if 'R' in xy or 'C' in xy:
            i += 1                                # a rename carries its old path next
        paths.append(path)
    return paths


def state_key(root, paths):
    h = hashlib.sha1(_git(root, 'rev-parse', 'HEAD'))
    h.update(_git(root, 'diff', 'HEAD', '--binary'))
    for p in sorted(paths):
        try:
            st = os.stat(os.path.join(root, p))
            h.update(('%s %d %d\n' % (p, st.st_size, st.st_mtime_ns)).encode())
        except OSError:
            h.update(p.encode())
    return h.hexdigest()


def run_gate(root):
    """The gate's JSON report, or a synthetic red one saying why it could not run."""
    gate = os.path.join(root, 'arkitect', 'lib', 'verify', 'gate.py')
    if not os.path.exists(gate):
        # a projects repository measured by the engine these hooks came from
        gate = os.path.join(hooklib.ENGINE, 'arkitect', 'lib', 'verify', 'gate.py')
        if not os.path.isdir(os.path.join(root, 'projects')):
            return None                            # neither an engine nor a workspace
        if not os.path.exists(gate):
            return {'ok': False, 'projects': {}, 'failures': [],
                    'errors': ['no gate: %s has projects/ but the engine at %s is gone'
                               % (root, hooklib.ENGINE)]}
    try:
        r = subprocess.run([sys.executable, gate, '--json'], cwd=root, capture_output=True,
                           text=True, timeout=GATE_TIMEOUT)
        return json.loads(r.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return {'ok': False, 'projects': {}, 'failures': [],
                'errors': ['the gate could not run: %s' % exc]}


def _slug(path):
    parts = path.split('/')
    return parts[1] if len(parts) > 2 and parts[0] == 'projects' else None


DEFAULT_POLICY = {'green_uncommitted': 'advise', 'red': 'advise'}


def policy(root):
    """The [hooks] table of arkitect/harness/config.py for this checkout, or the defaults."""
    try:
        sys.path.insert(0, hooklib.ENGINE)
        from arkitect.harness import config
        return dict(DEFAULT_POLICY, **config.load(root=root)['hooks'])
    except Exception:
        return dict(DEFAULT_POLICY)


def decide(paths, report, attended, worktree, blocks, rules=None):
    """(action, message): action is 'allow', 'advise' or 'block'. Pure, for the tests.
       `rules` is the [hooks] policy; the defaults when it is None."""
    rules = dict(DEFAULT_POLICY, **(rules or {}))
    if not paths:
        return 'allow', ''
    deliverables = [p for p in paths if p.lower().endswith(DELIVERABLE)]
    source = [p for p in paths if p not in deliverables]
    projects = (report or {}).get('projects', {})

    if worktree and deliverables:
        action, msg = 'block', (
            'The tracked deliverables changed in this worktree: %s. A worktree never commits '
            'them -- the merger regenerates them. Restore them: git checkout -- %s'
            % (', '.join(deliverables), ' '.join(deliverables)))
    else:
        stale = [p for p in deliverables if projects.get(_slug(p), {}).get('sheets_moved') == []]
        if stale:
            action, msg = 'block', (
                'These deliverables changed but their drawing did not (the gate finds no sheet '
                'moved), so the change is reportlab\'s embedded timestamp. Restore them rather '
                'than commit the noise: git checkout -- %s' % ' '.join(stale))
        elif report is None:
            action, msg = 'allow', ''              # no gate in this checkout: nothing to hold to
        elif not report.get('ok'):
            problems = report.get('errors', []) + report.get('failures', [])
            text = 'arkitect/lib/verify/gate.py is RED:\n- ' + '\n- '.join(problems)
            red = rules['red']
            if red == 'off':
                action, msg = 'allow', ''
            elif red == 'advise' or (red == 'block-unattended' and attended):
                action, msg = 'advise', text + '\n(uncommitted; the turn ends so the person here can decide)'
            else:
                action, msg = 'block', (text + '\nFix it and run `python3 -m arkitect.lib.verify.gate` '
                                        'again. If it cannot be fixed, say so plainly in your reply.')
        else:
            moved = ['%s %s' % (s, ', '.join(m['sheet'] for m in p['sheets_moved']))
                     for s, p in sorted(projects.items()) if p.get('sheets_moved')]
            action, msg = 'block', (
                'arkitect/lib/verify/gate.py is green and these changes are uncommitted:\n  %s\n'
                'Commit them now -- add each file BY NAME (never -A), one change per commit%s. '
                'A file that is scratch belongs outside the checkout; delete it instead.' % (
                    '\n  '.join(source + deliverables),
                    ('; the message says: Sheets moved: ' + '; '.join(moved)) if moved else ''))
            green = rules['green_uncommitted']
            if green == 'off':
                action, msg = 'allow', ''
            elif green == 'advise':
                action = 'advise'

    if action == 'block' and blocks >= MAX_BLOCKS:
        return 'advise', ('Stop hook: %d blocks in a row, letting the turn end. The last one was:\n%s'
                          % (blocks, msg))
    return action, msg


def _state_path(session):
    d = os.path.join(tempfile.gettempdir(), 'claude-stop-gate')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, '%s.json' % (session or 'none'))


def main():
    data = hooklib.read_input()
    root = hooklib.repo_root(data.get('cwd'))
    if not root:
        return 0
    paths = changes(root)
    state_file = _state_path(data.get('session_id'))
    try:
        with open(state_file) as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        state = {}

    report = None
    if paths:
        key = state_key(root, paths)
        if state.get('key') == key and state.get('root') == root:
            report = state.get('report')
        else:
            report = run_gate(root)
        state.update(key=key, root=root, report=report)

    # The main checkout's settings and a worktree's wire this hook with the SAME command
    # string, which Claude Code runs once. A time window that tried to merge two calls into
    # one decision also merged a session's quick retries, and the cap never fired: a live
    # trial blocked nine times running.
    action, msg = decide(paths, report, not hooklib.unattended(root=root),
                         hooklib.in_worktree(root), state.get('blocks', 0), policy(root))
    state['blocks'] = state.get('blocks', 0) + 1 if action == 'block' else 0
    try:
        with open(state_file, 'w') as fh:
            json.dump(state, fh)
    except OSError:
        pass

    if action == 'block':
        print(msg, file=sys.stderr)
        return 2
    if action == 'advise':
        print(json.dumps({'systemMessage': msg}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
