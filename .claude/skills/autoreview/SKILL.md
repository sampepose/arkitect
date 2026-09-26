---
name: autoreview
description: Run a project's plan review as a loop that does not wait to be asked — freeze a round, review and verify it, fix the findings in parallel attempts each judged by a close check from the re-rendered sheets, integrate what is kept, and start the next round, until a stop rule holds. Use when the designer asks for autoreview, for review rounds to run on their own or overnight, or to "keep reviewing and fixing" a set.
---

# autoreview: review, fix, repeat

You are the LEAD. The loop is autoresearch's: attempts are judged by a fixed evaluator, kept
or thrown away, every one logged, and the designer steers only through
`projects/<slug>/autoreview.md`, which you read again every round and never edit. docs/autoreview.md
is the reference; this is the procedure. **Do not stop to ask.** A question goes to the
decisions ledger and the finding waits; the loop works on something else. You stop only when
`arkitect autoreview status` says a stop rule holds.

All state is on disk, so you can be a fresh session: start every session with

```sh
arkitect autoreview status <slug>
```

and pick up at the stage it names.

## 0. Once per run

```sh
arkitect autoreview init <slug>       # if there is no autoreview.md yet; tell the designer it exists
arkitect autoreview begin <slug>      # the integration branch autoreview/<slug>-<date>, in its worktree
```

Work from the worktree `begin` prints. Every command below runs there unless it says otherwise.

## 1. Freeze a round

```sh
arkitect autoreview round <slug> --json
```

It renders every grouped sheet, writes the brief (with the known list), reopens the waiting
findings whose decisions were answered, and gives each group its `reviewer` and `verifier`
prompts and the paths their replies go to. It refuses once a stop rule holds.

## 2. Review and verify, as a pipeline

For each task, launch a `plan-reviewer` agent with its `reviewer` prompt, on the program's
`reviewer` model, all groups in parallel. As EACH reviewer returns, save its reply and launch
that group's `finding-verifier` on the `verifier` model at once; do not wait for the others:

```sh
arkitect review parse <reply or the agent's transcript .jsonl> --out <task raw path>
arkitect review parse <verifier reply or transcript> --out <task verified path>
```

Never tell a reviewer what you think is wrong, or give it code or a finding.

## 3. Ingest

```sh
arkitect autoreview ingest <slug>
```

Commit `projects/<slug>/review.json` and `projects/<slug>/autoreview/rounds.tsv` by name. Then
publish the trend: `arkitect autoreview chart <slug>` writes the page; republish the same
artifact every round so the designer's link stays one link.

## 4. Attempts, in parallel

Up to the program's `parallel_attempts` at once. For each discipline with open findings:

```sh
arkitect autoreview next <slug> --group <group> --claim
```

Launch a general-purpose agent on the program's `fixer` model whose prompt is: "Read <brief>
and follow it exactly." The brief holds the worktree command, the rules and the findings. As
each fixer reports:

1. Read its report. Record each CALL line as an OPEN decision (`arkitect decisions new`, then
   write the record); a NEEDS DESIGNER finding waits (step 5). An ENGINE REQUEST stays in the
   finding's next attempt unless the program says `engine: allow`.
2. In the fixer's worktree: `arkitect autoreview close <slug> <attempt>`. It gates the branch
   against the integration branch and renders what moved with a close brief.
3. Launch a `close-checker` agent (verifier model) on the close brief. It has not seen the fix;
   do not tell it anything about it.
4. `arkitect review parse <its reply> --out <file>` then
   `arkitect autoreview judge <slug> <attempt> <file>`: KEEP or DISCARD, and why.

## 5. Integrate and record

On the integration worktree, for a KEEP: `git merge --no-ff <branch>`. If it conflicts
(two attempts touched one file), DISCARD the later one instead (`git merge --abort`); the next round will
find the finding again. For a DISCARD: `git worktree remove --force <tree>` and
`git branch -D <branch>`. Then, KEEP or DISCARD:

```sh
arkitect autoreview record <slug> <attempt>
arkitect autoreview record <slug> <attempt> --waiting R-nnn,R-mmm --note "D-nnn"   # NEEDS DESIGNER ones
```

After the round's merges: `arkitect gate accept --project <slug>` once, `arkitect gate --full`,
and commit trace.md5, review.json and attempts.tsv by name, the message naming the sheets that
moved. A red gate here that one repair attempt does not fix: `arkitect autoreview stop <slug>
--reason "broken: ..."` and report.

When the queue is empty or every attempt is recorded, go to 1.

## 6. When a stop rule holds

Report to the designer, in a few lines: the rounds this run and the trend (new majors a round),
what was kept and discarded, every finding waiting on them (and `arkitect decisions pending`),
and the one command that lands the work, which is theirs to run in the main checkout:

```sh
arkitect autoreview land <slug>
```

Never merge the integration branch into main yourself, and never push it there.

## Carry a gap to another project

When a kept fix closes a gap another project in the workspace plainly shares (grep its
vocabulary there), do not fix it in this run: this run moves one project. Say so in the round
report, and the designer runs a review of that project.
