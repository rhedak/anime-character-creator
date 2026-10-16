// The body's upper half: the torso, the bare breasts and the underwear top, the chest lines and the navel, the bust drawn over the
// arms, and a kimono's hanging sleeves. Port of the `parts-body` module of character.py (see `harness/ts_port/modules.json`); the
// legs, skirts and boots are in `body-parts-legs.ts`. Names are the Python ones in camelCase and every expression keeps Python's
// evaluation order. Numbers reach the text only through the `fmt*` kernel functions.

import { OUTLINE, bareShoulderSk, bodyInset, interiorW, outlineW, strokeW } from "./character.ts";
import {
  BREAST_STOP,
  SLEEVE_CUT_ID,
  armLine,
  armpitX,
  breastEllipse,
  bustFold,
  bustShape,
  capTipY,
  capUndersideY,
  legGapAndTop,
  raisedCoatSleeve,
  rib as ribRun,
  shoulderSlope,
  sleeveHalfW,
  sleeveHemY,
  sleeveUnderCap,
  torsoAtArmpit,
} from "./core-limbs.ts";
import { arms } from "./core-limbs-arms.ts";
import { colorStr, crotchY } from "./body-parts-legs.ts";
import type { CharacterParams } from "./params.ts";
import {
  PyError,
  argMax,
  at,
  fmt0,
  fmt1,
  fmt2,
  pyCos,
  pyHypot,
  pyMax,
  pyMin,
  pyPow,
  pyReplace,
  pySin,
  radians,
  truthy,
} from "./pynum.ts";
import { sha1Hex } from "./sha1.ts";
import { bustY, replace } from "./skeleton.ts";
import type { Skeleton } from "./skeleton.ts";
import type { Point } from "./tables.ts";

/** `"x y"` of `(cx + s * x, y)` as the bare body's polylines write it, `:.1f` each. */
const xy = (cx: number, s: number, x: number, y: number): string => `${fmt1(cx + s * x)} ${fmt1(y)}`;

/**
 * `body` with every id it defines, and every reference to one of those, under `prefix`; ids
 * it only points at (defined elsewhere in the document) are left alone. For drawing a layer a
 * second time without defining its masks and clips a second time.
 */
export function redefineIds(body: string, prefix: string): string {
  // `\b` is Python's (Unicode word) boundary, as `namespaceIds` has it; `dict.fromkeys` is the distinct names in first-seen order.
  const names = new Set<string>();
  for (const m of body.matchAll(/(?<![\p{L}\p{N}_])id="([^"]+)"/gu)) names.add(m[1] as string);
  for (const name of names) {
    body = pyReplace(body, `id="${name}"`, `id="${prefix}-${name}"`);
    body = pyReplace(body, `url(#${name})`, `url(#${prefix}-${name})`);
    body = pyReplace(body, `href="#${name}"`, `href="#${prefix}-${name}"`);
  }
  return body;
}

/**
 * The bust in front of the arms: `chest`, the layers worn on the torso up
 * to the arms, drawn again masked to the lobe a bust adds to the torso, then
 * the bust's outline over it. Nothing without a bust.
 *
 * A bust stands forward of the arm hanging beside it, and the torso's side
 * does not: so only the lobe comes over the arm, and whatever is worn there
 * comes with it in its own colour and line work (a tunic, a coat's panel, a
 * strap), since it is those same layers drawn again. At the chibi the arm's
 * inner edge runs along the torso's side, and drawn under the arm the whole
 * bust was hidden: at the realistic build it moved no pixel at all
 * (`docs/bust-status.md`, step 2).
 *
 * The lobe also runs a stroke inside the plain side, so the arm's own
 * outline, which lies along it at the chibi, is covered rather than left as a
 * line through the bust.
 *
 * The outline is drawn only where it lies over an arm, clipped to the arms'
 * own shapes, so it leaves the arm's inner edge, crosses the sleeve and joins
 * it again: the bust overlapping the arm. Everywhere else the garment's own
 * outline is already there. Drawn whole, on a coat the colour of its sleeve
 * it read as a bracket floating in the middle of the white; that and a coat
 * worn over the arms (step 5b, reversed) were two halves of what the owner
 * asked for, the arm in front of the coat and behind the bust
 * (`docs/bust-plan.md`, step 5c).
 *
 * At the realistic build, now retired, the arm hung across the torso and the
 * lobe could not work there (`docs/bust-status.md`, step 5); the tall chibi
 * is the one figure (`docs/tall-chibi-plan.md`).
 *
 * The mask's id carries a hash of its shape, so figures sharing one document
 * (a cast sheet) cannot pick up each other's.
 *
 * With no tunic the chest is masked to the breasts instead (`_bare_breasts`,
 * which the chest then holds in the tunic's line's place), outline and all:
 * they carry their own, so nothing is clipped to the arms.
 */
