"""The decisions ledger: every call made among code-legal options, who made it, and what
moves if it is reversed. One file per decision in decisions/.

    python3 -m harness.decisions pending              # what waits on the designer, as questions
    python3 -m harness.decisions list [--status S] [--project P]
    python3 -m harness.decisions show D-912
    python3 -m harness.decisions about projects/<slug>/src/grading.py   # before editing it
    python3 -m harness.decisions new "<title>" --project P [--project Q]   # the next id, open
    python3 -m harness.decisions set D-912 confirmed --quote "<designer>, 2026-09-22: ..."
    python3 -m harness.decisions set D-912 waiting --on "AEP Ohio"
    python3 -m harness.decisions set D-912 superseded --by D-931

WHY. CLAUDE.md carried these as paragraphs -- "on three decisions not yet confirmed" --
about 75,000 characters of them, loaded into every session, with nothing to list what was
still open, nothing to say who decided, and nothing to stop a paragraph outliving the code
it described. A decision is a record with a status. Code comments and the CLAUDE.md files
cite it by id (D-912 -- examples in this repository use D-9nn, which no record takes);
a SHEET never does, because an id is this repository's vocabulary
and means nothing to a plan reviewer (lib/verify/gate.py fails a sheet that prints one).

A DECISION FILE is Markdown with a front matter of `key: value` lines and `key:` lists of
`  - item` lines (a strict YAML subset, read without a YAML library):

    id, title, status, by, date, projects[]    always
    decision                                   what was chosen, one paragraph
    alternatives[], if_reversed[], refs[]      what else was possible, what moves, where
    ask                                        status open: the question for the designer
    waiting_on                                 status waiting: who has to answer
    confirmed                                  status confirmed: the designer's words, dated
    superseded_by                              status superseded: the id that replaced it

and a body: the full account, as it stood in CLAUDE.md when it moved here.

STATUS is the point of the file. `open` is a call an agent made that the designer of record
has not confirmed -- who that is comes from harness/config.py, [designer] -- and only the
designer's words make it `confirmed`; `set` requires them (--quote). An agent that
makes a new call among code-legal options records it here with `new`, the way
feedback memory "mark my own design calls" asked it to be recorded in CLAUDE.md.
"""
import datetime
import os
import re
import sys

from lib import workspace

ROOT = workspace.WORKSPACE             # the ledger belongs to the projects, not the engine
DIR = os.path.join(ROOT, 'decisions')
STATUSES = ('open', 'confirmed', 'waiting', 'superseded')
BY = ('designer', 'agent', 'third-party')   # designer: the designer of record, harness/config.py
SCALARS = ('id', 'title', 'status', 'by', 'date', 'decision', 'ask', 'waiting_on', 'confirmed',
           'superseded_by')
LISTS = ('projects', 'alternatives', 'if_reversed', 'refs')
ID = re.compile(r'\bD-\d{3}\b')
PROJECTS = ('all',)          # or any project under projects/, looked up


# ---------------------------------------------------------------- the file format

def parse(text):
    """(fields, body). Raises ValueError on a front matter this module did not write."""
    if not text.startswith('---\n'):
        raise ValueError('no front matter')
    head, _sep, body = text[4:].partition('\n---\n')
    fields, key = {}, None
    for n, line in enumerate(head.split('\n'), 2):
        if not line.strip():
            continue
        if line.startswith('  - '):
            if key not in LISTS:
                raise ValueError('line %d: a list item under %r, which is not a list' % (n, key))
            fields[key].append(line[4:])
            continue
        m = re.match(r'^([a-z_]+):(?: (.*))?$', line)
        if not m:
            raise ValueError('line %d: %r is not `key: value`' % (n, line))
        key, val = m.group(1), m.group(2)
        if key in LISTS:
            if val:
                raise ValueError('line %d: %s is a list; put items on `  - ` lines' % (n, key))
            fields[key] = []
        elif key in SCALARS:
            fields[key] = val or ''
        else:
            raise ValueError('line %d: unknown field %r' % (n, key))
    return fields, body.lstrip('\n')


