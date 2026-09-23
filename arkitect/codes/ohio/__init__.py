"""Ohio: the state codes every project in the state answers to.

The Residential Code of Ohio (OAC 4101:8, eff. 7-1-2019, as amended 2024), the Ohio
Plumbing Code and the NEC edition the RCO adopts. A city's own code sits beside this
package (arkitect/codes/columbus), never in it.

A table here is ONE transcription with ONE test pinning it (arkitect/codes/verify). Projects import
it; they never carry a copy. Move a project's copy here only when arkitect/lib/verify/twins.py
shows it identical in every project that has it.
"""

NAME = 'Ohio'

# What every Ohio set's title block states of the codes, before the city adds its zoning line:
# the RCO's edition and amendments, the NEC it adopts, the IRC it is based on.
TITLEBLOCK_CODE = ["RESIDENTIAL CODE OF OHIO 2019",
                   "OAC 4101:8, EFF. 7-1-2019, AS AMENDED:",
                   "CH. 4 FOUNDATIONS, EFF. 3-1-2024",
                   "CH. 34 ELECTRICAL, EFF. 4-15-2024",
                   "CH. 44 STANDARDS, EFF. 4-15-2024",
                   "ELECTRICAL: NFPA 70, 2023 NEC",
                   "BASE: 2018 IRC FIRST PRINTING"]

# Ohio lets a one-, two- or three-family dwelling's plans be submitted without a seal, and the
# title block says so in one line -- the one thing true of every such set in the state.
# ORC 3791.04(A)(2)(b), verified against codes.ohio.gov on 2026-09-22.
SEAL_LINE = "NO SEAL REQUIRED \u2014 ORC 3791.04(A)(2)(b)"
