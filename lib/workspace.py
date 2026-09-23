"""Where the engine is, and where the projects are. They are two directories, and they may be
the same one.

    ENGINE      this checkout of the engine: lib/, codes/, harness/, style/, the tools
    WORKSPACE   the directory holding projects/, decisions/ and arkitect.toml -- a private
                projects repository that uses this engine, or the engine itself

A tool reads its own code, its examples and its house style from ENGINE, and the projects it
measures, their ledger, their review files, their caches and their settings from WORKSPACE.
WORKSPACE is, in order:

    1. $ARKITECT_WORKSPACE, if it is set
    2. the nearest directory at or above the current one that holds a projects/ directory
    3. ENGINE

so `python3 ../arkitect/lib/verify/gate.py` run inside a projects repository measures that
repository, and the same command run inside the engine measures the engine's examples.
Every process a tool starts is started IN its workspace, with the variable cleared (env()),
so the answer travels with the directory and never leaks into a scratch repository.
"""
import os

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = 'ARKITECT_WORKSPACE'
PROJECTS = 'projects'


def find(cwd=None, environ=None):
    """The workspace for a process started in `cwd` with `environ`."""
    environ = os.environ if environ is None else environ
    if environ.get(ENV):
        return os.path.abspath(environ[ENV])
    d = os.path.abspath(cwd or os.getcwd())
    while True:
        if os.path.isdir(os.path.join(d, PROJECTS)):
            return d
        up = os.path.dirname(d)
        if up == d:
            return ENGINE
        d = up


WORKSPACE = find()


def separate(workspace=None):
    """True when the projects live outside the engine."""
    return os.path.realpath(workspace or WORKSPACE) != os.path.realpath(ENGINE)


def env(workspace=None, engine=None, base=None):
    """`base` (default os.environ) for a process started IN `workspace`, with `engine` first on
       PYTHONPATH. $ARKITECT_WORKSPACE is taken out, so the process finds its workspace from
       the directory it starts in: a tool measuring an exported base starts there, and a test
       that runs a tool in a scratch repository gets that repository, never the caller's.
       `workspace` is accepted for the caller's clarity; the cwd is what carries it."""
    out = dict(os.environ if base is None else base)
    out.pop(ENV, None)
    engine = engine or ENGINE
    path = [p for p in out.get('PYTHONPATH', '').split(os.pathsep) if p and p != engine]
    out['PYTHONPATH'] = os.pathsep.join([engine] + path)
    return out


def setting(section, key, default, workspace=None):
    """One value from the workspace's arkitect.toml, for lib/, which may not import
       harness/config.py. harness/config.py reads the same file, and lists every key."""
    import tomllib
    p = os.path.join(workspace or WORKSPACE, 'arkitect.toml')
    if not os.path.exists(p):
        return default
    with open(p, 'rb') as fh:
        return tomllib.load(fh).get(section, {}).get(key, default)
