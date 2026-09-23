"""arkitect/lib/ is the drawing engine. It may not know which jurisdiction it is drawing for.

Five live strings named Ohio or NEC sections -- RCO 314, RCO 315, NEC 406.9,
NEC 110.26(A), RCO M1305.1 -- and one named a project's output file. A second
project in another city would have printed them on its first build, and a second
project in the SAME city would still have had arkitect/lib/ telling one project's story.

Docstrings are exempt. A docstring saying "RCO 307.1 wants 15 inches" explains why the
code is shaped as it is; a live string prints or asserts.
"""
import ast
import os
import re
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LIB = os.path.join(HERE, 'arkitect', 'lib')

CITATION = re.compile(r'\b(RCO|OPC|NEC|IRC|C\.C\.|ORC|CIC-)\s*[\dA-Z]')
PLACE = re.compile(r'\b(COLUMBUS|OHIO)\b', re.I)   # a project's own names: arkitect/harness/verify/test_identity.py


def live_strings(path):
    """Every string literal in a file that is not a docstring, with its line number."""
    tree = ast.parse(open(path).read())
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                docs.add(id(first.value))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in docs):
            yield node.lineno, node.value


def lib_files():
    for dirpath, dirnames, files in os.walk(LIB):
        dirnames[:] = [d for d in dirnames if d != '__pycache__' and d != 'verify']
        for f in sorted(files):
            if f.endswith('.py'):
                yield os.path.join(dirpath, f)


class NeutralityTests(unittest.TestCase):

    def test_lib_files_were_found(self):
        """Guards the two tests below from passing by scanning nothing."""
        self.assertGreater(len(list(lib_files())), 10)

    def test_no_code_citation_prints_from_lib(self):
        bad = []
        for path in lib_files():
            for lineno, value in live_strings(path):
                if CITATION.search(value):
                    bad.append('%s:%d %r' % (os.path.relpath(path, HERE), lineno,
                                             value[:70]))
        self.assertEqual(bad, [], 'arkitect/lib/ names a code section in a live string')

    def test_no_project_assembly_is_a_name_in_lib(self):
        """A wall type, a unit or a sheet of ONE project is not an identifier here. W4 was:
           lib defined its stud rows and drew them, and a project with no party wall carried them."""
        mark = re.compile(r'(^|_)(W[1-9][A-Z]?|U\d{1,2}|UNIT_?\d)(_|$)')
        bad = []
        for path in lib_files():
            for node in ast.walk(ast.parse(open(path).read())):
                for name in (getattr(node, 'id', None), getattr(node, 'attr', None), getattr(node, 'arg', None),
                             getattr(node, 'name', None)):
                    if isinstance(name, str) and mark.search(name):
                        bad.append('%s:%d %s' % (os.path.relpath(path, HERE), getattr(node, 'lineno', 0), name))
        self.assertEqual(sorted(set(bad)), [], 'arkitect/lib/ names one project\'s assembly or unit')

    def test_no_project_name_appears_in_lib(self):
        bad = []
        for path in lib_files():
            for lineno, value in live_strings(path):
                if PLACE.search(value):
                    bad.append('%s:%d %r' % (os.path.relpath(path, HERE), lineno,
                                             value[:70]))
        self.assertEqual(bad, [], 'arkitect/lib/ names this project in a live string')


def _layer(module):
    """The layer a module name belongs to: arkitect.codes.ohio -> codes, src.x -> src."""
    parts = module.split('.')
    return parts[1] if parts[0] == 'arkitect' and len(parts) > 1 else parts[0]


class LayeringTests(unittest.TestCase):
    """The import rule, enforced rather than trusted. arkitect/lib/ imports nothing above it;
       arkitect/codes/ imports arkitect/lib/ only. If a sheet ever imports the tool that generates it,
       the layering has inverted and this says so."""

    def imports(self, root):
        out = []
        for dirpath, dirnames, files in os.walk(os.path.join(HERE, root)):
            dirnames[:] = [d for d in dirnames if d != '__pycache__']
            for f in sorted(files):
                if not f.endswith('.py'):
                    continue
                path = os.path.join(dirpath, f)
                rel = os.path.relpath(path, HERE)
                if rel.startswith(os.path.join('arkitect', 'lib', 'verify')):
                    continue          # tests may import what they test
                for node in ast.walk(ast.parse(open(path).read())):
                    if isinstance(node, ast.Import):
                        for a in node.names:
                            out.append((rel, node.lineno, a.name))
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        out.append((rel, node.lineno, node.module))
        return out

    def test_lib_imports_nothing_above_it(self):
        # 'src' is included: a project's own package is literally named `src` (see
        # projects/<slug>/src), and arkitect/lib/ never sits two directories below a project
        # the way a project's build.py does, so it can never legitimately resolve one.
        # Without this, `from src import sitework` in a arkitect/lib/ module would slip through.
        bad = [(f, n, m) for f, n, m in self.imports(os.path.join('arkitect', 'lib'))
               if _layer(m) in ('codes', 'harness', 'projects', 'src')]
        self.assertEqual(bad, [], 'arkitect/lib/ imports a layer above it')

    def test_codes_imports_only_lib(self):
        # 'projects' is forbidden everywhere in arkitect/codes/, verify/ included -- nothing in this
        # layer has a reason to import one. 'src' is different:
        # arkitect/codes/verify/test_zoning_rules.py's `from src import sitework` is legitimate,
        # because a test IS the place that checks a rule's consumption against a real
        # project's model. Production code in arkitect/codes/ has no such reason -- it is not a
        # test and cannot know which project's `src` it would even be resolving -- so
        # 'src' is forbidden everywhere in arkitect/codes/ EXCEPT arkitect/codes/verify/.
        codes_verify = os.path.join('arkitect', 'codes', 'verify') + os.sep
        if not os.path.isdir(os.path.join(HERE, 'arkitect', 'codes')):
            self.fail('arkitect/codes/ does not exist yet')
        bad = []
        for f, n, m in self.imports(os.path.join('arkitect', 'codes')):
            top = _layer(m)
            if top == 'projects':
                bad.append((f, n, m))
            elif top == 'src' and not f.startswith(codes_verify):
                bad.append((f, n, m))
        self.assertEqual(bad, [], 'arkitect/codes/ imports a layer above it')



if __name__ == '__main__':
    unittest.main()