export function bustOverArms(sk: Skeleton, p: CharacterParams, chest: string): string {
  const bust = bustShape(sk, 0.0, true);
  if (bust === null) return "";
  // The same layers a second time: what they define (a coat's panel mask) goes under another name.
  chest = redefineIds(chest, "again");
  const cx = sk.head_cx;
  const sw = strokeW(sk);
  if (p.outfit.tunic_color === null) {
    const d = [-1, 1]
      .map((s) => "M " + bareBreastSpine(sk, p).map(([x, y]) => xy(cx, s, x, y)).join(" L ") + " Z")
      .join(" ");
    const maskId = "breasts-" + sha1Hex(d).slice(0, 10);
    // Stroked as well as filled, so the outline's outer half is inside it.
    return (
      `<defs><mask id="${maskId}" maskUnits="userSpaceOnUse" x="0" y="0" ` +
      `width="${fmt0(sk.canvas_w)}" height="${fmt0(sk.canvas_h)}">` +
      `<path d="${d}" fill="white" stroke="white" stroke-width="${fmt1(sw * 1.5)}" ` +
      `stroke-linejoin="round" /></mask></defs>` +
      `<g mask="url(#${maskId})">${chest}</g>`
    );
  }
  const b = bust;
  const plain: Point = [torsoAtArmpit(sk), b.armpit[1]];
  const lobe: string[] = [];
  const outline: string[] = [];
  for (const s of [-1, 1]) {
    const pt = (v: Point, dx = 0.0): string => `${fmt1(cx + s * (v[0] + dx))} ${fmt1(v[1])}`;

    const run = b.outline.slice(0, b.lobe_pieces);
    const edge = `M ${pt(b.armpit)} ` + run.map(([c, e]) => `Q ${pt(c)} ${pt(e)} `).join("");
    const end = at(run, -1)[1];
    outline.push(edge);
    // Closed back up the plain side to the plain armpit, not the bust's
    // (`_armpit_x`): that one is carried out past the arm's inner edge, and a
    // lobe closing there left the top of that edge half covered, a grey
    // smear under the armpit.
    lobe.push(edge + `L ${pt(end, -sw)} Q ${pt(b.plain_up, -sw)} ${pt(plain, -sw)} Z`);
  }
  const d = lobe.join(" ");
  const maskId = "bust-" + sha1Hex(d).slice(0, 10);
  // A mask rather than a clip path: a clip is applied to each layer in turn,
  // so along its soft edge every layer under the top one bleeds through, and a
  // dark tunic under a white coat showed as a grey seam down the bust. A mask
  // cuts out the chest once it is composited.
  const armsText = arms(sk, p, null, true);
  const clipId = "bust-arms-" + sha1Hex(d + armsText).slice(0, 10);
  return (
    `<defs><mask id="${maskId}" maskUnits="userSpaceOnUse" x="0" y="0" ` +
    `width="${fmt0(sk.canvas_w)}" height="${fmt0(sk.canvas_h)}">` +
    `<path d="${d}" fill="white" /></mask>` +
    `<clipPath id="${clipId}">${armsText}</clipPath></defs>` +
    `<g mask="url(#${maskId})">${chest}</g>` +
    `<path d="${outline.join(" ")}" fill="none" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(outlineW(sw))}" stroke-linecap="round" clip-path="url(#${clipId})" />`
  );
}

/**
 * The curve under each breast, the front-view cue a bust reads by.
 *
 * Seen from the front, the side outline says little: at the chibi it is half
 * under the arm and on some characters under their hair. What reads is the
 * underside (the anatomy review in `docs/bust-plan.md`, step 4). Each side's
 * curve starts on the tunic's own side outline at the fullest point, runs
 * round the bottom of the breast and up its inner side toward the sternum,
 * on the bare breast's own ellipse (`_breast_ellipse`). Starting on the
 * outline is the owner's "matching the width": a short arc centred under the
 * breast floated inside the silhouette.
 *
 * Drawn as a thin filled shape rather than a stroke, tapering at both ends,
 * so it varies in weight the way a drawn line does and melts into the
 * outline it leaves. Flat and hard-edged: line work, not a tone
 * (`CLAUDE.md`). Its weight grows with the bust up to 0.5, so it fades in
 * rather than appearing whole.
 *
 * Drawn right after the tunic: an outer layer, a coat or a robe front, hangs
 * over the bust and covers it, its own outline being the cue there. With no
 * tunic this is a fold with nothing to fold, and the breasts are drawn whole
 * in its place (`_bare_breasts`).
 */
