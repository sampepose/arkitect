"""The sheet renderers — one module per sheet, or per group that shares its drawing.

A renderer draws ONE sheet and knows nothing about the others: not which document it
belongs to, not what order the set is bound in, not where the file goes. build.py owns
all three, and a renderer that reaches for any of them has taken on a job that belongs
in the one place the whole set can be seen at once.

They share `common.py` — the canvas stand-in and the drawing-area corners — and nothing
else. Project geometry two sheets both draw lives in src/ with the rest of the model
(the site constants in src/sitework.py, the opening lists in src/schedules.py), because
it is the lot, not the drawing of it.
"""
