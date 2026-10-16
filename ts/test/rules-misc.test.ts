// Whole-document rules and repository hygiene: determinism, the transparent background, the retired builds' leftovers and
// the README's table. tests/test_smoke.py.

import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import type { CharacterParams } from "../src/params.ts";
import { PRESETS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";
import { REPO_ROOT } from "./fixtures.ts";
import { PRESET_NAMES } from "./rules-util.ts";
import { childrenOf, fromstring } from "./svg-scan.ts";

const REF_OUT = join(REPO_ROOT, "ref-out");

test("test_render_is_deterministic", () => {
  // `ref-out/` is compared byte for byte, so two runs have to agree (no module state, no cache leaking between calls).
  const p = PRESETS.satoko as CharacterParams;
  const first = renderCharacter(p);
  assert.equal(renderCharacter(p), first);
  // A render of something else in between does not change it either.
  renderCharacter(PRESETS.katherina);
  assert.equal(renderCharacter(p), first);
});

for (const name of PRESET_NAMES) {
  test(`test_the_figure_is_drawn_on_transparency[${name}]`, () => {
    // No background rectangle unless one is asked for. A character is composited onto a scene, so an opaque white rectangle
    // behind it is something the caller has to undo. Checked by walking the elements rather than by searching the text,
    // because `fill="white"` legitimately appears in the drawing: it is the sclera of every eye.
    for (const want of [null, "white", "#ff00ff"]) {
      const root = fromstring(renderCharacter(PRESETS[name] as CharacterParams, null, want));
      const full = childrenOf(root).filter((el) => el.tag === "rect" && el.attrs.width === "100%" && el.attrs.height === "100%");
      assert.deepEqual(
        full.map((el) => el.attrs.fill),
        want === null ? [] : [want],
        `${name} with background ${want}`,
      );
    }
  });
}

test("test_the_retired_builds_left_nothing_behind", () => {
  // No realistic renders anywhere under `ref-out/`: not the old top-level `*_real` files, nor `real/`, which went with the
  // realistic build. A leftover is the worst kind of stale: nothing renders to it any more, so no comparison ever looks at it again.
  assert.ok(existsSync(REF_OUT), "ref-out/ is the directory this rule is about");
  const left: string[] = [];
  const walkDir = (dir: string): void => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (e.isDirectory()) walkDir(join(dir, e.name));
      else if (/_real\./.test(e.name)) left.push(e.name);
    }
  };
  walkDir(REF_OUT);
  if (existsSync(join(REF_OUT, "real"))) left.push(...readdirSync(join(REF_OUT, "real")));
  assert.deepEqual(left.sort(), [], "the realistic build is retired; git rm these");
});

const README = readFileSync(join(REPO_ROOT, "README.md"), "utf8");
for (const name of PRESET_NAMES) {
  test(`test_the_readme_shows_every_character[${name}]`, () => {
    // The README's table has to keep up with `PRESETS`, and nothing made it: it is hand-written, so a new character
    // arrives on disk automatically and in the table only if somebody remembers. Checked as a link to `on-white/`, since
    // that is what the table is allowed to use: the transparent renders lose their outline against a dark theme.
    assert.ok(README.includes(`ref-out/on-white/${name}.png`), `${name} renders but the README never shows it: add a row`);
    assert.ok(!README.includes(`ref-out/on-white/${name}_real.png`), `${name}: the README points at an on-white realistic copy, which is not written any more`);
  });
}
