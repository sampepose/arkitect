"""The evaluator, apart from the generator: a reviewer that sees only the rendered sheets and
the house style, and whose findings come back as tasks the build must answer.

    python3 -m arkitect.harness.review prepare <slug> [--sheets A-101,P-601 | --moved] [--out DIR]
    python3 -m arkitect.harness.review ingest  <slug> <findings.json>
    python3 -m arkitect.harness.review list    <slug> [--status open]
    python3 -m arkitect.harness.review next    <slug>
    python3 -m arkitect.harness.review set     <slug> R-007 fixed|wontfix|rejected|open [--note "..."]

WHY APART. Every oracle this repository has measures a RULE: the trace, the model checks,
sheet_text, the fit checks. One project's worst faults -- headers deeper than the wall over their
windows, heat-pump heads hung across windows, a stack through two windows, one string printed
on another -- were green on all of them and were found by LOOKING. A reviewer that reads the
code learns what the drawing was meant to show and sees that; one that reads only the sheet
sees what it shows. So the reviewer (.claude/agents/plan-reviewer.md) has Read and Glob and
nothing else, and `prepare` hands it images and a brief -- never a path into the source.

ADVERSARIAL, THEN VERIFIED. The reviewer is told to find faults, which makes it
over-report; a second agent (.claude/agents/finding-verifier.md) re-reads each finding
against the images and rejects what it cannot see. Rejected findings are kept, so the next
review does not report them again.

A FINDING IS A TASK, and closing it is proved: `ingest` records the sheet's trace
fingerprint (arkitect/lib/verify/trace.py --by-sheet) when the finding is made, and `set ... fixed`
refuses unless that sheet has changed since. `wontfix` and `rejected` need a note. The
findings file, projects/<slug>/review.json, is written by this module alone; the hooks
refuse any other write, as they do progress.json.
"""
import datetime
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from arkitect.lib import workspace

ROOT = workspace.WORKSPACE             # the projects and their review.json live here
CATEGORIES = ('fit', 'legibility', 'consistency', 'missing', 'code', 'spelling',
              'one-home', 'arguing', 'revision-history', 'internal-vocabulary', 'other')
SEVERITIES = ('blocker', 'major', 'minor')
VERDICTS = ('CONFIRMED', 'PLAUSIBLE', 'REJECTED')
STATUSES = ('open', 'fixed', 'wontfix', 'rejected')
FIELDS = ('sheet', 'where', 'category', 'severity', 'finding', 'evidence', 'suggest')

# Whole sheet at a size to see its layout; tiles at a size to read 5 pt type.
WHOLE_DPI, TILE_DPI = 72, 200
TILE_GRID = (3, 2)          # columns, rows across an ARCH C sheet (about 8 x 9 in each)
TILE_OVERLAP = 0.6          # inches each tile runs into its neighbour, so no string is cut


# ---------------------------------------------------------------- the brief

STYLE = os.path.join('style', 'house-style.md')     # the default; arkitect/harness/config.py [style] house


def house_style(root=ROOT):
    """The house style arkitect/harness/config.py names (style/house-style.md by default), read live:
       the reviewer is held to the rules as they stand, never to a copy. Its own title and
       preface are left off the brief."""
    from arkitect.harness import config
    rel = config.get('style.house', root=root) or STYLE
    # the workspace's own style if it keeps one, else the engine's
    p = next((p for p in (os.path.join(root, rel), os.path.join(workspace.ENGINE, rel))
              if os.path.exists(p)), os.path.join(root, rel))
    with open(p) as fh:
        text = fh.read()
    body = re.split(r'\n\n', text, maxsplit=2)
    return body[2].strip() if len(body) == 3 else text.strip()