export function bustLines(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.tunic_color === null) return bareBreasts(sk, p);
  return bustFold(sk);
}

/**
 * One breast's outline with nothing worn, as offsets from the centre line:
 * from the arm's inner top corner down and a little out to the widest point,
 * then round an ellipse's outside and bottom and up its inner side. Empty
 * without a bust.
 *
 * Its own shape rather than the torso's side bent out and brought back in an
 * S (`_bust_shape`), which is right for cloth, the silhouette, but bare dented
 * where the S returned and left the armpit at a point: a breast is a round
 * form lying on the chest and over the side. Sized from the bust's anchors:
 * widest at the fullest point, reaching `bust_reach` past the plain side
 * there, dropping the fold's depth times `_BREAST_DEPTH`.
 *
 * It starts at the arm's own top corner, as `_arms` draws it, so arm top,
 * armpit and breast are one line; the shared armpit point sat a few pixels
 * off it, and a line fading in below the armpit left two ends side by side.
 * It arrives at the widest point vertical: joined lower on the ellipse, the
 * ellipse there lay inside the armpit and the curve wiggled in and out.
 */
export function bareBreastSpine(sk: Skeleton, p: CharacterParams): Point[] {
  const body = bareShoulderSk(sk, p);
  const ribSk = ribSkeleton(body);
  // Her reach is a couple of pixels, so the top was a band. The cast's own
  // breast drops about 0.14 of a head; give a tucked rib that much to read by.
  const minRy = ribSk !== body ? sk.head_r * 0.16 : 0.0;
  const ellipse = breastEllipse(ribSk, bodyInset(sk, p), minRy);
  if (ellipse === null) return [];
  const [xc, rx, yp, ryDown] = ellipse;
  const xOut = xc + rx;
  const [centreTop, topY] = armLine(body);
  const ax = centreTop - sk.arm_half_w;
  const ay = sleeveUnderCap(sk, p) ? capUndersideY(sk, ax, capTipY(sk)) : topY;
  const ctrl: Point = [xOut, ay + (yp - ay) * 0.5];
  const spine: Point[] = [];
  for (let k = 0; k < 12; k++) {
    // `(1 - u) ** 2` is the exact product, as C's `pow(x, 2.0)` is (the `x ** 2` rule of the guide).
    const u = k / 12;
    spine.push([
      (1 - u) * (1 - u) * ax + 2 * (1 - u) * u * ctrl[0] + u * u * xOut,
      (1 - u) * (1 - u) * ay + 2 * (1 - u) * u * ctrl[1] + u * u * yp,
    ]);
  }
  const stop = radians(BREAST_STOP);
  const steps = 48;
  for (let k = 0; k <= steps; k++) {
    const th = (stop * k) / steps;
    spine.push([xc + rx * pyCos(th), yp + ryDown * pySin(th)]);
  }
  return spine;
}

/**
 * Both breasts with nothing worn over them: each filled in the skin tone,
 * closed by a chord across the chest, so the arm's inner edge and the torso's
 * side stop at the outline, the usual way one form is drawn over another; and
 * outlined at full weight from the armpit round the outside and the bottom,
 * tapering up the inner side toward the sternum. The weight fades in with the
 * bust up to 0.2, so a very small one is not a line appearing whole.
 *
 * Drawn in the chest where the tunic's line under the bust goes, so a strap
 * or a belt worn over bare skin lies over it; at the chibi `_bust_over_arms`
 * draws it again over the arms.
 */
