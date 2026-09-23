# What costs model tokens, and what is free

Everything `arkitect` does by itself runs on your machine and calls no model. Tokens are
spent only when an agent works: drafting sheets and reviewing them, in Claude Code.

## Free: every `arkitect` command

`gate`, `test`, `trace`, `dxf`, `sheet-text`, `twins`, `intake`, `scaffold`, `progress`,
`decisions`, `config`, `hooks`, `engine`, and `review prepare / ingest / list / next / set` --
none calls a model. Measured on an Apple M3, Python 3.12:

| command                                       | time   |
|-----------------------------------------------|--------|
| `arkitect gate --project example_300` (27 sheets + C-102, 61,295 drawing calls) | 3.2 s |
| `arkitect gate` (all four examples)           | 3.9 s  |
| `arkitect gate --full` (and 1,170 tests)      | 69 s   |

## Model tokens: the agents

| work                                   | who does it                                    |
|----------------------------------------|------------------------------------------------|
| start an address                       | the `new-address` skill, in your Claude Code session |
| draw a sheet                           | the `next-feature` skill, one feature a session |
| review sheets                          | the `review-sheets` skill: a `plan-reviewer` agent that sees only the images, then a `finding-verifier` agent that throws out what the images do not bear out |
| any other request                      | your Claude Code session                        |

The agents name no model of their own: each runs on the model your session uses.

### A plan review, measured

One sheet -- `example_400`'s A-101, both floor plans of a two-storey house, reviewed as a whole
image and six 200 dpi tiles -- on 2026-09-23, with the session's model (Claude Opus 5.5):

| step                 | tokens  | reads | time    | result |
|----------------------|---------|-------|---------|--------|
| `plan-reviewer`      | 90,963  | 9     | 4 m 34 s | 22 findings |
| `finding-verifier`   | 80,357  | 10    | 2 m 10 s | 12 confirmed, 8 plausible, 2 rejected |
| **one sheet**        | **171,320** | 19 | **6 m 44 s** | 20 findings kept |

Most of it is the images: each tile is a large picture, and each agent reads all of them. A
denser sheet costs more, a sparse one less. **Not measured:** a review of a whole set. Reviewed
one sheet at a time it would be about 24 x 171,000 = 4.1 million tokens for `example_400`;
`review-sheets` batches several sheets per agent, which shares the brief and should cost less,
but that has not been measured.

Reviewing an example will always report its title block's owner, contractor and parcel as
placeholders: they are fictional on purpose.

### Drawing a sheet: not measured

A `next-feature` session writes a sheet's model and drawing code, runs the gate until it
passes, and looks at the sheet. Its cost varies with the sheet by an order of magnitude or
more -- a cover sheet is short; a framing plan that derives every header is not -- and none
has been measured under controlled conditions. Claude Code's `/cost` shows a session's total;
record it when you run one, and send the figure in.
