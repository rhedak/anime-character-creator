// Rules of the skeleton and the body profiles (no SVG, or one well-formed render at the end): the skeleton and body
// tests of tests/test_smoke.py. A figure's anchors are its body profile laid over the chibi build, stretched by `height`
// and shifted by `waist_shift`, and each rule below says what one knob may move and what it must leave alone.
//
// Two constants the Python tests read are not exported by the TypeScript modules that hold them (reported, not worked
// around in ts/src): `LONG_TORSO_HEAD_SCALE` (body.ts, 1.1) and `WIDTH_FOLLOW` (skeleton.ts, 0.6). They appear here as
// the literals the Python source gives, which is also what pins them.

import { ADULT_BODY_TYPES } from "../src/body-adult.ts";
import assert from "node:assert/strict";
import { test } from "node:test";
import { BODY_TYPES, limbTaperAt, skeletonFor } from "../src/body.ts";
import { armLine } from "../src/core-limbs.ts";
import { characterParams, replace } from "../src/model.ts";
import type { CharacterParams } from "../src/params.ts";
import { PRESETS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";
import { BUILDS, applied, buildSkeletonWith, bustY, bustReach, headScaled, replace as replaceSk, type BodyProfile, type Skeleton } from "../src/skeleton.ts";
import { approx, assertApprox } from "./rules-util.ts";
import { fromstring } from "./svg-scan.ts";

const LONG_TORSO_HEAD_SCALE = 1.1;
const WIDTH_FOLLOW = 0.6;
const CHIBI = BUILDS.chibi as number;

/** `(sk.<name> - sk.head_cy) / sk.head_r`: a landmark in head radii below the head centre. */
const hr = (sk: Skeleton, name: keyof Skeleton): number => ((sk[name] as number) - sk.head_cy) / sk.head_r;

test("test_a_body_profile_applies_at_the_chibi_build", () => {
  // A measured body replaces the chibi's lerped landmarks and nothing else: the figure takes the profile's height and
  // landmarks while `build` stays the chibi's own, so the face is unchanged.
  const p = PRESETS.katherina as CharacterParams;
  const profile = BODY_TYPES[p.body] as BodyProfile;
  const sk = skeletonFor(p);
  const plain = buildSkeletonWith({ heads: CHIBI, frame: p.frame });
  assert.equal(sk.build, plain.build);
  assert.ok(Math.abs(hr(sk, "waist_y") - (profile.waist_y as number)) < 1e-9, `waist ${hr(sk, "waist_y")} against ${profile.waist_y}`);
  assert.ok(Math.abs(hr(sk, "foot_y") - (2 * profile.heads - 1)) < 1e-6, `foot ${hr(sk, "foot_y")} against ${2 * profile.heads - 1}`);
});

for (const body of ["tall_chibi", "tall_chibi_long_torso"]) {
  test(`test_waist_shift_moves_the_belt_line_and_nothing_above_or_below_it[${body}]`, () => {
    // `waist_shift` slides the waist and hip together, in head radii, and leaves the shoulders, knees and soles where the
    // build put them. It is a character field, so it is ignored when a skeleton is handed in.
    const base = replace(PRESETS.satoshi as CharacterParams, { body, waist_shift: 0.0 });
    const shifted = replace(base, { waist_shift: 0.3 });
    const a = skeletonFor(base);
    const b = skeletonFor(shifted);
    assertApprox(b.waist_y, a.waist_y + 0.3 * a.head_r);
    assertApprox(b.hip_y, a.hip_y + 0.3 * a.head_r);
    for (const unchanged of ["shoulder_y", "knee_y", "ankle_y", "foot_y", "head_r", "head_cy"] as const) {
      assert.equal(b[unchanged], a[unchanged], unchanged);
    }
    fromstring(renderCharacter(shifted));
    assert.equal(renderCharacter(shifted, a), renderCharacter(base, a));
  });
}

test("test_tall_chibi_long_torso_is_tall_chibi_with_a_lower_belt_and_a_bigger_head", () => {
  // The default body is Katherina's measured `tall_chibi` with the belt half a head radius lower and the head 1.1 times
  // as big against the same body, and she keeps her own: her traced cuts were fitted to that profile's exact landmarks.
  const base = BODY_TYPES.tall_chibi as BodyProfile;
  const low = headScaled({ ...base, waist_y: (base.waist_y as number) + 0.5, hip_y: (base.hip_y as number) + 0.5 }, LONG_TORSO_HEAD_SCALE);
  const have = BODY_TYPES.tall_chibi_long_torso as BodyProfile;
  for (const name of Object.keys(base) as (keyof BodyProfile)[]) {
    const [h, l] = [have[name], low[name]];
    if (h === null || l === null) assert.equal(h, l, name);
    else assertApprox(h as number, l as number, undefined, name);
  }
  assert.equal(characterParams().body, "tall_chibi_long_torso");
  assert.equal((PRESETS.katherina as CharacterParams).body, "tall_chibi");
});

test("test_head_scaled_makes_the_head_bigger_against_the_same_body", () => {
  // `heads` alone would only rescale the whole figure. A scaled profile keeps the body's own proportions (its landmarks
  // against each other) and changes only the head against them, by exactly the scale.
  const base = BODY_TYPES.tall_chibi as BodyProfile;
  assert.deepEqual(headScaled(base, 1.0), base);
  const big = headScaled(base, 1.1);
  const sk0 = buildSkeletonWith({ heads: base.heads });
  const sk1 = buildSkeletonWith({ heads: big.heads });
  const a = applied(base, sk0, sk0.build);
  const b = applied(big, sk1, sk1.build);
  const legToHead = (sk: Skeleton): number => (sk.ankle_y - sk.hip_y) / (2 * sk.head_r);
  assertApprox(legToHead(b), legToHead(a) / 1.1);
  assertApprox((b.ankle_y - b.waist_y) / (b.waist_y - b.shoulder_y), (a.ankle_y - a.waist_y) / (a.waist_y - a.shoulder_y));
  assertApprox(b.waist_half_w / b.head_r, a.waist_half_w / a.head_r / 1.1);
});

test("test_a_skeleton_with_no_bust_is_the_skeleton_built_without_one", () => {
  // `bust=0` is the default in fact, not only in intent (`docs/bust-plan.md`).
  for (const heads of Object.values(BUILDS)) {
    assert.deepEqual(buildSkeletonWith({ heads, bust: 0.0 }), buildSkeletonWith({ heads }));
    assert.equal(bustReach(buildSkeletonWith({ heads })), 0.0);
  }
});

test("test_the_bust_rides_a_profiled_body_rather_than_the_one_it_replaced", () => {
  // The bust's height is derived from the shoulder and waist a profile or a waist shift leaves behind, so it always lies
  // between them. Stored, it kept the unprofiled body's height and went stale (`docs/bust-status.md`).
  for (const name of ["satoko", "katherina"]) {
    const sk = skeletonFor(replace(PRESETS[name] as CharacterParams, { bust: 1.0 }));
    assert.ok(sk.shoulder_y < bustY(sk) && bustY(sk) < sk.waist_y, `${name}: bust at ${bustY(sk)} between ${sk.shoulder_y} and ${sk.waist_y}`);
    const shifted = skeletonFor(replace(PRESETS[name] as CharacterParams, { bust: 1.0, waist_shift: 0.3 }));
    assert.ok(bustY(shifted) > bustY(sk), `${name}: the shifted bust did not move down`);
  }
});

for (const m of [0.25, 0.5, 1.0]) {
  test(`test_face_age_up_to_one_matures_only_the_head[${m}]`, () => {
    // `face_age` up to 1 draws a grown face through `Skeleton.face_build`; at 0 the face build is the figure's own, and
    // the body does not move with it.
    const p = replace(PRESETS.satoko as CharacterParams, { face_age: 0.0 });
    const sk0 = skeletonFor(p);
    const sk = skeletonFor(replace(p, { face_age: m }));
    assert.equal(sk0.build + sk0.face_maturity * (1.0 - sk0.build), sk0.build); // face_build of an unaged face is the build
    assert.ok(sk.build + sk.face_maturity * (1.0 - sk.build) > sk.build);
    assert.deepEqual(replaceSk(sk, { face_maturity: 0.0 }), sk0);
    fromstring(renderCharacter(replace(p, { face_age: m })));
  });
}

test("test_the_limbs_taper_with_the_height", () => {
  // `docs/detail-plan.md`, D4b: none at 0.8, half the adult taper from 1.3, linear between, carried on the skeleton the
  // figure is drawn on.
  assert.deepEqual([limbTaperAt(0.7), limbTaperAt(0.8), limbTaperAt(1.3), limbTaperAt(1.5)], [0.0, 0.0, 0.5, 0.5]);
  assertApprox(limbTaperAt(1.0), 0.2);
  const p = PRESETS.krista as CharacterParams;
  assertApprox(skeletonFor(replace(p, { height: 1.3 })).limb_taper, 0.5);
  assert.equal(skeletonFor(replace(p, { height: 0.8 })).limb_taper, 0.0);
});

for (const h of [0.8, 1.3]) {
  test(`test_the_height_stretches_below_the_shoulders_only[${h}]`, () => {
    // `height` stretches the tall chibi below the shoulder line, two thirds of the difference in the legs: against the
    // head, the shoulder line stays, the body's widths follow the height by `WIDTH_FOLLOW` and the neck's does not, the
    // torso changes by a third of what the legs do, and the knee stays half way down the leg. 1.0 is the tall chibi exactly.
    const p = PRESETS.satoko as CharacterParams;
    const base = skeletonFor(p);
    const tall = skeletonFor(replace(p, { height: h }));
    assert.deepEqual(skeletonFor(replace(p, { height: 1.0 })), base);
    assertApprox(hr(tall, "shoulder_y"), hr(base, "shoulder_y"));
    const grow = 1.0 + WIDTH_FOLLOW * (h - 1.0);
    for (const w of ["shoulder_half_w", "waist_half_w", "hip_half_w", "arm_half_w", "leg_half_w", "arm_x"] as const) {
      assertApprox(tall[w] / tall.head_r, (base[w] / base.head_r) * grow, undefined, w);
    }
    assertApprox(tall.neck_half_w / tall.head_r, base.neck_half_w / base.head_r);
    const run = (sk: Skeleton): number => hr(sk, "foot_y") - hr(sk, "shoulder_y");
    assertApprox(run(tall), run(base) * h);
    const torso = (sk: Skeleton): number => hr(sk, "hip_y") - hr(sk, "shoulder_y");
    const legs = (sk: Skeleton): number => hr(sk, "foot_y") - hr(sk, "hip_y");
    assertApprox(legs(tall) - legs(base), 2 * (torso(tall) - torso(base)));
    assertApprox(tall.knee_y, tall.hip_y + (tall.ankle_y - tall.hip_y) * 0.5);
    fromstring(renderCharacter(replace(p, { height: h })));
  });
}

test("test_a_body_profile_that_measures_the_wrist_moves_the_hand_and_the_rest_do_not", () => {
  // `wrist_y` and `wrist_x` are opt-in anchors on a body profile: the arm line takes them when they are set and derives
  // the wrist from the hip and the arm's width when they are not, so every body that never measured one draws as it always did.
  assert.ok(Object.keys(BODY_TYPES).length >= 3);
  for (const [name, profile] of Object.entries(BODY_TYPES)) {
    const sk = skeletonFor(characterParams({ body: name }));
    const measured = name === "tall_slender" || Object.hasOwn(ADULT_BODY_TYPES, name); // the adult woman's profile measures the wrist too
    assert.equal(profile.wrist_y !== null, measured, name);
    assert.equal(sk.wrist_y !== null, measured, name);
    const [, , centreWrist, wristY] = armLine(sk);
    if (measured) assert.deepEqual([wristY, centreWrist], [sk.wrist_y, sk.wrist_x]);
    else assertApprox(wristY, sk.hip_y + sk.arm_half_w * 0.8, undefined, name);
  }
});

test("test_only_a_profile_that_measured_the_neck_narrows_it", () => {
  // `neck_half_w` on a profile is opt-in too: her neck is a third narrower than the chibi's, and every other body keeps the build's own.
  const plain = skeletonFor(characterParams());
  const chibi = plain.neck_half_w / plain.head_r;
  for (const [name, profile] of Object.entries(BODY_TYPES)) {
    const sk = skeletonFor(characterParams({ body: name }));
    const narrow = name === "tall_slender" || Object.hasOwn(ADULT_BODY_TYPES, name); // and her neck
    assert.equal(profile.neck_half_w !== null, narrow, name);
    if (name === "tall_slender") assert.ok(sk.neck_half_w / sk.head_r < chibi * 0.75, `${name}: ${sk.neck_half_w / sk.head_r} against ${chibi}`);
  }
});

test("test_a_stretched_body_carries_its_measured_wrist_with_it", () => {
  const p = PRESETS.risa as CharacterParams;
  const sk = skeletonFor(p);
  const tall = skeletonFor(replace(p, { height: 1.2 }));
  const headsDown = (s: Skeleton): [number, number] => [((s.wrist_y as number) - s.head_cy) / s.head_r, (s.hip_y - s.head_cy) / s.head_r];
  const [wrist, hip] = headsDown(sk);
  const [tallWrist, tallHip] = headsDown(tall);
  assert.ok(tallWrist > wrist, "a taller figure's hand hangs lower, in head radii");
  // It keeps its place against the hip it was measured beside, rather than staying put.
  assert.ok(approx(tallWrist - tallHip, wrist - hip, 0.03), `${tallWrist - tallHip} against ${wrist - hip}`);
});