export function bareBreasts(sk: Skeleton, p: CharacterParams): string {
  const spine = bareBreastSpine(sk, p);
  if (spine.length === 0) return "";
  const cx = sk.head_cx;
  const sw = strokeW(sk);
  const heaviest = outlineW(sw * pyMin(1.0, sk.bust / 0.2));
  const n = spine.length - 1;
  const left: Point[] = [];
  const right: Point[] = [];
  spine.forEach(([x, y], k) => {
    const a0 = spine[pyMax(0, k - 1)] as Point;
    const a1 = spine[pyMin(n, k + 1)] as Point;
    const [dx, dy] = [a1[0] - a0[0], a1[1] - a0[1]];
    // `math.hypot(dx, dy) or 1.0`: so the divisions below never see a zero.
    const hyp = pyHypot(dx, dy);
    const norm = truthy(hyp) ? hyp : 1.0;
    // `n` is at least 60 here (the spine is 61 points), so `k / n` cannot divide by zero.
    const half = heaviest * 0.5 * pyPow(pyMin(1.0, (1.0 - k / n) / 0.3), 0.8);
    const [nx, ny] = [(-dy / norm) * half, (dx / norm) * half];
    left.push([x + nx, y + ny]);
    right.push([x - nx, y - ny]);
  });
  const ring: Point[] = [...left, ...right.slice().reverse()];
  const parts: string[] = [];
  for (const s of [-1, 1]) {
    const fill = "M " + spine.map(([x, y]) => xy(cx, s, x, y)).join(" L ") + " Z";
    const line = "M " + ring.map(([x, y]) => xy(cx, s, x, y)).join(" L ") + " Z";
    const [x0, y0] = spine[0] as Point;
    parts.push(
      `<path d="${fill}" fill="${colorStr(p.skin_tone)}" stroke="none" />` +
        `<path d="${line}" fill="${OUTLINE}" stroke="none" />` +
        `<circle cx="${fmt1(cx + s * x0)}" cy="${fmt1(y0)}" r="${fmt2(heaviest * 0.5)}" fill="${OUTLINE}" />`,
    );
  }
  return parts.join("");
}

/**
 * The base layer's top, drawn only with the tunic off, so no clothed
 * figure can move (`docs/bare-body-plan.md`, step 3).
 *
 * A plain band in `underwear_color`: down each breast's outer outline from
 * the armpit to its lowest point (`_bare_breast_spine`, so it sits on the
 * bare shape at any bust and comes over the arms with it at the chibi),
 * straight across under both, and closed by a shallow dip from armpit to
 * armpit. A thin line along each breast's inner lower curve says two cups
 * rather than a tube. Without a bust, and only when `underwear_top` asks
 * for one, a flat band inside the torso's side instead.
 */
export function underwearTop(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.tunic_color !== null) return "";
  const spine = bareBreastSpine(sk, p);
  if (spine.length === 0 && !truthy(p.outfit.underwear_top)) return "";
  const cx = sk.head_cx;
  const sw = strokeW(sk);
  const color = p.outfit.underwear_color;
  if (spine.length === 0) {
    const body = bareShoulderSk(sk, p);
    const side = torsoAtArmpit(sk) - sw;
    const top = sleeveHemY(body);
    // `sk.bust_y` is a property in Python: `bustY(sk)`.
    const bottom = bustY(sk) + (sk.waist_y - sk.shoulder_y) * 0.15;
    const dip = (bottom - top) * 0.3;
    const d =
      `M ${fmt1(cx - side)} ${fmt1(top)} L ${fmt1(cx - side)} ${fmt1(bottom)} ` +
      `L ${fmt1(cx + side)} ${fmt1(bottom)} L ${fmt1(cx + side)} ${fmt1(top)} ` +
      `Q ${fmt1(cx)} ${fmt1(top + dip)} ${fmt1(cx - side)} ${fmt1(top)} Z`;
    return (
      `<path d="${d}" fill="${colorStr(color)}" stroke="${OUTLINE}" ` +
      `stroke-width="${fmt2(outlineW(sw))}" stroke-linejoin="round" />`
    );
  }
  // `max(range(len(spine)), key=lambda k: spine[k][1])`: the first lowest point.
  const low = argMax(spine.map((q) => q[1]));
  const outer = spine.slice(0, low + 1);
  const inner = spine.slice(low);
  const [ax, ay] = spine[0] as Point;
  const peakBust = bustShape(ribSkeleton(bareShoulderSk(sk, p)), bodyInset(sk, p));
  if (peakBust === null) throw new PyError("AttributeError", "'NoneType' object has no attribute 'peak'");
  const yp = peakBust.peak[1];
  const left = outer.map(([x, y]) => `${fmt1(cx - x)} ${fmt1(y)}`).join(" L ");
  const right = outer
    .slice()
    .reverse()
    .map(([x, y]) => `${fmt1(cx + x)} ${fmt1(y)}`)
    .join(" L ");
  const d = `M ${left} L ${right} Q ${fmt1(cx)} ${fmt1(ay + (yp - ay) * 0.6)} ${fmt1(cx - ax)} ${fmt1(ay)} Z`;
  const cups = [-1, 1].map((s) => "M " + inner.map(([x, y]) => xy(cx, s, x, y)).join(" L ")).join(" ");
  return (
    `<path d="${d}" fill="${colorStr(color)}" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(outlineW(sw))}" stroke-linejoin="round" />` +
    `<path d="${cups}" fill="none" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(interiorW(sw, 0.6))}" stroke-linecap="round" />`
  );
}

