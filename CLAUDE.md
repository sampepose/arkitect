# arkitect -- working notes for agents

The engine: `arkitect/lib/` draws, `arkitect/codes/` holds the code rules, `arkitect/harness/` the tools, `style/` the
house style, `projects/` two examples. README.md is the reference; this is the card.

- **The PDFs are the product.** A change that moves a drawing by a thousandth of a point has
  moved it. `python3 -m arkitect.lib.verify.gate` says which sheets moved and fails until
  `python3 -m arkitect.lib.verify.gate accept` records that you meant it; `--full` adds the tests.
- **Two directories, maybe.** A person's own projects live in a workspace beside the engine
  (projects/, decisions/, arkitect.toml). `arkitect/lib/workspace.py` finds it from the cwd; tools read
  their code from the engine and their projects from the workspace. An ENGINE change is proved
  against a workspace with `python3 -m arkitect.lib.verify.gate --engine-base main --expect-unchanged`
  run inside it. Write every command in the `python3 -m arkitect.lib.verify.gate` form: a path such as
  `arkitect/lib/verify/gate.py` does not exist inside a workspace.
- **Layout.** `arkitect/lib/` knows no code section and no place; `arkitect/codes/` holds each rule with its
  citation and one pin per table in `arkitect/codes/verify/`; `arkitect/harness/` starts, advances, reviews and
  records a project; `projects/<slug>/` is one address.
- **Import, never copy.** A rule a second project needs goes in `arkitect/codes/` or `arkitect/lib/`;
  `arkitect/lib/verify/test_twins.py` fails a definition copied between projects.
- **The house style is `style/house-style.md`.** The plan reviewer reads it.
- **Decisions** among code-legal options are records in the workspace's `decisions/`
  (`python3 -m arkitect.harness.decisions`), confirmed only by the designer of record.
- A new address: `python3 -m arkitect.harness.intake` then `python3 -m arkitect.harness.scaffold`; the next
  sheet: `python3 -m arkitect.harness.progress next <slug>`; a review: `python3 -m arkitect.harness.review`.
- The test command is `python3 -m arkitect.lib.verify.run_tests`: it fails on zero tests collected,
  which both standard runners report as success.
