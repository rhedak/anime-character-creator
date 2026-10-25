"""fixtures/calls/*.json (the committed recorded Python calls): a CharacterParams is recorded field by field in the registry's order, compact, so the field goes in last, right after
highlight_strength, spelled as the recorder spells None (a bare null). Text substitution, formatting untouched. Run from ts/."""
import glob, json, re

RULE = re.compile(r'("highlight_strength":"[fi]:[^"]*")(\})')
total = files = 0
for f in sorted(glob.glob("../harness/ts_port/fixtures/calls/*.json")):
    raw = open(f).read()
    new, n = RULE.subn(lambda m: m.group(1) + ',"line_style":null' + m.group(2), raw)
    if n == 0:
        assert '"highlight_strength":"' not in raw, f
        continue
    assert raw.count('"highlight_strength":"') == n and raw.count('"body":"s:') == n, f
    json.loads(new)
    open(f, "w").write(new)
    total += n; files += 1
print("recorded calls updated:", total, "CharacterParams in", files, "files")