/**
 * Two soft arcs under the pectorals, with the tunic off and no bust
 * (`docs/bare-body-plan.md`, step 6; `harness/bare/male_torso.py` is the
 * study). At the chibi a man's bare silhouette is the women's exactly:
 * `frame` rides the build and moves a width by well under a percent there,
 * and the body profile sets the waist and hip itself. So the chest is line
 * work, as the bust was at the chibi.
 *
 * At the canon's half way from the shoulder line to the waist, each from
 * near the torso's side to a gap at the sternum, tapering at both ends, the
 * way a muscle's border is drawn rather than an edge; `chest` scales the
 * depth and the weight.
 */
export function chestLines(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.tunic_color !== null || sk.bust > 0 || p.chest <= 0) return "";
  const amount = pyMin(1.0, p.chest);
  const cx = sk.head_cx;
  const sw = strokeW(sk);
  const side = torsoAtArmpit(sk);
  const run = sk.waist_y - sk.shoulder_y;
  const depth = run * 0.07 * (0.6 + 0.4 * amount);
  const [xOut, xIn] = [side * 0.92, side * 0.1];
  const [xc, rx] = [(xOut + xIn) / 2, (xOut - xIn) / 2];
  const yc = sk.shoulder_y + run * 0.5 - depth;
  const heaviest = outlineW(sw * 0.8 * (0.5 + 0.5 * amount));
  const [a0, a1, steps] = [radians(15), radians(165), 28];
  const spine: Point[] = [];
  for (let k = 0; k <= steps; k++) {
    const th = a0 + ((a1 - a0) * k) / steps;
    spine.push([xc + rx * pyCos(th), yc + depth * pySin(th)]);
  }
  const n = spine.length - 1;
  const left: Point[] = [];
  const right: Point[] = [];
  spine.forEach(([x, y], k) => {
    const q0 = spine[pyMax(0, k - 1)] as Point;
    const q1 = spine[pyMin(n, k + 1)] as Point;
    const [dx, dy] = [q1[0] - q0[0], q1[1] - q0[1]];
    const hyp = pyHypot(dx, dy);
    const norm = truthy(hyp) ? hyp : 1.0;
    // `n` is 28 here, so `k / n` cannot divide by zero.
    const half = heaviest * 0.5 * pyPow(pySin((Math.PI * k) / n), 0.7);
    const [nx, ny] = [(-dy / norm) * half, (dx / norm) * half];
    left.push([x + nx, y + ny]);
    right.push([x - nx, y - ny]);
  });
  const ring: Point[] = [...left, ...right.slice().reverse()];
  return [-1, 1]
    .map((s) => '<path d="M ' + ring.map(([x, y]) => xy(cx, s, x, y)).join(" L ") + ` Z" fill="${OUTLINE}" stroke="none" />`)
    .join("");
}

/**
 * A small upright dot on every bare figure, a little below the waist:
 * without it a bare torso read as a blank block rather than skin
 * (`docs/bare-body-plan.md`, step 6). Only with the tunic off.
 */
export function navel(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.tunic_color !== null) return "";
  const sw = strokeW(sk);
  const y = sk.waist_y + (sk.hip_y - sk.waist_y) * 0.15;
  return (
    `<ellipse cx="${fmt1(sk.head_cx)}" cy="${fmt1(y)}" rx="${fmt2(sw * 0.45)}" ry="${fmt2(sw * 0.7)}" ` +
    `fill="${OUTLINE}" />`
  );
}

// How far inside the hip a bare waist sits, when the measured waist is wider
// than the hips. The side still runs back out to the leg, so the briefs meet it.
export const BARE_WAIST_OF_HIP = 0.82;

