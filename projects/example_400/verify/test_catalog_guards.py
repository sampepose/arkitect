"""400 Oak against arkitect/harness/catalog.py: a complete set runs every guard the catalog lists.

arkitect/harness/progress.py's probe runs Oak's build under a profiler; every guard of every catalog
sheet must have been CALLED, except the zoning fit, which Oak checks in its tests
(test_zoning_fit.py) rather than its build. A guard no real set ever runs would leave its
sheet unable to pass. Moved here from arkitect/harness/verify/ in phase 1 of the public release: the
engine's own tests may not lean on a project the public engine does not ship.
"""
import unittest

from arkitect.harness import catalog, progress


class CatalogGuardTests(unittest.TestCase):

    def test_a_real_set_runs_every_guard(self):
        ran = set(progress.probe('example_400')['ran'])
        guards = {g for _n, _t, gs in catalog.SHEETS for g in catalog.guards_for(gs, 'columbus')}
        self.assertEqual(guards - ran, {'arkitect.codes.columbus.fit'})


if __name__ == '__main__':
    unittest.main()
