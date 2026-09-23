"""Files a drawing needs that are not code.

A north arrow is not project data — every site plan has one — so it lives with the
library rather than beside one lot's build script. `path()` finds it however the
package was installed, which is what stops a sheet from depending on the working
directory it was run from.
"""
import os

from reportlab.lib.utils import ImageReader

HERE = os.path.dirname(os.path.abspath(__file__))
_READERS = {}


def path(name):
    """Absolute path to a library asset."""
    p = os.path.join(HERE, name)
    assert os.path.exists(p), "no such library asset: %s" % name
    return p


def image(name):
    """A library image, as an ImageReader, for drawImage().

    NOT the path, and the difference decides whether the issued PDF is reproducible.
    reportlab names the XObject it embeds by digesting what it is handed: given an
    ImageReader it digests the image's CONTENT, and given a filename it digests the
    FILENAME. Passing a path therefore wrote the absolute location of this checkout
    into the drawing -- building the same commit at a different path produced a
    different PDF, with the XObject going from FormXob.cd2c7478... to
    FormXob.0b255e81... and nothing else about the set changed.

    That is not a cosmetic difference. It means the deliverable could not be
    reproduced from its own commit unless the repository sat in the same directory it
    was issued from, which is the reproducibility that pinning reportlab was for; and
    with two projects it would mean two different names for one compass.

    Cached per name because ImageReader reads and decodes the file. reportlab caches
    by digest as well, so a second reader of the same image would not add a second
    XObject -- this only avoids decoding it twice.
    """
    if name not in _READERS:
        _READERS[name] = ImageReader(path(name))
    return _READERS[name]
