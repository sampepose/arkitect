---
name: new-address
description: Start a permit set for a new address in this repository — ask the intake questions, check the Columbus zoning fit, scaffold projects/<slug>/ so it builds and passes the gate on day one, and hand off the feature list. Use when the designer asks to start, make or add a new project, address, lot or permit set.
---

# Start a new address

You are the INITIALIZER. Your job ends when `projects/<slug>/` exists, passes
`python3 -m arkitect.lib.verify.gate`, and its feature list says what comes next. Drawing the set
is the workers' job (`next-feature`), one feature per session.

Everything below is a command. Do not re-derive what a command tells you.

## 1. Ask what a drawing cannot start without

The questions are `arkitect/harness/intake.py`'s `QUESTIONS` — read them there; that list is the
source, not this file. Ask them in as few rounds as you can: use AskUserQuestion where the
answer is a choice (corner or interior, alley or not, survey or GIS), plain questions for
figures. The designer of record is `python3 -m arkitect.harness.config get designer.name`. Read
`python3 -m arkitect.harness.config show`: `[defaults] design` holds the designer's defaults, which
apply unless they say otherwise, and `[titleblock] owner` / `contractor` are the owner and
contractor blocks to offer as the default and confirm. Where any of these is empty, ask for
it; never assume one.

Only Columbus is encoded (`arkitect/codes/columbus/__init__.py`). Another city is a code-research
deliverable, not a flag: say so and stop.

## 2. Write the intake and check the fit

Work in a worktree (the repository's rule). Write `projects/<slug>/intake.json` in the shape
of `arkitect/harness/verify/fixtures.py`'s EXAMPLE; the slug is `arkitect.harness.intake.slug_for(address)`.
Coordinates: feet, x from the LEFT side lot line looking from the street, y from the front
lot line toward the rear.

```sh
python3 -m arkitect.harness.intake projects/<slug>/intake.json
```

- **exit 1** — the intake is invalid; every problem is listed. Fix it, or ask.
- **exit 2** — valid, but the program does not fit: the listed rules are not met and state
  no relief. **This is the designer's decision, never yours.** Put it to them: redesign the
  massing (say what change clears it), or proceed on stated relief ("VARIANCE REQUESTED", as
  `projects/example_200/intake.json` states it, or a basis such as "BY THE LOT SPLIT OF ...").
  Record their choice in `relief`. Never invent relief
  to make the command pass.
- **exit 0** — it fits. Rows marked SECTION UNVERIFIED hold the program to a figure whose
  section nobody has confirmed; say which in your report.

## 3. Scaffold, then look

```sh
python3 -m arkitect.harness.scaffold projects/<slug>/intake.json
python3 -m arkitect.lib.verify.gate
python3 -m arkitect.lib.verify.gate render --project <slug> --sheets G-001,C-102
```

The gate must pass. Read both PNGs the render prints — a sheet can pass every assert and
still read badly. A fault in them is a fault in `arkitect/codes/columbus/zoning_sheets.py`, which is
shared: fix it there and prove every existing project unmoved with
`python3 -m arkitect.lib.verify.gate --base main --expect-unchanged` (every project by default; `--project <slug>` names one).

## 4. Tailor the feature list

`python3 -m arkitect.harness.progress status <slug>`. The catalog is a starting list. Drop a sheet
this set does not need, with the reason (`arkitect.harness.progress drop <slug> <id> --note "..."`);
add one it does (`arkitect.harness.progress add <slug> <id> "<title>" --after <id> --guard <module>`),
e.g. an exterior stair's details sheet. Never edit progress.json by hand — the hooks refuse,
because `set` is what proves a claim.

## 5. Commit and hand off

Commit BY NAME: `intake.json` and every file the scaffold printed (it lists them, including
`.gitignore`, `arkitect/lib/verify/run_tests.py` and `trace.md5`). Then report to the designer:

- the program and the fit — every rule not met and the relief it proceeds on;
- what the intake assumed that they have not confirmed (no survey, parcel TBD, a front line
  taken from a neighbour) — record each with `python3 -m arkitect.harness.decisions new "<title>"
  --project <slug>` (an open record with its question and what moves if they reverse it), and
  cite the ids in the commit;
- the next feature: `python3 -m arkitect.harness.progress next <slug>`.
