"""200 EXAMPLE AVE: the drawing against trace.md5, its text against lib/verify/sheet_text.py,
and progress.json against what the build proves."""
import unittest

from harness.testkit import ProjectTests
from projects.example_200.verify import PROJ, enter, leave


class Example200Tests(ProjectTests, unittest.TestCase):
    PROJ = PROJ
    ENTER = staticmethod(enter)
    LEAVE = staticmethod(leave)


if __name__ == "__main__":
    unittest.main()
