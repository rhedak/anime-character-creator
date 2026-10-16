// The generic stage test: for every corpus case, every stage the port can produce is compared with Python's, by sha256 and
// length. Stages that need a part that is not ported yet are skipped and counted, so this passes while the port is
// partial, fails the moment a ported part draws something different, and shows how far the port has got.
//
// Source of the expected hashes: the committed mini manifest (68 cases, 58 stages each), and, when it exists, the full
// per-stage manifest `harness/ts_port/out/full-stages.json` (`manifest_full.py build`).

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { test } from "node:test";
import type { CharacterParams } from "../src/params.ts";
import { renderStages } from "../src/render.ts";
import { loadFullCorpus, loadFullManifest, loadFullStages, sha256 as shaFull } from "./corpus.ts";
import { REPO_ROOT, loadJson } from "./fixtures.ts";

type Case = { id: string; params: CharacterParams; kwargs: { id_prefix?: string; background?: string } };
type Stage = { name: string; sha256: string; len: number };

const corpus = loadJson<Case[]>(join(REPO_ROOT, "harness/ts_port/corpus/mini.json"));
const manifest = loadJson<{ cases: Record<string, { stages: Stage[] }> }>(join(REPO_ROOT, "harness/ts_port/manifest/mini.json"));
const sha = (s: string): string => createHash("sha256").update(s, "utf8").digest("hex");

test("every stage the port can produce equals Python's, on the 68 mini cases", (t) => {
  const bad: string[] = [];
  let compared = 0;
  let skipped = 0;
  const nonEmpty = new Set<string>();
  const stillMissing = new Set<string>();
  for (const c of corpus) {
    const { stages, missing } = renderStages(c.params, { id_prefix: c.kwargs.id_prefix ?? "", background: c.kwargs.background ?? null });
    for (const m of missing) stillMissing.add(m);
    for (const want of manifest.cases[c.id]!.stages) {
      const got = stages.get(want.name);
      if (got === undefined) {
        bad.push(`${c.id}: no stage ${want.name}`);
        continue;
      }
      if (got === null) {
        skipped++;
        continue;
      }
      compared++;
      if (got.length > 0) nonEmpty.add(want.name);
      if (got.length !== want.len || sha(got) !== want.sha256) bad.push(`${c.id}: ${want.name}`);
    }
  }
  t.diagnostic(`compared ${compared} stages, skipped ${skipped} (need an unported part); ${nonEmpty.size} stage names produced text; ${stillMissing.size} parts still to port`);
  assert.deepEqual(bad.slice(0, 20), [], `${bad.length} stages differ`);
  assert.ok(compared > 0);
});

test("every stage the port can produce equals Python's, on the full corpus", (t) => {
  const stages = loadFullStages();
  const manifest = loadFullManifest();
  const corpus = loadFullCorpus();
  assert.equal(corpus.length, manifest.header.case_count);
  const bad: string[] = [];
  let compared = 0;
  let skipped = 0;
  let docs = 0;
  const stillMissing = new Set<string>();
  for (const c of corpus) {
    let result: ReturnType<typeof renderStages>;
    try {
      result = renderStages(c.params, { id_prefix: c.kw.id_prefix ?? "", background: c.kw.background ?? null, metadata: c.kw.metadata ?? false });
    } catch (e) {
      // Python rendered this case; the port raised.
      bad.push(`${c.id}: threw ${String(e).slice(0, 100)}`);
      continue;
    }
    const { stages: got, missing } = result;
    for (const m of missing) stillMissing.add(m);
    const want = stages?.[c.id];
    if (want) {
      for (const [name, wsha, wlen] of want.stages) {
        const g = got.get(name);
        if (g === undefined) {
          bad.push(`${c.id}: no stage ${name}`);
          continue;
        }
        if (g === null) {
          skipped++;
          continue;
        }
        compared++;
        if (g.length !== wlen && [...g].length !== wlen) bad.push(`${c.id}: ${name} length`);
        else if (shaFull(g) !== wsha) bad.push(`${c.id}: ${name}`);
      }
    }
    const doc = got.get("doc");
    if (doc !== null && doc !== undefined) {
      docs++;
      if (!shaFull(doc).startsWith(manifest.cases[c.id]![0])) bad.push(`${c.id}: doc`);
    }
  }
  t.diagnostic(`${corpus.length} cases; compared ${compared} stages${stages ? "" : " (per-stage manifest absent: run manifest_full.py build)"}, skipped ${skipped}; ${docs} whole documents; ${stillMissing.size} parts still to port`);
  assert.deepEqual(bad.slice(0, 20), [], `${bad.length} stages differ`);
});
