# Quickstart

From nothing to a new address that builds and passes every check, in about ten minutes.
Every command below is run exactly as written, in order, by this repository's own test of
the quickstart (`arkitect/harness/verify/test_quickstart.py`).

## 1. Install the engine

Python 3.11, 3.12 or 3.13, and git.

    git clone <this repository> arkitect
    cd arkitect
    python3 -m pip install -e ".[dev]"
    arkitect --version

The first `arkitect` command shows a short notice once: what the engine's output is not, and
its license. `arkitect disclaimer` shows it again.

## 2. Look at a whole set

Two of the four examples are complete permit sets. Check one, then draw a sheet to look at:

    arkitect gate --project example_300
    arkitect gate render --project example_300 --sheets A-101,S-102 --out ../look

`../look/example_300/A-101.png` is the Building 1 plan; S-102 is its floor framing, with the
header schedule the model derives. `arkitect gate` with no `--project` checks all four.

## 3. Make your workspace

Your projects live in a repository of their own, beside the engine:

    cd ..
    mkdir -p my-projects/projects my-projects/decisions
    cp arkitect/arkitect.example.toml my-projects/arkitect.toml
    touch my-projects/projects/__init__.py
    cd my-projects
    git init -q

Edit `arkitect.toml`: your name in `[designer]`, your company in `[titleblock]`. Every
`arkitect` command run inside `my-projects/` works on it.

## 4. Start an address

An address begins as an `intake.json`: the lot, the buildings, the dwellings, parking, and
any zoning relief you are asking for. Start from an example's:

    mkdir -p projects/oak_42
    cp ../arkitect/projects/example_100/intake.json projects/oak_42/intake.json

Change `"slug"` to `"oak_42"` and `"address"` to `"42 OAK ST"` (and anything else that is
yours), then:

    arkitect intake projects/oak_42/intake.json       # valid? does the program fit the zoning?
    arkitect scaffold projects/oak_42/intake.json     # write the project

`intake` prints every zoning rule the program is held to, with its section. A rule not met
with no relief named exits 2: redesign, or name the relief in `"relief"`.

`scaffold` writes a project that builds and passes the gate today -- a cover sheet and a zoning
site plan drawn from the massing -- and its feature list, the sheets still to draw:

    arkitect gate
    git add projects/oak_42 arkitect.toml
    git commit -qm "42 Oak St: day one"
    arkitect progress next oak_42

`progress next` names the next sheet, the shared rules that must run before it counts as done,
and where the examples draw the same sheet.

## 5. Draw it with Claude Code

The sheets are drawn by an agent, one feature a session, each held to the gate. Wire the
engine's hooks and skills into your workspace once:

    arkitect hooks install

Then open Claude Code in `my-projects/` and ask it to draw the next sheet of oak_42 (the
`next-feature` skill), or to review the set (`review-sheets`). A decision it makes among
code-legal options is recorded for you to confirm (`arkitect decisions pending`); nothing it
learns on one project changes another until you accept it.

## Where next

- `README.md` -- what the engine is and how its parts fit
- `docs/interface.md` -- the `--json` a program reads
- `docs/costs.md` -- what costs model tokens and what is free
