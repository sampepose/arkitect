---
name: new-address
description: Start a permit set for a new address in this repository — ask the intake questions, check the jurisdiction's zoning fit, scaffold projects/<slug>/ so it builds and passes the gate on day one, and hand off the feature list. Use when the designer asks to start, make or add a new project, address, lot or permit set.
---

# Start a new address

You are the INITIALIZER. Your job ends when `projects/<slug>/` exists, passes
`arkitect gate`, and its feature list says what comes next. Drawing the set
is the workers' job (`next-feature`), one feature per session.

Everything below is a command. Do not re-derive what a command tells you.

## 1. Ask what a drawing cannot start without

The questions are `arkitect/harness/intake.py`'s — print them with `arkitect intake questions`,
and once the jurisdiction is known, `arkitect intake questions --jurisdiction <name>` for its
own wording (its county's parcel number, its zoning code's sections). That list is the source,
not this file. Ask the jurisdiction first: every other rule depends on it. Ask them in as few rounds as you can: use AskUserQuestion where the
answer is a choice (corner or interior, alley or not, survey or GIS), plain questions for
figures. The designer of record is `arkitect config get designer.name`. Read
`arkitect config show`: `[defaults] design` holds the designer's defaults, which
apply unless they say otherwise, and `[titleblock] owner` / `contractor` are the owner and
contractor blocks to offer as the default and confirm. Where any of these is empty, ask for
it; never assume one.

The jurisdictions encoded are what `arkitect intake questions` lists (Columbus, Ohio is the
reference). A city not among them is a code-research deliverable, not a flag: say so, point at
docs/jurisdictions.md, and stop -- never draw a set against another city's rules.

## 2. Write the intake and check the fit

Work in a worktree (the repository's rule). Write `projects/<slug>/intake.json` in the shape
of `arkitect/harness/verify/fixtures.py`'s EXAMPLE; the slug is `arkitect.harness.intake.slug_for(address)`.
Coordinates: feet, x from the LEFT side lot line looking from the street, y from the front
lot line toward the rear.

```sh
arkitect intake projects/<slug>/intake.json
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
arkitect scaffold projects/<slug>/intake.json
arkitect gate
arkitect gate render --project <slug> --sheets G-001,C-102
```

The gate must pass. Read both PNGs the render prints — a sheet can pass every assert and
still read badly. A fault in them is a fault in `arkitect/codes/zoning_sheets.py`, or in the jurisdiction's
own words it prints (`arkitect/codes/<name>/__init__.py`), both shared: fix it there and prove every existing project unmoved with
`arkitect gate --base main --expect-unchanged` (every project by default; `--project <slug>` names one).

## 4. Tailor the feature list

`arkitect progress status <slug>`. The catalog is a starting list. Drop a sheet
this set does not need, with the reason (`arkitect.harness.progress drop <slug> <id> --note "..."`);
add one it does (`arkitect.harness.progress add <slug> <id> "<title>" --after <id> --guard <module>`),
e.g. an exterior stair's details sheet. Never edit progress.json by hand — the hooks refuse,
because `set` is what proves a claim.

## 5. Commit and hand off

Commit BY NAME: `intake.json` and every file the scaffold printed (it lists them, including
`.gitignore`, `arkitect/lib/verify/run_tests.py` and `trace.md5`). Then report to the designer:

- the program and the fit — every rule not met and the relief it proceeds on;
- what the intake assumed that they have not confirmed (no survey, parcel TBD, a front line
  taken from a neighbour) — record each with `arkitect decisions new "<title>"
  --project <slug>` (an open record with its question and what moves if they reverse it), and
  cite the ids in the commit;
- the next feature: `arkitect progress next <slug>`.
