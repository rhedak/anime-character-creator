// The arms: `_arms` and the pieces it draws (the wristband, the cuffs, the joint cap), and `_hands_after_coat`. Port of the arm
// code of character.py, `core-limbs` module (see `harness/ts_port/modules.json`).

import { escape } from "./attribution.ts";
import { OUTLINE, bareShoulderSk, curve, interiorW, outlineW, strokeW } from "./character.ts";
import { shade } from "./colorutil.ts";
import { RAISED_ARM_INTO_BODY, armLine, armPivot, capTipY, capUndersideY, coatCut, garmentPlacement, limbBuild, raisedCoatSleeve, raisedShoulder, sleevePlacement, sleeveUnderCap, tracedCoat, wornSleeve } from "./core-limbs.ts";
import { handTraced, hand } from "./core-limbs-hands.ts";
import type { CharacterParams } from "./params.ts";
import { PyError, fmt1, fmt2, pyDiv, pyMax, pyMin, truthy } from "./pynum.ts";
import { numberOf, pyTypeName } from "./pyvalue.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Chain, Segment } from "./tables.ts";

/**
 * An empty dict, which a link or the corpus holds as a plain `{}`: falsy in Python, and `truthy` (kernel) says true for any
 * object that is not an array, a `Map` or a `Set`. (A kernel gap; reported.)
 */
const isEmptyDict = (v: unknown): boolean =>
  typeof v === "object" && v !== null && Object.getPrototypeOf(v) === Object.prototype && Object.keys(v).length === 0;

/** `str(x)` of a string-or-None colour, for a place Python formats a bare name. */
const pyStr = (v: string | null): string => (v === null ? "None" : v);

// ---------------------------------------------------------------------------------------------------------
// The arms

/**
 * The arm from the sleeve hem down to the hand.
 *
 * The tunic draws its own sleeve now, so this starts where the sleeve ends. The
 * arm's top edge is flat and sits exactly on the sleeve hem, at the same width,
 * so the two strokes land on each other and read as one line: the hem of the
 * garment and the top of the limb are the same edge, the way `_fall_edge` is
 * shared between the hair's mass and its front lock.
 *
 * Still drawn last of everything below the neck, because the hands have to be
 * over every garment. The apron's edge sits about three pixels inside the hand
 * at chibi, and a clipped hand is the one collision that would show.
 *
 * Whatever the undersleeve is, it carries the arm's whole length. Against a
 * green tunic a tan sleeve is what separates the arm from the torso; left bare,
 * the arm is skin and does the same job.
 *
 * `Outfit.sleeve_long` swaps that whole tube to `tunic_color`, cuff included:
 * the same geometry the short sleeve's undersleeve already uses, just read in
 * the tunic's own colour instead of the undersleeve's, since a long sleeve is
 * the tunic's own cloth continuing rather than a second garment showing
 * through it.
 *
 * `hands` splits the limb for a garment drawn over the arms: False draws the
 * arms without their hands, True only the hands, each in its arm's own swing,
 * and None, the default, both together. A coat worn over the arms covers them
 * down to its hem, and the hand still has to come out over it
 * (`_hands_after_coat`).
 *
 * `silhouette` draws each arm as bare shapes with no paint, hand left off,
 * for use inside a `<clipPath>`: the bust's outline is drawn only where it
 * lies over an arm (`_bust_over_arms`).
 */
