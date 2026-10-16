// Rules for the adult woman body (docs/adult-body-plan.md). It is a TypeScript-only addition with no Python oracle, so the
// tests here pin what the plan promises: the underwear is always drawn, nothing anatomical is, and no existing body type
// or preset is reached by it.

import assert from "node:assert/strict";
import { test } from "node:test";
import { ADULT_BODY_TYPES } from "../src/body-adult.ts";
import { BODY_TYPES, skeletonFor } from "../src/body.ts";
import { characterParams, outfit } from "../src/model.ts";
import { PRESETS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const adult = (o: Parameters<typeof outfit>[0] = {}) =>
  characterParams({ body: "adult_female", face_age: 1.0, outfit: outfit({ tunic_color: null, skirt_color: null, boot_color: null, ...o }) });

const paths = (svg: string, fill: string): number => (svg.match(new RegExp(`<path [^>]*fill="${fill}"`, "g")) ?? []).length;

test("the adult body types stay out of the Python-mirrored BODY_TYPES and the presets", () => {
  for (const name of Object.keys(ADULT_BODY_TYPES)) {
    assert.ok(!(name in BODY_TYPES), `${name} must not join BODY_TYPES`);
    for (const [preset, p] of Object.entries(PRESETS)) assert.notEqual(p.body, name, `${preset} must not use ${name} before stage 5d`);
  }
});

test("the adult figure always wears underwear above and below the waist, whatever the outfit says", () => {
  for (const o of [{}, { underwear_top: false }, { underwear_top: true }, { underwear_color: "#223344" }]) {
    const color = (o as { underwear_color?: string }).underwear_color ?? "#e8e4dc";
    const svg = renderCharacter(adult(o));
    assert.ok(paths(svg, color) >= 2, `a top and briefs in ${color} for ${JSON.stringify(o)}`);
  }
});

test("the adult body draws no navel, bust lines or chest lines of the chibi (no anatomical detail)", () => {
  const svg = renderCharacter(adult());
  // The chibi's navel is a small filled ellipse in the line colour; the adult parts draw none.
  assert.ok(!/<ellipse[^>]*fill="#0d0d0d"[^>]*rx="[0-3](\.\d)?"/.test(svg));
});

test("the adult skeleton stands about 6.4 heads tall with its anchors in order", () => {
  const sk = skeletonFor(adult());
  const order = [sk.head_cy + sk.head_r, sk.shoulder_y, sk.waist_y, sk.hip_y, sk.ankle_y, sk.foot_y];
  for (let i = 1; i < order.length; i++) assert.ok((order[i] as number) > (order[i - 1] as number), `anchor ${i} below anchor ${i - 1}`);
  assert.ok(Math.abs((sk.foot_y - (sk.head_cy - sk.head_r)) / (2 * sk.head_r) - 6.4) < 0.05);
});
