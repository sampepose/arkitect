# The machine interface

What `arkitect <tool> ... --json` prints, for a program -- the hosted service, a CI job, an
editor -- to read instead of scraping text written for people. `arkitect/lib/interface.py`
writes every one of them.

## The envelope

Every JSON output is one object whose first four keys are always:

| key         | meaning                                                                 |
|-------------|-------------------------------------------------------------------------|
| `schema`    | the interface's number, now **1**                                       |
| `kind`      | `gate`, `progress`, `decisions`, `review` or one of `autoreview`'s      |
| `engine`    | the engine version that produced it (`arkitect --version`)              |
| `workspace` | the workspace it describes: the directory holding `projects/`            |

**The promise.** Within one schema number a field may be *added*; none is removed, renamed or
given another meaning. Anything else raises `schema`, and a reader should refuse a number it
does not know.

A tool finds its workspace from the directory it is run in, exactly as without `--json`.

## `gate`

    arkitect gate --json [--full] [--base REF] [--engine-base REF] [--project SLUG]

Exit status: 0 passed, 1 failed, 2 something could not run -- never 0 for a check that did not run.

| field        | meaning |
|--------------|---------|
| `ok`         | every check ran and passed |
| `tier`       | `fast` or `full` (`--full` adds the test suite) |
| `base`       | the commit measured against, and the engine's with `--engine-base` |
| `projects`   | per project: `trace` (`ok`, `digest`, `calls`, `committed`), `engine` (`recorded`, `running`, and `upgrade: "proposed"` when a new engine moved nothing), `sheets_moved` (`[{sheet, change, before, after}]`, or null with no base), `stdout_diff`, `vocab_lost`, `sheet_text` (`findings`), `dxf`, `progress` |
| `pyflakes`, `twins`, `tests` | the repository-wide checks, each with `ran` and `ok` |
| `decisions`  | `{status: count}` over the ledger |
| `review`     | `{project: {severity: open count}}` |
| `failures`, `errors` | sentences, one per problem: a failure is a check that failed, an error one that could not run |

## `progress`

    arkitect progress status SLUG --json      # and `next`: the same object
    arkitect progress verify SLUG --json      # without `features`

| field      | meaning |
|------------|---------|
| `project`  | the slug |
| `counts`   | `{passes, drawn, pending}` |
| `total`, `next` | how many features, and the next one's sheet number (null when every one passes) |
| `false`    | claims the build does not prove -- non-empty means exit 1 |
| `behind`   | sheets the build binds that the list still calls pending |
| `features` | `[{id, title, status, guards, notes}]`, in order |

## `decisions`

    arkitect decisions pending --json [--project SLUG]      # open and waiting
    arkitect decisions list --json [--status S] [--project SLUG]
    arkitect decisions about PATH --json
    arkitect decisions show D-nnn --json                    # with `body`

`decisions` is a list of records, each its front matter as fields: `id`, `title`, `status`
(`open`, `waiting`, `confirmed`, `superseded`), `by`, `date`, `projects`, `decision`, `ask`,
`confirmed`, `waiting_on`, `superseded_by`, `alternatives`, `if_reversed`, `refs` -- the ones a
record carries.

## `review`

    arkitect review list SLUG --json [--status S]
    arkitect review next SLUG --json          # the worst open finding, or none

`findings` is a list of `{id, sheet, where, category, severity, finding, evidence, suggest,
status, ...}`; `project` is the slug.

## `autoreview`

    arkitect autoreview status SLUG --json       # kind `autoreview`
    arkitect autoreview round SLUG --json        # kind `autoreview-round`
    arkitect autoreview next SLUG --json         # kind `autoreview-attempt`

`autoreview`: `project`; `run` (`branch`, `worktree`, `started`, `first_round`, `stopped`);
`stage`, a sentence; `round`, the newest round frozen; `claims` (`{attempt: [finding ids]}`);
`queue`, the findings an attempt may take; `open` and `waiting` (`{severity: count}`);
`rounds` and `attempts`, the rows of projects/SLUG/autoreview/rounds.tsv and attempts.tsv as
objects of strings; `stop`, a list of `{rule, holds, detail}`.

`autoreview-round`: `round`, `frozen`, `commit`, `dir`, `render` (the review directory),
`models` (`reviewer`, `verifier`, `fixer`), `reopened` (finding ids), `tasks` (per group:
`group`, `sheets`, `raw` and `verified` -- the paths its replies go to -- and `reviewer` and
`verifier`, the prompts), `ingested` (null until it is).

`autoreview-attempt`: `project`; `attempt`, null when the queue is empty, else `name`,
`round`, `findings`, `branch`, `base`, `tree`, `brief`, `since`, `fixer`.
