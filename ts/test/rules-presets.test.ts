// Rules over the registries of characters and moods: the cast, the neutral bases, the supporting cast, the expressions and
// the adult floor. tests/test_smoke.py, tests/test_open_mouth.py, tests/test_supporting.py and the policy pins. A new preset
// or expression that breaks one of these needs fixing at its source, not the rule loosened.

import assert from "node:assert/strict";
import { test } from "node:test";
import { AGE, basePoints, castPoints } from "../src/catalogue.ts";
import { mouthDepthShare } from "../src/face.ts";
import { ADULT_FACE_AGE, expressionAppliedTo } from "../src/model.ts";
import type { CharacterParams } from "../src/params.ts";
import { DISPLAY_NAMES, EXPRESSIONS, NEUTRAL_BASES, PRESETS, ROSTERS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";
import { DISPLAY_NAMES as SUPPORTING_NAMES, SUPPORTING } from "../src/supporting.ts";
import { BASE_NAMES, PRESET_NAMES } from "./rules-util.ts";
import { fromstring } from "./svg-scan.ts";

const preset = (name: string): CharacterParams => PRESETS[name] as CharacterParams;
const sameSet = (a: Iterable<string>, b: Iterable<string>): void => assert.deepEqual([...new Set(a)].sort(), [...new Set(b)].sort());

for (const base of BASE_NAMES) {
  test(`test_neutral_bases_render_and_stay_out_of_the_cast[${base}]`, () => {
    // The web tool's starting points. They render like any preset, but they are not presets: `PRESETS` is the named
    // characters the README and `ref-out/` publish, and a base has no design to publish there.
    const root = fromstring(renderCharacter(NEUTRAL_BASES[base] as CharacterParams));
    assert.equal(root.tag, "svg");
    assert.ok(!(base in PRESETS));
  });
}

for (const name of Object.keys(EXPRESSIONS).sort()) {
  for (const who of PRESET_NAMES) {
    test(`test_an_expression_changes_the_mood_and_nothing_else[${who}-${name}]`, () => {
      // The one property that makes a named mood reusable across characters. An expression is a delta, not a `FaceStyle`:
      // if it ever became a whole face, every character wearing it would silently inherit the stock aperture and stop
      // looking like themselves, while still rendering perfectly. The fields a mood may move may move, and every field
      // that says who the face is must come through untouched.
      const identity = ["eye_size", "eye_width", "eye_corner", "eye_tilt", "iris_size", "scar_side"] as const;
      const before = preset(who);
      const after = expressionAppliedTo(EXPRESSIONS[name]!, before);
      for (const f of identity) assert.equal(after.face[f], before.face[f], `${name} altered ${f}, which is who the face is rather than what it is doing`);
      assert.equal(after.hairstyle, before.hairstyle);
      assert.deepEqual(after.outfit, before.outfit);
      const moved = (["brow_tilt", "brow_weight", "eye_openness", "eye_lower_lid", "mouth_curve", "mouth_width"] as const).filter((f) => after.face[f] !== before.face[f]);
      assert.ok(moved.length > 0, `${name} on ${who} changes nothing at all`);
      fromstring(renderCharacter(after));
    });
  }
}

test("test_every_character_has_a_display_name_and_a_roster", () => {
  // Adding a preset has to mean adding it to the sheet, or it is invisible.
  for (const name of Object.keys(PRESETS)) {
    assert.ok(name in DISPLAY_NAMES, `${name} has no display name for the sheet`);
    assert.ok(
      Object.values(ROSTERS).some((names) => names.includes(name)),
      `${name} is on no roster`,
    );
  }
});

test("test_the_satoshi_roster_is_satoshis_persona_not_satokos", () => {
  // The owner's call on 2026-08-09: Satoshi leads, then alphabetical, no Satoko or Kyoko. It is derived from `cast`
  // rather than a second hand-written list so the two cannot drift apart.
  const roster = ROSTERS.satoshi as readonly string[];
  assert.equal(roster[0], "satoshi", "Satoshi has to lead his own roster");
  assert.ok(!roster.includes("satoko") && !roster.includes("kyoko"), "this is Satoshi's persona; Satoko and Kyoko belong to the other one");
  assert.ok(roster.includes("tomohiro"), "Tomohiro is Satoshi's own before-self and stays");
  const rest = roster.slice(1);
  assert.deepEqual(rest, [...rest].sort(), "everyone after Satoshi should be alphabetical");
  // Same membership as `cast` minus the two that were swapped out: nobody is on one roster and not the other except the two pairs that differ on purpose.
  sameSet(roster, (ROSTERS.cast as readonly string[]).filter((n) => n !== "satoko" && n !== "kyoko"));
});

test("test_every_preset_is_at_least_twenty_one", () => {
  // Every named character is twenty-one or older, the highest common age of majority. `ADULT_FACE_AGE` is the face the
  // project reads as twenty-one, the grown face is 1.0, and older faces sit above it.
  for (const [name, p] of Object.entries(PRESETS)) assert.ok(p.face_age >= ADULT_FACE_AGE, name);
  for (const [name, p] of Object.entries(NEUTRAL_BASES)) assert.ok(p.face_age >= 1.0, name);
  assert.equal(ADULT_FACE_AGE, 0.9);
});

test("test_the_gui_age_slider_starts_at_twenty_one", () => {
  assert.equal(AGE.lo, ADULT_FACE_AGE);
});

test("test_startled_opens_the_mouth_and_leaves_what_it_does_not_name", () => {
  const p = preset("satoshi");
  const startled = expressionAppliedTo(EXPRESSIONS.startled as never, p);
  assert.ok(startled.face.mouth_open > 0);
  assert.equal(startled.face.eye_size, p.face.eye_size); // a mood is a delta, not a new face
  assert.equal(startled.face.scar_side, p.face.scar_side);
});

test("test_the_comic_expressions_exist_and_each_changes_the_face", () => {
  const p = preset("satoshi");
  const base = renderCharacter(p);
  for (const name of ["startled", "exasperated", "alert", "smile", "menacing", "unyielding", "at_ease"]) {
    assert.ok(name in EXPRESSIONS, `${name} is not an expression`);
    assert.notEqual(renderCharacter(expressionAppliedTo(EXPRESSIONS[name] as never, p)), base, name);
  }
});

test("test_an_opening_beyond_the_width_does_not_make_the_mouth_taller_than_wide", () => {
  assert.ok(mouthDepthShare(0.3) === 0.3 && mouthDepthShare(0.8) === 0.8);
  const shares = Array.from({ length: 21 }, (_, o) => mouthDepthShare(o / 10));
  assert.deepEqual(shares, [...shares].sort((a, b) => a - b)); // it never closes up again as the opening grows
  assert.ok(Math.max(...shares) < 1.0);
});

test("test_every_supporting_character_has_a_display_name", () => {
  sameSet(Object.keys(SUPPORTING_NAMES), Object.keys(SUPPORTING));
  assert.ok(Object.keys(SUPPORTING).length >= 3);
});

test("test_none_of_them_is_a_preset_or_offered_by_the_web_tool", () => {
  // The owner's condition: there are enough starting points already. The web tool offers `catalogue._cast_points()` and
  // `_base_points()`, which here are `castPoints()` and `basePoints()`.
  const offered = new Set([...castPoints(), ...basePoints()].map((sp) => sp.id));
  assert.ok(offered.size >= 22);
  for (const name of Object.keys(SUPPORTING)) {
    assert.ok(!(name in PRESETS), `${name} is a preset`);
    assert.ok(!(name in NEUTRAL_BASES), `${name} is a neutral base`);
    assert.ok(!offered.has(name), `${name} is offered by the web tool`);
  }
});