/**
 * The skeleton a bare rib reads, when the measured waist is wider than the hips.
 *
 * Risa's waist was never measured: a blazer covers it, and the guess sits wider
 * than the legs, so bare she is a tube and the top has nothing to tuck into.
 * The waist comes in to just inside the hip the legs already draw. The armpit
 * stays on the arm: a narrower waist would pull it in with the usual blend and
 * open a gap beside the arm. The shoulder that blend needs is only for the rib.
 * The shoulder line, the arm and every clothed cut keep the measured waist.
 */
export function ribSkeleton(sk: Skeleton): Skeleton {
  const [gap, wTop] = legGapAndTop(sk, false);
  const hip = gap + wTop;
  if (sk.waist_half_w <= hip) return sk;
  const waist = hip * BARE_WAIST_OF_HIP;
  const [centreTop] = armLine(sk);
  const armpit = centreTop - sk.arm_half_w;
  // `_torso_at_armpit` is `waist + (shoulder - waist) * 0.12`. Solve the
  // shoulder that puts the armpit on the arm at this waist.
  const shoulder = waist + (armpit - waist) / 0.12;
  return replace(sk, { waist_half_w: waist, shoulder_half_w: shoulder });
}

/**
 * The body from the shoulders to the hip, in the skin tone.
 *
 * Built from the skeleton alone and reading no garment: every garment is drawn
 * over it and has to cover it, which `refresh-ref-out.sh --pixels` checks
 * (`docs/bust-plan.md`, step 3). Before this there was no torso at all, only
 * the tunic, so a bust had nowhere to live but on a garment.
 *
 * The tunic's plain side, from the same helpers, but with the shoulder the
 * arm's own: out to the arm's outer edge where it leaves the body, then down
 * the diagonal to the armpit that the arm's top edge follows. A shoulder out to
 * the sleeve's width showed past the slanted cap at the adult build.
 *
 * The whole outline sits `_body_inset` inside the garment's. A body
 * edge on a garment's edge draws the outline twice, and the second pass
 * darkens the antialiased rim of the first along every shared edge, so the
 * body has to be under the garment's fill, not its stroke. Its top is closed
 * straight across the neck, and drawn before the neck, whose skin runs down
 * past the shoulder line and covers it, so no outline shows in a neckline.
 */
