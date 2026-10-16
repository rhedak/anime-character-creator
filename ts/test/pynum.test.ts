// The kernel against CPython. Expected values come from `harness/ts_port/synthetic.py`, which asks Python.
// A larger set (gitignored) is used as well when `harness/ts_port/out/synthetic-large.json` exists.

import assert from "node:assert/strict";
import { join } from "node:path";
import { test } from "node:test";
import {
  PyError,
  at,
  fmtFixed,
  fmtHex2,
  pyFloat,
  pyHex,
  pyHypot,
  pyMod,
  pyModInt,
  pyRepr,
  pyRound,
  pySlice,
  pySum,
  roundTo,
  sorted,
} from "../src/pynum.ts";
import { parseTemplate, pySub } from "../src/pyre.ts";
import { sha1Hex } from "../src/sha1.ts";
import { REPO_ROOT, TS_ROOT, decodeFloat, exists, isErr, loadJson, sameBits } from "./fixtures.ts";

const small = loadJson(join(TS_ROOT, "fixtures", "synthetic.json"));
const largePath = join(REPO_ROOT, "harness", "ts_port", "out", "synthetic-large.json");
const sets: [string, any][] = [["small", small]];
if (exists(largePath)) sets.push(["large", loadJson(largePath)]);

function report(name: string, bad: unknown[], total: number): void {
  assert.equal(bad.length, 0, `${name}: ${bad.length} of ${total} differ from Python; first: ${JSON.stringify(bad.slice(0, 5))}`);
}

for (const [label, fx] of sets) {
  test(`fmtFixed matches f"{x:.Nf}" (${label})`, () => {
    const bad: unknown[] = [];
    for (const [xv, d, want] of fx.fmt) {
      const got = fmtFixed(decodeFloat(xv), d);
      if (got !== want) bad.push([xv, decodeFloat(xv), d, want, got]);
    }
    report("fmt", bad, fx.fmt.length);
  });

  test(`pyRound is round() with ties to even (${label})`, () => {
    const bad: unknown[] = [];
    for (const [xv, want] of fx.round) {
      const x = decodeFloat(xv);
      if (isErr(want)) {
        try {
          pyRound(x);
          bad.push([x, want, "no error"]);
        } catch (e) {
          if (!(e instanceof PyError) || e.pyType !== want.err) bad.push([x, want, String(e)]);
        }
      } else if (pyRound(x) !== Number(want.slice(2))) {
        bad.push([x, want, pyRound(x)]);
      }
    }
    report("round", bad, fx.round.length);
  });

  test(`roundTo is round(x, n) (${label})`, () => {
    const bad: unknown[] = [];
    for (const [xv, n, want] of fx.roundTo) {
      const got = roundTo(decodeFloat(xv), n);
      if (!sameBits(got, decodeFloat(want))) bad.push([xv, decodeFloat(xv), n, decodeFloat(want), got]);
    }
    report("roundTo", bad, fx.roundTo.length);
  });

  test(`pyRepr is repr(float) (${label})`, () => {
    const bad: unknown[] = [];
    for (const [xv, want] of fx.repr) {
      const got = pyRepr(decodeFloat(xv));
      if (got !== want) bad.push([xv, want, got]);
    }
    report("repr", bad, fx.repr.length);
  });

  test(`pyMod is the float % operator (${label})`, () => {
    const bad: unknown[] = [];
    for (const [av, bv, want] of fx.mod) {
      const a = decodeFloat(av);
      const b = decodeFloat(bv);
      if (isErr(want)) {
        try {
          pyMod(a, b);
          bad.push([a, b, want, "no error"]);
        } catch (e) {
          if (!(e instanceof PyError) || e.pyType !== want.err) bad.push([a, b, want, String(e)]);
        }
      } else {
        const got = pyMod(a, b);
        if (!sameBits(got, decodeFloat(want))) bad.push([a, b, decodeFloat(want), got]);
      }
    }
    report("mod", bad, fx.mod.length);
  });

  test(`pySum is CPython 3.12+ sum (${label})`, () => {
    const bad: unknown[] = [];
    for (const [items, lead, want] of fx.sum) {
      const nums = (items as string[]).map((v) => (v.startsWith("i:") ? Number(v.slice(2)) : decodeFloat(v)));
      const got = pySum(nums, lead);
      if (!sameBits(got, decodeFloat(want))) bad.push([items.length, lead, decodeFloat(want), got]);
    }
    report("sum", bad, fx.sum.length);
  });

  test(`pyHypot is math.hypot, bit for bit (${label})`, () => {
    const bad: unknown[] = [];
    for (const [av, bv, want] of fx.hypot) {
      const got = pyHypot(decodeFloat(av), decodeFloat(bv));
      if (!sameBits(got, decodeFloat(want))) bad.push([decodeFloat(av), decodeFloat(bv), decodeFloat(want), got]);
    }
    report("hypot", bad, fx.hypot.length);
  });
}

