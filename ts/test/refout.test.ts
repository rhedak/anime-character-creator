// The committed art. `ref-out/<name>.svg` is what the README shows and what `refresh-ref-out.sh --check` guards in Python; the
// TypeScript port has to draw the same bytes: every preset (with the skeleton handed in, as the script does) and the two
// neutral bases the web gallery paints first.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import { skeletonFor } from "../src/body.ts";
import { NEUTRAL_BASES, PRESETS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";
import { REPO_ROOT } from "./fixtures.ts";

const REF_OUT = join(REPO_ROOT, "ref-out");

for (const name of Object.keys(PRESETS).sort()) {
  test(`ref-out/${name}.svg is what the TypeScript draws`, () => {
    const p = PRESETS[name]!;
    assert.equal(renderCharacter(p, skeletonFor(p)), readFileSync(join(REF_OUT, `${name}.svg`), "utf8"));
  });
}

for (const name of Object.keys(NEUTRAL_BASES).sort()) {
  test(`ref-out/bases/${name}.svg is what the TypeScript draws`, () => {
    assert.equal(renderCharacter(NEUTRAL_BASES[name]), readFileSync(join(REF_OUT, "bases", `${name}.svg`), "utf8"));
  });
}

test("the default character draws, and a drawing is deterministic", () => {
  const a = renderCharacter();
  assert.equal(a, renderCharacter(null));
  assert.ok(a.startsWith("<svg "));
});