export function torso(sk: Skeleton, p: CharacterParams): string {
  const k = bodyInset(sk, p);
  // Bare, and only then: the rib tucks where the measured waist is the
  // garment's, and the shoulder rises off a blazer's line. Clothed, `sk`
  // itself, so the shirt and the coat do not move.
  const body = bareShoulderSk(sk, p);
  const ribSk = p.outfit.tunic_color === null ? ribSkeleton(body) : sk;
  const cx = sk.head_cx;
  const nw = sk.neck_half_w;
  // Twice the inset along the shoulder: it slopes, and an inset measured
  // straight down is less than the same inset measured square to the line.
  const sy = body.shoulder_y + 2 * k;
  const [centreTop0] = armLine(body);
  const tip = centreTop0 + body.arm_half_w - k;
  const slope = shoulderSlope(body);
  const cuffY = sleeveHemY(body);
  const tac = armpitX(ribSk, k);
  const ww = ribSk.waist_half_w - k;
  const wy = sk.waist_y;
  // The shoulder rounds over the top of the arm and down to where the arm
  // starts, a quarter round from its tip to half way back to the armpit,
  // the way a flat sleeve's shoulder does. It first cut straight from the tip
  // to the armpit along a slanted sleeve's underside, which bare left a wedge
  // of page between shoulder and arm (`docs/bust-plan.md`, step 3c). Under a
  // slanted sleeve the arm's own top covers what this adds.
  const rim = tip - (tip - tac) * 0.5;
  // The underside lies on the line the arm starts at, where the arm's own top
  // edge covers it, so a bare arm shows one line there and not two. Only in
  // the gap between the torso's side and the arm's inner edge, which nothing
  // covers below that line, does it step up an inset, under the tunic's sleeve.
  const [centreTop] = armLine(sk);
  const armIn = centreTop - sk.arm_half_w + k;
  // Bare, the arm has no top edge to cover that line (`_arms`), and a stroke
  // there showed its upper half across the top of the arm: the underside
  // drops inside the arm instead, where the arm's fill covers it, and only
  // the gap at the armpit stays on the line (`docs/bare-body-plan.md`, 4c).
  const bare = p.outfit.tunic_color === null;
  const underY = bare ? cuffY + strokeW(sk) * 1.5 : cuffY;
  // `under_down` and `under_up` are `str.format` templates in Python, filled once the x values are known; here they are
  // functions of those values.
  let underDown: (xTac: string, xIn: string) => string;
  let underUp: (xTac: string, xIn: string, xRim: string) => string;
  if (bare) {
    // Level inside the arm to its inner edge, up that edge to the arm's
    // top, and across the gap to the torso's side at the armpit. Rising
    // on the diagonal it met the arm's top mid-stroke, and half the stroke
    // showed as a nub there.
    const edgeIsIn = tac < armIn;
    underDown = (xTac, xIn) => {
      const xEdge = edgeIsIn ? xIn : xTac;
      return `L ${xEdge} ${fmt1(underY)} L ${xEdge} ${fmt1(cuffY)} L ${xTac} ${fmt1(cuffY)} `;
    };
    underUp = (xTac, xIn, xRim) => {
      const xEdge = edgeIsIn ? xIn : xTac;
      return `L ${xTac} ${fmt1(cuffY)} L ${xEdge} ${fmt1(cuffY)} L ${xEdge} ${fmt1(underY)} ` + `L ${xRim} ${fmt1(underY)} `;
    };
  } else if (tac >= armIn) {
    underDown = (xTac) => `L ${xTac} ${fmt1(cuffY)} `;
    underUp = (_xTac, _xIn, xRim) => `L ${xRim} ${fmt1(underY)} `;
  } else {
    underDown = (xTac, xIn) => `L ${xIn} ${fmt1(cuffY)} L ${xIn} ${fmt1(cuffY - k)} L ${xTac} ${fmt1(cuffY - k)} `;
    underUp = (xTac, xIn, xRim) =>
      `L ${xTac} ${fmt1(cuffY - k)} L ${xIn} ${fmt1(cuffY - k)} L ${xIn} ${fmt1(cuffY)} ` + `L ${xRim} ${fmt1(underY)} `;
  }
  // The tip rounded, as the tunic's slanted sleeve rounds its own: the slope
  // arrives nearly level and the side leaves straight down, and met at a point
  // they read as a shoulder pad's corner.
  //
  // Bare, the inset is zero and the corner was square: the shoulder rounds
  // over the top of the arm instead, by most of the arm's width, the way a
  // bare shoulder caps the arm below it.
  const roundR = bare
    ? pyMin(sk.arm_half_w * 0.9, (cuffY - (sy + slope)) * 0.6)
    : pyMin(k * 2.0, (cuffY - (sy + slope)) * 0.4);
  const tipY = sy + slope;
  // The torso narrows to the bare seat's width and runs down to the hip, a
  // stroke past it, under the seat drawn after it. Below that the body is the
  // legs' (`_bare_seat`, `_seat_notch_d`): at the chibi they are a straight
  // column at leg width, narrower than `hip_half_w`, and a torso carried down
  // at that width showed beside the trousers of every figure that wears them.
  // It first stopped in the belt band, where a tucked tunic ends and the seat
  // starts; but an untucked figure's seat starts at the hip, and the page
  // showed between the two (`docs/bust-plan.md`, step 3c).
  const [gap, wTop] = legGapAndTop(sk, false);
  const seat = gap + wTop - k;
  // Wider than the legs, the torso would show beside them. Where the waist
  // was tucked in, the side runs back out to the leg so it meets the briefs.
  const hw = ribSk !== sk ? seat : pyMin(ww, seat);
  const hy = sk.hip_y + strokeW(sk);
  // Where the legs part, the bottom edge rises into a small V to a stroke above
  // the crotch: on the long-torso chibi the crotch sits above the hip anchor,
  // and a straight edge at the hip showed in the notch between the legs of
  // every figure whose legs part there.
  const crotch = crotchY(sk, p);
  const notchW = strokeW(sk) * 2.0;
  const notchY = pyMin(hy, crotch - strokeW(sk));
  const hipCtrlY = hy - (hy - wy) * 0.45;
  const d =
    `M ${fmt1(cx - nw)} ${fmt1(sy)} ` +
    `Q ${fmt1(cx - tip * 0.5)} ${fmt1(sy + slope * 0.62)} ${fmt1(cx - tip + roundR)} ${fmt1(tipY - roundR * 0.3)} ` +
    `Q ${fmt1(cx - tip)} ${fmt1(tipY)} ${fmt1(cx - tip)} ${fmt1(tipY + roundR)} ` +
    (bare
      ? `L ${fmt1(cx - tip)} ${fmt1(underY)} L ${fmt1(cx - rim)} ${fmt1(underY)} `
      : `Q ${fmt1(cx - tip)} ${fmt1(underY)} ${fmt1(cx - rim)} ${fmt1(underY)} `) +
    underDown(fmt1(cx - tac), fmt1(cx - armIn)) +
    ribRun(ribSk, cx, -1, true, k) +
    `Q ${fmt1(cx - hw)} ${fmt1(hipCtrlY)} ${fmt1(cx - hw)} ${fmt1(hy)} ` +
    `L ${fmt1(cx - notchW)} ${fmt1(hy)} L ${fmt1(cx)} ${fmt1(notchY)} L ${fmt1(cx + notchW)} ${fmt1(hy)} ` +
    `L ${fmt1(cx + hw)} ${fmt1(hy)} ` +
    `Q ${fmt1(cx + hw)} ${fmt1(hipCtrlY)} ${fmt1(cx + ww)} ${fmt1(wy)} ` +
    ribRun(ribSk, cx, 1, false, k) +
    underUp(fmt1(cx + tac), fmt1(cx + armIn), fmt1(cx + rim)) +
    (bare
      ? `L ${fmt1(cx + tip)} ${fmt1(underY)} L ${fmt1(cx + tip)} ${fmt1(tipY + roundR)} `
      : `Q ${fmt1(cx + tip)} ${fmt1(underY)} ${fmt1(cx + tip)} ${fmt1(tipY + roundR)} `) +
    `Q ${fmt1(cx + tip)} ${fmt1(tipY)} ${fmt1(cx + tip - roundR)} ${fmt1(tipY - roundR * 0.3)} ` +
    `Q ${fmt1(cx + tip * 0.62)} ${fmt1(sy + slope * 0.3)} ${fmt1(cx + nw)} ${fmt1(sy)} Z`;
  return (
    `<path d="${d}" fill="${colorStr(p.skin_tone)}" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(outlineW(strokeW(sk)))}" />`
  );
}

