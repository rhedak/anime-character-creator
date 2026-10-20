"""urlstate.json: the encode cases hash the CharacterParams text, its link code and the url; the malformed cases hash the text a link decodes to; base_urls has a text and urls with links. Every one is the old
text/link with the two fields added (TEXT, LINK), hashed again. Needs urlold.json (urlold.ts, from the old tree). Run from ts/."""
import json, os, sys, hashlib, base64
sys.path.insert(0, "../harness/ts_port/golden-updates-elbow")
import elbowfix as E

sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
f = "fixtures/urlstate.json"
raw = open(f).read(); d = json.loads(raw)
nl = "\n" if raw.endswith("\n") else ""
assert json.dumps(d, indent=1) + nl == raw
old = json.load(open(os.environ["TMPDIR"] + "/urlold.json"))


def newtext(t):
    new = E.text_fix(t); E.check_text(t, new); return new


def walk(v):
    if isinstance(v, str): return E.fix_links(v)
    if isinstance(v, list): return [walk(x) for x in v]
    if isinstance(v, dict): return {k: walk(x) for k, x in v.items()}
    return v


for c, o in zip(d["encode"], old["enc"]):
    nt = newtext(o["params"]); ne = base64.urlsafe_b64encode(nt.encode()).decode().rstrip("=")
    assert ne == E.link_code(o["encoded"])
    assert c["params_sha256"] == sha(o["params"]), "params_sha256 is not the hash of the params text"
    c["params_sha256"] = sha(nt); c["encoded_sha256"] = sha(ne); c["encoded_len"] = len(ne)
    c["url_sha256"] = sha(E.fix_links(o["url"]))
    if "encoded" in c: assert c["encoded"] == o["encoded"]; c["encoded"] = ne
    if "params" in c: assert c["params"] == o["params"]; c["params"] = nt
for c, o in zip(d["malformed"], old["mal"]):
    if o is None: continue
    assert c["want"]["ok_sha256"] == o["sha"]
    c["want"]["ok_sha256"] = sha(newtext(o["text"]))
b = d["base_urls"]; b["params"] = newtext(b["params"]); b["cases"] = walk(b["cases"])
open(f, "w").write(json.dumps(d, indent=1) + nl)
print("urlstate.json updated:", len(d["encode"]), "encode cases,", sum(1 for o in old["mal"] if o), "malformed ok")
