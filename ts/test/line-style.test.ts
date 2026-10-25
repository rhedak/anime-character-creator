// Rules for a character's line style (`line_style`, `LINE_STYLES` in character.ts, docs/risa-polish-plan.md stage 5): none is the house lines, a style scales every stroke and composes with the
// soft finish's own scale, the fine style draws the hair's outline in its strand tone, and an unknown name is a KeyError.

import assert from "node:assert/strict";
import { test } from "node:test";
import { LINE_STYLES, OUTLINE } from "../src/character.ts";
import { adultHairInk } from "../src/body-adult-parts.ts";
import { replace } from "../src/model.ts";
import { PyError, pyFloat } from "../src/pynum.ts";
import { FRANZI, PRESETS, RISA } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const draw = (p: typeof RISA): string => renderCharacter(p, null, null, false);
const widths = (svg: string): number[] => [...svg.matchAll(/stroke-width="([0-9.]+)"/g)].map((m) => pyFloat(m[1] as string));

test("only Risa has a line style; every other preset draws the house lines", () => {
  for (const [name, p] of Object.entries(PRESETS)) assert.equal(p.line_style, name === "risa" ? "fine" : null, name);
});

test("a line style scales every stroke, and composes with the soft finish's scale", () => {
  const house = widths(draw(replace(RISA, { line_style: null })));
  const fine = widths(draw(RISA));
  assert.equal(fine.length, house.length);
  const k = (LINE_STYLES["fine"] as { scale: number }).scale;
  fine.forEach((w, i) => assert.ok(Math.abs(w - (house[i] as number) * k) <= 0.006, `${i}: ${w} against ${house[i]}`));
  const soft = widths(draw(replace(RISA, { line_style: null, finish: "soft" })));
  const softFine = widths(draw(replace(RISA, { finish: "soft" })));
  softFine.forEach((w, i) => assert.ok(Math.abs(w - (soft[i] as number) * k) <= 0.006, `soft ${i}: ${w} against ${soft[i]}`));
});

test("the fine style draws the hair's outline in its strand tone, the house lines in black", () => {
  assert.notEqual(adultHairInk(RISA), OUTLINE);
  assert.ok(draw(RISA).includes(`stroke="${adultHairInk(RISA)}"`));
  assert.equal(adultHairInk(replace(RISA, { line_style: null })), OUTLINE);
  assert.equal(adultHairInk(FRANZI), OUTLINE);
});

test("an unknown line style is a KeyError", () => {
  assert.throws(() => draw(replace(RISA, { line_style: "no_such_style" })), (e: unknown) => e instanceof PyError && e.pyType === "KeyError");
});
