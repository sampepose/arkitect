"""The evaluator, apart from the generator: a reviewer that sees only the rendered sheets and
the house style, and whose findings come back as tasks the build must answer.

    arkitect review prepare <slug> [--sheets A-101,P-601 | --moved] [--out DIR] [--known]
    arkitect review ingest  <slug> <findings.json>
    arkitect review list    <slug> [--status open]
    arkitect review next    <slug>
    arkitect review set     <slug> R-007 fixed|wontfix|rejected|waiting|open [--note "..."]
    arkitect review known   <slug> [--all] [--out FILE]     what earlier reviews raised and was settled
    arkitect review parse   <reply-or-transcript> [--out FILE]   the findings JSON in an agent's reply

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

WAITING IS NOT WONTFIX. A finding that turns on a call only the designer (or a third party)
can make is `waiting`, and its note names what it waits on -- a decision's id, most often.
`wontfix` is a finding judged and declined. The two used to share `wontfix`, so nothing could
tell a settled finding from one that should come back when its question is answered;
arkitect/harness/autoreview.py reopens a waiting finding once every decision its note names is
settled.

THE KNOWN LIST. A reviewer that has never seen the set raises the same settled items every
round. `known` writes what earlier rounds raised and the designer settled -- every `wontfix`
and `waiting` finding, with the title of each decision its note names in place of the id,
and the decisions still waiting on someone else -- so a brief can tell the reviewer what not
to spend its time on. It carries no id: a reviewer would only report it as internal
vocabulary.
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
STATUSES = ('open', 'fixed', 'wontfix', 'rejected', 'waiting')
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

You are reviewing a residential building permit set for {address}{place}, as {reviewer} would
-- and as the contractor who has to build from it would. You see
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


def prepare(slug, sheets=None, moved=False, out=None, root=ROOT, known_list=None, base='HEAD'):
    """Render the sheets for review and write the brief. Returns the review directory; its
       index.json lists every image and the fingerprint of each sheet as rendered. With
       `known_list` (known()'s text) the brief tells the reviewer what is already settled;
       `moved` names the sheets that differ from `base`."""
    import pymupdf
    from arkitect.lib.verify import gate
    out = gate._out_dir(out)
    scratch = tempfile.mkdtemp(prefix='review-')
    try:
        pages, prints = _measure(slug, scratch, root)
        if moved:
            _sha, bases = gate.baseline(base, [slug])
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
            fh.write(brief(slug, index, root, known_list))
        return out
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def jurisdiction_of(slug, root=ROOT):
    """The jurisdiction a project is in: its intake's `"jurisdiction"`, else its
       src/project.py's JURISDICTION = "...", else None."""
    p = os.path.join(root, 'projects', slug, 'intake.json')
    if os.path.exists(p):
        with open(p) as fh:
            name = json.load(fh).get('jurisdiction')
        if name:
            return name
    p = os.path.join(root, 'projects', slug, 'src', 'project.py')
    if os.path.exists(p):
        with open(p) as fh:
            m = re.search(r'^JURISDICTION = ["\']([a-z_]+/[a-z_]+)["\']', fh.read(), re.M)
        return m.group(1) if m else None
    return None


def brief(slug, index, root=ROOT, known_list=None):
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
    name = jurisdiction_of(slug, root)
    if name:
        from arkitect.codes import jurisdiction
        jur = jurisdiction.load(name)
        place, reviewer = ', ' + jur.NAME, 'the ' + jur.REVIEWER
    else:
        place, reviewer = '', "the jurisdiction's residential plan reviewer"
    lines = []
    for no, s in index['sheets'].items():
        lines.append('- **%s**: whole `%s`; tiles %s' % (
            no, s['whole'], ', '.join('`%s`' % t for t in s['tiles'])))
    text = BRIEF.format(address=address, place=place, reviewer=reviewer,
                        sheets='\n'.join(lines), cols=TILE_GRID[0],
                        rows=TILE_GRID[1], tile_dpi=TILE_DPI, style=house_style(root),
                        categories=' | '.join('"%s"' % c for c in CATEGORIES))
    if known_list:
        text = text.replace('## House style', known_list.rstrip('\n') + '\n\n## House style', 1)
    return text


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
    if status == 'waiting' and not note:
        raise ValueError('waiting needs --note naming what it waits on (a decision id, or who)')
    rec['status'] = status
    if note:
        rec['notes'] = note
    save(slug, data, root)
    return rec


# ---------------------------------------------------------------- the known list

KNOWN = """## Already raised and settled -- do not report these again

Earlier reviews raised each item below, and the designer settled it on purpose or it waits
on someone outside the set. Do not report one again unless a sheet now CONTRADICTS what the
item says (a different figure, a note it says is printed and is not). Spend your time on what
nobody has found yet: fit, constructability, figures that disagree between sheets, code
sections misapplied, and anything a builder could not build from the sheets as drawn.

"""

_DID = re.compile(r'\bD-\d{3}\b')
_RID = re.compile(r'\bR-\d{3,}\b')


def _clip(text, n):
    text = re.sub(r'\s+', ' ', text).strip()
    return text if len(text) <= n else text[:n-3].rstrip() + '...'


def known(slug, root=ROOT, severities=('blocker', 'major')):
    """The known list, as Markdown. A wontfix or waiting finding of `severities` whose note
       names decisions is folded into ONE line per set of decisions -- their titles and what
       they chose, and the sheets it was raised on -- because a settled question is raised
       again in new words every round; a finding whose note names none is listed with its
       note, once however often it recurred. Then the decisions about the project still
       waiting on someone. No id of any kind is printed."""
    from arkitect.harness import decisions
    recs = {f['id']: f for f, _b in decisions.all_decisions(root)}
    order = {s: i for i, s in enumerate(SEVERITIES)}
    rows = sorted((r for r in load(slug, root)['findings']
                   if r['status'] in ('wontfix', 'waiting') and r['severity'] in severities),
                  key=lambda r: (order[r['severity']], r['sheet'], r['id']))
    by_decision, loose = {}, []
    for r in rows:
        ids = tuple(sorted(set(d for d in _DID.findall(r.get('notes') or '') if d in recs)))
        if ids:
            by_decision.setdefault(ids, []).append(r)
        else:
            loose.append(r)
    lines = []
    for ids, rs in by_decision.items():
        sheets = sorted(set(r['sheet'] for r in rs))
        what = ' '.join(recs[d].get('decision') or recs[d]['title'] for d in ids)
        head = '; '.join(recs[d]['title'] for d in ids)
        lines.append('- **%s** (%s, on %s): %s' % (
            _clip(head, 200), 'waits' if all(r['status'] == 'waiting' for r in rs) else 'settled',
            ', '.join(sheets), _clip(_scrub(what), 320)))
    seen = []
    for r in loose:
        key = _norm(r.get('notes') or r['finding'])
        if any(difflib.SequenceMatcher(None, key, k).ratio() > 0.6 for k in seen):
            continue
        seen.append(key)
        why = _scrub(r.get('notes') or '')
        lines.append('- **%s** (%s): %s%s' % (
            r['sheet'], 'waits' if r['status'] == 'waiting' else 'settled',
            _clip(r['finding'], 240), (' -- ' + _clip(why, 200)) if why else ''))
    for f in recs.values():
        if f['status'] == 'waiting' and (slug in f.get('projects', []) or 'all' in f.get('projects', [])):
            lines.append('- **Waits on %s**: %s' % (f.get('waiting_on') or 'a third party',
                                                    _clip(_scrub(f['title']), 220)))
    return KNOWN + ('\n'.join(lines) if lines else '(nothing yet)') + '\n'


def _scrub(text):
    """`text` with every decision and finding id taken out."""
    text = _RID.sub('', _DID.sub('', text or ''))
    text = re.sub(r'\(\s*[/,;]*\s*\)', '', text)
    return re.sub(r'\s+([,.;:])', r'\1', text).strip(' -;,:')


# ---------------------------------------------------------------- an agent's reply

def _reply_text(text):
    """The text that holds the findings: `text` itself, or -- for a Claude Code transcript
       (.jsonl) -- the last assistant message, or tool input, that carries a JSON array."""
    lines = text.splitlines()
    try:
        recs = [json.loads(l) for l in lines if l.strip()]
    except json.JSONDecodeError:
        return text
    if not recs or not all(isinstance(r, dict) for r in recs):
        return text
    for r in reversed(recs):
        m = r.get('message') or {}
        if m.get('role') != 'assistant' or not isinstance(m.get('content'), list):
            continue
        for c in m['content']:
            if c.get('type') == 'text' and '[' in c.get('text', ''):
                return c['text']
            if c.get('type') == 'tool_use':
                for v in (c.get('input') or {}).values():
                    if isinstance(v, str) and '"sheet"' in v and '[' in v:
                        return v
    raise ValueError('no assistant message in the transcript carries a JSON array')


def parse(text):
    """The findings array in an agent's reply, a file of JSON, or a transcript. A reply's last
       ```json fence wins; else the first `[` to the last `]`. An unescaped double quote inside
       a string -- the one mistake reviewers make in quoting a sheet's 3'-0" -- is escaped
       where the decoder stops on it."""
    body = _reply_text(text)
    fences = re.findall(r'```(?:json)?\s*\n(.*?)```', body, re.S)
    body = next((f for f in reversed(fences) if f.strip().startswith('[')), body)
    if '[' not in body or ']' not in body:
        raise ValueError('no JSON array in the reply')
    a = body[body.index('['):body.rindex(']')+1]
    for _ in range(500):
        try:
            out = json.loads(a)
            break
        except json.JSONDecodeError as exc:
            q = a.rfind('"', 0, exc.pos)
            if q <= 0 or a[q-1] == '\\':
                raise ValueError('the array does not parse: %s' % exc)
            a = a[:q] + '\\"' + a[q+1:]
    else:
        raise ValueError('the array does not parse after 500 repairs')
    if not isinstance(out, list) or not all(isinstance(f, dict) for f in out):
        raise ValueError('the reply is JSON but not an array of findings')
    return out


def _line(r):
    return '%s  %-8s %-7s %-6s %-18s %s' % (r['id'], r['status'], r['severity'], r['sheet'],
                                            r['category'], r['finding'][:110])


def main(argv):
    if len(argv) < 2 or argv[0] not in ('prepare', 'ingest', 'list', 'next', 'set', 'known', 'parse'):
        print(__doc__)
        return 1
    cmd, slug = argv[0], argv[1]
    opt = lambda f: next((argv[i+1] for i, a in enumerate(argv[:-1]) if a == f), None)
    if cmd in ('list', 'next') and '--json' in argv:
        from arkitect.lib import interface
        order = {s: i for i, s in enumerate(SEVERITIES)}
        rows = load(slug)['findings']
        if cmd == 'next':
            rows = sorted((r for r in rows if r['status'] == 'open'),
                          key=lambda r: (order[r['severity']], r['id']))[:1]
        elif opt('--status'):
            rows = [r for r in rows if r['status'] == opt('--status')]
        interface.emit('review', {'project': slug, 'findings': rows})
        return 0
    try:
        if cmd == 'parse':
            with open(slug) as fh:                 # `parse` takes a file, not a slug
                found = parse(fh.read())
            text = json.dumps(found, indent=1)
            if opt('--out'):
                with open(opt('--out'), 'w') as fh:
                    fh.write(text + '\n')
                print('%d findings -> %s' % (len(found), opt('--out')))
            else:
                print(text)
        elif cmd == 'known':
            text = known(slug, severities=SEVERITIES if '--all' in argv else ('blocker', 'major'))
            if opt('--out'):
                with open(opt('--out'), 'w') as fh:
                    fh.write(text)
                print('known list -> %s' % opt('--out'))
            else:
                print(text, end='')
        elif cmd == 'prepare':
            sh = opt('--sheets')
            out = prepare(slug, sh.split(',') if sh else None, '--moved' in argv, opt('--out'),
                          known_list=known(slug) if '--known' in argv else None)
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
                  '  arkitect review set %s %s fixed' % (slug, r['id']))
        else:
            r = set_status(slug, argv[2], argv[3], opt('--note'))
            print('%s is %s' % (r['id'], r['status']))
    except (ValueError, RuntimeError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
