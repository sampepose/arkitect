# The local web UI

    cd my-projects          # a workspace: the repository that holds your projects/
    arkitect web            # opens http://127.0.0.1:8765/  (--port, --no-open)

A browser view over the same files the CLI works on. It is the first step of the hosted service
(docs/hosted-service.md, phase 7) run on one machine for one person: no accounts, no sandbox,
bound to 127.0.0.1.

**It is a view, not a second system.** Every screen reads a `--json` tool of the CLI
(docs/interface.md) or a file the workspace holds, and every button that changes something
runs the command you would type -- `gate accept`, `decisions set ... confirmed --quote`,
`review set`, `git commit` of named paths, `git restore` -- in the workspace, and shows what it
printed. Nothing a drawing depends on lives only in the UI. Close it and the terminal sees the
same commits.

## The screens

| screen | shows | does |
|--------|-------|------|
| **Workspace** | the last gate run, each project (sheets, trace calls, open findings, digest, sheet text, DXF), recent commits and the sheets each moved, the decisions waiting on you | run the gate, fast or full; download a project's permit set, zoning sheet and DXF |
| **Sheets** | a project's sheets by discipline, each rendered from the build; the plan-review findings pinned where their tile is; the decisions about the modules that draw the sheet; its checks at the last gate | zoom; open a finding in review |
| **Gate** | every oracle per project and for the workspace; each moved sheet at the base and now, by swipe, overlay (difference) or side by side, with the changed regions boxed; the build output's diff; what the base printed that nothing prints now | accept and commit, the message naming the sheets that moved and the files chosen (the digests `gate accept` writes are always in it); discard a change, which asks twice |
| **Decisions** | the ledger by status and project; a record's choice, its questions one by one, the alternatives, what moves if it is reversed, its account | Keep each question, then Confirm with your words, committed alone. A Change is work, not a confirmation: it is not recorded here |
| **Review** | a project's plan-review findings, by status, severity and sheet, each with the tile it names | mark fixed (refused, as on the CLI, until the sheet has changed since the finding), reopen, won't fix with a note; each committed alone |

## Where things live

- **The cache** -- sheet indexes and renders -- is `~/.cache/arkitect/web/<workspace>-<hash>/`,
  outside every checkout, where `gate render` insists a render goes. Each entry is keyed by the
  commit, the engine version and every uncommitted change under the project, so an edit shows
  on the next load and a stale render is never served. Deleting it costs only a rebuild.
- **The sheet index** is `arkitect/web/index.py`, run as a subprocess per project: it listens for
  the sheets the drawing classes announce while the build draws into a scratch directory.
- **The last gate run** is kept in the cache so the pages can show it; the gate itself still
  runs only when you ask.

## Not yet (the next milestone)

The buttons for agent work -- *New address*, *Review this sheet*, *Review sheets…*, *Ask Claude
to fix*, *Hand changes to Claude* -- are drawn and disabled. Each is one agent session (a
skill: new-address, review-sheets, next-feature, a requested change) run in the workspace with
its log streamed to the page; until then, ask for it in the terminal. The UI does not rebuild the
tracked deliverables on accept either: rebuild them as you do today when a drawing change is
merged.
