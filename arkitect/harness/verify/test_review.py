"""arkitect/harness/review.py: the brief is the house style as it stands, the tiles cover every inch of
a sheet with overlap, and a finding is a task that cannot be closed by a note."""
import json
import os
import tempfile
import unittest
from unittest import mock

from arkitect.harness import review as R
from arkitect.lib import workspace

GOOD = {'sheet': 'A-101', 'where': 'tile r1c1 -- the entry', 'category': 'fit',
        'severity': 'major', 'finding': 'The D-1 and D-6 swings cross in the entry.',
        'evidence': 'two arcs meet below the D-6 tag', 'suggest': 'swing D-6 into the closet',
        'verdict': 'CONFIRMED', 'verdict_reason': 'both arcs visible on r1c1'}


class BriefTests(unittest.TestCase):

    def test_the_house_style_is_read_live_from_claude_md(self):
        style = R.house_style()
        self.assertIn('American spelling on every sheet', style)
        self.assertIn('Notes instruct. They do not argue.', style)
        self.assertNotIn('## Constraints', style)          # one section, not the file

    def test_the_brief_lists_every_image_and_the_output_contract(self):
        index = {'sheets': {'A-101': {'whole': '/r/A-101/whole.png',
                                      'tiles': ['/r/A-101/tile-r1c1.png'], 'md5': 'x'}}}
        text = R.brief('example_100', index, workspace.ENGINE)     # the engine's own example
        self.assertIn('100 EXAMPLE ST', text)
        self.assertIn('/r/A-101/tile-r1c1.png', text)
        for c in R.CATEGORIES:
            self.assertIn('"%s"' % c, text)
        self.assertNotIn('.py', text.split('## House style')[0])   # no path into the source


class TileTests(unittest.TestCase):

    def test_the_tiles_cover_the_sheet_and_overlap(self):
        import pymupdf
        doc = pymupdf.open()
        page = doc.new_page(width=24*72, height=18*72)
        tiles = R._tiles(page)
        self.assertEqual(len(tiles), R.TILE_GRID[0]*R.TILE_GRID[1])
        for x in range(0, 24*72+1, 36):          # every half inch across and down
            for y in range(0, 18*72+1, 36):
                self.assertTrue(any(r.x0 <= x <= r.x1 and r.y0 <= y <= r.y1 for _l, r in tiles))
        r11, r12 = tiles[0][1], tiles[1][1]
        self.assertGreater(r11.x1-r12.x0, 0.5*72)          # neighbours overlap


class FindingTests(unittest.TestCase):

    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = t.name
        os.makedirs(os.path.join(self.root, 'projects', 'demo'))
        self.index = {'commit': 'abc1234', 'sheets': {'A-101': {'md5': 'm1'}, 'A-102': {'md5': 'm2'}}}

    def ingest(self, *fs):
        return R.ingest('demo', list(fs), self.index, self.root)

    def test_a_verified_finding_becomes_an_open_task_with_its_sheets_fingerprint(self):
        added, dups = self.ingest(GOOD)
        self.assertEqual(dups, [])
        rec = R.load('demo', self.root)['findings'][0]
        self.assertEqual((rec['id'], rec['status'], rec['sheet_md5'], rec['commit']),
                         ('R-001', 'open', 'm1', 'abc1234'))

    def test_an_unverified_or_malformed_batch_is_refused_whole(self):
        with self.assertRaises(ValueError):
            self.ingest(GOOD, dict(GOOD, verdict=None, finding='something else'))
        with self.assertRaises(ValueError):
            self.ingest(dict(GOOD, category='vibes'))
        self.assertEqual(R.load('demo', self.root)['findings'], [])

    def test_a_rejected_finding_is_kept_so_it_is_not_reported_again(self):
        self.ingest(dict(GOOD, verdict='REJECTED'))
        self.assertEqual(R.load('demo', self.root)['findings'][0]['status'], 'rejected')
        added, dups = self.ingest(dict(GOOD, finding='The D-1 and D-6 swings cross in the entry!'))
        self.assertEqual((len(added), dups[0][1]), (0, 'R-001'))

    def test_the_same_words_on_another_sheet_are_not_a_duplicate(self):
        self.ingest(GOOD)
        added, _d = self.ingest(dict(GOOD, sheet='A-102'))
        self.assertEqual(added[0]['id'], 'R-002')

    def test_fixed_is_refused_until_the_sheet_changes(self):
        self.ingest(GOOD)
        with mock.patch.object(R, 'fingerprints', return_value={'A-101': 'm1'}):
            with self.assertRaises(ValueError):
                R.set_status('demo', 'R-001', 'fixed', root=self.root)
        with mock.patch.object(R, 'fingerprints', return_value={'A-101': 'm1-changed'}):
            self.assertEqual(R.set_status('demo', 'R-001', 'fixed', root=self.root)['status'], 'fixed')

    def test_wontfix_and_rejected_need_a_reason(self):
        self.ingest(GOOD)
        for st in ('wontfix', 'rejected'):
            with self.assertRaises(ValueError):
                R.set_status('demo', 'R-001', st, root=self.root)
        self.assertEqual(R.set_status('demo', 'R-001', 'wontfix', note='D-004 waits on the designer',
                                      root=self.root)['notes'], 'D-004 waits on the designer')

    def test_a_finding_on_a_sheet_the_build_does_not_bind_is_refused(self):
        with self.assertRaises(ValueError):
            self.ingest(dict(GOOD, sheet='Z-999'))


class PrepareTests(unittest.TestCase):

    def test_prepare_renders_one_real_sheet_whole_and_tiled(self):
        """On the example project the engine ships with."""
        with tempfile.TemporaryDirectory() as out:
            d = R.prepare('example_100', ['G-001'], out=out, root=workspace.ENGINE)
            with open(os.path.join(d, 'index.json')) as fh:
                idx = json.load(fh)
            s = idx['sheets']['G-001']
            self.assertEqual(len(s['tiles']), 6)
            self.assertTrue(all(os.path.exists(p) for p in [s['whole']] + s['tiles']))
            self.assertTrue(os.path.exists(os.path.join(d, 'brief.md')))
            self.assertEqual(len(s['md5']), 32)


if __name__ == '__main__':
    unittest.main()
