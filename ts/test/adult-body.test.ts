// Rules for the adult woman body (docs/adult-body-plan.md). It is a TypeScript-only addition with no Python oracle, so the
// tests here pin what the plan promises: the underwear is always drawn, nothing anatomical is, and no existing body type
// or preset is reached by it.

import assert from "node:assert/strict";
import { test } from "node:test";
import { ADULT_BODY_TYPES } from "../src/body-adult.ts";
import { BODY_TYPES, skeletonFor } from "../src/body.ts";
import { ADULT_FACE_AGE, characterParams, outfit, replace } from "../src/model.ts";
import { buildCatalogue } from "../src/catalogue.ts";
import { ADULT_CUT_ON_CHIBI, hairstyleFor, hairstyleOf } from "../src/core-head.ts";
import { FRANZI, PRESETS } from "../src/presets.ts";
import { adultBodiceCloth } from "../src/body-adult-garments.ts";
import { renderCharacter } from "../src/render.ts";

/** Franzi in her underwear alone: the preset starts in the dirndl, and most of these tests add one garment at a time to a figure that wears none. */
const BARE = characterParams({ ...FRANZI, outfit: outfit({ ...FRANZI.outfit, tunic_color: null, bodice_color: null, skirt_color: null, apron_color: null }) });

const adult = (o: Parameters<typeof outfit>[0] = {}) =>
  characterParams({ body: "adult_female", face_age: 1.0, outfit: outfit({ tunic_color: null, skirt_color: null, boot_color: null, ...o }) });

const paths = (svg: string, fill: string): number => (svg.match(new RegExp(`<path [^>]*fill="${fill}"`, "g")) ?? []).length;

