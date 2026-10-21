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
  /** How far the forearm folds at the elbow, in degrees, further in the direction the arm was raised: 0 is straight, 90 square, about 140 folded back. */
  readonly bend: number;
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

/**
 * The least elbow bend, in degrees, that is drawn (a bent arm is drawn on its own), and the most the elbow folds. The traced arm's upper arm and forearm lean outward by about 7 and 12 degrees
 * when it hangs, so the angle between them when folded is |175 - bend|, and the two outer edges, which form the crease inside the fold, cross only if the forearm is long enough to reach the
 * crossing, at half the arm's width over the tangent of half that angle. 155 leaves a crease of 20 degrees that crosses inside the forearm; a folded arm cannot reach the angle of the fold
 * the packs draw (about 15 degrees) with arms as wide as these, and is clamped here instead of drawn as a tangle.
 */
export const ARM_ELBOW_MIN = 1;
export const ARM_ELBOW_MAX = 155;

/** The depth below the chin, in head heights, where a raised arm begins and turns: the shoulder's tip. The body outline on that side stops its shoulder here too. It is a knot of the shoulder table (0.4), so the line and the arm's edge both lie on the hanging outline's own curve there; at 0.36, between knots, a point on the straight interpolation made the curve wobble and the outline step at the tip. */
export const RAISED_SHOULDER_D = 0.4;

/**
 * Whether a garment that would stay on the hanging arm is worn: a coat or a robe. Their sleeves are cut for the hanging arm, so until they follow a raised one the arms stay down under

 * them, as the companion treats a gesture with no pictures (it does nothing). The blouse's sleeves do follow a raised arm (`adultBlouse` splits them from the bodice along the seam), and so do the school shirt's
 * and blazer's (`adultPosedSleeve` in body-adult-pose-arm.ts: the posed arm's own silhouette, grown), so the blazer is not one of the coats.
 */
export const armsUnderSleeves = (p: CharacterParams): boolean => (p.outfit.coat_color !== null && p.outfit.coat_cut !== "blazer") || p.outfit.robe_color !== null;

/** The raised arms, left then right. None when both hang (the default: her drawing is then exactly what it was) or a sleeve is in the way. */
export function adultArmPoses(p: CharacterParams): ArmPose[] {
  if (armsUnderSleeves(p)) return [];
  const hand: PoseHand = gripIsFist(p) ? "fist" : "open";
  const out: ArmPose[] = [];
  for (const sign of [-1, 1]) {
    const swing = Math.max(0, Math.min(ARM_POSE_MAX, Number(sign === -1 ? p.right_arm_out : p.left_arm_out)));
    const folded = Math.max(0, Math.min(ARM_ELBOW_MAX, Number(sign === -1 ? p.right_elbow : p.left_elbow)));
    const bend = folded >= ARM_ELBOW_MIN ? folded : 0;
    // a bent arm is drawn on its own even when it hangs, because the one outline cannot bend: it is held out the least that leaves a gap beside the ribs
    const angle = bend > 0 ? Math.max(swing, ARM_POSE_MIN) : swing;
    if (angle >= ARM_POSE_MIN) out.push({ sign, angle, bend, hand });
  }
  return out;
}

/** Whether the hands are fists (`grip_style` "fist"): a raised arm's hand, and a hanging arm's too, which is then the traced fist where it was the relaxed hand. */
export const gripIsFist = (p: CharacterParams): boolean => p.grip_style === "fist";

/** The sides whose arm is raised, for the body outline to leave out. */
export const raisedSides = (p: CharacterParams): number[] => adultArmPoses(p).map((a) => a.sign);
