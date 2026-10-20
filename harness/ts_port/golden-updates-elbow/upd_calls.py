"""fixtures/calls/*.json (the committed recorded Python calls): a CharacterParams is recorded field by field in the registry's order, compact, so the two fields go in right after left_arm_out, before
shaded, spelled as the recorder spells the float 0.0 ("f:" and the hex of the double). Text substitution, formatting untouched. Run from ts/."""
import glob, json, re

HEX0 = "f:0000000000000000"
RULE = re.compile(r'("left_arm_out":"[fi]:[^"]*",)("shaded")')
total = files = 0
for f in sorted(glob.glob("../harness/ts_port/fixtures/calls/*.json")):
    raw = open(f).read()
    new, n = RULE.subn(lambda m: m.group(1) + f'"right_elbow":"{HEX0}","left_elbow":"{HEX0}",' + m.group(2), raw)
    if n == 0:
        assert "left_arm_out" not in raw, f
        continue
    assert raw.count('"left_arm_out"') == n, f
    json.loads(new)
    open(f, "w").write(new)
    total += n; files += 1
print("recorded calls updated:", total, "CharacterParams in", files, "files")
