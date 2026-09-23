# Contributing to arkitect

Contributions are welcome: a fix, a check the engine does not make, a sheet it does not draw,
a jurisdiction it does not know. Every pull request needs a signed contributor license
agreement (below). The code is under the PolyForm Noncommercial License 1.0.0 and the
documentation under CC BY-NC 4.0; NOTICE says which path is which.

## Set up

Python 3.11, 3.12 or 3.13, from a checkout:

    git clone <this repository> arkitect && cd arkitect
    python3 -m pip install -e ".[dev]"
    arkitect --version

Install from a checkout, not a wheel, and do not change a pin in `requirements.txt` or
`pyproject.toml` in passing: reportlab's text metrics are load-bearing, so a different
version can move a drawn dimension. Read `requirements.txt` before proposing a bump.

Optionally, `arkitect hooks install` wires the Claude Code hooks that refuse the commands
which have produced false greens here and run the gate when a turn ends.

## The one check

    arkitect gate --full

must pass before you open a pull request, and CI runs it on Linux and macOS under every
supported Python. It builds every example project, records every canvas call of every sheet,
holds each drawing to the digest its project committed in `trace.md5`, runs the DXF exporter,
pyflakes and the sheet-text checks, and with `--full` the test suite. It exits 0 only if every
check ran and passed. `arkitect test` alone is not the check, and neither is `pytest` or
`unittest discover`: both report success after collecting nothing.

**The PDFs are the product.** A change that moves a sheet by a thousandth of a point has moved
it, and a "cleanup" that alters a drawn dimension is a defect in a document somebody will build
from. So the gate fails on a moved drawing until you record that you meant it:

    arkitect gate render --moved       # look at what moved
    arkitect gate accept               # the only writer of trace.md5; prints the sheets that moved

Accept only a drawing you meant to move, and say in the commit message and the pull request
which sheets moved and why. A refactor moves nothing: prove it with
`arkitect gate --base main --expect-unchanged`. Never edit a `trace.md5` by hand.

## Commits

- Stage files by name (`git add path/to/file`, or `git add --pathspec-from-file=<list>`).
  Never `git add -A`, `git add .`, `git add -u` or `git commit -a`: scratch files and other
  work have been swept into commits that way.
- One change a commit, with a message that says what changed and, when a sheet moved, which.
- Never discard a checker's stderr or mask its exit status (`2>/dev/null`, `|| true`) when
  you report that it passed.

## Import, never copy

A table, a check or a drawing helper that a second project needs goes in `arkitect/codes/`
(a rule that cites a code section, with one pin per transcribed table in
`arkitect/codes/verify/`) or `arkitect/lib/` (geometry and drawing with no citation), never
into one project's model. `arkitect/lib/verify/test_twins.py` fails a definition copied from
one project into another. `arkitect/lib/` knows no code section and no place.

Transcribe a code table from the code's own text, never from a summary of it, and say in the
pull request which edition and section it is.

## The house style

Every note on a sheet follows `style/house-style.md`: American spelling, one home per rule,
notes that instruct, no revision history, no internal vocabulary, labels in order, figures from
the model. The plan reviewer reads that file, so a rule written there is a rule it enforces.
Read it before writing a note.

## A new jurisdiction

How a jurisdiction is added is documented in `docs/jurisdictions.md`. A city is a
code-research job, not a setting: its rules arrive with their citations.

## The contributor license agreement

Every pull request needs a signed CLA from each of its authors before it is merged. Read
[CLA.md](CLA.md): you keep the copyright in your contribution and grant the maintainer a
perpetual, worldwide, non-exclusive, royalty-free, irrevocable copyright and patent license
to it, including the right to sublicense and to use it commercially. CLA.md says how to sign;
you sign once, and it covers every later contribution.
