# arkitect

Residential building permit drawing sets, generated from a model and checked against the
code before a line is drawn. Python and reportlab. There is no CAD file anyone edits by
hand: a project is a model in Python, and the sheets, the schedules and the DXF are its
output.

**Scope.** United States, one- to three-family dwellings in detached buildings, wood-frame on
slab-on-grade, imperial units. One jurisdiction is encoded: Columbus, Ohio. Another city is
a code-research job, not a setting.

**Not professional work.** What this produces is not the work of a licensed architect or
engineer, and a set that passes every check here is not thereby code-compliant. Who may
prepare and submit residential drawings is set by your state; the plan reviewer decides.

**License.** PolyForm Noncommercial 1.0.0 for the code and CC BY-NC 4.0 for the
documentation. Commercial use needs written permission; ask the maintainer.

## Install

Python 3.12 (the sets are built and issued on 3.12.4) and the pinned packages:

    python3 -m pip install -r requirements.txt

The pins matter. reportlab's text metrics are load-bearing -- a sheet sizes its type to its
widest line -- so a different reportlab can move a drawn dimension. Read
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

Make the engine importable from anywhere once, then work inside the workspace:

    cd arkitect && arkitect engine link        # one line in your site-packages
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
    style/        the house style every sheet is held to; the plan reviewer reads it.
    projects/     the two examples.
    .claude/      the hooks, skills and agents for Claude Code.

**Import, never copy.** A table, a check or a drawing helper a second project needs goes in
`arkitect/codes/` or `arkitect/lib/`, never into one project's model. `arkitect/lib/verify/test_twins.py` fails a
definition copied from one project into another.
