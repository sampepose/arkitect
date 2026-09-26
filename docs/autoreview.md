# autoreview: review, fix, repeat

    arkitect autoreview init <slug>        # projects/<slug>/autoreview.md, the program you steer with
    # then, in a Claude Code session -- a background one is the point:  "run autoreview on <slug>"
    arkitect autoreview status <slug>      # where the loop is, what it kept, what waits on you
    arkitect autoreview land <slug>        # in the main checkout: fast-forward main, rebuild, push

A plan review finds faults; a fix round closes them; the next review finds what is left. Run
by hand, that loop needs the designer to say "fix them" and "one more round" every time.
autoreview runs it until a stop rule says the set is done. It is modelled on
karpathy/autoresearch: an agent edits, a fixed evaluator scores each attempt, a better one is
kept and a worse one reset, every attempt is a line in a log, and the human steers only
through a program file. It never stops to ask.

## What carries over, and what cannot

| autoresearch | autoreview |
|---|---|
| `train.py`, the one file the agent edits | `projects/<slug>/`, less what an attempt may not touch (below). The engine is read-only by default. |
| `prepare.py` + `val_bpb`, a fixed evaluator | **the frozen review**: `review prepare`'s tiles, the brief, the house style, the known list, the reviewer and verifier models, captured when a round is frozen and unchanged until it is ingested |
| a 5-minute budget per experiment | `attempt_minutes` per attempt; past it the fixer commits what is green and reports the rest open |
| keep if `val_bpb` fell, else `git reset` | keep an attempt only if the **close check** says so (`judge`); else its branch is deleted and the reason logged |
| `program.md`, which the human edits | `projects/<slug>/autoreview.md`, which the designer edits, read again at every round |
| `results.tsv` | `projects/<slug>/autoreview/attempts.tsv` (a row per finding an attempt took) and `rounds.tsv` (a row per round, the chart's data) |
| branch `autoresearch/<tag>` | branch `autoreview/<slug>-<date>`, never main; `land` brings it to main when the designer runs it |
| NEVER STOP | stops on a stop rule, never to ask: a question goes to the decisions ledger, its finding waits, the loop works on something else |

**The one real difference is the metric.** `val_bpb` is precise enough to judge one
experiment. A plan review is not: one set, fixed after every round, drew 2 to 9 confirmed
majors a round for eleven rounds running -- a stochastic instrument good to about ±3. So the
two jobs autoresearch gives one number are split:

- **An attempt is judged locally**, by the close check on the sheets it moved. That test is
  sharp, and it is the keep rule.
- **A round is judged globally**, by the frozen review. That number is noisy, and it decides
  only **when to stop**.

## The two loops

```
ROUND n  (outer)                                   arkitect autoreview ...
  1  freeze     read the program; reopen answered findings; render,
                brief, known list; a reviewer + verifier task per group   round
  2  review     one plan-reviewer per group, in parallel, Read + Glob only
  3  verify     one finding-verifier per group, as its reviewer returns    (review parse --out)
  4  ingest     into review.json, duplicates closed; a rounds.tsv row     ingest
  5  attempts   the inner loop, parallel_attempts at a time
  6  integrate  kept branches merged; gate accept once; gate --full
  7  stop?      the stop rules; if none holds, round n+1                  status

ATTEMPT  (inner)
  a  take       a group's open findings (up to `batch`), or the worst
                one and the others on its sheet; claimed                  next --claim
  b  fix        a fixer agent under the brief `next` wrote, on a branch
                off the integration branch, in its own worktree
  c  close      in that worktree: the gate against the integration
                branch, and what moved rendered with a close brief         close
  d  check      a close-checker agent, which never sees the fix
  e  judge      KEEP or DISCARD                                           judge
  f  record     after the merge (or the branch's deletion): fixed,
                discarded or waiting, a row each; the new faults filed    record
```

A finding discarded twice leaves the queue; the round report names it, and the next frozen
review can raise it again. Each attempt's brief carries the notes of the discards before it.

## The close check (the keep rule)

`judge` keeps an attempt only if every one of these holds:

1. **The gate is green** on its branch against the integration branch, and **every other
   project is unmoved**.
2. **A sheet moved.** A finding is a fault on a sheet; nothing unmoved can have been fixed.
3. **Nothing was resolved by removal.** The close checker, which has read the finding and the
   re-rendered tiles and nothing else, answers RESOLVED, NOT RESOLVED or RESOLVED BY REMOVAL
   for each; the close brief lists every citation and dimension the sheets printed before and
   print nowhere now, so it can tell.
4. **At least one finding is RESOLVED.** Those are set fixed; the rest are logged discarded
   and stay open.

The checker also reports any blocker or major the fix itself introduced, and `record` files
those as findings in the same queue. Rules 3 and 4 are the **Goodhart guard**: a fixer paid in
closed findings can close one by deleting the note it was about, and that is a discard.

## When it stops

`rounds.tsv`, a row a round: `round date commit reviewer sheets new_blocker new_major new_minor
rejected duplicates majors`, where `majors` lists the new blocker and major ids.
`init` backfills it from `review.json` for a project reviewed before autoreview kept the log.

`status` evaluates, and `round` refuses to freeze once any holds (`--force` overrides):

- **designer**: `STOP` on a line of its own in autoreview.md, or `arkitect autoreview stop`.
- **converged**: two rounds in a row with no new blocker or major the loop can act on -- a
  major now waiting on the designer does not count.
- **noise floor**: with six three-round means, the last three set no new low. The reviewer is
  finding what the reviewer finds, not what the set lacks.
- **budget**: `rounds` this run, or `hours` since `begin`.

## What an attempt may not touch

- **The engine**, unless the program says `engine: allow`: then only as an opt-in keyword that
  leaves every project unmoved. Otherwise a fix that needs it is an ENGINE REQUEST in the
  fixer's report and the finding stays open.
- **trace.md5**: accepted on the fixer's branch so its gate passes, never committed. The lead
  accepts once, on the merged result, so parallel branches never conflict on it.
- **review.json, the logs and the ledger**: the lead records outcomes (`record`); a fixer's
  design call is a CALL line the lead records as an open decision. The hooks refuse a hand
  edit of `rounds.tsv` and `attempts.tsv`, as of `review.json`.
- **The deliverables**: `land` rebuilds them, on main.
- **Any other project**: a gap two projects share is fixed in this one and reported for the
  other, never fixed there in the same run.

## The designer in the loop, without the loop waiting on them

- **autoreview.md is the program.** Its front matter: `reviewer`, `verifier`, `fixer` (the
  models), `rounds`, `hours`, `attempt_minutes`, `parallel_attempts`, `batch`, `severities`
  (`blocker, major` for a majors-only run), `known_list` (`on` gives reviewers the settled
  items so they look for something new), `engine` (`queue` or `allow`), and one
  `group <name>: <sheets>` line per reviewer -- the same every round, so the rounds compare.
  Its body -- the design-call policy, the focus of this run -- goes into every fixer's brief
  word for word.
- **Questions queue.** A finding that needs the designer is set `waiting` with the decision
  that holds the question (`record --waiting ... --note D-nnn`). When the designer confirms
  that decision, the next `round` reopens the finding on its own.
- **The trend is one page**: `arkitect autoreview chart <slug>` draws `rounds.tsv`.

## Where things live

```
projects/<slug>/autoreview.md              the program (the designer's; committed)
projects/<slug>/autoreview/rounds.tsv      a row a round (committed)
projects/<slug>/autoreview/attempts.tsv    a row a finding an attempt took (committed)
~/.cache/arkitect/autoreview/<repo>-<hash>/<slug>/
    run.json                               the integration branch, its worktree, when it began
    claims.json                            the attempts in flight
    round-NN/                              round.json, known.md, render/ (brief, tiles, index),
                                           <group>.json and v-<group>.json, the replies
    attempts/<name>/                       brief.md, close/ (close.md and its tiles),
                                           close.json, judgment.json
```

The state directory is keyed by the repository, not the checkout, so the lead in a worktree
and the designer in the main checkout see one loop; it is outside every checkout, where
`gate render` insists a render goes. Because all of it is on disk, **a lead can be one session
per round**: it reads `status`, runs the stage it names, commits, and ends. A lost session
costs at most one round.

## Commands

```
arkitect autoreview init   <slug> [--force]         write autoreview.md; backfill rounds.tsv
arkitect autoreview begin  <slug>                   the integration branch and worktree (resumed if open)
arkitect autoreview round  <slug> [--force] [--json]   freeze the next round
arkitect autoreview ingest <slug>                   the frozen round's verified findings in
arkitect autoreview next   <slug> [--group G] [--claim] [--json]   the next attempt and its brief
arkitect autoreview close  <slug> <attempt>         in its worktree: gate, render, close brief
arkitect autoreview judge  <slug> <attempt> <verdicts>   KEEP or DISCARD
arkitect autoreview record <slug> <attempt> [--waiting R-nnn,... --note D-nnn]
arkitect autoreview status <slug> [--json]
arkitect autoreview stop   <slug> [--reason "..."]
arkitect autoreview chart  <slug> [--out FILE]
arkitect autoreview land   <slug> [--no-push]       main checkout, on main only
arkitect review known      <slug> [--all]           the settled list a brief carries
arkitect review parse      <reply-or-transcript> [--out FILE]
```

The agents come from `.claude/skills/autoreview/SKILL.md`, the lead's procedure, and three
agents with Read and Glob only: `plan-reviewer`, `finding-verifier` and `close-checker`.

## Not yet

- A carry check that files a shared gap in the other project's review as a finding of its own.
- A serialized engine lane that takes ENGINE REQUESTs between rounds.
- The web UI's Rounds tab, and an *autoreview* button beside *Review sheets*.
- Token budgets: `hours` and `rounds` are measured; tokens are not visible to the engine.
