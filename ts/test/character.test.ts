// The spike's slice of the drawing against the Python stage oracle.
//
//  * Layers: `neck`, `mask` and `hatUnderside` against the committed manifest (sha256 and length of each stage).
//  * Post-steps: `softStrokeWidths`, `namespaceIds` and `documentWrap` on the recorded body strings, when the
//    ignored `harness/ts_port/out/stages/` dumps exist (`manifest.py dump`).

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { test } from "node:test";
import { skeletonFor } from "../src/body.ts";
import { documentWrap, hatUnderside, mask, namespaceIds, neck, soft, softStrokeWidths } from "../src/character.ts";
import type { CharacterParams } from "../src/params.ts";
import { REPO_ROOT, exists, loadJson } from "./fixtures.ts";

type Case = { id: string; params: CharacterParams; kwargs: { id_prefix?: string; background?: string } };
type Stage = { name: string; sha256: string; len: number };

const corpus = loadJson<Case[]>(join(REPO_ROOT, "harness/ts_port/corpus/mini.json"));
const manifest = loadJson<{ cases: Record<string, { stages: Stage[] }> }>(join(REPO_ROOT, "harness/ts_port/manifest/mini.json"));
const sha = (s: string): string => createHash("sha256").update(s, "utf8").digest("hex");

const LAYERS: Record<string, (c: Case) => string> = {
  "layers[1]": (c) => hatUnderside(skeletonFor(c.params), c.params),
  "layers[5]": (c) => neck(skeletonFor(c.params), c.params),
  "layers[22]": (c) => mask(skeletonFor(c.params), c.params),
};

for (const [name, fn] of Object.entries(LAYERS)) {
  test(`${name} matches Python on every mini-corpus case`, () => {
    const bad: string[] = [];
    let nonEmpty = 0;
    for (const c of corpus) {
      const want = manifest.cases[c.id]!.stages.find((s) => s.name === name)!;
      const got = fn(c);
      if (got.length > 0) nonEmpty++;
      if (got.length !== want.len || sha(got) !== want.sha256) bad.push(c.id);
    }
    assert.deepEqual(bad, []);
    assert.ok(nonEmpty >= 2, `${name} was empty on every case, so this tested nothing`);
  });
}

const stagesDir = join(REPO_ROOT, "harness/ts_port/out/stages");
test("post-steps and the document wrapper reproduce the recorded strings", { skip: !exists(stagesDir) && "run manifest.py dump" }, () => {
  const bad: string[] = [];
  let softCases = 0;
  let prefixed = 0;
  for (const c of corpus) {
    const d = loadJson<{ stages: { name: string; text: string }[]; kwargs: Case["kwargs"] }>(join(stagesDir, `${c.id}.json`));
    const text = (n: string): string => d.stages.find((s) => s.name === n)!.text;
    const sk = skeletonFor(c.params);
    let body = text("body");
    if (soft(c.params)) {
      softCases++;
      body = softStrokeWidths(body);
    }
    if (body !== text("body_soft")) bad.push(`${c.id}: body_soft`);
    const prefix = c.kwargs.id_prefix ?? "";
    if (prefix) prefixed++;
    const ns = prefix ? namespaceIds(body, prefix) : body;
    if (ns !== text("body_ns")) bad.push(`${c.id}: body_ns`);
    if (documentWrap(sk, ns, c.kwargs.background ?? null) !== text("doc")) bad.push(`${c.id}: doc`);
  }
  assert.deepEqual(bad, []);
  assert.ok(softCases > 10 && prefixed > 3);
});
