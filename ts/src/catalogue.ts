// What the web tool is allowed to show, and nothing it has to guess.
//
// `docs/web-gui-plan.md` calls for "a limited set of choices: pick a character, change colours, and swap between
// the hairstyles and garments that already exist", deliberately short of a full parameter editor. `CharacterParams`
// alone cannot answer that: it is `dataclasses.fields()` away from FaceStyle's fourteen floats and `shaded`, a
// killed behaviour with a live field still attached to it, neither of which belong on a page for someone who has
// never opened a terminal (see "Knobs that are traps" in that document).
//
// So this module is the curated middle: a small, explicit list of which fields are public, in which order, with
// which labels and ranges, built once here against the real field registry so a rename anywhere it points at
// breaks a test rather than silently drifting. It emits that list as JSON via `toJson()`, which must equal
// `ref-out/catalogue.json` byte for byte (the Python writes that file with `refresh-catalogue.sh`).
//
// **The web layer learns no geometry from this.** Every range is a number the project already looked at, on a
// rendered chibi, not the type's full domain.
//
// The data (label tables, garment slots, ranges) is generated from `catalogue.py` by
// `harness/ts_port/gen_catalogue_tables.py` into `catalogue-tables.ts`; the shapes and the field checks are in
// `catalogue-types.ts`. Both are re-exported here, so a caller imports everything from this module.

import { BODY_TYPES } from "./body.ts";
import { HAIRSTYLES } from "./core-head.ts";
import { FINISHES } from "./character.ts";
import { PyInt, dumps } from "./pyjson.ts";
import type { Json } from "./pyjson.ts";
import { pyStrRepr, sorted } from "./pynum.ts";
import { DISPLAY_NAMES, NEUTRAL_BASES, PRESETS } from "./presets.ts";
import {
  BODY_IGNORES,
  BODY_LABELS,
  COLORS,
  FACE_BOOLS,
  FACE_RANGES,
  FACE_SELECTS,
  FINISH_LABELS,
  GARMENTS,
  GRIP_LABELS,
  GRIP_STYLES,
  HAIRSTYLE_LABELS,
  HAIR_KNOT,
  HAIR_LENGTH,
  HAIR_TAIL,
  HAND_LABELS,
  HAND_STYLES,
  HEIGHT,
  AGE,
  BUST,
  CHEST,
  HIGHLIGHT_STRENGTH,
  SKIN_SWATCHES,
  WAIST_SHIFT,
} from "./catalogue-tables.ts";
import {
  CHARACTER_FIELDS,
  OUTFIT_FIELDS,
  lookup,
  pyAssert,
} from "./catalogue-types.ts";
import type { BoolField, ColorField, GarmentSlot, RangeField, SelectField, StartingPoint } from "./catalogue-types.ts";

export * from "./catalogue-tables.ts";
export * from "./catalogue-types.ts";

/** A JSON object as `build_catalogue` returns it (a `dict[str, object]`). */
export type JsonObject = { readonly [key: string]: Json };

/**
 * Every `Outfit` field name reachable from `GARMENTS`, so a field added to
 * `Outfit` and forgotten here shows up as a set difference rather than a
 * silent gap in the web tool.
 */
export function outfitFieldsNamed(): ReadonlySet<string> {
  const out = new Set<string>();
  for (const g of GARMENTS) {
    out.add(g.color.field);
    for (const r of g.ranges) out.add(r.field);
    for (const b of g.bools) out.add(b.field);
    for (const s of g.selects) out.add(s.field);
  }
  return out;
}

// The module-level asserts of `catalogue.py` that tie its tables to the dataclasses. The ones that tie a label
// table to the table of `character.py` (`set(SLEEVE_CUT_LABELS) == set(SLEEVE_CUTS)` and the rest) sit next to each
// label table in the generated `catalogue-tables.ts`.
{
  const named = outfitFieldsNamed();
  const missing = [...OUTFIT_FIELDS].filter((f) => !named.has(f));
  const extra = [...named].filter((f) => !OUTFIT_FIELDS.has(f));
  pyAssert(
    missing.length === 0 && extra.length === 0,
    `GARMENTS and Outfit have drifted apart: missing ${JSON.stringify(missing)}, extra ${JSON.stringify(extra)}`,
  );
}
for (const c of COLORS) pyAssert(CHARACTER_FIELDS.has(c.field), `CharacterParams has no field ${pyStrRepr(c.field)}`);
pyAssert(CHARACTER_FIELDS.has(HAIR_LENGTH.field));
pyAssert(CHARACTER_FIELDS.has("finish"));
pyAssert(CHARACTER_FIELDS.has(HIGHLIGHT_STRENGTH.field));
pyAssert(CHARACTER_FIELDS.has(WAIST_SHIFT.field));
pyAssert(CHARACTER_FIELDS.has(HEIGHT.field));
pyAssert(CHARACTER_FIELDS.has(AGE.field));
pyAssert(CHARACTER_FIELDS.has(BUST.field));
pyAssert(CHARACTER_FIELDS.has(CHEST.field));
pyAssert(CHARACTER_FIELDS.has(HAIR_TAIL.field));
pyAssert(CHARACTER_FIELDS.has(HAIR_KNOT.field));
pyAssert(CHARACTER_FIELDS.has("body"));
pyAssert(CHARACTER_FIELDS.has("hand_style"));
pyAssert(CHARACTER_FIELDS.has("grip_style"));
// (`FACE_RANGES`, `FACE_BOOLS` and `FACE_SELECTS` are checked as they are built, by `faceRange` and its twins.)

