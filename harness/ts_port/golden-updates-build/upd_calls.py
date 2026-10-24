"""fixtures/calls/*.json (the committed recorded Python calls): a CharacterParams is recorded field by field in the registry's order, compact, so the field goes in right after body, before height,
spelled as the recorder spells None (a bare null). Text substitution, formatting untouched. Run from ts/."""
import glob, json, re

RULE = re.compile(r'("body":"s:[^"]*",)("height")')
total = files = 0
for f in sorted(glob.glob("../harness/ts_port/fixtures/calls/*.json")):
    raw = open(f).read()
    new, n = RULE.subn(lambda m: m.group(1) + '"body_build":null,' + m.group(2), raw)
    if n == 0:
        assert '"body":"s:' not in raw, f
        continue
    assert raw.count('"body":"s:') == n and raw.count('"left_arm_out":"') == n, f
    json.loads(new)
    open(f, "w").write(new)
    total += n; files += 1
print("recorded calls updated:", total, "CharacterParams in", files, "files")
