# Jurisdictions

A permit set is drawn to the rules of one place. `arkitect` encodes a place as a
**jurisdiction**: a city's zoning, its title block and the words its reviewers use, built on
a **state** package holding the building, plumbing and electrical codes the state adopts.
**Columbus, Ohio** is encoded, and is the reference: every rule below is shown by what
Columbus does.

    arkitect jurisdiction list              # what is encoded, and when each was verified
    arkitect jurisdiction check <name>      # does it meet the contract?
    arkitect jurisdiction new <name> --name "City, State" --state arkitect.codes.<state>

**Adding a city is code research, not configuration.** The engine will not let an intake name a
jurisdiction until someone has encoded its rules from the code's own text, checked them
against a real permit set, and recorded when and against what (`VERIFIED_ON`,
`VERIFIED_AGAINST`). A skeleton that has not been verified is refused.

## How a jurisdiction is chosen

An address's `intake.json` names it -- `"jurisdiction": "columbus"` -- and everything after
reads it from there (`arkitect/codes/jurisdiction.py`):

| what                         | how it uses the jurisdiction |
|------------------------------|------------------------------|
| `arkitect intake`            | asks the jurisdiction first, then its questions in its own words; checks the program against its zoning fit; relief may name only its rules |
| `arkitect scaffold`          | the new project imports that city's `fit` and `titleblock` |
| G-001 and C-102              | print its zoning rows, its city name, its parcel label, where an unsurveyed lot's figures come from (`arkitect/codes/zoning_sheets.py`) |
| the feature list             | each sheet's guards name its zoning fit and its state's rules (`{zoning}`, `{state}` in `arkitect/harness/catalog.py`) |
| a plan review                | the reviewer reviews as that place's reviewer would |

A whole set that has no intake names its jurisdiction in `src/project.py`:
`JURISDICTION = "columbus"`.

## The contract

A jurisdiction is a package `arkitect/codes/<name>/`. `arkitect jurisdiction check` holds it to
this, and so does the shared test suite (`arkitect/codes/verify/test_jurisdictions.py`), which
runs for every jurisdiction encoded.

### `__init__.py`

| name               | Columbus                                              | what it is |
|--------------------|-------------------------------------------------------|------------|
| `NAME`             | `'Columbus, Ohio'`                                    | the place, as a sentence says it |
| `CITY`             | `'COLUMBUS'`                                          | as its zoning line prints it: "ZONING: COLUMBUS R-4" |
| `STATE`            | `'arkitect.codes.ohio'`                               | the state package it builds on |
| `CODES`            | the RCO as amended 2024, the OPC, NEC 2023, C.C. Title 33 | what it encodes, editions included; G-001 lists them |
| `VERIFIED_ON`      | `'2026-09-17'`                                        | when its rules were checked against a real permit set; **empty refuses the jurisdiction** |
| `VERIFIED_AGAINST` | `'a Columbus permit set, 27 sheets'`                  | what they were checked against |
| `REVIEWER`         | `'City of Columbus residential plan reviewer'`        | who the plan-review brief says the reviewer is |
| `PARCEL_LABEL`     | `'FRANKLIN COUNTY PARCEL'`                            | the title block's line before the parcel number |
| `LOT_SOURCE`       | `"the Franklin County Auditor's GIS"`                 | where an unsurveyed lot's figures come from; C-102's note prints it in capitals |
| `LOT_SOURCE_SHORT` | `"Auditor's GIS"`                                     | the same, in a table cell |
| `ZONING_CODE`      | `'C.C.'`                                              | the prefix of its zoning sections, left off in the zoning tables |
| `QUESTION_TEXT`    | its parcel, district, front-line and survey questions | `{intake path: question}`, only where it can phrase a question better than the generic one |
| `TITLEBLOCK_CODE`  | Ohio's code lines, its zoning line, Ohio's seal line  | the title block's CODE lines; `%s` takes the zoning district |
| `titleblock(d)`    |                                                       | the whole title block from an intake: the address block, OWNER, CONTRACTOR, CODE |

### `fit.py`

The zoning check every new address runs before a line is drawn. It reads a `Massing` and
answers in `Row`s (`arkitect/codes/massing.py`), the shape every city shares.

| name                 | what it is |
|----------------------|------------|
| `fit(massing)`       | one `Row` per rule: what is required, what the massing provides, `MEETS` / `DOES NOT MEET` / `RELIEF STATED` / `NOT CHECKED`, the section, a note |
| `CITE`               | `{rule: section}` for every rule `fit` can answer -- and the only names an intake's `relief` may use |
| `failing(rows)`      | the rules not met with no relief stated (`arkitect/codes/massing.py` has one) |
| `summary(rows)`      | the rows as text (likewise) |
| `check(massing)`     | a build's zoning check: print the rows, stop on a rule failed with no relief |

Columbus's `fit.py` is the worked example of the discipline the tests hold every city to:

- **Every figure has a source**: a section, written beside the figure, that a permit set here
  already prints. A figure whose section nobody has established prints `SECTION UNVERIFIED`,
  never a plausible number.
- **A rule that needs what the massing does not have yet** (a height before the roof is
  modelled) is `NOT CHECKED`, never assumed to pass.
- **Relief is stated, not granted**: a rule not met can carry the project's basis ("VARIANCE
  REQUESTED"); it still does not meet the rule, and a person decides whether the basis holds.

### The state package

`arkitect/codes/<state>/` holds the codes the state adopts: for Ohio, the Residential Code of
Ohio (`rco/`), the Ohio Plumbing Code, the NEC edition it adopts. It exports `NAME` and
`TITLEBLOCK_CODE` (the title block's lines for those codes), and `SEAL_LINE` where the state
lets residential plans go without a seal (Ohio: ORC 3791.04(A)(2)(b)). A second Ohio city
reuses all of it.

**The rule modules a sheet is checked by are named per state**, not per city: a sheet's guards
are `{state}.rco.egress`, `{state}.opc_drainage` and so on. A new state must supply modules of
the same names -- each a transcription of that state's table, with its pin in
`arkitect/codes/verify/` -- before its sheets can be marked passing. Until then those sheets'
guards cannot run, and `arkitect progress` says so.

## Adding a city

1. **Write the skeleton**:

       arkitect jurisdiction new dayton --name "Dayton, Ohio" --state arkitect.codes.ohio

   It writes `arkitect/codes/dayton/__init__.py` and `fit.py` with every name above, every
   zoning rule `NOT CHECKED`, and `VERIFIED_ON = None`. `arkitect jurisdiction check dayton`
   says it has not been verified; no intake may name it.
2. **Encode the zoning** in `fit.py`, rule by rule, from the zoning code's own text: each figure
   with its section beside it, `SECTION UNVERIFIED` where the text has not been obtained. Pin
   every figure with a test in `arkitect/codes/verify/`.
3. **Fill in the words**: `REVIEWER`, `PARCEL_LABEL`, `LOT_SOURCE`, `ZONING_CODE`,
   `QUESTION_TEXT`.
4. **Verify it** against a real permit set from that city -- its zoning table, its title block,
   what its reviewers asked for -- and record it: `VERIFIED_ON`, `VERIFIED_AGAINST`.
5. `arkitect jurisdiction check dayton` passes; `arkitect gate --full` passes, and the shared
   tests have run it through intake and scaffold.

## Adding a state

A state is a larger job: its residential code, its plumbing code, the NEC edition it adopts, and
their amendments, each table transcribed once with one test pinning it. Start from
`arkitect/codes/ohio/`: its package docstring says what belongs there. A state's first city is
added as above, naming the new state package.
