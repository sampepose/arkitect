"""200 EXAMPLE AVE — the title block and the output names. Everything else it knows comes
from intake.json through src/sitework.py."""
from arkitect.codes.ohio.columbus import titleblock
from src.sitework import INTAKE

ADDRESS = INTAKE["address"]
TITLEBLOCK = titleblock(INTAKE)

PDF_OUT = "200-Example-permit-set.pdf"
ZONING_OUT = "200-Example-zoning-site-plan.pdf"
DXF_OUT = "200-Example-floor-plans.dxf"