/** The characters on offer as starting points, by id. */
export function castPoints(): readonly StartingPoint[] {
  return sorted(Object.keys(PRESETS)).map((name) => ({ id: name, label: lookup(DISPLAY_NAMES, name) }));
}

/** The neutral bases on offer as starting points, by id. */
export function basePoints(): readonly StartingPoint[] {
  const labels: Readonly<Record<string, string>> = { female: "Female base", male: "Male base" };
  return sorted(Object.keys(NEUTRAL_BASES)).map((name) => ({ id: name, label: lookup(labels, name) }));
}

export function colorJson(c: ColorField): JsonObject {
  return { field: c.field, label: c.label, optional: c.optional };
}

/** A range's `min` and `max`: floats, except where Python's literals are ints (`RangeField.int`). */
export function rangeJson(r: RangeField): JsonObject {
  return r.int === true
    ? { field: r.field, label: r.label, min: new PyInt(r.lo), max: new PyInt(r.hi) }
    : { field: r.field, label: r.label, min: r.lo, max: r.hi };
}

export function boolJson(b: BoolField): JsonObject {
  return { field: b.field, label: b.label };
}

/**
 * A select's `options`. A value that is a number is an int in every table here (`scar_side`, the wristband and
 * shoulder-bar sides, 0 and plus or minus 1), so it is written without a decimal point.
 */
export function selectJson(s: SelectField): JsonObject {
  return {
    field: s.field,
    label: s.label,
    options: s.options.map(([v, lbl]) => ({ value: typeof v === "number" ? new PyInt(v) : v, label: lbl })),
  };
}

export function garmentJson(g: GarmentSlot): JsonObject {
  const out: { [key: string]: Json } = {
    id: g.id,
    label: g.label,
    color: colorJson(g.color),
  };
  if (g.ranges.length > 0) out.ranges = g.ranges.map(rangeJson);
  if (g.bools.length > 0) out.bools = g.bools.map(boolJson);
  if (g.selects.length > 0) out.selects = g.selects.map(selectJson);
  if (g.requires !== null) out.requires = g.requires;
  return out;
}

/**
 * The whole public surface, as plain JSON-able data.
 *
 * No coordinate, no head-radius fraction, nothing derived from a `Skeleton`:
 * only field names, labels and the ranges that have actually been rendered
 * and judged. A visitor's browser turns this into controls without ever
 * knowing what the fields mean; only `render_character` does.
 */
export function buildCatalogue(): JsonObject {
  return {
    starting_points: {
      cast: castPoints().map((s) => ({ id: s.id, label: s.label })),
      bases: basePoints().map((s) => ({ id: s.id, label: s.label })),
    },
    bodies: sorted(Object.keys(BODY_TYPES)).map((name) => ({ id: name, label: lookup(BODY_LABELS, name) })),
    body_ignores: Object.fromEntries(Object.entries(BODY_IGNORES).map(([body, fields]) => [body, [...fields]])),
    hand_styles: HAND_STYLES.map((name) => ({ id: name, label: lookup(HAND_LABELS, name) })),
    grip_styles: GRIP_STYLES.map((name) => ({ id: name, label: lookup(GRIP_LABELS, name) })),
    height: rangeJson(HEIGHT),
    face_age: rangeJson(AGE),
    colors: COLORS.map(colorJson),
    hairstyles: sorted(Object.keys(HAIRSTYLES)).map((name) => ({ id: name, label: lookup(HAIRSTYLE_LABELS, name) })),
    finishes: FINISHES.map((name) => ({ id: name, label: lookup(FINISH_LABELS, name) })),
    highlight_strength: rangeJson(HIGHLIGHT_STRENGTH),
    hair_length: rangeJson(HAIR_LENGTH),
    hair_tail: rangeJson(HAIR_TAIL),
    waist_shift: rangeJson(WAIST_SHIFT),
    bust: rangeJson(BUST),
    chest: rangeJson(CHEST),
    skin_swatches: SKIN_SWATCHES.map(([lbl, v]) => ({ label: lbl, value: v })),
    hair_knot: boolJson(HAIR_KNOT),
    garments: GARMENTS.map(garmentJson),
    face: {
      ranges: FACE_RANGES.map(rangeJson),
      bools: FACE_BOOLS.map(boolJson),
      selects: FACE_SELECTS.map(selectJson),
    },
  };
}

/** The committed form: stable key order, trailing newline, diffable. */
export function toJson(): string {
  return `${dumps(buildCatalogue(), { indent: 2, sortKeys: false })}\n`;
}
