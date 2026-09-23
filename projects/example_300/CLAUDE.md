# 300 S Elm Ave — working notes for agents

A complete permit set: five dwelling units in two detached buildings on a corner lot,
Columbus OH, 27 sheets and an 11 x 17 zoning site plan. Building 1 holds Unit 1 (two
storeys at the front) and Units 2 / 3 (stacked at the rear), separated by two 1-hour walls
back to back; Building 2 holds Units 4 / 5. Both exterior stairs are prescriptive wood, the
set is all-electric, and every figure a sheet prints is derived from `src/`.

This is an ANONYMIZED copy of a real set drawn with this engine: the names, addresses,
parcel, owner and contractor are fictional; the design, the checks and the sheets are the
real set's. `example_400` was drawn next, as a copy of this one, which is why the two share
the code `lib/verify/twins.py` counts; what they proved in common has since moved into
`lib/` and `codes/`.

- `build.py` is the document order and `check_model()`: the model checks run before a
  line is drawn, and a failing one stops the build with the rule and the room named.
- `src/` is the model (levels, openings, the two buildings, framing, roof, bracing,
  mechanical, electrical, plumbing, drainage, grading, fire separation) and `src/sheets/`
  one module per sheet.
- `verify/` holds the tests, including the pins of every transcribed code table.
- `python3 -m lib.verify.gate --project example_300` checks it; `render --sheets A-101`
  shows a sheet.

Read a module's docstring before changing it: most say which rule they carry and which
sheet prints it.
