import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const H = process.env.TMPDIR + "/head";
const { PyError } = await import(`${H}/src/pynum.ts`);
const { loadsText } = await import(`${H}/src/pyjsonload.ts`);
const { decodeParams, encodeParams, paramsFromDict } = await import(`${H}/src/urlstate.ts`);
const { decodedPlain, sha256 } = await import(`${H}/test/corpus.ts`);
const REPO_ROOT = join(process.cwd(), "..");
const entries = (loadsText(readFileSync(join(REPO_ROOT, "harness/ts_port/corpus/errors.json"), "utf8")) as unknown[]).map((e) => decodedPlain(e) as any);
function floats(v: any): any {
  if (v instanceof Map) return new Map([...v].map(([k, x]) => [k, floats(x)]));
  if (Array.isArray(v)) return v.map(floats);
  if (v !== null && typeof v === "object" && Object.keys(v).length === 1 && "$float" in v) return ({ nan: NaN, inf: Infinity, "-inf": -Infinity } as any)[v.$float];
  return v;
}
const out: Record<string, { old: string; encoded: string }> = {};
for (const e of entries) {
  if (e.exc || e.op === "render") continue;
  let enc: string;
  if (e.op === "params_from_dict") enc = encodeParams(paramsFromDict(new Map(Object.entries(floats(e.arg)))));
  else enc = encodeParams(decodeParams(e.arg));
  if (sha256(enc) !== e.result_sha) throw new Error("old TS does not reproduce " + e.id);
  out[e.id] = { old: e.result_sha, encoded: enc };
}
writeFileSync(process.env.TMPDIR + "/errold.json", JSON.stringify(out));
console.log("old link outcomes reproduce the golden:", Object.keys(out).length);
