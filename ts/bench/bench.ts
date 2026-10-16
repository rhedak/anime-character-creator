// How fast the ported slice runs in V8, against the per-layer times CPython measured on the same cases
// (`harness/ts_port/time_layers.py` writes `harness/ts_port/out/time-python.json`).
//
//   node bench/bench.ts

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { skeletonFor } from "../src/body.ts";
import { hatUnderside, mask, neck, softStrokeWidths } from "../src/character.ts";
import { fmtFixed } from "../src/pynum.ts";
import { sha1Hex } from "../src/sha1.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const corpus = JSON.parse(readFileSync(join(root, "harness/ts_port/corpus/mini.json"), "utf8")) as { id: string; params: any }[];
const py = JSON.parse(readFileSync(join(root, "harness/ts_port/out/time-python.json"), "utf8")) as { cases: Record<string, { layers_ms: Record<string, number>; total_ms: number }> };

const median = (xs: number[]): number => [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)] as number;

function timeMs(fn: () => unknown, reps: number): number {
  for (let i = 0; i < Math.min(reps, 200); i++) fn(); // warm up
  const runs: number[] = [];
  for (let r = 0; r < 7; r++) {
    const t0 = performance.now();
    for (let i = 0; i < reps; i++) fn();
    runs.push((performance.now() - t0) / reps);
  }
  return median(runs);
}

const layers: [string, (sk: any, p: any) => string][] = [
  ["layers[5] neck", neck],
  ["layers[22] mask", mask],
  ["layers[1] hat underside", hatUnderside],
];
console.log(`node ${process.version}, V8 ${process.versions.v8}\n`);
console.log("layer                        V8 median (us)   CPython median (us)   ratio (CPython / V8)");
for (const [label, fn] of layers) {
  const key = label.split(" ")[0] as string;
  const v8: number[] = [];
  const cp: number[] = [];
  for (const c of corpus) {
    const sk = skeletonFor(c.params);
    v8.push(timeMs(() => fn(sk, c.params), 300));
    const t = py.cases[c.id]?.layers_ms[key];
    if (t !== undefined) cp.push(t);
  }
  const a = median(v8) * 1000;
  const b = median(cp) * 1000;
  console.log(`${label.padEnd(28)} ${a.toFixed(2).padStart(10)} ${b.toFixed(2).padStart(20)} ${(b / a).toFixed(2).padStart(18)}`);
}

const skTimes = corpus.map((c) => timeMs(() => skeletonFor(c.params), 300));
console.log(`\nskeletonFor, median of 68 cases: ${(median(skTimes) * 1000).toFixed(2)} us`);

const xs = Array.from({ length: 4096 }, (_, i) => Math.sin(i) * 300 + i / 7);
let sink = 0;
const perCall = timeMs(() => { for (const x of xs) sink += fmtFixed(x, 1).length; }, 100) / xs.length;
console.log(`fmtFixed(x, 1): ${(perCall * 1e6).toFixed(0)} ns per call (CPython f"{x:.1f}" is about 150 to 250 ns)`);

const text = "x".repeat(60000);
console.log(`softStrokeWidths on a 60 KB body with no tags: ${timeMs(() => softStrokeWidths(text), 200).toFixed(3)} ms; sha1 of 40 chars: ${(timeMs(() => sha1Hex("M 100.0 20.5 L 30 40 Q 3 4 5 6 Z"), 5000) * 1000).toFixed(2)} us`);
void sink;
