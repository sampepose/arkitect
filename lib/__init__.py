"""A drawing-set generator, independent of any one lot.

Everything here answers yes to one question: would a different project use it
unchanged? Anything that names this address, this owner, this zoning district or this
building's dimensions lives in src/ instead.

    lib.draw     the canvas: a sheet, a plan, text on a page
    lib.model    the geometry: the stud-to-stud regrid, dimension chains, mirrors,
                 floor levels, window marks, exterior stairs
    lib.symbols  plan symbols, grouped by what the thing is
    lib.export   DXF, recorded from the same calls that draw the PDF
    lib.verify   the golden-master harness a refactor is checked against
"""
