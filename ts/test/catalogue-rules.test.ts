// The portable tests of `tests/test_catalogue.py` (22 functions), in TypeScript.
//
// Guards for `catalogue.ts`, so the web tool's list of what is public cannot silently drift from what
// `CharacterParams`, `Outfit` and `HAIRSTYLES` actually are. Most of this is enforced at import time, by the asserts
// next to the tables (a field name that stops existing fails every test in this file just by loading it). What is
// here on top of that is the checklist `docs/web-gui-plan.md` sets out: every range actually renders, every
// starting point is real, and the committed JSON is current (`catalogue.test.ts` holds that last one).
//
// Differences from the Python, all forced by the language:
// * `dataclasses.fields()` is the field registry `FIELDS` (`model.ts`).
// * `ET.fromstring(svg)` is `wellFormed(svg)`, a regex-based check (Node has no XML parser): balanced tags, quoted
//   attributes with no duplicates, no stray `<` or bare `&`, one root element.
// * `HAND_STYLES`, `GRIP_STYLES` come from `catalogue-tables.ts` (the TypeScript modules do not export them).

import assert from "node:assert/strict";
import { test } from "node:test";
import { BODY_TYPES } from "../src/body.ts";
import {
  AGE,
  COLORS,
  FACE_BOOLS,
  FACE_RANGES,
  FACE_SCAR,
  FACE_SELECTS,
  FINISH_LABELS,
  GARMENTS,
  HAIRSTYLE_LABELS,
  HAIR_KNOT,
  HAIR_LENGTH,
  HAIR_TAIL,
  HIGHLIGHT_STRENGTH,
  buildCatalogue,
  type JsonObject,
} from "../src/catalogue.ts";
import { FINISHES } from "../src/character.ts";
import { HAIRSTYLES } from "../src/core-head.ts";
import { ADULT_FACE_AGE, FIELDS, characterParams, faceStyle, outfit, replace } from "../src/model.ts";
import type { CharacterParams, FaceStyle, Outfit } from "../src/params.ts";
import { NEUTRAL_BASES, PRESETS } from "../src/presets.ts";
import { PyInt } from "../src/pyjson.ts";
import { renderCharacter } from "../src/render.ts";
import { BUILDS, buildSkeletonWith } from "../src/skeleton.ts";
import { decodeParams, encodeParams } from "../src/urlstate.ts";

const names = (cls: keyof typeof FIELDS): ReadonlySet<string> => new Set(FIELDS[cls].map((f) => f.name));

/**
 * `ET.fromstring(svg)` without an XML parser: throws when the text is not a well-formed XML document, as far as a
 * scan can tell (tags balance and nest, attributes are quoted and unique, text has no `<` or bare `&`, comments
 * are closed, there is exactly one root). Returns the root element's name.
 */
