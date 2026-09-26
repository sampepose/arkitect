"""Tests for the Claude Code hooks in .claude/hooks/.

They live here, not beside the hooks, because arkitect/lib/verify/run_tests.py skips every
dot-directory -- it has to, .claude/worktrees holds whole checkouts -- so a test under
.claude/ would never be collected, which is the failure run_tests.py exists to prevent.

Every rule is held to a command it must refuse AND one it must let through: a guard that
refuses too much gets switched off, and then it guards nothing.
"""
import importlib.util, json, os, subprocess, sys, unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HOOKS = os.path.join(HERE, '.claude', 'hooks')


def _load(name):
    sys.path.insert(0, HOOKS)
    spec = importlib.util.spec_from_file_location('hook_' + name, os.path.join(HOOKS, name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MAIN = '/Users/x/repo'
WORKTREE = '/Users/x/repo/.claude/worktrees/some-job'


class GuardBashTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.g = _load('guard_bash')

    def refuses(self, command, root=MAIN):
        self.assertIsNotNone(self.g.check(command, root), 'should refuse: %r' % command)

    def allows(self, command, root=MAIN):
        why = self.g.check(command, root)
        self.assertIsNone(why, 'should allow: %r\n%s' % (command, why))

    def test_git_add_all(self):
        for c in ('git add -A', 'git add .', 'git add --all', 'git add -u', 'git add -Av',
                  'cd x && git add -A && git commit -m x'):
            self.refuses(c)
        self.allows('git add arkitect/lib/verify/gate.py arkitect/lib/verify/test_gate.py')
        self.allows('git add projects/oak_42/trace.md5')

    def test_git_commit_all(self):
        for c in ('git commit -a -m x', 'git commit -am x', 'git commit --all'):
            self.refuses(c)
        for c in ('git commit -m x', 'git commit -q -m x', 'git commit --amend --no-edit',
                  'git commit -F msg.txt'):
            self.allows(c)

    def test_words_inside_a_message_are_not_commands(self):
        self.allows('git commit -q -m "never git add -A here"')
        self.allows("git add a.py && git commit -F - <<'EOF'\nwhy not git add -A\nEOF")
        self.allows("git commit -m 'python3 arkitect/lib/export/dxf.py >/dev/null 2>&1 && echo x'")

    def test_test_runners_that_pass_on_nothing(self):
        for c in ('python3 -m pytest lib', 'pytest -k grading',
                  "python3 -m unittest discover -s arkitect/lib/verify -p 'tests_*.py'"):
            self.refuses(c)
        for c in ('python3 arkitect/lib/verify/run_tests.py', 'python3 -m unittest arkitect.lib.verify.test_gate'):
            self.allows(c)

    def test_an_oracles_stderr_is_never_discarded(self):
        for c in ('python3 arkitect/lib/export/dxf.py >/dev/null 2>&1 && echo rebuilt',
                  'python3 arkitect/lib/verify/trace.py t.txt 2>/dev/null',
                  'python3 projects/oak_42/build.py &>/dev/null'):
            self.refuses(c)
        self.allows('python3 arkitect/lib/verify/gate.py > /tmp/gate.txt')      # stdout only
        self.allows('ls lib 2>/dev/null')                             # not an oracle

    def test_an_oracles_exit_status_is_never_masked(self):
        for c in ('python3 arkitect/lib/verify/gate.py || true', 'python3 arkitect/lib/verify/run_tests.py && echo ok'):
            self.refuses(c)
        self.allows('python3 arkitect/lib/verify/gate.py; echo "exit $?"')
        self.allows('python3 arkitect/lib/verify/gate.py && git add x')

    def test_a_worktree_does_not_rewrite_the_deliverables(self):
        self.refuses('python3 projects/oak_42/build.py', WORKTREE)
        self.refuses('python3 arkitect/lib/export/dxf.py projects/elm_7/build.py', WORKTREE)
        self.allows('python3 arkitect/lib/export/dxf.py projects/elm_7/build.py /tmp/x.dxf', WORKTREE)
        self.allows('python3 arkitect/lib/verify/trace.py /tmp/t.txt projects/oak_42/build.py', WORKTREE)
        self.allows('python3 arkitect/lib/verify/gate.py render --sheets A-101', WORKTREE)
        self.allows('python3 projects/oak_42/build.py', MAIN)      # the merger rebuilds

    def test_trace_md5_is_written_by_accept_alone(self):
        for c in ('echo abc > projects/oak_42/trace.md5',
                  'md5 -q t.txt >projects/elm_7/trace.md5',
                  'cp /tmp/d projects/oak_42/trace.md5',
                  "sed -i '' 's/a/b/' projects/oak_42/trace.md5",
                  'md5 -q t.txt | tee projects/oak_42/trace.md5'):
            self.refuses(c)
        for c in ('cat projects/oak_42/trace.md5', 'grep -rn trace.md5 lib',
                  'git checkout -- projects/oak_42/trace.md5',
                  'git add projects/oak_42/trace.md5',
                  'python3 arkitect/lib/verify/gate.py accept'):
            self.allows(c)

    def test_progress_json_is_written_by_its_tool_alone(self):
        for c in ('echo {} > projects/oak_42/progress.json',
                  "sed -i '' 's/pending/passes/' projects/oak_42/progress.json",
                  'cp /tmp/p.json projects/oak_42/progress.json'):
            self.refuses(c)
        for c in ('cat projects/oak_42/progress.json',
                  'arkitect progress set oak_42 A-101 passes',
                  'git add projects/oak_42/progress.json'):
            self.allows(c)

    def test_the_hook_exits_2_with_its_reason_on_stderr(self):
        data = json.dumps({'tool_name': 'Bash', 'tool_input': {'command': 'git add -A'},
                           'cwd': HERE})
        r = subprocess.run([sys.executable, os.path.join(HOOKS, 'guard_bash.py')],
                           input=data, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn('BY NAME', r.stderr)
        ok = json.dumps({'tool_name': 'Bash', 'tool_input': {'command': 'git status'}, 'cwd': HERE})
        r = subprocess.run([sys.executable, os.path.join(HOOKS, 'guard_bash.py')],
                           input=ok, capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stderr), (0, ''))


class GuardWriteTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.g = _load('guard_write')

    def test_trace_md5_anywhere(self):
        self.assertIsNotNone(self.g.check(MAIN + '/projects/oak_42/trace.md5', MAIN))
        self.assertIsNotNone(self.g.check(WORKTREE + '/projects/elm_7/trace.md5', WORKTREE))

    def test_a_deliverable_inside_the_checkout(self):
        self.assertIsNotNone(self.g.check(MAIN + '/projects/oak_42/42-N-Oak-permit-set.pdf', MAIN))
        self.assertIsNotNone(self.g.check(MAIN + '/projects/elm_7/7-Elm-floor-plans.dxf', MAIN))
        self.assertIsNotNone(self.g.check(MAIN + '/projects/oak_42/42-N-Oak-zoning-site-plan.pdf', MAIN))

    def test_progress_json_inside_the_checkout(self):
        self.assertIsNotNone(self.g.check(MAIN + '/projects/oak_42/progress.json', MAIN))
        self.assertIsNone(self.g.check('/tmp/progress.json', MAIN))           # not a project's

    def test_the_autoreview_logs_inside_the_checkout(self):
        for name in ('rounds.tsv', 'attempts.tsv'):
            self.assertIsNotNone(self.g.check(MAIN + '/projects/oak_42/autoreview/' + name, MAIN))
        self.assertIsNone(self.g.check(MAIN + '/projects/oak_42/autoreview.md', MAIN))  # the designer's

    def test_everything_else(self):
        self.assertIsNone(self.g.check(MAIN + '/projects/oak_42/src/stairs.py', MAIN))
        self.assertIsNone(self.g.check('/tmp/render/A-101.pdf', MAIN))          # outside
        self.assertIsNone(self.g.check(MAIN + '/lib/verify/test_trace.py', MAIN))

    def test_the_hook_exits_2_with_its_reason_on_stderr(self):
        data = json.dumps({'tool_name': 'Edit', 'cwd': HERE, 'tool_input': {
            'file_path': os.path.join(HERE, 'projects', 'oak_42', 'trace.md5')}})
        r = subprocess.run([sys.executable, os.path.join(HOOKS, 'guard_write.py')],
                           input=data, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn('arkitect gate accept', r.stderr)


def _report(ok=True, moved=None, failures=()):
    moved = [] if moved is None else moved
    return {'ok': ok, 'failures': list(failures), 'errors': [],
            'projects': {'oak_42': {'sheets_moved': [{'sheet': s} for s in moved]},
                         'elm_7': {'sheets_moved': []}}}


class StopGateTests(unittest.TestCase):
    """decide() is the policy. These hold option C -- the designer's own, set in their
       arkitect.toml -- and one test holds the default a new installation gets."""

    @classmethod
    def setUpClass(cls):
        cls.s = _load('stop_gate')

    OPTION_C = {'green_uncommitted': 'block', 'red': 'block-unattended'}

    def decide(self, paths, report, attended=True, worktree=False, blocks=0, rules=None):
        return self.s.decide(paths, report, attended, worktree, blocks,
                             dict(self.OPTION_C, **(rules or {})))

    def test_a_new_installation_is_advised_never_blocked(self):
        """The default, for someone who has just installed the hooks: every problem shown,
           no turn held."""
        self.assertEqual(self.s.DEFAULT_POLICY, {'green_uncommitted': 'advise', 'red': 'advise'})
        red = _report(ok=False, failures=['oak_42: the build failed'])
        for report in (_report(), red):
            for attended in (True, False):
                self.assertEqual(self.s.decide(['arkitect/lib/x.py'], report, attended, False, 0)[0],
                                 'advise')

    def test_nothing_changed_ends_the_turn(self):
        self.assertEqual(self.decide([], None), ('allow', ''))

    def test_green_and_uncommitted_blocks_everywhere(self):
        for attended in (True, False):
            action, msg = self.decide(['projects/oak_42/src/stairs.py'],
                                      _report(moved=['A-604']), attended=attended)
            self.assertEqual(action, 'block')
            self.assertIn('Sheets moved: oak_42 A-604', msg)
            self.assertIn('BY NAME', msg)

    def test_red_blocks_only_an_unattended_session(self):
        red = _report(ok=False, failures=['oak_42: the build failed'])
        self.assertEqual(self.decide(['arkitect/lib/x.py'], red, attended=False)[0], 'block')
        action, msg = self.decide(['arkitect/lib/x.py'], red, attended=True)
        self.assertEqual(action, 'advise')
        self.assertIn('the build failed', msg)

    def test_a_worktrees_deliverables_are_restored_not_committed(self):
        action, msg = self.decide(['projects/oak_42/42-N-Oak-permit-set.pdf'],
                                  _report(moved=['A-101']), worktree=True)
        self.assertEqual(action, 'block')
        self.assertIn('git checkout --', msg)

    def test_a_timestamp_only_pdf_is_restored_in_the_main_checkout(self):
        action, msg = self.decide(['projects/elm_7/7-Elm-permit-set.pdf'], _report())
        self.assertEqual(action, 'block')
        self.assertIn('timestamp', msg)

    def test_a_pdf_whose_drawing_moved_is_committed_in_the_main_checkout(self):
        action, msg = self.decide(['projects/oak_42/42-N-Oak-permit-set.pdf',
                                   'projects/oak_42/trace.md5'], _report(moved=['C-101']))
        self.assertEqual(action, 'block')
        self.assertIn('Commit them now', msg)

    def test_three_blocks_in_a_row_let_the_turn_end(self):
        action, msg = self.decide(['arkitect/lib/x.py'], _report(), blocks=3)
        self.assertEqual(action, 'advise')
        self.assertIn('3 blocks in a row', msg)

    def test_a_checkout_without_the_gate_is_left_alone(self):
        self.assertEqual(self.decide(['arkitect/lib/x.py'], None)[0], 'allow')

    # The [hooks] policy (arkitect/harness/config.py) overrides the defaults one key at a time.

    def test_red_block_blocks_even_an_attended_session(self):
        red = _report(ok=False, failures=['oak_42: the build failed'])
        action, msg = self.decide(['arkitect/lib/x.py'], red, attended=True, rules={'red': 'block'})
        self.assertEqual(action, 'block')
        self.assertIn('the build failed', msg)

    def test_red_advise_advises_even_an_unattended_session(self):
        red = _report(ok=False, failures=['oak_42: the build failed'])
        action, msg = self.decide(['arkitect/lib/x.py'], red, attended=False, rules={'red': 'advise'})
        self.assertEqual(action, 'advise')
        self.assertIn('the build failed', msg)

    def test_red_off_lets_the_turn_end(self):
        red = _report(ok=False, failures=['oak_42: the build failed'])
        for attended in (True, False):
            self.assertEqual(self.decide(['arkitect/lib/x.py'], red, attended=attended,
                                         rules={'red': 'off'}), ('allow', ''))

    def test_green_uncommitted_advise_shows_the_commit_message(self):
        for attended in (True, False):
            action, msg = self.decide(['projects/oak_42/src/stairs.py'], _report(moved=['A-604']),
                                      attended=attended, rules={'green_uncommitted': 'advise'})
            self.assertEqual(action, 'advise')
            self.assertIn('Sheets moved: oak_42 A-604', msg)

    def test_green_uncommitted_off_lets_the_turn_end(self):
        self.assertEqual(self.decide(['arkitect/lib/x.py'], _report(),
                                     rules={'green_uncommitted': 'off'}), ('allow', ''))

    def test_one_rule_leaves_the_other_at_its_default(self):
        red = _report(ok=False, failures=['oak_42: the build failed'])
        rules = {'green_uncommitted': 'off'}
        self.assertEqual(self.decide(['arkitect/lib/x.py'], red, attended=False, rules=rules)[0], 'block')
        self.assertEqual(self.decide(['arkitect/lib/x.py'], red, attended=True, rules=rules)[0], 'advise')


class SettingsTests(unittest.TestCase):
    """.claude/hooks/settings.template.json wires the hooks (arkitect hooks
       install). A hook it names that does not exist would be skipped in silence by the
       command's own `[ -f ]` guard, so check it here."""
    TEMPLATE = os.path.join(HOOKS, 'settings.template.json')

    def test_every_wired_hook_exists_and_every_hook_is_wired(self):
        with open(self.TEMPLATE) as fh:
            cfg = json.load(fh)['hooks']
        wired = set()
        for groups in cfg.values():
            for group in groups:
                for h in group['hooks']:
                    name = h['command'].split('/.claude/hooks/')[1].split('"')[0]
                    self.assertTrue(os.path.isfile(os.path.join(HOOKS, name)), name)
                    wired.add(name)
        hooks = {f for f in os.listdir(HOOKS) if f.endswith('.py') and f != 'hooklib.py'}
        self.assertEqual(wired, hooks)

    def test_an_installed_checkout_is_not_out_of_date(self):
        if not os.path.exists(os.path.join(HERE, '.claude', 'settings.json')):
            self.skipTest('hooks not installed here')
        sys.path.insert(0, HERE)
        from arkitect.harness import hooks
        self.assertIn(hooks.status(HERE), ('installed', 'not installed'),
                      'arkitect hooks install')

    def test_a_block_reaches_claude_through_the_wrapper(self):
        with open(self.TEMPLATE) as fh:
            cmd = json.load(fh)['hooks']['PreToolUse'][0]['hooks'][0]['command']
        r = subprocess.run(['sh', '-c', cmd], cwd=HERE, capture_output=True, text=True,
                           input=json.dumps({'tool_input': {'command': 'git add -A'}, 'cwd': HERE}))
        self.assertEqual(r.returncode, 2, r.stderr)


class SessionStartTests(unittest.TestCase):

    def test_each_feature_list_is_the_handoff(self):
        import tempfile
        s = _load('session_start')
        with tempfile.TemporaryDirectory() as root:
            proj = os.path.join(root, 'projects', 'oak_42')
            os.makedirs(proj)
            os.makedirs(os.path.join(root, 'projects', 'no_list'))
            with open(os.path.join(proj, 'progress.json'), 'w') as fh:
                json.dump({'features': [
                    {'id': 'G-001', 'title': 'COVER', 'status': 'passes'},
                    {'id': 'A-101', 'title': 'PLANS', 'status': 'pending'}]}, fh)
            lines = s.progress_lines(root)
        self.assertEqual(len(lines), 1)
        self.assertIn('oak_42: 1 of 2 features pass; next A-101 PLANS', lines[0])


class HookLibTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.h = _load('hooklib')

    def test_segments_pair_each_command_with_the_operator_after_it(self):
        self.assertEqual(self.h.segments('a && b || c; d | e'),
                         [('a', '&&'), ('b', '||'), ('c', ';'), ('d', '|'), ('e', '')])

    def test_a_redirection_stays_with_its_command(self):
        self.assertEqual(self.h.segments('a >/dev/null 2>&1 && b'),
                         [('a >/dev/null 2>&1', '&&'), ('b', '')])

    def test_unattended(self):
        self.assertTrue(self.h.unattended({'CLAUDE_CODE_SESSION_ATTENDED': '0'}, MAIN))
        self.assertTrue(self.h.unattended({'CLAUDE_JOB_DIR': '/j'}, MAIN))
        self.assertTrue(self.h.unattended({}, WORKTREE))
        self.assertFalse(self.h.unattended({}, MAIN))
        self.assertFalse(self.h.unattended({'CLAUDE_CODE_SESSION_ATTENDED': '1'}, MAIN))


if __name__ == '__main__':
    unittest.main()