export function arms(sk: Skeleton, p: CharacterParams, hands: boolean | null = null, silhouette = false): string {
  sk = bareShoulderSk(sk, p);
  const cx = sk.head_cx;
  // A coat's sleeve runs to the wrist by definition, so `coat_sleeves` is a
  // long sleeve whether or not anything is worn under it. Without this, a
  // character given coat sleeves and no undersleeve came out bare-armed: the
  // cap sleeve ended at the shoulder and skin ran from there to the hand.
  //
  // A long sleeve is the tunic's, so it goes with the tunic; a coat's sleeve
  // over no tunic takes the coat's colour, since the coat is then the only
  // cloth on the arm.
  const tunic = p.outfit.tunic_color;
  const coatSleeve = truthy(p.outfit.coat_sleeves) && p.outfit.coat_color !== null;
  const longSleeve = (truthy(p.outfit.sleeve_long) && tunic !== null) || coatSleeve;
  const sleeve: string | null = longSleeve
    ? truthy(tunic)
      ? tunic
      : p.outfit.coat_color
    : truthy(p.outfit.undersleeve_color)
      ? p.outfit.undersleeve_color
      : p.skin_tone;
  const [centreTop, topY, centreWrist, wristY] = armLine(sk);
  const elbowY = sk.waist_y;

  // Tapers on the build, the way the leg does. A constant-width tube is right at
  // chibi and matches ref/girl-chibi.png; at a taller build it reads as a pipe.
  const wTop = sk.arm_half_w;
  const wElbow = sk.arm_half_w * (1.0 - 0.15 * limbBuild(sk));
  const wWrist = sk.arm_half_w * (1.0 - 0.34 * limbBuild(sk));
  // The arm is narrower than the sleeve it comes out of, which is what says
  // "sleeve" rather than "plank". It used to be the sleeve's own width, to 1%,
  // deliberately, so the two outlines landed on each other and the silhouette
  // ran from shoulder to wrist with no step in it. That reads as one continuous
  // limb wearing nothing: the canon puts a visible step at the hem on both
  // characters and at both builds, and a garment hanging over a thinner arm is
  // the whole of what the step means.
  //
  // The arm's top edge still sits exactly on `_sleeve_hem_y`, so the hem line
  // and the top of the limb remain one line and the narrower arm simply leaves
  // the outer stretch of that line showing either side of it.
  //
  // Where the arm starts and ends is `_arm_line`, shared with `_hand_centre`.
  const centreElbow = centreTop + (centreWrist - centreTop) * 0.35;

  const parts: string[] = [];
  for (const s of [-1, 1]) {
    const x = (offset: number): number => cx + s * offset;

    // A raised arm in a coat whose sleeve is part of its silhouette starts at the shoulder
    // and is drawn in full from there (`_raised_shoulder`).
    const shoulder = wornSleeve(sk, p) === null ? raisedShoulder(sk, p, s) : null;
    let [armTop, armTopY] = shoulder !== null ? shoulder : [centreTop, topY];
    if (shoulder !== null) {
      // Carried on up its own line into the body, where the coat covers it, so the arm's
      // lower edge runs on until it meets the torso instead of stopping at the joint.
      const lean = pyDiv(centreWrist - centreTop, wristY - topY);
      armTopY -= RAISED_ARM_INTO_BODY * sk.head_r;
      armTop -= lean * RAISED_ARM_INTO_BODY * sk.head_r;
    }
    let topIn = armTopY;
    let topOut = armTopY;
    if (shoulder === null && sleeveUnderCap(sk, p)) {
      const tipY = capTipY(sk);
      topIn = capUndersideY(sk, centreTop - wTop, tipY);
      topOut = capUndersideY(sk, centreTop + wTop, tipY);
    }
    // The arm's outline, from its outer top corner down and back up the
    // inside, and the flat edge across the top that closes it. They are kept
    // apart because a sleeve worn over its own coat does not show that edge:
    // the shoulder rounds into the sleeve as one line in the reference, and
    // a straight cut across the top reads as a square shoulder tacked on.
    // It was never visible before, the coat being drawn over the arms; P5
    // flipped that order and put it on show (the owner, 2026-09-21).
    const topEdge = `M ${fmt1(x(armTop - wTop))} ${fmt1(topIn)} L ${fmt1(x(armTop + wTop))} ${fmt1(topOut)} `;
    const body =
      `Q ${fmt1(x(armTop + wTop * 1.03))} ${fmt1(topOut + (elbowY - topOut) * 0.55)} ` +
      `${fmt1(x(centreElbow + wElbow))} ${fmt1(elbowY)} ` +
      `Q ${fmt1(x(centreWrist + wWrist * 1.06))} ${fmt1(elbowY + (wristY - elbowY) * 0.5)} ` +
      `${fmt1(x(centreWrist + wWrist))} ${fmt1(wristY)} ` +
      `L ${fmt1(x(centreWrist - wWrist))} ${fmt1(wristY)} ` +
      `Q ${fmt1(x(centreWrist - wWrist * 1.06))} ${fmt1(elbowY + (wristY - elbowY) * 0.5)} ` +
      `${fmt1(x(centreElbow - wElbow))} ${fmt1(elbowY)} ` +
      `Q ${fmt1(x(armTop - wTop * 1.03))} ${fmt1(topIn + (elbowY - topIn) * 0.55)} ` +
      `${fmt1(x(armTop - wTop))} ${fmt1(topIn)} `;
    const d = topEdge + body + "Z";
    // No tone down the sleeve. It was a turn along the inner side, and a
    // narrower one was tried, but a stripe running the length of something as
    // long and thin as a sleeve reads as a two-tone plank at any width. The
    // canon's are flat tan, separated from the torso by the outline alone.
    const cut = wornSleeve(sk, p);
    // A traced sleeve under a traced jacket is the jacket's own sleeve: one
    // garment from the shoulder to the cuff, in the jacket's colour, and
    // `coat_sleeves` says the same of the parametric sleeve.
    const wearsCoatSleeve = p.outfit.coat_color !== null && ((cut !== null && tracedCoat(sk, p)) || truthy(p.outfit.coat_sleeves));
    // An arm held out takes the coat's sleeve with it, when the coat's sleeve is part of its
    // silhouette (`_sleeve_cutaway` leaves it out of the coat), and the shirt shows at the cuff.
    const raisedSleeve = cut === null && raisedCoatSleeve(p, s);
    const sleeveFill = pyStr(wearsCoatSleeve || raisedSleeve ? p.outfit.coat_color : sleeve);
    // The arm's bare outline, for `silhouette`.
    let shapes = [`<path d="${d}"`];
    let limb: string[];
    if (cut !== null) {
      const place = sleevePlacement(sk, cut, s);

      const traced = (chain: Chain): string => {
        const [start, segs] = chain;
        return curve(sk.head_cx, sk.head_cy, sk.head_r, place(start), segs.map(([q, e]): Segment => [place(q), place(e)]));
      };

      limb = [cut.sleeve, cut.cuff].map(
        (part) =>
          `<path d="${traced(part)}" fill="${sleeveFill}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`,
      );
      shapes = [cut.sleeve, cut.cuff].map((part) => `<path d="${traced(part)}"`);
    } else if (
      truthy(p.outfit.coat_sleeves) ||
      (p.outfit.tunic_color === null && p.outfit.undersleeve_color === null && !longSleeve)
    ) {
      // Filled whole, stroked everywhere but across the top. A bare arm
      // too: the shoulder rounds over it, and a line across its top read
      // as a sleeve's hem with no sleeve (`docs/bare-body-plan.md`, 4c).
      let outline = `M ${fmt1(x(armTop + wTop))} ${fmt1(topOut)} ${body}`;
      if (handTraced(p, s)) {
        // Open across the wrist: the traced hand runs on from the arm,
        // and a line there would cut it off (`_traced_hand`).
        const across = `L ${fmt1(x(centreWrist - wWrist))} ${fmt1(wristY)} `;
        const repl = `M ${fmt1(x(centreWrist - wWrist))} ${fmt1(wristY)} `;
        // `str.replace(a, b, 1)`: the first occurrence only (a function, so `$` in the text has no meaning).
        outline = outline.replace(across, () => repl);
      }
      limb = [
        `<path d="${d}" fill="${sleeveFill}" stroke="none" />`,
        `<path d="${outline}" fill="none" ` +
          `stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" stroke-linejoin="round" />`,
      ];
    } else {
      limb = [`<path d="${d}" fill="${sleeveFill}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`];
    }
    if (cut === null && truthy(p.outfit.coat_sleeves)) {
      limb.push(cuffLine(sk, x(centreWrist), wristY, wWrist));
    } else if (
      cut === null &&
      (p.outfit.undersleeve_color !== null || longSleeve) &&
      // A traced coat owns its sleeve, and what shows past it is the arm's own
      // sleeve and a line where it ends: a band there was a second tone the
      // reference's white cuff does not have (`docs/risa-plan.md`, M7).
      !tracedCoat(sk, p)
    ) {
      limb.push(wristCuff(sk, sleeve as string, x(centreWrist), wristY, wWrist));
    }
    if (raisedSleeve) {
      limb.push(raisedCuff(sk, p, s, d, sleeve as string, x(centreElbow), x(centreWrist), wElbow, wWrist, wristY));
    }
    limb.push(wristband(sk, p, s, x(centreWrist), wristY, wWrist));
    const hand_ = hand(sk, p, x(centreWrist), wristY, wWrist, s);
    if (hands === null && handTraced(p, s)) {
      // Under the arm, so a sleeve's cuff lies over the wrist as a sleeve
      // does, and a bare arm's fill over the hand's tucked-in top.
      limb.unshift(hand_);
    } else if (hands === null) {
      limb.push(hand_);
    } else if (truthy(hands)) {
      limb = [hand_];
    }

    // `s == -1` is the character's own right arm (viewer's left), `s == 1`
    // the left (viewer's right); see `CharacterParams.right_arm_out`. The
    // sign flips between the two sides so a positive angle always reads as
    // "outward" on whichever arm it is applied to, not as one screen
    // direction: the two sides are mirror images of each other, so the
    // same swing needs the opposite rotation to point the same way out.
    const swing = s === -1 ? p.right_arm_out : p.left_arm_out;
    if (truthy(silhouette)) {
      let turn = "";
      if (truthy(swing)) {
        const [pivotX, pivotY] = armPivot(sk, p, s);
        turn = ` transform="rotate(${fmt2(-s * swing)} ${fmt1(pivotX)} ${fmt1(pivotY)})"`;
      }
      for (const shape of shapes) parts.push(shape + turn + " />");
      continue;
    }
    if (truthy(swing)) {
      const [pivotX, pivotY] = armPivot(sk, p, s);
      const angle = -s * swing;
      // Drawn under the (rotated) limb, at the fixed, unrotated pivot:
      // see `_arm_joint_cap` for why this closes the gap the rotation
      // opens at the shoulder. A traced sleeve's cap is a disc about its
      // pivot and needs none.
      // An arm raised from the shoulder needs none: the coat's own shoulder covers the
      // joint, and the base of the arm is outlined where it meets the torso.
      if (shoulder === null && cut === null && !truthy(hands)) {
        parts.push(armJointCap(sk, sleeve as string, pivotX, pivotY, wTop));
      }
      parts.push(`<g transform="rotate(${fmt2(angle)} ${fmt1(pivotX)} ${fmt1(pivotY)})">` + limb.join("") + "</g>");
    } else {
      // No group, no cap: at the default 0 this is byte-identical to
      // drawing the limb straight into `parts`, which is deliberate so
      // every preset that never touches this knob renders unchanged.
      parts.push(...limb);
    }
  }
  return parts.join("");
}

