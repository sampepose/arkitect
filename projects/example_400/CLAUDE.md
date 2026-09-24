# 400 Oak Ave — working notes for agents

A building permit set for 400 Oak Ave, Columbus OH 43200: a 20'-0" x 33'-0" two-storey
house at the front (Building 1 / Unit 1, 3 BR / 2 BA) and a 20'-0" x 33'-0" building of two
stacked ADUs at the rear (Building 2 / Unit 2 at grade, Unit 3 above, 2 BR / 1 BA each),
on an assumed 30'-0" x 124'-0" interior lot with a 20'-0" alley. No zoning relief is
requested. Copied from `projects/example_300` on 2026-09-17 and rebuilt sheet by sheet on
2026-09-18; the repo-level `CLAUDE.md` (300's) still governs house style, the oracles and
the working rules. **This file is only what is different here.**

The PDFs and the DXF are the product and are **tracked**, as 300's are (the designer, 2026-09-20).
`build.py` rewrites the PDFs every run and the merge rebuilds all three, so a committed
output can never fall behind the source that made it. They were gitignored until then and
had drifted weeks behind; the DXF had never been produced at all.

**The drawing is pinned by `trace.md5`** (2026-09-18), as 300's is. A change that moves a sheet
fails `verify/test_trace_digest.py`: trace, find which sheets moved, and commit the new digest
with the change, naming them — `rm -f t.txt && arkitect trace t.txt
projects/example_400/build.py && md5 -q t.txt > projects/example_400/trace.md5`. Never update it just
to make the test pass.

## Commands

```sh
python3 projects/example_400/build.py          # 0.3 s: every model check, then both PDFs
python3 -m unittest discover -s projects/example_400/verify -t .   # Oak's tests alone
arkitect test             # everything; REQUIRED when arkitect/lib/ or arkitect/codes/ is touched
python3 -m pyflakes projects/example_400/build.py projects/example_400/src projects/example_400/verify
```

The designer's loop for Oak: make the change, build, test, commit, reply in 1–3 lines. **Gate the
commit on the build and tests with `&&`.** Touching `arkitect/lib/` or `arkitect/codes/` also needs 300's
trace proved byte-identical against a worktree of the previous commit (it was, for the
`chase` and `jbox` symbols).

The physical-fit checks (headers, heads across windows, stacks at windows, washer drains against
dryer ducts) are `arkitect/lib/model/fit.py`'s and the drawn-text sweep is `arkitect/lib/verify/sheet_text.py`'s — both
shared with 300, which had every fault they found here. `verify/test_sheet_text.py` holds this set
to no string printed on another, no unbound sheet cited and no unprinted note cited.

Both projects' packages are named `src`; Oak's tests swap it in with
`projects/example_400/verify/__init__.py`'s `enter()` / `leave()`. `arkitect/lib/verify/run_tests.py`
carries a floor on Oak's test count — raise it when you add tests.

## The set: 24 sheets + C-102

G-001 · C-101 · C-103 · A-001 · A-101 · A-102 · A-201 · A-202 · A-301 · A-601 · A-602 ·
A-603 · S-101..S-104 · M-101 · M-102 · E-101 · E-102 · P-101..P-103 · P-601, and C-102 as
its own 11x17 document. `build.SHEETS` is asserted against `g001.SHEET_INDEX`. There is no
A-103 / A-203 / A-604 here: A-102 is Building 2's plans, A-202 its four elevations, and the
stair details are **A-603**.

## Coordinates — the trap that costs the most

- **Model feet are pre-mirror.** Model x runs from the SOUTH wall (404 Oak): x 0.5 is
  south, x W-0.5 north; y from the front face toward the alley.
- **Page feet**: x = W − `plan.x(x, y)`, y = `plan.y(y)`. So 396 Oak (NORTH) is at page
  x 0, on the LEFT of every plan. A model mount `'e'` is page `'w'`.
- The regrid maps a rectangle corner by corner and shrinks it; `plan.keep()` maps the
  origin and keeps the size. Use `keep()` for appliances and chases (`_wd()` in
  `mechanical.py` got this wrong once).
- Elevations: FRONT x = `P.x`; REAR x = W − `P.x` − len; NORTH x = `P.y`; SOUTH x = D − `P.y` − len.
- Site feet: x from the north lot line, y from the Oak lot line. `B1_X, B1_Y = 5, 25`;
  Building 2 stands 15'-0" behind Building 1.

## What is derived, and what stops the build

Every check runs from `build.check_model()`. Move a wall, a window, a fixture or a strip
and the sheets follow or the build fails with the rule named. Oak-specific ones:

- **Services** (`src/services.py`): HP-1, EM-1, TC-1 on Building 1's north wall behind the
  dining run; EM-2 and TC-2 on Building 2's north wall, HP-2 / HP-3 on its south. C-101 and
  the elevations draw them from there.
- **Mechanical** (`src/mechanical.py`): bath caps placed by M1504.3's 3'-0"; Level 1 baths
  through a side wall, Level 2 through the roof over the fan (S-103 draws the same points).
  DR-2 / DR-3 stand 7'-6" above their floors, over the parking walk. **Range hoods
  recirculate** — the wall behind Unit 1's range is over the Units 2 / 3 walk.
  `head_violations()`: a wall head may not share wall with a window on its level (window
  heads are at 8'-0"). The heads stand on or toward their outdoor unit's wall
  (`lineset_lengths()`, the designer: "optimize the line so it runs the short way"). The designer keeps a
  head in every bedroom of the ADUs and a CEILING fan in Unit 2's bath, not a wall fan — it
  now hangs in that bath's soffit, below the rated F1 ceiling (see the floors, below).
  **UNIT 1 IS DUCTED, THE ADUs ARE NOT** (the designer, 2026-09-19, ~$2-4k under the four wall heads
  it replaced and two filters to keep instead of four heads to clean). One two-zone system
  on HP-1: `AHU_MARK` is AHU-1 (Level 1) and AHU-2 (Level 2), each a concealed air handler
  in that level's hall soffit (`building1.U1_SOFFIT_ROOMS`, `U1_SOFFIT_DROP` 12",
  `U1_AHU`; `U1_SOFFIT` is the extent A-101 and M-101 dash -- Level 1's whole hall, Level 2's
  cross-hall and the corridor back from 6'-6", so the attic hatch stands clear of it at the
  corridor's front, a design call; Level 2's runs stay in it to sidewall registers in the
  hall walls, `run_violations()`, a design call), each an `ahu` device on the heat-pump circuit so E-101 and the NEC walk see
  it. `REGISTERS` holds every supply register and the one return per level, in model feet;
  `ducted_violations()` (from `check_mechanical()`) fails the build if a level has other
  than one air handler, if it stands outside its hall, if a register is not inside the room
  it names, if the return is not one, or if the soffit leaves under RCO 305.1's 7'-0"
  (`soffit_clear()`: 7'-8-3/8" on Level 1, 7'-11-3/8" on Level 2). **Nothing is in the
  attic** — that is what keeps 1103.3.3's duct test off the set, and A-602 says so; put a
  duct or an air handler up there and that row is false. The line sets went 42'-6" to
  about 38'-0" as drawn, each leaving its air handler off the supply trunk and Level 2's
  dropping inside the north wall. M-101 note 6a has Manual D, the dampers, the filter and the return path; note 3
  adds RCO M1411.3.1's auxiliary pan, which a unit over a finished ceiling needs. The
  legend lists what a building draws (`m_common.legend_kinds()`), which is why 300's M
  sheets are byte-identical though `arkitect/lib/symbols/mechanical.py` gained two symbols.
  **Each zone has its own thermostat** in its hall beside the air handler, and each ADU a
  wall control in its living space (the designer, 2026-09-19; RCO 1103.1, the root notes have the
  rule). Programmable for the two ducted zones, 1103.1.1.
- **Water** (`src/plumbing.py`): ONE service from Oak down the NORTH side yard, a supply
  under each building's north wall, a submeter per unit, the DPU meter in a pit at the
  right-of-way. 24.9 WSFU at 156 ft: 3/4" meter, 1-1/4" service.
  `check_working_spaces()` holds each water heater out of its panel's 36" — it moved
  Building 2's heater to the room's rear hall-side corner.
- **Drainage** (`src/drainage.py`): one exit per building through its SOUTH wall to one 4"
  sewer down the south yard, so water and sewer never cross. `COVER` is **20"**, not 300's
  12": the lot falls ~14" to Oak (`grading.FRONT_LOT`) and `sewer_cover()` must stay over
  1'-0". Five stacks: A (Bath 2, vents the kitchen sink), vent B (Bath 1 + laundry), D, E, F.
  **Stacks A and E stand in chases the plans draw** (`building1.STACK_A_CHASE`,
  `building2.STACK_E_CHASE`); E cannot rise behind the sinks because the kitchen W-B is over
  them on both levels. `laundry_violations()` keeps washer drains 6" off the dryer ducts.
- **Radon** (`src/radon.py`, voluntary, the designer: "add it for oak too"): RR-1 in the hall /
  mechanical room partition stepping to the bedrooms' partition, RR-2 beside stack D with
  one lateral through a 4" sleeve in Building 2's bearing strip. The lateral lies in the
  aggregate OVER the drains — that is only true while `COVER` keeps them deep. One attic
  `jbox` device per riser, within 6'-0".
- **Grading** (`src/grading.py`): all grass — swales S-1..S-3 (north side and courtyard) to
  Oak, S-4 (south of Building 2) to the alley, walk edge W-1 south of Building 1. The designer asked
  for "as minimal and as cheap as possible whilst still following code": no gutters, no
  catch basin, no curb pipes.
- **Fire separation** (`src/fsd.py`): the imaginary line stands 6'-3" off the house and
  8'-9" off Building 2; the Unit 3 stair and the house's rear rake are each 5'-3" from it.
- **Floors are OPEN-WEB FLOOR TRUSSES, and F1 is UL Design L528** (the designer, 2026-09-18: "let's go
  with trusses, whatever is more dummy proof"). 14" deep at **24" o.c.** in both buildings (the designer,
  2026-09-19, a third fewer trusses; S-102 had carried 24" as the plant's alternate), from
  the roof trusses' plant; the listing allows 12" deep minimum and 24" o.c. maximum, ONE 5/8"
  Type C layer (any maker Item 4 lists) on resilient channels at 16", flooring System No. 1
  (plain 23/32" T&G), and NO INSULATION in the cavity -- the listing has no insulation item,
  while pipes, cables and line sets still run through the open webs without piercing the
  membrane (A-601 F1 item B, S-102 note 6). `framing.f1_listing_violations()` holds it.
  **Two traps the listing sets:** a ceiling damper needs 18" trusses AND a floor topping, and no
  item lists a recessed luminaire — so **Unit 2's bath ceiling is a soffit 8" below the rated
  membrane** (`building2.U2_SOFFIT_ROOMS`) with the fan, its duct and the light in it, and the
  rest of Unit 2 takes surface luminaires. A fan or a `rec` device anywhere else in Unit 2's
  ceiling stops the build. Do not deepen the trusses without looking at the headers: the
  plate is `SUBFLOOR_TOP` less the depth, and Level 1's 8'-0" window heads leave 6" under it.
  The listing text was read from a copy of UL Product iQ dated 2025-06-30 on a supplier's
  site, not from UL's own database.
  **The 24" o.c. sets three things.** `framing.MAX_SPAN` is Alpine Engineered Products' 4x2
  floor truss table at 40 psf live / 55 total, L/480, 24" o.c. — 14" spans 19'-9", 16" 21'-7"
  (at 16" o.c. they were 22'-7" and 24'-11"); Building 2's rear bay is 19'-7-1/8", so the 14"
  truss clears it by about 1-7/8" and a deeper bay or a deeper truss needs the plant's design
  first. `levels.F2_GYPSUM` is **5/8"** because the board hangs straight off trusses at 24"
  (F1's is unaffected: its channels stay at 16"), which drops Unit 1's Level 1 ceiling and the
  stair headroom 1/8" to 8'-8-3/8" and 8'-0-3/8". A-601's F1 section picks the largest standard
  scale its 3" column fits — 1" = 1'-0" at this spacing — and prints it.
- **Every header is checked for FIT, and three are LVL** (the designer, 2026-09-18: "do lvl and add the
  checks so we don't miss this again"). Window heads are at 8'-0"; under the double top plate
  that leaves 6" on Level 1 and 9" on Level 2, and Table 602.7's header for a loaded opening
  can be 9-1/4" or 11-1/4" deep. `framing.header_room()` measures each opening's room from its
  own head (`_HEAD`) and its storey's plate; `_make()` schedules the table's header where it
  fits and a 2-ply 1-3/4" x 5-1/2" LVL — a 2x6's depth, so all headers frame alike — where it
  does not (H4, H13, H20 today); `header_violations()` fails the build if any header is deeper
  than its room, if an LVL stands where lumber fits, or if the LVL fails bending, shear or L/360
  under this set's own loads (`lvl_violations()`, a plausibility check: the maker's table
  sizes it, S-102 note 4a). Raise a window head, deepen the floor or widen an opening and
  the schedule changes or the build stops. Unit 2's bath soffit is held to RCO 305.1's 6'-8".
- **The water closet clearances are the ONE dimension measured to finished surfaces**
  (2026-09-20, a reviewer's comment the designer pasted). Every other string on a plan runs stud
  face to stud face — A-001 notes 1 and 1a, G-001 note 5 — and a room rectangle in the
  model IS a stud face, so RCO 307.1's 15" to a *wall* is that face plus its board.
  `arkitect/lib/model/dimensions.py`'s `wc_clearances(..., finish)` starts each side at the
  FINISHED wall face and lets a fixture take it in from there; a fixture needs no
  deduction, since it stands in the room with its finished face where it is drawn. The
  board is `finishes.BOARD` (1/2", A-601 W2, ONE definition — A-602's schedule cell prints
  the same constant), passed as `wall_finish` on each `PlanLevel` and to
  `check_clearances()`. **Bath 1's hall wall is PINNED on the page for this**
  (`building1.BATH1_BAY`, `BATH1_WALL_X`, in Level 1's `xpins` only — `_XPINS` is shared
  with Level 2, which has no wall there): the bay is 15" twice plus the board plus 1/2",
  because unpinned the room stretched to whatever the rear band's slack left, which was
  30-1/2" stud to shower — 30" finished, so a pan centered in it had nothing to spare and
  a pan centered in the STUD band, as this set drew until 2026-09-20, read 15-1/4" each
  side and stood 14-3/4" off the drywall. Move that pin and the pantry, the mechanical /
  laundry room, the hall and everything authored at a model x in that band follow.
  A-001 note 1a states the exception; `verify/test_clearances.py` pins the deduction with
  a synthetic pan that passes to the studs and fails to the finish. 300 carries the same
  shared code and does not move: every pan there is bounded by a tub and a vanity.
- **Schedules**: `schedules.door_tags()` is what A-101 / A-102 draw; the build fails if the
  plans tag anything A-602 does not count.

**The venting is now DRAWN, and the three arrangements are checked apart** (2026-09-20, the
same reviewer through the designer: "another explanatory paragraph will not finish the job. A
coordinated drawing should show the traps, vent takeoffs, drain connections, and vent
reconnections. Conventional venting, bathroom wet venting, and waste-stack venting have
different requirements"). Three findings, one cause: the MODEL said what the old note said.

- **Unit 2's bath was not a wet vent at all.** Its lavatory sat in stack D's `serves`, so it
  drained into the stack under Unit 3's discharge while the closet and the tub drained below
  the slab with nothing venting them, and V-D dashed across to the closet and tub symbols.
  Now `LAV2` drops through the slab at the lavatory (penetration 1) and its drain runs to the
  closet bend and on to the tub: **912.1's horizontal wet vent, lavatory then closet then
  tub**, 2" to the closet and 3" from there, V-D standing at the head with nothing upstream
  of it (912.2.1). The tub is the most downstream fixture because its waste is at the tub's
  own centre, past the closet -- the other order is not drawable here. **Stack D carries Unit
  3 alone** and comes into the building drain at `D_FOOT_X`, east of the tub's trap box,
  downstream of the whole group as 912.1 requires of any additional fixture.

- **The Level 2 groups are 912.1.1 VERTICAL wet vents**, which is what makes the stack their
  vent: `CONN_Z` puts each closet bend 12" under its floor, the tub 6" under and the
  lavatories 16" and 20" over (`CONN_STEP` staggers a second fixture of one kind), each
  connection independent, the closet lowest, and the stack carried full size over the highest
  connection is the dry vent (912.2.2). An assert holds the closet bend inside the floor it
  drops through, so deepening a truss is caught.

- **Stacks E and F are 913 WASTE STACK VENTS and the set now says so.** `WASTE_STACKS`,
  `waste_stacks()`; neither takes a water closet, E sits exactly on Table 913.4's 2" row
  (2 DFU at a branch interval, 4 in all -- add a fixture to either kitchen and the build
  stops), F is 3", and each offsets to its foot AT THE SLAB, under the lowest fixture connection
  and so outside the span 913.2 allows no offset in (`STACK_OFFSET_Z`). The claim is
  interlocked: `stack_vent_violations(..., claimed_913=WASTE_STACKS)` skips them and the
  project hands it the fixtures with no dry vent of their own, so dropping either name from
  `WASTE_STACKS` fails the build with "only a 913 waste stack vent may do that".

The rules are `arkitect/codes/ohio/opc_vents.py` (`vertical_wet_violations`, `horizontal_wet_violations`,
Table 912.3 as `WET_VENT`, `waste_stack_text`) and the DRAWING is
`arkitect/codes/ohio/opc_vents_draw.py` -- in `arkitect/codes/` because every label names a section and arkitect/lib/ is
code-neutral. P-601's riser draws each trap where it stands, each connection in order with its
height printed, each vent takeoff on its fixture's connection and each reconnection above every
fixture on that stack; the stack is solid where it carries waste and dashed above its highest
connection; each waste stack carries a bracket over the span 913.2 governs and its offset drawn
below it. Notes 1v to 1z are one per arrangement. P-101 note 8 gives every offset (A 7-3/8",
E 8-1/2", F 1'-8-1/4") and cites 1z. **300 can take the drawing as it stands.**

**Bath 2 is a HORIZONTAL wet vent in the Level 2 floor, not a vertical one on stack A**
(2026-09-20, a reviewer's comment the designer pasted: the model connected the two lavatories to stack
A 16" and 20" over the floor while P-601 note 1a sent Bath 2's branches through the floor
trusses -- and the drawing could not show both). The routing note was the true one. Stack A
rises in the Level 1 kitchen chase to a point UNDER BATH 2'S TUB, and the lavatories stand
6'-8" and 9'-8" from it along the hall wall, past Table 909.1's 6'-0" for a 1-1/2" trap:
no vertical pipe stands at them, so 912.1.1 was never available. `BATH2_BRANCH` and
`BATH2_CONNS` in `src/drainage.py` are now ONE branch on the closet flange's line -- far
lavatory, near lavatory, closet, tub -- to stack A's top, 2" to the closet and 3" from it
(Table 912.3), with **V-E** in the hall partition behind the far lavatory as its dry
vent, nothing upstream of it (912.2.1), rising to tie into stack A's vent in the attic.
`FLOOR_BRANCHES` keeps stack A out of `vertical_wet_groups()`, `floor_branch_bottom()` holds
the branch inside the truss webs between the chords (its bottom 8" under the SUBFLOOR
against the bottom chord at 13-1/4", so deepening the branch or shallowing the trusses stops
the build), and Bath 2's trap arms are measured to
the branch, which 912.1 makes their vent. The riser gained a FLOOR form in
`arkitect/codes/ohio/opc_vents_draw.py` (`Floor`, a `Cell` field defaulting to none, so 300 is
byte-identical) and **P-102 draws an enlarged Bath 2 plan** -- the drawing the reviewer asked
for: the stack, every drop, the branch sizes and falls, V-E, and the statement that no
lavatory runs in a wall above the floor and no chase is needed.
**The plumbing annotations are 7 pt, and three things broke when they grew** (2026-09-20, a
reviewer through the designer: "several plumbing annotations are approximately 5-6-point text at full
sheet size, which is difficult to use in the field"). `opc_vents_draw`'s SUB went 5.4 -> 7.0
(TITLE / LEVEL / FIX / METHOD with it), P-102's enlargement 5.2 and 5.6 -> `ANNO` 7.0, and
P-601's trap schedule 5.8 -> `SCHED` 7.0. **Nothing was holding any of them to a width**,
because at 5.4 pt they happened to fit: three riser labels then ran into the NEXT cell, two
cells' foot notes ran into each other, and the legend ran into the sheet frame.
`_cell_label()` wraps a riser label to its own cell and asserts it, and `legend()` asserts
its column -- the assert fired on the first try, which is the point. **`sheet_text.py` saw
none of it**: the strings share a baseline but it pairs only what it is looking for, so a
label sitting on its neighbour is not a finding. Look at the sheet after a type change.
**300's P-601 is untouched**: its riser is hand-typed and never calls `riser()`, which is
why its trace stayed byte-identical through all of this -- and why its own small type is
still small. A separate call.


## the designer's design rules for this project

"Function over form" (the pantry got no window). Cheapest code-compliant option by
default. Windows and doors laid out for symmetry first, equipment placed after. All
openings on all faces are cased. A back door in Unit 1's hall. Fixed W-D over the stair.

## Decisions

What the designer confirmed, what is still an agent's call, and what waits on AEP, DPU, Public Service
or the county is in the ledger, not here: `arkitect decisions pending --project
example_400` and `arkitect decisions about <path>`. The root CLAUDE.md, "Decisions",
has the rules. This file's "Confirmed by the designer" and "Open" sections moved there on 2026-09-22.

## Leftovers to be careful with

Several modules still explain themselves in 300's words, and `building2.py` still names
Unit 3's stair `U5_*`. A comment that says Sage means Building 2's NORTH wall. Nothing
stale prints: the last audit extracted every string from both PDFs and found no 300
vocabulary, no reference to a sheet outside the set, and no dangling note citation.

- **The isometric is the GOVERNING DETAIL for Bath 2's venting, and the other three places
  cite it** (2026-09-21, the reviewer: "keep the new isometric. You can now shorten the
  repeated explanation of lavatory venting in P-102, P-601 note 1a and the isometric caption;
  one governing detail with cross-references would suffice"). He was reading the one-home rule
  back to us. **OPC 909.2 was printed FOUR times** -- P-102's note, note 1a, the caption and
  note 1y -- and is printed once now, in **note 1y**, the arrangement note where the other
  arrangements' rules already live. The caption says what is DRAWN and cites 1y; note 1a keeps
  only where things stand (which chase, which partition, no chase needed) and cites the
  isometric; P-102 keeps what the PLAN shows and cites P-601 note 1a.
  **The dimensions were left alone on purpose.** The crown, the bottom and the 11" print on
  both P-102 and the caption, as the exterior stair's 15 risers print on both A-001 13a and
  A-603 2. The one-home rule governs RULES; a figure a trade builds to is not one.
  **The caption cites a note on its OWN sheet**, which `sheet_text.py` cannot check -- it
  matches "X-000 NOTE n" across sheets and a bare "NOTE 1y" is matched by neither that nor an
  existence check. Read by hand: 1y is on P-601 and carries the 909.2 sentence. Renumber
  1v-1z and this breaks silently.
  **`check_vapor_retarder()` was dead** -- defined in `src/envelope.py` and called from
  nowhere. It runs from `check_model()` now, beside `check_stack_bay()`.

**S-103's notes are numbered one lower than 300's from note 6 on.** 300 carries a W4 note
there and this set has no W4, so here ventilation is **note 6**, attic access 7, insulation
8, roof penetrations 9. Copy a note or a leader between the two sheets and its "note n"
comes over wrong — that is how the eave and ridge vent leaders came to cite note 7 until
2026-09-20. Nothing checks a same-sheet note reference; read them.

- Ohio's minimum building-sewer depth was never checked (as on 300).

- The DXF is `arkitect dxf projects/example_400/build.py`, tracked like the PDFs.
  It has failed TWICE on a layer the exporter had no colour for — the door tags until
  2026-09-18, and `M-HVAC-DUCT` under Unit 1's supply registers until 2026-09-20, when it
  could not be written at all while every other oracle stayed green. `arkitect/lib/verify/test_dxf.py`
  now exports BOTH projects in the suite, reading exit status and stderr, so a third one fails
  loudly. Add a new symbol layer to `COLOR` in `arkitect/lib/export/dxf.py` when you add the symbol.

- The whole set was swept for overlapping text and the flagged pages read; nobody has read
  every page against every other.
