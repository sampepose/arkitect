"""Feet and inches, as this trade writes them.

The most primitive thing in the library: a plan draws them, a schedule prints them and
a note quotes them, so it sits below both the page and the text on it.
"""
import math


def IN(n):
    """n inches, expressed in FEET — the project's one length unit.

    Everything in the model is feet: the regrid's 1/96 grid, PlanDraw.X/Y, the scales
    in points per foot, and fmt() and inches() below, which are the only two things that
    turn a length into words. A module that keeps its own numbers in inches does not
    avoid the conversion, it just moves it to everyone who reads it. Two used to:
    src/levels.py made build.py write levels.F2_PLATE/12 at 48 call sites, and Unit 1's
    stair made it write TR_IN/12.0 at 8 more. Both are feet now, and so is every
    dimension in src/. Points appear only inside arkitect/lib/draw.

    So an inch dimension is written where it is defined and in feet from then on:

        EXT_STUD = IN(5.5)      # a 2x6
        FF2      = IN(126)      # upper finished floor

    It divides rather than multiplying by a stored 1/12 because 5.5/12.0 is exactly what
    this code has always computed, and the golden-master trace compares drawing calls to
    a millionth of a point."""
    return n / 12.0


def fmt(v, sep="-"):
    """Feet and inches to the nearest 1/8 inch — the grid the plan is laid out on.
       Whole inches cannot state a real assembly: the grouping separation is 9-1/4 in
       stud to stud and used to print as 0'-11".

       `sep` joins the whole inches to the fraction. The set hyphenates (10'-1-3/4");
       the labels inside Unit 1's plans came from the supplied study and space it
       (10'-1 3/4"), which is the only thing that made them a separate formatter."""
    if round(v*96)<0: return '-'+fmt(-v, sep)     # the sign ahead of the figure, never inside it
    f=int(v+1e-6); e=int(round((v-f)*96))          # eighths of an inch
    if e>=96: f,e = f+1, e-96
    w,r = divmod(e,8)
    if r==0: return f"{f}'-{w}\""
    d=math.gcd(r,8)
    return f"{f}'-{w}{sep}{r//d}/{8//d}\""


def inches(v, sep="-"):
    """Inches only, to the nearest 1/8. For a clearance small enough that the feet
       get in the way of reading it: a code minimum is written 15", so the dimension
       demonstrating it should read 16-1/2", not 1'-4-1/2". `sep` as in fmt()."""
    e=int(round(v*96))                             # eighths of an inch
    if e<0: return '-'+inches(-v, sep)             # divmod floors a negative: -1/2" read -1-1/2"
    w,r = divmod(e,8)
    if r==0: return f'{w}"'
    d=math.gcd(r,8)
    if w==0: return f'{r//d}/{8//d}"'          # 1/2", never 0-1/2"
    return f'{w}{sep}{r//d}/{8//d}"'


def inches32(v, sep="-"):
    """Inches to the nearest 1/32, for a divided rise whose 1/16 would not multiply back:
       120-1/2" over 15 risers is 8.03", which inches16() prints 8-1/16" -- and 15 of those
       are 120-15/16". Print the total rise beside it; that is the figure that controls."""
    n=int(round(v*384))                            # thirty-seconds of an inch
    if n<0: return '-'+inches32(-v, sep)
    w,r = divmod(n,32)
    if r==0: return f'{w}"'
    d=math.gcd(r,32)
    if w==0: return f'{r//d}/{32//d}"'
    return f'{w}{sep}{r//d}/{32//d}"'


def inches16(v, sep="-"):
    """Inches to the nearest 1/16, for a figure a divided rise makes: 121" over 15 risers is
       8.07", which inches() would print 8-1/8", overstating every riser."""
    n=int(round(v*192))                            # sixteenths of an inch
    if n<0: return '-'+inches16(-v, sep)
    w,r = divmod(n,16)
    if r==0: return f'{w}"'
    d=math.gcd(r,16)
    if w==0: return f'{r//d}/{16//d}"'
    return f'{w}{sep}{r//d}/{16//d}"'
