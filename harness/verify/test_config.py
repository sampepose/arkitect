"""harness/config.py: the defaults stand alone, each file overrides the one before, and a
misspelt key or an unknown hook policy is refused rather than ignored."""
import os
import tempfile
import unittest

from harness import config

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ConfigTests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self._tmp.name, 'repo')
        self.home = os.path.join(self._tmp.name, 'home')
        os.makedirs(os.path.join(self.root, 'projects', 'oak_42'))
        os.makedirs(os.path.join(self.home, '.config', 'arkitect'))

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, path, text):
        with open(path, 'w') as fh:
            fh.write(text)

    def load(self, project=None):
        return config.load(project, root=self.root, home=self.home)

    def test_no_file_is_the_defaults(self):
        self.assertEqual(self.load(), config.DEFAULTS)
        self.assertEqual(self.load()['designer']['name'], 'the designer of record')

    def test_user_then_checkout_then_project(self):
        self.write(os.path.join(self.home, '.config', 'arkitect', 'config.toml'),
                   '[designer]\nname = "User"\n[hooks]\nred = "advise"\n')
        self.write(os.path.join(self.root, 'arkitect.toml'), '[designer]\nname = "Checkout"\n')
        self.write(os.path.join(self.root, 'projects', 'oak_42', 'arkitect.toml'),
                   '[titleblock]\nowner = ["OAK LLC"]\n')
        self.assertEqual(self.load()['designer']['name'], 'Checkout')
        self.assertEqual(self.load()['hooks']['red'], 'advise')
        self.assertEqual(self.load()['titleblock']['owner'], [])
        self.assertEqual(self.load('oak_42')['titleblock']['owner'], ['OAK LLC'])

    def test_a_misspelt_key_is_refused(self):
        self.write(os.path.join(self.root, 'arkitect.toml'), '[designer]\nnmae = "x"\n')
        with self.assertRaisesRegex(ValueError, 'unknown setting'):
            self.load()

    def test_an_unknown_policy_is_refused(self):
        self.write(os.path.join(self.root, 'arkitect.toml'), '[hooks]\nred = "sometimes"\n')
        with self.assertRaisesRegex(ValueError, 'must be one of'):
            self.load()

    def test_a_list_must_be_a_list(self):
        self.write(os.path.join(self.root, 'arkitect.toml'), '[titleblock]\nowner = "ONE LINE"\n')
        with self.assertRaisesRegex(ValueError, 'must be a list'):
            self.load()

    def test_the_shipped_example_loads(self):
        with open(os.path.join(HERE, 'arkitect.example.toml')) as fh:
            self.write(os.path.join(self.root, 'arkitect.toml'), fh.read())
        self.assertEqual(self.load()['designer']['name'], 'Jane Doe')


if __name__ == '__main__':
    unittest.main()