def render(fields, body):
    out = ['---']
    for k in SCALARS[:5]:
        out.append('%s: %s' % (k, fields.get(k, '')))
    out.append('projects:')
    out += ['  - ' + p for p in fields.get('projects', [])]
    for k in SCALARS[5:]:
        if fields.get(k):
            out.append('%s: %s' % (k, fields[k]))
    for k in LISTS[1:]:
        if fields.get(k):
            out.append('%s:' % k)
            out += ['  - ' + v for v in fields[k]]
    out.append('---')
    return '\n'.join(out) + '\n\n' + body.rstrip('\n') + '\n'


def path_of(did, root=ROOT):
    return os.path.join(root, 'decisions', '%s.md' % did)


def load(did, root=ROOT):
    with open(path_of(did, root)) as fh:
        return parse(fh.read())


def save(did, fields, body, root=ROOT):
    with open(path_of(did, root), 'w') as fh:
        fh.write(render(fields, body))


def all_decisions(root=ROOT):
    """[(fields, body)] in id order."""
    d = os.path.join(root, 'decisions')
    out = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else ():
        if ID.fullmatch(f[:-3] or '') and f.endswith('.md'):
            with open(os.path.join(d, f)) as fh:
                out.append(parse(fh.read()))
    return out


# ---------------------------------------------------------------- what makes one valid

def problems(fields, body, filename=None, root=ROOT):
    """Every way a decision file is malformed, as sentences."""
    bad = []
    did = fields.get('id', '?')
    if not ID.fullmatch(did):
        bad.append('%s: id must be D-nnn' % did)
    if filename and filename != did + '.md':
        bad.append('%s is in %s' % (did, filename))
    for k in ('title', 'status', 'by', 'date', 'decision'):
        if not fields.get(k):
            bad.append('%s: %s is missing' % (did, k))
    st = fields.get('status')
    if st and st not in STATUSES:
        bad.append('%s: status %r is not one of %s' % (did, st, ', '.join(STATUSES)))
    if fields.get('by') and fields['by'] not in BY:
        bad.append('%s: by %r is not one of %s' % (did, fields['by'], ', '.join(BY)))
    if fields.get('date') and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', fields['date']):
        bad.append('%s: date must be YYYY-MM-DD' % did)
    if not fields.get('projects'):
        bad.append('%s: projects is empty' % did)
    for p in fields.get('projects', []):
        if p not in PROJECTS and not os.path.isdir(os.path.join(root, 'projects', p)):
            bad.append('%s: project %r does not exist' % (did, p))
    need = {'open': 'ask', 'waiting': 'waiting_on', 'confirmed': 'confirmed',
            'superseded': 'superseded_by'}.get(st)
    if need and not fields.get(need):
        bad.append('%s: a %s decision needs %s' % (did, st, need))
    if st == 'open' and fields.get('by') == 'designer':
        bad.append('%s: open means nobody has confirmed it, so it cannot be by the designer' % did)
    if st == 'open' and not fields.get('if_reversed'):
        bad.append('%s: an open decision says what moves if it is reversed (if_reversed)' % did)
    if not body.strip():
        bad.append('%s: the body is empty' % did)
    return bad


# ---------------------------------------------------------------- commands

def _designer():
    from harness import config
    return config.get('designer.name')


def next_id(root=ROOT):
    ids = [int(f['id'][2:]) for f, _b in all_decisions(root)]
    return 'D-%03d' % (max(ids)+1 if ids else 1)


def new(title, projects, root=ROOT):
    """An open decision with the next id: the agent then writes the body and fields."""
    did = next_id(root)
    fields = {'id': did, 'title': title, 'status': 'open', 'by': 'agent',
              'date': datetime.date.today().isoformat(), 'projects': list(projects),
              'decision': 'TODO', 'ask': 'TODO', 'if_reversed': ['TODO']}
    save(did, fields, 'TODO: the account -- what was decided, why, and what else was possible.\n',
         root)
    return did


