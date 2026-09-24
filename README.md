# arkitect

Residential building permit drawing sets, generated from a model and checked against the
code before a line is drawn. Python and reportlab. There is no CAD file anyone edits by
hand: a project is a model in Python, and the sheets, the schedules and the DXF are its
output.

**Scope.** United States, one- to three-family dwellings in detached buildings, wood-frame on
slab-on-grade, imperial units. One jurisdiction is encoded: Columbus, Ohio. Another city is
a code-research job, not a setting.

**Not professional work.** What this produces is not the work of a licensed architect or
engineer, and a set that passes every check here is not thereby code-compliant: the building
official decides what is. Who may prepare and submit residential drawings is set by your
state. `arkitect` says so the first time you run it, and `arkitect disclaimer` says it again.
The sheets carry no disclaimer; in Ohio the title block states the one thing that is true of
every such set, that no seal is required (ORC 3791.04(A)(2)(b)).

**License.** PolyForm Noncommercial 1.0.0 for the code ([LICENSE](LICENSE)); CC BY-NC 4.0
for the documentation, the house style and the example drawings ([LICENSE-docs](LICENSE-docs)).
[NOTICE](NOTICE) says which paths are under which. A designer or contractor who wants to use
it on paid work may ask the maintainer for a written commercial grant, decided case by case.
Contributions are welcome under a contributor license agreement: [CONTRIBUTING.md](CONTRIBUTING.md)
and [CLA.md](CLA.md).

**Start here:** [docs/quickstart.md](docs/quickstart.md) goes from a clone to a new address
that passes every check. [docs/interface.md](docs/interface.md) is the `--json` a program
reads; [docs/costs.md](docs/costs.md) says what costs model tokens and what is free.

## Install

Python 3.11, 3.12 or 3.13, from a checkout of this repository:

    git clone <this repository> arkitect && cd arkitect
    python3 -m pip install -e ".[dev]"
    arkitect --version

That is an editable install: the checkout IS the engine, and `arkitect` is the one command
for every tool (`arkitect` alone lists them). Install from a checkout, not a wheel: the house
style, the hooks and the examples live beside the package, not inside it.

The pins matter. reportlab's text metrics are load-bearing -- a sheet sizes its type to its
widest line -- so a different reportlab can move a drawn dimension, and every example's
committed digest is the same on every supported Python and platform (CI checks it). Read
`requirements.txt` before bumping anything.

## Try it

Four example projects ship with the engine. Two are whole permit sets, anonymized copies of
real ones drawn with it -- every sheet, every model check, every test -- and two are
scaffolded sets on their first day, the way a new address starts:

    projects/example_300/     300 S Elm Ave: five units in two buildings on a corner lot,
                              27 sheets and a zoning site plan
    projects/example_400/     400 Oak Ave: a house and two stacked ADUs on an interior lot,
                              24 sheets and a zoning site plan
    projects/example_100/     100 Example St, an interior lot: cover sheet, zoning site plan,
                              and the feature list that says what to draw next
    projects/example_200/     200 Example Ave, a corner lot: the same

In the whole sets the names, addresses, parcels, owners and contractors are fictional; the
design and the sheets are the real sets'. Build one to a scratch directory, or look at it:

    arkitect gate render --project example_300 --sheets A-101

    arkitect gate                  # every check, every project, against HEAD
    arkitect progress next example_100                           # what comes next

`gate` is the one command to trust. It builds every project, records every canvas call of
every sheet (the trace), holds each drawing to the digest its project committed
(`trace.md5`), lists printed strings that stand on one another and notes cited but not
printed, runs the DXF exporter and pyflakes, and exits 0 only if every check RAN and
passed (1 failed, 2 could not run). `--full` adds the test suite.

## Your own projects live in a repository of their own

The engine is this repository. Your addresses, their decisions and your settings are yours,
and belong in a second repository beside it -- a **workspace**:

    ~/work/
      arkitect/                the engine (this repository)
      my-projects/             your workspace
        projects/<slug>/       one address: its model, sheets, build.py, deliverables, tests
        decisions/             the calls you make among code-legal options (arkitect.harness.decisions)
        arkitect.toml          who you are and how the tools behave (arkitect.example.toml)

