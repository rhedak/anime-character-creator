// Risa's hair under the soft finish (docs/risa-polish-plan.md, stage 6): her cut's clumps on the hair behind, those that reach the fringe again over it, and a lit clump down each front lock;
// none of it in the flat finish, and Franzi's clumps at the strength they were judged at.

import assert from "node:assert/strict";
import { test } from "node:test";
import { adultCutOf } from "../src/body-adult-cuts.ts";
import { replace } from "../src/model.ts";
import { FRANZI, RISA } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const draw = (p: typeof RISA): string => renderCharacter(p, null, null, false);
const group = (svg: string, clip: string): string => {
  const i = svg.indexOf(`<g clip-path="url(#${clip})">`);
  return i < 0 ? "" : svg.slice(i, svg.indexOf("</g>", i));
};
const shapes = (g: string): number => (g.match(/<path /g) ?? []).length;

const groups = (svg: string, clip: string): number => svg.split(`<g clip-path="url(#${clip})">`).length - 1;

test("the flat finish draws none of Risa's clumps: the hair and the fringe have only their strands' group, the soft finish a clumps' group as well", () => {
  const flat = draw(replace(RISA, { finish: "flat" }));
  const soft = draw(replace(RISA, { finish: "soft" }));
  assert.ok(!flat.includes("adult-front-lock-0"));
  for (const clip of ["adult-hair-clip", "adult-fringe-clip"]) {
    assert.equal(groups(flat, clip), 1, `flat ${clip}`);
    assert.equal(groups(soft, clip), 2, `soft ${clip}`);
  }
});

test("the soft finish draws her clumps behind, the ones that reach the fringe over it, and a lit clump down each front lock, with unique ids", () => {
  const svg = draw(replace(RISA, { finish: "soft" }));
  const cut = adultCutOf(RISA);
  const lit = cut.locks.filter(([role]) => role === "lit").length;
  const shadow = cut.locks.length - lit;
  // each clump is two shapes: a lit body and its highlight, or a shadow and its separation
  assert.equal(shapes(group(svg, "adult-hair-clip")), 2 * (lit + shadow));
  const onFringe = cut.locks.filter(([, pts]) => pts.some(([, y]) => y < 0.25)).length;
  assert.ok(onFringe > 0 && onFringe < cut.locks.length);
  assert.equal(shapes(group(svg, "adult-fringe-clip")), 2 * onFringe);
  for (const i of [0, 1]) assert.equal(shapes(group(svg, `adult-front-lock-${i}`)), 2, `front lock ${i}`);
  const ids = [...svg.matchAll(/ id="([^"]+)"/g)].map((m) => m[1] as string);
  assert.deepEqual(ids.filter((id, k) => ids.indexOf(id) !== k), []);
});

test("Franzi's clumps keep the strength they were judged at; Risa's are stronger", () => {
  assert.equal(adultCutOf(FRANZI).lockGain, 1);
  assert.ok(adultCutOf(RISA).lockGain > 1);
});