def set_status(did, status, quote=None, on=None, by=None, root=ROOT):
    """Move a decision to a status, with what that status requires."""
    fields, body = load(did, root)
    if status not in STATUSES:
        raise ValueError('status must be one of %s' % ', '.join(STATUSES))
    if status == 'confirmed':
        if not quote:
            who = _designer()
            raise ValueError('confirmed needs %s\'s words: --quote "%s, <date>: ..."' % (who, who))
        fields.update(status='confirmed', by='designer', confirmed=quote)
    elif status == 'waiting':
        if not on:
            raise ValueError('waiting needs who: --on "AEP Ohio"')
        fields.update(status='waiting', waiting_on=on)
    elif status == 'superseded':
        if not by or not ID.fullmatch(by):
            raise ValueError('superseded needs the decision that replaced it: --by D-nnn')
        fields.update(status='superseded', superseded_by=by)
    else:
        fields['status'] = 'open'
    bad = problems(fields, body, root=root)
    if bad:
        raise ValueError('\n'.join(bad))
    save(did, fields, body, root)
    return fields


def pending_text(root=ROOT, project=None):
    """What is waiting on the designer: every open decision as its question, then what is waiting on
       someone else."""
    ds = [f for f, _b in all_decisions(root)
          if not project or project in f['projects'] or 'all' in f['projects']]
    opn = [f for f in ds if f['status'] == 'open']
    wait = [f for f in ds if f['status'] == 'waiting']
    out = ['%d decision(s) waiting on %s:' % (len(opn), _designer())]
    for f in opn:
        out.append('\n%s  %s  [%s]' % (f['id'], f['title'], ', '.join(f['projects'])))
        out.append('    ASK: ' + f['ask'])
        if f.get('alternatives'):
            out.append('    ALTERNATIVES: ' + '; '.join(f['alternatives']))
    if wait:
        out.append('\n%d waiting on someone else:' % len(wait))
        for f in wait:
            out.append('  %s  %s -- %s' % (f['id'], f['title'], f['waiting_on']))
    return '\n'.join(out)


def about(path, root=ROOT):
    """The records whose refs name this path, or a file under it, or a directory holding it:
       what has been decided about the thing you are about to change."""
    path = os.path.normpath(path).rstrip(os.sep)
    out = []
    for f, _b in all_decisions(root):
        for r in f.get('refs', []):
            ref = os.path.normpath(r.partition(' @')[0].strip()).rstrip(os.sep)
            if ref == path or ref.startswith(path + os.sep) or path.startswith(ref + os.sep):
                out.append(f)
                break
    return out


def _opt(argv, flag):
    return [argv[i+1] for i, a in enumerate(argv[:-1]) if a == flag]


def main(argv):
    if not argv or argv[0] not in ('pending', 'list', 'show', 'new', 'set', 'about'):
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == 'pending':
        p = _opt(argv, '--project')
        print(pending_text(project=p[0] if p else None))
        return 0
    if cmd == 'list':
        st, pj = _opt(argv, '--status'), _opt(argv, '--project')
        for f, _b in all_decisions():
            if st and f['status'] != st[0]:
                continue
            if pj and pj[0] not in f['projects'] and 'all' not in f['projects']:
                continue
            print('%s  %-10s %-6s %s' % (f['id'], f['status'], f['by'], f['title']))
        return 0
    if cmd == 'about':
        hits = about(argv[1])
        for f in hits:
            print('%s  %-10s %s' % (f['id'], f['status'], f['title']))
            if f['status'] == 'open':
                print('            OPEN -- if reversed: ' + '; '.join(f.get('if_reversed', [])))
        if not hits:
            print('no decision refers to %s' % argv[1])
        return 0
    if cmd == 'show':
        with open(path_of(argv[1])) as fh:
            print(fh.read())
        return 0
    try:
        if cmd == 'new':
            print(new(argv[1], _opt(argv, '--project') or ['all']))
        else:
            q, on, by = _opt(argv, '--quote'), _opt(argv, '--on'), _opt(argv, '--by')
            f = set_status(argv[1], argv[2], q[0] if q else None, on[0] if on else None,
                           by[0] if by else None)
            print('%s is %s' % (f['id'], f['status']))
            if f['status'] != 'open' and f.get('if_reversed'):
                print('If this reverses the decision, what moves:\n  ' + '\n  '.join(f['if_reversed']))
    except (ValueError, OSError, IndexError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