With the engine installed (above), make the workspace and work inside it:

    mkdir -p ../my-projects/projects ../my-projects/decisions
    cp arkitect.example.toml ../my-projects/arkitect.toml
    touch ../my-projects/projects/__init__.py
    cd ../my-projects && git init

Every tool finds its workspace the way git finds a repository: `$ARKITECT_WORKSPACE`, else
the nearest directory at or above where you run it that holds a `projects/`, else the engine
itself (`arkitect/lib/workspace.py`). So the same commands work in both:

    arkitect gate --base main              # a change to a project, against main
    arkitect gate --engine-base main --expect-unchanged
                                                        # a change to the ENGINE: the base is the
                                                        # engine at main, your projects as they are

With the projects outside the engine, the gate's base is two exports -- your workspace at
`--base` and the engine at `--engine-base`, or the engine as it stands -- so a change on
either side is measured against exactly one thing that moved.

## Engine versions: a project never changes unseen

Each project's `trace.md5` records its drawing's digest AND the engine version that drew it
(`<md5> engine=0.1.0`), written by `arkitect gate accept`. When you run a newer engine, the
gate compares:

- **the same drawing:** the gate passes and reports the upgrade as proposed -- "engine 0.1.0
  -> 0.2.0: no sheet moved" -- and `arkitect gate accept` takes it;
- **a sheet moved:** the gate fails, naming the sheets and both versions, until you have looked
  (`arkitect gate render --moved`) and accepted.

The engine's version is `arkitect/__init__.py`'s: the minor number rises for anything that can
move a sheet, the patch number for anything that cannot, and each release is tagged `vX.Y.Z`.

## For programs: `--json`

`arkitect gate`, `progress`, `decisions` and `review` each take `--json` and print one object
whose first keys are `schema`, `kind`, `engine` and `workspace`. Within a schema number a
field may be added, never removed or renamed. `docs/interface.md` lists every field.

## In a browser

    arkitect web                   # inside your workspace; opens http://127.0.0.1:8765/

A local web UI over the same files: the workspace, every sheet rendered with its plan-review
findings pinned on it, the gate with each moved sheet compared against the base, the decisions
waiting on you, and the review. Every button runs the command you would type and commits what
it changes, nothing more. [docs/web-ui.md](docs/web-ui.md).

## A new address

Ask Claude Code for one: the `new-address` skill asks the intake questions, checks the
zoning fit and scaffolds a project that builds and passes the gate on its first day. By
hand, it is:

    arkitect intake projects/<slug>/intake.json     # validate; print the zoning fit
    arkitect scaffold projects/<slug>/intake.json   # write the project
    arkitect progress next <slug>                   # the next sheet, and where it is drawn

The `next-feature` skill draws one feature a session; the `review-sheets` skill puts the
sheets in front of a reviewer that sees only the images. Both run in Claude Code.

## The guard rails, if you want them

    arkitect hooks install     # in the engine, or in your workspace

wires Claude Code hooks that refuse the commands which have produced false greens here (an
oracle with its stderr thrown away, a test runner that collected nothing, a hand-edited
digest), and run the gate when a turn ends. In a workspace it also links the engine's
skills and agents, so a session opened there has the workflows. The policy is
`arkitect.toml`'s `[hooks]` table. Nothing is wired until you run it.

## Layout

    arkitect/lib/          the drawing engine: sheets, plans, geometry, the trace and the gate.
                  Knows no code section and no place.
    arkitect/codes/        the code rules, each with its citation: Ohio's residential code, plumbing,
                  the NEC, Columbus zoning. One pin per transcribed table in arkitect/codes/verify/.
    arkitect/harness/      the tools that start, advance, review and record a project.
    arkitect/web/          the local web UI (`arkitect web`): a page and a JSON API over the tools.
    style/        the house style every sheet is held to; the plan reviewer reads it.
    projects/     the two examples.
    .claude/      the hooks, skills and agents for Claude Code.

**Import, never copy.** A table, a check or a drawing helper a second project needs goes in
`arkitect/codes/` or `arkitect/lib/`, never into one project's model. `arkitect/lib/verify/test_twins.py` fails a
definition copied from one project into another.