/**
 * A band round the wrist, just above the hand, with optional text on it.
 *
 * Drawn inside `_arms`' limb, so it turns with a swung arm. Slightly wider at
 * the top than the bottom, as `_wrist_cuff` is, because the arm still tapers
 * across the band's own height. The text is a deeper tone of the band's colour,
 * centred, sized to the band's height and kept inside the arm's width.
 */
export function wristband(sk: Skeleton, p: CharacterParams, side: number, cx: number, wrist_y: number, w: number): string {
  const color = p.outfit.wristband_color;
  if (color === null || p.outfit.wristband_side !== side) return "";
  const r = sk.head_r;
  const sw = strokeW(sk);
  const h = r * 0.24;
  const y1 = wrist_y - r * 0.03;
  const y0 = y1 - h;
  const [topW, botW] = [w * 1.0, w * 0.97];
  const band =
    `<path d="M ${fmt1(cx - topW)} ${fmt1(y0)} L ${fmt1(cx + topW)} ${fmt1(y0)} ` +
    `L ${fmt1(cx + botW)} ${fmt1(y1)} L ${fmt1(cx - botW)} ${fmt1(y1)} Z" ` +
    `fill="${color}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw, 0.85))}" stroke-linejoin="round" />`;
  const text = p.outfit.wristband_text;
  if (!truthy(text) || isEmptyDict(text)) return band;
  const ink = shade(color, 0.3);
  // `len(text)` of a number is a `TypeError`; a list or a dict has a length, and `escape` then fails on it.
  if (typeof text !== "string") {
    if (numberOf(text) !== undefined) throw new PyError("TypeError", `object of type '${pyTypeName(text)}' has no len()`);
    throw new PyError("AttributeError", `'${Array.isArray(text) ? "list" : "dict"}' object has no attribute 'replace'`);
  }
  // `len(text)` counts code points; the text is never empty here, so the divisor is above zero.
  const size = pyMin(h * 0.66, pyDiv(2 * w * 0.92, 0.62 * [...text].length));
  return (
    band +
    `<text x="${fmt1(cx)}" y="${fmt1(y1 - h * 0.22)}" font-family="Helvetica, Arial, sans-serif" ` +
    `font-weight="bold" font-size="${fmt1(size)}" text-anchor="middle" fill="${ink}">${escape(text)}</text>`
  );
}

