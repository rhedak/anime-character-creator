"""model.json: the expression cases hash the CharacterParams text of a preset with a mood applied; the new hash is that old text with the field added (TEXT), hashed. Needs modelold.json. Run from ts/."""
import json, os, sys, hashlib
sys.path.insert(0, "../harness/ts_port/golden-updates-build")
import buildfix as E

sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
f = "fixtures/model.json"
raw = open(f).read(); d = json.loads(raw)
nl = "\n" if raw.endswith("\n") else ""
assert json.dumps(d, indent=1) + nl == raw
old = json.load(open(os.environ["TMPDIR"] + "/modelold.json"))
assert len(old) == len(d["expressions"])
for c, t in zip(d["expressions"], old):
    assert c["params_sha256"] == sha(t), "params_sha256 is not the hash of the old text"
    nt = E.text_fix(t); E.check_text(t, nt)
    c["params_sha256"] = sha(nt)
open(f, "w").write(json.dumps(d, indent=1) + nl)
print("model.json updated:", len(old), "expression cases")
