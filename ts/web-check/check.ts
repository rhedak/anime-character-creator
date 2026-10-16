// The cross-engine check: the kernel and the spike's slice of the drawing against what CPython recorded, run in
// whichever JavaScript engine loads this file (Node, Chrome, Firefox, Safari). Browser-safe: no Node imports. The
// page (`index.html`) and Node (`run.ts`) both call `runChecks`.

import { skeletonFor } from "../src/body.ts";
import { highlightRise, litTone, shade, softShadowTone, tint } from "../src/colorutil.ts";
import { documentWrap, hatUnderside, mask, neck } from "../src/character.ts";
import type { CharacterParams } from "../src/params.ts";
import { PyInt, dumps, type Json } from "../src/pyjson.ts";
import { fmtFixed, pyHypot, pyMod, pyRepr, pyRound, pySum, roundTo } from "../src/pynum.ts";
import { sha1Hex } from "../src/sha1.ts";
import type { Skeleton } from "../src/skeleton.ts";
import { sha256Hex } from "./sha256.ts";

export type Result = { name: string; total: number; bad: number; first: string[] };
export type FetchJson = (path: string) => Promise<any>;

const dv = new DataView(new ArrayBuffer(8));
function dec(v: string): number {
  dv.setUint32(0, parseInt(v.slice(2, 10), 16));
  dv.setUint32(4, parseInt(v.slice(10, 18), 16));
  return dv.getFloat64(0);
}
const bitsOf = (x: number): string => {
  dv.setFloat64(0, x);
  return `${dv.getUint32(0)}:${dv.getUint32(4)}`;
};
const same = (a: number, b: number): boolean => bitsOf(a) === bitsOf(b) || (a !== a && b !== b);
const num = (v: string): number => (v.startsWith("i:") ? Number(v.slice(2)) : dec(v));

function tally(name: string, rows: readonly unknown[], test: (row: any) => string | null): Result {
  let bad = 0;
  const first: string[] = [];
  for (const row of rows) {
    const msg = test(row);
    if (msg !== null) {
      bad++;
      if (first.length < 3) first.push(msg);
    }
  }
  return { name, total: rows.length, bad, first };
}

const skeletonJson = (sk: Skeleton): Json => ({
  ...(sk as unknown as Record<string, Json>),
  canvas_w: new PyInt(sk.canvas_w),
  canvas_h: new PyInt(sk.canvas_h),
});

export async function runChecks(get: FetchJson): Promise<Result[]> {
  const out: Result[] = [];
  const syn = await get("fixtures/synthetic.json");
  out.push(tally("float format .Nf", syn.fmt, ([x, d, want]) => (fmtFixed(dec(x), d) === want ? null : `${dec(x)} .${d}f want ${want} got ${fmtFixed(dec(x), d)}`)));
  out.push(tally("round()", syn.round, ([x, want]) => (typeof want === "string" ? (pyRound(dec(x)) === Number(want.slice(2)) ? null : `${dec(x)}`) : null)));
  out.push(tally("round(x, n)", syn.roundTo, ([x, n, want]) => (same(roundTo(dec(x), n), dec(want)) ? null : `${dec(x)}, ${n}`)));
  out.push(tally("float repr", syn.repr, ([x, want]) => (pyRepr(dec(x)) === want ? null : `${dec(x)} want ${want} got ${pyRepr(dec(x))}`)));
  out.push(tally("float %", syn.mod, ([a, b, want]) => (typeof want === "string" && !same(pyMod(dec(a), dec(b)), dec(want)) ? `${dec(a)} % ${dec(b)}` : null)));
  out.push(tally("sum() (3.12 compensated)", syn.sum, ([items, lead, want]) => (same(pySum((items as string[]).map(num), lead), dec(want)) ? null : `${items.length} items`)));
  out.push(tally("math.hypot, bit for bit", syn.hypot, ([a, b, want]) => (same(pyHypot(dec(a), dec(b)), dec(want)) ? null : `${dec(a)}, ${dec(b)}`)));
  out.push(tally("sha1", syn.sha1, ([text, want]) => (sha1Hex(text) === want ? null : text.slice(0, 20))));

  const colors = await get("fixtures/colors.json");
  const ops: Record<string, (c: string) => string | number> = {
    shade: (c) => shade(c), shade62: (c) => shade(c, 0.62), tint: (c) => tint(c), lit12: (c) => litTone(c, 0.12), lit38: (c) => litTone(c, 0.38),
    rise: (c) => highlightRise(c), soft_g05: (c) => softShadowTone(c, 0.5), soft_g2: (c) => softShadowTone(c, 2.0),
  };
  out.push(
    tally("colour tones (colorsys)", colors, (row) => {
      for (const [k, fn] of Object.entries(ops)) {
        const want = row[k];
        if (typeof want === "object") continue;
        let got: string | number;
        try { got = fn(row.c); } catch { return `${row.c} ${k} threw`; }
        const ok = typeof got === "number" ? same(got, dec(want)) : got === want;
        if (!ok) return `${row.c} ${k} want ${want} got ${got}`;
      }
      return null;
    }),
  );

  const sweep = await get("fixtures/skeleton-sweep.json");
  const corpus = await get("../harness/ts_port/corpus/mini.json");
  const manifest = await get("../harness/ts_port/manifest/mini.json");
  const base: CharacterParams = corpus.find((c: any) => c.id === "satoko-flat").params;
  out.push(
    tally("skeleton sweep (trig, pow)", sweep, ([body, height, frame, bust, shift, age, hat, sha20]) => {
      const p = { ...base, body, height, frame, bust, waist_shift: shift, face_age: age, outfit: { ...base.outfit, hat_color: hat } };
      return sha256Hex(dumps(skeletonJson(skeletonFor(p)), { sortKeys: true, compact: true })).startsWith(sha20) ? null : `${body} h${height}`;
    }),
  );
  out.push(
    tally("skeleton, 68 characters", corpus, (c: any) =>
      sha256Hex(dumps(skeletonJson(skeletonFor(c.params)), { sortKeys: true, compact: true })) === manifest.cases[c.id].skeleton_sha256 ? null : c.id,
    ),
  );
  const layerFns: Record<string, (sk: Skeleton, p: CharacterParams) => string> = { "layers[1]": hatUnderside, "layers[5]": neck, "layers[22]": mask };
  for (const [name, fn] of Object.entries(layerFns)) {
    out.push(
      tally(`${name} drawing (${name === "layers[5]" ? "neck" : name === "layers[1]" ? "hat underside" : "mask"})`, corpus, (c: any) => {
        const want = manifest.cases[c.id].stages.find((s: any) => s.name === name);
        const got = fn(skeletonFor(c.params), c.params);
        return got.length === want.len && sha256Hex(got) === want.sha256 ? null : c.id;
      }),
    );
  }
  void documentWrap;
  return out;
}