/**
 * Whether a traced coat is worn over the arms, so the hands have to be
 * drawn after it rather than with their arms. Keiko's reference draws her hand
 * over her lab coat, which the hand-shaped bite in the coat's traced crop
 * shows (`docs/bust-plan.md`, step 5b).
 */
export function handsAfterCoat(sk: Skeleton, p: CharacterParams): boolean {
  return tracedCoat(sk, p) && coatCut(p.outfit.coat_cut).over_arms;
}

/**
 * The shirt past a raised arm's coat sleeve: the arm's own tube again in the shirt's
 * colour from the sleeve's hem down to the wrist, and the hem across it, so the arm ends
 * the way the sleeve does at rest (`COAT_CUTS` `sleeve_hem_y`). Drawn inside the arm's
 * own turn, so it goes where the arm goes.
 */
export function raisedCuff(
  sk: Skeleton,
  p: CharacterParams,
  s: number,
  tube: string,
  shirt: string,
  elbow_x: number,
  wrist_x: number,
  w_elbow: number,
  w_wrist: number,
  wrist_y: number,
): string {
  const cut = coatCut(p.outfit.coat_cut);
  if (cut.sleeve_hem_y === null) throw new PyError("AssertionError", "");
  const hemY = sk.head_cy + garmentPlacement(sk, cut.ref_body)([0.0, cut.sleeve_hem_y])[1] * sk.head_r;
  const elbowY = sk.waist_y;
  const t = pyMin(1.0, pyMax(0.0, pyDiv(hemY - elbowY, wrist_y - elbowY)));
  const centre = elbow_x + (wrist_x - elbow_x) * t;
  const half = (w_elbow + (w_wrist - w_elbow) * t) * 1.03;
  const clipId = `sleeve-cuff-${s === -1 ? "l" : "r"}`;
  const sw = outlineW(strokeW(sk));
  return (
    `<defs><clipPath id="${clipId}"><rect x="${fmt1(wrist_x - sk.head_r * 3)}" y="${fmt1(hemY)}" ` +
    `width="${fmt1(sk.head_r * 6)}" height="${fmt1(sk.head_r * 2)}" /></clipPath></defs>` +
    `<path d="${tube}" fill="${shirt}" stroke="${OUTLINE}" stroke-width="${fmt2(sw)}" clip-path="url(#${clipId})" />` +
    `<path d="M ${fmt1(centre - half)} ${fmt1(hemY)} L ${fmt1(centre + half)} ${fmt1(hemY)}" fill="none" ` +
    `stroke="${OUTLINE}" stroke-width="${fmt2(sw)}" stroke-linecap="round" />`
  );
}

