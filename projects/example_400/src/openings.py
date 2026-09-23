"""Window marks — the three units this project uses, in one place.

The elevations, the glazing percentages, the egress schedule and the stair-soffit check
all have to read the same numbers, and both buildings draw from the same three marks.
Door marks are still in build.py with the schedule that prints them.
"""

# ---------------- window marks ----------------
# One place for the three marks, because the elevations, the glazing percentages, the
# egress schedule and the stair-soffit check all have to read the same numbers.
# W-A is the only egress unit. Its 3'-0" x 6'-0" is the frame the plans and elevations
# draw; the net clear opening a sash leaves belongs to the product, so the set states no
# opening for it — only the minimums below, which A-602 and G-001 8a hold every product
# to with the manufacturer's data. Head stays at 8'-0", so the sill is 2'-0".
WIN_W    = {'A':3.0, 'B':3.0, 'C':5.0, 'D':3.0}          # nominal unit width
WIN_GEOM = {'A':(2.0,6.0), 'B':(4.0,4.0), 'C':(4.0,4.0), 'D':(4.0,4.0)}   # sill above floor, height
# W-D is W-B's frame, FIXED: over the house's stair, where no one can reach a sash (400 Oak).
WIN_FIXED = ('D',)
WIN_SF   = {m:WIN_W[m]*WIN_GEOM[m][1] for m in WIN_W}
WIN_HEAD = {m:sum(WIN_GEOM[m]) for m in WIN_GEOM}
assert len({WIN_HEAD[m] for m in WIN_HEAD})==1, "window heads no longer all align"

# The W-A sill below which A-001 5b has every Level 2 W-A take an opening limiting device.
# That is this set's rule, not Ohio's: RCO 312.2 requires no window fall protection and
# governs a device only "when provided" — ASTM F2090, 312.2.1; release for escape,
# 312.2.2.2. The IRC's 24" sill / 72" above grade trigger is not in the Ohio text.
WIN_FALL_MIN = 2.0
