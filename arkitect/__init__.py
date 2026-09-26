"""arkitect: residential permit sets generated from a model and checked against the code.

    arkitect.lib      the drawing engine: sheets, plans, geometry, the trace and the gate
    arkitect.codes    the code rules, each with its citation
    arkitect.harness  the tools that start, advance, review and record a project
"""

# The engine's version: what a project records when its drawing is accepted, and what an
# upgrade is proposed against (arkitect/lib/verify/gate.py). Raise
# the minor number for anything that can move a sheet, the patch number for anything that
# cannot, and tag the commit vX.Y.Z.
__version__ = '0.6.9'
