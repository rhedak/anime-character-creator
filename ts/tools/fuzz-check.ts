// Check the TypeScript against a fuzz recording made by the frozen Python (`harness/ts_port/fuzz.py`).
//   node tools/fuzz-check.ts ../harness/ts_port/out/fuzz-777.json
import { readFileSync } from "node:fs";
import { PyError } from "../src/pynum.ts";
import { renderCharacter } from "../src/render.ts";
import { loadsText } from "../src/pyjsonload.ts";
import type { Json } from "../src/pyjson.ts";
import { paramsFromDiff, plainObjects } from "../web-check/corpus-diff.ts";
import { sha256 } from "../test/corpus.ts";

type Entry = { id: string; p: Record<string, unknown>; kw: Record<string, unknown>; doc?: string; exc?: string };
const entries = (loadsText(readFileSync(process.argv[2]!, "utf8")) as Json[]).map((e) => plainObjects(e) as Entry);
let same = 0;
const bad: string[] = [];
const t0 = performance.now();
for (const e of entries) {
  let got: { doc?: string; exc?: string };
  try {
    const kw = e.kw;
    const svg = renderCharacter(paramsFromDiff(e.p), null, kw.background ?? null, kw.metadata ?? false, kw.id_prefix ?? "");
    got = { doc: sha256(svg).slice(0, 20) };
  } catch (err) {
    got = { exc: err instanceof PyError ? err.pyType : `JS ${String(err).slice(0, 70)}` };
  }
  if (got.doc === e.doc && got.exc === e.exc) same++;
  else bad.push(`${e.id}: Python ${e.exc ?? "doc " + e.doc}, port ${got.exc ?? "doc " + got.doc}`);
}
console.log(`${entries.length} cases in ${((performance.now() - t0) / 1000).toFixed(1)} s: ${same} identical, ${bad.length} differ`);
for (const b of bad.slice(0, 25)) console.log("  " + b);
process.exitCode = bad.length ? 1 : 0;
