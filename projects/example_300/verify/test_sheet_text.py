"""This set's drawn text, read through lib/verify/sheet_text.py: no string stands on another,
   every sheet cited is bound, and every 'SHEET NOTE n' citation finds its note.

   Added 2026-09-18, after the same sweep on 400 Oak found a note printed over a detail's
   label — and then found the same fault here on S-101, and two working-space captions printed
   on top of each other on A-101 and A-102."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
BUILD = os.path.join(PROJ, 'build.py')
PAGES = {}

# No overlap is excused. The one that was — Unit 1's Bedroom 1 closet / linen caption under the
# 5'-1" of the dimension row beside it, A-101 and A-102 — went when that row dropped the segment
# the caption already gives. An entry here is (sheet, string, string) and must still occur.
KNOWN = set()


def setUpModule():
    from lib.verify import sheet_text as st
    PAGES.update(st.read(BUILD))


class SheetTextTests(unittest.TestCase):

    def test_the_whole_set_was_read(self):
        self.assertEqual(len(PAGES), 28)
        self.assertTrue(all(len(v) > 20 for v in PAGES.values()))

    def test_no_string_stands_on_another(self):
        from lib.verify import sheet_text as st
        found = {(no, a, b) for no, items in PAGES.items() for _area, a, b in st.overlaps(items)}
        self.assertEqual(sorted(found-KNOWN), [])
        self.assertEqual(sorted(KNOWN-found), [], 'an excused overlap is gone: take it off the list')

    def test_every_sheet_cited_is_bound(self):
        from lib.verify import sheet_text as st
        self.assertEqual(st.sheet_references(PAGES), [])

    def test_every_note_cited_is_printed(self):
        from lib.verify import sheet_text as st
        self.assertEqual(st.note_references(PAGES), [])


if __name__ == '__main__':
    unittest.main()
