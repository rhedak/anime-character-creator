// The skeleton of every mini-corpus case against the committed manifest: sha256 of Python's compact, key-sorted
// `json.dumps` of `asdict(skeleton_for(p))`. Needs no Python at test time.

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { test } from "node:test";
import { skeletonFor } from "../src/body.ts";
import type { CharacterParams } from "../src/params.ts";
import { PyInt, dumps, type Json } from "../src/pyjson.ts";
import { PyError } from "../src/pynum.ts";
import { buildSkeleton, type Skeleton } from "../src/skeleton.ts";
import { REPO_ROOT, loadJson } from "./fixtures.ts";

const corpus = loadJson<{ id: string; params: CharacterParams }[]>(join(REPO_ROOT, "harness/ts_port/corpus/mini.json"));
const manifest = loadJson<{ cases: Record<string, { skeleton_sha256: string }> }>(join(REPO_ROOT, "harness/ts_port/manifest/mini.json"));

/** The skeleton as Python's `asdict` holds it: the two canvas sizes are ints there, everything else a float. */
export function skeletonJson(sk: Skeleton): Json {
  return { ...(sk as unknown as Record<string, Json>), canvas_w: new PyInt(sk.canvas_w), canvas_h: new PyInt(sk.canvas_h) };
}

test("skeletonFor reproduces Python's skeleton for every mini-corpus case", () => {
  const bad: string[] = [];
  for (const c of corpus) {
    const got = createHash("sha256").update(dumps(skeletonJson(skeletonFor(c.params)), { sortKeys: true, compact: true })).digest("hex");
    if (got !== manifest.cases[c.id]?.skeleton_sha256) bad.push(c.id);
  }
  assert.deepEqual(bad, []);
  assert.ok(corpus.length >= 60);
});

test("skeletonFor over a sweep of bodies, heights, frames, busts, shifts, ages and hats", () => {
  const rows = loadJson<[string, number, number, number, number, number, string | null, string][]>(join(REPO_ROOT, "ts/fixtures/skeleton-sweep.json"));
  const base = corpus.find((c) => c.id === "satoko-flat")!.params;
  const bad: unknown[] = [];
  for (const [body, height, frame, bust, waistShift, faceAge, hat, sha20] of rows) {
    const params: CharacterParams = {
      ...base,
      body,
      height,
      frame,
      bust,
      waist_shift: waistShift,
      face_age: faceAge,
      outfit: { ...base.outfit, hat_color: hat },
    };
    const got = createHash("sha256").update(dumps(skeletonJson(skeletonFor(params)), { sortKeys: true, compact: true })).digest("hex");
    if (!got.startsWith(sha20)) bad.push([body, height, frame, bust, waistShift, faceAge, hat]);
  }
  assert.equal(bad.length, 0, `${bad.length} of ${rows.length} differ; first: ${JSON.stringify(bad.slice(0, 3))}`);
});

test("a division by zero raises, as in Python, where JavaScript would give Infinity or NaN", () => {
  assert.throws(() => buildSkeleton({ heads: 0 }), (e: unknown) => e instanceof PyError && e.pyType === "ZeroDivisionError");
  assert.throws(() => skeletonFor({ ...corpus[0]!.params, body: "nope" }), (e: unknown) => e instanceof PyError && e.pyType === "KeyError");
});
