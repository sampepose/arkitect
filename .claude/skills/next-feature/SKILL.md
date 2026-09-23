---
name: next-feature
description: Advance a scaffolded project by one feature — take the next item in projects/<slug>/progress.json, draw it on the shared rules in arkitect/codes/ and arkitect/lib/, prove it with the gate, and mark it passes. Use when asked to continue, advance or work on a project that has a progress.json, or to draw its next sheet.
---

# Advance a project by one feature

You are a WORKER. One feature, proved, committed, reported. The session start told you
each project's next feature; if more than one project has a list and the designer did not say
which, ask.

## 1. Take the next feature

```sh
arkitect progress next <slug>
```

It prints the feature, the GUARDS — the shared rule modules that must actually run in this
project's build before it can pass — and where other projects here already draw it. Read
the smallest, newest of them first; `projects/example_100` (interior lot) and
`projects/example_200` (corner lot) show a scaffolded project's shape.

## 2. Build it on the shared layers

- The model goes in `projects/<slug>/src/`, the sheet in `src/sheets/`. Read the project's
  `CLAUDE.md` and the root `CLAUDE.md`'s traps for the area before writing, and
  `arkitect decisions about <path>` for each file you will change: a record there
  is a call already made, and an open one may be reversed by the designer, not by you.
- **Import, never copy.** A rule that cites a section is in `arkitect/codes/`; geometry is in `arkitect/lib/`.
  If what you need exists only inside another project, MOVE it to the shared layer first and
  prove every existing project unmoved:
  `arkitect gate --base main --expect-unchanged` (every project by default; `--project <slug>` names one).
  A copied definition fails `arkitect/lib/verify/test_twins.py` the moment it lands.
- Call every guard from `check_model()` — the probe watches the build run them. A guard
  imported and never called does not count.
- Bind the sheet in `build.py`'s `SHEETS` and add it to `INDEX` so G-001's sheet index lists it.

## 3. Prove it

```sh
arkitect gate                    # every oracle; names the sheets that moved
arkitect gate render --moved     # LOOK at every sheet that moved
arkitect gate accept             # trace.md5, once the move is meant
arkitect progress set <slug> <id> passes
```

`set ... passes` is refused unless the sheet is bound and every guard ran. If it is
refused, the build is missing something — fix the build, never the list. If the feature is
drawn but cannot pass yet (a decision the designer has not made), mark it `drawn` with
`--note "waiting on ..."` and say so.

## 4. Commit and stop

Commit by name, with the "Sheets moved:" line `accept` printed. Report to the designer: what was
drawn, which rules now run, what you decided that they have not confirmed (each recorded with
`arkitect decisions new "<title>" --project <slug>`, and its id in the commit), and
the next feature. Then stop — the next feature is
the next session's.
