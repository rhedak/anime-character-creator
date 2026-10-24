// Rules for the front locks of an adult cut (body-adult-front-locks.ts, docs/risa-polish-plan.md stage 4): only a cut that has them draws them, their outline is masked to the body and what is
// worn on it (white shapes only, which cairosvg and a browser read alike), the document's ids stay unique, and the locks sit on the body as it is built.

import assert from "node:assert/strict";
import { test } from "node:test";
import { replace } from "../src/model.ts";
import { FRANZI, RISA } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const draw = (p: typeof RISA): string => renderCharacter(p, null, null, false);
const ids = (svg: string): string[] => [...svg.matchAll(/ id="([^"]+)"/g)].map((m) => m[1] as string);
const dupes = (svg: string): string[] => ids(svg).filter((id, i, all) => all.indexOf(id) !== i);

test("only a cut with front locks draws them: Franzi's ponytail none, Risa's two, each outline masked", () => {
  assert.ok(!draw(FRANZI).includes("adult-front-locks"));
  const risa = draw(RISA);
  assert.equal((risa.match(/mask="url\(#adult-front-locks-ink\)"/g) ?? []).length, 2);
  assert.ok(!risa.includes("adult-front-locks-mask"));
});

test("a posed arm draws the locks as a hanging one does, its sleeve in the outline's mask, and the document's ids stay unique", () => {
  const waving = draw(replace(RISA, { right_arm_out: 6, right_elbow: 150 }));
  assert.ok(!waving.includes("adult-front-locks-mask"));
  const mask = (waving.match(/<mask id="adult-front-locks-ink">(.*?)<\/mask>/s) ?? [])[1] as string;
  assert.ok(mask.includes("-fill"), "the posed arm is in the outline's mask");
  assert.ok(!/fill="#000000"/.test(mask), "white shapes on nothing: cairosvg reads a mask by its alpha");
  assert.deepEqual(dupes(waving), []);
  assert.deepEqual(dupes(draw(replace(RISA, { right_arm_out: 130, right_elbow: 40, left_arm_out: 35, left_elbow: 100 }))), []);
});

test("the locks sit on the body as it is built: the traced body puts them elsewhere than her slender build", () => {
  const lock = (svg: string): string => (svg.match(/<path d="(M [^"]+)Z" fill="#6b1f2a" stroke="none" \/>/) ?? [])[1] as string;
  const slender = lock(draw(RISA));
  const traced = lock(draw(replace(RISA, { body_build: null })));
  assert.ok(slender !== undefined && traced !== undefined);
  assert.notEqual(slender, traced);
});
