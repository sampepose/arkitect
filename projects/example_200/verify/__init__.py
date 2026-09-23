"""200 EXAMPLE AVE's own tests. Both the isolation and the tests every project needs are
harness/testkit.py's, imported rather than copied."""
import os

from harness.testkit import isolation

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
enter, leave = isolation(PROJ)
