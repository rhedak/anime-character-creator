import json, hashlib, os, re, sys, base64
sys.path.insert(0, os.environ["TMPDIR"])
from rawfix import R2, r2
from linkfix import newcode, fix_str, walk
sha=lambda s: hashlib.sha256(s.encode()).hexdigest()
f="fixtures/urlstate.json"; raw=open(f).read(); d=json.loads(raw)
nl="\n" if raw.endswith("\n") else ""
assert json.dumps(d,indent=1)+nl==raw
old=json.load(open(os.environ["TMPDIR"]+"/urlold.json"))
def newtext(t):
    new,n=R2.subn(r2,t); assert n==1, n
    a=json.loads(t); b=json.loads(new); assert b["outfit"].pop("bodice_color") is None and a==b
    return new
for c,o in zip(d["encode"],old["enc"]):
    nt=newtext(o["params"]); ne=base64.urlsafe_b64encode(nt.encode()).decode().rstrip("=")
    assert ne==newcode(o["encoded"])
    assert c["params_sha256"] in (sha(o["params"]),) , "params_sha256 is not the hash of the params text"
    c["params_sha256"]=sha(nt); c["encoded_sha256"]=sha(ne); c["encoded_len"]=len(ne)
    c["url_sha256"]=sha(fix_str(o["url"]))
    if "encoded" in c: assert c["encoded"]==o["encoded"]; c["encoded"]=ne
    if "params" in c: assert c["params"]==o["params"]; c["params"]=nt
for c,o in zip(d["malformed"],old["mal"]):
    if o is None: continue
    assert c["want"]["ok_sha256"]==o["sha"]
    c["want"]["ok_sha256"]=sha(newtext(o["text"]))
# base_urls: a params text and urls with links
b=d["base_urls"]; b["params"]=newtext(b["params"]); b["cases"]=walk(b["cases"])
open(f,"w").write(json.dumps(d,indent=1)+nl)
print("urlstate.json updated")
