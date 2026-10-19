// Franzi's default drawing is pinned byte for byte (docs/franzi-expressions-plan.md, step 0). The face and arm fields the companion
// sends (mouth, blink, brows, gestures) are being added to the adult body; at their neutral values she must draw exactly what v0.5.0
// drew, so every picture made from her before the change (ref-out/, a pack drawn at 0.5.0) stays the same. The hashes were taken from
// v0.5.0 on 2026-10-20. If one of them has to change, her default look has moved: that is the owner's call, not a test to update.

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";
import { characterParams, faceStyle, outfit } from "../src/model.ts";
import { FRANZI } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const sha = (p: Parameters<typeof renderCharacter>[0]): string => createHash("sha256").update(renderCharacter(p, null, null, false)).digest("hex");

const UNDERWEAR = characterParams({ ...FRANZI, outfit: outfit({ ...FRANZI.outfit, tunic_color: null, bodice_color: null, skirt_color: null, apron_color: null }) });

const V050 = {
  dirndl: "0f61e4d3f85303f57a4c26c9be2c36525210c32063331162e50c7b7d98f76890",
  underwear: "0847893c61f10dfac625040263a198daa8d13b99a7709a64843d78eaa2c0d855",
  dirndlSoft: "2a9e9478ece7484090469f2976cdb6b50007f94cfdde1483f7afede3e59ff461",
};

test("her default drawing is what v0.5.0 drew, in the dirndl, in her underwear and in the soft finish", () => {
  assert.equal(sha(FRANZI), V050.dirndl);
  assert.equal(sha(UNDERWEAR), V050.underwear);
  assert.equal(sha(characterParams({ ...FRANZI, finish: "soft" })), V050.dirndlSoft);
});

test("her face carries the defaults of the fields the companion changes, so 'neutral' is the drawing above", () => {
  const f = FRANZI.face;
  assert.equal(f.mouth_curve, 1);
  assert.equal(f.mouth_width, 1);
  assert.equal(f.mouth_open, 0);
  assert.equal(f.eyes_closed, false);
});

// ---- the blink and the mouth (step 1 of the plan): the fields the companion sends now change her drawing

const withFace = (face: Record<string, unknown>, finish: "flat" | "soft" = "flat") => characterParams({ ...FRANZI, finish, face: faceStyle({ ...FRANZI.face, ...face }) });
const draw = (p: ReturnType<typeof withFace>): string => renderCharacter(p, null, null, false);
const ids = (svg: string): string[] => [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);

test("a blink (eyes_closed) replaces the open eyes with a lid line, and is not the default drawing", () => {
  const open = draw(FRANZI);
  const shut = draw(withFace({ eyes_closed: true }));
  assert.notEqual(shut, open);
  assert.ok(open.includes('id="adult-eye-l"') && open.includes('id="adult-eye-r"'), "the open eyes have their clip paths");
  assert.ok(!shut.includes("adult-eye-l") && !shut.includes("adult-eye-r"), "a shut eye draws no aperture, iris or highlights");
  assert.ok(shut.length < open.length, "a shut eye is a line and a flick, smaller than the open eye");
  assert.equal(draw(withFace({ eyes_closed: false })), open, "eyes_closed false is the default drawing");
});

test("the four mouth openings the companion draws for talking are four different pictures, each wider than the last", () => {
  const rest = draw(FRANZI);
  const frames = [0, 0.3, 0.55, 0.85].map((mouth_open) => draw(withFace({ mouth_open })));
  assert.equal(frames[0], rest, "mouth_open 0 is the default drawing");
  assert.equal(new Set(frames).size, 4);
  // the inside is one flat dark red; its path grows with the opening (it is the only path in that colour)
  const inside = (svg: string): number => {
    const m = svg.match(/<path d="M ([^"]+)Z" fill="#6b2f2f" \/>/);
    assert.ok(m, "an open mouth draws its inside");
    const nums = [...(m![1] as string).matchAll(/-?\d+(?:\.\d+)?/g)].map((x) => Number(x[0]));
    const ys = nums.filter((_, i) => i % 2 === 1);
    return Math.max(...ys) - Math.min(...ys);
  };
  assert.ok(!frames[0]!.includes("#6b2f2f"), "a shut mouth has no inside");
  const heights = frames.slice(1).map(inside);
  assert.ok(heights[0]! < heights[1]! && heights[1]! < heights[2]!, `the opening grows: ${heights.join(", ")}`);
});

test("mouth_curve bends the mouth line and mouth_width scales it, both leaving the rest of her unchanged", () => {
  const rest = draw(FRANZI);
  const smile = draw(withFace({ mouth_curve: 1.6 }));
  const frown = draw(withFace({ mouth_curve: -1.4 }));
  const narrow = draw(withFace({ mouth_width: 0.6 }));
  assert.equal(new Set([rest, smile, frown, narrow]).size, 4);
  // only the mouth moves: the SVG has the same number of elements, so nothing else was added or dropped
  const count = (svg: string): number => (svg.match(/</g) ?? []).length;
  for (const v of [smile, frown, narrow]) assert.equal(count(v), count(rest));
});

test("the blink and the open mouth keep her ids unique and every reference resolved, in both finishes", () => {
  for (const finish of ["flat", "soft"] as const) {
    for (const face of [{ eyes_closed: true }, { mouth_open: 0.85 }, { eyes_closed: true, mouth_open: 0.3, mouth_curve: 1.6, mouth_width: 0.8 }]) {
      const svg = draw(withFace(face, finish));
      const defined = ids(svg);
      assert.equal(new Set(defined).size, defined.length, `${JSON.stringify(face)} ${finish}: an id is defined twice`);
      const used = [...svg.matchAll(/url\(#([^)]+)\)/g), ...svg.matchAll(/href="#([^"]+)"/g)].map((m) => m[1] as string);
      for (const u of used) assert.ok(defined.includes(u), `${JSON.stringify(face)} ${finish}: ${u} is used and never defined`);
    }
  }
});

test("the chibi's blink and open mouth are untouched by the adult face", () => {
  const chibi = characterParams({ face: faceStyle({ eyes_closed: true, mouth_open: 0.5 }) });
  assert.ok(renderCharacter(chibi, null, null, false).includes("#6b2f2f"));
});
