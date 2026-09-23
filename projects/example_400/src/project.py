"""400 Oak Ave — the lot, and everything on a sheet that names it.

The one place a different project starts. Nothing in arkitect/lib/ knows any of this; the
title block is handed in, and the output names come from here.
"""

ADDRESS = "400 OAK AVE"

TITLEBLOCK = [
    (None, [ADDRESS,
            "COLUMBUS, OHIO 43200",
            "FRANKLIN COUNTY PARCEL TBD",
            "SPLIT FROM PARCEL 010-000400-00",
            "NEW CONSTRUCTION — 3 DWELLING UNITS",
            "2 DETACHED RESIDENTIAL BUILDINGS"]),
    # From the designer on 2026-09-22; the same owner as 300.
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

PDF_OUT = "400-Oak-permit-set.pdf"
ZONING_OUT = "400-Oak-zoning-site-plan.pdf"
DXF_OUT = "400-Oak-floor-plans.dxf"