/**
 * `layer` clipped like the coat is: the body's shoulder under a raised arm's sleeve would
 * show once the sleeve is gone (`_sleeve_cutaway` makes the clip path).
 */
export function withoutRaisedSleeves(layer: string, p: CharacterParams): string {
  if (!(raisedCoatSleeve(p, -1) || raisedCoatSleeve(p, 1))) return layer;
  return `<g clip-path="url(#${SLEEVE_CUT_ID})">${layer}</g>`;
}

/**
 * The bag of cloth a kimono sleeve is, hanging off the shoulder.
 *
 * Not a tube on an arm. `_arms` draws a limb and a sleeve that follows it,
 * which is right for every other garment here and wrong for this one: a
 * furisode hangs straight down from the shoulder seam and the arm inside it is
 * somewhere else entirely. So this is its own shape, drawn behind the arms, and
 * the arm carries on being drawn over it.
 *
 * Squared off at the bottom with a rounded outer corner, which is the shape,
 * and hanging from the tunic's own sleeve line so the two share an edge instead
 * of stacking two outlines at the shoulder.
 */
export function hangingSleeves(sk: Skeleton, p: CharacterParams): string {
  const drop = pyMax(0.0, pyMin(1.0, p.outfit.sleeve_drop));
  if (drop <= 0.0 || p.outfit.robe_color === null) return "";
  const cx = sk.head_cx;
  const color = p.outfit.robe_color;
  const sw = strokeW(sk);
  const top = sleeveHemY(sk);
  const hem = top + (sk.hip_y - sk.shoulder_y) * drop;
  const outer = sleeveHalfW(sk) * 1.02;
  const inner = sk.waist_half_w * 0.98;
  const r = (outer - inner) * 0.35;
  const parts: string[] = [];
  for (const s of [-1, 1]) {
    const d =
      `M ${fmt1(cx + s * inner)} ${fmt1(top)} ` +
      `L ${fmt1(cx + s * outer)} ${fmt1(top)} ` +
      `L ${fmt1(cx + s * outer)} ${fmt1(hem - r)} ` +
      `Q ${fmt1(cx + s * outer)} ${fmt1(hem)} ${fmt1(cx + s * (outer - r))} ${fmt1(hem)} ` +
      `L ${fmt1(cx + s * inner)} ${fmt1(hem)} ` +
      `Z`;
    parts.push(`<path d="${d}" fill="${colorStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`);
  }
  return parts.join("");
}
