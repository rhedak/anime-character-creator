"""Rules that add the new top-level field `line_style` (null) to a golden file without reformatting it, as ../golden-updates-build/buildfix.py did for `body_build`.

The goldens were recorded from the Python, which is gone, so they are changed by these mechanical rules from their old content, never regenerated from the new code; each updater
then checks the result against what the new code says (see README.md).

DICT   a CharacterParams as a dict (registry order): the field goes last, right after highlight_strength.
TEXT   the key-sorted compact JSON text of a CharacterParams (Python's json.dumps(sort_keys=True, separators=(",", ":"))), which may sit inside a JSON string (so its quotes may be escaped):
       line_style sorts right after left_elbow (and before outfit).
LINK   a character link's `c=` value is the base64url of that text, so it is decoded, given the field by TEXT, checked to differ by that field alone, and encoded again.
"""

import base64
import json
import re

NUM = r'(?:-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|NaN|-?Infinity)'
# TEXT: the escape prefix (\\*) is captured so the same rule works inside JSON strings
TEXT = re.compile(r'(\\*)"left_elbow\1":(' + NUM + r'),')


def text_fix(t):
    """A compact sorted CharacterParams text with the field added. Raises unless it has exactly one left_elbow field."""
    t2, n = TEXT.subn(lambda m: f'{m.group(1)}"left_elbow{m.group(1)}":{m.group(2)},{m.group(1)}"line_style{m.group(1)}":null,', t)
    if n != 1:
        raise ValueError(f"expected one left_elbow field, found {n}")
    return t2


def text_is_params(t):
    return isinstance(t, str) and TEXT.search(t) is not None


def check_text(old, new):
    a, b = json.loads(old), json.loads(new)
    assert "line_style" in b and b.pop("line_style") is None
    assert a == b, "the new text differs from the old by more than the field"


def link_code(code):
    pad = "=" * (-len(code) % 4)
    text = base64.urlsafe_b64decode(code + pad).decode("ascii")
    new = text_fix(text)
    check_text(text, new)
    return base64.urlsafe_b64encode(new.encode("ascii")).decode("ascii").rstrip("=")


LINK = re.compile(r'(\?c=)([A-Za-z0-9_\-]+)')


def fix_links(s):
    return LINK.sub(lambda m: m.group(1) + link_code(m.group(2)), s)


def dict_fix(d):
    """A dict (a parsed CharacterParams) with the field after highlight_strength, the registry's last."""
    assert list(d)[-1] == "highlight_strength", list(d)[-3:]
    return {**d, "line_style": None}
