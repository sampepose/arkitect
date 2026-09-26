"""Review, fix, repeat -- until a stop rule says the set is done. autoresearch's loop (an
agent edits, a fixed evaluator scores, a better score is kept and a worse one reset, every
attempt logged, a human steering only through a program file) run on a permit set.

    arkitect autoreview init   <slug>                   the program, projects/<slug>/autoreview.md
    arkitect autoreview begin  <slug>                   the integration branch and its worktree
    arkitect autoreview round  <slug> [--force]         freeze round n: render, brief, known list, groups
    arkitect autoreview ingest <slug>                   the round's verified findings -> review.json, rounds.tsv
    arkitect autoreview next   <slug> [--group G] [--claim]   the next attempt and its worker brief
    arkitect autoreview close  <slug> <attempt>         in the attempt's worktree: gate and render what moved
    arkitect autoreview judge  <slug> <attempt> <verdicts.json>   KEEP or DISCARD, and why
    arkitect autoreview record <slug> <attempt> [--waiting R-nnn,... --note D-nnn]   after the merge
    arkitect autoreview status <slug> [--json]          where the loop is; the stop rules
    arkitect autoreview stop   <slug> [--reason "..."]
    arkitect autoreview chart  <slug> [--out FILE]      the rounds as a page
    arkitect autoreview land   <slug> [--no-push]       in the main checkout: ff main, rebuild, push

docs/autoreview.md is the reference; .claude/skills/autoreview/SKILL.md is the lead's
procedure. What this module owns is the state, so a lead can be one session per round:

    projects/<slug>/autoreview.md             the program the designer edits (committed)
    projects/<slug>/autoreview/rounds.tsv     one row a round (committed; the chart's data)
    projects/<slug>/autoreview/attempts.tsv   one row a finding an attempt took (committed)
    ~/.cache/arkitect/autoreview/<repo>/<slug>/   run.json, claims.json, round-NN/ (renders,
                                              briefs, raw and verified findings): outside every
                                              checkout, shared by every worktree of the repository

TWO NUMBERS, TWO JOBS. A plan review is a stochastic instrument: one set, fixed after every
round, drew 2 to 9 confirmed majors a round for eleven rounds. That cannot judge one fix. So
an ATTEMPT is judged locally -- the gate, nothing a builder needs lost, and a fresh verifier
that sees the finding and the re-rendered sheet and says RESOLVED (`judge`) -- and a ROUND's
count decides only when to stop (`stop_rules`).
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time

from arkitect.harness import review
from arkitect.lib import workspace

ROOT = workspace.WORKSPACE

KEYS = {'reviewer': 'opus', 'verifier': 'opus', 'fixer': 'opus', 'rounds': '6', 'hours': '0',
        'attempt_minutes': '25', 'parallel_attempts': '6', 'batch': '8',
        'severities': 'blocker, major, minor', 'known_list': 'on', 'engine': 'queue'}
CHOICES = {'known_list': ('on', 'off'), 'engine': ('queue', 'allow')}
ROUND_COLS = ('round', 'date', 'commit', 'reviewer', 'sheets', 'new_blocker', 'new_major',
              'new_minor', 'rejected', 'duplicates', 'majors')
ATTEMPT_COLS = ('round', 'attempt', 'finding', 'severity', 'sheet', 'outcome', 'branch',
                'minutes', 'fixer', 'date', 'note')
OUTCOMES = ('kept', 'discarded', 'waiting')
CLOSE_VERDICTS = ('RESOLVED', 'NOT RESOLVED', 'RESOLVED BY REMOVAL')
MAX_ATTEMPTS = 2          # discards before a finding waits on the lead
GROUP_MAX = 6             # sheets a reviewer reads together (the review-sheets skill)
DISCIPLINES = (('G', 'general'), ('A', 'architectural'), ('C', 'site'), ('L', 'site'),
               ('S', 'structural'), ('P', 'plumbing'), ('M', 'mechanical-electrical'),
               ('E', 'mechanical-electrical'))


# ---------------------------------------------------------------- places

def _git(*args, cwd=None, check=True):
    r = subprocess.run(['git'] + list(args), cwd=cwd or ROOT, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError('git %s: %s' % (' '.join(args), (r.stderr or r.stdout).strip()))
    return r.stdout.strip()


def common_dir(root=ROOT):
    """The repository's shared .git directory, the same from every worktree; the workspace
       itself outside git."""
    r = subprocess.run(['git', 'rev-parse', '--git-common-dir'], cwd=root, capture_output=True,
                       text=True)
    if r.returncode:
        return os.path.realpath(root)
    return os.path.realpath(os.path.join(root, r.stdout.strip()))


def main_checkout(root=ROOT):
    d = common_dir(root)
    return os.path.dirname(d) if os.path.basename(d) == '.git' else d


def state_dir(slug, root=ROOT, home=None):
    """~/.cache/arkitect/autoreview/<repo>-<hash>/<slug>: outside every checkout, one per
       repository, so the lead in a worktree and the designer in the main checkout see one
       loop."""
    base = os.path.join(home, '.cache') if home else (
        os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~'), '.cache'))
    repo = common_dir(root)
    tag = hashlib.sha1(repo.encode()).hexdigest()[:10]
    name = os.path.basename(main_checkout(root))
    d = os.path.join(base, 'arkitect', 'autoreview', '%s-%s' % (name, tag), slug)
    os.makedirs(d, exist_ok=True)
    return d


def program_path(slug, root=ROOT):
    return os.path.join(root, 'projects', slug, 'autoreview.md')


def log_dir(slug, root=ROOT):
    return os.path.join(root, 'projects', slug, 'autoreview')


def _now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as fh:
        return json.load(fh)


def _write_json(path, data):
    tmp = path + '.partial'
    with open(tmp, 'w') as fh:
        json.dump(data, fh, indent=1)
        fh.write('\n')
    os.replace(tmp, path)


# ---------------------------------------------------------------- the program

TEMPLATE = """---
{keys}
{groups}
---

# autoreview: {slug}

