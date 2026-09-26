"""arkitect/harness/autoreview.py: the program is parsed strictly, a round is frozen once and
ingested once, an attempt is kept only on the close check's word and never by deleting what a
finding was about, and the stop rules read the log -- all in a scratch repository with a
scratch cache, the renderer and the gate stood in for."""
import json
import os
import subprocess
import tempfile
import unittest
from unittest import mock

from arkitect.harness import autoreview as A
from arkitect.harness import review as R
from arkitect.harness import decisions as D

SHEETS = ['G-001', 'A-101', 'A-102', 'C-101', 'S-101', 'P-101', 'E-101']


def finding(sheet='A-101', severity='major', text='The D-1 swing crosses the range.', **more):
    f = {'sheet': sheet, 'where': 'tile r1c1', 'category': 'fit', 'severity': severity,
         'finding': text, 'evidence': 'two arcs meet', 'suggest': 'swing it the other way',
         'verdict': 'CONFIRMED', 'verdict_reason': 'visible'}
    f.update(more)
    return f


def fake_prepare(slug, sheets=None, moved=False, out=None, root=None, known_list=None, base='HEAD'):
    os.makedirs(out, exist_ok=True)
    idx = {'project': slug, 'commit': 'abc1234',
           'sheets': {s: {'whole': os.path.join(out, s, 'whole.png'), 'tiles': [], 'md5': 'm-' + s}
                      for s in sheets}}
    with open(os.path.join(out, 'index.json'), 'w') as fh:
        json.dump(idx, fh)
    with open(os.path.join(out, 'brief.md'), 'w') as fh:
        fh.write(known_list or '')
    return out