test("fmtHex2 and pyModInt", () => {
  for (const [n, want] of small.hex2) assert.equal(fmtHex2(n), want);
  for (const [a, b, want] of small.modInt) assert.equal(pyModInt(a, b), Number(want.slice(2)), `${a} % ${b}`);
});

test("pySlice and at follow Python indexing", () => {
  const bad: unknown[] = [];
  for (const [list, start, stop, step, want] of small.slice) {
    const got = pySlice(list, start, stop, step);
    if (JSON.stringify(got) !== JSON.stringify(want)) bad.push([start, stop, step, want, got]);
  }
  report("slice", bad, small.slice.length);
  for (const [list, k, want] of small.at) {
    if (isErr(want)) assert.throws(() => at(list, k), PyError);
    else assert.equal(at(list, k), want);
  }
});

test("sha1Hex is hashlib.sha1", () => {
  const bad: unknown[] = [];
  for (const [text, want] of small.sha1) if (sha1Hex(text) !== want) bad.push([text.slice(0, 20), want, sha1Hex(text)]);
  report("sha1", bad, small.sha1.length);
});

test("re.sub templates: odd id prefixes give what Python gives", () => {
  const bad: unknown[] = [];
  for (const [body, pre, want] of small.template) {
    let got: string | { err: string };
    try {
      let r = pySub(/(?<![\p{L}\p{N}_])id="([^"]+)"/gu, `id="${pre}-\\1"`, body);
      r = pySub(/url\(#([^)]+)\)/g, `url(#${pre}-\\1)`, r);
      got = pySub(/href="#([^"]+)"/g, `href="#${pre}-\\1"`, r);
    } catch (e) {
      got = { err: e instanceof PyError ? e.pyType : String(e) };
    }
    const ok = isErr(want) ? isErr(got) && got.err === want.err : got === want;
    if (!ok) bad.push([pre, want, got]);
  }
  report("template", bad, small.template.length);
  assert.deepEqual(parseTemplate("a", 1), ["a"]);
});

test("pyFloat and pyHex accept and refuse as Python does, on the forms the code uses", () => {
  for (const [s, want] of small.pyFloat) {
    // Python also takes "1_0", "inf", "nan" and non-ASCII digits; the kernel refuses them (see the ledger).
    if (isErr(want) || !/^[0-9.eE+\- ]+$/.test(s)) continue;
    assert.ok(sameBits(pyFloat(s), decodeFloat(want)), `float(${JSON.stringify(s)})`);
  }
  for (const [s, want] of small.pyHex) {
    if (isErr(want)) assert.throws(() => pyHex(s), PyError, JSON.stringify(s));
    else if (/^[0-9a-fA-F]+$/.test(s)) assert.equal(pyHex(s), Number(want.slice(2)));
  }
});

test("sorted is numeric, not string order", () => {
  for (const [items, want] of small.sorted) {
    const nums = (items as string[]).map((v) => (v.startsWith("i:") ? Number(v.slice(2)) : decodeFloat(v)));
    const wantNums = (want as string[]).map((v) => (v.startsWith("i:") ? Number(v.slice(2)) : decodeFloat(v)));
    assert.deepEqual(sorted(nums), wantNums);
  }
});
