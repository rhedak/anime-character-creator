"""pages.json: each case is the sha256 and size of the page the frozen Python drew for some arguments. Where the page carries metadata its links are given the two fields (LINK), so the new page is the old
one (drawn by the old tree, checked against the recorded sha) with its links fixed, which is then checked against what the new tree draws, and hashed. Needs the old tree at $TMPDIR/head. Run from ts/."""
import hashlib, json, os, subprocess, sys, tempfile
sys.path.insert(0, "../harness/ts_port/golden-updates-elbow")
import elbowfix as E

sha = lambda b: hashlib.sha256(b).hexdigest()
f = "fixtures/pages.json"
raw = open(f).read(); d = json.loads(raw)
nl = "\n" if raw.endswith("\n") else ""
assert json.dumps(d, indent=1) + nl == raw
head = os.environ["TMPDIR"] + "/head"
work = tempfile.mkdtemp(prefix="pages-elbow-", dir=os.environ["TMPDIR"])
local = os.path.join(work, "local"); os.makedirs(local)
open(os.path.join(local, "cover_faces.json"), "w").write('{"satoko": 0.55, "kyoko": 1, "tomohiro": "0.7"}')


def draw(root, kind, args, local_faces, name):
    script = os.path.join(root, "bin", f"{kind}.ts")
    base = os.path.join(work, name)
    env = dict(os.environ, ACC_LOCAL_DIR=local if local_faces else "/nonexistent")
    r = subprocess.run(["node", script, *args, "--out", base], capture_output=True, text=True, env=env, cwd=root)
    assert r.returncode == 0, r.stderr
    return open(base + ".svg", "rb").read()


changed = 0
for i, c in enumerate(d["cases"]):
    old = draw(head, c["kind"], c["args"], c["local_faces"], f"old{i}")
    assert sha(old) == c["sha256"] and len(old) == c["bytes"], f"the old tree does not reproduce case {i}"
    new = E.fix_links(old.decode("utf8")).encode("utf8")
    now = draw(os.getcwd(), c["kind"], c["args"], c["local_faces"], f"new{i}")
    assert now == new, f"the new tree's page differs from the old one with its links fixed: case {i}"
    if new != old:
        c["sha256"] = sha(new); c["bytes"] = len(new); changed += 1
open(f, "w").write(json.dumps(d, indent=1) + nl)
print("pages.json updated:", changed, "of", len(d["cases"]), "cases changed")
