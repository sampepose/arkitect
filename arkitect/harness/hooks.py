"""The guard-rail hooks are opt-in: this installs them into .claude/settings.json.

    arkitect hooks status       # installed, missing, or out of date against the template
    arkitect hooks install      # wire every hook the template names
    arkitect hooks uninstall    # take them out again; other settings are kept

.claude/hooks/settings.template.json is the wiring the engine ships: SessionStart prints the
checkout's state, PreToolUse refuses the commands and writes that have produced false greens
here (guard_bash.py, guard_write.py), and Stop runs the gate when a turn ends (stop_gate.py),
with the policy arkitect/harness/config.py's [hooks] table sets. Nothing is wired until a person runs
`install`, because a Stop hook that blocks is a working rule its user should choose.

In a projects repository outside the engine (arkitect/lib/workspace.py) each hook runs by name
through the linked engine (`python3 -m arkitect.harness.hook stop_gate`), so the settings name no
path and can be committed; `install` also links .claude/skills and .claude/agents to the
engine's, locally, so a session opened there has the workflows and their reviewers.

`install` merges: every key of settings.json other than a hook this template owns is left as
it was, and a second install changes nothing. A hook is recognised as the template's by its
command, which names .claude/hooks/<file>.py.
"""
import json
import os
import sys

from arkitect.lib import workspace

ENGINE = workspace.ENGINE
ROOT = workspace.WORKSPACE             # where settings.json is written
TEMPLATE = os.path.join('.claude', 'hooks', 'settings.template.json')
SETTINGS = os.path.join('.claude', 'settings.json')
MARK = '/.claude/hooks/'


def _read(path):
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return json.load(fh)


RUNNER = 'python3 -m arkitect.harness.hook '


def template(root=ROOT):
    """The engine's wiring, for `root`. Inside the engine each command finds its script in the
       checkout it fires in, so a worktree runs its own hooks. A projects repository outside
       the engine runs each by name through the linked engine (arkitect/harness/hook.py), so the
       settings it commits name no path; an engine that is not linked fails loudly."""
    hooks = _read(os.path.join(ENGINE, TEMPLATE))['hooks']
    if not workspace.separate(root):
        return hooks
    for groups in hooks.values():
        for g in groups:
            for h in g['hooks']:
                cmd = h['command']
                i, j = cmd.index(MARK), cmd.index('.py', cmd.index(MARK))
                h['command'] = RUNNER + cmd[i+len(MARK):j]
    return hooks


def _ours(group):
    return any(MARK in h.get('command', '') or h.get('command', '').startswith(RUNNER)
               for h in group.get('hooks', []))


def _without(hooks):
    """`hooks` with every group the template owns taken out, and empty events dropped."""
    out = {}
    for event, groups in hooks.items():
        kept = [g for g in groups if not _ours(g)]
        if kept:
            out[event] = kept
    return out


def status(root=ROOT):
    """'installed', 'not installed' or 'out of date'."""
    have = _read(os.path.join(root, SETTINGS)).get('hooks', {})
    ours = {e: [g for g in gs if _ours(g)] for e, gs in have.items()}
    ours = {e: gs for e, gs in ours.items() if gs}
    if not ours:
        return 'not installed'
    return 'installed' if ours == template(root) else 'out of date'


def _write(root, cfg):
    path = os.path.join(root, SETTINGS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        json.dump(cfg, fh, indent=2)
        fh.write('\n')


# What a Claude session opened in a projects repository needs from the engine besides the
# hooks: the skills that run the workflows and the agents they call. Linked, never copied,
# so a change to one reaches every repository at once -- and never committed, since a link
# names this machine's path: `install` makes them, and the SessionStart hook makes them in a
# checkout or worktree that has none (link_shared()).
SHARED = (os.path.join('.claude', 'skills'), os.path.join('.claude', 'agents'))


def link_shared(root=ROOT):
    """Link SHARED into `root` where missing or stale; the paths linked."""
    made = []
    if not workspace.separate(root):
        return made
    for rel in SHARED:
        dest, src = os.path.join(root, rel), os.path.join(ENGINE, rel)
        if os.path.islink(dest) and os.readlink(dest) != src:
            os.remove(dest)
        if not os.path.exists(dest) and not os.path.islink(dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            os.symlink(src, dest)
            made.append(rel)
    return made


def install(root=ROOT):
    cfg = _read(os.path.join(root, SETTINGS))
    hooks = _without(cfg.get('hooks', {}))
    for event, groups in template(root).items():
        hooks.setdefault(event, []).extend(groups)
    cfg['hooks'] = hooks
    _write(root, cfg)
    link_shared(root)


def uninstall(root=ROOT):
    for rel in SHARED:
        dest = os.path.join(root, rel)
        if os.path.islink(dest) and workspace.separate(root):
            os.remove(dest)
    path = os.path.join(root, SETTINGS)
    if not os.path.exists(path):
        return
    cfg = _read(path)
    hooks = _without(cfg.get('hooks', {}))
    if hooks:
        cfg['hooks'] = hooks
    else:
        cfg.pop('hooks', None)
    _write(root, cfg)


def main(argv):
    if not argv or argv[0] not in ('status', 'install', 'uninstall'):
        print(__doc__)
        return 1
    if argv[0] == 'install':
        install()
    elif argv[0] == 'uninstall':
        uninstall()
    print('hooks: %s (%s)' % (status(), SETTINGS))
    if argv[0] == 'install':
        print('Policy: arkitect config show  ([hooks]); restart Claude Code to load them.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
