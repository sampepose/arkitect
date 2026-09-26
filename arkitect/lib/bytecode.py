"""Bytecode a measuring process can trust, without compiling the world for every process.

Python trusts a .pyc whose source has the same size and mtime (to the second), so a file
rewritten within a second by an edit of the same length -- one constant for another -- ran as
its OLD code, and a tool measured a build that no longer existed. A test that swapped
'PER D-912' for 'DOOR D-4A' found it (arkitect/lib/verify/test_gate.py). The cure was a fresh
PYTHONPYCACHEPREFIX per run, which made every process recompile every library it imported,
reportlab, numpy and ezdxf included: half a second a process, and the test suite starts
hundreds.

So, before a tool starts a process that measures, hash_pycs() gives every source of the
engine and the workspace a CHECKED-HASH pyc in its own __pycache__: trusted only while it
matches the source's bytes, and rewritten by the importer as another checked-hash pyc when it
does not. The libraries keep the ordinary pycs they were installed with, and env() takes out
a PYTHONPYCACHEPREFIX that would send the process to look anywhere else.
"""
import importlib.util
import os
import py_compile
import sys

SKIP = {'.git', '.verify-cache', 'worktrees', '__pycache__'}


def env(base):
    """`base` less PYTHONPYCACHEPREFIX: the process reads the pycs hash_pycs() wrote."""
    return {k: v for k, v in base.items() if k != 'PYTHONPYCACHEPREFIX'}


def pyc(src):
    """Where a process run with env() keeps `src`'s bytecode."""
    return os.path.join(os.path.dirname(src), '__pycache__', '%s.%s.pyc' % (
        os.path.basename(src)[:-3], sys.implementation.cache_tag))


def hash_pycs(*roots):
    """Give every .py under `roots` a checked-hash pyc, compiling only those that have none or
       have a timestamp pyc; the importer checks the rest against their source. A file that
       does not compile is left to whatever imports it to report."""
    for root in sorted(set(roots)):
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP]
            for f in files:
                if not f.endswith('.py'):
                    continue
                src = os.path.join(d, f)
                out = pyc(src)
                try:
                    with open(out, 'rb') as fh:
                        head = fh.read(8)
                    if head[:4] == importlib.util.MAGIC_NUMBER and head[4] & 0b11 == 0b11:
                        continue
                except OSError:
                    pass
                try:
                    py_compile.compile(src, out, doraise=True,
                                       invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH)
                except (py_compile.PyCompileError, OSError, ValueError):
                    pass
