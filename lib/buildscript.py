"""Loading a project's build script from a tool that needs to re-run it.

lib/export/dxf.py and lib/verify/trace.py both work by running a build with a recording
canvas in place. They used to do that with

    exec(compile(open(BUILD).read(), 'build.py', 'exec'),
         {'__name__': '__main__', '__file__': BUILD})

which runs the script's __main__ block — so the tool got whatever that block does,
including writing the project's real PDFs over themselves. The DXF exporter did exactly
that until it was told to write its canvas somewhere else, and a TEST of the exporter
dirtied tracked files every run.

A build script is a module. Import it and call what it exposes:

    DOCUMENTS   a tuple of functions, one per file the project writes, each
                fn(output_path=None, make_canvas=None) -> the path written

`make_canvas` is how a tool gets its recorder in without patching reportlab, and the
output path is how it keeps the real deliverables out of the way. A script that does
not define DOCUMENTS is assumed to have just build_set.
"""
import importlib.util, os, sys


def load(path):
    """Import a build script by path and return the module. Importing it must not draw
       anything — that is the contract build.py documents at its own build_set().

       `path` is trusted input. Importing a module runs its top level, so this runs
       whatever Python is at that path with this process's privileges. That is the
       point — it is the `python3 build.py` the calling tool is standing in for — but
       it means load() is not a sandbox and does not check anything. Both callers take
       the path from argv on a developer's machine, which is the shape this is for.
       Do not pass it a path that arrived from a request, an upload, or a config
       someone else can write."""
    path = os.path.abspath(path)
    name = "buildscript_" + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None:
        raise ImportError("not a Python file: %s" % path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod          # so dataclasses/pickle inside it can find it
    spec.loader.exec_module(mod)
    return mod


def build_arg(value, tool, usage):
    """The build script a tool was given, or exit naming the projects there are. No tool
       defaults to a project: the engine is used by projects it has never heard of, and a
       default that named one of them would build the wrong set in silence."""
    if value:
        return value
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base = os.path.join(here, 'projects')
    builds = sorted(os.path.join('projects', d, 'build.py') for d in
                    (os.listdir(base) if os.path.isdir(base) else ())
                    if os.path.isfile(os.path.join(base, d, 'build.py')))
    sys.exit('%s: which project? usage: %s\n  projects here: %s'
             % (tool, usage, ', '.join(builds) or 'none'))


def documents(mod):
    """The functions that write this project's files, in the order it writes them."""
    docs = getattr(mod, "DOCUMENTS", None)
    if docs is None:
        docs = (mod.build_set,)
    return tuple(docs)
