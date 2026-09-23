"""RCO 310.2.1, the emergency escape and rescue opening: the net clear area, width and height a
bedroom's window must give, and the check that a drawn frame, opened as a double hung, can give them.
It proves a frame is not too small, never that a product meets the minimums.
"""
from lib.units import IN, fmt, inches


# The net clear opening every W-A product shall give by normal operation from inside,
# RCO 310.2.1, and the most the bottom of that opening may stand above the floor,
# 310.2.2. All three opening figures at once: 20" x 24" is only 3.3 SF. The 5 SF of
# 310.2.1's grade-floor exception is not taken — W-A is one product in all twelve
# bedrooms, on both levels, so every one carries 5.7 SF.
EGRESS_MIN_SF   = 5.7


EGRESS_MIN_W    = IN(20)


EGRESS_MIN_H    = IN(24)


EGRESS_MAX_SILL = IN(44)


def check_egress_window(*, win_geom, win_w):
    """The drawn W-A frame can host the minimums as a double hung, and its sill is within
       RCO 310.2.2. One sash opens at most the unit's width by half its height, which
       bounds every product from above: this proves the frame is not too small for the
       requirement, never that a product meets it. The product data does that."""
    w, (sill, h) = win_w['A'], win_geom['A']
    ow, oh = w, h/2.0
    print("   W-A EGRESS   PRODUCT MINIMUM %s SF, %s W, %s H;  %s x %s DOUBLE HUNG OPENS AT MOST %s x %s = %.1f SF;  SILL %s"
          %(EGRESS_MIN_SF, inches(EGRESS_MIN_W), inches(EGRESS_MIN_H), fmt(w), fmt(h),
            inches(ow), inches(oh), ow*oh, fmt(sill)))
    assert ow >= EGRESS_MIN_W-1e-9, "W-A is narrower than the net clear width every product must give"
    assert oh >= EGRESS_MIN_H-1e-9, "a W-A sash cannot open the net clear height every product must give"
    assert ow*oh >= EGRESS_MIN_SF-1e-9, "a W-A sash cannot open the net clear area every product must give"
    assert sill <= EGRESS_MAX_SILL+1e-9, "W-A's sill is over the 44\" of RCO 310.2.2"
