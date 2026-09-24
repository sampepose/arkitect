"""One project's sheet index, for the web UI: every sheet its build draws -- its number, title,
scale and the document it is bound in -- and the title block's address.

    python3 -m arkitect.web.index projects/<slug>/build.py      # prints JSON

Run as a subprocess, one project at a time: a project's `src` is a package of its own, and two
of them in one interpreter would be one `src`. It listens for the sheets the drawing classes
announce (arkitect/lib/draw/context.py observe()), so it reads each Sheet's own attributes
rather than parsing a PDF, and the build draws into a scratch directory, never the checkout.
"""
import json
import os
import sys
import tempfile

from arkitect.lib import buildscript
from arkitect.lib.draw import context


class _Sheets:
    """An observer: one row per sheet, in the order the documents draw them."""

    def __init__(self):
        self.rows, self.doc, self.titleblock = [], None, None

    def sheet(self, sh):
        if self.titleblock is None and sh.titleblock:
            self.titleblock = sh.titleblock
        self.rows.append({'no': sh.no, 'title': sh.title, 'scale': sh.scale, 'doc': self.doc})


def index(build_path):
    """{'address', 'city', 'titleblock': [(heading, lines)], 'sheets': [{no, title, scale, doc,
       page}]} for a build."""
    obs = context.observe(_Sheets())            # no document is open: every one inherits it
    keep = sys.stdout
    sys.stdout = open(os.devnull, 'w')          # the build's own report is the gate's, not ours
    try:
        mod = buildscript.load(build_path)
        with tempfile.TemporaryDirectory() as tmp:
            for doc in buildscript.documents(mod):
                obs.doc = doc.__name__
                doc(os.path.join(tmp, doc.__name__ + '.pdf'))
    finally:
        sys.stdout.close()
        sys.stdout = keep
        context.unobserve(obs)
    seen, sheets = set(), []
    pages = {}
    for r in obs.rows:
        pages[r['doc']] = pages.get(r['doc'], 0) + 1
        if r['no'] in seen:                     # a sheet bound twice keeps its first place
            continue
        seen.add(r['no'])
        sheets.append(dict(r, page=pages[r['doc']]))
    tb = [(h, list(lines)) for h, lines in (obs.titleblock or [])]
    first = tb[0][1] if tb else []
    return {'address': first[0] if first else '', 'city': first[1] if len(first) > 1 else '',
            'titleblock': tb, 'sheets': sheets}


def main(argv):
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    json.dump(index(argv[0]), sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
