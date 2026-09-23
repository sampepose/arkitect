"""docs/quickstart.md runs as written: every command in its code blocks from step 2 on, in order,
in a scratch directory -- so the document cannot drift from the tools it describes."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DOC = os.path.join(HERE, 'docs', 'quickstart.md')

# What a person does by hand between two commands, as the prose asks: keyed by the command it
# follows. Nothing else is added to the document's commands.
BY_HAND = {
    'cp ../arkitect/projects/example_100/intake.json projects/oak_42/intake.json':
        "sed -i.bak -e 's/\"example_100\"/\"oak_42\"/' -e 's/100 EXAMPLE ST/42 OAK ST/' "
        "projects/oak_42/intake.json && rm projects/oak_42/intake.json.bak",
}


def commands(text):
    """The document's commands, step 2 onwards: every line of an indented code block."""
    body = text.split('## 2.', 1)[1]
    out = []
    for block in re.findall(r'(?:^    \S.*\n)+', body, re.M):
        for ln in block.splitlines():
            ln = re.sub(r'\s+#.*$', '', ln.strip())
            if ln:
                out.append(ln)
    return out


@unittest.skipUnless(shutil.which('git') and shutil.which('bash'), 'needs git and bash')
class QuickstartTests(unittest.TestCase):

    def test_the_quickstart_runs_as_written(self):
        with open(DOC) as fh:
            cmds = commands(fh.read())
        self.assertIn('arkitect scaffold projects/oak_42/intake.json', cmds)
        script = ['set -e', 'arkitect() { "%s" -m arkitect.harness.cli "$@"; }' % sys.executable]
        for c in cmds:
            script.append(c)
            if c in BY_HAND:
                script.append(BY_HAND[c])
        t = tempfile.mkdtemp(prefix='quickstart-')
        self.addCleanup(shutil.rmtree, t, True)
        # "git clone ... arkitect && cd arkitect": a real copy of the working tree, never a link --
        # a process started in a linked directory resolves `..` beside the link's TARGET, and
        # the quickstart's `../look` and `cd ..` would write next to this checkout
        engine = os.path.join(t, 'arkitect')
        shutil.copytree(HERE, engine, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '.verify-cache', '*.egg-info', 'build', '*.pdf', '*.dxf'))
        os.makedirs(os.path.join(t, 'home'))
        env = dict(os.environ, HOME=os.path.join(t, 'home'), PYTHONPATH=engine,
                   GIT_AUTHOR_NAME='q', GIT_AUTHOR_EMAIL='q@example.com',
                   GIT_COMMITTER_NAME='q', GIT_COMMITTER_EMAIL='q@example.com')
        env.pop('ARKITECT_WORKSPACE', None)
        r = subprocess.run(['bash', '-c', '\n'.join(script)], cwd=engine,
                           capture_output=True, text=True, env=env, timeout=900)
        self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-3000:])
        ws = os.path.join(t, 'my-projects')
        self.assertTrue(os.path.exists(os.path.join(t, 'look', 'example_300', 'A-101.png')))
        self.assertTrue(os.path.exists(os.path.join(ws, 'projects', 'oak_42', 'trace.md5')))
        self.assertIn('NEXT:', r.stdout)                            # progress next printed
        self.assertTrue(os.path.islink(os.path.join(ws, '.claude', 'skills')))


if __name__ == '__main__':
    unittest.main()
