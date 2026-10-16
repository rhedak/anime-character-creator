// Proportion anchors the character is built around.
//
// Everything downstream (hair, clothes, limbs) positions itself relative to these points instead of using hardcoded
// coordinates, so changing the proportions here doesn't require touching every shape. The whole figure derives from
// one number, `heads`: how many head-heights tall it stands. Vertical anchors are fractions of the body (chin to
// floor), so they keep their relationship at any height, while widths interpolate between builds.
//
// Port of skeleton.py. Field names stay snake_case so a skeleton dumped from Python loads as it is.

import { BadValue, pyDiv, pyMax, pyMin } from "./pynum.ts";

export const BUILDS: Readonly<Record<string, number>> = { chibi: 2.4 };
export const DEFAULT_BUILD = "chibi";
export const DEFAULT_HEADS = BUILDS[DEFAULT_BUILD] as number;

const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;

export interface Skeleton {
  readonly canvas_w: number;
  readonly canvas_h: number;
  readonly heads: number;
  /** How far along the chibi-to-adult range this build sits: 0 at a 2-head chibi, 1 at the 6-head adult. */
  readonly build: number;
  readonly head_cx: number;
  readonly head_cy: number;
  readonly head_r: number;
  readonly neck_y: number;
  readonly neck_half_w: number;
  readonly shoulder_y: number;
  readonly shoulder_half_w: number;
  readonly waist_y: number;
  readonly waist_half_w: number;
  readonly hip_y: number;
  readonly hip_half_w: number;
  readonly hem_y: number;
  readonly hem_half_w: number;
  readonly arm_half_w: number;
  readonly arm_x: number;
  readonly leg_half_w: number;
  readonly knee_y: number;
  readonly boot_y: number;
  readonly ankle_y: number;
  readonly foot_y: number;
  /** How much bust the figure carries, 0 for none. Only the knob is stored. */
  readonly bust: number;
  /** How grown-up the face reads, 0 to 1. */
  readonly face_maturity: number;
  /** How far along the retired adult build's limb taper the arms and legs are drawn, 0 to 1. */
  readonly limb_taper: number;
  readonly wrist_y: number | null;
  readonly wrist_x: number | null;
}

const BUST_ALONG = 0.15;
const BUST_REACH: readonly [number, number] = [0.1, 0.2];

/** The build the head and face are drawn at: the figure's own at face maturity 0, the adult build's (1) at 1. */
export const faceBuild = (sk: Skeleton): number => sk.build + sk.face_maturity * (1.0 - sk.build);

/** Where the arm leaves the torso, which is also where a short sleeve ends. */
export const armpitY = (sk: Skeleton): number => sk.shoulder_y + (sk.waist_y - sk.shoulder_y) * 0.42;

/** The height of the bust's fullest point, measured down from the armpit. */
export const bustY = (sk: Skeleton): number => armpitY(sk) + (sk.waist_y - armpitY(sk)) * BUST_ALONG;

/** How far the bust carries the torso out at `bustY`, 0 with none. An offset, so each part adds it to its own width. */
export const bustReach = (sk: Skeleton): number => sk.head_r * lerp(BUST_REACH[0], BUST_REACH[1], sk.build) * pyMax(0, sk.bust);

export function replace(sk: Skeleton, changes: Partial<Skeleton>): Skeleton {
  return { ...sk, ...changes };
}

type Numeric = number | null | undefined;

/** One character's measured proportions, laid over a built skeleton. `null` is "not measured, keep the lerp". */
export interface BodyProfile {
  readonly heads: number;
  readonly shoulder_y: Numeric;
  readonly waist_y: Numeric;
  readonly hip_y: Numeric;
  readonly hem_y: Numeric;
  /** The reference's boot top (see `Skeleton.boot_y`); the knee is derived. */
  readonly boot_y: Numeric;
  readonly ankle_y: Numeric;
  readonly shoulder_half_w: Numeric;
  readonly waist_half_w: Numeric;
  readonly hip_half_w: Numeric;
  readonly hem_half_w: Numeric;
  readonly arm_half_w: Numeric;
  readonly arm_x: Numeric;
  readonly leg_half_w: Numeric;
  /** Where the hand begins: its height and how far out the arm's centre hangs there. */
  readonly wrist_y: Numeric;
  readonly wrist_x: Numeric;
  /** Half the neck's width. `null` keeps the build's own (a chibi's thick one). */
  readonly neck_half_w: Numeric;
}

/** A profile with every landmark unmeasured, for the ones that name only some. */
export function profile(heads: number, measured: Partial<Omit<BodyProfile, "heads">> = {}): BodyProfile {
  return {
    heads,
    shoulder_y: null,
    waist_y: null,
    hip_y: null,
    hem_y: null,
    boot_y: null,
    ankle_y: null,
    shoulder_half_w: null,
    waist_half_w: null,
    hip_half_w: null,
    hem_half_w: null,
    arm_half_w: null,
    arm_x: null,
    leg_half_w: null,
    wrist_y: null,
    wrist_x: null,
    neck_half_w: null,
    ...measured,
  };
}

