# arkitect -- working notes for agents

The engine, installed as the package `arkitect` (`python3 -m pip install -e ".[dev]"`):
`arkitect/lib/` draws, `arkitect/codes/` holds the code rules, `arkitect/harness/` the tools;
beside the package, `style/` the house style, `.claude/` the hooks, skills and agents, and
`projects/` four examples -- two whole sets (`example_300`, `example_400`) and two first-day
scaffolds. README.md is the reference; this is the card.

- **The PDFs are the product.** A change that moves a drawing by a thousandth of a point has
  moved it. `arkitect gate` says which sheets moved and fails until `arkitect gate accept`
  records that you meant it; `--full` adds the tests. Run `arkitect gate --full` before a
  commit; CI runs it on Linux and macOS, Python 3.11 to 3.13.
- **One command.** Every tool is `arkitect <tool>`: gate, test, trace, dxf, sheet-text, twins,
  intake, scaffold, progress, review, decisions, config, hooks, engine, release. Write
  commands that way, never as a path: `arkitect/lib/verify/gate.py` does not exist inside a
  workspace. `arkitect release check`, run inside a private workspace, scans every file the
  engine tracks and every commit message in its history for that workspace's private words
  (authors are exempt) and runs the full gate: the check before the engine is published.
- **Two directories, maybe.** A person's own projects live in a workspace beside the engine
  (projects/, decisions/, arkitect.toml). `arkitect/lib/workspace.py` finds it from the cwd;
  tools read their code from the engine and their projects from the workspace. An ENGINE
  change is proved against a workspace with `arkitect gate --engine-base main
  --expect-unchanged` run inside it.
- **Versions.** `arkitect/__init__.py`'s `__version__`; each `trace.md5` records the engine
  that drew it. Raise the minor number for a change that can move a sheet, the patch number
  otherwise, and tag the release `vX.Y.Z`. A workspace on an older engine sees the upgrade as
  proposed, never applied.
- **`--json` is an interface** (`docs/interface.md`, `arkitect/lib/interface.py`): within a
  schema number add fields, never remove or rename one.
- **Layout.** `arkitect/lib/` knows no code section and no place; `arkitect/codes/` holds each
  rule with its citation and one pin per table in `arkitect/codes/verify/`;
  `arkitect/harness/` starts, advances, reviews and records a project; `projects/<slug>/` is
  one address.
- **Import, never copy.** A rule a second project needs goes in `arkitect/codes/` or
  `arkitect/lib/`; `arkitect/lib/verify/test_twins.py` fails a definition copied between
  projects beyond the workspace's ceiling (`arkitect.toml`).
- **The house style is `style/house-style.md`.** The plan reviewer reads it.
- **Decisions** among code-legal options are records in the workspace's `decisions/`
  (`arkitect decisions`), confirmed only by the designer of record. The engine has none, and
  no engine file may cite a record's id.
- A new address: `arkitect intake` then `arkitect scaffold`; the next sheet:
  `arkitect progress next <slug>`; a review: `arkitect review`.
- The test command is `arkitect test`: it fails on zero tests collected, which both
  standard runners report as success.
