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

// ---- step 2: brows, lids, gaze and blush

/** The two traced brows' paths (the only paths filled and stroked with the outline colour at 0.3), each as its points. */
const brows = (svg: string): [number, number][][] =>
  [...svg.matchAll(/<path d="M ([^"]+)Z" fill="#0d0d0d" stroke="#0d0d0d" stroke-width="0\.3"/g)].map((m) => {
    const n = [...(m[1] as string).matchAll(/-?\d+(?:\.\d+)?/g)].map((x) => Number(x[0]));
    return n.reduce<[number, number][]>((acc, v, i) => (i % 2 === 0 ? [...acc, [v, 0]] : (acc[acc.length - 1]![1] = v, acc)), []);
  });
/** The point of a brow nearest the centre line (the inner end), x = 200. */
const innerEnd = (pts: [number, number][]): [number, number] => pts.reduce((a, q) => (Math.abs(q[0] - 200) < Math.abs(a[0] - 200) ? q : a));

test("brow_tilt turns each brow: positive drops the inner ends, negative raises them, 0 is the traced brow", () => {
  const flat = brows(draw(FRANZI));
  assert.equal(flat.length, 2);
  const stern = brows(draw(withFace({ brow_tilt: 1.4 })));
  const sad = brows(draw(withFace({ brow_tilt: -1.2 })));
  for (let i = 0; i < 2; i++) {
    assert.ok(innerEnd(stern[i]!)[1] > innerEnd(flat[i]!)[1] + 0.3, `brow ${i}: a positive tilt drops the inner end`);
    assert.ok(innerEnd(sad[i]!)[1] < innerEnd(flat[i]!)[1] - 0.3, `brow ${i}: a negative tilt raises the inner end`);
  }
  assert.equal(draw(withFace({ brow_tilt: 0 })), draw(FRANZI));
});

test("eye_openness lowers the lid and crops the iris; 1 is the traced eye; the lid comes down further the lower the value", () => {
  const rest = draw(FRANZI);
  const frames = [0.9, 0.7, 0.5].map((eye_openness) => draw(withFace({ eye_openness })));
  assert.equal(draw(withFace({ eye_openness: 1 })), rest);
  assert.equal(new Set([rest, ...frames]).size, 4);
  // the aperture's clip path is the eye's opening: its top edge (the smallest y) comes down with the lid
  const top = (svg: string): number => {
    const m = svg.match(/<clipPath id="adult-eye-l"><path d="([^"]+)"/);
    assert.ok(m, "the left eye has its aperture");
    const ys = [...(m![1] as string).matchAll(/-?\d+(?:\.\d+)?/g)].map((q) => Number(q[0])).filter((_, i) => i % 2 === 1);
    return Math.min(...ys);
  };
  const low = [rest, ...frames].map(top);
  assert.ok(low[0]! < low[1]! && low[1]! < low[2]! && low[2]! < low[3]!, `the opening's top comes down: ${low.join(", ")}`);
});

test("gaze moves the irises together, to the viewer's left or right, and 0 is the traced eye", () => {
  const rest = draw(FRANZI);
  assert.equal(draw(withFace({ gaze: 0 })), rest);
  const left = draw(withFace({ gaze: -1 }));
  const right = draw(withFace({ gaze: 1 }));
  assert.equal(new Set([rest, left, right]).size, 3);
  const dx = (svg: string): number[] => [...svg.matchAll(/<g transform="translate\((-?\d+(?:\.\d+)?) 0\)">/g)].map((m) => Number(m[1]));
  assert.deepEqual(dx(rest), []);
  assert.equal(dx(left).length, 2, "one shift for each eye");
  assert.ok(dx(left).every((v) => v < 0) && dx(right).every((v) => v > 0), "negative looks left, positive right, for both eyes");
  assert.equal(dx(left)[0], dx(left)[1], "the two eyes move the same way by the same amount");
});

test("blush draws only above her default of 1, as two cheeks that grow more opaque", () => {
  const cheeks = (svg: string): number[] => [...svg.matchAll(/<ellipse [^>]*transform="rotate\([^"]*"[^>]*fill="#[0-9a-f]{6}" opacity="(\d\.\d+)"/g)].map((m) => Number(m[1]));
  for (const b of [0, 0.5, 1]) assert.deepEqual(cheeks(draw(withFace({ blush: b }))), [], `blush ${b} draws none`);
  assert.equal(draw(withFace({ blush: 1 })), draw(FRANZI));
  const a = cheeks(draw(withFace({ blush: 1.5 })));
  const c = cheeks(draw(withFace({ blush: 2 })));
  assert.equal(a.length, 2);
  assert.equal(c.length, 2);
  assert.ok(c[0]! > a[0]!, "a stronger blush is more opaque");
  assert.ok(cheeks(draw(withFace({ blush: 9 }))).every((v) => v <= 1), "never past solid");
});

test("the seven companion emotions are seven different faces, each unlike her neutral one except neutral itself", async () => {
  const { readFileSync, existsSync } = await import("node:fs");
  const emotions: Record<string, Record<string, unknown>> = {
    neutral: {},
    happy: { mouth_curve: 1.6, brow_tilt: -0.1, blush: 1.0, eye_openness: 0.7, mouth_open: 0.3 },
    sad: { mouth_curve: -1.4, brow_tilt: -1.2, eye_openness: 0.7, blush: 0.0 },
    angry: { mouth_curve: -1.0, brow_tilt: 1.4, eye_openness: 0.6, eye_tilt: 0.2 },
    surprised: { eye_size: 1.12, iris_size: 0.8, brow_tilt: -0.5, mouth_curve: 0.2, mouth_width: 0.6, mouth_open: 0.65 },
    shy: { blush: 1.5, gaze: 0.8, mouth_curve: 0.6, brow_tilt: -0.6, eye_openness: 0.8 },
    thinking: { gaze: -0.8, mouth_curve: -0.1, brow_tilt: 0.3, eye_openness: 0.9, mouth_width: 0.6 },
  };
  // the companion's own table, when its checkout is next to this one, must be the one copied above (a drift would make this test check the wrong faces)
  const theirs = new URL("../../../anime_ai_companion-dev/emotions.json", import.meta.url);
  if (existsSync(theirs)) assert.deepEqual(JSON.parse(readFileSync(theirs, "utf8")), emotions);
  const svgs = Object.fromEntries(Object.entries(emotions).map(([k, v]) => [k, draw(withFace(v))]));
  assert.equal(svgs["neutral"], draw(FRANZI));
  assert.equal(new Set(Object.values(svgs)).size, 7);
});

test("lids, gaze, brows and blush keep her ids unique and every reference resolved, in both finishes", () => {
  for (const finish of ["flat", "soft"] as const) {
    for (const face of [{ eye_openness: 0.6, gaze: 0.8 }, { blush: 1.5, brow_tilt: 1.4 }, { eyes_closed: true, blush: 2 }]) {
      const svg = draw(withFace(face, finish));
      const defined = ids(svg);
      assert.equal(new Set(defined).size, defined.length, `${JSON.stringify(face)} ${finish}: an id is defined twice`);
      for (const u of [...svg.matchAll(/url\(#([^)]+)\)/g), ...svg.matchAll(/href="#([^"]+)"/g)].map((m) => m[1] as string)) assert.ok(defined.includes(u), `${JSON.stringify(face)} ${finish}: ${u} is used and never defined`);
    }
  }
});
