"""Stage manifest for the full corpus: the Python side of the TypeScript port oracle at scale.

    manifest_full.py build               write manifest/full.json (committed) and out/full-stages.json
    manifest_full.py verify [--all]      recompute and compare; lists EVERY differing case
    manifest_full.py check-docs          only the instrumented-vs-plain document equality check
    manifest_full.py show CASE STAGE     print one stage's text (STAGE may be "skeleton" or "doc")
    manifest_full.py dump CASE...        write the full stage texts to out/stages-full/<case>.json

Inputs are corpus/full.json (cases that render) and corpus/errors.json (cases that raise, plus the
urlstate operations). `build` and `verify` first prove, for EVERY case, that the document produced
through the AST hook (`instrument.render_stages`, unchanged) is the document a second interpreter
produces with no hook (`manifest_full.py _plain`): same sha256, and for the error cases the same
exception class and message.

manifest/full.json (committed, compact)
  header   python, platform, src_sha256 (the frozen package), corpus_sha256 (the two corpus files),
           case_count, error_count
  cases    id -> [doc_sha256[:20], stages_digest[:20]] where stages_digest is the sha256 over the lines
           "name:sha256" of every stage (chest[i], under_arms[i], layers[i], body, body_soft, body_ns,
           doc) joined by "\\n"
  errors   id -> [exception class, sha256(message)[:20]]; for a urlstate operation that succeeded,
           ["ok", sha256(result_sha)[:20]]

out/full-stages.json (not committed): per case the skeleton sha, and every stage's sha256 and length,
so that a mismatch can be localised. `show` regenerates a stage's text on demand.

Text is hashed as UTF-8 with `surrogatepass`: a lone surrogate in user text (the wristband) makes
the document impossible to encode strictly, and the hash must still be defined.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import _bootstrap

HERE = _bootstrap.HERE
MANIFEST = HERE / "manifest" / "full.json"
STAGES_FILE = HERE / "out" / "full-stages.json"
STAGES_DIR = HERE / "out" / "stages-full"
FULL = HERE / "corpus" / "full.json"
ERRORS = HERE / "corpus" / "errors.json"
WORKERS = int(os.environ.get("MANIFEST_WORKERS", "8"))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()


def digest_of(stages: list[tuple[str, str, int]]) -> str:
    return sha("\n".join(f"{n}:{h}" for n, h, _ in stages))[:20]


def src_sha256() -> str:
    import manifest as mini

    return mini.src_sha256()


def corpus_sha256() -> str:
    h = hashlib.sha256()
    for p in (FULL, ERRORS):
        h.update(p.read_bytes())
    return h.hexdigest()


def dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def one_line_per_key(obj: dict[str, Any]) -> str:
    """A JSON object with one line per top-level key and per case: small diffs, small files."""
    parts = []
    for k in sorted(obj):
        v = obj[k]
        if isinstance(v, dict) and k in ("cases", "errors"):
            inner = ",\n".join(f"{json.dumps(i)}:{dumps(v[i])}" for i in sorted(v))
            parts.append(f'{json.dumps(k)}:{{\n{inner}\n}}')
        else:
            parts.append(f"{json.dumps(k)}:{dumps(v)}")
    return "{\n" + ",\n".join(parts) + "\n}\n"


def load_entries() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return json.loads(FULL.read_text(encoding="utf-8")), json.loads(ERRORS.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# workers
# --------------------------------------------------------------------------
def _instrumented_one(entry: dict[str, Any]) -> dict[str, Any]:
    import corpus_full as cf
    import instrument

    out: dict[str, Any] = {"id": entry["id"]}
    try:
        r = instrument.render_stages(cf.load_full_case(entry), **entry["kw"])
    except Exception as e:
        out["exc"] = [type(e).__name__, str(e)]
        return out
    out["skeleton"] = sha(json.dumps(r["skeleton"], sort_keys=True, separators=(",", ":")))
    out["stages"] = [(s["name"], sha(s["text"]), len(s["text"])) for s in r["stages"]]
    out["doc"] = sha(r["stages"][-1]["text"])
    return out


def _error_one(entry: dict[str, Any]) -> dict[str, Any]:
    """An entry of errors.json under the hook: the outcome as (class, message) or ("ok", result_sha)."""
    import corpus_full as cf
    import instrument

    if entry["op"] != "render":
        res = cf.run_url_op(entry)
        if res["exc"] is None:
            return {"id": entry["id"], "outcome": ["ok", res["result_sha"]]}
        return {"id": entry["id"], "outcome": [res["exc"], res["msg"]]}
    try:
        instrument.render_stages(cf.load_full_case(entry), **entry["kw"])
    except Exception as e:
        return {"id": entry["id"], "outcome": [type(e).__name__, str(e)]}
    return {"id": entry["id"], "outcome": ["ok", ""]}


def _plain_one(entry: dict[str, Any]) -> dict[str, Any]:
    import corpus_full as cf
    from anime_character_creator.character import render_character

    if "op" in entry and entry["op"] != "render":
        res = cf.run_url_op(entry)
        return {"id": entry["id"], "outcome": ["ok", res["result_sha"]] if res["exc"] is None else [res["exc"], res["msg"]]}
    try:
        doc = render_character(cf.load_full_case(entry), **entry["kw"])
    except Exception as e:
        return {"id": entry["id"], "outcome": [type(e).__name__, str(e)]}
    return {"id": entry["id"], "doc": sha(doc), "outcome": ["ok", ""]}


def _map(fn: Any, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if WORKERS <= 1:
        return [fn(i) for i in items]
    import multiprocessing

    with multiprocessing.get_context("fork").Pool(WORKERS) as pool:
        return pool.map(fn, items, chunksize=64)


def plain_all() -> dict[str, Any]:
    """Run in a fresh interpreter WITHOUT the hook."""
    from anime_character_creator import character

    _bootstrap.assert_package_location()
    if "__stage" in character.render_character.__code__.co_names:
        raise RuntimeError("plain process is instrumented")
    ok, errs = load_entries()
    rows = _map(_plain_one, ok) + _map(_plain_one, errs)
    return {r["id"]: r for r in rows}


def run_plain() -> dict[str, Any]:
    env = dict(os.environ, PYTHONPATH=str(_bootstrap.SRC), PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, str(HERE / "manifest_full.py"), "_plain"], capture_output=True, text=True, env=env, check=False)
    if r.returncode != 0:
        raise RuntimeError(f"plain process failed:\n{r.stderr[-2000:]}")
    return json.loads(r.stdout)


def compute() -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    import instrument

    instrument.install()
    ok, errs = load_entries()
    results = {r["id"]: r for r in _map(_instrumented_one, ok)}
    outcomes = {r["id"]: r["outcome"] for r in _map(_error_one, errs)}
    return results, outcomes


def check_docs(results: dict[str, dict[str, Any]], outcomes: dict[str, list[str]]) -> list[str]:
    plain = run_plain()
    problems = []
    want = set(results) | set(outcomes)
    if set(plain) != want:
        problems.append("case id sets differ between the plain and instrumented runs")
    for cid, r in results.items():
        p = plain.get(cid, {})
        if "exc" in r:
            problems.append(f"{cid}: raised under the hook ({r['exc'][0]}: {r['exc'][1][:60]}) but is in full.json")
        elif p.get("doc") != r["doc"]:
            problems.append(f"{cid}: doc differs (plain {p.get('doc')}, instrumented {r['doc']})")
    for cid, o in outcomes.items():
        if plain.get(cid, {}).get("outcome") != o:
            problems.append(f"{cid}: outcome differs (plain {plain.get(cid, {}).get('outcome')}, instrumented {o})")
    return problems


def build_manifest(results: dict[str, dict[str, Any]], outcomes: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "header": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "src_sha256": src_sha256(),
            "corpus_sha256": corpus_sha256(),
            "case_count": len(results),
            "error_count": len(outcomes),
        },
        "cases": {cid: [r["doc"][:20], digest_of(r["stages"])] for cid, r in results.items()},
        "errors": {cid: [o[0], sha(o[1])[:20]] for cid, o in outcomes.items()},
    }


def stage_file(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {cid: {"skeleton": r["skeleton"], "stages": [list(s) for s in r["stages"]]} for cid, r in results.items()}


def localise(cid: str, r: dict[str, Any], old: dict[str, Any] | None) -> str:
    if old is None or cid not in old:
        return "no out/full-stages.json entry to compare with"
    a, b = old[cid]["stages"], r["stages"]
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else None
        y = list(b[i]) if i < len(b) else None
        if x != y:
            return f"first differing stage #{i}: recorded {x}, now {y}"
    if old[cid]["skeleton"] != r["skeleton"]:
        return "skeleton differs, stages equal"
    return "stages equal"


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "_plain":
        print(json.dumps(plain_all()))
        return 0
    if cmd not in {"build", "verify", "show", "dump", "check-docs"}:
        print(__doc__)
        return 2
    results, outcomes = compute()
    _bootstrap.assert_package_location()
    if cmd in {"build", "verify", "check-docs"}:
        problems = check_docs(results, outcomes)
        if problems:
            print(f"DOC CHECK FAILED ({len(problems)}):\n  " + "\n  ".join(problems[:10]))
            return 1
        print(f"doc check: instrumented doc == plain doc for all {len(results)} cases; {len(outcomes)} error/op outcomes equal")
    if cmd == "build":
        m = build_manifest(results, outcomes)
        MANIFEST.parent.mkdir(exist_ok=True)
        MANIFEST.write_text(one_line_per_key(m), encoding="utf-8")
        STAGES_FILE.parent.mkdir(exist_ok=True)
        STAGES_FILE.write_text(one_line_per_key({"cases": stage_file(results)}), encoding="utf-8")
        print(f"wrote {MANIFEST} ({MANIFEST.stat().st_size} bytes) and {STAGES_FILE} ({STAGES_FILE.stat().st_size} bytes)")
    elif cmd == "verify":
        committed = json.loads(MANIFEST.read_text(encoding="utf-8"))
        now = build_manifest(results, outcomes)
        for k in ("python", "platform"):
            if committed["header"][k] != now["header"][k]:
                print(f"note: {k} differs: committed {committed['header'][k]!r}, now {now['header'][k]!r}")
        for k in ("src_sha256", "corpus_sha256", "case_count", "error_count"):
            if committed["header"][k] != now["header"][k]:
                print(f"VERIFY FAILED: header {k}: committed {committed['header'][k]} vs now {now['header'][k]}")
                return 1
        old_stages = json.loads(STAGES_FILE.read_text(encoding="utf-8"))["cases"] if STAGES_FILE.exists() else None
        bad_doc, bad_stage, bad_err = [], [], []
        for cid, (doc, dig) in committed["cases"].items():
            n = now["cases"][cid]
            if n[0] != doc:
                bad_doc.append(cid)
            elif n[1] != dig:
                bad_stage.append(cid)
        for cid, v in committed["errors"].items():
            if now["errors"][cid] != v:
                bad_err.append(cid)
        print(f"differing documents: {len(bad_doc)}; same document but different stages: {len(bad_stage)}; differing error outcomes: {len(bad_err)}")
        shown = bad_doc + bad_stage if "--all" in argv else (bad_doc + bad_stage)[:10]
        for cid in shown:
            print(f"  {cid}: {localise(cid, results[cid], old_stages)}")
        for cid in (bad_err if "--all" in argv else bad_err[:10]):
            print(f"  {cid}: error outcome {committed['errors'][cid]} vs now {now['errors'][cid]}")
        if bad_doc or bad_stage or bad_err:
            print("VERIFY FAILED")
            return 1
        print(f"verify ok: {len(results)} cases and {len(outcomes)} outcomes match {MANIFEST.name}")
    elif cmd == "show":
        if len(argv) != 4:
            print("usage: manifest_full.py show CASE_ID STAGE_NAME")
            return 2
        return show(argv[2], argv[3])
    elif cmd == "dump":
        import corpus_full as cf
        import instrument

        ok, _ = load_entries()
        by = {e["id"]: e for e in ok}
        STAGES_DIR.mkdir(parents=True, exist_ok=True)
        for cid in argv[2:]:
            e = by[cid]
            r = instrument.render_stages(cf.load_full_case(e), **e["kw"])
            doc = {"id": cid, "kw": e["kw"], "skeleton": r["skeleton"], "stages": r["stages"]}
            (STAGES_DIR / f"{cid}.json").write_text(json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"wrote {len(argv) - 2} files to {STAGES_DIR}")
    return 0


def show(cid: str, stage: str) -> int:
    import corpus_full as cf
    import instrument

    ok, errs = load_entries()
    by = {e["id"]: e for e in [*ok, *errs]}
    e = by.get(cid)
    if e is None:
        print(f"no case {cid!r}")
        return 2
    if "op" in e and e["op"] != "render":
        print(json.dumps(cf.run_url_op(e), indent=1))
        return 0
    try:
        r = instrument.render_stages(cf.load_full_case(e), **e["kw"])
    except Exception as ex:
        print(f"{cid} raises {type(ex).__name__}: {ex}")
        return 0
    if stage == "skeleton":
        print(json.dumps(r["skeleton"], sort_keys=True, indent=1))
        return 0
    for s in r["stages"]:
        if s["name"] == stage:
            sys.stdout.write(s["text"].encode("utf-8", "surrogatepass").decode("utf-8", "replace"))
            return 0
    print(f"no stage {stage!r}; stages: {[s['name'] for s in r['stages']]}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