BRIEF = """# Plan review: {address}

You are reviewing a residential building permit set for {address}, Columbus, Ohio, as the
city's plan reviewer would -- and as the contractor who has to build from it would. You see
only the sheets. Find what is WRONG with them. You are not here to praise; a review with no
findings on sheets this dense is a review that did not look.

## What you have

{sheets}

Each sheet has a WHOLE image (its layout) and TILES (a {cols} x {rows} grid, overlapping, at
{tile_dpi} dpi: read the text on the tiles, never on the whole image). Read every tile of every
sheet you are given. Where two sheets show the same thing, compare them.

## Look for

- **fit** -- things drawn on top of each other that cannot both be built: equipment across a
  window, a header or duct through an opening, a stack through a window, a door swing into a
  fixture, a label on a line so neither can be read.
- **legibility** -- text on text, text on linework, text too small or too crowded to read,
  a dimension whose number cannot be matched to its line.
- **consistency** -- the same thing named, numbered or dimensioned differently on two sheets
  or two places on one; a dimension string that does not add up; a schedule that disagrees
  with the plan; a note that cites a sheet, note or detail that is not there.
- **missing** -- something a reviewer or a builder would need and cannot find: an undimensioned
  element, an untagged opening, a detail cited nowhere, a north arrow, a scale.
- **code** -- something the sheet shows that looks non-compliant on its face (a stair, an
  egress window, a clearance). Say what you see and which rule you think it breaks; you
  cannot see the calculations behind it, so say so.
- The house style below: **spelling** (American, not British), **one-home** (a rule restated
  on a second sheet instead of cited), **arguing** (a note that argues or defends instead of
  instructing), **revision-history** (a note about what changed), **internal-vocabulary**
  (words that mean something only to the people who drew it, including ids like D-912).

## Do not report

- What you cannot see. Every finding names the tile and quotes what is printed.
- The conventions the house style records as deliberate (a greyed background plan under an
  overlay, dimensions to the face of stud).
- Taste. "Could be clearer" is not a finding; "the 4'-0\\" string overlaps the W-A tag and the
  4 reads as 1" is.

## House style (the rules this set is held to)

{style}

## Output

Reply with ONE JSON array and nothing else. Each element:

{{"sheet": "A-101", "where": "tile r1c2 -- the Level 1 kitchen, above the range",
  "category": one of {categories},
  "severity": "blocker" (cannot be built or will be rejected) | "major" (a reviewer will
    return it) | "minor" (worth fixing),
  "finding": "what is wrong, in one or two sentences",
  "evidence": "exactly what is printed or drawn -- quote the text",
  "suggest": "what would fix it"}}
"""


def _tiles(page, grid=TILE_GRID, overlap=TILE_OVERLAP):
    """(label, pymupdf.Rect) for each tile of a page, overlapping by `overlap` inches."""
    import pymupdf
    w, h = page.rect.width, page.rect.height
    cols, rows = grid
    ov = overlap*72
    out = []
    for r in range(rows):
        for c in range(cols):
            x0 = max(0, c*w/cols-ov)
            x1 = min(w, (c+1)*w/cols+ov)
            y0 = max(0, r*h/rows-ov)
            y1 = min(h, (r+1)*h/rows+ov)
            out.append(('r%dc%d' % (r+1, c+1), pymupdf.Rect(x0, y0, x1, y1)))
    return out


def _measure(slug, scratch, root=ROOT):
    """Trace the project once, keeping its PDFs and its per-sheet fingerprints."""
    from arkitect.lib.verify import gate
    res = gate.measure(root, slug, scratch, dxf=False, text=False, engine=workspace.ENGINE)
    if not res['trace']['ok']:
        raise RuntimeError('%s does not build:\n%s' % (slug, res['trace'].get('stderr', '')))
    return gate._bound(scratch), gate.by_sheet(os.path.join(scratch, 'sheets.txt'))


