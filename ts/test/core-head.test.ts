// The core-head module against Python: every recorded call of every function `harness/ts_port/modules.json` lists under
// "core-head" is replayed and must give what Python gave.
//
// `calls.test.ts` skips every record whose file name starts with an underscore, which is every private Python function,
// so it never reaches the hair system; this test names the module's functions itself. The committed sample is always
// replayed, and the full recording (`harness/ts_port/out/calls/`, 150 MB, not committed) when it is on disk.

import assert from "node:assert/strict";
import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import * as character from "../src/character.ts";
import * as head from "../src/core-head.ts";
import * as model from "../src/model.ts";
import { PyError } from "../src/pynum.ts";
import { decode, same, type Enc, type Tally } from "./calls-codec.ts";
import { REPO_ROOT, loadJson } from "./fixtures.ts";

const SAMPLE = join(REPO_ROOT, "harness/ts_port/fixtures/calls");
const FULL = join(REPO_ROOT, "harness/ts_port/out/calls");

type Call = { args: Enc[]; kwargs: Record<string, Enc>; result: Enc; count: number };
type Rec = { function: string; module: string; calls: Call[] };
type Fn = (...a: unknown[]) => unknown;

const camel = (py: string): string =>
  py
    .replace(/^_+/, "")
    .split("_")
    .map((p, i) => (i === 0 ? p : p.charAt(0).toUpperCase() + p.slice(1)))
    .join("");

/** The module's function names, from the ownership table. */
const modules = loadJson<Record<string, { names: { name: string; kind: string }[] }>>(join(REPO_ROOT, "harness/ts_port/modules.json"));
const MINE = new Set(modules["core-head"]!.names.filter((n) => n.kind === "def").map((n) => n.name));

/** Functions of the module that character.ts and model.ts ported first (core-common); they are replayed too. */
const found = (py: string): Fn | undefined => {
  const name = camel(py);
  for (const m of [head, character, model] as Record<string, unknown>[]) {
    if (typeof m[name] === "function") return m[name] as Fn;
  }
  return undefined;
};

const refs = (name: string): unknown => {
  const [table, ...path] = name.split(".");
  let v: unknown = (head as Record<string, unknown>)[table as string];
  for (const k of path) v = (v as Record<string, unknown> | undefined)?.[k];
  if (v === undefined) throw new Error(`registry object ${name} is not exported`);
  return v;
};

function replay(dir: string, t: { diagnostic: (m: string) => void }): { functions: Set<string>; calls: number } {
  const signatures = loadJson<Record<string, string[]>>(join(SAMPLE, "_signatures.json"));
  const functions = new Set<string>();
  const bad: string[] = [];
  const tally: Tally = { exact: 0, withinUlps: 0 };
  let calls = 0;
  for (const f of readdirSync(dir).filter((n) => n.endsWith(".json") && n !== "_signatures.json").sort()) {
    const rec = loadJson<Rec>(join(dir, f));
    if (!rec.function || !MINE.has(rec.function) || rec.module !== "character") continue;
    const fn = found(rec.function);
    if (fn === undefined) {
      bad.push(`${rec.function}: not exported`);
      continue;
    }
    functions.add(rec.function);
    for (const c of rec.calls) {
      calls++;
      const args = c.args.map((a) => decode(a, refs));
      for (const [name, v] of Object.entries(c.kwargs ?? {})) {
        const at = (signatures[rec.function] ?? []).indexOf(name);
        assert.ok(at >= 0, `keyword ${name} is not in the signature of ${rec.function}`);
        while (args.length < at) args.push(undefined);
        args[at] = decode(v, refs);
      }
      const wantsError = c.result !== null && typeof c.result === "object" && "exc" in c.result;
      let got: unknown;
      let threw: string | null = null;
      try {
        got = fn(...args);
      } catch (e) {
        threw = e instanceof PyError ? e.pyType : String(e);
      }
      if (wantsError) {
        if (threw !== (c.result as { exc: string }).exc) bad.push(`${rec.function}: expected ${(c.result as { exc: string }).exc}, got ${threw ?? "a result"}`);
      } else if (threw !== null) {
        bad.push(`${rec.function}: threw ${threw} on ${JSON.stringify(c.args).slice(0, 160)}`);
      } else if (!same(c.result, got, refs, 4, tally)) {
        bad.push(`${rec.function}(${JSON.stringify(c.args).slice(0, 120)}): got ${JSON.stringify(got)?.slice(0, 120)}`);
      }
    }
  }
  t.diagnostic(`${dir === FULL ? "full" : "sample"}: ${functions.size} functions, ${calls} recorded calls; floats: ${tally.exact} exact, ${tally.withinUlps} within 4 ulp`);
  assert.deepEqual(bad.slice(0, 15), [], `${bad.length} calls differ`);
  return { functions, calls };
}

test("core-head: the committed sample of recorded calls", { skip: !existsSync(SAMPLE) && "no recorded calls" }, (t) => {
  const { calls } = replay(SAMPLE, t);
  assert.ok(calls > 100, "the sample should reach the module");
});

test("core-head: the full recording, every function of the module that was ever called", { skip: !existsSync(FULL) && "run calls.py record" }, (t) => {
  const { functions, calls } = replay(FULL, t);
  assert.ok(calls > 5000, `only ${calls} calls replayed`);
  const missing = [...MINE].filter((n) => !functions.has(n));
  assert.deepEqual(missing, [], "functions of the module with no recorded calls (or no export)");
});

test("core-head: HAIRSTYLES holds the eight cuts, in Python's order, and an unknown name is a KeyError", () => {
  assert.deepEqual(Object.keys(head.HAIRSTYLES), [
    "long_blunt",
    "short_layered",
    "long_center_part",
    "long_traced",
    "long_parted",
    "long_fringed",
    "short_crop",
    "short_tousled",
  ]);
  assert.throws(() => head.hairstyleFor("constructor"), (e: unknown) => e instanceof PyError && e.pyType === "KeyError");
});
