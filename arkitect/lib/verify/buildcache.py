"""One recording of a build, kept under everything the build depends on, so a project is
built once for every tool and test that asks for the same build.

A build is a function of the files it reads and the Python that runs it. The gate, the trace
digest test, the sheet index test, the DXF frame test and sheet_text all asked for the same
build of the same tree, and each built it again: five or six builds of each project in one
suite. arkitect/lib/verify/trace.py now records everything once -- the trace, what the build
printed, the per-sheet digests, the sheet text, the DXF and the PDFs -- into a directory named
for key(), and serves the next request for any of it from there.

THE KEY is everything a build can read, so a changed input is a new key and never a stale hit:

    every file of the engine and of the workspace, by content (sha256), except the
        repository's own machinery (.git), caches (.verify-cache, __pycache__), .claude, and
        the outputs a build writes and never reads (*.pdf, *.dxf)
    the user's ~/.config/arkitect/config.toml, which arkitect/harness/config.py merges in
    the build's path within the workspace
    Python's version and -O, and the installed reportlab, rl_accel, ezdxf, numpy and pillow

It is content, not mtime: an edit of the same size within the same second is a new key (the
failure arkitect/lib/bytecode.py exists for). Only a project's own build.py, under the
workspace's projects/, with nothing on PYTHONPATH outside the engine and the workspace, is
kept at all; anything else -- a scratch build in a temporary directory, say -- is built as it
always was. A build that fails, or a part of one that fails, is never kept.
ARKITECT_BUILD_CACHE=off turns it off.
"""
import contextlib
import hashlib
import os
import shutil
import sys

SKIP_DIRS = {'.git', '.verify-cache', '__pycache__', '.claude', 'node_modules'}
SKIP_SUFFIX = ('.pdf', '.dxf', '.pyc', '.DS_Store')
PACKAGES = ('reportlab', 'rl_accel', 'ezdxf', 'numpy', 'pillow')
KEEP = 24                     # recordings kept per workspace, newest first
# what a recording holds, as trace.py writes it
PARTS = ('trace.txt', 'stdout.txt', 'sheets.txt', 'text.json', 'pages.json', 'floor.dxf', 'pdf',
         'summary.txt', 'dxf-summary.txt')


def _tree(h, root):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            if f.endswith(SKIP_SUFFIX):
                continue
            p = os.path.join(d, f)
            try:
                with open(p, 'rb') as fh:
                    data = fh.read()
            except OSError:
                continue                       # a dangling link reads as nothing, both times
            h.update(b'F' + os.path.relpath(p, root).encode() + b'\0' +
                     hashlib.sha256(data).digest())


def _versions():
    from importlib import metadata
    out = []
    for p in PACKAGES:
        try:
            out.append('%s=%s' % (p, metadata.version(p)))
        except metadata.PackageNotFoundError:
            out.append('%s=none' % p)
    return out


def usable(build, engine, workspace):
    """True when this build's recording may be kept: a project's build.py under the
       workspace, and nothing on PYTHONPATH that the key does not cover."""
    if os.environ.get('ARKITECT_BUILD_CACHE', '').lower() in ('off', '0', 'no'):
        return False
    real = os.path.realpath(build)
    ws, en = os.path.realpath(workspace), os.path.realpath(engine)
    rel = os.path.relpath(real, ws).split(os.sep)
    if len(rel) != 3 or rel[0] != 'projects' or rel[2] != 'build.py':
        return False
    for p in filter(None, os.environ.get('PYTHONPATH', '').split(os.pathsep)):
        rp = os.path.realpath(p)
        if not any(rp == t or rp.startswith(t + os.sep) for t in (ws, en)):
            return False
    return True


def key(build, engine, workspace, home=None):
    """The recording's name: a digest of everything the build can read (module docstring)."""
    h = hashlib.sha256()
    h.update(('\n'.join([sys.version, 'O=%d' % sys.flags.optimize] + _versions())).encode())
    ws, en = os.path.realpath(workspace), os.path.realpath(engine)
    h.update(b'\nBUILD ' + os.path.relpath(os.path.realpath(build), ws).encode())
    h.update(b'\nWORKSPACE\n')
    _tree(h, ws)
    if en != ws:
        h.update(b'\nENGINE\n')
        _tree(h, en)
    cfg = os.path.join(home or os.path.expanduser('~'), '.config', 'arkitect', 'config.toml')
    if os.path.exists(cfg):
        with open(cfg, 'rb') as fh:
            h.update(b'\nCONFIG ' + hashlib.sha256(fh.read()).digest())
    return h.hexdigest()[:32]


def directory(workspace):
    return os.path.join(workspace, '.verify-cache', 'builds')


def found(k, workspace):
    """The recording's directory if it is whole, else None."""
    d = os.path.join(directory(workspace), k)
    return d if os.path.exists(os.path.join(d, 'DONE')) else None


@contextlib.contextmanager
def locked(k, workspace):
    """One process records a key at a time; the rest wait, then find it."""
    import fcntl
    os.makedirs(directory(workspace), exist_ok=True)
    with open(os.path.join(directory(workspace), k + '.lock'), 'w') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def keep(k, workspace, staged):
    """Move a whole recording in `staged` into place under `k`, and drop the oldest."""
    base = directory(workspace)
    with open(os.path.join(staged, 'DONE'), 'w') as fh:
        fh.write(k)
    dest = os.path.join(base, k)
    if os.path.exists(dest):
        shutil.rmtree(staged, True)
    else:
        os.rename(staged, dest)
    entries = sorted((d for d in os.listdir(base) if os.path.exists(os.path.join(base, d, 'DONE'))),
                     key=lambda d: os.path.getmtime(os.path.join(base, d, 'DONE')), reverse=True)
    for old in entries[KEEP:]:
        shutil.rmtree(os.path.join(base, old), True)
        try:
            os.remove(os.path.join(base, old + '.lock'))
        except OSError:
            pass
