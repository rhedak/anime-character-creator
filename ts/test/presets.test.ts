// `presets.ts` against Python: every character as `asdict` and as the compact JSON `encode_params` encodes (which
// tells an int from a float in each of the 134 fields), and the tables around them.

import assert from "node:assert/strict";
import { test } from "node:test";
import { ADULT_FACE_AGE } from "../src/model.ts";
import {
  BASE_FEMALE,
  BASE_MALE,
  BLACK_HAIR,
  CRYSTAL_KIT,
  DISPLAY_NAMES,
  EXPRESSIONS,
  HAIR,
  MAN_LASH,
  NEUTRAL_BASES,
  PRESETS,
  ROSTERS,
  UNIFORM,
} from "../src/presets.ts";
import { SUPPORTING } from "../src/supporting.ts";
import { dumps } from "../src/pyjson.ts";
import { dataclassJson, paramsJsonText } from "../src/urlstate.ts";
import { fixture } from "./phase3.ts";

const fx = fixture("presets.json");

function checkTable(label: string, table: Record<string, object>, want: Record<string, { dict: unknown; json: string }>): void {
  test(`${label}: the same names in the same order, every field deep-equal, every spelling the same`, () => {
    assert.deepEqual(Object.keys(table), Object.keys(want));
    const bad: string[] = [];
    for (const [name, p] of Object.entries(table)) {
      const w = want[name]!;
      assert.deepEqual(JSON.parse(JSON.stringify(p)), w.dict, `${name}: fields`);
      // The text carries int against float in every field: `1` and `1.0` differ here and nowhere else.
      if (paramsJsonText(p as never) !== w.json) bad.push(name);
    }
    assert.deepEqual(bad, []);
  });
}

checkTable("PRESETS", PRESETS, fx.presets);
checkTable("NEUTRAL_BASES", NEUTRAL_BASES, fx.neutral_bases);
checkTable("SUPPORTING", SUPPORTING, fx.supporting);

test("EXPRESSIONS: deltas, in order, and the same text", () => {
  assert.deepEqual(Object.keys(EXPRESSIONS), Object.keys(fx.expressions));
  for (const [name, e] of Object.entries(EXPRESSIONS)) {
    assert.deepEqual(JSON.parse(JSON.stringify(e)), fx.expressions[name].dict, name);
    assert.equal(dumps(dataclassJson("Expression", e), { sortKeys: true, compact: true }), fx.expressions[name].json, name);
  }
  assert.equal(Object.keys(EXPRESSIONS).length, 13);
});

test("ROSTERS (with the later assignments) and DISPLAY_NAMES", () => {
  assert.deepEqual(Object.keys(ROSTERS), Object.keys(fx.rosters));
  assert.deepEqual(JSON.parse(JSON.stringify(ROSTERS)), fx.rosters);
  assert.deepEqual(DISPLAY_NAMES, fx.display_names);
  assert.deepEqual(Object.keys(DISPLAY_NAMES), Object.keys(fx.display_names));
  for (const members of Object.values(ROSTERS)) for (const m of members) assert.ok(m in PRESETS, m);
});

test("the constants", () => {
  assert.equal(MAN_LASH, fx.constants.MAN_LASH);
  assert.equal(BLACK_HAIR, fx.constants.BLACK_HAIR);
  assert.equal(HAIR, fx.constants.HAIR);
  assert.equal(UNIFORM, fx.constants.UNIFORM);
  assert.deepEqual([...CRYSTAL_KIT], fx.constants.CRYSTAL_KIT);
});

test("every preset is twenty-one or older, the neutral bases are adults, and the bases are the registry's defaults but for what they name", () => {
  for (const p of Object.values(PRESETS)) assert.ok(p.face_age >= ADULT_FACE_AGE);
  assert.equal(BASE_FEMALE.face_age, 1.0);
  assert.equal(BASE_MALE.hairstyle, "short_crop");
});

test("Kyoko and Tomohiro differ from Satoko and Satoshi in the three disguise fields, the outfit and the age, and nothing else", () => {
  const strip = (p: object): Record<string, unknown> => {
    const { hair_color, hair_tip_color, outfit, face_age, face, ...rest } = p as Record<string, unknown> & { face: object };
    void hair_color; void hair_tip_color; void outfit; void face_age;
    const { scar_side, ...faceRest } = face as Record<string, unknown>;
    void scar_side;
    return { ...rest, face: faceRest };
  };
  assert.deepEqual(strip(PRESETS.kyoko!), strip(PRESETS.satoko!));
  assert.deepEqual(strip(PRESETS.tomohiro!), strip(PRESETS.satoshi!));
  assert.equal(PRESETS.kyoko!.face.scar_side, 0);
  assert.equal(PRESETS.satoko!.face.scar_side, 1);
});