class Base(unittest.TestCase):

    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = os.path.join(t.name, 'ws')
        os.makedirs(os.path.join(self.root, 'projects', 'demo'))
        os.makedirs(os.path.join(self.root, 'decisions'))
        env = mock.patch.dict(os.environ, {'XDG_CACHE_HOME': os.path.join(t.name, 'cache')})
        env.start()
        self.addCleanup(env.stop)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 't@example.com')
        self.git('config', 'user.name', 'T')
        A.init('demo', self.root, sheets=SHEETS)
        self.git('add', '--', 'projects/demo/autoreview.md')
        self.git('commit', '-q', '-m', 'program')

    def git(self, *args):
        return subprocess.run(['git'] + list(args), cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def index(self):
        return {'commit': 'abc1234', 'sheets': {s: {'md5': 'm-' + s} for s in SHEETS}}

    def ingest(self, *fs):
        return R.ingest('demo', list(fs), self.index(), self.root)

    def program(self, **keys):
        p = A.program_path('demo', self.root)
        with open(p) as fh:
            text = fh.read()
        for k, v in keys.items():
            text = text.replace('\n%s: %s\n' % (k, A.KEYS[k]), '\n%s: %s\n' % (k, v))
        with open(p, 'w') as fh:
            fh.write(text)

    def freeze_and_verify(self, *verified):
        meta = A.freeze('demo', self.root, prepare=fake_prepare)
        for i, t in enumerate(meta['tasks']):
            with open(t['verified'], 'w') as fh:
                json.dump(list(verified) if i == 0 else [], fh)
        return meta


class ProgramTests(Base):

    def test_init_writes_a_program_that_parses_with_every_sheet_grouped(self):
        prog = A.program('demo', self.root)
        self.assertEqual(sorted(s for _g, ss in prog['groups'] for s in ss), sorted(SHEETS))
        self.assertEqual(dict(prog['groups'])['architectural'], ['A-101', 'A-102'])
        self.assertEqual(prog['severities'], ('blocker', 'major', 'minor'))
        self.assertFalse(prog['stop'])
        self.assertIn('## Design calls', prog['body'])

    def test_a_group_is_never_more_than_six_sheets(self):
        groups = A.default_groups(['A-%d' % i for i in range(100, 113)])
        self.assertEqual([len(ss) for _g, ss in groups], [6, 6, 1])
        self.assertEqual([g for g, _s in groups], ['architectural-1', 'architectural-2', 'architectural-3'])

    def test_an_unknown_key_or_value_is_refused(self):
        good = A.TEMPLATE.format(keys='reviewer: opus', groups='group a: A-101', slug='demo')
        self.assertEqual(A.parse_program(good)['groups'], [('a', ['A-101'])])
        for bad in ('reviwer: opus', 'engine: sometimes', 'rounds: many', 'severities: major, fatal'):
            with self.assertRaises(ValueError, msg=bad):
                A.parse_program(good.replace('reviewer: opus', bad))

    def test_stop_on_a_line_of_its_own_stops(self):
        with open(A.program_path('demo', self.root), 'a') as fh:
            fh.write('\nSTOP\n')
        self.assertTrue(A.program('demo', self.root)['stop'])
        self.assertTrue(next(r for r in A.stop_rules('demo', self.root) if r['rule'] == 'designer')['holds'])

    def test_init_backfills_the_rounds_a_project_had_before(self):
        root = os.path.join(os.path.dirname(self.root), 'other')
        os.makedirs(os.path.join(root, 'projects', 'demo'))
        R.ingest('demo', [finding(), finding(sheet='C-101', severity='minor', text='x y z')],
                 self.index(), root)
        R.ingest('demo', [finding(text='A new one entirely, on the stair.')],
                 dict(self.index(), commit='def5678'), root)
        A.init('demo', root, sheets=SHEETS)
        rows = A.rounds('demo', root)
        self.assertEqual([(r['round'], r['commit'], r['new_major'], r['new_minor']) for r in rows],
                         [('1', 'abc1234', '1', '1'), ('2', 'def5678', '1', '0')])


class RoundTests(Base):

    def test_a_round_is_frozen_once_and_ingested_once(self):
        meta = self.freeze_and_verify(finding(), finding(sheet='C-101', severity='minor', text='a b c'),
                                      finding(sheet='G-001', text='Wrong title.', verdict='REJECTED'))
        self.assertEqual(A.freeze('demo', self.root, prepare=fake_prepare)['round'], meta['round'])
        row, added, dups = A.ingest_round('demo', self.root)
        self.assertEqual((row['new_major'], row['new_minor'], row['rejected'], row['duplicates']),
                         (1, 1, 1, 0))
        self.assertEqual(row['majors'], 'R-001')
        with self.assertRaises(ValueError):
            A.ingest_round('demo', self.root)
        self.assertEqual(A.freeze('demo', self.root, prepare=fake_prepare)['round'], meta['round'] + 1)

    def test_ingest_waits_for_every_group(self):
        meta = A.freeze('demo', self.root, prepare=fake_prepare)
        with open(meta['tasks'][0]['verified'], 'w') as fh:
            json.dump([], fh)
        with self.assertRaises(ValueError) as cm:
            A.ingest_round('demo', self.root)
        self.assertIn(meta['tasks'][1]['group'], str(cm.exception))

    def test_every_task_names_its_sheets_and_where_its_replies_go(self):
        meta = A.freeze('demo', self.root, prepare=fake_prepare)
        t = meta['tasks'][0]
        self.assertIn(', '.join(t['sheets']), t['reviewer'])
        self.assertIn(t['raw'], t['verifier'])
        self.assertTrue(t['verified'].startswith(meta['dir']))
        self.assertFalse(meta['dir'].startswith(self.root))              # outside the checkout

    def test_a_waiting_finding_reopens_when_its_decision_is_confirmed(self):
        self.ingest(finding())
        R.set_status('demo', 'R-001', 'waiting', note='D-901', root=self.root)
        fields = dict(id='D-901', title='Keep it', status='open', by='agent', date='2026-09-01',
                      projects=['demo'], decision='Kept.', ask='Keep it?')
        D.save('D-901', fields, 'account', root=self.root)
        self.assertEqual(A.freeze('demo', self.root, prepare=fake_prepare)['reopened'], [])
        self.assertEqual(R.load('demo', self.root)['findings'][0]['status'], 'waiting')
        for t in A.current_round('demo', self.root)[1]['tasks']:
            with open(t['verified'], 'w') as fh:
                json.dump([], fh)
        A.ingest_round('demo', self.root)
        D.save('D-901', dict(fields, status='confirmed', confirmed='yes'), 'account', root=self.root)
        self.assertEqual(A.freeze('demo', self.root, prepare=fake_prepare)['reopened'], ['R-001'])
        self.assertEqual(R.load('demo', self.root)['findings'][0]['status'], 'open')

    def test_the_known_list_goes_in_the_brief_unless_the_program_says_off(self):
        meta = A.freeze('demo', self.root, prepare=fake_prepare)
        with open(os.path.join(meta['render'], 'brief.md')) as fh:
            self.assertIn('Already raised and settled', fh.read())


class AttemptTests(Base):

    def setUp(self):
        super().setUp()
        self.ingest(finding(), finding(text='The A-101 range hood misses its duct.', severity='minor'),
                    finding(sheet='P-101', severity='blocker', text='The stack crosses a window.'),
                    finding(sheet='C-101', text='The walk ends at the lawn.', severity='minor'))

    def test_the_worst_finding_comes_first_with_the_others_on_its_sheet(self):
        a = A.next_attempt('demo', self.root)
        self.assertEqual(a['findings'], ['R-003'])
        A.next_attempt('demo', self.root, claim=True)
        self.assertEqual(A.next_attempt('demo', self.root)['findings'], ['R-001', 'R-002'])

    def test_a_group_attempt_takes_the_groups_findings_up_to_the_batch(self):
        self.program(batch='1')
        a = A.next_attempt('demo', self.root, group='architectural', claim=True)
        self.assertEqual((a['findings'], a['name']), (['R-001'], 'r0-architectural'))
        b = A.next_attempt('demo', self.root, group='architectural', claim=True)
        self.assertEqual((b['findings'], b['name']), (['R-002'], 'r0-architectural-2'))
        with self.assertRaises(ValueError):
            A.next_attempt('demo', self.root, group='nonesuch')

    def test_the_brief_carries_the_findings_the_program_and_the_rules(self):
        a = A.next_attempt('demo', self.root, group='architectural', claim=True)
        with open(a['brief']) as fh:
            text = fh.read()
        for s in ('R-001', 'R-002', 'swing it the other way', '## Design calls', 'UNCOMMITTED',
                  'Do not edit the engine', a['branch'], a['tree']):
            self.assertIn(s, text)

    def test_a_program_of_majors_leaves_the_minors(self):
        self.program(severities='blocker, major')
        self.assertEqual([f['id'] for f in A.queue('demo', self.root)], ['R-003', 'R-001'])

    def attempt(self, **close):
        a = A.next_attempt('demo', self.root, group='architectural', claim=True)
        rec = dict({'gate_ok': True, 'failures': [], 'moved': ['A-101'], 'others_moved': {},
                    'vocab_lost': []}, **close)
        d = os.path.join(A.state_dir('demo', self.root), 'attempts', a['name'])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'close.json'), 'w') as fh:
            json.dump(rec, fh)
        return a

    def test_keep_needs_a_resolved_finding_and_no_removal(self):
        a = self.attempt()
        j = A.judge('demo', a['name'], [{'id': 'R-001', 'verdict': 'RESOLVED', 'reason': 'gone'},
                                        {'id': 'R-002', 'verdict': 'NOT RESOLVED', 'reason': 'still'}],
                    self.root)
        self.assertTrue(j['keep'])
        self.assertEqual((j['resolved'], j['open']), (['R-001'], ['R-002']))
        j = A.judge('demo', a['name'], [{'id': 'R-001', 'verdict': 'RESOLVED BY REMOVAL', 'reason': 'cut'},
                                        {'id': 'R-002', 'verdict': 'RESOLVED', 'reason': 'ok'}], self.root)
        self.assertFalse(j['keep'])
        self.assertIn('resolved by removal: R-001', j['why'])

    def test_resolved_on_a_sheet_that_did_not_move_is_not_resolved(self):
        self.ingest(finding(sheet='C-101', text='The C-101 walk is short.'))
        A._save_claims('demo', {}, self.root)
        self.program(batch='9')
        a = A.next_attempt('demo', self.root, claim=True)          # R-003 on P-101 comes first
        A._save_claims('demo', {}, self.root)
        a = A.next_attempt('demo', self.root, group='architectural', claim=True)
        a['findings'].append('R-005')                             # a finding off the moved sheet
        A._save_claims('demo', {a['name']: a}, self.root)
        d = os.path.join(A.state_dir('demo', self.root), 'attempts', a['name'])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'close.json'), 'w') as fh:
            json.dump({'gate_ok': True, 'failures': [], 'moved': ['A-101'], 'others_moved': {},
                       'vocab_lost': []}, fh)
        j = A.judge('demo', a['name'], [{'id': 'R-001', 'verdict': 'RESOLVED', 'reason': 'ok'},
                                        {'id': 'R-005', 'verdict': 'RESOLVED', 'reason': 'ok'}], self.root)
        self.assertEqual(j['resolved'], ['R-001'])
        self.assertEqual(j['reasons']['R-005'], 'C-101 did not move')

    def test_a_red_gate_another_project_moved_or_no_sheet_moved_discards(self):
        for close, words in (({'gate_ok': False, 'failures': ['tests failed']}, 'gate is red'),
                             ({'others_moved': {'other': ['A-101']}}, 'another project moved'),
                             ({'moved': []}, 'no sheet moved')):
            A._save_claims('demo', {}, self.root)          # each case a fresh attempt
            a = self.attempt(**close)
            j = A.judge('demo', a['name'], [{'id': 'R-001', 'verdict': 'RESOLVED', 'reason': 'x'}], self.root)
            self.assertFalse(j['keep'])
            self.assertTrue(any(words in w for w in j['why']), j['why'])

    def test_a_verdict_on_a_finding_the_attempt_did_not_take_is_refused(self):
        a = self.attempt()
        with self.assertRaises(ValueError):
            A.judge('demo', a['name'], [{'id': 'R-004', 'verdict': 'RESOLVED'}], self.root)
        with self.assertRaises(ValueError):
            A.judge('demo', a['name'], [{'id': 'R-001', 'verdict': 'FINE'}], self.root)

    def test_a_discard_is_logged_and_twice_takes_the_finding_off_the_queue(self):
        for n in range(2):
            a = self.attempt()
            A.judge('demo', a['name'], [{'id': 'R-001', 'verdict': 'NOT RESOLVED', 'reason': 'still there'},
                                        {'id': 'R-002', 'verdict': 'NOT RESOLVED', 'reason': 'no'}], self.root)
            rows = A.record('demo', a['name'], self.root)
            self.assertEqual({r['outcome'] for r in rows}, {'discarded'})
        self.assertNotIn('R-001', [f['id'] for f in A.queue('demo', self.root)])
        self.assertEqual(R.load('demo', self.root)['findings'][0]['status'], 'open')
        with open(A.next_attempt('demo', self.root, claim=True)['brief']) as fh:
            self.assertNotIn('an earlier attempt', fh.read())       # R-003, never tried

    def test_keep_is_recorded_only_once_its_branch_is_merged(self):
        a = self.attempt()
        A.judge('demo', a['name'], [
            {'id': 'R-001', 'verdict': 'RESOLVED', 'reason': 'the swing is reversed'},
            {'id': 'R-002', 'verdict': 'NOT RESOLVED', 'reason': 'hood unchanged'},
            dict(finding(text='The reversed swing now hits the fridge.'), id='NEW')], self.root)
        self.git('branch', a['branch'])
        self.git('checkout', '-q', a['branch'])
        with open(os.path.join(self.root, 'projects', 'demo', 'x.py'), 'w') as fh:
            fh.write('x = 1\n')
        self.git('add', '--', 'projects/demo/x.py')
        self.git('commit', '-q', '-m', 'fix')
        self.git('checkout', '-q', 'main')
        with self.assertRaises(ValueError):
            A.record('demo', a['name'], self.root)
        self.git('merge', '-q', '--ff-only', a['branch'])
        with mock.patch.object(R, 'fingerprints', return_value={s: 'moved' for s in SHEETS}):
            rows = A.record('demo', a['name'], self.root)
        self.assertEqual([(r['finding'], r['outcome']) for r in rows],
                         [('R-001', 'kept'), ('R-002', 'discarded')])
        found = {f['id']: f for f in R.load('demo', self.root)['findings']}
        self.assertEqual((found['R-001']['status'], found['R-002']['status']), ('fixed', 'open'))
        self.assertEqual(found['R-005']['finding'], 'The reversed swing now hits the fridge.')
        self.assertNotIn(a['name'], A._live_claims('demo', self.root))

    def test_waiting_findings_are_set_waiting_with_the_note(self):
        a = A.next_attempt('demo', self.root, group='architectural', claim=True)
        rows = A.record('demo', a['name'], self.root, waiting=['R-001', 'R-002'], note='D-901')
        self.assertEqual({r['outcome'] for r in rows}, {'waiting'})
        self.assertEqual(R.load('demo', self.root)['findings'][0]['status'], 'waiting')

    def test_close_writes_the_brief_for_the_sheets_that_moved(self):
        a = A.next_attempt('demo', self.root, group='architectural', claim=True)
        rep = {'ok': True, 'failures': [], 'projects': {
            'demo': {'sheets_moved': [{'sheet': 'A-101'}], 'vocab_lost': ['R302.1']},
            'other': {'sheets_moved': []}}}
        rec = A.close('demo', a['name'], self.root, gate_run=lambda base: rep, prepare=fake_prepare)
        self.assertEqual((rec['moved'], rec['others_moved'], rec['vocab_lost']), (['A-101'], {}, ['R302.1']))
        with open(rec['brief']) as fh:
            text = fh.read()
        self.assertIn('R302.1', text)
        self.assertIn('The D-1 swing crosses the range.', text)
        self.assertIn('RESOLVED BY REMOVAL', text)