test("the adult body types are in BODY_TYPES, and only characters at or above the age floor use them", () => {
  for (const name of Object.keys(ADULT_BODY_TYPES)) {
    assert.ok(name in BODY_TYPES, `${name} is a body type like the others since stage 7`);
    for (const [preset, p] of Object.entries(PRESETS)) if (p.body === name) assert.ok(p.face_age >= ADULT_FACE_AGE, `${preset} is on ${name} and under the age floor`);
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

test("the adult cut is in HAIRSTYLES and reachable by name", async () => {
  const { HAIRSTYLES, hairstyleFor } = await import("../src/core-head.ts");
  assert.ok("swept_ponytail" in HAIRSTYLES);
  assert.equal(typeof hairstyleFor("swept_ponytail").mass, "function");
});

test("Franzi's hair draws: the cut closes, and its mass and front piece come out as paths", () => {
  const svg = renderCharacter(characterParams({ body: "adult_female", face_age: 1.0, hairstyle: "swept_ponytail", hair_length: 0.5, outfit: outfit({ tunic_color: null, skirt_color: null, boot_color: null }) }));
  assert.ok((svg.match(/<path [^>]*fill="#e8b84b"/g) ?? []).length >= 2);
});

test("Franzi is a preset on the adult body, at or above the age floor", () => {
  assert.equal(PRESETS.franzi, FRANZI);
  assert.equal(FRANZI.body, "adult_female");
  assert.ok(Object.hasOwn(ADULT_BODY_TYPES, FRANZI.body));
  assert.ok(FRANZI.face_age >= ADULT_FACE_AGE);
});

test("Franzi draws, in the white she is given, with her top and her briefs", () => {
  const svg = renderCharacter(BARE, null, null, false);
  assert.ok(paths(svg, "#faf5f4") >= 2, "a top and briefs in her white");
  assert.equal(renderCharacter(BARE, null, null, false), svg, "a render is deterministic");
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
  const base = body === null ? PRESETS.satoko! : BARE;
  return characterParams({ ...base, outfit: outfit({ ...base.outfit, trouser_color: "#efe9dc" }) });
};

test("adult shorts: drawn on trouser_color, in that colour, and nothing without it", () => {
  const without = renderCharacter(BARE, null, null, false);
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
  replace(characterParams({ ...BARE, outfit: outfit({ ...BARE.outfit, ...fields }) }), { finish });

test("the adult blouse: drawn on tunic_color in that colour, not without it, and not on a chibi's tunic path", () => {
  const without = renderCharacter(BARE, null, null, false);
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
  const without = renderCharacter(BARE, null, null, false);
  assert.ok(!without.includes("adult-arm-strip"), "no arm redraw when nothing hangs in front of the legs");
  const skirt = renderCharacter(wearing({ skirt_color: "#2b5a37" }), null, null, false);
  assert.ok(skirt.includes('fill="#2b5a37"'));
  assert.ok(skirt.includes('id="adult-arm-strip"'));
  assert.ok(skirt.indexOf('id="adult-arm-strip"') > skirt.indexOf('fill="#2b5a37"'), "the arms are drawn after the skirt");
  const both = renderCharacter(wearing({ skirt_color: "#2b5a37", apron_color: "#7d1f27" }), null, null, false);
  assert.ok(both.indexOf('fill="#7d1f27"') > both.indexOf('fill="#2b5a37"'), "the apron is over the skirt");
  assert.ok(both.includes('id="adult-apron-sash"'));
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

test("worn with a skirt the blouse is tucked in: drawn before the skirt, so it does not lie over it; the apron and its bow come after both", () => {
  const svg = renderCharacter(wearing({ tunic_color: "#faf8f4", skirt_color: "#2b5a37", apron_color: "#7d1f27" }), null, null, false);
  const blouse = svg.indexOf('fill="#faf8f4"');
  const skirt = svg.indexOf('fill="#2b5a37"');
  const apron = svg.indexOf('fill="#7d1f27"');
  assert.ok(blouse >= 0 && skirt > blouse && apron > skirt, `blouse ${blouse}, skirt ${skirt}, apron ${apron}`);
  // the bow: its shapes are drawn in the apron's colour with outlines, after the apron itself
  assert.ok((svg.match(/fill="#7d1f27" stroke="#0d0d0d"/g) ?? []).length >= 6, "two tails, two loops, the knot and the apron");
  // without a skirt the blouse stays in the chest layers, over the shorts
  const loose = renderCharacter(wearing({ tunic_color: "#faf8f4", trouser_color: "#efe9dc" }), null, null, false);
  assert.ok(loose.indexOf('fill="#faf8f4"') > loose.indexOf('fill="#efe9dc"'));
});

test("the dirndl bodice: sixteen buttons, a lacing of crossing ribbons, cut at the hem it is given", () => {
  const sk = skeletonFor(BARE);
  const whole = adultBodiceCloth(sk, "#245c33");
  assert.equal((whole.match(/<circle [^>]*fill="#dfae45"/g) ?? []).length, 16);
  assert.ok(!whole.includes("adult-bodice-cut"), "whole: not cut");
  assert.ok((whole.match(/stroke-linecap="round"/g) ?? []).length >= 2 * 15, "two layers (outline and band) for each of the 15 ribbons, plus the top one");
  const cut = adultBodiceCloth(sk, "#245c33", 1.34);
  assert.ok(cut.includes('id="adult-bodice-cut"'));
  assert.equal(adultBodiceCloth(sk, "#245c33", 1.34), cut, "deterministic");
});

test("bodice_color: drawn over the blouse and under the apron's sash, cut there, and nothing on a chibi", () => {
  const dirndl = wearing({ tunic_color: "#faf8f4", bodice_color: "#245c33", skirt_color: "#2b5a37", apron_color: "#7d1f27" });
  const svg = renderCharacter(dirndl);
  const ids = [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
  assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), [], "an id is defined twice");
  assert.ok(svg.indexOf('id="adult-bodice-clip"') > svg.indexOf('fill="#faf8f4"'), "the bodice is over the blouse");
  assert.ok(svg.indexOf('id="adult-apron-sash"') > svg.indexOf('id="adult-bodice-clip"'), "and under the apron's sash");
  assert.ok(svg.includes('id="adult-bodice-cut"'), "cut where the sash covers it");
  // worn alone it is whole, down to the hips
  assert.ok(!renderCharacter(wearing({ tunic_color: "#faf8f4", bodice_color: "#245c33" })).includes("adult-bodice-cut"));
  // a chibi with a bodice colour draws nothing of it
  const chibi = characterParams({ ...PRESETS.satoko!, outfit: outfit({ ...PRESETS.satoko!.outfit, bodice_color: "#245c33" }) });
  assert.equal(renderCharacter(chibi), renderCharacter(PRESETS.satoko!));
  // without the field the document has no bodice
  assert.ok(!renderCharacter(wearing({ tunic_color: "#faf8f4" })).includes("adult-bodice"));
});

test("a blouse is tucked into the shorts when the outfit says so, and lies over them otherwise", () => {
  const tuckedSvg = renderCharacter(wearing({ tunic_color: "#faf8f4", trouser_color: "#efe9dc", tunic_tucked: true }), null, null, false);
  const looseSvg = renderCharacter(wearing({ tunic_color: "#faf8f4", trouser_color: "#efe9dc" }), null, null, false);
  assert.ok(tuckedSvg.indexOf('fill="#faf8f4"') < tuckedSvg.indexOf('fill="#efe9dc"'), "tucked: the shorts are over the blouse");
  assert.ok(looseSvg.indexOf('fill="#faf8f4"') > looseSvg.indexOf('fill="#efe9dc"'), "loose: the blouse is over the shorts");
});

for (const cut of ["blazer", "lab_coat", "open_jacket"]) {
  test(`a coat on the adult woman defines every id once and draws her hands after it [${cut}]`, () => {
    const svg = renderCharacter(wearing({ coat_color: "#3a6ea5", coat_cut: cut }));
    const ids = [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
    assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), [], "an id is defined twice");
    const refs = [...svg.matchAll(/url\(#([^)]+)\)/g)].map((m) => m[1] as string);
    assert.deepEqual(refs.filter((r) => !ids.includes(r)), []);
    assert.ok(svg.indexOf('id="adult-hand-body"') > svg.indexOf('fill="#3a6ea5"'), "the hands are drawn over the coat");
  });
}

test("her cut on a chibi body falls back to a chibi cut, so the head has hair, and is hers again on the adult body", () => {
  for (const body of ["tall_chibi", "tall_chibi_long_torso", "tall_slender"]) {
    const hers = characterParams({ ...FRANZI, body });
    const fallback = characterParams({ ...FRANZI, body, hairstyle: "long_center_part" });
    assert.equal(renderCharacter(hers), renderCharacter(fallback), `${body}: the cut is the nearest chibi one`);
    assert.ok((renderCharacter(hers).match(/fill="#1b1c22"/g) ?? []).length >= 2, `${body}: the hair is drawn in her colour`);
  }
  assert.equal(hairstyleOf(FRANZI), hairstyleFor("swept_ponytail"));
  assert.equal(hairstyleOf(characterParams({ ...FRANZI, body: "tall_chibi" })), hairstyleFor(ADULT_CUT_ON_CHIBI));
  assert.equal(FRANZI.hairstyle, "swept_ponytail", "the character still says swept_ponytail");
});

// ---- the controls a body does not use (catalogue.body_ignores, hidden by the page)

test("BODY_IGNORES is what drawing the adult woman shows, plus the three controls hidden because they draw something wrong", async () => {
  const { BODY_HIDDEN_EXTRA, BODY_IGNORES } = await import("../src/catalogue-tables.ts");
  const { ignoredFields } = await import("./ignored-fields.ts");
  const derived = ignoredFields("adult_female");
  const table = [...(BODY_IGNORES["adult_female"] ?? [])];
  assert.deepEqual(table, [...new Set([...derived, ...(BODY_HIDDEN_EXTRA["adult_female"] ?? [])])].sort(), "the table drifted from the drawing: node harness/franzi/ignored_fields.ts prints what it should be");
  for (const f of ["hair_tail", "hair_knot", "waist_shift"]) assert.ok(table.includes(f), f);
  // the controls she does use are not hidden
  for (const f of ["skin_tone", "hair_color", "eye_color", "height", "tunic_color", "skirt_color", "apron_color", "bodice_color", "trouser_color", "hat_color", "glasses", "familiar_color"]) assert.ok(!table.includes(f), `${f} is used`);
});

test("the catalogue carries body_ignores, only for bodies that are in it, only of fields that exist", async () => {
  const cat = buildCatalogue() as unknown as { bodies: { id: string }[]; body_ignores: Record<string, string[]> };
  const { controls } = await import("./ignored-fields.ts");
  const known = new Set(controls().map((c) => c.field));
  for (const [body, fields] of Object.entries(cat.body_ignores)) {
    assert.ok(cat.bodies.some((b) => b.id === body), body);
    for (const f of fields) assert.ok(known.has(f), `${body} ignores ${f}, which no control has`);
  }
});

// ---- knee socks and boots

test("adult knee socks and boots: drawn on their colours, the foot's toes and nails left out under a boot, ids unique", () => {
  const bare = renderCharacter(BARE, null, null, false);
  const socks = renderCharacter(wearing({ knee_sock_color: "#f1ece4" }), null, null, false);
  const boots = renderCharacter(wearing({ boot_color: "#5b4632" }), null, null, false);
  const both = renderCharacter(wearing({ knee_sock_color: "#f1ece4", boot_color: "#5b4632" }), null, null, false);
  assert.ok(socks.includes('fill="#f1ece4"') && !bare.includes("#f1ece4"));
  assert.ok(boots.includes('fill="#5b4632"') && !bare.includes("#5b4632"));
  assert.ok(both.indexOf('fill="#5b4632"') > both.indexOf('fill="#f1ece4"'), "the boot is over the sock");
  assert.ok(bare.includes('id="adult-foot-rows"'), "a bare foot has its outline redrawn below the ankle");
  assert.ok(!boots.includes('id="adult-foot-rows"') && !boots.includes('id="adult-foot-body"'), "a boot covers the foot: no toes, nails or foot outline under it");
  assert.ok(socks.includes('id="adult-foot-rows"'), "socks stop at the ankle and leave the foot bare");
  for (const svg of [socks, boots, both, renderCharacter(wearing({ boot_color: "#5b4632", boot_cut: "loafer" })), renderCharacter(wearing({ boot_color: "#5b4632", boot_shaft: 1 }))]) {
    const ids = [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
    assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), []);
  }
  // a taller shaft draws a different, longer boot; a loafer a shorter one; the same call twice is the same drawing
  const full = renderCharacter(wearing({ boot_color: "#5b4632", boot_shaft: 1 }), null, null, false);
  const loafer = renderCharacter(wearing({ boot_color: "#5b4632", boot_cut: "loafer" }), null, null, false);
  assert.ok(new Set([boots, full, loafer]).size === 3);
  assert.equal(renderCharacter(wearing({ boot_color: "#5b4632" }), null, null, false), boots);
});

const uniqueIds = (svg: string) => {
  const ids = [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
  return ids.filter((v, i) => ids.indexOf(v) !== i);
};

test("the adult belt, pouches and crystals: drawn on their colours at the waist, the pouches and crystals only with a belt, and the belt's chibi cuts and keepers do nothing", () => {
  const draw = (f: Record<string, unknown>) => renderCharacter(wearing(f), null, null, false);
  const bare = draw({});
  const belt = draw({ belt_color: "#6b4a2a" });
  const full = draw({ belt_color: "#6b4a2a", pouch_color: "#8a5a2a", crystal_color_1: "#4aa0e0", crystal_color_4: "#e0c84a", crystal_tongs: true });
  assert.ok(belt.includes('fill="#6b4a2a"') && !bare.includes("#6b4a2a"));
  assert.ok(full.includes('fill="#8a5a2a"') && full.includes('fill="#4aa0e0"') && full.includes('fill="#e0c84a"'));
  // without a belt there is nothing to hang them from
  assert.equal(draw({ pouch_color: "#8a5a2a", crystal_color_1: "#4aa0e0" }), bare);
  // the chibi's cut, keeper pair and reach are not read; the height is
  assert.equal(draw({ belt_color: "#6b4a2a", belt_cut: "buckled", belt_keeper_pair: true, belt_reach: 1.4 }), belt);
  assert.notEqual(draw({ belt_color: "#6b4a2a", belt_scale: 3 }), belt);
  assert.deepEqual(uniqueIds(full), []);
});

test("the adult coat: two panels on coat_color from the shoulders, the hem set by coat_length, the belt drawn over it, the traced cuts not read", () => {
  const draw = (f: Record<string, unknown>) => renderCharacter(wearing(f), null, null, false);
  const bare = draw({});
  const vest = draw({ coat_color: "#8a2a2a", coat_length: 0.3 });
  const long = draw({ coat_color: "#8a2a2a", coat_length: 0.85 });
  assert.equal(paths(vest, "#8a2a2a"), 2);
  assert.ok(!bare.includes("#8a2a2a"));
  assert.notEqual(vest, long);
  assert.equal(draw({ coat_color: "#8a2a2a", coat_length: 0.3, coat_cut: "lab_coat" }), vest, "a traced cut is the chibi's shape and is not drawn");
  const belted = draw({ coat_color: "#8a2a2a", belt_color: "#6b4a2a" });
  assert.ok(belted.indexOf('fill="#6b4a2a"') > belted.indexOf('fill="#8a2a2a"'), "the belt is over the coat");
  assert.deepEqual(uniqueIds(belted), []);
});

test("the adult robe and hakama: a V-necked front with hanging sleeves on sleeve_drop, wide trousers to hakama_length drawn under the belt, the arms redrawn below the sleeves", () => {
  const draw = (f: Record<string, unknown>) => renderCharacter(wearing(f), null, null, false);
  const bare = draw({});
  const robe = draw({ robe_color: "#3a3a8a" });
  const sleeved = draw({ robe_color: "#3a3a8a", sleeve_drop: 0.5 });
  assert.equal(paths(robe, "#3a3a8a"), 1);
  assert.equal(paths(sleeved, "#3a3a8a"), 3, "the front and a sleeve on each side");
  assert.ok(!bare.includes("#3a3a8a"));
  const hakama = draw({ hakama_color: "#2a2a5a", hakama_length: 0.9 });
  assert.ok(hakama.includes('fill="#2a2a5a"') && !bare.includes("#2a2a5a"));
  assert.notEqual(draw({ hakama_color: "#2a2a5a", hakama_length: 0.5 }), hakama);
  const belted = draw({ hakama_color: "#2a2a5a", belt_color: "#c8b040" });
  assert.ok(belted.indexOf('fill="#c8b040"') > belted.indexOf('fill="#2a2a5a"'), "the belt is over the hakama");
  // a hakama is worn with the blouse tucked in, so the blouse is drawn before it
  const tucked = draw({ hakama_color: "#2a2a5a", tunic_color: "#faf6f5" });
  assert.ok(tucked.indexOf('fill="#faf6f5"') < tucked.indexOf('fill="#2a2a5a"'));
  for (const svg of [robe, sleeved, hakama, belted, tucked, draw({ robe_color: "#3a3a8a", sleeve_drop: 1, hakama_color: "#2a2a5a", skirt_color: "#285032" })]) assert.deepEqual(uniqueIds(svg), []);
});

test("the adult collar: a band on collar_color at the neck, standing or mock, and a chibi's traced cut is not read", () => {
  const draw = (f: Record<string, unknown>) => renderCharacter(wearing(f), null, null, false);
  const bare = draw({});
  const standing = draw({ collar_color: "#2a2a5a" });
  assert.ok(standing.includes('fill="#2a2a5a"') && !bare.includes("#2a2a5a"));
  assert.notEqual(draw({ collar_color: "#2a2a5a", collar_mock: true }), standing);
  assert.equal(draw({ collar_color: "#2a2a5a", collar_cut: "pointed" }), standing);
});

test("the soft finish on her: hair clumps and a shaded iris, nothing in the flat finish, none at highlight strength 0, ids unique, costing little over the flat one", () => {
  const withFinish = (finish: "flat" | "soft", extra: Record<string, unknown> = {}) => renderCharacter(replace(characterParams({ ...FRANZI, ...extra }), { finish }), null, null, false);
  const flat = withFinish("flat");
  const softer = withFinish("soft");
  assert.ok(!flat.includes("-grad") && !flat.includes("-glow"));
  assert.ok(softer.includes('id="adult-eye-l-grad"') && softer.includes('id="adult-eye-r-glow"'));
  // the strands are one group clipped to the hair; the clumps are a second
  const clumps = (svg: string) => (svg.match(/<g clip-path="url\(#adult-hair-clip\)">/g) ?? []).length - 1;
  assert.equal(clumps(flat), 0);
  assert.equal(clumps(softer), 1);
  const none = withFinish("soft", { highlight_strength: 0 });
  assert.equal(clumps(none), 0);
  assert.ok(none.includes('id="adult-eye-l-grad"'), "the eyes are shaded whatever the highlight strength is");
  assert.notEqual(withFinish("soft", { highlight_strength: 2 }), softer);
  assert.deepEqual(uniqueIds(softer), []);
  // her flat document is already 230 KB (the body outline), over the chibis' 150 KB soft budget: what the soft finish adds to it is what is held down
  assert.ok(softer.length - flat.length < 20_000, `${softer.length - flat.length} bytes added`);
});

// ---- the bust (an offset from the traced bust on the adult woman)

test("the adult bust: 0 is the traced one, below 0 a smaller one that moves only the bust's own shapes", async () => {
  const { adultBustScale, bustWarp } = await import("../src/body-adult-parts.ts");
  assert.equal(adultBustScale(0), 1);
  assert.ok(adultBustScale(-0.2) < 1 && adultBustScale(0.2) > 1);
  // the warp: the identity at 1, the neck and straps untouched, the cleavage's V on the centre line, a smaller bust narrower and shorter
  assert.deepEqual(bustWarp([0.3, 0.8], 1), [0.3, 0.8]);
  assert.deepEqual(bustWarp([0.2, 0.1], 0.8), [0.2, 0.1]);
  assert.equal((bustWarp([0, 0.8], 0.8) as readonly number[])[0], 0);
  const [x, d] = bustWarp([0.4, 0.9], 0.8) as readonly [number, number];
  assert.ok(x < 0.4 && d < 0.9 && d > 0.45, "narrower and with its lower edge raised, below the top of the breasts");
  // drawn: the default is a bust of 0, a smaller one is a different drawing with no new ids, and Franzi at 0 is unchanged by it
  const base = renderCharacter(BARE, null, null, false);
  assert.equal(renderCharacter(characterParams({ ...BARE, bust: 0 }), null, null, false), base);
  const smaller = renderCharacter(characterParams({ ...BARE, bust: -0.2 }), null, null, false);
  assert.notEqual(smaller, base);
  const ids = [...smaller.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
  assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), []);
});

// ---- the school shirt (collar_cut "shirt", docs/risa-adult-plan.md)

test("the adult school shirt replaces the puff blouse, tucks under a skirt and keeps its sleeves in front of it, with unique ids", () => {
  const shirt = (o: Parameters<typeof outfit>[0] = {}) => characterParams({ ...BARE, outfit: outfit({ ...BARE.outfit, tunic_color: "#f4ecec", collar_cut: "shirt", sleeve_long: true, tunic_tucked: true, ...o }) });
  const blouse = renderCharacter(characterParams({ ...BARE, outfit: outfit({ ...BARE.outfit, tunic_color: "#f4ecec" }) }), null, null, false);
  const bare = renderCharacter(shirt(), null, null, false);
  assert.ok(bare.includes('id="adult-shirt-clip"') && !blouse.includes('id="adult-shirt-clip"'), "the shirt is its own garment, the blouse is not drawn with it");
  assert.notEqual(bare, blouse);
  // over a skirt the sleeves are drawn again in the cloth, not as skin
  const skirted = renderCharacter(shirt({ skirt_color: "#697897", skirt_cut: "pleated" }), null, null, false);
  assert.ok(skirted.includes('id="adult-shirt-sleeves-over"'));
  const plain = renderCharacter(shirt({ skirt_color: "#697897" }), null, null, false);
  assert.ok(plain.includes('id="adult-shirt-sleeves-over"') && !plain.includes('id="adult-arm-strip"'));
  for (const svg of [bare, skirted, plain]) {
    const ids = [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
    assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), []);
  }
  // Franzi's own collar and blouse are unchanged by it
  assert.ok(!renderCharacter(BARE, null, null, false).includes("adult-shirt"));
});

test("the adult ribbon is a bow in ribbon_color under the shirt's collar, mirrored, and the chibi's traced bow is not drawn on this body", () => {
  const withRibbon = (o: Parameters<typeof outfit>[0] = {}) => characterParams({ ...BARE, outfit: outfit({ ...BARE.outfit, tunic_color: "#f4ecec", collar_cut: "shirt", sleeve_long: true, tunic_tucked: true, ...o }) });
  const plain = renderCharacter(withRibbon(), null, null, false);
  const bow = renderCharacter(withRibbon({ ribbon_color: "#5784ae" }), null, null, false);
  assert.ok(bow.includes('fill="#5784ae"') && !plain.includes('fill="#5784ae"'));
  // five pieces a side's worth: two bands, two tails, two loops, the knot (seven filled paths), over the shirt and before the collar
  assert.equal((bow.match(/fill="#5784ae"/g) ?? []).length, 7);
  assert.ok(bow.indexOf('fill="#5784ae"') < bow.lastIndexOf("adult-shirt-neck-opening"), "the bow is drawn before the collar's neck is put back over it");
  const ids = [...bow.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
  assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), []);
  // without a shirt the same bow is drawn on its own, in the same colour
  const blouse = renderCharacter(characterParams({ ...BARE, outfit: outfit({ ...BARE.outfit, tunic_color: "#f4ecec", ribbon_color: "#5784ae" }) }), null, null, false);
  assert.equal((blouse.match(/fill="#5784ae"/g) ?? []).length, 7);
});

// ---- the school blazer (coat_cut "blazer", docs/risa-adult-plan.md)

test("the adult blazer replaces the open coat, is two mirrored panels with three gold buttons, and keeps its sleeves in front of the skirt, with unique ids", () => {
  const worn = (o: Parameters<typeof outfit>[0] = {}) =>
    characterParams({ ...BARE, outfit: outfit({ ...BARE.outfit, tunic_color: "#f4ecec", collar_cut: "shirt", sleeve_long: true, tunic_tucked: true, skirt_color: "#697897", skirt_cut: "pleated", coat_color: "#212940", coat_button_color: "#ba975e", ...o }) });
  const coat = renderCharacter(worn({ coat_cut: null }), null, null, false);
  const blazer = renderCharacter(worn({ coat_cut: "blazer" }), null, null, false);
  assert.notEqual(blazer, coat);
  assert.equal((blazer.match(/fill="#ba975e"/g) ?? []).length, 3, "three gold buttons");
  assert.equal((blazer.match(/fill="#212940"/g) ?? []).length >= 2, true, "two panels in the blazer's colour");
  assert.ok(blazer.includes('id="adult-blazer-sleeves-over"'), "the sleeves are drawn again over the skirt");
  const ids = [...blazer.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
  assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), []);
  // without a shirt the blazer is still drawn on its own, and Franzi's own outfit is untouched
  const alone = renderCharacter(characterParams({ ...BARE, outfit: outfit({ ...BARE.outfit, coat_color: "#212940", coat_cut: "blazer" }) }), null, null, false);
  assert.equal((alone.match(/fill="#212940"/g) ?? []).length >= 2, true);
  assert.ok(!renderCharacter(BARE, null, null, false).includes("adult-blazer"));
});

test("the school sock and loafer (boot_cut loafer with knee socks): open-ended sock, rim and strap on the shoe, unique ids, and the other boots unchanged", () => {
  const worn = (o: Parameters<typeof outfit>[0] = {}) => characterParams({ ...BARE, outfit: outfit({ ...BARE.outfit, knee_sock_color: "#2a282b", boot_color: "#4d332c", ...o }) });
  const school = renderCharacter(worn({ boot_cut: "loafer" }), null, null, false);
  const plain = renderCharacter(worn({}), null, null, false);
  assert.ok(school.includes('id="adult-loafer-clip-l"') && school.includes('id="adult-loafer-clip-r"'));
  assert.ok(!plain.includes("adult-loafer-clip"), "an ankle boot is not the loafer");
  const ids = [...school.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
  assert.deepEqual(ids.filter((v, i) => ids.indexOf(v) !== i), []);
});

test("Risa's face is straight and symmetric: the eyes level about one midline, the brows mirrored, the jaw the same either side, and the nose and mouth on the midline", async () => {
  const { ADULT_HEAD_CUTS } = await import("../src/body-adult-cuts.ts");
  const cut = ADULT_HEAD_CUTS["long_straight_fringed"] as (typeof ADULT_HEAD_CUTS)[string];
  const [l, r] = [cut.irisAt[-1] as readonly number[], cut.irisAt[1] as readonly number[]];
  assert.equal(l[1], r[1], "the eyes are level");
  const mid = ((l[0] as number) + (r[0] as number)) / 2;
  // the jaw: at each row below the eyes the two edges are the same distance from the midline
  const px = (q: readonly number[]): [number, number] => [660 + (q[0] as number) * 175.7, 270.5 + (q[1] as number) * 175.7];
  const [start, segs] = (cut.face[0] as NonNullable<typeof cut.face[0]>);
  const pts = [start, ...segs.map(([, e]) => e)].map(px);
  for (const y of [345, 370, 395, 420]) {
    const xs: number[] = [];
    for (let i = 0; i + 1 < pts.length; i++) {
      const [p, q] = [pts[i] as [number, number], pts[i + 1] as [number, number]];
      if (p[1] !== q[1] && (p[1] - y) * (q[1] - y) <= 0) xs.push(p[0] + ((q[0] - p[0]) * (y - p[1])) / (q[1] - p[1]));
    }
    assert.ok(Math.abs((Math.min(...xs) + Math.max(...xs)) / 2 - mid) < 0.5, `row ${y}: edges ${xs.map((x) => x.toFixed(1)).join(", ")} about ${mid}`);
  }
  assert.equal(Math.max(...pts.map((p) => p[1])), pts.find((p) => p[0] === mid)?.[1], "the chin is on the midline");
  const [bl, br] = cut.brows!.lines.map((c) => [c[0], ...c[1].map((s) => s[1])].map(px));
  assert.ok(Math.abs((bl![0]![0] + br![br!.length - 1]![0]) / 2 - mid) < 0.01 && Math.abs(bl![0]![1] - br![br!.length - 1]![1]) < 0.01, "the right brow is the left one mirrored");
  assert.ok(Math.abs(cut.featuresAt.mouth[0] + 666.5 - mid) < 1e-9 && Math.abs(cut.featuresAt.nose[0] + 660 - mid) < 1e-9, "the nose and the mouth are centred on the midline");
  // the mouth line: mirrored about the middle of its ends, so both corners sit at the same height (the traced right corner is 3.5 px higher, which on a straight face reads as a smirk)
  const { SYMMETRIC_MOUTH_POINTS: m } = await import("../src/body-adult-parts.ts");
  assert.ok(m.length % 2 === 0 && m.length >= 10);
  for (let i = 0; i < m.length / 2; i++) {
    const [a, z] = [m[i] as readonly number[], m[m.length - 1 - i] as readonly number[]];
    assert.ok(Math.abs((a[0] as number) + (z[0] as number) - ((m[0] as readonly number[])[0] as number) - ((m[m.length - 1] as readonly number[])[0] as number)) < 1e-9 && a[1] === z[1], `point ${i} mirrors point ${m.length - 1 - i}`);
  }
  assert.equal(cut.symmetricMouth, true);
  assert.equal((ADULT_HEAD_CUTS["swept_ponytail"] as typeof cut).symmetricMouth, true, "Franzi's is straightened too");
});

test("Franzi's face is straight too: the eyes level, the mouth symmetric, her jaw the same either side of the midline of her eyes", async () => {
  const { ADULT_HEAD_CUTS } = await import("../src/body-adult-cuts.ts");
  const cut = ADULT_HEAD_CUTS["swept_ponytail"] as (typeof ADULT_HEAD_CUTS)[string];
  assert.equal((cut.irisAt[-1] as readonly number[])[1], (cut.irisAt[1] as readonly number[])[1], "the eyes are level");
  assert.equal(cut.symmetricMouth, true);
  const mid = (((cut.irisAt[-1] as readonly number[])[0] as number) + ((cut.irisAt[1] as readonly number[])[0] as number)) / 2;
  const px = (q: readonly number[]): [number, number] => [660 + (q[0] as number) * 175.7, 270.5 + (q[1] as number) * 175.7];
  const [start, segs] = cut.face[0] as NonNullable<(typeof cut.face)[0]>;
  const pts = [start, ...segs.map(([, e]) => e)].map(px);
  for (const y of [370, 395, 420]) {
    const xs: number[] = [];
    for (let i = 0; i + 1 < pts.length; i++) {
      const [p, q] = [pts[i] as [number, number], pts[i + 1] as [number, number]];
      if (p[1] !== q[1] && (p[1] - y) * (q[1] - y) <= 0) xs.push(p[0] + ((q[0] - p[0]) * (y - p[1])) / (q[1] - p[1]));
    }
    assert.ok(Math.abs((Math.min(...xs) + Math.max(...xs)) / 2 - mid) < 0.5, `row ${y}`);
  }
});

test("hair_tip_color on the adult woman repaints the lower hair of each cut in the tip colour, and unset changes nothing", () => {
  for (const name of ["risa", "franzi"]) {
    const base = PRESETS[name] as ReturnType<typeof characterParams>;
    const plain = renderCharacter(base);
    const tipped = renderCharacter(replace(base, { hair_tip_color: "#ff88cc" }));
    assert.equal(paths(plain, "#ff88cc"), 0, `${name}: no tip colour without hair_tip_color`);
    assert.ok(paths(tipped, "#ff88cc") >= 1, `${name}: the tip colour is painted`);
    assert.match(tipped, /clip-path="url\(#hair-tips\)"/);
    assert.equal(renderCharacter(replace(base, { hair_tip_color: null })), plain, `${name}: unset is the drawing it was`);
  }
});
