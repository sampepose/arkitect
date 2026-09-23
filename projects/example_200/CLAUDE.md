# 200 EXAMPLE AVE — working notes for agents

A permit set for 200 EXAMPLE AVE: BUILDING 1, principal, 24'-0" x 36'-0", 2 storeys: UNIT 1 (3 BR); BUILDING 2, ADU, 22'-0" x 24'-0", 1 storey: UNIT 2 (1 BR) on a 35'-0" x 120'-0" corner lot with a 20'-0" alley. Scaffolded from `intake.json` on 2026-09-22 by `arkitect/harness/scaffold.py`. The repo-level
`CLAUDE.md` governs house style, the oracles and the working rules. **This file is only
what is different here.**

## The loop

```sh
python3 -m arkitect.harness.progress next example_200      # the next feature: its guards, its references
python3 -m arkitect.lib.verify.gate                   # every oracle; names the sheets that moved
python3 -m arkitect.lib.verify.gate render --moved    # look at what moved
python3 -m arkitect.lib.verify.gate accept            # write trace.md5 once the move is meant
python3 -m arkitect.harness.progress set example_200 <id> passes   # refused unless the build proves it
```

`intake.json` is the program and the ONE definition of the lot; `src/sitework.py` reads it.
Change it, then `python3 -m arkitect.harness.intake projects/example_200/intake.json`, then build.

## Zoning, as scaffolded

```
RELIEF STATED   Lot width                          50'-0"                       35'-0"                         C.C. 3332.05  -- VARIANCE REQUESTED
MEETS           Dwelling units                     5 MAX, 2 ADUs MAX            2 (1 PRINCIPAL, 1 ADU)         C.C. 3332.355(B)(2)
MEETS           Lot area per principal unit        1,500 SF                     4,200 SF                       SECTION UNVERIFIED  -- lot area used; the density area of 3332.18(C) is not derived
MEETS           Front building line                20'-0"                       20'-0"                         C.C. 3332.21
MEETS           Side street yard                   5'-0"                        5'-0" (BUILDING 1)             C.C. 3332.22(a)(1)
MEETS           Side yard, right                   3'-0"                        6'-0" (BUILDING 1)             SECTION UNVERIFIED  -- framing dimension; a yard is measured to any part of the building or structure, C.C. 3332.26
MEETS           Side yards combined                6'-0"                        11'-0"                         SECTION UNVERIFIED
MEETS           Wall to an interior lot line       5'-0"                        6'-0"                          RCO TABLE 302.1(1)  -- building code, not zoning: under this the wall is rated and its openings limited
MEETS           Lot coverage                       65%                          1,392 SF = 33.1%               SECTION UNVERIFIED
MEETS           Rear yard                          1,050 SF (25% OF LOT)        2,240 SF                       C.C. 3332.27
MEETS           ADU in the rear yard               BEHIND THE PRINCIPAL BUILDING YES                            C.C. 3332.355(C)(1)
MEETS           ADU share of the rear yard         45% MAX                      528 SF = 23.6%                 C.C. 3332.355(C)(3)
MEETS           ADU area, largest                  1,123 SF MAX, NOT OVER 1,728 SF 528 SF                         C.C. 3332.355(B)(3)(a)  -- ESTIMATE from gross floor area
NOT CHECKED     Building height                    35'-0"                       —                              C.C. 3332.29  -- derived once the roof is modelled
NOT CHECKED     ADU height                         25'-0", NOT OVER THE PRINCIPAL —                              C.C. 3332.355(B)(3)(b)  -- derived once the roofs are modelled
MEETS           Parking                            2 (ADUs EXEMPT)              2                              C.C. 3312.49
MEETS           Stall depth                        18'-0"                       18'-0" (22'-0" BEHIND THE BUILDINGS) SECTION UNVERIFIED
MEETS           Maneuvering                        20'-0"                       20'-0"                         C.C. 3312.25  -- the alley right-of-way plus any pad past the stall
MEETS           Parking setback                    8'-0"                        10'-0"                         C.C. 3312.27
MEETS           Alley clear vision triangle        10'-0" x 10'-0"              10'-0" CLEAR                   C.C. 3321.05(B)(1)
RELIEF STATED   Street corner clear vision triangle 30'-0" x 30'-0"              25'-0" (BUILDING 1)            C.C. 3321.05(B)(2)  -- VARIANCE REQUESTED; 5'-0" inside the hypotenuse
```

## Open — from the intake

- **No survey.** The lot is the Auditor's GIS; C-102 says so.
- **Parcel number TBD** on the title block.
- **Lot width** (C.C. 3332.05): VARIANCE REQUESTED. Stated in intake.json `relief`, not granted.
- Building height: not checked yet (derived once the roof is modelled).
- ADU height: not checked yet (derived once the roofs are modelled).
- **Street corner clear vision triangle** (C.C. 3321.05(B)(2)): VARIANCE REQUESTED. Stated in intake.json `relief`, not granted.
- Lot area per principal unit is held to a figure whose section is unverified.
- Side yard, right is held to a figure whose section is unverified.
- Side yards combined is held to a figure whose section is unverified.
- Lot coverage is held to a figure whose section is unverified.
- Stall depth is held to a figure whose section is unverified.
