// Rules for the adult woman body (docs/adult-body-plan.md). It is a TypeScript-only addition with no Python oracle, so the
// tests here pin what the plan promises: the underwear is always drawn, nothing anatomical is, and no existing body type
// or preset is reached by it.

import assert from "node:assert/strict";
import { test } from "node:test";
import { ADULT_BODY_TYPES } from "../src/body-adult.ts";
import { BODY_TYPES, skeletonFor } from "../src/body.ts";
import { ADULT_FACE_AGE, characterParams, outfit, replace } from "../src/model.ts";
import { ADULT_PRESETS, FRANZI, PRESETS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const adult = (o: Parameters<typeof outfit>[0] = {}) =>
  characterParams({ body: "adult_female", face_age: 1.0, outfit: outfit({ tunic_color: null, skirt_color: null, boot_color: null, ...o }) });

const paths = (svg: string, fill: string): number => (svg.match(new RegExp(`<path [^>]*fill="${fill}"`, "g")) ?? []).length;

test("the adult body types stay out of the Python-mirrored BODY_TYPES and the presets", () => {
  for (const name of Object.keys(ADULT_BODY_TYPES)) {
    assert.ok(!(name in BODY_TYPES), `${name} must not join BODY_TYPES`);
    for (const [preset, p] of Object.entries(PRESETS)) assert.notEqual(p.body, name, `${preset} must not use ${name}: the characters on adult bodies are in ADULT_PRESETS until the owner decides at stage 7`);
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

test("the adult cuts are reachable by name but stay out of HAIRSTYLES, the Python-mirrored table", async () => {
  const { HAIRSTYLES, hairstyleFor } = await import("../src/core-head.ts");
  await import("../src/body-adult-hair.ts");
  assert.ok(!("swept_ponytail" in HAIRSTYLES));
  assert.equal(typeof hairstyleFor("swept_ponytail").mass, "function");
});

test("Franzi's hair draws: the cut closes, and its mass and front piece come out as paths", () => {
  const svg = renderCharacter(characterParams({ body: "adult_female", face_age: 1.0, hairstyle: "swept_ponytail", hair_length: 0.5, outfit: outfit({ tunic_color: null, skirt_color: null, boot_color: null }) }));
  assert.ok((svg.match(/<path [^>]*fill="#e8b84b"/g) ?? []).length >= 2);
});

test("Franzi is an adult preset on the adult body, apart from PRESETS, and at or above the age floor", () => {
  assert.equal(ADULT_PRESETS.franzi, FRANZI);
  assert.ok(!("franzi" in PRESETS), "she joins the catalogue, the command line and ref-out only at stage 7, the owner's call");
  assert.equal(FRANZI.body, "adult_female");
  assert.ok(Object.hasOwn(ADULT_BODY_TYPES, FRANZI.body));
  for (const [name, p] of Object.entries(ADULT_PRESETS)) {
    assert.ok(p.face_age >= ADULT_FACE_AGE, `${name} is under the age floor`);
    assert.ok(Object.hasOwn(ADULT_BODY_TYPES, p.body), `${name} is in ADULT_PRESETS, so it needs an adult body`);
  }
});

test("Franzi draws, in the white she is given, with her top and her briefs", () => {
  const svg = renderCharacter(FRANZI, null, null, false);
  assert.ok(paths(svg, "#faf5f4") >= 2, "a top and briefs in her white");
  assert.equal(renderCharacter(FRANZI, null, null, false), svg, "a render is deterministic");
});

for (const finish of ["flat", "soft"] as const) {
  test(`Franzi's ids are defined once and every reference resolves [${finish}]`, () => {
    const svg = renderCharacter(replace(FRANZI, { finish }));
    const ids = [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
    assert.ok(ids.length > 0, "the control needs ids");
    assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), [], "an id is defined twice");
    const refs = [...svg.matchAll(/url\(#([^)]+)\)/g)].map((m) => m[1] as string);
    assert.deepEqual(refs.filter((r) => !ids.includes(r)), []);
  });
}

test("Franzi's drawing defines the 46 KB body outline once and stays small", () => {
  const svg = renderCharacter(FRANZI, null, null, false);
  assert.equal((svg.match(/id="adult-body-outline"/g) ?? []).length, 1, "defined once, referred to with <use>");
  assert.ok((svg.match(/<use /g) ?? []).length >= 20, "the clips and strokes refer to it");
  // 2.3 MB when each clip and stroke carried its own copy of the outline; 184 KB with one. The limit leaves room for the detail still to come.
  assert.ok(svg.length < 400_000, `${svg.length} bytes`);
});

// ---- garments fitted to the adult body (body-adult-garments.ts)

const shortsOn = (body: string | null) => {
  const base = body === null ? PRESETS.satoko! : FRANZI;
  return characterParams({ ...base, outfit: outfit({ ...base.outfit, trouser_color: "#efe9dc" }) });
};

test("adult shorts: drawn on trouser_color, in that colour, and nothing without it", () => {
  const without = renderCharacter(FRANZI, null, null, false);
  const withShorts = renderCharacter(shortsOn("adult_female"), null, null, false);
  assert.notEqual(without, withShorts);
  assert.ok(withShorts.includes('fill="#efe9dc"'));
  assert.ok(!without.includes("#efe9dc"));
  assert.equal(renderCharacter(shortsOn("adult_female"), null, null, false), withShorts, "deterministic");
});

test("adult shorts cover the briefs' top and show no more of the body than the briefs do", () => {
  // The briefs' waistband is at 1.713 H and the shorts' top at 1.68 H: the shorts begin above it, so the briefs' top edge is hidden by them.
  const svg = renderCharacter(shortsOn("adult_female"), null, null, false);
  const shorts = svg.indexOf('fill="#efe9dc"');
  const briefs = svg.indexOf('fill="#faf5f4"');
  assert.ok(briefs >= 0 && shorts > briefs, "the shorts are drawn after the briefs, over them");
});

test("trouser_color on a chibi body is untouched by the adult garments", () => {
  // The adult garment parts are laid over the adult body's parts only; a chibi with trousers draws as before.
  const chibi = shortsOn(null);
  assert.equal(chibi.body === "adult_female", false);
  const svg = renderCharacter(chibi, null, null, false);
  assert.ok(svg.includes("#efe9dc"));
  assert.ok(!svg.includes("adult-body-outline"));
});

const wearing = (fields: Record<string, unknown>, finish: "flat" | "soft" = "flat") =>
  replace(characterParams({ ...FRANZI, outfit: outfit({ ...FRANZI.outfit, ...fields }) }), { finish });

test("the adult blouse: drawn on tunic_color in that colour, not without it, and not on a chibi's tunic path", () => {
  const without = renderCharacter(FRANZI, null, null, false);
  const svg = renderCharacter(wearing({ tunic_color: "#faf8f4" }), null, null, false);
  assert.ok(svg.includes('fill="#faf8f4"'));
  assert.ok(!without.includes("#faf8f4"));
  assert.ok(svg.includes('id="adult-blouse-clip"'));
  assert.equal(renderCharacter(wearing({ tunic_color: "#faf8f4" }), null, null, false), svg, "deterministic");
  // a chibi's tunic does not go through the adult blouse
  assert.ok(!renderCharacter(PRESETS.satoko!, null, null, false).includes("adult-blouse-clip"));
});

for (const finish of ["flat", "soft"] as const) {
  test(`blouse and shorts together: ids defined once, references resolve, small [${finish}]`, () => {
    const svg = renderCharacter(wearing({ tunic_color: "#faf8f4", trouser_color: "#efe9dc" }, finish));
    const ids = [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
    assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), [], "an id is defined twice");
    const refs = [...svg.matchAll(/url\(#([^)]+)\)/g)].map((m) => m[1] as string);
    assert.deepEqual(refs.filter((r) => !ids.includes(r)), []);
    assert.ok(svg.length < 400_000, `${svg.length} bytes`);
  });
}

test("the blouse is drawn over the body and under the hands' layer, and over the shorts' top", () => {
  const svg = renderCharacter(wearing({ tunic_color: "#faf8f4", trouser_color: "#efe9dc" }), null, null, false);
  const shorts = svg.indexOf('fill="#efe9dc"');
  const blouse = svg.indexOf('fill="#faf8f4"');
  const hands = svg.indexOf('id="adult-hand-zone"');
  assert.ok(shorts >= 0 && blouse > shorts, "the blouse comes after the shorts, so its hem lies over their waist");
  assert.ok(hands > blouse, "the hands' layer comes after the blouse");
});

test("the adult skirt and apron: drawn on skirt_color and apron_color, the arms redrawn over them, nothing extra without them", () => {
  const without = renderCharacter(FRANZI, null, null, false);
  assert.ok(!without.includes("adult-arm-strip"), "no arm redraw when nothing hangs in front of the legs");
  const skirt = renderCharacter(wearing({ skirt_color: "#2b5a37" }), null, null, false);
  assert.ok(skirt.includes('fill="#2b5a37"'));
  assert.ok(skirt.includes('id="adult-arm-strip"'));
  assert.ok(skirt.indexOf('id="adult-arm-strip"') > skirt.indexOf('fill="#2b5a37"'), "the arms are drawn after the skirt");
  const both = renderCharacter(wearing({ skirt_color: "#2b5a37", apron_color: "#7d1f27" }), null, null, false);
  assert.ok(both.indexOf('fill="#7d1f27"') > both.indexOf('fill="#2b5a37"'), "the apron is over the skirt");
  assert.ok(both.includes('id="adult-apron-clip"'));
  // the chibi underskirt is not drawn on her
  assert.equal(renderCharacter(wearing({ skirt_color: "#2b5a37", underskirt_color: "#ffffff" }), null, null, false), skirt);
});

for (const finish of ["flat", "soft"] as const) {
  test(`blouse, skirt, apron and shorts together: ids defined once, references resolve, small [${finish}]`, () => {
    const svg = renderCharacter(wearing({ tunic_color: "#faf8f4", skirt_color: "#2b5a37", apron_color: "#7d1f27", trouser_color: "#efe9dc" }, finish));
    const ids = [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
    assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), [], "an id is defined twice");
    const refs = [...svg.matchAll(/url\(#([^)]+)\)/g)].map((m) => m[1] as string);
    assert.deepEqual(refs.filter((r) => !ids.includes(r)), []);
    assert.ok(svg.length < 400_000, `${svg.length} bytes`);
  });
}
