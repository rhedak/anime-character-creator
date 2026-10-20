"""presets.json: every CharacterParams dict gets the two fields (DICT), every key-sorted text gets them (TEXT), and so does the defaults text. Run from ts/."""
import json, sys
sys.path.insert(0, "../harness/ts_port/golden-updates-elbow")
import elbowfix as E

f = "fixtures/presets.json"
raw = open(f).read()
d = json.loads(raw)
nl = "\n" if raw.endswith("\n") else ""
assert json.dumps(d, indent=1) + nl == raw
n = 0
for sec in ("presets", "neutral_bases", "supporting"):
    for name, e in d[sec].items():
        e["dict"] = E.dict_fix(e["dict"])
        new = E.text_fix(e["json"]); E.check_text(e["json"], new); e["json"] = new
        n += 1
new = E.text_fix(d["defaults"]["CharacterParams"]); E.check_text(d["defaults"]["CharacterParams"], new); d["defaults"]["CharacterParams"] = new
open(f, "w").write(json.dumps(d, indent=1) + nl)
print("presets.json updated:", n, "entries and the defaults text")
