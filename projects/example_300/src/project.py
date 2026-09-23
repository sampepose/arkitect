"""300 S Elm Ave — the lot, and everything on a sheet that names it.

The one place a different project starts. Nothing in arkitect/lib/ knows any of this; the
title block is handed in, and the output names come from here.
"""

ADDRESS = "300 S ELM AVE"

TITLEBLOCK = [
    (None, [ADDRESS,
            "COLUMBUS, OHIO 43200",
            "FRANKLIN COUNTY PARCEL 010-000300-00",
            "NEW CONSTRUCTION — 5 DWELLING UNITS",
            "2 DETACHED RESIDENTIAL BUILDINGS"]),
    ("OWNER", ["EXAMPLE HOLDINGS LLC",
               "100 MAIN ST SUITE 100",
               "ANYTOWN, OH 43000",
               "614-555-0100"]),
    # The city registration, not the state OCILB trade licence the P/M notes ask of the
    # subs — different instrument, different issuer. LIC-APP0000000 was the portal's
    # Application record; G00000 is the number the city issued, from the designer on 2026-09-15.
    ("CONTRACTOR", ["EXAMPLE CONSTRUCTION LLC",
                    "COLUMBUS GENERAL CONTRACTOR",
                    "REGISTRATION NO. G00000"]),
    ("CODE", ["RESIDENTIAL CODE OF OHIO 2019",
              "OAC 4101:8, EFF. 7-1-2019, AS AMENDED:",
              "CH. 4 FOUNDATIONS, EFF. 3-1-2024",
              "CH. 34 ELECTRICAL, EFF. 4-15-2024",
              "CH. 44 STANDARDS, EFF. 4-15-2024",
              "ELECTRICAL: NFPA 70, 2023 NEC",
              "BASE: 2018 IRC FIRST PRINTING",
              "ZONING: COLUMBUS R-4",
              "NO SEAL REQUIRED — ORC 3791.04(A)(2)(b)"]),
]

PDF_OUT = "300-S-Elm-permit-set.pdf"
DXF_OUT = "300-S-Elm-floor-plans.dxf"
