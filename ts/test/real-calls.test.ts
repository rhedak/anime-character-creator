// The kernel against every numeric call CPython made while rendering the wide corpus (`harness/ts_port/record.py`).
//
// MUST MATCH: formatting, round, sum, mod, hypot (CPython's own algorithm), sqrt, radians, degrees, copysign.
// MEASURED, not asserted: sin, cos, atan2, acos and `**`, which come from the C library in Python and from V8 here.
// Their mismatch counts are the point; they go to the test log and to `ts/out/libm-report.json`.
//
// Uses the committed sample, and the full 100+ MB recording too when `harness/ts_port/out/real-calls.json` exists.

import assert from "node:assert/strict";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import {
  copysign,
  degrees,
  fmtFixed,
  fmtHex2,
  pyHypot,
  pyMod,
  pyModInt,
  pyRound,
  pySqrt,
  pySum,
  radians,
  roundTo,
} from "../src/pynum.ts";
import { REPO_ROOT, TS_ROOT, decodeFloat, exists, loadJson, sameBits } from "./fixtures.ts";

const SAMPLE = join(REPO_ROOT, "harness/ts_port/fixtures/real-calls.sample.json");
const FULL = join(REPO_ROOT, "harness/ts_port/out/real-calls.json");

const isInt = (v: string): boolean => v.startsWith("i:");
const num = (v: string): number => (isInt(v) ? Number(v.slice(2)) : decodeFloat(v));

type Counts = { total: number; bad: number; first: unknown[] };
const fresh = (): Counts => ({ total: 0, bad: 0, first: [] });
function note(c: Counts, ok: boolean, info: () => unknown): void {
  c.total++;
  if (!ok) {
    c.bad++;
    if (c.first.length < 4) c.first.push(info());
  }
}

function replay(d: any): Record<string, Counts> {
  const r: Record<string, Counts> = {};
  const at = (k: string): Counts => (r[k] ??= fresh());
  for (const [v, spec, out] of d.fmt) {
    const c = at("fmt");
    if (spec === "02x") note(c, fmtHex2(num(v)) === out, () => [v, spec, out]);
    else note(c, fmtFixed(num(v), Number(spec[1])) === out, () => [num(v), spec, out, fmtFixed(num(v), Number(spec[1]))]);
  }
  for (const [v, nd, out] of d.round) {
    const c = at("round");
    if (nd === null) note(c, pyRound(num(v)) === num(out), () => [num(v), out]);
    else {
      const n = typeof nd === "string" ? num(nd) : nd;
      note(c, sameBits(roundTo(num(v), n), num(out)), () => [num(v), n, num(out), roundTo(num(v), n)]);
    }
  }
  for (const [items, start, out] of d.sum) {
    const c = at("sum");
    let lead = 0;
    while (lead < items.length && isInt(items[lead])) lead++;
    const values = items.map(num);
    const withStart = start === "i:0" ? values : [num(start), ...values];
    note(c, sameBits(pySum(withStart, start === "i:0" ? lead : 0), num(out)), () => [items.length, num(out), pySum(withStart, lead)]);
  }
  for (const [a, b, out] of d.mod) {
    const c = at("mod");
    const got = isInt(a) && isInt(b) ? pyModInt(num(a), num(b)) : pyMod(num(a), num(b));
    note(c, sameBits(got, num(out)), () => [a, b, out, got]);
  }
  for (const [a, b, out] of d.pow) {
    const A = num(a);
    const B = num(b);
    note(at("pow (V8 Math.pow)"), sameBits(Math.pow(A, B), num(out)), () => [A, B, num(out), Math.pow(A, B)]);
    if (B === 2) note(at("pow (x*x for x**2)"), sameBits(A * A, num(out)), () => [A, num(out), A * A]);
  }
  const m = d.math;
  const unary: Record<string, [(x: number) => number, boolean]> = {
    sin: [Math.sin, false],
    cos: [Math.cos, false],
    acos: [Math.acos, false],
    sqrt: [pySqrt, true],
    radians: [radians, true],
    degrees: [degrees, true],
  };
  for (const [name, [fn, must]] of Object.entries(unary)) {
    for (const row of m[name] ?? []) {
      const x = num(row[0]);
      const want = num(row[1]);
      note(at(`${name}${must ? "" : " (V8)"}`), sameBits(fn(x), want), () => [x, want, fn(x)]);
    }
  }
  for (const [a, b, out] of m.atan2 ?? []) note(at("atan2 (V8)"), sameBits(Math.atan2(num(a), num(b)), num(out)), () => [num(a), num(b)]);
  for (const [a, b, out] of m.hypot ?? []) {
    note(at("hypot (CPython algorithm)"), sameBits(pyHypot(num(a), num(b)), num(out)), () => [num(a), num(b), num(out), pyHypot(num(a), num(b))]);
    note(at("hypot (V8 Math.hypot, for comparison)"), sameBits(Math.hypot(num(a), num(b)), num(out)), () => []);
    note(at("hypot (sqrt(x*x+y*y), for comparison)"), sameBits(Math.sqrt(num(a) * num(a) + num(b) * num(b)), num(out)), () => []);
  }
  for (const [a, b, out] of m.copysign ?? []) note(at("copysign"), sameBits(copysign(num(a), num(b)), num(out)), () => [a, b, out]);
  return r;
}

const MUST = ["fmt", "round", "sum", "mod", "hypot (CPython algorithm)", "sqrt", "radians", "degrees", "copysign"];

function run(label: string, data: any, t: { diagnostic: (m: string) => void }): void {
  const r = replay(data);
  const lines = Object.entries(r).map(([k, c]) => `${k.padEnd(42)} ${String(c.total).padStart(9)} calls, ${String(c.bad).padStart(7)} differ (${((100 * c.bad) / Math.max(1, c.total)).toFixed(3)}%)`);
  t.diagnostic(`${label}:\n${lines.join("\n")}`);
  mkdirSync(join(TS_ROOT, "out"), { recursive: true });
  writeFileSync(join(TS_ROOT, "out", `libm-report-${label}.json`), JSON.stringify(r, null, 1));
  for (const k of MUST) {
    const c = r[k];
    if (c === undefined) continue;
    assert.equal(c.bad, 0, `${label} ${k}: ${c.bad} of ${c.total} differ from CPython; first: ${JSON.stringify(c.first)}`);
  }
}

test("kernel vs the recorded sample of real calls", (t) => run("sample", loadJson(SAMPLE), t));
test("kernel vs the full recording of real calls", { skip: !exists(FULL) && "run record.py record" }, (t) => run("full", loadJson(FULL), t));
