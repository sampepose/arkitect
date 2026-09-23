"""The few printed lines whose WORDING changes what the set means.

Most printed text is prose and does not want a test. A handful of lines are not prose:
they tell a builder how to read every other number on the drawings, or they identify the
property. Those had nothing holding them. "DIMENSIONS TO FACE OF STUD" became "TO FACE
OF FINISH" -- one word, changing how every dimension in the set is read -- and 425 tests,
the build, pyflakes and the trace all passed with one line different. So did moving the
project's ZIP code across all 28 pages, though test_titleblock.py pins the contractor
block hard.

This file is deliberately short. It pins the lines that are load-bearing, not the lines
that are long.
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from src import project
from src.sheets.a001 import PLAN_NOTES


def _note(label):
    hits = [n for n in PLAN_NOTES if n.startswith(label)]
    assert len(hits) == 1, 'A-001 note %r appears %d times' % (label, len(hits))
    return hits[0]


class DimensionConventionTests(unittest.TestCase):
    """A-001 note 1 is the key to the whole set: it says what every dimension measures
       to. Get it wrong and every figure on every sheet is read against the wrong
       face."""

    def test_dimensions_are_to_face_of_stud(self):
        n = _note('1.')
        self.assertIn('FACE OF STUD', n)
        self.assertNotIn('FACE OF FINISH', n)

    def test_the_set_says_not_to_scale_it(self):
        self.assertIn('DO NOT SCALE', _note('1.'))

    def test_interior_strings_are_clear_dimensions_stud_to_stud(self):
        """Note 1a. The distinction between a clear dimension and an overall one is the
           difference between a room that fits and one that does not."""
        n = _note('1a.')
        self.assertIn('CLEAR DIMENSIONS', n)
        self.assertIn('FACE OF STUD TO FACE OF STUD', n)


class IdentityTests(unittest.TestCase):
    """Who and where. A permit set that names the wrong parcel is not this set."""

    def test_the_title_block_names_the_property_once_and_correctly(self):
        lines = [ln for _head, body in project.TITLEBLOCK for ln in body]
        joined = ' | '.join(lines)
        self.assertIn('300', joined)
        self.assertIn('ELM', joined.upper())
        self.assertIn('COLUMBUS, OHIO 43200', joined)

    def test_the_parcel_number_is_the_one_on_the_deed(self):
        lines = ' '.join(ln for _h, b in project.TITLEBLOCK for ln in b)
        self.assertIn('010-000300-00', lines)

    def test_there_is_exactly_one_zip_code_in_the_title_block(self):
        """It prints on all 28 pages; a second one means two addresses."""
        lines = ' '.join(ln for _h, b in project.TITLEBLOCK for ln in b)
        zips = set(re.findall(r'\bOHIO (\d{5})\b', lines))
        self.assertEqual(zips, {'43200'}, zips)


class HouseStyleTests(unittest.TestCase):
    """Two rules CLAUDE.md states, held against the notes that are easiest to break
       them in."""

    BRITISH = ('STOREY', 'CENTRELINE', 'VAPOUR', 'LICENCE', 'LABELLED', 'FIBRE',
               'ALUMINIUM', 'GALVANISED', 'COLOUR', 'GREY ', 'CENTRED')

    def test_the_plan_notes_are_in_american_spelling(self):
        for n in PLAN_NOTES:
            for word in self.BRITISH:
                self.assertNotIn(word, n.upper(), '%r in %r' % (word, n[:60]))

    def test_no_dwelling_is_called_a_flat(self):
        for n in PLAN_NOTES:
            self.assertNotIn('FLATS', n.upper(), n[:60])
            self.assertNotIn('TWO-FLAT', n.upper(), n[:60])

    def test_RCO_citations_drop_the_IRC_R_prefix(self):
        """'RCO 311.7', not 'RCO R311.7'. IRC R313 keeps its R because it names the
           IRC."""
        for n in PLAN_NOTES:
            for hit in re.findall(r'RCO\s+R\d', n):
                self.fail('%r in %r' % (hit, n[:60]))

    def test_the_notes_instruct_rather_than_argue(self):
        for n in PLAN_NOTES:
            up = n.upper()
            for phrase in ('NOT A PREFERENCE', 'NOT A DRAFTING ERROR', 'BY DESIGN',
                           'IS INTENTIONAL'):
                self.assertNotIn(phrase, up, '%r in %r' % (phrase, n[:60]))

    def test_the_notes_carry_no_revision_history(self):
        for n in PLAN_NOTES:
            up = n.upper()
            for phrase in ('PREVIOUSLY SCHEDULED', 'IS DELETED', 'NO LONGER AN',
                           'FORMERLY', 'SUPERSEDED'):
                self.assertNotIn(phrase, up, '%r in %r' % (phrase, n[:60]))

    def test_no_internal_vocabulary_reaches_a_note(self):
        """'THE MIRROR' is a module in this repo and means nothing on a sheet."""
        for n in PLAN_NOTES:
            up = n.upper()
            for word in ('THE MIRROR', '.PY', 'REGRID', 'CHECK_MODEL'):
                self.assertNotIn(word, up, '%r in %r' % (word, n[:60]))


class LabelOrderTests(unittest.TestCase):

    def test_the_A001_note_labels_ascend(self):
        """Cross-references run between sheets, so the ENTRIES get reordered and never
           the labels. A label out of order means a citation elsewhere now points at
           different text."""
        def key(lab):
            m = re.match(r'(\d+)([a-z]*)', lab)
            return (int(m.group(1)), m.group(2))
        labels = [re.match(r'(\d+[a-z]*)\.', n).group(1)
                  for n in PLAN_NOTES if re.match(r'\d+[a-z]*\.', n)]
        self.assertEqual(labels, sorted(labels, key=key), labels)

    def test_no_label_appears_twice(self):
        labels = [re.match(r'(\d+[a-z]*)\.', n).group(1)
                  for n in PLAN_NOTES if re.match(r'\d+[a-z]*\.', n)]
        dupes = {l for l in labels if labels.count(l) > 1}
        self.assertFalse(dupes, dupes)


if __name__ == '__main__':
    unittest.main()