class StopTests(Base):

    def rows(self, majors):
        for n, m in enumerate(majors, len(A.rounds('demo', self.root)) + 1):
            A.append_tsv(os.path.join(A.log_dir('demo', self.root), 'rounds.tsv'), A.ROUND_COLS,
                         [{'round': n, 'new_blocker': 0, 'new_major': m, 'new_minor': 5, 'rejected': 0,
                           'majors': ''}])

    def holds(self, rule):
        return next(r for r in A.stop_rules('demo', self.root) if r['rule'] == rule)['holds']

    def test_converged_after_two_quiet_rounds(self):
        self.rows([5, 3, 0])
        self.assertFalse(self.holds('converged'))
        self.rows([0])
        self.assertTrue(self.holds('converged'))

    def test_a_major_waiting_on_the_designer_does_not_hold_the_loop_open(self):
        self.ingest(finding())
        R.set_status('demo', 'R-001', 'waiting', note='D-901', root=self.root)
        for n in (1, 2):
            A.append_tsv(os.path.join(A.log_dir('demo', self.root), 'rounds.tsv'), A.ROUND_COLS,
                         [{'round': n, 'new_blocker': 0, 'new_major': 1, 'new_minor': 0,
                           'rejected': 0, 'majors': 'R-001'}])
        self.assertTrue(self.holds('converged'))

    def test_the_noise_floor_is_three_rounds_with_no_new_low(self):
        self.rows([9, 8, 7, 6, 5, 4, 5, 5, 5])        # means 8 7 6 5 4.7 4.7 5 ...
        self.assertFalse(self.holds('noise floor'))
        self.rows([6, 6, 6])
        self.assertTrue(self.holds('noise floor'))

    def test_the_budget_counts_this_runs_rounds_and_its_hours(self):
        self.rows([5, 5])
        with open(os.path.join(A.state_dir('demo', self.root), 'run.json'), 'w') as fh:
            json.dump({'branch': 'b', 'started': '2026-01-01T00:00:00', 'first_round': 2}, fh)
        self.program(rounds='2')
        self.assertFalse(self.holds('budget'))
        self.rows([5])
        self.assertTrue(self.holds('budget'))
        self.program(rounds='9', hours='1')
        self.assertTrue(self.holds('budget'))                      # 2026-01-01 is long ago

    def test_a_round_is_refused_once_a_rule_holds_unless_forced(self):
        A.stop('demo', 'enough', self.root)
        with self.assertRaises(ValueError):
            A.freeze('demo', self.root, prepare=fake_prepare)
        self.assertEqual(A.freeze('demo', self.root, force=True, prepare=fake_prepare)['round'], 1)

    def test_the_chart_draws_both_lines(self):
        self.rows([5, 3, 1])
        html = A.chart('demo', self.root)
        self.assertEqual(html.count('<polyline'), 2)
        self.assertIn('prefers-color-scheme:dark', html)

    def test_status_reads_everything_without_a_build(self):
        self.rows([5])
        st = A.status('demo', self.root)
        self.assertEqual((st['round'], st['queue'], len(st['rounds'])), (0, 0, 1))
        self.assertIn('stop rule', A.status_text(st))


