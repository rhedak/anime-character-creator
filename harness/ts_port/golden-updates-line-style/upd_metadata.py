"""metadata.json: each case's block carries the character's link, which is given the field (LINK). Run from ts/."""
import json, sys
sys.path.insert(0, "../harness/ts_port/golden-updates-line-style")
import linefix as E

f = "fixtures/metadata.json"
raw = open(f).read(); d = json.loads(raw)
nl = "\n" if raw.endswith("\n") else ""
assert json.dumps(d, indent=1) + nl == raw
n = 0
for c in d["cases"]:
    new = E.fix_links(c["block"]); assert new != c["block"]; c["block"] = new; n += 1
open(f, "w").write(json.dumps(d, indent=1) + nl)
print("metadata.json updated:", n, "blocks")
