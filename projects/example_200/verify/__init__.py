"""200 EXAMPLE AVE's own tests. Both the isolation and the tests every project needs are
arkitect/harness/testkit.py's, imported rather than copied."""
import os

from arkitect.harness.testkit import isolation

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
enter, leave = isolation(PROJ)
