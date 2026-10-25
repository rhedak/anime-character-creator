"""Rules that add the new top-level field `body_build` (null) to a golden file without reformatting it, as ../golden-updates-elbow/elbowfix.py did for the elbow fields.

The goldens were recorded from the Python, which is gone, so they are changed by these mechanical rules from their old content, never regenerated from the new code; each updater
then checks the result against what the new code says (see README.md).

DICT   a CharacterParams as a dict (registry order): the field goes right after body.
TEXT   the key-sorted compact JSON text of a CharacterParams (Python's json.dumps(sort_keys=True, separators=(",", ":"))), which may sit inside a JSON string (so its quotes may be escaped):
       body_build sorts right after body (no other key starts with "body").
LINK   a character link's `c=` value is the base64url of that text, so it is decoded, given the field by TEXT, checked to differ by that field alone, and encoded again.
"""

import base64
import json
import re

# TEXT: the escape prefix (\\*) is captured so the same rule works inside JSON strings; a body name is lower case, digits and underscores
TEXT = re.compile(r'(\\*)"body\1":\1"([a-z0-9_]*)\1",')


def text_fix(t):
    """A compact sorted CharacterParams text with the field added. Raises unless it has exactly one body field."""
    t2, n = TEXT.subn(lambda m: f'{m.group(1)}"body{m.group(1)}":{m.group(1)}"{m.group(2)}{m.group(1)}",{m.group(1)}"body_build{m.group(1)}":null,', t)
    if n != 1:
        raise ValueError(f"expected one body field, found {n}")
    return t2


def text_is_params(t):
    return isinstance(t, str) and TEXT.search(t) is not None


def check_text(old, new):
    a, b = json.loads(old), json.loads(new)
    assert "body_build" in b and b.pop("body_build") is None
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
    """A dict (a parsed CharacterParams) with the field inserted after body, in the registry's order."""
    out = {}
    for k, v in d.items():
        out[k] = v
        if k == "body":
            out["body_build"] = None
    assert "body_build" in out
    return out
