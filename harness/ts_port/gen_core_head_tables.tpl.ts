// The core-head module's tables: the hair cuts' traced contours, locks and strands, and the numbers they are placed by.
// Generated once by harness/ts_port/gen_core_head.py from character.py (never typed), then owned by hand.

import { degrees, pyAcos } from "./pynum.ts";
import type { Chain, Point, Segment } from "./tables.ts";

//@lead Lock
export type Lock = readonly [string, readonly Point[], number, number];

//@const _HAIR_CHEEK_Y
//@const _HAIR_TIP_LINE
//@const _HAIR_FADE
//@const _HAIR_CROWN_Y
//@const _CROWN_R
//@lead _CROWN_TO_TEMPLE
export const CROWN_TO_TEMPLE = degrees(pyAcos(0.30 / CROWN_R));
//@const _FALL_TEMPLE_X
//@const _FALL_CHEEK_X
//@const _FALL_MID_X
//@const _FALL_WIDE_X
//@const _FALL_FLARE_X
//@const _FALL_TIP_X
//@const _LONG_EDGE_START
//@const _LONG_EDGE
//@const _LONG_LINE_START
//@const _LONG_LINE
//@const _LONG_BASE_TIP
//@const _LONG_TONE_LIFT
//@const _LONG_LINE_TUCK
//@const _LONG_CROWN_AT
//@const _LONG_LOCKS_FALL
//@const _LONG_LOCKS
//@const _SHORT_LOCKS
//@const _CROP_LOCKS
//@const _PARTED_LOCKS_FALL
//@const _PARTED_LOCKS
//@const _PARTED_EDGE
//@const _PARTED_SEAM_L
//@const _PARTED_CROWN_AT
//@const _PARTED_SEAM_R
//@const _PARTED_BASE_TIP
//@const _PARTED_LINE
//@const _PARTED_LOCK_L
//@const _PARTED_LOCK_R
//@const _PARTED_APEX_L
//@const _PARTED_APEX_R
//@const _PARTED_UNDER_L
//@const _PARTED_UNDER_R
//@const _PARTED_TIPS_BEHIND
//@const _PARTED_TIPS_FRONT
//@const _PARTED_SEAM_LIFT
//@const _PARTED_TONE_LIFT
//@const _PARTED_TONE_WIDEN
//@const _CROP_START
//@const _CROP_EDGE
//@const _CROP_CROWN_AT
//@const _CROP_TEMPLE_L
//@const _CROP_TEMPLE_R
//@const _CROP_BASE_TIP
//@const _CROP_REAL_START
//@const _CROP_REAL_EDGE
//@const _CROP_REAL_SIDEBURN_PUSH
//@lead _CROP_REAL_SIDEBURN_L
/** A Python `range(start, stop)`. */
export interface PyRange {
  readonly start: number;
  readonly stop: number;
}
/** `i in range(...)` for an int `i`. */
export const inRange = (i: number, r: PyRange): boolean => r.start <= i && i < r.stop;
export const CROP_REAL_SIDEBURN_L: PyRange = { start: -1, stop: 8 };
export const CROP_REAL_SIDEBURN_R: PyRange = { start: 32, stop: 42 };
//@const _CROP_REAL_EAR_X
//@const _CROP_REAL_EAR_MARGIN
//@const _CROP_REAL_EAR_BUFFER
//@const _CROP_REAL_TEMPLE_L
//@const _CROP_REAL_TEMPLE_R
//@const _CROP_REAL_CROWN_AT
//@const _CROP_REAL_FALL
//@const _CROP_REAL_TOL
//@const _CROP_REAL_SCALE
//@const _CROP_FRINGE_START
//@const _CROP_FRINGE
//@const _CROP_NOTCHES
//@const _CROP_FILL_INSET
//@const _CROP_TONE_LIFT
//@const _CROP_SWEEP
//@const _CROP_STRAND_RUN
//@const _TOUSLE_NOTCHES
//@const _TOUSLE_TIPS
//@const _TOUSLE_TEMPLE
//@const _TOUSLE_CROWN
//@const _FRINGED_BASE_TIP
//@const _FRINGED_FRONT
//@const _FRINGED_MASS
//@const _FRINGED_UNDERSIDE
//@const _FRINGED_STRANDS
//@const _FRINGED_OPENINGS
//@const _FRINGED_SHADE
//@const _FRINGED_LOCKS
//@const _EAR_TOP_Y
//@const _EAR_BOT_Y
//@const _EYE_ASPECT
//@const _EYE_GAP
//@const _EYE_CORNER_CLEAR
//@const _MATURE_EYE_DROP
//@const _MATURE_EYE_SHARE
