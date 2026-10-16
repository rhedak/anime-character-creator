// The inputs where Python raises (272 renders) and the link operations with a defined outcome (61), from
// `harness/ts_port/corpus/errors.json` and the committed manifest. The port must raise the same exception CLASS (decision
// D12: class names are Python's, the text is the port's own, listed in docs/ts-port-errors*.md). A link operation that
// succeeds in Python must succeed here and encode to the same bytes.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import { PyError, truthy } from "../src/pynum.ts";
import { loadsText } from "../src/pyjsonload.ts";
import { decodeParams, encodeParams, paramsFromDict } from "../src/urlstate.ts";
import { renderCharacter } from "../src/render.ts";
import type { CharacterParams } from "../src/params.ts";
import { decodedPlain, paramsFromDiff, sha256 } from "./corpus.ts";
import { REPO_ROOT } from "./fixtures.ts";

type Entry = { id: string; op: string; exc: string | null; msg?: string; at?: string; arg?: unknown; kw?: Record<string, unknown>; p?: Record<string, unknown>; result_sha?: string };

const entries = (loadsText(readFileSync(join(REPO_ROOT, "harness/ts_port/corpus/errors.json"), "utf8")) as unknown[]).map((e) => decodedPlain(e) as Entry);

/** The `{"$float": ...}` markers the corpus uses for non-finite numbers, as the numbers they stand for. */
function floats(v: unknown): unknown {
  if (v instanceof Map) return new Map([...v].map(([k, x]) => [k, floats(x)]));
  if (Array.isArray(v)) return v.map(floats);
  if (v !== null && typeof v === "object" && Object.keys(v as object).length === 1 && "$float" in (v as object)) {
    return { nan: NaN, inf: Infinity, "-inf": -Infinity }[(v as { $float: string }).$float];
  }
  return v;
}

function outcome(e: Entry): { cls: string | null; sha?: string } {
  try {
    if (e.op === "render") {
      const params = paramsFromDiff(floats(e.p ?? {}) as Record<string, unknown>) as CharacterParams;
      const kw = (floats(e.kw ?? {}) ?? {}) as Record<string, unknown>;
      renderCharacter(params, null, kw.background ?? null, kw.metadata ?? false, kw.id_prefix ?? "");
      return { cls: null };
    }
    if (e.op === "params_from_dict") {
      const arg = e.arg as Record<string, unknown>;
      const m = new Map(Object.entries(floats(arg) as object));
      return { cls: null, sha: sha256(encodeParams(paramsFromDict(m))) };
    }
    return { cls: null, sha: sha256(encodeParams(decodeParams(e.arg as string))) };
  } catch (err) {
    return { cls: err instanceof PyError ? err.pyType : `JS ${String(err).slice(0, 80)}` };
  }
}

test("every input Python rejects is rejected with the same exception class", (t) => {
  const bad: string[] = [];
  let n = 0;
  for (const e of entries) {
    n++;
    const got = outcome(e);
    const want = e.exc ?? null;
    if (got.cls !== want) bad.push(`${e.id} (${e.op}${e.at ? " at " + e.at : ""}): Python ${want ?? "succeeds"}, port ${got.cls ?? "succeeds"}`);
    else if (want === null && got.sha !== e.result_sha) bad.push(`${e.id}: link encodes to different bytes`);
  }
  t.diagnostic(`${n} outcomes, ${bad.length} differ`);
  assert.deepEqual(bad.slice(0, 40), [], `${bad.length} of ${n} differ`);
  assert.ok(truthy(n));
});
