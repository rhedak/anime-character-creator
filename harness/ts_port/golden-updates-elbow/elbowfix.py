"""Rules that add the two new top-level fields `right_elbow` and `left_elbow` (0.0) to a golden file without reformatting it, as rawfix.py did for `bodice_color`.

The goldens were recorded from the Python, which is gone, so they are changed by these mechanical rules from their old content, never regenerated from the new code; each updater
then checks the result against what the new code says (see README.md).

DICT   a CharacterParams as a dict (registry order): the two fields go right after left_arm_out, right_elbow first (the registry's order).
TEXT   the key-sorted compact JSON text of a CharacterParams (Python's json.dumps(sort_keys=True, separators=(",", ":"))), which may sit inside a JSON string (so its quotes may be escaped):
       left_elbow sorts right after left_arm_out, right_elbow right after right_arm_out.
LINK   a character link's `c=` value is the base64url of that text, so it is decoded, given the fields by TEXT, checked to differ by those fields alone, and encoded again.
"""

import base64
import json
import re

NUM = r'(?:-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|NaN|-?Infinity)'

# DICT, in a pretty-printed JSON file: "left_arm_out": 0.0,<ws>"shaded": ...
DICT = re.compile(r'("left_arm_out"(\s*):(\s*)' + NUM + r')(,)(\s*)')


def dict_sub(m):
    return f'{m.group(1)},{m.group(5)}"right_elbow"{m.group(2)}:{m.group(3)}0.0,{m.group(5)}"left_elbow"{m.group(2)}:{m.group(3)}0.0,{m.group(5)}'


# TEXT: the escape prefix (\\*) is captured so the same rule works inside JSON strings
TEXT_L = re.compile(r'(\\*)"left_arm_out\1":(' + NUM + r'),')
TEXT_R = re.compile(r'(\\*)"right_arm_out\1":(' + NUM + r'),')


def text_fix(t):
    """A compact sorted CharacterParams text with the two fields added. Raises unless it has exactly one of each arm field."""
    t2, nl = TEXT_L.subn(lambda m: f'{m.group(1)}"left_arm_out{m.group(1)}":{m.group(2)},{m.group(1)}"left_elbow{m.group(1)}":0.0,', t)
    t2, nr = TEXT_R.subn(lambda m: f'{m.group(1)}"right_arm_out{m.group(1)}":{m.group(2)},{m.group(1)}"right_elbow{m.group(1)}":0.0,', t2)
    if (nl, nr) != (1, 1):
        raise ValueError(f"expected one left_arm_out and one right_arm_out, found {nl} and {nr}")
    return t2


def text_is_params(t):
    return isinstance(t, str) and TEXT_L.search(t) is not None and TEXT_R.search(t) is not None


def check_text(old, new):
    a, b = json.loads(old), json.loads(new)
    assert b.pop("left_elbow") == 0.0 and b.pop("right_elbow") == 0.0
    assert a == b, "the new text differs from the old by more than the two fields"


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
    """A dict (a parsed CharacterParams) with the two fields inserted after left_arm_out, in the registry's order."""
    out = {}
    for k, v in d.items():
        out[k] = v
        if k == "left_arm_out":
            out["right_elbow"] = 0.0
            out["left_elbow"] = 0.0
    assert "right_elbow" in out
    return out
