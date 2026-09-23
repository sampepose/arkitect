"""Find the definitions two projects both carry, word for word.

A project here starts as a copy of the last one, and everything the copy did not need to
change stays in both: the transcribed code tables, the check algorithms, the drawing
helpers. A fault in one of those is then in every project, and a fix made in one never
reaches the others — four faults were found and fixed twice that way before this existed.

This lists every top-level function, class, or assignment of three lines or more that is
byte-identical in the same file of two projects, and sorts each into

    MOVABLE           every module-level name it reads is itself identical, an import from
                      the shared layers or the standard library, or a builtin: it can be cut
                      out and imported back today
    NEEDS PARAMETERS  it reads a name that differs between the projects, or something
                      imported from the project's own package: it has to be handed those
                      before it can be shared

    python3 arkitect/lib/verify/twins.py                 every file, and a TOTAL of twin lines
    python3 arkitect/lib/verify/twins.py --file roof.py  one file, every name
    python3 arkitect/lib/verify/twins.py --why           with the names that hold each one back

The TOTAL may not grow: arkitect/lib/verify/test_twins.py holds it to the workspace's ceiling
(arkitect.toml [verify] twins_ceiling, 0 when unset) and fails when a definition is
copied from one project into another. It reports; it always exits 0.
"""
import ast, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path: sys.path.insert(0, HERE)
from arkitect.lib import workspace                        # noqa: E402
ROOT = os.path.join(workspace.WORKSPACE, 'projects')
PACKAGE = 'src'


def projects(root=ROOT):
    """The project directories under `root` that hold a package to compare."""
    return sorted(os.path.join(root, d) for d in os.listdir(root)
                  if os.path.isdir(os.path.join(root, d, PACKAGE)))


def _files(package):
    out = {}
    for d, _dirs, fs in os.walk(package):
        for f in fs:
            if f.endswith('.py'):
                out[os.path.relpath(os.path.join(d, f), package)] = os.path.join(d, f)
    return out


def defs(path):
    """({name: (node, text)}, names imported from the project's own package)."""
    src = open(path).read(); tree = ast.parse(src); L = src.split('\n'); d = {}; local = set()
    for n in tree.body:
        text = '\n'.join(L[n.lineno-1:n.end_lineno])
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)): d[n.name] = (n, text)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for nm in ast.walk(t):
                    if isinstance(nm, ast.Name): d[nm.id] = (n, text)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            mod = getattr(n, 'module', None) or n.names[0].name
            if mod.split('.')[0] == PACKAGE:
                local |= {(a.asname or a.name).split('.')[0] for a in n.names}
    return d, local


def _names(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _imports_inside(node):
    """The project's own modules a definition imports in its body, where a name scan cannot see them."""
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.ImportFrom) and (n.module or '').split('.')[0] == PACKAGE:
            out.append(n.module)
        elif isinstance(n, ast.Import):
            out += [a.name for a in n.names if a.name.split('.')[0] == PACKAGE]
    return sorted(set(out))


def twins(a_path, b_path):
    """(movable, needs): {name: lines} and {name: (lines, [what holds it back])}, for the
       same file in two projects."""
    a, la = defs(a_path); b, lb = defs(b_path)
    def counted(k):
        return isinstance(a[k][0], (ast.FunctionDef, ast.ClassDef)) or a[k][1].count('\n') >= 2
    same = {k for k in a if k in b and a[k][1] == b[k][1]}
    pure = set(same); why = {}; moved = True
    while moved:
        moved = False
        for k in sorted(pure):
            used = _names(a[k][0])-{k}
            held = sorted(x for x in used if (x in a or x in b) and x not in pure) \
                 + sorted(used & (la | lb)) + _imports_inside(a[k][0])
            if held: pure.discard(k); why[k] = held; moved = True
    lines = lambda k: a[k][1].count('\n')+1
    return ({k: lines(k) for k in pure if counted(k)},
            {k: (lines(k), why[k]) for k in same-pure if counted(k)})


def survey(root=ROOT):
    """[(file, project a, project b, movable, needs)] for every file two projects share."""
    out = []
    ps = projects(root)
    for i, pa in enumerate(ps):
        for pb in ps[i+1:]:
            fa, fb = _files(os.path.join(pa, PACKAGE)), _files(os.path.join(pb, PACKAGE))
            for rel in sorted(set(fa) & set(fb)):
                m, n = twins(fa[rel], fb[rel])
                if m or n: out.append((rel, os.path.basename(pa), os.path.basename(pb), m, n))
    return out


def total(rows):
    return sum(sum(m.values())+sum(v[0] for v in n.values()) for _f, _a, _b, m, n in rows)


if __name__ == '__main__':
    args = sys.argv[1:]
    why = '--why' in args
    only = args[args.index('--file')+1] if '--file' in args else None
    rows = [r for r in survey() if only is None or r[0] == only]
    for rel, pa, pb, m, n in rows:
        print('%-22s movable %3d defs %4d lines | needs parameters %3d defs %4d lines   (%s, %s)'
              % (rel, len(m), sum(m.values()), len(n), sum(v[0] for v in n.values()), pa, pb))
        if only or why:
            for k in sorted(m, key=lambda k: -m[k]): print('      movable  %4d  %s' % (m[k], k))
            for k in sorted(n, key=lambda k: -n[k][0]):
                print('      needs    %4d  %s   <- %s' % (n[k][0], k, ', '.join(n[k][1])))
    print('TOTAL %d' % total(rows))