def fingerprints(slug, root=ROOT):
    """{sheet: md5} of the build as it stands."""
    scratch = tempfile.mkdtemp(prefix='review-fp-')
    try:
        return {k: v[1] for k, v in _measure(slug, scratch, root)[1].items()}
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def prepare(slug, sheets=None, moved=False, out=None, root=ROOT):
    """Render the sheets for review and write the brief. Returns the review directory; its
       index.json lists every image and the fingerprint of each sheet as rendered."""
    import pymupdf
    from arkitect.lib.verify import gate
    out = gate._out_dir(out)
    scratch = tempfile.mkdtemp(prefix='review-')
    try:
        pages, prints = _measure(slug, scratch, root)
        if moved:
            _sha, bases = gate.baseline('HEAD', [slug])
            names = [m['sheet'] for m in gate.moved(gate._base_sheets(bases[slug]), prints)
                     if m['sheet'] in pages]
        else:
            names = [n for n in pages if not sheets or n in sheets]
        if sheets and set(sheets) - set(pages):
            raise ValueError('no such sheet: %s' % ', '.join(sorted(set(sheets)-set(pages))))
        index = {'project': slug, 'commit': _head(root), 'sheets': {}}
        for no in names:
            pdf, i = pages[no]
            d = os.path.join(out, no)
            os.makedirs(d, exist_ok=True)
            with pymupdf.open(pdf) as doc:
                page = doc[i]
                whole = os.path.join(d, 'whole.png')
                page.get_pixmap(dpi=WHOLE_DPI).save(whole)
                tiles = []
                for label, rect in _tiles(page):
                    p = os.path.join(d, 'tile-%s.png' % label)
                    page.get_pixmap(dpi=TILE_DPI, clip=rect).save(p)
                    tiles.append(p)
            index['sheets'][no] = {'whole': whole, 'tiles': tiles, 'md5': prints[no][1]}
        with open(os.path.join(out, 'index.json'), 'w') as fh:
            json.dump(index, fh, indent=1)
        with open(os.path.join(out, 'brief.md'), 'w') as fh:
            fh.write(brief(slug, index, root))
        return out
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def brief(slug, index, root=ROOT):
    address = slug
    for rel in ('intake.json',):
        p = os.path.join(root, 'projects', slug, rel)
        if os.path.exists(p):
            with open(p) as fh:
                address = json.load(fh).get('address', slug)
    if address == slug:
        p = os.path.join(root, 'projects', slug, 'src', 'project.py')
        if os.path.exists(p):
            with open(p) as fh:
                m = re.search(r'^ADDRESS = "([^"]+)"', fh.read(), re.M)
            address = m.group(1).title() if m else slug
    lines = []
    for no, s in index['sheets'].items():
        lines.append('- **%s**: whole `%s`; tiles %s' % (
            no, s['whole'], ', '.join('`%s`' % t for t in s['tiles'])))
    return BRIEF.format(address=address, sheets='\n'.join(lines), cols=TILE_GRID[0],
                        rows=TILE_GRID[1], tile_dpi=TILE_DPI, style=house_style(root),
                        categories=' | '.join('"%s"' % c for c in CATEGORIES))


def _head(root):
    r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=root, capture_output=True, text=True)
    return r.stdout.strip()


# ---------------------------------------------------------------- the findings file

def path_for(slug, root=ROOT):
    return os.path.join(root, 'projects', slug, 'review.json')


def load(slug, root=ROOT):
    p = path_for(slug, root)
    if not os.path.exists(p):
        return {'project': slug, 'findings': []}
    with open(p) as fh:
        return json.load(fh)


def save(slug, data, root=ROOT):
    p = path_for(slug, root)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix='.partial')
    with os.fdopen(fd, 'w') as fh:
        json.dump(data, fh, indent=1)
        fh.write('\n')
    os.replace(tmp, p)


def problems(f):
    """Every way one incoming finding is malformed."""
    bad = []
    tag = '%s/%s' % (f.get('sheet', '?'), (f.get('finding') or '?')[:40])
    for k in FIELDS:
        if not isinstance(f.get(k), str) or not f[k].strip():
            bad.append('%s: %s is missing' % (tag, k))
    if f.get('category') not in CATEGORIES:
        bad.append('%s: category %r is not one of %s' % (tag, f.get('category'), ', '.join(CATEGORIES)))
    if f.get('severity') not in SEVERITIES:
        bad.append('%s: severity %r is not one of %s' % (tag, f.get('severity'), ', '.join(SEVERITIES)))
    if f.get('verdict') not in VERDICTS:
        bad.append('%s: verdict %r is not one of %s (run the verifier first)'
                   % (tag, f.get('verdict'), ', '.join(VERDICTS)))
    return bad


def _norm(t):
    return re.sub(r'\s+', ' ', t.lower()).strip()


def duplicate_of(f, existing):
    """An existing finding on the same sheet saying the same thing, or None."""
    for e in existing:
        if e['sheet'] == f['sheet'] and difflib.SequenceMatcher(
                None, _norm(e['finding']), _norm(f['finding'])).ratio() > 0.8:
            return e
    return None


