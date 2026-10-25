"""corpus/errors.json: an entry that succeeds records the sha256 of the link its result encodes to; the new hash is that link given the field (LINK), hashed. The file is changed by text
substitution of each old hash, so its formatting is untouched. Needs errold.json (errold.ts, from the old tree). Run from ts/."""
import json, os, sys, hashlib
sys.path.insert(0, "../harness/ts_port/golden-updates-build")
import buildfix as E

sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
f = "../harness/ts_port/corpus/errors.json"
raw = open(f).read()
old = json.load(open(os.environ["TMPDIR"] + "/errold.json"))
n = 0
for id_, o in old.items():
    new_enc = E.link_code(o["encoded"])
    assert sha(o["encoded"]) == o["old"]
    if o["old"] not in raw:  # an earlier entry with the same old link (so the same new one) already replaced it
        assert sha(new_enc) in raw, id_
    raw = raw.replace(o["old"], sha(new_enc))
    n += 1
open(f, "w").write(raw)
print("errors.json updated:", n, "entries")
