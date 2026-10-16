"""Stage manifest for the mini corpus: the Python side of the TypeScript port oracle.

    manifest.py build            write manifest/mini.json (also runs the doc check)
    manifest.py verify           recompute everything, compare with manifest/mini.json
    manifest.py show CASE STAGE  print one stage's text (STAGE may be "skeleton")
    manifest.py dump             write the full stage texts to out/stages/<case>.json
    manifest.py check-docs       only the instrumented-vs-plain document equality check

The doc check renders every case twice: here, through the instrumenting hook, and in
a second interpreter that never installs the hook. The sha256 of each document must
match. The second interpreter is this same file run as `manifest.py _plain`.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from typing import Any

import _bootstrap

HERE = _bootstrap.HERE
MANIFEST = HERE / "manifest" / "mini.json"
STAGES_DIR = HERE / "out" / "stages"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def skeleton_sha(skeleton: dict[str, Any]) -> str:
    return sha(json.dumps(skeleton, sort_keys=True, separators=(",", ":")))


def src_sha256() -> str:
    h = hashlib.sha256()
    files = sorted(
        (str(p.relative_to(_bootstrap.PKG)), p)
        for p in _bootstrap.PKG.rglob("*.py")
        if "__pycache__" not in p.parts
    )
    for rel, p in files:
        data = p.read_bytes()
        h.update(rel.encode("utf-8") + b"\0" + str(len(data)).encode() + b"\0" + data)
    return h.hexdigest()


def plain_docs() -> dict[str, str]:
    """Run in a fresh interpreter WITHOUT the hook: sha256 of each case's document."""
    from anime_character_creator import character

    _bootstrap.assert_package_location()
    if "__stage" in character.render_character.__code__.co_names:
        raise RuntimeError("plain process is instrumented")
    import cases

    out = {}
    for c in cases.load_cases():
        out[c["id"]] = sha(character.render_character(c["p"], **c["kwargs"]))
    return out


def run_plain() -> dict[str, str]:
    env = dict(os.environ, PYTHONPATH=str(_bootstrap.SRC), PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run(
        [sys.executable, str(HERE / "manifest.py"), "_plain"],
        capture_output=True, text=True, env=env, check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(f"plain process failed:\n{r.stderr}")
    return json.loads(r.stdout)


def compute() -> dict[str, dict[str, Any]]:
    """Instrumented renders of every case: {id: {"skeleton", "stages", "kwargs"}}."""
    import instrument

    instrument.install()
    import cases

    out = {}
    for c in cases.load_cases():
        r = instrument.render_stages(c["p"], **c["kwargs"])
        r["kwargs"] = c["kwargs"]
        out[c["id"]] = r
    return out


def check_docs(results: dict[str, dict[str, Any]]) -> list[str]:
    plain = run_plain()
    problems = []
    if sorted(plain) != sorted(results):
        problems.append("case id sets differ between the plain and instrumented runs")
    for cid, r in results.items():
        got = sha(r["stages"][-1]["text"])
        if plain.get(cid) != got:
            problems.append(f"{cid}: doc differs (plain {plain.get(cid)}, instrumented {got})")
    return problems


def build_manifest(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    libc = platform.libc_ver()
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "libm": "-".join(libc) if any(libc) else platform.machine(),
        "src_sha256": src_sha256(),
        "cases": {
            cid: {
                "skeleton_sha256": skeleton_sha(r["skeleton"]),
                "stages": [
                    {"name": s["name"], "sha256": sha(s["text"]), "len": len(s["text"])}
                    for s in r["stages"]
                ],
            }
            for cid, r in sorted(results.items())
        },
    }


def first_difference(old: dict[str, Any], new: dict[str, Any]) -> str | None:
    if old["src_sha256"] != new["src_sha256"]:
        return f"src_sha256: committed {old['src_sha256']} vs now {new['src_sha256']}"
    oc, nc = old["cases"], new["cases"]
    if list(oc) != list(nc):
        gone = sorted(set(oc) - set(nc))
        extra = sorted(set(nc) - set(oc))
        return f"case ids differ: only in manifest {gone[:5]}, only now {extra[:5]}"
    for cid in oc:
        if oc[cid]["skeleton_sha256"] != nc[cid]["skeleton_sha256"]:
            return f"{cid}: skeleton_sha256 {oc[cid]['skeleton_sha256']} vs {nc[cid]['skeleton_sha256']}"
        os_, ns = oc[cid]["stages"], nc[cid]["stages"]
        for i in range(max(len(os_), len(ns))):
            a = os_[i] if i < len(os_) else None
            b = ns[i] if i < len(ns) else None
            if a != b:
                return f"{cid}: stage #{i}: committed {a} vs now {b}"
    return None


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "_plain":
        print(json.dumps(plain_docs()))
        return 0
    if cmd not in {"build", "verify", "show", "dump", "check-docs"}:
        print(__doc__)
        return 2
    results = compute()
    _bootstrap.assert_package_location()
    if cmd in {"build", "verify", "check-docs"}:
        problems = check_docs(results)
        if problems:
            print("DOC CHECK FAILED:\n  " + "\n  ".join(problems[:10]))
            return 1
        print(f"doc check: instrumented doc == plain doc for all {len(results)} cases")
    if cmd == "build":
        import cases

        m = build_manifest(results)
        MANIFEST.write_text(cases.dump_json(m), encoding="utf-8")
        print(f"wrote {MANIFEST}")
    elif cmd == "verify":
        committed = json.loads(MANIFEST.read_text(encoding="utf-8"))
        now = build_manifest(results)
        for k in ("python", "platform", "libm"):
            if committed[k] != now[k]:
                print(f"note: {k} differs: committed {committed[k]!r}, now {now[k]!r}")
        diff = first_difference(committed, now)
        if diff:
            print(f"VERIFY FAILED, first difference: {diff}")
            return 1
        print(f"verify ok: {len(results)} cases match {MANIFEST.name}")
    elif cmd == "show":
        if len(argv) != 4:
            print("usage: manifest.py show CASE_ID STAGE_NAME")
            return 2
        r = results.get(argv[2])
        if r is None:
            print(f"no case {argv[2]!r}")
            return 2
        if argv[3] == "skeleton":
            print(json.dumps(r["skeleton"], sort_keys=True, indent=1))
            return 0
        for s in r["stages"]:
            if s["name"] == argv[3]:
                sys.stdout.write(s["text"])
                return 0
        print(f"no stage {argv[3]!r}; stages: {[s['name'] for s in r['stages']]}")
        return 2
    elif cmd == "dump":
        import cases

        STAGES_DIR.mkdir(parents=True, exist_ok=True)
        for cid, r in sorted(results.items()):
            doc = {"id": cid, "kwargs": r["kwargs"], "skeleton": r["skeleton"], "stages": r["stages"]}
            (STAGES_DIR / f"{cid}.json").write_text(cases.dump_json(doc), encoding="utf-8")
        print(f"wrote {len(results)} files to {STAGES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
