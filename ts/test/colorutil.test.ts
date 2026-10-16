// colorutil (and the two colorsys functions it uses) against CPython, on every colour the presets use plus edge and
// random colours. Fixtures: harness/ts_port/colors.py.

import assert from "node:assert/strict";
import { join } from "node:path";
import { test } from "node:test";
import { highlightRise, litTone, shade, softShadowTone, tint } from "../src/colorutil.ts";
import { PyError } from "../src/pynum.ts";
import { TS_ROOT, decodeFloat, isErr, loadJson, sameBits } from "./fixtures.ts";

const rows = loadJson<Record<string, any>[]>(join(TS_ROOT, "fixtures", "colors.json"));

const calls: Record<string, (c: string) => string | number> = {
  shade: (c) => shade(c),
  shade62: (c) => shade(c, 0.62),
  shade_b13: (c) => shade(c, 0.87, 1.3),
  tint: (c) => tint(c),
  tint25: (c) => tint(c, 0.25),
  lit06: (c) => litTone(c, 0.06),
  lit12: (c) => litTone(c, 0.12),
  lit38: (c) => litTone(c, 0.38),
  lit_big: (c) => litTone(c, 0.9),
  rise: (c) => highlightRise(c),
  soft_g05: (c) => softShadowTone(c, 0.5),
  soft_g1: (c) => softShadowTone(c, 1.0),
  soft_g2: (c) => softShadowTone(c, 2.0),
};

for (const [name, fn] of Object.entries(calls)) {
  test(`colorutil ${name} equals Python on ${rows.length} colours`, () => {
    const bad: unknown[] = [];
    for (const row of rows) {
      const want = row[name];
      let got: unknown;
      try {
        got = fn(row.c);
      } catch (e) {
        got = { err: e instanceof PyError ? e.pyType : String(e) };
      }
      const ok = isErr(want)
        ? isErr(got) && (got as any).err === want.err
        : typeof want === "string" && want.startsWith("f:")
          ? typeof got === "number" && sameBits(got, decodeFloat(want))
          : got === want;
      if (!ok) bad.push([row.c, want, got]);
    }
    assert.equal(bad.length, 0, `${bad.length} differ; first: ${JSON.stringify(bad.slice(0, 5))}`);
  });
}
