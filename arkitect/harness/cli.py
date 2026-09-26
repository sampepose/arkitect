"""The one command: `arkitect <tool> [args]`, each tool exactly as `python3 -m <module>` runs it.

    arkitect gate [--full] [--base REF] [--engine-base REF] [--json] ...   every check
    arkitect gate accept | render ...
    arkitect test [-v]                  the test suite (it fails on zero tests collected)
    arkitect trace OUT BUILD [...]      the golden-master trace of one build
    arkitect dxf BUILD [OUT]            a build's floor plans as DXF
    arkitect sheet-text BUILD           strings printed over one another, citations not printed
    arkitect twins [--why]              definitions two projects carry word for word
    arkitect intake | scaffold | progress | review | decisions | config | hooks | hook | engine
    arkitect autoreview <cmd> <slug>    review, fix, repeat until a stop rule holds (docs/autoreview.md)
    arkitect jurisdiction list | check <state>/<city> | new <state>/<city>   the cities encoded, and adding one
    arkitect release check              in your workspace: is the engine fit to publish?
    arkitect web [--port 8765]          the local web UI over this workspace (docs/web-ui.md)
    arkitect disclaimer                 what this engine's output is not
    arkitect --version

The first time a person runs it, `arkitect` shows the disclaimer on stderr, once.

A tool finds its workspace from the directory it is run in (arkitect/lib/workspace.py), so run
it inside the repository that holds your projects/.
"""
import runpy
import sys

TOOLS = {
    'gate': 'arkitect.lib.verify.gate',
    'test': 'arkitect.lib.verify.run_tests',
    'trace': 'arkitect.lib.verify.trace',
    'dxf': 'arkitect.lib.export.dxf',
    'sheet-text': 'arkitect.lib.verify.sheet_text',
    'twins': 'arkitect.lib.verify.twins',
    'intake': 'arkitect.harness.intake',
    'scaffold': 'arkitect.harness.scaffold',
    'progress': 'arkitect.harness.progress',
    'review': 'arkitect.harness.review',
    'autoreview': 'arkitect.harness.autoreview',
    'decisions': 'arkitect.harness.decisions',
    'config': 'arkitect.harness.config',
    'hooks': 'arkitect.harness.hooks',
    'hook': 'arkitect.harness.hook',
    'engine': 'arkitect.harness.engine',
    'disclaimer': 'arkitect.harness.disclaimer',
    'web': 'arkitect.web.server',
    'jurisdiction': 'arkitect.harness.jurisdiction',
    'release': 'arkitect.harness.release',
}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] != ['disclaimer']:
        from arkitect.harness import disclaimer
        disclaimer.first_run()
    if argv[:1] in (['--version'], ['-V']):
        from arkitect import __version__
        print('arkitect', __version__)
        return 0
    if not argv or argv[0] not in TOOLS:
        print(__doc__, file=sys.stderr if argv else sys.stdout)
        return 2 if argv else 0
    module = TOOLS[argv[0]]
    sys.argv = ['arkitect ' + argv[0]] + argv[1:]
    try:
        runpy.run_module(module, run_name='__main__', alter_sys=True)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
