// The body domain's parts (`src/parts-body.ts`): their ten stage slots on the full corpus, which must all be produced (never
// skipped) and equal Python's by sha256, and the three places where Python raises inside them.

import assert from "node:assert/strict";
import { test } from "node:test";
import { characterParams, outfit } from "../src/model.ts";
import { plainParams } from "../src/plain.ts";
import { PyError } from "../src/pynum.ts";
import { PARTS } from "../src/parts-body.ts";
import { renderStages } from "../src/render.ts";
import { loadFullCorpus, loadFullStages, sha256 } from "./corpus.ts";
import { skeletonFor } from "../src/body.ts";

const MINE = ["layers[4]", "layers[6]", "layers[7]", "layers[8]", "layers[9]", "layers[10]", "chest[1]", "chest[2]", "chest[3]", "chest[4]"];

test("the body's twelve roots are registered under their Python names", () => {
  assert.deepEqual(Object.keys(PARTS).sort(), [
    "_bust_lines", "_bust_over_arms", "_chest_lines", "_hakama", "_hanging_sleeves", "_legs_and_boots", "_navel", "_skirt", "_torso", "_underskirt", "_underwear_top", "_without_raised_sleeves",
  ]);
});

test("the body's stage slots equal Python's on the full corpus (every case, none skipped)", (t) => {
  const stages = loadFullStages();
  if (!stages) return t.skip("per-stage manifest absent: run manifest_full.py build");
  const mine = new Set(MINE);
  const bad: string[] = [];
  let compared = 0;
  for (const c of loadFullCorpus()) {
    const want = stages[c.id];
    if (!want) continue;
    const { stages: got } = renderStages(c.params, { id_prefix: c.kw.id_prefix ?? "", background: c.kw.background ?? null, metadata: c.kw.metadata ?? false });
    for (const [name, wsha] of want.stages) {
      if (!mine.has(name)) continue;
      const g = got.get(name);
      if (g === null || g === undefined) {
        bad.push(`${c.id}: ${name} not produced`);
        continue;
      }
      compared++;
      if (sha256(g) !== wsha) bad.push(`${c.id}: ${name}`);
    }
  }
  t.diagnostic(`compared ${compared} slot texts`);
  assert.deepEqual(bad.slice(0, 20), [], `${bad.length} slots differ`);
  assert.ok(compared >= 7662 * MINE.length);
});

test("a cut name that is not a cut, and a number where the arithmetic wants one, raise as Python does", () => {
  const raises = (o: object, name: string, cls: string): void => {
    // The drawing reads the parameters as `plainParams` makes them: a string in a number field becomes a value that raises when used.
    const p = plainParams(characterParams({ outfit: outfit(o) }));
    const sk = skeletonFor(p);
    assert.throws(() => (PARTS[name] as (...a: unknown[]) => string)(sk, p), (e: unknown) => e instanceof PyError && e.pyType === cls);
  };
  raises({ boot_cut: "nope" }, "_legs_and_boots", "KeyError");
  raises({ skirt_color: "#336699", skirt_cut: "nope" }, "_skirt", "KeyError");
  raises({ robe_color: "#336699", sleeve_drop: "x" }, "_hanging_sleeves", "TypeError");
});