function wellFormed(svg: string): string {
  const tag = /<(\/?)([A-Za-z_][\w:.-]*)((?:\s+[A-Za-z_][\w:.-]*\s*=\s*(?:"[^"<]*"|'[^'<]*'))*)\s*(\/?)>/y;
  const stack: string[] = [];
  let root: string | null = null;
  let roots = 0;
  let i = 0;
  const text = (s: string): void => {
    assert.ok(!s.includes("<"), `a stray < in text: ${s.slice(0, 40)}`);
    assert.ok(!/&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)/.test(s), `a bare & in text: ${s.slice(0, 40)}`);
    if (stack.length === 0) assert.ok(s.trim() === "", `text outside the root element: ${s.slice(0, 40)}`);
  };
  while (i < svg.length) {
    const lt = svg.indexOf("<", i);
    if (lt === -1) {
      text(svg.slice(i));
      break;
    }
    text(svg.slice(i, lt));
    if (svg.startsWith("<!--", lt)) {
      const end = svg.indexOf("-->", lt + 4);
      assert.ok(end !== -1, "an unclosed comment");
      assert.ok(!svg.slice(lt + 4, end).includes("--"), "a double hyphen inside a comment");
      i = end + 3;
    } else if (svg.startsWith("<?", lt)) {
      const end = svg.indexOf("?>", lt);
      assert.ok(end !== -1, "an unclosed processing instruction");
      i = end + 2;
    } else if (svg.startsWith("<![CDATA[", lt)) {
      const end = svg.indexOf("]]>", lt);
      assert.ok(end !== -1, "an unclosed CDATA section");
      i = end + 3;
    } else if (svg.startsWith("<!", lt)) {
      const end = svg.indexOf(">", lt);
      assert.ok(end !== -1, "an unclosed declaration");
      i = end + 1;
    } else {
      tag.lastIndex = lt;
      const m = tag.exec(svg);
      assert.ok(m !== null, `a malformed tag at ${lt}: ${svg.slice(lt, lt + 60)}`);
      const [whole, close, name, attrs, selfClose] = m as unknown as [string, string, string, string, string];
      if (close === "/") {
        assert.equal(stack.pop(), name, `a closing tag </${name}> that does not match`);
        assert.equal(attrs.trim(), "", "attributes on a closing tag");
      } else {
        const seen = new Set<string>();
        for (const a of attrs.matchAll(/([A-Za-z_][\w:.-]*)\s*=/g)) {
          assert.ok(!seen.has(a[1] as string), `a duplicate attribute ${a[1]} on <${name}>`);
          seen.add(a[1] as string);
        }
        if (stack.length === 0) {
          roots += 1;
          root ??= name;
        }
        if (selfClose !== "/") stack.push(name);
      }
      i = lt + whole.length;
    }
  }
  assert.deepEqual(stack, [], "unclosed tags");
  assert.equal(roots, 1, "not exactly one root element");
  return root as string;
}

/** `ET.fromstring(svg)` then `root.tag.endswith("svg")`. */
const isSvgDocument = (svg: string): boolean => wellFormed(svg).endsWith("svg");

test("the well-formedness check itself accepts a drawing and refuses broken text", () => {
  assert.ok(isSvgDocument(renderCharacter(null)));
  assert.throws(() => wellFormed("<svg><g></svg>"));
  assert.throws(() => wellFormed("<svg><g/></svg><svg/>"));
  assert.throws(() => wellFormed('<svg a="1" a="2"/>'));
  assert.throws(() => wellFormed("<svg>a & b</svg>"));
  assert.throws(() => wellFormed('<svg a=1/>'));
  assert.throws(() => wellFormed("<svg><!-- a -- b --></svg>"));
  assert.equal(wellFormed('<?xml version="1.0"?><svg a="x &amp; y"><g/></svg>'), "svg");
});

const cat = (): JsonObject => buildCatalogue();
const obj = (v: unknown): JsonObject => v as JsonObject;
const arr = (v: unknown): JsonObject[] => v as JsonObject[];

test("every_color_field_exists_on_character_params", () => {
  const known = names("CharacterParams");
  for (const c of COLORS) assert.ok(known.has(c.field), c.field);
});

test("every_garment_field_exists_on_outfit", () => {
  const known = names("Outfit");
  for (const g of GARMENTS) {
    assert.ok(known.has(g.color.field), g.color.field);
    for (const r of g.ranges) assert.ok(known.has(r.field), r.field);
    for (const b of g.bools) assert.ok(known.has(b.field), b.field);
    for (const s of g.selects) assert.ok(known.has(s.field), s.field);
  }
});

test("every_face_field_exists_on_facestyle", () => {
  const known = names("FaceStyle");
  for (const r of FACE_RANGES) assert.ok(known.has(r.field), r.field);
  for (const b of FACE_BOOLS) assert.ok(known.has(b.field), b.field);
  for (const s of FACE_SELECTS) assert.ok(known.has(s.field), s.field);
});

test("every_face_select_option_is_a_real_scar_side", () => {
  // A select's values have to be values the generator actually reads: the scar side can only offer what `_scar` accepts.
  const scar = FACE_SELECTS.find((s) => s.field === "scar_side")!;
  assert.deepEqual(new Set(scar.options.map(([v]) => v)), new Set([0, -1, 1]));
});

test("hair_tail_and_knot_fields_exist_on_character_params", () => {
  const known = names("CharacterParams");
  assert.ok(known.has(HAIR_TAIL.field));
  assert.ok(known.has(HAIR_KNOT.field));
});

test("the_build_slider_and_the_compressed_chibi_are_retired", () => {
  // The tall chibi is the one figure: the catalogue offers no build and no `None` body, only the tall chibi's two.
  const c = cat();
  assert.ok(!("build" in c));
  assert.ok(arr(c.bodies).every((b) => b.id !== null));
});

test("every_hairstyle_label_is_a_real_hairstyle", () => {
  assert.deepEqual(new Set(Object.keys(HAIRSTYLE_LABELS)), new Set(Object.keys(HAIRSTYLES)));
});

test("every_cast_starting_point_is_in_presets", () => {
  for (const entry of arr(obj(cat().starting_points).cast)) assert.ok(Object.hasOwn(PRESETS, entry.id as string), entry.id as string);
});

test("every_base_starting_point_is_a_neutral_base", () => {
  const bases = arr(obj(cat().starting_points).bases);
  for (const entry of bases) assert.ok(Object.hasOwn(NEUTRAL_BASES, entry.id as string), entry.id as string);
  // And the reverse: nothing in NEUTRAL_BASES is missing from the catalogue, which is the direction a forgotten
  // export would fail silently in.
  assert.deepEqual(new Set(bases.map((e) => e.id)), new Set(Object.keys(NEUTRAL_BASES)));
});

const BUILD_NAMES = Object.keys(BUILDS).sort();

for (const build of BUILD_NAMES) {
  test(`hair_length_extremes_render[${build}]`, () => {
    for (const value of [HAIR_LENGTH.lo, HAIR_LENGTH.hi]) {
      const p = replace(characterParams(), { hair_length: value });
      assert.ok(isSvgDocument(renderCharacter(p)), `hair_length ${value}`);
    }
  });

  test(`hair_tail_extremes_render[${build}]`, () => {
    for (const value of [HAIR_TAIL.lo, HAIR_TAIL.hi]) {
      const p = replace(characterParams(), { hair_tail: value });
      assert.ok(isSvgDocument(renderCharacter(p)), `hair_tail ${value}`);
    }
  });

  test(`hair_knot_renders[${build}]`, () => {
    const p = replace(characterParams(), { hair_knot: true });
    assert.ok(isSvgDocument(renderCharacter(p)));
  });
}

/** `base` with one more optional color set, so a companion range on that slot actually draws something rather than being silently skipped. */
function turnedOn(base: Outfit, field: string): Outfit {
  if ((base as unknown as Record<string, unknown>)[field] !== null) return base;
  return replace(base, { [field]: "#5a5a5a" } as Partial<Outfit>);
}

for (const build of BUILD_NAMES) {
  test(`every_garment_range_extreme_renders[${build}]`, () => {
    let renders = 0;
    for (const g of GARMENTS) {
      if (g.ranges.length === 0) continue;
      const on = turnedOn(outfit(), g.color.field);
      for (const r of g.ranges) {
        for (const value of [r.lo, r.hi]) {
          const outfitAt = replace(on, { [r.field]: value } as Partial<Outfit>);
          const p = characterParams({ outfit: outfitAt });
          const svg = renderCharacter(p, buildSkeletonWith({ frame: p.frame, heads: BUILDS[build] }));
          assert.ok(isSvgDocument(svg), `${g.id} ${r.field} ${value}`);
          renders += 1;
        }
      }
    }
    assert.ok(renders >= 2 * GARMENTS.filter((g) => g.ranges.length > 0).length);
  });

  test(`face_range_extremes_render[${build}]`, () => {
    const sk = buildSkeletonWith({ heads: BUILDS[build] });
    for (const r of FACE_RANGES) {
      for (const value of [r.lo, r.hi]) {
        const p = characterParams({ face: replace(faceStyle(), { [r.field]: value } as Partial<FaceStyle>) });
        assert.ok(isSvgDocument(renderCharacter(p, sk)), `${r.field} ${value}`);
      }
    }
  });

  test(`face_scar_options_render[${build}]`, () => {
    const sk = buildSkeletonWith({ heads: BUILDS[build] });
    for (const [value] of FACE_SCAR.options) {
      const p = characterParams({ face: replace(faceStyle(), { scar_side: value as number }) });
      assert.ok(isSvgDocument(renderCharacter(p, sk)), `scar_side ${value}`);
    }
  });
}

test("every catalogue extreme also renders with the catalogue's own int-valued range (shoulder_bars)", () => {
  // `RangeField("shoulder_bars", "Bars", 1, 4)`: the ends are ints and the garment needs a coat on to show them.
  const slot = GARMENTS.find((g) => g.id === "shoulder_bars")!;
  const r = slot.ranges.find((x) => x.field === "shoulder_bars")!;
  assert.equal(r.int, true);
  const on = replace(outfit(), { coat_color: "#5a5a5a", shoulder_bars_color: "#d9b23c" });
  for (const value of [r.lo, r.hi]) {
    const svg = renderCharacter(characterParams({ outfit: replace(on, { shoulder_bars: value }) }));
    assert.ok(isSvgDocument(svg), `shoulder_bars ${value}`);
  }
});

test("the_bust_slider_covers_every_preset_s_value", () => {
  // `bust` is offered as a plain range beside the belt line, and the cast's own values sit inside it.
  const bust = obj(cat().bust);
  assert.ok(bust.field === "bust" && bust.min === 0.0 && bust.max === 1.0);
  for (const p of Object.values(PRESETS)) assert.ok((bust.min as number) <= p.bust && p.bust <= (bust.max as number));
});

test("the_chest_slider_covers_every_preset_s_value", () => {
  // `chest` is offered as a plain range beside the bust, and the cast's own values sit inside it.
  const chest = obj(cat().chest);
  assert.ok(chest.field === "chest" && chest.min === 0.0 && chest.max === 1.0);
  for (const p of Object.values(PRESETS)) assert.ok((chest.min as number) <= p.chest && p.chest <= (chest.max as number));
});

test("the_skin_swatches_include_the_default_and_render", () => {
  // The skin tones offered as swatches: the default among them, every one a colour a figure renders in.
  const swatches = arr(cat().skin_swatches);
  const values = swatches.map((s) => s.value as string);
  assert.ok(values.includes(characterParams().skin_tone));
  for (const v of values) assert.ok(renderCharacter(characterParams({ skin_tone: v })).includes(`fill="${v}"`), v);
});

test("the_height_slider_covers_every_preset_and_its_ends_render", () => {
  // `height` is offered from 0.8 to 1.3; the cast stands at 1.0, and both ends render for every preset.
  const height = obj(cat().height);
  assert.ok(height.field === "height" && height.min === 0.8 && height.max === 1.3);
  for (const [name, p] of Object.entries(PRESETS)) {
    assert.ok((height.min as number) <= p.height && p.height <= (height.max as number), name);
    for (const h of [height.min as number, height.max as number]) {
      assert.ok(isSvgDocument(renderCharacter(replace(p, { height: h }))), `${name} at ${h}`);
    }
  }
});

test("the_finish_controls_are_real_fields_with_a_label_for_every_finish", () => {
  assert.deepEqual(new Set(Object.keys(FINISH_LABELS)), new Set(FINISHES));
  assert.ok(names("CharacterParams").has(HIGHLIGHT_STRENGTH.field));
  const c = cat();
  assert.deepEqual(arr(c.finishes).map((f) => f.id), [...FINISHES]);
  assert.equal(obj(c.highlight_strength).min, 0.0);
  assert.equal(obj(c.highlight_strength).max, 2.0);
});

test("a_soft_character_survives_a_link_and_renders", () => {
  const p = replace(PRESETS.risa as CharacterParams, { finish: "soft", highlight_strength: 0.4 });
  const back = decodeParams(encodeParams(p));
  assert.deepEqual([back.finish, back.highlight_strength], ["soft", 0.4]);
  assert.equal(renderCharacter(back), renderCharacter(p));
});

// ---- tests of other files that read the catalogue (test_smoke.py), kept here because they are about its content

test("the_gui_age_slider_starts_at_twenty_one (test_smoke.py): the catalogue's age range opens at ADULT_FACE_AGE", () => {
  assert.equal(AGE.lo, ADULT_FACE_AGE);
  const age = obj(cat().face_age);
  assert.equal(age.min, ADULT_FACE_AGE);
  assert.equal(age.max, 2.0);
});

test("every catalogue body is a body type and the catalogue lists them all, sorted", () => {
  const ids = arr(cat().bodies).map((b) => b.id as string);
  assert.deepEqual(ids, Object.keys(BODY_TYPES).sort());
});

test("the one int-valued range prints as an int in the built catalogue", () => {
  const bars = arr(cat().garments).find((g) => g.id === "shoulder_bars")!;
  const r = arr(bars.ranges)[0]!;
  assert.ok(r.min instanceof PyInt && r.max instanceof PyInt);
});
