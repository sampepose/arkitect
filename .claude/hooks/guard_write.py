"""PreToolUse hook for the file tools: no hand edit of trace.md5 or progress.json, and
none of a PDF or a DXF inside the checkout. Exit 2 with the reason on stderr; Claude reads
it. progress.json is written by `python3 -m arkitect.harness.progress`, whose `set` refuses a claim
the build does not prove.

trace.md5 is written by `python3 -m arkitect.lib.verify.gate accept` alone, after someone has
looked at what moved. The PDFs and DXFs in the checkout are the issued deliverables, which
a build writes and the merger regenerates; a render to look at goes outside the checkout
(`gate.py render`).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402


PROGRESS = ("progress.json is written by `python3 -m arkitect.harness.progress set / add / drop` and "
            "nothing else: `set` refuses a claim the build does not prove, and a hand edit would "
            "skip exactly that.")


REVIEW = ("review.json is written by `python3 -m arkitect.harness.review ingest / set` and nothing else: "
          "`set ... fixed` refuses unless the finding's sheet has changed since it was found.")


def check(path, root):
    """The reason an edit of `path` is refused, or None."""
    if not path:
        return None
    path = os.path.realpath(path)
    if os.path.basename(path) == 'trace.md5':
        return ("trace.md5 is written by `python3 -m arkitect.lib.verify.gate accept` and nothing else: "
                "review what moved first (`gate.py`, `gate.py render --moved`), then accept, and "
                "name the sheets it prints in the commit message.")
    root = os.path.realpath(root) if root else None
    inside = root and (path == root or path.startswith(root + os.sep))
    if inside and os.path.basename(path) == 'progress.json':
        return PROGRESS
    if inside and os.path.basename(path) == 'review.json':
        return REVIEW
    if inside and path.lower().endswith(('.pdf', '.dxf')):
        return ("the PDFs and DXFs in the checkout are deliverables a build writes; they are "
                "never edited by hand. To look at a sheet, render it outside the checkout: "
                "`python3 -m arkitect.lib.verify.gate render --sheets A-101`.")
    return None


def main():
    data = hooklib.read_input()
    ti = data.get('tool_input') or {}
    path = ti.get('file_path') or ti.get('notebook_path') or ''
    why = check(path, hooklib.repo_root(data.get('cwd')))
    if why:
        print('Blocked by .claude/hooks/guard_write.py: ' + why, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