def ingest(slug, findings, index=None, root=ROOT):
    """Add verified findings. A REJECTED one is kept as rejected, so it is not reported
       again. Returns (added, duplicates). Refuses the whole batch if any is malformed."""
    bad = [p for f in findings for p in problems(f)]
    if bad:
        raise ValueError('\n'.join(bad))
    data = load(slug, root)
    prints = (index or {}).get('sheets') or {}
    now = fingerprints(slug, root) if not prints else {k: v['md5'] for k, v in prints.items()}
    n = max([int(e['id'][2:]) for e in data['findings']] or [0])
    added, dups = [], []
    for f in findings:
        d = duplicate_of(f, data['findings'])
        if d:
            dups.append((f, d['id']))
            continue
        if f['sheet'] not in now:
            raise ValueError('%s is not a sheet this build binds' % f['sheet'])
        n += 1
        rec = {k: f[k] for k in FIELDS}
        rec.update(id='R-%03d' % n, verdict=f['verdict'], verdict_reason=f.get('verdict_reason', ''),
                   status='rejected' if f['verdict'] == 'REJECTED' else 'open',
                   sheet_md5=now[f['sheet']], found=datetime.date.today().isoformat(),
                   commit=(index or {}).get('commit') or _head(root), notes='')
        data['findings'].append(rec)
        added.append(rec)
    save(slug, data, root)
    return added, dups


def set_status(slug, rid, status, note=None, root=ROOT):
    """Close or reopen a finding. `fixed` is refused unless its sheet has changed since the
       finding was made; `wontfix` and `rejected` need a note saying why."""
    if status not in STATUSES:
        raise ValueError('status must be one of %s' % ', '.join(STATUSES))
    data = load(slug, root)
    rec = next((r for r in data['findings'] if r['id'] == rid), None)
    if rec is None:
        raise ValueError('%s has no finding %s' % (slug, rid))
    if status == 'fixed':
        now = fingerprints(slug, root).get(rec['sheet'])
        if now == rec['sheet_md5']:
            raise ValueError('refused: %s has not changed since %s was found -- nothing on it can '
                             'have been fixed' % (rec['sheet'], rid))
    if status in ('wontfix', 'rejected') and not note:
        raise ValueError('%s needs --note saying why' % status)
    rec['status'] = status
    if note:
        rec['notes'] = note
    save(slug, data, root)
    return rec


def _line(r):
    return '%s  %-8s %-7s %-6s %-18s %s' % (r['id'], r['status'], r['severity'], r['sheet'],
                                            r['category'], r['finding'][:110])


def main(argv):
    if len(argv) < 2 or argv[0] not in ('prepare', 'ingest', 'list', 'next', 'set'):
        print(__doc__)
        return 1
    cmd, slug = argv[0], argv[1]
    opt = lambda f: next((argv[i+1] for i, a in enumerate(argv[:-1]) if a == f), None)
    try:
        if cmd == 'prepare':
            sh = opt('--sheets')
            out = prepare(slug, sh.split(',') if sh else None, '--moved' in argv, opt('--out'))
            print('review ready: %s\nthe brief: %s' % (out, os.path.join(out, 'brief.md')))
        elif cmd == 'ingest':
            with open(argv[2]) as fh:
                findings = json.load(fh)
            idx = opt('--index')
            index = json.load(open(idx)) if idx else None
            added, dups = ingest(slug, findings, index)
            for r in added:
                print('added ' + _line(r))
            for f, rid in dups:
                print('duplicate of %s: %s %s' % (rid, f['sheet'], f['finding'][:90]))
        elif cmd == 'list':
            st = opt('--status')
            for r in load(slug)['findings']:
                if not st or r['status'] == st:
                    print(_line(r))
        elif cmd == 'next':
            order = {s: i for i, s in enumerate(SEVERITIES)}
            opn = sorted((r for r in load(slug)['findings'] if r['status'] == 'open'),
                         key=lambda r: (order[r['severity']], r['id']))
            if not opn:
                print('no open finding')
                return 0
            r = opn[0]
            print('NEXT: %s (%s, %s) on %s -- %s' % (r['id'], r['severity'], r['category'],
                                                    r['sheet'], r['where']))
            print('  finding:  ' + r['finding'])
            print('  evidence: ' + r['evidence'])
            print('  suggest:  ' + r['suggest'])
            print('Fix it, run the gate, render the sheet and look, then:\n'
                  '  python3 -m arkitect.harness.review set %s %s fixed' % (slug, r['id']))
        else:
            r = set_status(slug, argv[2], argv[3], opt('--note'))
            print('%s is %s' % (r['id'], r['status']))
    except (ValueError, RuntimeError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