class PlaceTests(Base):

    def test_every_worktree_of_one_repository_shares_one_state(self):
        tree = os.path.join(self.root, '.claude', 'worktrees', 'x')
        self.git('worktree', 'add', '-q', tree, '-b', 'x')
        self.assertEqual(A.state_dir('demo', tree), A.state_dir('demo', self.root))
        self.assertEqual(os.path.realpath(A.main_checkout(tree)), os.path.realpath(self.root))

    def test_begin_makes_the_integration_worktree_and_resumes_it(self):
        import datetime
        run = A.begin('demo', self.root, today=datetime.date(2026, 9, 26))
        self.assertEqual(run['branch'], 'autoreview/demo-20260926')
        self.assertTrue(os.path.isdir(run['worktree']))
        self.assertEqual(A.begin('demo', self.root)['started'], run['started'])

    def test_land_runs_only_on_main_in_the_main_checkout(self):
        run = {'branch': 'autoreview/demo-1', 'worktree': '', 'started': '2026-01-01T00:00:00'}
        tree = os.path.join(self.root, '.claude', 'worktrees', 'y')
        self.git('worktree', 'add', '-q', tree, '-b', 'y')
        with self.assertRaises(ValueError):
            A.land('demo', tree, push=False, run=run)
        self.git('checkout', '-q', '-b', 'side')
        with self.assertRaises(ValueError):
            A.land('demo', self.root, push=False, run=run)


if __name__ == '__main__':
    unittest.main()
