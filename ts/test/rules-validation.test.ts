// Rules of the link and metadata layer: tests/test_metadata.py (the portable tests) and the old-link and adult-floor tests of
// tests/test_smoke.py. A link is the one way a character arrives from outside, so what it may and may not become is a rule.
// Errors are asserted by class (Python's names, `PyError.pyType`) and, where Python asserted one, the stable fragment.

import assert from "node:assert/strict";
import { test } from "node:test";
import { TOOL_URL, REPOSITORY_URL, NOVEL_URL } from "../src/attribution.ts";
import { ADULT_FACE_AGE, characterParams } from "../src/model.ts";
import type { CharacterParams } from "../src/params.ts";
import { PRESETS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";
import { characterUrl, decodeParams, paramsFromDict, paramsJsonText, paramsToDict } from "../src/urlstate.ts";
import { assertRaises } from "./rules-util.ts";
import { findChild, fromstring, itertext } from "./svg-scan.ts";

const GARBAGE: [string, string][] = [
  ["bad base64", "not-valid-base64!!!"],
  ["empty", ""],
  ["unknown field", "eyJub3RfYV9maWVsZCI6MX0"], // valid base64/JSON, not a CharacterParams field
];
for (const [label, garbage] of GARBAGE) {
  test(`test_decode_rejects_what_it_did_not_encode[${label}]`, () => {
    // Python asserts the class ValueError and no text. Every codec failure (base64, UTF-8, JSON, an unknown field) must
    // arrive as a ValueError, not as the JavaScript or inner class that raised it.
    assertRaises(() => decodeParams(garbage), "ValueError");
  });
}

test("test_character_url_carries_the_base_and_the_encoding", () => {
  const p = PRESETS.krista as CharacterParams;
  const url = characterUrl(p, TOOL_URL);
  assert.ok(url.startsWith(`${TOOL_URL}?c=`), url);
  const back = decodeParams(url.split("?c=", 2)[1] as string);
  assert.equal(paramsJsonText(back), paramsJsonText(p));
});

test("test_metadata_embeds_a_working_character_link", () => {
  const p = PRESETS.krista as CharacterParams;
  const svg = renderCharacter(p, null, null, true);
  const root = fromstring(svg);
  const md = findChild(root, "metadata");
  assert.ok(md !== undefined, "no <metadata> element");
  const text = (tag: string): string | undefined => {
    const el = findChild(md, tag);
    return el === undefined ? undefined : itertext(el);
  };
  const link = text("character");
  assert.ok(link !== undefined && link.startsWith(TOOL_URL), String(link));
  const back = decodeParams(link.split("?c=", 2)[1] as string);
  assert.equal(paramsJsonText(back), paramsJsonText(p));
  assert.equal(text("source"), TOOL_URL);
  assert.equal(text("repository"), REPOSITORY_URL);
  assert.equal(text("novel"), NOVEL_URL);
});

test("test_an_old_link_loads_as_the_tall_chibi", () => {
  // A link from before the realistic build and the compressed chibi were retired, carrying another `heads` or `body: null`,
  // loads as the default tall chibi rather than failing.
  const old: Record<string, unknown> = paramsToDict(PRESETS.satoko as CharacterParams);
  old.heads = 6.0;
  old.body = null;
  const p = paramsFromDict(old);
  const realHair = paramsFromDict({ ...paramsToDict(PRESETS.satoko as CharacterParams), hairstyle: "long_traced_real" });
  assert.equal(realHair.hairstyle, "long_traced");
  assert.equal(p.body, characterParams().body);
  assert.equal(renderCharacter(p), renderCharacter(PRESETS.satoko));
});

for (const style of ["realistic", "anime"]) {
  test(`test_an_old_link_with_an_eye_style_loads_with_the_one_eye[${style}]`, () => {
    // The second eye style and its `eye_glow` knob are retired; a link carrying either loads with the one eye.
    const old: Record<string, unknown> = paramsToDict(PRESETS.satoko as CharacterParams);
    old.face = { ...(old.face as Record<string, unknown>), eye_style: style, eye_glow: 0.5 };
    assert.equal(renderCharacter(paramsFromDict(old)), renderCharacter(PRESETS.satoko));
  });
}

test("test_a_character_from_outside_is_never_drawn_below_the_floor", () => {
  // Links, the web tool and a companion app's model all arrive through `params_from_dict`, which raises a younger face to the adult floor.
  const d = paramsToDict(PRESETS.satoko as CharacterParams);
  for (const age of [0.0, 0.5, 0.89]) {
    assert.equal(paramsFromDict({ ...d, face_age: age }).face_age, ADULT_FACE_AGE, `face_age ${age}`);
  }
  assert.equal(paramsFromDict({ ...d, face_age: 1.4 }).face_age, 1.4);
});