/** The same body under a head `s` times as big (every landmark is in head radii; the chin stays where it is). */
export function headScaled(bp: BodyProfile, s: number): BodyProfile {
  const y = (v: Numeric): Numeric => (v == null ? null : pyDiv(v - 1.0 + s, s));
  const w = (v: Numeric): Numeric => (v == null ? null : pyDiv(v, s));
  return {
    heads: pyDiv(bp.heads - 1.0 + s, s),
    shoulder_y: y(bp.shoulder_y),
    waist_y: y(bp.waist_y),
    hip_y: y(bp.hip_y),
    hem_y: y(bp.hem_y),
    boot_y: y(bp.boot_y),
    ankle_y: y(bp.ankle_y),
    shoulder_half_w: w(bp.shoulder_half_w),
    waist_half_w: w(bp.waist_half_w),
    hip_half_w: w(bp.hip_half_w),
    hem_half_w: w(bp.hem_half_w),
    arm_half_w: w(bp.arm_half_w),
    arm_x: w(bp.arm_x),
    leg_half_w: w(bp.leg_half_w),
    wrist_y: y(bp.wrist_y),
    wrist_x: w(bp.wrist_x),
    neck_half_w: w(bp.neck_half_w),
  };
}

const PROFILE_YS = ["shoulder_y", "waist_y", "hip_y", "hem_y", "boot_y", "ankle_y", "wrist_y"] as const;
const PROFILE_WS = [
  "shoulder_half_w",
  "waist_half_w",
  "hip_half_w",
  "hem_half_w",
  "arm_half_w",
  "arm_x",
  "leg_half_w",
  "wrist_x",
  "neck_half_w",
] as const;

export function applied(bp: BodyProfile, sk: Skeleton, build: number): Skeleton {
  const changes: { -readonly [K in keyof Skeleton]?: Skeleton[K] } = { build };
  for (const name of PROFILE_YS) {
    const v = bp[name];
    if (v != null) changes[name] = sk.head_cy + v * sk.head_r;
  }
  for (const name of PROFILE_WS) {
    const v = bp[name];
    if (v != null) changes[name] = v * sk.head_r;
  }
  // The real knee, half way down the leg this profile gives the figure.
  const hip = changes.hip_y ?? sk.hip_y;
  const ankle = changes.ankle_y ?? sk.ankle_y;
  changes.knee_y = hip + (ankle - hip) * 0.5;
  return replace(sk, changes);
}

const STRETCH_YS = ["waist_y", "hip_y", "hem_y", "knee_y", "boot_y", "ankle_y", "foot_y"] as const;
const KEEP_YS = ["neck_y", "shoulder_y"] as const;
const KEEP_WS = [
  "neck_half_w",
  "shoulder_half_w",
  "waist_half_w",
  "hip_half_w",
  "hem_half_w",
  "arm_half_w",
  "arm_x",
  "leg_half_w",
] as const;

/** How much the body's widths follow the height: `1 + WIDTH_FOLLOW * (h - 1)`. The neck stays with the head. */
export const WIDTH_FOLLOW = 0.6;

/** `sk` standing `h` times as tall from the shoulder line to the sole, with the head kept and the widths following a little. */
export function stretched(sk: Skeleton, h: number, refit: (heads: number) => Skeleton, legsShare = 2 / 3): Skeleton {
  const hr = (v: number): number => pyDiv(v - sk.head_cy, sk.head_r);
  const sh = hr(sk.shoulder_y);
  const hip = hr(sk.hip_y);
  const foot = hr(sk.foot_y);
  const extra = (foot - sh) * (h - 1.0);
  const torso = 1 + pyDiv(extra * (1 - legsShare), hip - sh);
  const legs = 1 + pyDiv(extra * legsShare, foot - hip);

  const y = (v: number): number => {
    if (v <= hip) return sh + (v - sh) * torso;
    return sh + (hip - sh) * torso + (v - hip) * legs;
  };

  const fit = refit((y(foot) + 1) / 2);
  const changes: { -readonly [K in keyof Skeleton]?: Skeleton[K] } = { build: sk.build };
  for (const name of STRETCH_YS) changes[name] = fit.head_cy + y(hr(sk[name])) * fit.head_r;
  for (const name of KEEP_YS) changes[name] = fit.head_cy + hr(sk[name]) * fit.head_r;
  if (sk.wrist_y !== null) changes.wrist_y = fit.head_cy + y(hr(sk.wrist_y)) * fit.head_r;
  const grow = 1.0 + WIDTH_FOLLOW * (h - 1.0);
  for (const name of KEEP_WS) {
    const follow = name === "neck_half_w" ? 1.0 : grow;
    changes[name] = pyDiv(sk[name], sk.head_r) * fit.head_r * follow;
  }
  if (sk.wrist_x !== null) changes.wrist_x = pyDiv(sk.wrist_x, sk.head_r) * fit.head_r * grow;
  return replace(fit, changes);
}

