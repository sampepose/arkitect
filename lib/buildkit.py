"""A project's DOCUMENTS from what it draws: the build.py contract, for a project with
nothing of its own to say about opening a canvas.

The first two projects write this out in their build.py -- a `drawing()` context, then
build_set() and build_zoning_sheet() -- and they came first. A project scaffolded by
harness/scaffold.py imports it instead, so its build.py holds only what is its own: the
title block, the model check, and the sheets in binding order.

The contract is lib/buildscript.py's: each document is fn(output_path=None,
make_canvas=None) -> the path written, and it runs the model check before it draws, so a
tool drawing one document alone still checks the model.
"""
import contextlib

from reportlab.pdfgen import canvas

from lib.draw import page


def documents(titleblock, check_model, sheets, set_out, zoning_sheet=None, zoning_out=None):
    """(build_set,) or (build_set, build_zoning_sheet): the set in binding order at ARCH C,
       and the zoning site plan as its own 11 x 17 document."""

    @contextlib.contextmanager
    def drawing(path, size, make_canvas):
        cv = (make_canvas or canvas.Canvas)(path, pagesize=size)
        with page.document(cv, titleblock=titleblock):
            yield cv
            cv.save()

    def build_set(output_path=None, make_canvas=None):
        path = output_path or set_out
        with drawing(path, page.ARCH_C.size, make_canvas):
            check_model()
            for sheet in sheets:
                sheet()
        return path

    if zoning_sheet is None:
        return (build_set,)

    def build_zoning_sheet(output_path=None, make_canvas=None):
        path = output_path or zoning_out
        with drawing(path, page.ANSI_B.size, make_canvas):
            check_model()
            zoning_sheet()
        return path

    return (build_set, build_zoning_sheet)
