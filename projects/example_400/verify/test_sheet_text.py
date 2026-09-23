"""400 Oak's drawn text, read through lib/verify/sheet_text.py: no string stands on another,
   every sheet cited is bound, and every 'SHEET NOTE n' citation finds its note."""
import os
import unittest

from projects.example_400.verify import enter, leave

BUILD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build.py')
PAGES = {}

# Three 4 pt lines under the Unit 3 stair's stoop on A-202 stand at their own leading and read
# clearly; their boxes touch. Nothing else is excused.
TIGHT = {('A-202', 'CONCRETE STOOP'), ('A-202', 'ONE 7-3/4" STEP DOWN')}


def setUpModule():
    enter()
    from lib.verify import sheet_text as st
    PAGES.update(st.read(BUILD))


def tearDownModule():
    leave()


class SheetTextTests(unittest.TestCase):

    def test_the_whole_set_was_read(self):
        self.assertEqual(len(PAGES), 25)
        self.assertTrue(all(len(v) > 20 for v in PAGES.values()))

    def test_no_string_stands_on_another(self):
        from lib.verify import sheet_text as st
        bad = [(no, a[:50], b[:50]) for no, items in PAGES.items() for _area, a, b in st.overlaps(items)
               if not any(no == s and (a.startswith(t) or b.startswith(t)) for s, t in TIGHT)]
        self.assertEqual(bad, [])

    def test_every_sheet_cited_is_bound(self):
        from lib.verify import sheet_text as st
        self.assertEqual(st.sheet_references(PAGES), [])

    def test_every_note_cited_is_printed(self):
        from lib.verify import sheet_text as st
        self.assertEqual(st.note_references(PAGES), [])


if __name__ == '__main__':
    unittest.main()
