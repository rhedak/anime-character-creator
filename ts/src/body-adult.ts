// Body profiles with no Python counterpart: the adult woman of ref/franzi/ and whatever follows her. They live apart
// from `BODY_TYPES` (body.ts), which mirrors the frozen Python table and is enumerated by the recorded-call fixtures,
// the catalogue and its tests; `skeletonFor` looks a name up in both. Docs: docs/adult-body-plan.md.

import { profile, type BodyProfile } from "./skeleton.ts";

/**
 * Landmarks are read off the references' silhouettes (harness/franzi/measure.py, docs/adult-body-status.md). The
 * units are head radii below the head centre, so the chin is at 1.0 and a width in head heights is a half-width here.
 */
/** The adult woman's landmark half-widths, in head radii: what the knot tables in body-adult-data.ts were measured at. */
export const ADULT_REF = {
  shoulder_half_w: 1.0,
  waist_half_w: 0.69,
  hip_half_w: 1.23,
  arm_half_w: 0.14,
  arm_x: 1.14,
  leg_half_w: 0.38,
  neck_half_w: 0.22,
} as const;

export const ADULT_BODY_TYPES: Readonly<Record<string, BodyProfile>> = {
  adult_female: profile(6.4, {
    shoulder_y: 1.56,
    waist_y: 3.6,
    hip_y: 5.4,
    ankle_y: 10.4,
    ...ADULT_REF,
    wrist_y: 6.2,
    wrist_x: 1.5,
  }),
};
