"""src/faces.py: what an elevation face carries is read from the models, and it stands clear."""
import io
import contextlib
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class ParcelFaceTests(unittest.TestCase):

    def test_the_parcel_face_carries_every_cap_and_box(self):
        """The designer, 2026-09-15: RH-1, EF-1A and EF-2 are scheduled on this wall and EM-1,
           HP-2 and HP-3 stand on it. GM-1 left with the fuel gas."""
        from src.faces import face_boxes, face_terms
        self.assertEqual(sorted(t.mark for t in face_terms(1, 'ADJACENT-PARCEL WALL')), ['EF-1A', 'EF-2', 'RH-1'])
        self.assertEqual(sorted(b.mark for b in face_boxes(1, 'ADJACENT-PARCEL WALL')), ['EM-1', 'HP-2', 'HP-3'])

    def test_meter_positions(self):
        from src.faces import face_boxes
        n = {b.mark: b.positions for b in face_boxes(1, 'ADJACENT-PARCEL WALL')}
        self.assertEqual((n['EM-1'], n['HP-2']), (4, 0))
        self.assertNotIn('GM-1', n)

    def test_building2_parcel_face_carries_its_boxes(self):
        """A-203 draws Building 2's parcel face, so its three boxes have heights and
           check_faces() holds them clear of its openings."""
        from src.faces import DRAWN_BOXES, face_boxes, face_terms
        self.assertIn((2, 'ADJACENT-PARCEL WALL'), DRAWN_BOXES)
        n = {b.mark: b.positions for b in face_boxes(2, 'ADJACENT-PARCEL WALL')}
        self.assertEqual(n, {'HP-4': 0, 'HP-5': 0, 'EM-3': 3})
        self.assertEqual(face_terms(2, 'ADJACENT-PARCEL WALL'), [])

    def test_building2_parcel_boxes_are_one_centred_group(self):
        """The designer, 2026-09-16: the boxes stand as one composed group centered between the two
           windows, at Building 1's heights, rather than HP-4 tucked into the corner beside
           the W-C."""
        from src import sitework as S
        from src.faces import face_boxes
        boxes = sorted(face_boxes(2, 'ADJACENT-PARCEL WALL'), key=lambda b: b.lo)
        self.assertEqual([b.mark for b in boxes], ['HP-4', 'HP-5', 'EM-3'])
        ops = sorted((a-S.B2_Y0, b-S.B2_Y0) for a, b, _m in S.B2_WALL_OPEN)
        before = max(hi for lo, hi in ops if hi <= boxes[0].lo+1e-9)
        after = min(lo for lo, hi in ops if lo >= boxes[-1].hi-1e-9)
        self.assertAlmostEqual(boxes[0].lo-before, after-boxes[-1].hi, places=6)
        for a, b in zip(boxes, boxes[1:]):
            self.assertAlmostEqual(b.lo-a.hi, S.HP_PAIR_GAP, places=6)
        self.assertEqual(S.SVC_Z['HP-4'], S.SVC_Z['HP-2'])
        self.assertEqual(S.SVC_Z['EM-3'], S.SVC_Z['EM-1'])

    def test_check_faces_passes(self):
        from src.faces import check_faces
        with contextlib.redirect_stdout(io.StringIO()):
            check_faces()

    def test_an_outdoor_unit_under_the_c101_minimum_fails(self):
        """C-101 note 5b's 4" above grade is the only thing left setting an outdoor
           unit's height now that no gas leg runs under one."""
        from arkitect.lib.units import IN
        from src import sitework
        from src.faces import face_violations
        keep = dict(sitework.SVC_Z)
        try:
            sitework.SVC_Z['HP-2'] = (IN(2), sitework.HP_H)
            bad, _ = face_violations()
        finally:
            sitework.SVC_Z.clear(); sitework.SVC_Z.update(keep)
        self.assertTrue(any('HP-2' in b and 'above grade' in b for b in bad), bad)

    def test_a_box_with_no_height_fails(self):
        from src import sitework
        from src.faces import face_boxes
        keep = dict(sitework.SVC_Z)
        try:
            del sitework.SVC_Z['EM-1']
            with self.assertRaises(KeyError):
                face_boxes(1, 'ADJACENT-PARCEL WALL')
        finally:
            sitework.SVC_Z.clear(); sitework.SVC_Z.update(keep)


if __name__ == '__main__':
    unittest.main()
