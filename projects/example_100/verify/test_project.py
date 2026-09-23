"""100 EXAMPLE ST: the drawing against trace.md5, its text against arkitect/lib/verify/sheet_text.py,
and progress.json against what the build proves."""
import unittest

from arkitect.harness.testkit import ProjectTests
from projects.example_100.verify import PROJ, enter, leave


class Example100Tests(ProjectTests, unittest.TestCase):
    PROJ = PROJ
    ENTER = staticmethod(enter)
    LEAVE = staticmethod(leave)


if __name__ == "__main__":
    unittest.main()
