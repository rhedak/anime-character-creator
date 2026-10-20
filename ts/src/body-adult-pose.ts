// Which arms of the adult woman are raised, how far, and with which hand (docs/franzi-expressions-plan.md, steps 3 and 4). A leaf module: it reads the parameters and nothing
// else, so the body outline (body-adult-parts.ts) can ask which arms to leave out without importing the code that draws them (body-adult-pose-arm.ts).
//
// The companion asks for a gesture as an angle per arm, `right_arm_out` and `left_arm_out` (degrees from the body: 0 hangs, 90 is level, about 125 to 155 is raised high; the character's own
// right arm is the viewer's left, as on the chibi). A raised arm is the hanging arm turned about the shoulder, so the angle is the whole of the pose; the hand it ends in is the open palm
// unless `grip_style` is "fist" (the chibi's word for a closed hand). The hanging arm keeps the traced relaxed hand and none of this applies to it.

import type { CharacterParams } from "./params.ts";

export type PoseHand = "open" | "fist";

export interface ArmPose {
  /** -1 for the viewer's left (the character's own right arm), +1 for the viewer's right. */
  readonly sign: number;
  /** Degrees from hanging, outward then up: 90 level, 180 straight up. */
  readonly angle: number;
  readonly hand: PoseHand;
}

/** The furthest an arm is turned: straight up. */
export const ARM_POSE_MAX = 180;

/**
 * The least an arm is turned to be drawn on its own: below it the arm hangs, in the body's one outline. A separate arm turned a degree or two leaves a sliver of page between it and the
 * ribs, where the one outline has no gap above the gap's tip, so the hanging drawing carries the arm up to here (6 degrees moves the arm's inner edge about 0.06 H at the gap's tip, which is a
 * gap and no longer a sliver).
 */
export const ARM_POSE_MIN = 6;

/** The depth below the chin, in head heights, where a raised arm begins and turns: the shoulder's tip. The body outline on that side stops its shoulder here too. */
export const RAISED_SHOULDER_D = 0.36;

/**
 * Whether a garment that would stay on the hanging arm is worn: a coat or a robe. Their sleeves are cut for the hanging arm, so until they follow a raised one the arms stay down under
 * them, as the companion treats a gesture with no pictures (it does nothing). The blouse's sleeves do follow a raised arm (`adultBlouse` splits them from the bodice along the seam).
 */
export const armsUnderSleeves = (p: CharacterParams): boolean => p.outfit.coat_color !== null || p.outfit.robe_color !== null;

/** The raised arms, left then right. None when both hang (the default: her drawing is then exactly what it was) or a sleeve is in the way. */
export function adultArmPoses(p: CharacterParams): ArmPose[] {
  if (armsUnderSleeves(p)) return [];
  const hand: PoseHand = gripIsFist(p) ? "fist" : "open";
  const out: ArmPose[] = [];
  for (const sign of [-1, 1]) {
    const angle = Math.max(0, Math.min(ARM_POSE_MAX, Number(sign === -1 ? p.right_arm_out : p.left_arm_out)));
    if (angle >= ARM_POSE_MIN) out.push({ sign, angle, hand });
  }
  return out;
}

/** Whether the hands are fists (`grip_style` "fist"): a raised arm's hand, and a hanging arm's too, which is then the traced fist where it was the relaxed hand. */
export const gripIsFist = (p: CharacterParams): boolean => p.grip_style === "fist";

/** The sides whose arm is raised, for the body outline to leave out. */
export const raisedSides = (p: CharacterParams): number[] => adultArmPoses(p).map((a) => a.sign);
