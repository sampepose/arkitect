"""Code knowledge: what the Residential Code of Ohio, the OPC, the NEC and the Columbus
City Code require, as data.

Not the drawing engine (that is lib/, which may not know which city it is drawing for)
and not any one lot (that is projects/). A module here is true of every project in the
jurisdiction it names and of no particular one.

Nothing here may import a project. lib/verify/test_neutrality.py enforces it.
"""
