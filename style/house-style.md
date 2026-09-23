# House style

The rules every sheet in this repository is held to. The plan reviewer
(`harness/review.py`) reads this file into its brief, so a rule written here is a rule
the reviewer enforces.

- **American spelling on every sheet** (2026-09-16: British spelling is the single biggest
  sign a set was not drawn by a local drafter). STORY / STORIES, CENTERLINE, VAPOR,
  LICENSE, LABELED, CENTERED, CENTER, FIBER, ALUMINUM, GALVANIZED, COLOR, GRAY; and
  stacked units are UNITS or a STACKED PAIR, never FLATS or a TWO-FLAT. Identifiers such
  as `L2_STOREY` and reportlab's `drawCentredString` are code, not text, and stay.
- **Each rule has ONE home sheet; every other sheet cross-references it** (2026-09-16,
  after one rule — that nothing crosses the unit separation wall — was found printed on
  about 20 notes). A rule lives in one numbered note (the separation wall's crossings on
  A-001, the CO alarms on G-001, the exterior stairs on A-001 and their detail sheet), and
  every other sheet points there. A sheet that repeats another's whole note block — M-102,
  E-102, P-103 beside M-101, E-101, P-102 — carries "SEE M-101" / "SEE E-101" / "SEE P-102"
  in its place (`notes(..., see=)`). Do not restate a rule on a second sheet; cite its home.
  **A summary sheet is where this rule fails most** (2026-09-20, an outside review:
  "consolidate the repeated egress-window, smoke-alarm, stair, ceiling-height and
  all-electric language"). A life safety summary on A-602 became a second copy of G-001's
  general notes — the escape opening, ceiling height, room area, stairs and the alarms,
  figures and all, the escape opening a THIRD time because the window schedule notes on
  the same sheet carry the product requirement. It should cite the G-001 notes and keep
  only what is that project's own fact (how many sleeping rooms, the bedroom areas).
  Summarising and restating look the same while you are writing one.
  **Before deleting a restatement, check the rule HAS a home.** One set's A-602 carried
  "LANDING AT EACH EXTERIOR DOOR PER RCO 311.3" and nothing else on that set said a
  landing was required; trimming it would have taken the requirement off the set. It
  moved to the grading sheet instead. A grep sweep found it; `lib/verify/sheet_text.py`
  could not, because a rule that stops being stated cites nothing and overlaps nothing.
  The cheap oracle for a trim is a VOCABULARY diff of the two `sheet_text` dumps rather
  than a line diff: pull every RCO / OPC / NEC citation and every dimension out of each,
  and list what the before dump has and the after dump has nowhere. "None" is what says a
  rule moved rather than died. Write it as a throwaway beside the dumps; it is ten lines
  of `re.findall`.
- **RCO sections are cited without the IRC's R prefix**: "RCO 311.7", "TABLE 602.7(1)",
  "302.2.6" — the Residential Code of Ohio numbers them that way. "IRC R313" keeps its
  R because it names the IRC. `lib/verify` pins some table keys, so a key and its lookup
  change together; never reintroduce a lone "RCO R…".
- **Chapter 15 is the 2018 IRC's arrangement, not the 2015 IRC's** (2026-09-20, after
  the M sheets cited M1507). The filed rule — OAC 4101:8-15-01, eff. 7-1-2019, downloaded
  from codes.ohio.gov, not a summary — numbers them **1503.3** exhaust discharge (the
  ductless hood exception), **1504.3** exhaust openings (3'-0" to a property line, an
  opening, a door), **1505.4** whole-house mechanical ventilation, **TABLE 1505.4.3(1)**
  continuous whole-house rates and **TABLE 1505.4.4** local exhaust rates. M1506.3 and
  M1507 are the 2015 IRC, and the 2021 IRC keeps 1504 / 1505, so a source that agrees is
  not proof of the edition. This was "corrected" the wrong way once already, by a
  2026-09-14 commit whose subject says "the sections are the 2018 IRC's". **Ohio prints
  them with no M**, as it prints no R; the sets still write M1305.1, M1502.3, M1504.3,
  and dropping that prefix set-wide is the designer's call, not a cleanup.
- **The louvered dryer closet's 100 SQ IN has no home in Ohio, and the sets assert it**
  (2026-09-20). It is 2015 IRC M1502.5, "Makeup air"; the 2018 IRC deleted that section,
  so in the adopted chapter 1502.5 is "Protection required" — shield plates — and no
  section of Chapter 15 carries the figure (1503.6's make-up air needs a fuel-burning
  appliance inside the air barrier AND over 400 cfm, and an all-electric project burns
  nothing). The IMC keeps it at 504.6 and does not govern a one- to three-family dwelling
  here. A set prints it as its own minimum beside the rule that does bind — M1502.1, the
  dryer maker's instructions. **Do not put "RCO M1502.5" back beside the 100 SQ IN**, and
  do not read the figure as code. **Keeping the figure is settled** (2026-09-20), over
  requiring only the maker's opening: the IMC still carries it at 504.6, and a scheduled
  door type should give the framer a number to build to rather than a document to go and
  find. Do not delete the number for want of a section.
- **A note that cites a note on its OWN sheet is checked by nothing.**
  `lib/verify/sheet_text.py` matches "X-000 NOTE n" across sheets and the tests hold its
  findings at zero, but a bare "note 7" is matched by neither, and the number it names
  usually EXISTS — so an existence check would not catch it either. The same sheet can be
  numbered differently in two projects (one has a note the other has no need of, so every
  note after it is off by one), and a note copied between them carries the other's
  numbering silently: two sets once shipped it, in opposite directions. Renumber or copy
  a note and read every "note n" on that sheet by hand.
- **Notes instruct. They do not argue.** No "THIS IS NOT A PREFERENCE", "NOT A DRAFTING
  ERROR", "BY DESIGN". A note insisting it is not an error plants the idea that it is.
- **No revision history on a sheet.** The reviewer has never seen a prior issue, so
  "PREVIOUSLY SCHEDULED", "IS DELETED", "NO LONGER AN EXCEPTION" can only confuse. State
  the condition, not the change.
- **No internal vocabulary.** A module name such as "THE MIRROR" means nothing on a
  sheet.
- **Keep labels in ascending order** — cross-references run between sheets (one A-001
  note can be called from three of them), so reorder the entries, never the labels.
- Every figure in a note is derived from the model, which is why the note lists live
  beside the sheets that print them.
