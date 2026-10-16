// The function-level oracle for the `core-limbs` module: every recorded Python call of every function the module owns
// (`harness/ts_port/modules.json`), replayed against the TypeScript port, private functions (a leading underscore) included.
// The same replay as `calls.test.ts`, restricted to this module's names and not skipping the files whose function name
// starts with an underscore.

import assert from "node:assert/strict";
import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { test } from "node:test";
import { bustPieces } from "../src/core-limbs.ts";
import { classOf } from "../src/model.ts";
import { plainParams } from "../src/plain.ts";
import { PyInt } from "../src/pyjson.ts";
import { BadValue, PyError } from "../src/pynum.ts";
import { PyFloat } from "../src/pyvalue.ts";
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

const mine = (): Set<string> => {
  const modules = loadJson<Record<string, { names: { name: string; kind: string }[] }>>(join(REPO_ROOT, "harness/ts_port/modules.json"));
  return new Set((modules["core-limbs"] as { names: { name: string; kind: string }[] }).names.filter((n) => n.kind === "def").map((n) => n.name));
};

/**
 * The recorded arguments as the real flow hands them to a part: a `CharacterParams` through `plainParams`, a `Skeleton` as
 * `buildSkeleton` stores one (a number field holding a string or a list is a `BadValue`, an int is a plain number). The
 * codec decodes a dataclass as its raw fields, with the int markers a link needs.
 */
function normalize(v: unknown): unknown {
  if (Array.isArray(v)) return v.map(normalize);
  if (v === null || typeof v !== "object" || v instanceof Set || v instanceof Map) return v;
  const o = v as Record<string, unknown>;
  if (classOf(o) === "CharacterParams") return plainParams(o as never);
  if ("canvas_w" in o && "waist_half_w" in o && "head_cx" in o) {
    return Object.fromEntries(
      Object.entries(o).map(([k, x]) => {
        if (x instanceof PyInt) return [k, Number(x.value)];
        if (x instanceof PyFloat) return [k, x.value];
        // `wrist_x` and `wrist_y` are the two fields that may be None.
        if ((x === null && (k === "wrist_x" || k === "wrist_y")) || typeof x === "number" || typeof x === "boolean" || x instanceof BadValue) return [k, x];
        return [k, new BadValue(x)];
      }),
    );
  }
  return v;
}

// The parameters that are numbers: a string or a list there is what `plainParams` turns into a `BadValue` in the real flow.
const NUMBER_PARAMS = new Set(["length", "length_chibi", "x_off", "tip_y", "peak_y", "inset", "weight", "y", "scale", "w", "cx", "cy", "wrist_y", "w_top", "elbow_x", "wrist_x", "w_elbow", "w_wrist", "min_ry"]);
const asParam = (fn: string, signatures: Record<string, string[]>, i: number, v: unknown): unknown =>
  (typeof v === "string" || Array.isArray(v)) && NUMBER_PARAMS.has((signatures[fn] ?? [])[i] as string) ? new BadValue(v) : v;

// A method of a dataclass is recorded as `Class.method` with the instance first; the port keeps it as a function.
const METHODS: Record<string, (...a: any[]) => unknown> = { "_Bust.pieces": (self: Parameters<typeof bustPieces>[0]) => bustPieces(self) };