This file is the program. The loop reads it again at the start of every round, so an edit
here steers the next round. Write STOP on a line of its own to end the run.

The keys above: the models the lead gives its reviewers, verifiers and fixers; the budget
(`rounds` a run, `hours` a run with 0 for none, `attempt_minutes`, `parallel_attempts`, and
`batch`, the findings one attempt takes); the `severities` the attempts work; whether the
brief carries the `known_list` of settled items; whether a fix may change the `engine`
(`queue` leaves it an ENGINE REQUEST); and each `group`, the sheets one reviewer reads
together -- the same every round, so the rounds compare.

## Design calls

Where a finding turns on a choice among code-legal options, take the cheapest code-compliant
one, implement it, and report it as a CALL line. Leave a finding waiting only for a change to
the building's program, a cost well above the alternatives, or code text that cannot be
verified.

## Focus this run

(none)
"""


def default_groups(sheets):
    """Sheets by discipline letter, in their build order, at most GROUP_MAX to a group."""
    by = {}
    for s in sheets:
        name = next((n for p, n in DISCIPLINES if s.upper().startswith(p)), 'other')
        by.setdefault(name, []).append(s)
    out = []
    for name, ss in by.items():
        chunks = [ss[i:i+GROUP_MAX] for i in range(0, len(ss), GROUP_MAX)]
        for i, c in enumerate(chunks):
            out.append((name if len(chunks) == 1 else '%s-%d' % (name, i+1), c))
    return out


def parse_program(text):
    """{keys..., 'groups': [(name, [sheets])], 'body': str, 'stop': bool}."""
    if not text.startswith('---\n'):
        raise ValueError('autoreview.md: no front matter')
    head, sep, body = text[4:].partition('\n---\n')
    if not sep:
        raise ValueError('autoreview.md: the front matter is not closed with ---')
    prog, groups = dict(KEYS), []
    for n, line in enumerate(head.split('\n'), 2):
        line = line.split('#', 1)[0].rstrip()
        if not line.strip():
            continue
        m = re.match(r'^group ([A-Za-z0-9_.-]+):\s*(.+)$', line)
        if m:
            groups.append((m.group(1), [s.strip() for s in m.group(2).split(',') if s.strip()]))
            continue
        m = re.match(r'^([a-z_]+):\s*(.*)$', line)
        if not m or m.group(1) not in KEYS:
            raise ValueError('autoreview.md line %d: %r is not a known `key: value`' % (n, line))
        prog[m.group(1)] = m.group(2).strip()
    for k, ok in CHOICES.items():
        if prog[k] not in ok:
            raise ValueError('autoreview.md: %s is %r, not one of %s' % (k, prog[k], ', '.join(ok)))
    for k in ('rounds', 'hours', 'attempt_minutes', 'parallel_attempts', 'batch'):
        if not re.fullmatch(r'\d+(\.\d+)?', prog[k]):
            raise ValueError('autoreview.md: %s must be a number, not %r' % (k, prog[k]))
    sev = tuple(s.strip() for s in prog['severities'].split(','))
    if not sev or set(sev) - set(review.SEVERITIES):
        raise ValueError('autoreview.md: severities must come from %s' % ', '.join(review.SEVERITIES))
    prog['severities'] = sev
    names = [g for g, _s in groups]
    if len(set(names)) != len(names):
        raise ValueError('autoreview.md: a group is named twice')
    prog.update(groups=groups, body=body.strip('\n'),
                stop=bool(re.search(r'^STOP\s*$', body, re.M)))
    return prog


def program(slug, root=ROOT):
    p = program_path(slug, root)
    if not os.path.exists(p):
        raise ValueError('%s has no autoreview.md: run `arkitect autoreview init %s`' % (slug, slug))
    with open(p) as fh:
        return parse_program(fh.read())


# ---------------------------------------------------------------- the logs

def read_tsv(path):
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        rows = [l.rstrip('\n').split('\t') for l in fh if l.strip()]
    head = rows[0]
    return [dict(zip(head, r)) for r in rows[1:]]


def append_tsv(path, cols, rows):
    new = not os.path.exists(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a') as fh:
        if new:
            fh.write('\t'.join(cols) + '\n')
        for r in rows:
            fh.write('\t'.join(re.sub(r'[\t\n]+', ' ', str(r.get(c, ''))) for c in cols) + '\n')


def rounds(slug, root=ROOT):
    return read_tsv(os.path.join(log_dir(slug, root), 'rounds.tsv'))


def attempts(slug, root=ROOT):
    return read_tsv(os.path.join(log_dir(slug, root), 'attempts.tsv'))


def backfill(slug, root=ROOT):
    """rounds.tsv rebuilt from review.json, one row per ingest commit in order, for a project
       reviewed before autoreview kept the log. Duplicates were never recorded; they read ''."""
    batches = {}
    for f in review.load(slug, root)['findings']:
        batches.setdefault(f.get('commit', ''), []).append(f)
    rows = []
    for n, (commit, fs) in enumerate(batches.items(), 1):
        rows.append(_round_row(n, fs[0].get('found', ''), commit, '', '', fs, ''))
    return rows


def _round_row(n, date, commit, reviewer, sheets, added, duplicates):
    live = [f for f in added if f.get('verdict') != 'REJECTED']
    count = lambda sev: sum(1 for f in live if f['severity'] == sev)
    return {'round': n, 'date': date, 'commit': commit, 'reviewer': reviewer, 'sheets': sheets,
            'new_blocker': count('blocker'), 'new_major': count('major'),
            'new_minor': count('minor'), 'rejected': len(added) - len(live),
            'duplicates': duplicates,
            'majors': ','.join(f['id'] for f in live if f['severity'] in ('blocker', 'major'))}


# ---------------------------------------------------------------- init, begin

def init(slug, root=ROOT, sheets=None, force=False):
    """Write autoreview.md (groups from the build's sheets) and, if the project was reviewed
       before, rounds.tsv from its review.json. Returns the lines to print."""
    out = []
    p = program_path(slug, root)
    if os.path.exists(p) and not force:
        out.append('%s exists; kept (--force rewrites it)' % os.path.relpath(p, root))
    else:
        if sheets is None:          # the fingerprints also carry each document's page tree
            sheets = [s for s in review.fingerprints(slug, root) if not s.startswith('(')]
        keys = '\n'.join('%s: %s' % (k, v) for k, v in KEYS.items())
        groups = '\n'.join('group %s: %s' % (g, ', '.join(ss)) for g, ss in default_groups(sheets))
        with open(p, 'w') as fh:
            fh.write(TEMPLATE.format(keys=keys, groups=groups, slug=slug))
        out.append('wrote %s: %d sheets in %d groups' % (os.path.relpath(p, root), len(sheets),
                                                         len(default_groups(sheets))))
    rt = os.path.join(log_dir(slug, root), 'rounds.tsv')
    if not os.path.exists(rt):
        rows = backfill(slug, root)
        if rows:
            append_tsv(rt, ROUND_COLS, rows)
            out.append('wrote %s: %d earlier rounds from review.json' % (os.path.relpath(rt, root),
                                                                        len(rows)))
    return out


def run_state(slug, root=ROOT):
    return _read_json(os.path.join(state_dir(slug, root), 'run.json'), {})


def begin(slug, root=ROOT, today=None):
    """The integration branch autoreview/<slug>-<date> off main, in a worktree of its own;
       an unfinished run is resumed, never restarted. Returns run.json."""
    run = run_state(slug, root)
    if run.get('branch') and not run.get('stopped') and os.path.isdir(run.get('worktree', '')):
        return run
    top = main_checkout(root)
    branch = 'autoreview/%s-%s' % (slug, (today or datetime.date.today()).strftime('%Y%m%d'))
    tree = os.path.join(top, '.claude', 'worktrees', 'autoreview-%s' % slug)
    if not os.path.isdir(tree):
        exists = _git('branch', '--list', branch, cwd=top)
        _git('worktree', 'add', tree, *(([branch]) if exists else ['-b', branch, 'main']), cwd=top)
    run = {'branch': branch, 'worktree': tree, 'started': _now(),
           'first_round': max([int(r['round']) for r in rounds(slug, tree)] or [0]) + 1,
           'stopped': None}
    _write_json(os.path.join(state_dir(slug, root), 'run.json'), run)
    return run


def stop(slug, reason, root=ROOT):
    path = os.path.join(state_dir(slug, root), 'run.json')
    run = _read_json(path, {})
    run['stopped'] = reason or 'the designer stopped it'
    _write_json(path, run)
    return run


# ---------------------------------------------------------------- the outer loop

REVIEWER = ("Review directory: {dir}\n\nRead {dir}/brief.md first and follow it exactly. Review "
            "ONLY these sheets, every tile of each, comparing them where they show the same "
            "thing: {sheets}.\n\nReply with the JSON array of findings and nothing else.")
VERIFIER = ("Review directory: {dir}\n\nThe findings to verify are the JSON array in {raw}. "
            "Re-read each one against the tiles it names and return the same array with "
            "\"verdict\" (CONFIRMED | PLAUSIBLE | REJECTED) and \"verdict_reason\" on each. "
            "Reply with the JSON array and nothing else.")


def round_dir(slug, n, root=ROOT):
    return os.path.join(state_dir(slug, root), 'round-%02d' % n)


def current_round(slug, root=ROOT):
    """(n, round.json) of the newest round frozen, or (0, None)."""
    d = state_dir(slug, root)
    ns = sorted(int(m.group(1)) for m in (re.fullmatch(r'round-(\d+)', x) for x in os.listdir(d)) if m)
    for n in reversed(ns):
        meta = _read_json(os.path.join(round_dir(slug, n, root), 'round.json'))
        if meta:
            return n, meta
    return 0, None


def reopen_settled(slug, root=ROOT):
    """Every waiting finding whose note names decisions, all of them now settled (confirmed
       or superseded), goes back to open. Returns the ids."""
    from arkitect.harness import decisions
    recs = {f['id']: f['status'] for f, _b in decisions.all_decisions(root)}
    out = []
    for f in review.load(slug, root)['findings']:
        ids = [d for d in review._DID.findall(f.get('notes') or '') if d in recs]
        if f['status'] == 'waiting' and ids and all(recs[d] in ('confirmed', 'superseded') for d in ids):
            review.set_status(slug, f['id'], 'open', note=f['notes'] + ' -- reopened: answered',
                              root=root)
            out.append(f['id'])
    return out


def freeze(slug, root=ROOT, force=False, prepare=None):
    """Round n: the program read again, waiting findings whose questions are answered
       reopened, every grouped sheet rendered with the brief (and the known list), and each
       group's reviewer and verifier task written. A round frozen and not yet ingested is
       returned as it is. Returns round.json."""
    prog = program(slug, root)
    n, meta = current_round(slug, root)
    if meta and not meta.get('ingested'):
        return meta
    held = [r for r in stop_rules(slug, root) if r['holds']]
    if held and not force:
        raise ValueError('stopped: %s (--force runs a round anyway)' % '; '.join(
            '%s -- %s' % (r['rule'], r['detail']) for r in held))
    reopened = reopen_settled(slug, root)
    n = max([int(r['round']) for r in rounds(slug, root)] + [n]) + 1
    d = round_dir(slug, n, root)
    os.makedirs(d, exist_ok=True)
    sheets = [s for _g, ss in prog['groups'] for s in ss]
    known = review.known(slug, root) if prog['known_list'] == 'on' else None
    if known:
        with open(os.path.join(d, 'known.md'), 'w') as fh:
            fh.write(known)
    render = os.path.join(d, 'render')
    (prepare or review.prepare)(slug, sheets, out=render, root=root, known_list=known)
    tasks = []
    for g, ss in prog['groups']:
        raw, ver = os.path.join(d, '%s.json' % g), os.path.join(d, 'v-%s.json' % g)
        tasks.append({'group': g, 'sheets': ss, 'raw': raw, 'verified': ver,
                      'reviewer': REVIEWER.format(dir=render, sheets=', '.join(ss)),
                      'verifier': VERIFIER.format(dir=render, raw=raw)})
    meta = {'round': n, 'frozen': _now(), 'commit': review._head(root), 'dir': d,
            'render': render, 'models': {k: prog[k] for k in ('reviewer', 'verifier', 'fixer')},
            'reopened': reopened, 'tasks': tasks, 'ingested': None}
    _write_json(os.path.join(d, 'round.json'), meta)
    return meta


def ingest_round(slug, root=ROOT):
    """The frozen round's verified findings, every group's, into review.json, and its row
       into rounds.tsv. Refused while a group's verified file is missing."""
    n, meta = current_round(slug, root)
    if not meta:
        raise ValueError('no round frozen: run `arkitect autoreview round %s`' % slug)
    if meta.get('ingested'):
        raise ValueError('round %d is ingested already' % n)
    missing = [t['group'] for t in meta['tasks'] if not os.path.exists(t['verified'])]
    if missing:
        raise ValueError('round %d: no verified findings yet for %s' % (n, ', '.join(missing)))
    found = []
    for t in meta['tasks']:
        found += _read_json(t['verified'])
    index = _read_json(os.path.join(meta['render'], 'index.json'))
    added, dups = review.ingest(slug, found, index, root)
    row = _round_row(n, meta['frozen'][:10], index.get('commit', ''), meta['models']['reviewer'],
                     len(index['sheets']), added, len(dups))
    append_tsv(os.path.join(log_dir(slug, root), 'rounds.tsv'), ROUND_COLS, [row])
    meta['ingested'] = _now()
    _write_json(os.path.join(meta['dir'], 'round.json'), meta)
    return row, added, dups


# ---------------------------------------------------------------- the inner loop

WORKER = """# Attempt {name}: {slug}

You are fixing plan-review findings on one project's permit set. A separate verifier will
judge your work from the re-rendered sheets alone; a finding closed by deleting what it was
about is a discard, not a win.

## Setup

1. `git -C {top} worktree add {tree} -b {branch} {base}`
2. Work ONLY inside {tree}. Scratch files go in {scratch}.
3. Read the project's CLAUDE.md, if it has one, and the house style before editing.

## Rules

- Never run projects/{slug}/build.py or `arkitect dxf` in the worktree: they rewrite the
  deliverables. To look at a sheet: `arkitect gate render --project {slug} --sheets <S>`
  (PNGs outside the checkout), `--clip x0,y0,x1,y1` to zoom. LOOK at every sheet you change.
- Every figure on a sheet comes from the model: fix the model or the drawing code, never type
  a number the model already knows.
- Commit after every fix, files by name (never `git add -A`, `.` or `-u`), the gate green
  first; the message says which sheets moved.
- trace.md5: when the gate reports moved sheets, run `arkitect gate accept --project {slug}`
  so it passes, and leave every trace.md5 UNCOMMITTED. The lead accepts once, on the merge.
- Every other project must not move: the gate must say each matches. If one moved, you
  changed something shared: stop and undo it.
- Do not edit review.json (the lead records the outcome) or the decisions ledger. A design
  call is a CALL line in your report.
- {engine}
- Your budget is {minutes} minutes. Past it, commit what is green and report the rest open.
- Before finishing: `arkitect gate --full` passes. Do not merge and do not push.

## The findings ({count})

{findings}

## The designer's program

{program}

## Report (your final message)

The branch, its commits, and for each finding: FIXED (what changed, which sheet), OPEN (why),
or NEEDS DESIGNER (the question, with the cheapest code-compliant answer). Then any CALL
lines, any ENGINE REQUEST, and the sheets that moved.
"""
ENGINE_QUEUE = ("Do not edit the engine. A fix that needs one is an ENGINE REQUEST in your "
                "report, with the change you would make; leave the finding open.")
ENGINE_ALLOW = ("An engine change is allowed only as an opt-in keyword whose default leaves "
                "every project unmoved, proved with `arkitect gate --engine-base main "
                "--expect-unchanged`; say so in the report.")


def claims(slug, root=ROOT):
    return _read_json(os.path.join(state_dir(slug, root), 'claims.json'), {})


def _save_claims(slug, data, root=ROOT):
    _write_json(os.path.join(state_dir(slug, root), 'claims.json'), data)


def _live_claims(slug, root=ROOT, minutes=25):
    """Claims younger than twice the attempt budget: an older one is abandoned."""
    now = time.time()
    return {k: v for k, v in claims(slug, root).items()
            if now - v['since_ts'] < 2 * minutes * 60 and not v.get('recorded')}


def discards(slug, root=ROOT):
    out = {}
    for a in attempts(slug, root):
        if a['outcome'] == 'discarded':
            out.setdefault(a['finding'], []).append(a['note'])
    return out


def queue(slug, root=ROOT, prog=None):
    """Open findings the loop may take, worst first: of the program's severities, not claimed,
       discarded fewer than MAX_ATTEMPTS times."""
    prog = prog or program(slug, root)
    taken = {r for c in _live_claims(slug, root, float(prog['attempt_minutes'])).values()
             for r in c['findings']}
    tried = discards(slug, root)
    order = {s: i for i, s in enumerate(review.SEVERITIES)}
    return sorted((f for f in review.load(slug, root)['findings']
                   if f['status'] == 'open' and f['severity'] in prog['severities']
                   and f['id'] not in taken and len(tried.get(f['id'], ())) < MAX_ATTEMPTS),
                  key=lambda f: (order[f['severity']], f['id']))


def next_attempt(slug, root=ROOT, group=None, claim=False):
    """The next attempt: with `group`, every queued finding on that group's sheets (up to the
       program's batch); else the worst queued finding and the others on its sheet. With
       `claim`, it is recorded as taken and its worker brief written. Returns the attempt or
       None when the queue is empty."""
    prog = program(slug, root)
    q = queue(slug, root, prog)
    n = max([int(r['round']) for r in rounds(slug, root)] or [0])
    batch = int(float(prog['batch']))
    if group:
        sheets = dict(prog['groups']).get(group)
        if sheets is None:
            raise ValueError('no group %r in autoreview.md' % group)
        take = [f for f in q if f['sheet'] in sheets][:batch]
        name = 'r%d-%s' % (n, group)
    else:
        take = [f for f in q if q and f['sheet'] == q[0]['sheet']][:batch]
        name = 'r%d-%s' % (n, take[0]['id'].lower()) if take else ''
    if not take:
        return None
    live = claims(slug, root)
    base, k = name, 2
    while name in live:                  # a second attempt at the same group or finding
        name, k = '%s-%d' % (base, k), k + 1
    run = run_state(slug, root)
    top = main_checkout(root)
    tried = discards(slug, root)
    attempt = {'name': name, 'round': n, 'findings': [f['id'] for f in take],
               'branch': 'ar/%s/%s' % (slug, name), 'base': run.get('branch') or 'main',
               'tree': os.path.join(top, '.claude', 'worktrees', 'ar-%s-%s' % (slug, name)),
               'since': _now(), 'since_ts': time.time(), 'fixer': prog['fixer']}
    scratch = os.path.join(state_dir(slug, root), 'attempts', name)
    attempt['brief'] = os.path.join(scratch, 'brief.md')
    if claim:
        os.makedirs(scratch, exist_ok=True)
        with open(attempt['brief'], 'w') as fh:
            fh.write(WORKER.format(
                name=name, slug=slug, top=top, tree=attempt['tree'], branch=attempt['branch'],
                base=attempt['base'], scratch=scratch, minutes=prog['attempt_minutes'],
                engine=ENGINE_ALLOW if prog['engine'] == 'allow' else ENGINE_QUEUE,
                count=len(take), program=prog['body'] or '(none)',
                findings='\n\n'.join(_finding_text(f, tried.get(f['id'])) for f in take)))
        live[name] = attempt
        _save_claims(slug, live, root)
    return attempt


def _finding_text(f, earlier=None):
    out = ['### %s (%s, %s) on %s' % (f['id'], f['severity'], f['category'], f['sheet']),
           '- where: ' + f['where'], '- finding: ' + f['finding'], '- evidence: ' + f['evidence'],
           '- suggest: ' + f['suggest']]
    for note in earlier or ():
        out.append('- an earlier attempt was discarded: ' + note)
    return '\n'.join(out)


CLOSE = """# Close check: attempt {name}

A fixer changed the sheets below to close the findings listed. You have not seen the fix or
its reasoning, and you will not: judge only what the re-rendered sheets show. Read each
sheet's tiles; the finding's `where` says which tile to start from.

## The findings

{findings}

## What the sheets printed before and print nowhere now

{lost}

## The sheets as they are now

{sheets}

## Judge

For each finding, one of:
- "RESOLVED": what the finding described is gone, and what a reviewer or builder needed from
  that place is still on the sheet.
- "NOT RESOLVED": the fault is still visible, in whole or in part, or moved somewhere else.
- "RESOLVED BY REMOVAL": the fault is gone because the thing it was about -- a note, a
  dimension, a tag, a detail a builder needs -- was deleted or cut short instead of fixed.

Then look at every tile for a blocker or major fault the fix itself introduced: text now on
text, something now drawn across an opening, a figure now disagreeing with another sheet.

Reply with ONE JSON array and nothing else: one element per finding,
  {{"id": "R-012", "verdict": "RESOLVED", "reason": "the tile shows ..."}}
and one element per new fault, with "id": "NEW" and the plan-review fields:
  {{"id": "NEW", "sheet": "A-101", "where": "tile r1c2 -- ...", "category": one of {categories},
    "severity": "blocker" | "major", "finding": "...", "evidence": "quote what is printed",
    "suggest": "...", "verdict": "CONFIRMED" | "PLAUSIBLE", "verdict_reason": "..."}}
"""


def close(slug, name, root=ROOT, gate_run=None, prepare=None):
    """Run in the attempt's worktree: the gate against the integration branch, and the sheets
       it moved rendered with the close brief. Writes close.json; returns it."""
    live = claims(slug, root)
    if name not in live:
        raise ValueError('no attempt %r is claimed' % name)
    a = live[name]
    from arkitect.lib.verify import gate
    rep = (gate_run or gate.gate)(base=a['base'])
    mine = rep['projects'].get(slug) or {}
    moved = [m['sheet'] for m in (mine.get('sheets_moved') or [])]
    others = {s: [m['sheet'] for m in (p.get('sheets_moved') or [])]
              for s, p in rep['projects'].items() if s != slug}
    out = os.path.join(state_dir(slug, root), 'attempts', name, 'close')
    rec = {'attempt': name, 'gate_ok': bool(rep['ok']), 'failures': rep.get('failures', []),
           'moved': moved, 'others_moved': {s: m for s, m in others.items() if m},
           'vocab_lost': mine.get('vocab_lost') or [], 'dir': out, 'brief': None}
    if moved:
        render = (prepare or review.prepare)(slug, moved, out=out, root=root)
        index = _read_json(os.path.join(render, 'index.json'))
        found = {f['id']: f for f in review.load(slug, root)['findings']}
        sheets = '\n'.join('- **%s**: whole `%s`; tiles %s' % (
            s, v['whole'], ', '.join('`%s`' % t for t in v['tiles'])) for s, v in index['sheets'].items())
        rec['brief'] = os.path.join(render, 'close.md')
        with open(rec['brief'], 'w') as fh:
            fh.write(CLOSE.format(
                name=name, sheets=sheets,
                findings='\n\n'.join(_finding_text(found[i]) for i in a['findings'] if i in found),
                lost=', '.join(rec['vocab_lost']) or '(nothing)',
                categories=' | '.join('"%s"' % c for c in review.CATEGORIES)))
    _write_json(os.path.join(state_dir(slug, root), 'attempts', name, 'close.json'), rec)
    return rec


def judge(slug, name, verdicts, root=ROOT):
    """KEEP or DISCARD from close.json and the close checker's array. KEEP needs the gate
       green, every other project unmoved, a sheet moved, no RESOLVED BY REMOVAL, and at least
       one RESOLVED -- on a sheet that moved, or it is not. Writes judgment.json; returns it."""
    a = claims(slug, root).get(name)
    if not a:
        raise ValueError('no attempt %r is claimed' % name)
    rec = _read_json(os.path.join(state_dir(slug, root), 'attempts', name, 'close.json'))
    if rec is None:
        raise ValueError('no close check for %s: run `arkitect autoreview close %s %s` in its '
                         'worktree' % (name, slug, name))
    per = {v['id']: v for v in verdicts if v.get('id') not in (None, 'NEW')}
    bad = [v for v in per.values() if v.get('verdict') not in CLOSE_VERDICTS]
    if bad or set(per) - set(a['findings']):
        raise ValueError('the verdicts name %s' % ', '.join(sorted(
            [v['id'] + ' ' + str(v.get('verdict')) for v in bad] + list(set(per) - set(a['findings'])))))
    new = [v for v in verdicts if v.get('id') == 'NEW']
    for f in new:
        f.pop('id')
    why = []
    if not rec['gate_ok']:
        why.append('the gate is red: ' + '; '.join(rec['failures'][:3]))
    if rec['others_moved']:
        why.append('another project moved: ' + ', '.join(
            '%s %s' % (s, ','.join(m)) for s, m in rec['others_moved'].items()))
    if not rec['moved']:
        why.append('no sheet moved, so nothing on one can have been fixed')
    removed = [i for i, v in per.items() if v['verdict'] == 'RESOLVED BY REMOVAL']
    if removed:
        why.append('resolved by removal: ' + ', '.join(removed))
    sheet = {f['id']: f['sheet'] for f in review.load(slug, root)['findings']}
    for i, v in per.items():            # `review set fixed` would refuse it: nothing on it changed
        if v['verdict'] == 'RESOLVED' and sheet.get(i) not in rec['moved']:
            v.update(verdict='NOT RESOLVED', reason='%s did not move' % sheet.get(i))
    resolved = [i for i in a['findings'] if per.get(i, {}).get('verdict') == 'RESOLVED']
    if not resolved and not why:
        why.append('the close check resolved none of them')
    j = {'attempt': name, 'keep': not why, 'why': why, 'resolved': resolved if not why else [],
         'open': [i for i in a['findings'] if i not in resolved or why],
         'reasons': {i: per.get(i, {}).get('reason', 'no verdict') for i in a['findings']},
         'new': new}
    _write_json(os.path.join(state_dir(slug, root), 'attempts', name, 'judgment.json'), j)
    return j


def record(slug, name, root=ROOT, waiting=(), note=None, today=None):
    """After the lead has merged a KEPT attempt into the integration branch (or deleted a
       DISCARDED one): findings resolved are set fixed, the new faults the close check saw are
       ingested, the rest are logged discarded, `waiting` ones set waiting with `note`, and the
       claim is released. Returns the attempts.tsv rows."""
    live = claims(slug, root)
    a = live.get(name)
    if not a:
        raise ValueError('no attempt %r is claimed' % name)
    j = _read_json(os.path.join(state_dir(slug, root), 'attempts', name, 'judgment.json'))
    if j is None and not waiting:
        raise ValueError('no judgment for %s: run `arkitect autoreview judge`' % name)
    j = j or {'keep': False, 'why': ['waits on the designer'], 'resolved': [], 'reasons': {}, 'new': []}
    if waiting and not note:
        raise ValueError('--waiting needs --note naming what they wait on')
    if j['keep']:
        r = subprocess.run(['git', 'merge-base', '--is-ancestor', a['branch'], 'HEAD'], cwd=root)
        if r.returncode:
            raise ValueError('%s is KEEP but %s is not merged into this checkout: merge it first'
                             % (name, a['branch']))
    minutes = round((time.time() - a['since_ts']) / 60)
    date = (today or datetime.date.today()).isoformat()
    found = {f['id']: f for f in review.load(slug, root)['findings']}
    rows = []
    for i in a['findings']:
        if i in waiting:
            review.set_status(slug, i, 'waiting', note=note, root=root)
            outcome, why = 'waiting', note
        elif j['keep'] and i in j['resolved']:
            review.set_status(slug, i, 'fixed', note='autoreview %s: %s' % (name, j['reasons'].get(i, '')),
                              root=root)
            outcome, why = 'kept', j['reasons'].get(i, '')
        else:
            outcome = 'discarded'
            why = '; '.join(j['why']) if j['why'] else j['reasons'].get(i, 'not resolved')
        f = found.get(i, {})
        rows.append({'round': a['round'], 'attempt': name, 'finding': i,
                     'severity': f.get('severity', ''), 'sheet': f.get('sheet', ''),
                     'outcome': outcome, 'branch': a['branch'], 'minutes': minutes,
                     'fixer': a.get('fixer', ''), 'date': date, 'note': why})
    append_tsv(os.path.join(log_dir(slug, root), 'attempts.tsv'), ATTEMPT_COLS, rows)
    if j['keep'] and j.get('new'):
        review.ingest(slug, j['new'], None, root)
    live[name]['recorded'] = _now()
    _save_claims(slug, live, root)
    return rows


# ---------------------------------------------------------------- when to stop

def _actionable(row, found):
    ids = [i for i in (row.get('majors') or '').split(',') if i]
    if ids and found:
        return sum(1 for i in ids if found.get(i, {}).get('status') != 'waiting')
    return int(row.get('new_blocker') or 0) + int(row.get('new_major') or 0)


def stop_rules(slug, root=ROOT, now=None):
    """[{rule, holds, detail}] for each stop rule, in the order docs/autoreview.md gives."""
    prog = program(slug, root)
    run = run_state(slug, root)
    rs = rounds(slug, root)
    found = {f['id']: f for f in review.load(slug, root)['findings']}
    act = [_actionable(r, found) for r in rs]
    out = []
    out.append({'rule': 'designer', 'holds': bool(prog['stop'] or run.get('stopped')),
                'detail': run.get('stopped') or ('STOP in autoreview.md' if prog['stop'] else 'running')})
    out.append({'rule': 'converged', 'holds': len(act) >= 2 and act[-1] == 0 and act[-2] == 0,
                'detail': 'majors the loop can act on, last two rounds: %s' % (act[-2:] or 'none yet')})
    mean = [sum(act[i-2:i+1]) / 3 for i in range(2, len(act))]
    stalled = len(mean) >= 6 and min(mean[-3:]) >= min(mean[:-3])
    out.append({'rule': 'noise floor', 'holds': stalled,
                'detail': 'three-round mean of majors %s; lowest before %s' % (
                    ', '.join('%.1f' % m for m in mean[-3:]) or 'n/a',
                    '%.1f' % min(mean[:-3]) if len(mean) > 3 else 'n/a')})
    done = len([r for r in rs if int(r['round']) >= run.get('first_round', 10**6)])
    hours = float(prog['hours'])
    spent = ((now or time.time()) - datetime.datetime.fromisoformat(run['started']).timestamp()) / 3600 \
        if run.get('started') else 0
    out.append({'rule': 'budget', 'holds': bool(run) and (done >= int(float(prog['rounds'])) or
                                                          (hours > 0 and spent >= hours)),
                'detail': '%d of %s rounds this run, %.1f h%s' % (
                    done, prog['rounds'], spent, ' of %s' % prog['hours'] if hours else '')})
    return out


def status(slug, root=ROOT):
    prog = program(slug, root)
    n, meta = current_round(slug, root)
    stage = 'no round yet'
    if meta:
        got = [t['group'] for t in meta['tasks'] if os.path.exists(t['raw'])]
        ver = [t['group'] for t in meta['tasks'] if os.path.exists(t['verified'])]
        if meta.get('ingested'):
            stage = 'round %d ingested; attempts' % n
        else:
            stage = 'round %d frozen: %d of %d reviewed, %d verified' % (
                n, len(got), len(meta['tasks']), len(ver))
    live = _live_claims(slug, root, float(prog['attempt_minutes']))
    findings = review.load(slug, root)['findings']
    count = lambda st: {s: sum(1 for f in findings if f['status'] == st and f['severity'] == s)
                        for s in review.SEVERITIES}
    return {'project': slug, 'run': run_state(slug, root), 'stage': stage, 'round': n,
            'claims': {k: v['findings'] for k, v in live.items()},
            'queue': len(queue(slug, root, prog)), 'open': count('open'), 'waiting': count('waiting'),
            'rounds': rounds(slug, root), 'attempts': attempts(slug, root),
            'stop': stop_rules(slug, root)}


def status_text(st):
    out = ['autoreview %s: %s' % (st['project'], st['stage'])]
    run = st['run']
    if run:
        out.append('  run: %s since %s%s' % (run.get('branch'), run.get('started'),
                                             ', STOPPED: %s' % run['stopped'] if run.get('stopped') else ''))
    out.append('  queue %d; open %s; waiting %s' % (
        st['queue'], ', '.join('%d %s' % (v, k) for k, v in st['open'].items() if v) or 'none',
        ', '.join('%d %s' % (v, k) for k, v in st['waiting'].items() if v) or 'none'))
    for k, v in st['claims'].items():
        out.append('  attempt %s: %s' % (k, ', '.join(v)))
    out.append('  round  new blk/maj/min  rejected  dup')
    for r in st['rounds'][-8:]:
        out.append('  %5s  %3s/%3s/%3s  %8s  %3s' % (r['round'], r['new_blocker'], r['new_major'],
                                                    r['new_minor'], r['rejected'], r['duplicates']))
    kept = sum(1 for a in st['attempts'] if a['outcome'] == 'kept')
    out.append('  findings kept %d, discarded %d, waiting %d' % (
        kept, sum(1 for a in st['attempts'] if a['outcome'] == 'discarded'),
        sum(1 for a in st['attempts'] if a['outcome'] == 'waiting')))
    for r in st['stop']:
        out.append('  stop rule %-12s %s  (%s)' % (r['rule'], 'HOLDS' if r['holds'] else '-', r['detail']))
    return '\n'.join(out)


# ---------------------------------------------------------------- the chart, landing

def chart(slug, root=ROOT):
    """rounds.tsv as a self-contained HTML page: new majors and minors a round."""
    rs = rounds(slug, root)
    w, h, pad = 720, 300, 40
    mx = max([int(r['new_major']) + int(r['new_blocker']) for r in rs] +
             [int(r['new_minor']) for r in rs] + [1])
    x = lambda i: pad + (w - 2*pad) * (i / max(len(rs) - 1, 1))
    y = lambda v: h - pad - (h - 2*pad) * v / mx
    def line(key, colour):
        pts = ' '.join('%.1f,%.1f' % (x(i), y(v)) for i, v in enumerate(key(r) for r in rs))
        return '<polyline fill="none" stroke="%s" stroke-width="2" points="%s"/>' % (colour, pts)
    major = lambda r: int(r['new_major']) + int(r['new_blocker'])
    minor = lambda r: int(r['new_minor'])
    ticks = ''.join('<text x="%.1f" y="%d" font-size="11" text-anchor="middle">%s</text>' % (
        x(i), h - pad + 16, r['round']) for i, r in enumerate(rs))
    return ('<!doctype html><meta charset="utf-8"><title>Review Rounds</title>'
            '<style>:root{color-scheme:light dark;--fg:#222;--bg:#fff}@media (prefers-color-scheme:dark)'
            '{:root{--fg:#ddd;--bg:#161616}}body{font:14px system-ui;margin:16px;color:var(--fg);'
            'background:var(--bg)}svg{max-width:100%%;height:auto}text{fill:var(--fg)}</style>'
            '<h1>%s: new findings a round</h1><p>Blockers and majors (red), minors (grey), '
            'confirmed or plausible, duplicates of earlier findings left out.</p>'
            '<svg viewBox="0 0 %d %d">%s%s%s</svg>' % (slug, w, h, line(minor, '#999'),
                                                      line(major, '#c0392b'), ticks))


def land(slug, root=ROOT, push=True, run=None):
    """In the main checkout: fast-forward main to the integration branch, rebuild the project,
       export its DXF, gate, commit the deliverables by name, push. Stops at the first step
       that fails, with its output."""
    run = run or run_state(slug, root)
    if not run.get('branch'):
        raise ValueError('no run to land: `arkitect autoreview begin %s` starts one' % slug)
    if os.path.realpath(root) != os.path.realpath(main_checkout(root)):
        raise ValueError('land runs in the main checkout (%s), not a worktree' % main_checkout(root))
    if _git('rev-parse', '--abbrev-ref', 'HEAD', cwd=root) != 'main':
        raise ValueError('land runs on main')
    steps = [['git', 'merge', '--ff-only', run['branch']],
             [sys.executable, os.path.join('projects', slug, 'build.py')],
             [sys.executable, '-m', 'arkitect.harness.cli', 'dxf', os.path.join('projects', slug, 'build.py')],
             [sys.executable, '-m', 'arkitect.harness.cli', 'gate']]
    for cmd in steps:
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError('%s failed (exit %d):\n%s' % (' '.join(cmd), r.returncode,
                                                             (r.stdout + r.stderr)[-3000:]))
    changed = [p for p in _git('diff', '--name-only', '--', os.path.join('projects', slug),
                               cwd=root).splitlines()
               if p.lower().endswith(('.pdf', '.dxf'))]
    if changed:
        _git('add', '--', *changed, cwd=root)
        _git('commit', '-m', 'autoreview %s: the deliverables rebuilt from %s' % (slug, run['branch']),
             cwd=root)
    if push:
        _git('push', 'origin', 'main', cwd=root)
    return changed


# ---------------------------------------------------------------- the command

def _opt(argv, flag):
    return next((argv[i+1] for i, a in enumerate(argv[:-1]) if a == flag), None)


def main(argv):
    cmds = ('init', 'begin', 'round', 'ingest', 'next', 'close', 'judge', 'record', 'status',
            'stop', 'chart', 'land')
    if len(argv) < 2 or argv[0] not in cmds:
        print(__doc__)
        return 1
    cmd, slug = argv[0], argv[1]
    try:
        if cmd == 'init':
            print('\n'.join(init(slug, force='--force' in argv)))
        elif cmd == 'begin':
            run = begin(slug)
            print('run on %s\nwork in: %s' % (run['branch'], run['worktree']))
        elif cmd == 'round':
            meta = freeze(slug, force='--force' in argv)
            if '--json' in argv:
                from arkitect.lib import interface
                interface.emit('autoreview-round', meta)
                return 0
            print('round %d frozen at %s: %s' % (meta['round'], meta['commit'], meta['dir']))
            if meta['reopened']:
                print('reopened, their questions answered: ' + ', '.join(meta['reopened']))
            for t in meta['tasks']:
                print('  %-24s %s\n      reviewer reply -> review parse ... --out %s\n'
                      '      verifier reply -> review parse ... --out %s' % (
                          t['group'], ', '.join(t['sheets']), t['raw'], t['verified']))
        elif cmd == 'ingest':
            row, added, dups = ingest_round(slug)
            print('round %s: %s blocker, %s major, %s minor new; %s rejected; %s duplicates' % (
                row['round'], row['new_blocker'], row['new_major'], row['new_minor'],
                row['rejected'], row['duplicates']))
            for f in added:
                if f['status'] == 'open' and f['severity'] in ('blocker', 'major'):
                    print('  ' + review._line(f))
        elif cmd == 'next':
            a = next_attempt(slug, group=_opt(argv, '--group'), claim='--claim' in argv)
            if '--json' in argv:
                from arkitect.lib import interface
                interface.emit('autoreview-attempt', {'project': slug, 'attempt': a})
            elif a is None:
                print('queue empty')
            else:
                print('%s %s: %s\n  branch %s off %s\n  brief %s' % (
                    'claimed' if '--claim' in argv else 'next', a['name'], ', '.join(a['findings']),
                    a['branch'], a['base'], a['brief'] if '--claim' in argv else '(--claim writes it)'))
        elif cmd == 'close':
            rec = close(slug, argv[2])
            print('gate %s; moved %s; other projects moved %s; lost %s\nclose brief: %s' % (
                'green' if rec['gate_ok'] else 'RED', ', '.join(rec['moved']) or 'nothing',
                rec['others_moved'] or 'none', ', '.join(rec['vocab_lost']) or 'nothing',
                rec['brief'] or '(none: no sheet moved)'))
        elif cmd == 'judge':
            with open(argv[3]) as fh:
                j = judge(slug, argv[2], review.parse(fh.read()))
            print('%s %s: %s' % ('KEEP' if j['keep'] else 'DISCARD', argv[2],
                                 'resolved ' + ', '.join(j['resolved']) if j['keep'] else '; '.join(j['why'])))
            if j['keep'] and j['open']:
                print('  still open: ' + ', '.join(j['open']))
            if j['new']:
                print('  %d new fault(s) the fix introduced, filed on record' % len(j['new']))
        elif cmd == 'record':
            w = [x for x in (_opt(argv, '--waiting') or '').split(',') if x]
            for r in record(slug, argv[2], waiting=w, note=_opt(argv, '--note')):
                print('%s %s %s' % (r['finding'], r['outcome'], r['note'][:100]))
        elif cmd == 'status':
            st = status(slug)
            if '--json' in argv:
                from arkitect.lib import interface
                interface.emit('autoreview', st)
            else:
                print(status_text(st))
        elif cmd == 'stop':
            stop(slug, _opt(argv, '--reason'))
            print('stopped')
        elif cmd == 'chart':
            html = chart(slug)
            out = _opt(argv, '--out') or os.path.join(state_dir(slug), 'rounds.html')
            with open(out, 'w') as fh:
                fh.write(html)
            print(out)
        else:
            changed = land(slug, push='--no-push' not in argv)
            print('landed %s; deliverables %s' % (slug, ', '.join(changed) or 'unchanged'))
    except (ValueError, RuntimeError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
