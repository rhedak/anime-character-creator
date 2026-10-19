import re, json, base64, sys
sys.path.insert(0, __import__("os").environ["TMPDIR"])
from rawfix import R2, r2
LINK = re.compile(r'(\?c=)([A-Za-z0-9_\-]+)')
def newcode(code):
    pad = "=" * (-len(code) % 4)
    text = base64.urlsafe_b64decode(code + pad).decode("ascii")
    old = json.loads(text)
    new, n = R2.subn(r2, text)
    assert n == 1 and '"strap_color"' in text, "expected exactly one outfit in the link"
    nj = json.loads(new)
    assert nj["outfit"].pop("bodice_color") is None
    assert nj == old, "the new text differs from the old by more than the field"
    return base64.urlsafe_b64encode(new.encode("ascii")).decode("ascii").rstrip("=")
def fix_str(s):
    return LINK.sub(lambda m: m.group(1) + newcode(m.group(2)), s)
def walk(v):
    if isinstance(v, str): return fix_str(v)
    if isinstance(v, list): return [walk(x) for x in v]
    if isinstance(v, dict): return {k: walk(x) for k, x in v.items()}
    return v
if __name__ == "__main__":
    f = sys.argv[1]
    raw = open(f).read(); d = json.loads(raw)
    nl = "\n" if raw.endswith("\n") else ""
    assert json.dumps(d, indent=1) + nl == raw
    open(f, "w").write(json.dumps(walk(d), indent=1) + nl)
    print("done", f)
