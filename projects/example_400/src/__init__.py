"""400 Oak Ave — this lot, and nothing else. (Copied from 300 S Elm; the history below is that project's.)

A package, not a directory on sys.path. It used to be the latter: build.py and both
tools did `sys.path.insert(0, HERE/'src')` and imported `levels`, `mirror`, `project`
by bare name, which put eight of this project's module names into the same flat
namespace as the standard library's. That is not a hypothetical cost — a module here
called `site.py` silently resolved to CPython's own `site`, and `from site import *`
returned the interpreter's module with no error at all. It is `sitework.py` now for
that reason and no other.

Import from here: `from src.levels import FF1`, never `import levels`.
"""
