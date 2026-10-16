// The function-level oracle: every function of the Python package that has recorded calls and a TypeScript counterpart
// is replayed with the same arguments and must return what Python returned.
//
// A Python function `_hair_fall` is looked for as `hairFall` among the exports of every module in `src/`; module-level
// constants and tables keep their names (`HAIRSTYLES`). Functions with no counterpart yet are counted, not failed.
// Recorded calls: the committed sample `harness/ts_port/fixtures/calls/` and, when present, the full set `out/calls/`.

import assert from "node:assert/strict";
import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { test } from "node:test";
import { PyError } from "../src/pynum.ts";
import { NotPorted } from "../src/render.ts";
import { decode, same, type Enc, type Tally } from "./calls-codec.ts";
import { REPO_ROOT, TS_ROOT, loadJson } from "./fixtures.ts";

const SAMPLE = join(REPO_ROOT, "harness/ts_port/fixtures/calls");
const FULL = join(REPO_ROOT, "harness/ts_port/out/calls");

const camel = (py: string): string => {
  const parts = py.replace(/^_+/, "").split("_");
  return parts.map((p, i) => (i === 0 ? p : p.charAt(0).toUpperCase() + p.slice(1))).join("");
};

async function loadExports(): Promise<Map<string, unknown>> {
  const out = new Map<string, unknown>();
  const dir = join(TS_ROOT, "src");
  for (const f of readdirSync(dir).filter((n) => n.endsWith(".ts")).sort()) {
    const mod = (await import(pathToFileURL(join(dir, f)).href)) as Record<string, unknown>;
    for (const [k, v] of Object.entries(mod)) if (!out.has(k)) out.set(k, v);
  }
  return out;
}

type Call = { args: Enc[]; kwargs: Record<string, Enc>; result: Enc; count: number };
type Rec = { function: string; module: string; calls: Call[] };

async function replayAll(dir: string, t: { diagnostic: (m: string) => void }): Promise<void> {
  const exportsMap = await loadExports();
  const refs = (name: string): unknown => {
    const [table, ...path] = name.split(".");
    let v: unknown = exportsMap.get(table as string);
    for (const k of path) v = (v as Record<string, unknown> | undefined)?.[k];
    if (v === undefined) throw new Error(`registry object ${name} is not ported`);
    return v;
  };
  const signatures = loadJson<Record<string, string[]>>(join(SAMPLE, "_signatures.json"));
  const files = readdirSync(dir).filter((f) => f.endsWith(".json") && !f.startsWith("_")).sort();
  let ported = 0;
  let calls = 0;
  let notPortedCalls = 0;
  const tally: Tally = { exact: 0, withinUlps: 0 };
  const bad: string[] = [];
  for (const f of files) {
    const rec = loadJson<Rec>(join(dir, f));
    const fn = exportsMap.get(camel(rec.function)) ?? exportsMap.get(rec.function);
    if (typeof fn !== "function") continue;
    ported++;
    for (const c of rec.calls) {
      calls++;
      let args: unknown[];
      try {
        args = c.args.map((a) => decode(a, refs));
        // A keyword argument goes to its position; the gap is `undefined`, which takes the TypeScript default.
        for (const [name, v] of Object.entries(c.kwargs ?? {})) {
          const at = (signatures[rec.function] ?? []).indexOf(name);
          if (at < 0) throw new Error(`keyword ${name} is not in the signature of ${rec.function}`);
          while (args.length < at) args.push(undefined);
          args[at] = decode(v, refs);
        }
      } catch (e) {
        bad.push(`${rec.function}: cannot decode arguments (${(e as Error).message})`);
        continue;
      }
      const wantsError = c.result !== null && typeof c.result === "object" && "exc" in c.result;
      let got: unknown;
      let threw: string | null = null;
      try {
        got = (fn as (...a: unknown[]) => unknown)(...args);
      } catch (e) {
        if (e instanceof NotPorted) {
          notPortedCalls++;
          continue;
        }
        threw = e instanceof PyError ? e.pyType : String(e);
      }
      if (wantsError) {
        if (threw !== (c.result as { exc: string }).exc) bad.push(`${rec.function}: expected ${(c.result as { exc: string }).exc}, got ${threw ?? "a result"}`);
      } else if (threw !== null) {
        bad.push(`${rec.function}: threw ${threw} on ${JSON.stringify(c.args).slice(0, 160)} ${JSON.stringify(c.kwargs).slice(0, 200)}`);
      } else if (!same(c.result, got, refs, 4, tally)) {
        bad.push(`${rec.function}(${JSON.stringify(c.args).slice(0, 120)}): got ${JSON.stringify(got)?.slice(0, 120)}`);
      }
    }
  }
  t.diagnostic(`${dir.includes("out") ? "full" : "sample"}: ${ported} of ${files.length} functions ported, ${calls} recorded calls replayed; ${notPortedCalls} skipped for parts not ported yet; floats: ${tally.exact} exact, ${tally.withinUlps} within 4 ulp`);
  if (process.env.CALLS_SUMMARY) {
    const by = new Map<string, number>();
    for (const b of bad) by.set(b.split(":")[0]!.split("(")[0]!, (by.get(b.split(":")[0]!.split("(")[0]!) ?? 0) + 1);
    t.diagnostic(`differences by function: ${JSON.stringify([...by].sort((a, b) => b[1] - a[1]))}`);
  }
  assert.deepEqual(bad.slice(0, Number(process.env.CALLS_SHOW ?? 15)), [], `${bad.length} calls differ`);
}

test("every ported function reproduces its recorded Python calls (committed sample)", { skip: !existsSync(SAMPLE) && "no recorded calls yet (harness/ts_port/calls.py)" }, async (t) => {
  await replayAll(SAMPLE, t);
});
test("every ported function reproduces its recorded Python calls (full recording)", { skip: !existsSync(FULL) && "run calls.py record" }, async (t) => {
  await replayAll(FULL, t);
});
