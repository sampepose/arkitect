"""The skills in .claude/skills/ are procedures made of commands. A command renamed or a
flag dropped would leave a skill telling the next agent to run something that does not
exist, and nothing else reads a SKILL.md. These hold every command a skill names to the
code it names."""
import os
import re
import unittest

from arkitect.harness import progress

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SKILLS = os.path.join(ROOT, '.claude', 'skills')


def skills():
    for name in sorted(os.listdir(SKILLS)):
        with open(os.path.join(SKILLS, name, 'SKILL.md')) as fh:
            yield name, fh.read()


class SkillTests(unittest.TestCase):

    def test_the_skills_exist_and_name_themselves(self):
        found = dict(skills())
        self.assertEqual(sorted(found), ['autoreview', 'new-address', 'next-feature', 'review-sheets'])
        for name, text in found.items():
            head = text.split('---')[1]
            self.assertIn('name: %s' % name, head)
            self.assertRegex(head, r'description: \S')

    def test_every_harness_module_named_exists(self):
        for name, text in skills():
            for mod in set(re.findall(r'python3 -m (harness\.\w+)', text)):
                self.assertTrue(os.path.exists(os.path.join(ROOT, *mod.split('.')) + '.py'),
                                '%s names %s' % (name, mod))

    def test_every_progress_subcommand_named_exists(self):
        with open(os.path.join(ROOT, 'arkitect', 'harness', 'progress.py')) as fh:
            src = fh.read()
        for name, text in skills():
            for sub in set(re.findall(r'harness\.progress (\w+)', text)):
                self.assertIn("'%s'" % sub, src, '%s names progress %s' % (name, sub))
        self.assertTrue(progress.STATUSES)

    def test_every_review_subcommand_and_agent_named_exists(self):
        with open(os.path.join(ROOT, 'arkitect', 'harness', 'review.py')) as fh:
            src = fh.read()
        agents = os.path.join(ROOT, '.claude', 'agents')
        for name, text in skills():
            for sub in set(re.findall(r'(?:harness\.review|arkitect review) (\w+)', text)):
                self.assertIn("'%s'" % sub, src, '%s names review %s' % (name, sub))
            for agent in set(re.findall(r'`(plan-reviewer|finding-verifier|close-checker)`', text)):
                self.assertTrue(os.path.exists(os.path.join(agents, agent + '.md')), agent)

    def test_every_autoreview_subcommand_named_exists(self):
        from arkitect.harness import autoreview
        with open(os.path.join(ROOT, 'arkitect', 'harness', 'autoreview.py')) as fh:
            src = fh.read()
        named = set()
        for name, text in skills():
            for sub in re.findall(r'arkitect autoreview (\w+)', text):
                named.add(sub)
                self.assertIn("'%s'" % sub, src, '%s names autoreview %s' % (name, sub))
        self.assertIn('land', named)
        self.assertTrue(autoreview.KEYS)

    def test_the_review_agents_cannot_read_the_code_or_change_anything(self):
        for agent in ('plan-reviewer', 'finding-verifier', 'close-checker'):
            with open(os.path.join(ROOT, '.claude', 'agents', agent + '.md')) as fh:
                head = fh.read().split('---')[1]
            self.assertIn('name: %s' % agent, head)
            self.assertIn('tools: Read, Glob\n', head)          # no shell, no edits, no grep

    def test_every_gate_flag_named_exists(self):
        with open(os.path.join(ROOT, 'arkitect', 'lib', 'verify', 'gate.py')) as fh:
            src = fh.read()
        for name, text in skills():
            for line in re.findall(r'arkitect/lib/verify/gate\.py([^`\n]*)', text):
                for flag in re.findall(r'--[a-z-]+', line):
                    self.assertIn("'%s'" % flag, src, '%s names gate %s' % (name, flag))
                for sub in re.findall(r'^\s*(render|accept)\b', line):
                    self.assertIn("['%s']" % sub, src)


if __name__ == '__main__':
    unittest.main()
