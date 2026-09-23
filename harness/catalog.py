"""What a set is made of: the sheets a residential permit set here binds, in order, with
the shared rules that must RUN in a project's build before each can be called done.
Where another project in the checkout already draws a sheet is looked up, not listed:
`references()` finds every `def sheet_<id>` under projects/*/src/sheets/, so the engine names
no project and a worker still gets pointed at a drawn example of the sheet it is starting.

`features(intake)` expands the catalog for one address -- a floor plan, an elevation, a
mechanical, electrical and water supply sheet per building -- into the feature list
harness/progress.py keeps. It is the starting list, not a contract: the initializer and
the workers edit a project's own progress.json when its set needs another sheet (one project may need
A-103, A-203 and A-604, another none of them).

GUARDS are modules in codes/ and lib/model/fit.py. harness/progress.py runs the build
under a profiler and a feature is DONE only when every guard of its had a function
called during that build -- so "A-101 passes" cannot be claimed of a floor plan whose
egress windows nothing checked. A guard names a module, not a function, so refactoring
inside a rule does not break the list.
"""
import re

# (number or pattern, title, guards). `{i}` is filled per building, from 1.
SHEETS = (
    ('G-001', 'COVER, CODE DATA, GENERAL NOTES', ('codes.columbus.fit',)),
    ('C-101', 'SITE PLAN', ('codes.columbus.fit', 'codes.ohio.opc_separation')),
    ('C-103', 'GRADING AND DRAINAGE PLAN', ('lib.model.grade', 'codes.ohio.rco.site_steps')),
    ('A-001', 'FLOOR PLAN GENERAL NOTES', ('codes.ohio.rco.egress',)),
    ('A-10{i}', '{b} — FLOOR PLANS', ('codes.ohio.rco.egress', 'codes.clearances', 'lib.model.fit')),
    ('A-20{i}', '{b} — EXTERIOR ELEVATIONS', ('codes.ohio.rco.fire_separation',)),
    ('A-301', 'BUILDING SECTIONS AND HEIGHT SCHEDULE', ('lib.model.stairs',)),
    ('A-601', 'ASSEMBLIES AND FIRE SEPARATION SCHEDULE', ('codes.ohio.rco.fire_separation',)),
    ('A-602', 'WINDOW, DOOR AND FINISH SCHEDULES', ('codes.ohio.rco.egress',)),
    ('S-101', 'FOUNDATION PLANS', ('codes.ohio.rco.concrete', 'codes.ohio.opc_service_entry')),
    ('S-102', 'FLOOR FRAMING PLANS', ('codes.ohio.rco.headers', 'codes.ohio.rco.floor_checks',
                                     'lib.model.fit')),
    ('S-103', 'ROOF FRAMING PLANS AND DETAILS', ('codes.ohio.rco.roof_checks',
                                                'codes.ohio.rco.attic_ventilation')),
    ('S-104', 'WALL BRACING PLANS AND DETAILS', ('codes.ohio.rco.bracing',)),
    ('M-10{i}', '{b} — MECHANICAL PLANS', ('codes.ohio.rco.mechanical',)),
    ('E-10{i}', '{b} — ELECTRICAL PLANS', ('codes.nec.dwelling', 'codes.nec.load')),
    ('P-101', 'SANITARY / UNDER-SLAB PLANS', ('codes.ohio.opc_drainage', 'lib.model.drains')),
    ('P-10{j}', '{b} — WATER SUPPLY PLANS', ('codes.ohio.water_supply',)),
    ('P-601', 'PLUMBING RISER DIAGRAM AND NOTES', ('codes.ohio.opc_vents',)),
    ('C-102', 'ZONING SITE PLAN — 11 x 17, ISSUED SEPARATELY', ('codes.columbus.fit',)),
)

# Drawn by a scaffold on its first day, from the massing (codes/columbus/zoning_sheets.py).
DAY_ONE = ('G-001', 'C-102')


def features(intake):
    """The feature list for one address, in binding order: one dict per sheet."""
    names = [b['name'] for b in intake['buildings']]
    out = []
    for no, title, guards in SHEETS:
        if '{i}' in no or '{j}' in no:
            for i, b in enumerate(names, 1):
                n = no.replace('{i}', str(i)).replace('{j}', str(i+1))
                out.append(_feature(n, title.replace('{b}', b), guards))
        else:
            out.append(_feature(no, title, guards))
    return out


def _feature(no, title, guards):
    return {'id': no, 'title': title, 'status': 'drawn' if no in DAY_ONE else 'pending',
            'guards': list(guards), 'notes': ''}


def references(sheet_id, root=None, exclude=None):
    """Every module under projects/*/src/sheets/ that defines this sheet's function
       (`sheet_a101` for A-101), except in project `exclude`: a drawn example to read. The
       workspace's projects come first, relative to it; with the projects outside the engine,
       the engine's own examples follow, by absolute path."""
    import os
    from lib import workspace
    fn = re.compile(r'^def sheet_%s\(' % re.escape(sheet_id.replace('-', '').lower()), re.M)
    roots = [root] if root else [workspace.WORKSPACE] + (
        [workspace.ENGINE] if workspace.separate() else [])
    out = []
    for i, r in enumerate(roots):
        base = os.path.join(r, 'projects')
        for slug in sorted(os.listdir(base)) if os.path.isdir(base) else ():
            d = os.path.join(base, slug, 'src', 'sheets')
            if slug == exclude or not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                if f.endswith('.py'):
                    with open(os.path.join(d, f)) as fh:
                        if fn.search(fh.read()):
                            rel = os.path.join('projects', slug, 'src', 'sheets', f)
                            out.append(rel if i == 0 else os.path.join(r, rel))
    return out