/**
 * Fills the wedge a swung arm opens at the shoulder.
 *
 * `_arms` draws the tube's flat top edge exactly on the sleeve hem, so
 * hanging straight the two read as one line, per that function's own
 * docstring. Rotating the tube about that edge's own centre point (the
 * pivot `right_arm_out`/`left_arm_out` swing around) carries its corners
 * away from the hem's fixed corners on an arc, opening a notch between
 * them. Both corners sit exactly `w_top` from the pivot regardless of
 * rotation, so a half-disc of that radius centred on the pivot always
 * reaches both and covers the wedge between them. Only the curved half is
 * drawn; the flat side lies on the hem line itself, on top of the hem's own
 * stroke, so it reads as that edge rather than as a seam of its own.
 */
export function armJointCap(sk: Skeleton, color: string, cx: number, cy: number, w_top: number): string {
  const r = w_top + strokeW(sk) * 0.5;
  return (
    `<path d="M ${fmt1(cx - r)} ${fmt1(cy)} A ${fmt1(r)} ${fmt1(r)} 0 0 0 ${fmt1(cx + r)} ${fmt1(cy)} Z" ` +
    `fill="${color}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`
  );
}

/**
 * The cuff on a coat's sleeve: one line across it, no second tone.
 *
 * The reference draws the cuff as a band of the same white as the sleeve, so
 * the only thing that shows is the line dividing them, 0.175 head radii above
 * the sleeve's end on a figure whose heights this project squashes by 0.9215
 * (`harness/keiko/trace_coat.py`). A filled band in a second tone is what
 * `_wrist_cuff` draws for an undersleeve showing past a short one, which is
 * the other garment and the other story: there the cuff is a different piece
 * of cloth, here it is the same piece turned back.
 *
 * Line work, so it is drawn thinner than the outline and with round caps, the
 * same as the placket's centre line.
 */
