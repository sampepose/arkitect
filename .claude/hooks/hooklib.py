"""What the hooks in this directory share: reading a hook's input, finding the checkout it
fired in, telling an unattended session from one a person is sitting in, and reading a shell
command well enough to judge it.

The hooks are a seatbelt, not a sandbox. They read the command Claude is about to run and
refuse the handful of shapes that have cost this repository real time -- `git add -A`, an
oracle whose stderr went to /dev/null, a hand-written trace.md5, a worktree rewriting the
deliverables. A determined `python3 -c` gets past every one of them; arkitect/lib/verify/gate.py,
which recomputes everything, is what cannot be talked past.
"""
import json
import os
import re
import subprocess
import sys


def read_input():
    """The hook's JSON on stdin, or {} when there is none (a person running it by hand)."""
    try:
        data = sys.stdin.read()
        return json.loads(data) if data.strip() else {}
    except ValueError:
        return {}


# The engine these hook scripts belong to: the checkout they fired in, or -- in a projects
# repository that installed them from outside (python3 -m arkitect.harness.hooks install) -- the
# engine that repository uses.
ENGINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def repo_root(cwd=None):
    """The checkout the hook fired in: the WORKTREE when the session is in one, which is
       why this reads the hook's cwd and not CLAUDE_PROJECT_DIR."""
    cwd = cwd or os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()
    try:
        r = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=cwd,
                           capture_output=True, text=True, timeout=20)
        if r.returncode == 0:
            return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def in_worktree(path):
    """A checkout under .claude/worktrees/: a parallel session's isolated copy."""
    return bool(path) and (os.sep + os.path.join('.claude', 'worktrees') + os.sep) in path + os.sep


def unattended(env=None, root=None):
    """True for a background job or a worktree session, where nobody watches a turn end.
       Background jobs carry CLAUDE_CODE_SESSION_ATTENDED=0 and CLAUDE_JOB_DIR; a worktree
       is recognised by its path, which holds even if a hook runs without the session's
       environment."""
    env = os.environ if env is None else env
    if env.get('CLAUDE_CODE_SESSION_ATTENDED') == '0' or env.get('CLAUDE_JOB_DIR'):
        return True
    return in_worktree(root)


# ---------------------------------------------------------------- reading a shell command

_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?=\n|$)", re.S)
_QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")
_SPLIT = re.compile(r"(&&|\|\||;|\n|(?<![>&])\|(?!\|))")


def _unquote(m):
    """A quoted word with no space in it is a path or a flag and is kept, unquoted; a
       quoted phrase is a message or a script and is blanked, so `git commit -m "never
       git add -A"` is not read as the command it mentions."""
    body = m.group(0)[1:-1]
    return body if body and not re.search(r"\s", body) else "''"


def segments(command):
    """[(simple command, the operator after it)] for a shell line: heredoc bodies and
       quoted phrases removed, then split at && || ; | and newlines, the last operator ''.
       Redirections stay with their command."""
    text = _QUOTED.sub(_unquote, _HEREDOC.sub('<<HEREDOC', command))
    parts = _SPLIT.split(text)
    out = []
    for i in range(0, len(parts), 2):
        seg = parts[i].strip()
        op = parts[i + 1] if i + 1 < len(parts) else ''
        if seg:
            out.append((seg, op))
        elif out and op:
            out[-1] = (out[-1][0], op)
    return out
