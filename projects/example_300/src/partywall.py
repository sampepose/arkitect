"""W4's plan dimensions. A leaf: it imports nothing, so the building model, the separation
model, the roof and A-301 can all read it without a cycle. src/separation.py owns what W4 IS
and checks it; these four figures are only how thick it draws and how much plan it takes.
They lived in lib/model/regrid.py until 2026-09-18, where a second project with no party
wall carried them."""

# W4, the grouping separation: two independent 1-hour UL U305 walls back to back — W4A,
# Unit 1's, and W4B, Units 2 / 3' — each 2x4 at 16" o.c. with one 5/8" UL Type SCX layer
# each face. The inner layers touch; 9-1/2" finished.
W4_STUD   = 3.5/12.0     # one wall's 2x4 stud row
W4_CORE   = 1.25/12.0    # the two inner 5/8" layers, one per wall, between the stud rows
SEP_STUD  = W4_STUD+W4_CORE+W4_STUD   # stud face to stud face across both walls, 8-1/4"

W4_FACE   = 0.625/12.0   # one 5/8-inch SCX layer on EACH unit face; 9-1/2 inches finished