async function replay(dir: string, t: { diagnostic: (m: string) => void }): Promise<void> {
  const exportsMap = await loadExports();
  const refs = (name: string): unknown => {
    const [table, ...path] = name.split(".");
    let v: unknown = exportsMap.get(table as string);
    for (const k of path) v = (v as Record<string, unknown> | undefined)?.[k];
    if (v === undefined) throw new Error(`registry object ${name} is not ported`);
    return v;
  };
  const signatures = loadJson<Record<string, string[]>>(join(SAMPLE, "_signatures.json"));
  const names = mine();
  const wanted = new Set([...names, ...Object.keys(METHODS)]);
  const files = readdirSync(dir).filter((f) => f.endsWith(".json") && f !== "_signatures.json");
  let ported = 0;
  let calls = 0;
  let recorded = 0;
  let waiting = 0;
  const tally: Tally = { exact: 0, withinUlps: 0 };
  const bad: string[] = [];
  const seen = new Set<string>();
  const inexact = new Map<string, number>();
  for (const f of files.sort()) {
    const rec = loadJson<Rec>(join(dir, f));
    if (!wanted.has(rec.function)) continue;
    recorded++;
    seen.add(rec.function);
    const fn = METHODS[rec.function] ?? exportsMap.get(camel(rec.function)) ?? exportsMap.get(rec.function);
    if (typeof fn !== "function") continue;
    ported++;
    for (const c of rec.calls) {
      calls++;
      let args: unknown[];
      try {
        args = c.args.map((a, i) => asParam(rec.function, signatures, i, normalize(decode(a, refs))));
        for (const [name, v] of Object.entries(c.kwargs ?? {})) {
          const at = (signatures[rec.function] ?? []).indexOf(name);
          if (at < 0) throw new Error(`keyword ${name} is not in the signature of ${rec.function}`);
          while (args.length < at) args.push(undefined);
          args[at] = normalize(decode(v, refs));
        }
      } catch (e) {
        // A registry object of another module's (a collar cut, a skirt cut) is not there until that module is ported.
        if (/^registry object .* is not ported$/.test((e as Error).message)) {
          waiting++;
          continue;
        }
        bad.push(`${rec.function}: cannot decode arguments (${(e as Error).message})`);
        continue;
      }
      const wantsError = c.result !== null && typeof c.result === "object" && "exc" in c.result;
      const before = tally.withinUlps;
      let got: unknown;
      let threw: string | null = null;
      try {
        got = (fn as (...a: unknown[]) => unknown)(...args);
      } catch (e) {
        if (e instanceof NotPorted) continue;
        threw = e instanceof PyError ? e.pyType : String(e);
      }
      if (wantsError) {
        if (threw !== (c.result as { exc: string }).exc) bad.push(`${rec.function}: expected ${(c.result as { exc: string }).exc}, got ${threw ?? "a result"}`);
      } else if (threw !== null) {
        bad.push(`${rec.function}: threw ${threw} on ${JSON.stringify(c.args).slice(0, 160)} ${JSON.stringify(c.kwargs).slice(0, 200)}`);
      } else if (!same(c.result, got, refs, 4, tally)) {
        bad.push(`${rec.function}(${JSON.stringify(c.args).slice(0, 120)}): got ${JSON.stringify(got)?.slice(0, 120)}`);
      }
      if (tally.withinUlps > before) inexact.set(rec.function, (inexact.get(rec.function) ?? 0) + tally.withinUlps - before);
    }
  }
  const none = [...names].filter((n) => !seen.has(n)).sort();
  t.diagnostic(
    `${dir.includes("out") ? "full" : "sample"}: ${ported} of ${recorded} recorded core-limbs functions ported, ${calls} calls replayed, ` +
      `floats ${tally.exact} exact and ${tally.withinUlps} within 4 ulp; ${waiting} calls wait for another module's registry objects; floats within 4 ulp by function: ${JSON.stringify([...inexact])}; ${none.length} functions of the module have no recording: ${none.join(" ")}`,
  );
  assert.deepEqual(bad.slice(0, Number(process.env.CALLS_SHOW ?? 15)), [], `${bad.length} calls differ`);
}

test("core-limbs reproduces its recorded Python calls (committed sample)", { skip: !existsSync(SAMPLE) && "no recorded calls" }, async (t) => {
  await replay(SAMPLE, t);
});
test("core-limbs reproduces its recorded Python calls (full recording)", { skip: !existsSync(FULL) && "run calls.py record" }, async (t) => {
  await replay(FULL, t);
});
