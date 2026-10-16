// The head outline end to end: sin, cos and a fractional power from the maths library, then one-decimal text. This
// is where an engine's last-bit difference would show if it ever changed a printed digit.

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { test } from "node:test";
import { curve, headShape } from "../src/character.ts";
import { REPO_ROOT, TS_ROOT, exists, loadJson } from "./fixtures.ts";

type Row = [number, number, number, number, string];

function run(rows: Row[]): { bad: Row[]; numbers: number } {
  const bad: Row[] = [];
  for (const row of rows) {
    const [build, cx, cy, r, sha20] = row;
    const [start, segs] = headShape(build);
    const d = curve(cx, cy, r, start, segs);
    if (!createHash("sha256").update(d).digest("hex").startsWith(sha20)) bad.push(row);
  }
  return { bad, numbers: rows.length * 34 };
}

test("head outline text equals Python's over 8,000 random geometries", () => {
  const { bad } = run(loadJson<Row[]>(join(TS_ROOT, "fixtures", "headshape-sweep.json")));
  assert.equal(bad.length, 0, `${bad.length} differ; first: ${JSON.stringify(bad.slice(0, 3))}`);
});

const large = join(REPO_ROOT, "harness/ts_port/out/headshape-sweep-large.json");
test("head outline text equals Python's over 400,000 random geometries", { skip: !exists(large) && "generate with headshape_sweep.py 400000" }, (t) => {
  const rows = loadJson<Row[]>(large);
  const { bad, numbers } = run(rows);
  t.diagnostic(`${rows.length} outlines, ${numbers} printed numbers, ${bad.length} outlines differ`);
  assert.equal(bad.length, 0, `${bad.length} differ; first: ${JSON.stringify(bad.slice(0, 3))}`);
});