export function cuffLine(sk: Skeleton, cx: number, wrist_y: number, w: number): string {
  const y = wrist_y - sk.head_r * 0.161;
  const sw = strokeW(sk);
  return (
    `<line x1="${fmt1(cx - w)}" y1="${fmt1(y)}" x2="${fmt1(cx + w)}" y2="${fmt1(y)}" ` +
    `stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.7))}" stroke-linecap="round" />`
  );
}

/**
 * A band closing the undersleeve at the wrist.
 *
 * Small element, so it takes the second tone: this is the pouch-flap and
 * boot-cuff case the flat-colour rule leaves open, a turn of cloth reading as
 * thickness, not a plane across a panel.
 *
 * Satoko's canon undersleeves end in one of these and Satoshi's are rolled at
 * the forearm instead, with a thicker cuff, two roll lines and bare arm below.
 * Only this one is drawn: the roll belongs to the satoshi references, which
 * drive his haircut and nothing else about his design (the owner's call,
 * 2026-08-07). Drawn only when there is an undersleeve, since a cuff on a bare
 * arm is a bracelet.
 */
export function wristCuff(sk: Skeleton, color: string, cx: number, wrist_y: number, w: number): string {
  const h = w * 0.55;
  // The arm still tapers across the band's own height, so the top is a shade
  // wider than the bottom. Without that the cuff reads as pasted on.
  const topW = w * 1.05;
  return (
    `<path d="M ${fmt1(cx - topW)} ${fmt1(wrist_y - h)} L ${fmt1(cx + topW)} ${fmt1(wrist_y - h)} ` +
    `L ${fmt1(cx + w)} ${fmt1(wrist_y)} L ${fmt1(cx - w)} ${fmt1(wrist_y)} Z" ` +
    `fill="${shade(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(strokeW(sk), 0.85))}" />`
  );
}

