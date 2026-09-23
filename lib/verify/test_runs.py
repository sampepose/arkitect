"""lib/model/runs.py: runs and rectangles in plan feet."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from lib.model import runs


class RunsTests(unittest.TestCase):

    def test_points_on_paths(self):
        path = [(0.0, 0.0), (0.0, 10.0), (5.0, 10.0)]
        self.assertTrue(runs.on_path((0.0, 4.0), path)); self.assertTrue(runs.on_path((5.0, 10.0), path))
        self.assertFalse(runs.on_path((1.0, 4.0), path))
        self.assertAlmostEqual(runs.along(path, (2.0, 10.0)), 12.0)
        with self.assertRaises(ValueError):
            runs.along(path, (9.0, 9.0))

    def test_parallel_and_crossing(self):
        self.assertEqual(runs.parallel((0, 0), (0, 10), (1, 5), (1, 20)), (True, 1.0))
        self.assertEqual(runs.parallel((0, 0), (0, 10), (1, 11), (1, 20)), (False, 1.0))     # no overlap
        self.assertEqual(runs.parallel((0, 0), (0, 10), (0, 5), (5, 5)), (False, None))      # perpendicular
        self.assertEqual(runs.crossing((0, 0), (0, 10), (-1, 5), (5, 5)), (0, 5))
        self.assertIsNone(runs.crossing((0, 0), (0, 10), (1, 5), (5, 5)))
        self.assertAlmostEqual(runs.seg_rect_dist((0, 0), (0, 10), (2.0, 3.0, 1.0, 1.0)), 2.0)
        self.assertAlmostEqual(runs.seg_rect_dist((0, 5), (10, 5), (2.0, 3.0, 1.0, 1.0)), 1.0)
        self.assertEqual(runs.seg_rect_dist((0, 3.5), (10, 3.5), (2.0, 3.0, 1.0, 1.0)), 0.0)

    def test_rectangles_and_lengths(self):
        r = (2.0, 3.0, 4.0, 1.0)
        self.assertEqual(runs.length([(0, 0), (0, 3), (4, 3)]), 7.0)
        self.assertTrue(runs.in_rect((2.0, 3.0), r)); self.assertFalse(runs.in_rect((1.9, 3.0), r))
        self.assertEqual(runs.pt_rect_dist((4.0, 3.5), r), 0.0)
        self.assertAlmostEqual(runs.pt_rect_dist((9.0, 8.0), r), 5.0)             # 3 across, 4 up
        self.assertEqual(runs.grow(r, 0.5), (1.5, 2.5, 5.0, 2.0))
        self.assertTrue(runs.rects_overlap(r, (5.0, 3.5, 3.0, 3.0)))
        self.assertFalse(runs.rects_overlap(r, (6.0, 3.0, 1.0, 1.0)))             # sharing an edge is not overlapping
        self.assertAlmostEqual(runs.pt_seg_dist((3.0, 4.0), (0.0, 0.0), (6.0, 0.0)), 4.0)
        self.assertAlmostEqual(runs.pt_seg_dist((9.0, 4.0), (0.0, 0.0), (6.0, 0.0)), 5.0)   # past the end

    def test_points_walks_a_run_end_to_end(self):
        pts = list(runs.points([(0, 0), (0, 1), (2, 1)], step=0.5))
        self.assertEqual(pts[0], (0, 0)); self.assertEqual(pts[-1], (2, 1))
        self.assertTrue(all(abs(b[0]-a[0])+abs(b[1]-a[1]) <= 0.5+1e-9 for a, b in zip(pts, pts[1:])))


if __name__ == '__main__':
    unittest.main()
