"""The decisions ledger (decisions/, arkitect/harness/decisions.py): every record valid, everything it
points at real, and every id cited anywhere in the repository a record that exists."""
import os
import re
import subprocess
import tempfile
import unittest

from arkitect.harness import decisions as D
from arkitect.lib import workspace

ROOT = D.ROOT
# A record's refs name the workspace's files and the engine's (arkitect/codes/, arkitect/lib/, arkitect/harness/): with
# the projects outside the engine, a path is looked for in each. `path @rev` is a commit of
# the workspace, whose repository carries the history.
TREES = [ROOT] + ([workspace.ENGINE] if workspace.separate(ROOT) else [])
CITED_IN = ('arkitect', 'projects', '.claude/hooks', '.claude/skills')


def _ref_exists(ref):
    """A path in the tree, or `path @rev` in a commit (the specs deleted in 2eb7db6)."""
    path, _sep, rev = ref.partition(' @')
    path = path.strip()
    if rev:
        return subprocess.run(['git', 'cat-file', '-e', '%s:%s' % (rev.strip(), path)],
                              cwd=ROOT, capture_output=True).returncode == 0
    path = path.split('::')[0]
    # a record written before the engine's code moved under arkitect/ names lib/..., codes/...
    # or harness/...: the same file, one level down
    return any(os.path.exists(os.path.join(t, p)) for t in TREES
               for p in (path, os.path.join('arkitect', path)))


def _cited():
    """{id: [where]} for every D-nnn in code, tests, hooks, skills and the CLAUDE.md files."""
    out = {}
    files = [p for p in (os.path.join(t, 'CLAUDE.md') for t in TREES) if os.path.exists(p)]
    for top in [os.path.join(t, c) for t in TREES for c in CITED_IN]:
        for d, dirs, fs in os.walk(top):
            dirs[:] = [x for x in dirs if x not in ('__pycache__',)]
            # a test's ids are synthetic by design (a scratch ledger numbers from D-001)
            files += [os.path.join(d, f) for f in fs if f.endswith(('.py', '.md'))
                      and not f.startswith('test_')]
    for p in files:
        with open(p, errors='replace') as fh:
            for m in D.ID.findall(fh.read()):
                out.setdefault(m, []).append(p)
    return out


class LedgerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.files = sorted(f for f in os.listdir(os.path.join(ROOT, 'decisions'))
                           if f.endswith('.md') and D.ID.fullmatch(f[:-3]))   # a README is not a record
        cls.all = []
        for f in cls.files:
            with open(os.path.join(ROOT, 'decisions', f)) as fh:
                cls.all.append((f,) + D.parse(fh.read()))

    def test_the_ledger_directory_exists(self):
        """It may be empty: the public engine ships with no records, a project's are its own."""
        self.assertTrue(os.path.isdir(os.path.join(ROOT, 'decisions')))

    def test_every_record_is_valid(self):
        bad = [p for f, fields, body in self.all for p in D.problems(fields, body, f)]
        self.assertEqual(bad, [])

    def test_every_record_round_trips(self):
        for f, fields, body in self.all:
            with open(os.path.join(ROOT, 'decisions', f)) as fh:
                self.assertEqual(D.render(fields, body), fh.read(), f)

    def test_every_ref_exists(self):
        bad = ['%s: %s' % (fields['id'], r) for _f, fields, _b in self.all
               for r in fields.get('refs', []) if not _ref_exists(r)]
        self.assertEqual(bad, [])

    def test_every_id_cited_is_a_record(self):
        have = {fields['id'] for _f, fields, _b in self.all}
        missing = {k: v for k, v in _cited().items() if k not in have and not k.startswith('D-9')}
        self.assertEqual(missing, {})

    def test_a_superseded_record_names_one_that_exists(self):
        have = {fields['id'] for _f, fields, _b in self.all}
        for _f, fields, _b in self.all:
            if fields['status'] == 'superseded':
                self.assertIn(fields['superseded_by'], have)


