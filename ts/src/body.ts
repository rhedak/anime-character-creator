// The body profiles and the skeleton a character is drawn on: the part of character.py (BODY_TYPES, skeleton_for,
// hat_hair_margin, _limb_taper_at) that builds a Skeleton for a CharacterParams.

import { ADULT_BODY_TYPES } from "./body-adult.ts";
import { ADULT_BUILDS } from "./body-adult-build.ts";
import type { CharacterParams } from "./params.ts";
import { plainParams } from "./plain.ts";
import { PyError, pyMax, pyMin, truthy } from "./pynum.ts";
import { pyValueRepr } from "./pyvalue.ts";
import {
  BUILDS,
  applied,
  buildSkeletonWith,
  defaultHairMargin,
  headScaled,
  profile,
  replace,
  stretched,
  type BodyProfile,
  type Skeleton,
} from "./skeleton.ts";
import { HAT_BRIM } from "./tables.ts";

export const LONG_TORSO_HEAD_SCALE = 1.1;
export const SLENDER_HEAD_SCALE = 0.85;

const tallChibi: BodyProfile = profile(3.47, {
  shoulder_y: 1.13,
  waist_y: 2.384,
  hip_y: 2.955,
  hem_y: 4.26,
  boot_y: 3.39,
  ankle_y: 5.55,
  waist_half_w: 0.563,
  hip_half_w: 0.83,
  hem_half_w: 1.13,
  leg_half_w: 0.23,
});

/** Body profiles by name. `tall_chibi` is measured; the other two are laid out in character.py's comments. */
export const BODY_TYPES: Readonly<Record<string, BodyProfile>> = {
  ...ADULT_BODY_TYPES,
  tall_chibi: tallChibi,
  tall_chibi_long_torso: headScaled(
    { ...tallChibi, waist_y: (tallChibi.waist_y as number) + 0.5, hip_y: (tallChibi.hip_y as number) + 0.5 },
    LONG_TORSO_HEAD_SCALE,
  ),
  tall_slender: headScaled(
    profile(4.362, {
      shoulder_y: 1.4,
      waist_y: 3.0,
      hip_y: 3.9,
      hem_y: 4.43,
      boot_y: 5.675,
      ankle_y: 7.05,
      shoulder_half_w: 0.8,
      waist_half_w: 0.7,
      hip_half_w: 1.2,
      hem_half_w: 0.93,
      arm_half_w: 0.145,
      arm_x: 0.9,
      leg_half_w: 0.225,
      wrist_y: 3.947,
      wrist_x: 0.999,
      neck_half_w: 0.151,
    }),
    SLENDER_HEAD_SCALE,
  ),
};

export const TAPER_FROM = 0.8;
export const TAPER_TO = 1.3;
export const TAPER_MAX = 0.5;

/** How much limb taper a figure of this height is drawn with. */
export function limbTaperAt(height: number): number {
  return TAPER_MAX * pyMin(1.0, pyMax(0.0, (height - TAPER_FROM) / (TAPER_TO - TAPER_FROM)));
}

/** Headroom, in head radii above the skull, that `p`'s hat needs; 0 for none. */
export function hatHairMargin(p: CharacterParams): number {
  if (p.outfit.hat_color === null) return 0.0;
  const [start, segs] = HAT_BRIM;
  const top = pyMin(start[1], ...segs.flatMap(([c, e]) => [c[1], e[1]]));
  return -top - 1.0 + 0.06;
}

function skeletonAt(p: CharacterParams): Skeleton {
  const heads = BUILDS.chibi as number;
  let margin = hatHairMargin(p);
  const bodyProfile = BODY_TYPES[p.body];
  if (bodyProfile === undefined) throw new PyError("KeyError", pyValueRepr(p.body));
  // The hair always draws at the chibi build under a profile, so it needs the chibi build's own headroom.
  margin = pyMax(margin, defaultHairMargin(heads));
  let sk = buildSkeletonWith({ heads: bodyProfile.heads, frame: p.frame, bust: p.bust, min_hair_margin: margin });
  // The chibi's build, computed rather than written as 0.1: (2.4 - 2.0) / 4.0 in floating point.
  const chibi = buildSkeletonWith({ heads, frame: p.frame, bust: p.bust }).build;
  sk = applied(bodyProfile, sk, chibi);
  // Not stretched at all at 1.0, rather than stretched by one: the identity in floating point is not exact.
  if (p.height !== 1.0) {
    sk = stretched(sk, p.height, (h) => buildSkeletonWith({ heads: h, frame: p.frame, bust: p.bust, min_hair_margin: margin }));
  }
  if (p.face_age > 0.0) sk = replace(sk, { face_maturity: pyMin(1.0, p.face_age) });
  return replace(sk, { limb_taper: limbTaperAt(p.height) });
}

/** The skeleton `p` is drawn on: its body profile laid over the chibi build. */
export function skeletonFor(typed: CharacterParams): Skeleton {
  const p = plainParams(typed);
  let sk = skeletonAt(p);
  if (truthy(p.waist_shift)) {
    const shift = p.waist_shift * sk.head_r;
    sk = replace(sk, { waist_y: sk.waist_y + shift, hip_y: sk.hip_y + shift });
  }
  // A build of the adult woman's body (body-adult-build.ts): the skeleton carries it to `place`, which warps the outline by it. Every other body ignores it, and a skeleton
  // without one has no such key at all, so it is the same object the recorded calls hold.
  if (p.body_build !== null && p.body in ADULT_BODY_TYPES) {
    const build = ADULT_BUILDS[p.body_build];
    if (build === undefined) throw new PyError("KeyError", pyValueRepr(p.body_build));
    sk = replace(sk, { adult_build: build });
  }
  return sk;
}
