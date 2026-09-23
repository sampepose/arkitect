"""PreToolUse hook for Bash: refuse the shell commands that have produced a false green or
a bad commit in this repository. Exit 2 with the reason on stderr; Claude reads it.

Each rule is a function of (segment, context) returning a reason or None, so
arkitect/lib/verify/test_hooks.py can hold every rule to one command it must refuse and one it
must let through.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402

ORACLES = ('build.py', 'dxf.py', 'trace.py', 'run_tests.py', 'gate.py', 'sheet_text.py')
# the same tools run as modules, the form that works in the engine and in a projects repository
MODULES = ('arkitect.lib.verify.gate', 'arkitect.lib.verify.trace', 'arkitect.lib.verify.run_tests', 'arkitect.lib.export.dxf',
           'arkitect.lib.verify.sheet_text')


def _words(seg):
    return seg.split()


def _runs_oracle(seg):
    return any(w.endswith(ORACLES) or w in MODULES for w in _words(seg))


def rule_git_add_all(seg, ctx):
    w = _words(seg)
    if len(w) >= 2 and w[0] == 'git' and 'add' in w[1:3]:
        rest = w[w.index('add') + 1:]
        if any(a in ('-A', '--all', '.', ':/', '-u', '--update') or
               (a.startswith('-') and not a.startswith('--') and 'A' in a) for a in rest):
            return ("never `git add -A` / `git add .` / `-u` in this repository: other sessions' "
                    "worktrees and files live here and have been swept into commits twice. "
                    "Add the files you changed BY NAME.")
    if len(w) >= 2 and w[0] == 'git' and 'commit' in w[1:3]:
        rest = w[w.index('commit') + 1:]
        # --all, or a short-option cluster holding a: -a, -am, -qa
        if any(a == '--all' or re.fullmatch(r'-[b-zA-Z]*a[a-zA-Z]*', a) for a in rest):
            return "never `git commit -a` here: stage the files you changed by name, then commit."
    return None


def rule_test_runner(seg, ctx):
    w = _words(seg)
    if 'pytest' in w or ('unittest' in w and 'discover' in w) or \
            any(x.endswith('pytest') for x in w[:1]):
        return ("run `python3 -m arkitect.lib.verify.run_tests` (or `python3 -m arkitect.lib.verify.gate --full`): "
                "`unittest discover` with a mistyped pattern and `pytest -k` that deselects "
                "everything both exit 0 after running nothing.")
    return None


def rule_hidden_stderr(seg, ctx):
    if not _runs_oracle(seg):
        return None
    s = seg.replace(' ', '')
    hides = ('2>/dev/null' in s or '&>/dev/null' in s or '>&/dev/null' in s or
             ('>/dev/null' in s and '2>&1' in s))
    if hides:
        return ("do not discard an oracle's stderr: the DXF exporter was dead for several "
                "commits behind `>/dev/null 2>&1 && echo rebuilt`. Run it plainly, or run "
                "`python3 -m arkitect.lib.verify.gate`, which reads every exit status and keeps stderr.")
    return None


def rule_masked_exit(segs, ctx):
    """`oracle || true` and `oracle && echo ok` report the echo, not the oracle."""
    for (seg, op), (nxt, _op) in zip(segs, segs[1:]):
        if _runs_oracle(seg) and op in ('||', '&&') and re.fullmatch(r'(true|:|echo\b.*)', nxt):
            return ("do not follow an oracle with `|| true` or `&& echo`: the exit status is "
                    "the result. Run it plainly, or run `python3 -m arkitect.lib.verify.gate`.")
    return None


def rule_worktree_deliverables(seg, ctx):
    if not hooklib.in_worktree(ctx.get('root')):
        return None
    w = _words(seg)
    py = [i for i, x in enumerate(w) if re.fullmatch(r'(\S*/)?python3?(\.\d+)?', x)]
    for i in py:
        args = [a for a in w[i + 1:] if not a.startswith('-')]
        if not args:
            continue
        script = args[0]
        if re.search(r'(^|/)projects/[^/]+/build\.py$', script):
            return ("a worktree does not rewrite the tracked PDFs: the merger regenerates them. "
                    "To look at a sheet: `python3 -m arkitect.lib.verify.gate render --sheets A-101` "
                    "(PNGs outside the checkout); to check the build: `python3 -m arkitect.lib.verify.gate`.")
        if script.endswith('export/dxf.py') and len(args) < 3:
            return ("in a worktree, give arkitect/lib/export/dxf.py an output path outside the checkout "
                    "(`python3 -m arkitect.lib.export.dxf <build.py> /tmp/x.dxf`); without one it rewrites "
                    "the tracked DXF, which the merger regenerates.")
    return None


# Files one tool writes, and what to say to anything else that tries.
TOOL_WRITTEN = {
    'trace.md5': ("trace.md5 is written by `python3 -m arkitect.lib.verify.gate accept` and nothing else: "
                  "review what moved first (`gate.py`, `gate.py render --moved`), then accept, and "
                  "name the sheets it prints in the commit message."),
    'progress.json': ("progress.json is written by `python3 -m arkitect.harness.progress set / add / drop` "
                      "and nothing else: `set` refuses a claim the build does not prove."),
    'review.json': ("review.json is written by `python3 -m arkitect.harness.review ingest / set` and nothing "
                    "else: `set ... fixed` refuses unless the finding's sheet has changed."),
}


def rule_trace_md5(seg, ctx):
    for name, why in TOOL_WRITTEN.items():
        if name not in seg:
            continue
        w = _words(seg)
        s = seg.replace(' ', '')
        writes = (re.search(r'>>?[^>&]*' + re.escape(name), s) or
                  (w and w[0] in ('tee', 'cp', 'mv', 'install', 'dd', 'truncate') and
                   w[-1].endswith(name)) or
                  (w and w[0] == 'sed' and any(a.startswith('-i') for a in w)))
        if writes:
            return why
    return None


SEGMENT_RULES = (rule_git_add_all, rule_test_runner, rule_hidden_stderr,
                 rule_worktree_deliverables, rule_trace_md5)


def check(command, root=None):
    """The first reason this command is refused, or None."""
    segs = hooklib.segments(command)
    ctx = {'root': root}
    for seg, _op in segs:
        for rule in SEGMENT_RULES:
            why = rule(seg, ctx)
            if why:
                return why
    return rule_masked_exit(segs, ctx)


def main():
    data = hooklib.read_input()
    command = (data.get('tool_input') or {}).get('command', '')
    why = check(command, hooklib.repo_root(data.get('cwd')))
    if why:
        print('Blocked by .claude/hooks/guard_bash.py: ' + why, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