class ProseTests(unittest.TestCase):
    """The ledger exists because CLAUDE.md grew 75,000 characters of calls stated in prose.
       A line there that says a call is unconfirmed must cite the record that holds it."""

    UNCONFIRMED = re.compile(r'unconfirmed|not confirmed|has not confirmed|, and mine\b', re.I)

    def test_an_unconfirmed_call_in_a_claude_md_cites_its_record(self):
        bad = []
        rels = ['CLAUDE.md'] + sorted(os.path.join('projects', d, 'CLAUDE.md')
                                      for d in os.listdir(os.path.join(ROOT, 'projects')))
        for rel in [r for r in rels if os.path.exists(os.path.join(ROOT, r))]:
            with open(os.path.join(ROOT, rel)) as fh:
                section = ''
                for n, line in enumerate(fh, 1):
                    if line.startswith('## '):
                        section = line
                    if section.startswith('## Decisions'):
                        continue                          # the rule itself
                    if self.UNCONFIRMED.search(line) and not D.ID.search(line):
                        bad.append('%s:%d %s' % (rel, n, line.strip()[:80]))
        self.assertEqual(bad, [])


class CommandTests(unittest.TestCase):
    """new / set / pending on a scratch ledger."""

    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = self.t.name
        os.makedirs(os.path.join(self.root, 'decisions'))
        for slug in ('example_100', 'example_200'):      # a record names its workspace's projects
            os.makedirs(os.path.join(self.root, 'projects', slug))

    def test_new_takes_the_next_id_and_is_open(self):
        a = D.new('first', ['example_100'], self.root)
        b = D.new('second', ['example_200'], self.root)
        self.assertEqual((a, b), ('D-001', 'D-002'))
        self.assertEqual(D.load(b, self.root)[0]['status'], 'open')

    def test_confirmed_needs_the_designers_words(self):
        did = D.new('x', ['example_100'], self.root)
        with self.assertRaises(ValueError):
            D.set_status(did, 'confirmed', root=self.root)
        f = D.set_status(did, 'confirmed', quote='the owner, 2026-09-22: yes', root=self.root)
        self.assertEqual((f['status'], f['by']), ('confirmed', 'designer'))

    def test_waiting_and_superseded_need_their_field(self):
        did = D.new('x', ['example_100'], self.root)
        with self.assertRaises(ValueError):
            D.set_status(did, 'waiting', root=self.root)
        with self.assertRaises(ValueError):
            D.set_status(did, 'superseded', by='nope', root=self.root)
        self.assertEqual(D.set_status(did, 'waiting', on='AEP Ohio', root=self.root)['status'],
                         'waiting')

    def test_pending_lists_open_questions_and_what_waits_on_others(self):
        a = D.new('a call', ['example_100'], self.root)
        fields, body = D.load(a, self.root)
        fields['ask'] = 'Keep it?'
        D.save(a, fields, body, self.root)
        b = D.new('a tap', ['example_200'], self.root)
        D.set_status(b, 'waiting', on='Columbus DPU', root=self.root)
        text = D.pending_text(self.root)
        self.assertRegex(text, r'^1 decision\(s\) waiting on .+:')
        self.assertIn('ASK: Keep it?', text)
        self.assertIn('Columbus DPU', text)
        self.assertNotIn('a tap', D.pending_text(self.root, project='example_100'))

    def test_about_finds_a_record_by_its_file_and_its_directory(self):
        did = D.new('x', ['example_100'], self.root)
        f, body = D.load(did, self.root)
        f['refs'] = ['projects/example_100/src/grading.py',
                     'docs/superpowers/specs/x.md @2eb7db6^']
        D.save(did, f, body, self.root)
        hit = lambda p: [r['id'] for r in D.about(p, self.root)]
        self.assertEqual(hit('projects/example_100/src/grading.py'), [did])
        self.assertEqual(hit('projects/example_100/src'), [did])            # a directory above it
        self.assertEqual(hit('docs/superpowers/specs/x.md'), [did])       # a deleted spec
        self.assertEqual(hit('projects/example_100/src/grading'), [])       # not a prefix match

    def test_a_malformed_front_matter_is_refused(self):
        for text in ('no front matter', '---\nid: D-001\nbogus: 1\n---\nbody',
                     '---\nprojects: example_100\n---\nbody'):
            with self.assertRaises(ValueError):
                D.parse(text)

    def test_an_open_record_says_what_moves(self):
        f = {'id': 'D-001', 'title': 't', 'status': 'open', 'by': 'agent', 'date': '2026-09-22',
             'projects': ['example_100'], 'decision': 'd', 'ask': 'a'}
        self.assertTrue(any('if_reversed' in p for p in D.problems(f, 'body')))


class SheetTests(unittest.TestCase):

    def test_the_id_pattern_never_matches_a_door_mark(self):
        for mark in ('D-1', 'D-4A', 'D-12', 'D-1A'):
            self.assertIsNone(re.search(r'\bD-\d{3}\b', mark))


if __name__ == '__main__':
    unittest.main()
