"""One recording of a build, kept under everything the build depends on, so a project is
built once for every tool and test that asks for the same build.

A build is a function of the files it reads and the Python that runs it. The gate, the trace
digest test, the sheet index test, the DXF frame test and sheet_text all asked for the same
build of the same tree, and each built it again: five or six builds of each project in one
suite. arkitect/lib/verify/trace.py now records everything once -- the trace, what the build
printed, the per-sheet digests, the sheet text, the DXF and the PDFs -- into a directory named
for key(), and serves the next request for any of it from there.

THE KEY is everything a build can read, so a changed input is a new key and never a stale hit:

    every file of the workspace and of the engine, by content (sha256), and of every
        directory on PYTHONPATH besides them -- except the repository's own machinery (.git),
        caches (.verify-cache, __pycache__), .claude, and the outputs a build writes and never
        reads (*.pdf, *.dxf)
    the user's ~/.config/arkitect/config.toml, which arkitect/harness/config.py merges in
    the build's path within the workspace
    Python's version and -O, and the installed reportlab, rl_accel, ezdxf, numpy and pillow

It is content, not mtime -- an edit of the same size within the same second is a new key --
and it is not the tree's location: a copy of a tree is the same build, which is what lets the
quickstart's and the scaffold tests' fresh copies share one recording. So recordings live in
the user's cache, and trace.py never keeps one that prints the path of the tree it was built
in. Only a project's own build.py under a workspace's projects/ is kept at all; a build that
fails, or a part of one that fails, never is. ARKITECT_BUILD_CACHE=off turns it off.
"""
import contextlib
import hashlib
import os
import shutil
import sys
import time

SKIP_DIRS = {'.git', '.verify-cache', '__pycache__', '.claude', 'node_modules'}
SKIP_SUFFIX = ('.pdf', '.dxf', '.pyc', '.DS_Store')
PACKAGES = ('reportlab', 'rl_accel', 'ezdxf', 'numpy', 'pillow')
MOST_FILES = 5000             # a PYTHONPATH directory bigger than this is not hashed: not kept
LIMIT = 400 * 1024 * 1024     # bytes of recordings kept, oldest-used dropped first
IN_USE = 600                  # seconds: a recording used this recently is never dropped
# what a recording holds, as trace.py writes it
PARTS = ('trace.txt', 'stdout.txt', 'sheets.txt', 'text.json', 'pages.json', 'floor.dxf', 'pdf',
         'summary.txt', 'dxf-summary.txt')
TEXT_PARTS = ('trace.txt', 'stdout.txt', 'sheets.txt', 'text.json', 'pages.json', 'summary.txt',
              'dxf-summary.txt')


class _TooBig(Exception):
    pass


def _tree(h, root, most=None):
    n = 0
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            if f.endswith(SKIP_SUFFIX):
                continue
            n += 1
            if most and n > most:
                raise _TooBig(root)
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


def usable(build, workspace):
    """True when this build's recording may be kept: a project's build.py under the workspace."""
    if os.environ.get('ARKITECT_BUILD_CACHE', '').lower() in ('off', '0', 'no'):
        return False
    rel = os.path.relpath(os.path.realpath(build), os.path.realpath(workspace)).split(os.sep)
    return len(rel) == 3 and rel[0] == 'projects' and rel[2] == 'build.py'


def key(build, engine, workspace, home=None, pythonpath=None):
    """The recording's name: a digest of everything the build can read (module docstring), or
       None where that cannot be hashed (a PYTHONPATH directory past MOST_FILES). `pythonpath`
       is the PYTHONPATH of the process that builds, when that is not this one."""
    h = hashlib.sha256()
    h.update(('\n'.join([sys.version, 'O=%d' % sys.flags.optimize] + _versions())).encode())
    ws, en = os.path.realpath(workspace), os.path.realpath(engine)
    h.update(b'\nBUILD ' + os.path.relpath(os.path.realpath(build), ws).encode())
    h.update(b'\nWORKSPACE\n')
    _tree(h, ws)
    if en != ws:
        h.update(b'\nENGINE\n')
        _tree(h, en)
    covered = [ws, en]
    if pythonpath is None:
        pythonpath = os.environ.get('PYTHONPATH', '')
    for p in filter(None, pythonpath.split(os.pathsep)):
        rp = os.path.realpath(p)
        if not os.path.isdir(rp) or any(rp == t or rp.startswith(t + os.sep) for t in covered):
            continue
        h.update(b'\nPYTHONPATH ' + str(len(covered)).encode() + b'\n')
        try:
            _tree(h, rp, MOST_FILES)
        except _TooBig:
            return None
        covered.append(rp)
    cfg = os.path.join(home or os.path.expanduser('~'), '.config', 'arkitect', 'config.toml')
    if os.path.exists(cfg):
        with open(cfg, 'rb') as fh:
            h.update(b'\nCONFIG ' + hashlib.sha256(fh.read()).digest())
    return h.hexdigest()[:32]


def directory():
    base = os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~'), '.cache')
    # .noindex: Spotlight leaves it alone, which it does not a directory rewritten this often
    return os.path.join(base, 'arkitect', 'builds.noindex')


def found(k):
    """The recording's directory if it is whole, else None. Finding it marks it used."""
    d = os.path.join(directory(), k)
    done = os.path.join(d, 'DONE')
    if not os.path.exists(done):
        return None
    try:
        os.utime(done)
    except OSError:
        return None
    return d


def names_its_tree(staged, *trees):
    """True if any text part of the recording in `staged` prints one of `trees` by path: such
       a recording is of that location, not of the content every copy shares."""
    paths = {p for t in trees for p in (t, os.path.realpath(t))}
    for part in TEXT_PARTS:
        f = os.path.join(staged, part)
        if os.path.exists(f):
            with open(f, errors='replace') as fh:
                text = fh.read()
            if any(p in text for p in paths):
                return True
    return False


@contextlib.contextmanager
def locked(k):
    """One process records a key at a time; the rest wait, then find it."""
    import fcntl
    os.makedirs(directory(), exist_ok=True)
    with open(os.path.join(directory(), k + '.lock'), 'w') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _size(d):
    return sum(os.path.getsize(os.path.join(r, f)) for r, _ds, fs in os.walk(d) for f in fs)


def keep(k, staged):
    """Move a whole recording in `staged` into place under `k`, then drop the least recently
       used past LIMIT, never one used in the last IN_USE seconds."""
    base = directory()
    with open(os.path.join(staged, 'DONE'), 'w') as fh:
        fh.write(k)
    dest = os.path.join(base, k)
    if os.path.exists(dest):
        shutil.rmtree(staged, True)
    else:
        os.rename(staged, dest)
    used = []
    for d in os.listdir(base):
        done = os.path.join(base, d, 'DONE')
        if os.path.exists(done):
            used.append((os.path.getmtime(done), d))
    used.sort(reverse=True)
    total, now = 0, time.time()
    for when, d in used:
        total += _size(os.path.join(base, d))
        if total > LIMIT and now - when > IN_USE:
            shutil.rmtree(os.path.join(base, d), True)
            try:
                os.remove(os.path.join(base, d + '.lock'))
            except OSError:
                pass
