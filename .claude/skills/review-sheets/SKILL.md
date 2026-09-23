---
name: review-sheets
description: Review a project's rendered sheets the way a plan reviewer would — an adversarial reviewer that sees only the images and the house style, a verifier that throws out what the sheets do not bear out, and every surviving finding filed as a task in projects/<slug>/review.json. Use when the designer asks to review, check or critique a set or some sheets, or after a feature changes a sheet.
---

# Review sheets as a plan reviewer would

The generator (whoever drew the sheet) does not grade its own work here. The reviewer sees
only pictures of the sheets and the house style; it has never read the code, so it sees what
the sheet shows instead of what it was meant to show. That is how the worst faults of an
earlier set — headers deeper than their wall, heads across windows, a stack through two
windows — were found, after every rule-based oracle had passed them.

## 1. Prepare

```sh
python3 -m arkitect.harness.review prepare <slug> --sheets A-101,A-102      # or --moved, or every sheet
```

It renders each sheet whole and in overlapping tiles at 200 dpi, writes `brief.md` (with the
house style read live from `style/house-style.md`, config `[style] house`) and `index.json` (every image, and each sheet's
fingerprint as rendered), and prints the directory.

## 2. Review — adversarially, in parallel

Give each `plan-reviewer` agent the review directory and a GROUP of related sheets to read
together, so it can compare them (the plans with their elevations; the P sheets together; the
E and M sheets for one building). Four to six sheets a reviewer. Launch the groups in
parallel. Do not tell a reviewer what the sheets are meant to show or what you think is
wrong; do not give it code. Each returns a JSON array of findings.

If the `plan-reviewer` type is not available in this session, use a general-purpose agent
whose prompt is `.claude/agents/plan-reviewer.md`'s body, and tell it to use only Read and Glob.

## 3. Verify

Concatenate the arrays and give them, with the review directory, to a `finding-verifier`
agent (or a general-purpose agent carrying `.claude/agents/finding-verifier.md`'s body). It
returns every finding with a verdict: CONFIRMED, PLAUSIBLE or REJECTED. Save that array to a
file OUTSIDE the checkout (the job tmp directory).

## 4. File the findings

```sh
python3 -m arkitect.harness.review ingest <slug> <verified.json> --index <review dir>/index.json
```

Each finding becomes R-nnn in `projects/<slug>/review.json` with the sheet's fingerprint;
REJECTED ones are kept as rejected, so the next review is not told the same thing twice, and a
finding that repeats an earlier one is reported as its duplicate, not added. Commit
`review.json` by name.

## 5. Report

To the designer: how many findings, by severity; every blocker and major one in a line each, with its
sheet; how many the verifier rejected. Do not fix anything in this skill — the findings are the
tasks. A worker takes them one at a time:

```sh
python3 -m arkitect.harness.review next <slug>
# fix it, gate, render the sheet and LOOK, then:
python3 -m arkitect.harness.review set <slug> R-nnn fixed      # refused unless that sheet changed
python3 -m arkitect.harness.review set <slug> R-nnn wontfix --note "why"   # the designer's call, not yours
```

A finding that turns on a choice the designer has not made is a decision: record it with
`python3 -m arkitect.harness.decisions new` and mark the finding `wontfix` citing the id until they answer.