/** Headroom above the skull a figure at `heads` gets by default, in head radii, so the hair has somewhere to go. */
export function defaultHairMargin(heads: number): number {
  const t0 = pyMin(1.0, pyMax(0.0, (heads - 2.0) / 4.0));
  return lerp(0.75, 0.36, t0);
}

export interface BuildOptions {
  canvas_w?: number;
  canvas_h?: number;
  heads?: number;
  frame?: number;
  bust?: number;
  hair_margin?: number | null;
  bottom_margin?: number;
  min_hair_margin?: number;
}

/** `build_skeleton(...)` with named arguments, for callers that pass only a few. */
export const buildSkeletonWith = (o: BuildOptions): Skeleton =>
  buildSkeleton(o.canvas_w, o.canvas_h, o.heads, o.frame, o.bust, o.hair_margin, o.bottom_margin, o.min_hair_margin);

/** `build_skeleton`, with Python's parameters in Python's order (an `undefined` takes the default). */
export function buildSkeleton(
  canvasW0?: number,
  canvasH0?: number,
  heads0?: number,
  frame0?: number,
  bust0?: number,
  hairMargin0?: number | null,
  bottomMargin0?: number,
  minHairMargin0?: number,
): Skeleton {
  // A value that is not a number is kept as it is and raises `TypeError` where Python's arithmetic would (`BadValue`).
  const num = <T>(v: T, allowNull = false): T => (v === undefined || (v === null && allowNull) || typeof v === "number" || typeof v === "boolean" || v instanceof BadValue ? v : (new BadValue(v) as T));
  const opts: BuildOptions = {
    canvas_w: num(canvasW0),
    canvas_h: num(canvasH0),
    heads: num(heads0),
    frame: num(frame0),
    bust: num(bust0),
    hair_margin: num(hairMargin0, true),
    bottom_margin: num(bottomMargin0),
    min_hair_margin: num(minHairMargin0),
  };
  const canvasW = opts.canvas_w ?? 400;
  const canvasH = opts.canvas_h ?? 500;
  const heads = opts.heads ?? DEFAULT_HEADS;
  const frame = opts.frame ?? 0.0;
  const bust = opts.bust ?? 0.0;
  const bottomMargin = opts.bottom_margin ?? 0.03;
  const minHairMargin = opts.min_hair_margin ?? 0.0;
  let hairMargin = opts.hair_margin ?? null;
  // Passing `hair_margin` explicitly overrides `defaultHairMargin` entirely.
  if (hairMargin === null) hairMargin = defaultHairMargin(heads);
  // A floor rather than an override, for something worn above the hair (a witch's hat).
  hairMargin = pyMax(hairMargin, minHairMargin);
  const figH = pyDiv(canvasH * (1.0 - bottomMargin), 1.0 + pyDiv(hairMargin, 2.0 * heads));
  const headH = pyDiv(figH, heads);
  const headR = headH / 2;
  const headCy = headR * (1.0 + hairMargin);
  const chinY = headCy + headR;
  const body = figH - headH;

  // 0 at a 2-head chibi, 1 at 6 heads and up.
  const t = pyMin(1.0, pyMax(0.0, (heads - 2.0) / 4.0));
  // Frame is the shoulder-against-hip ratio: -1 narrow-shouldered and wide in the hip, +1 the other way.
  const f = pyMax(-1.0, pyMin(1.0, frame)) * t;

  const shoulderY = chinY + body * lerp(0.02, 0.028, t);
  const shoulderHalfW = headR * lerp(0.68, 1.55, t) * (1.0 + 0.09 * f);
  const waistY = chinY + body * lerp(0.46, 0.333, t);
  const waistHalfW = headR * lerp(0.88, 1.0, t) * (1.0 + 0.03 * f);

  return {
    canvas_w: canvasW,
    canvas_h: canvasH,
    heads,
    build: t,
    head_cx: canvasW / 2,
    head_cy: headCy,
    head_r: headR,
    neck_y: headCy + headR * 0.85,
    neck_half_w: headR * lerp(0.21, 0.4, t),
    shoulder_y: shoulderY,
    shoulder_half_w: shoulderHalfW,
    waist_y: waistY,
    waist_half_w: waistHalfW,
    hip_y: chinY + body * lerp(0.58, 0.417, t),
    hip_half_w: headR * lerp(0.95, 1.3, t) * (1.0 - 0.11 * f),
    hem_y: chinY + body * lerp(0.7, 0.58, t),
    hem_half_w: headR * lerp(1.02, 1.6, t),
    arm_half_w: headR * lerp(0.14, 0.33, t),
    arm_x: headR * lerp(0.85, 1.2, t) * (1.0 + 0.09 * f),
    leg_half_w: headR * lerp(0.22, 0.42, t),
    knee_y: chinY + body * lerp(0.81, 0.708, t),
    boot_y: chinY + body * lerp(0.81, 0.708, t),
    ankle_y: chinY + body * lerp(0.93, 0.95, t),
    foot_y: chinY + body,
    bust,
    face_maturity: 0.0,
    limb_taper: 0.0,
    wrist_y: null,
    wrist_x: null,
  };
}
