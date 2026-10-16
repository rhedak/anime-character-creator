// The face domain's facial hair and worn pieces: the beard (with the two tracks that follow the skull's edge), the glasses, the
// goggles (the strap under the hair, the lenses over it) and the blindfold. Port of character.py's `_beard` (7104 to 7344),
// `_glasses`, `_goggle_geometry`, `_goggles_strap`, `_goggles` and `_blindfold` (7352 to 7640) and of `_jaw_track` and
// `_face_track` (12105 to 12169). The ears, the head and the face are in face.ts. Function names are the Python ones in
// camelCase; every expression keeps Python's evaluation order.

import { OUTLINE, headPt, interiorW, outlineW, strokeW } from "./character.ts";
import { shade } from "./colorutil.ts";
import { eyePlacement, hairEdgeX, headEdgeX, EYE_ASPECT } from "./core-head.ts";
import { MOUTH_REALISTIC_DROP, MOUTH_Y, noseY, pyStr } from "./face.ts";
import type { CharacterParams } from "./params.ts";
import { fmt1, fmt2, pyDiv, pyMax, pyMin, pyPow, pySlice, at, truthy } from "./pynum.ts";
import { type Skeleton, faceBuild } from "./skeleton.ts";
import type { Point } from "./tables.ts";

// ---------------------------------------------------------------------------------------------------------
// The tracks along the skull's edge

/**
 * The lower skull from height `y0` round to the chin, sunk by `drop`.
 *
 * The jaw's own line, moved down rather than replaced by an arc of somebody
 * else's shape. The sink ramps in from nothing at `y0`, so the curve leaves the
 * top corner where the sideburn left it instead of stepping away from it, and
 * the x scale ramps the other way, from the mass's inset at the top to the
 * skull's full width at the chin. Both ramps exist for the same reason: a beard
 * that starts exactly where the strip ended and ends exactly under the chin has
 * no seam anywhere, whatever the build does to the jaw underneath it.
 *
 * Right side only, ending on the centre line, which is where `_head_pt` puts the
 * chin. The caller mirrors it.
 */
export function jawTrack(y0: number, build: number, drop: number, inset: number, steps = 12): Point[] {
  // `next((d for d in range(90, 181) if _head_pt(float(d), 1.0, build)[1] >= y0), 90)`
  let deg0 = 90;
  for (let d = 90; d < 181; d++) {
    if ((headPt(d, 1.0, build) as Point)[1] >= y0) {
      deg0 = d;
      break;
    }
  }
  const pts: Point[] = [];
  for (let i = 0; i < steps + 1; i++) {
    const f = pyDiv(i, steps);
    const [x, y] = headPt(deg0 + (180.0 - deg0) * f, 1.0, build);
    pts.push([x * (inset + (1.0 - inset) * f), y + drop * f]);
  }
  // `deg0` is a whole degree, so it lands at or just past `y0`, which leaves the
  // first point up to a fiftieth of a head radius below where the strip ended.
  // That is a kink rather than a gap, since the path runs a straight line into
  // it, but it is a kink that moves with the build, and the point it should be
  // at is known exactly.
  pts[0] = [headEdgeX(y0, build) * inset, y0];
  return pts;
}

/**
 * Points down the skull's edge from `y0` to `y1`, in head radii.
 *
 * Each point sits `r` of the way out to the edge and then `w` further in, both
 * interpolated across the span, so a caller can lay a band along the cheek that
 * holds its own width while the face under it narrows. The two knobs are not
 * the same thing and both are needed: a ratio alone gives a band that thins as
 * the jaw draws in, and a width alone gives one that ignores the taper.
 *
 * `w_ease` bends the width's interpolation: above 1 it holds the band near `w0`
 * for longer and opens it late. That matters when only one end of the span is
 * crowded, which is the usual case for a band laid against a head, since the
 * top of the face is where the hair and the ear both arrive.
 *
 * Sampled off `_head_edge_x` rather than fitted, for the reason that helper
 * exists at all: it cannot drift away from the drawn outline. A polyline is
 * enough at the size this is looked at, ten segments over a quarter of the
 * skull being finer than the eight quadratics that draw the skull itself.
 */
export function faceTrack(
  y0: number,
  y1: number,
  build: number,
  r0: number,
  r1: number,
  w0 = 0.0,
  w1 = 0.0,
  w_ease = 1.0,
  steps = 10,
): Point[] {
  const pts: Point[] = [];
  for (let i = 0; i < steps + 1; i++) {
    const f = pyDiv(i, steps);
    const y = y0 + (y1 - y0) * f;
    const x = headEdgeX(y, build) * (r0 + (r1 - r0) * f) - (w0 + (w1 - w0) * pyPow(f, w_ease));
    pts.push([x, y]);
  }
  return pts;
}

// ---------------------------------------------------------------------------------------------------------
// The beard

// Where the beard's mass meets the face at the sides, and how far inside the
// skull's edge it lands there. Named constants rather than literals so a sweep
// can try candidates without editing the drawing code; see `harness/beard/`.
//
// The inset was 1.00, landing the top corners exactly on the skull's contour so
// the two outlines merged into one jaw. That was right about the outline and
// wrong about everything else: at the widest part of the face it left no cheek
// either side, so the mass ran ear to ear and the beard read as a hood with a
// face hole cut in it. Pulling it in to 0.87 put skin back beside the beard,
// which is what says the hair is growing on a jaw rather than wrapped round one.
// Four candidates were rendered against both references at head size and at tile
// size, since this part fails in opposite directions at the two sizes.
//
// It then moved back out to 0.93 on 2026-08-09, when the sideburns came to ride
// the same contour: the cheek is now held clear by the top edge's dive past the
// mouth rather than by this number, so what 0.87 bought was no longer a cheek but
// a band of skin between the strip and the hair above it, and a sideburn that
// does not reach the hair is a strap. 0.98 was tried too and is the old failure
// coming back, the beard meeting the hair along the whole side and closing the
// face in. See `harness/beard/sideburn.py`, which carries the old two-quadratic
// version alongside so the change can be judged as one.
export const BEARD_TOP = 0.63;
export const BEARD_SIDE_INSET = 0.93;
// How high the sideburn strip climbs the side of the face, in head radii from the
// head centre. About level with the top of the ear: high enough to meet the hair,
// and no higher, because a strip that carries on past the ear is a chinstrap.
export const BEARD_SIDEBURN_Y = 0.02;
// How far out the strip's outer edge starts, as a share of the skull's own edge.
// Just inside rather than on it, so the outline's stroke has somewhere to sit: at
// 1.00 half the line weight lands outside the head.
export const BEARD_SIDEBURN_OUT = 0.99;
// The strip's width in head radii, at the top and where it runs into the mass.
//
// **Wider at the bottom**, which is the way round a real sideburn goes and the
// opposite of what was here. The strip used to start 0.31 head radii wide at eye
// level and converge to 0.06 at the jaw, and a band whose two edges converge is a
// triangle: it read as a cut-out or a chinstrap rather than as hair, on both
// wearers, at both sizes. Against `ref/reinhard.png` the strip is narrow down the
// front of the ear and only spreads where it meets the beard, so the taper is
// inverted here and the numbers are small.
//
// The top width does two more jobs, and both want it small. It sets how much of
// the strip's top cut shows, that cut being a horizontal level with the top of the
// ear, and a long one reads as the edge of something worn rather than the top of
// some hair. And it decides how hard the strip collides with what is already at
// that height: 0.02 head radii is the head at its widest, where the side hair
// comes down and one hundredth above where the ear attaches, so three outlines
// arrive in the same place and at 0.08 they butt into each other instead of one
// tucking under another. At 0.04 the strip arrives as a taper thin enough to slip
// under the fringe, and it clears the ear rather than crossing it.
export const BEARD_SIDEBURN_W_TOP = 0.04;
export const BEARD_SIDEBURN_W_BOT = 0.17;
// How late the strip opens out. Above 1 it stays near its top width for longer and
// flares near the jaw instead of widening evenly the whole way down.
//
// Which is what the crowding actually wants, because only one end of this span is
// crowded. Widening evenly puts the strip back at a colliding width a short way
// down, still inside the stretch the ear runs alongside; at 2.0 it is half its
// final width only in the last third, which is past everything it can hit and is
// also the shape `ref/reinhard.png` has, a thin line in front of the ear that
// spreads at the jaw.
export const BEARD_SIDEBURN_W_EASE = 2.0;
// The moustache: how high it reaches at the centre, and how far out it runs
// before the edge turns down the jaw. Both in head radii.
//
// This is what stops the beard reading as a neckbeard. The top edge used to dive
// to about 0.895 in the middle with the chin at 1.0, so the mass covered the last
// tenth of the chin and hung below it, leaving bare skin from the lower lip to the
// jaw: shaved the face, kept the neck. The owner's call on 2026-08-09 was to bring
// the coverage up over the chin and around the mouth.
//
// **Raising the edge is not the same as raising it evenly**, and that distinction
// is the whole part. A level edge across the lower face is a surgical mask, which
// is what the first attempt at this drew and what the dive existed to avoid. So
// the edge stays low where it crosses the cheek and rises only in the middle, over
// a span narrow enough to read as a moustache. `_BEARD_TASH_HALF` is that span;
// past about 0.36 the lobe stops being a moustache and the mask comes back.
//
// The height is set by what is left between the lobe and the lip, not by where the
// lobe sits. At 0.46 that band came to 0.037 head radii, which on an 88 pixel head
// is 3.3 pixels of hair inside a 4 pixel outline: what got drawn was a line above
// the mouth rather than a moustache, and the owner's read was exactly that. At
// 0.36 it is 0.137, about a seventh of a head, which is a moustache. The other end
// is close: 0.31 was rendered too and the lobe starts climbing toward the nose and
// reads as a snout.
//
// That was 0.36 head radii at the old, heavier line. On 2026-09-27 the owner found
// it had always sat a bit high, and the grown face (`docs/detail-plan.md`, D3)
// needed the edge under its nose anyway: so the top is now `_BEARD_NOSE_GAP` under
// the nose's line (`_nose_y`) at every face age, about 0.43 on the chibi face. The
// band over the lip is thinner, and at the lighter line of D1 it still reads as a
// moustache at the smallest insert size (`harness/detail/beard_height.py`).
export const BEARD_NOSE_GAP = 0.05;
export const BEARD_TASH_HALF = 0.28;
// The lips, showing through. Both as multiples of the mouth's own half width, so
// the lozenge keeps its proportions on a character whose mouth is narrow; zero
// draws none.
//
// Without this the hair round the mouth and the hair under it are one unbroken
// field of colour, and a solid field over the whole lower face is a mask no
// matter what its outline does. The lip is what makes the same shape read as a
// moustache above and a beard below, and it is why a beard can cover the mouth
// at all without swallowing the face.
export const BEARD_LIP_W = 2.3;
export const BEARD_LIP_H = 0.63;

/**
 * Facial hair: a mass round the mouth and the chin, hanging below the jaw.
 *
 * Welded to the skull the way the ear is, by sampling `_head_edge_x` rather
 * than by assuming a circle, so it follows the jaw taper as the build gets
 * taller instead of standing off the face at one end of the range.
 *
 * Drawn over the head and under the face, which is what lets the moustache
 * exist: the skull's chin outline would otherwise run across the mass, and the
 * mouth has to sit on top of the hair around it rather than under it.
 *
 * A moustache is not a separate part. It is the middle of this one path's top
 * edge, lifted over the lip, which is also why that edge is four curves: it has
 * to stay off the cheek at the sides and climb in the middle, and one curve can
 * only do one of those.
 */
export function beard(sk: Skeleton, p: CharacterParams): string {
  if (p.beard_color === null) return "";
  const cx = sk.head_cx;
  const cy = sk.head_cy;
  const r = sk.head_r;
  const b = faceBuild(sk);
  const color = p.beard_color;
  const sw = strokeW(sk);
  // Where the mass meets the face at the sides. Level with the mouth, which is
  // as high as it can go before the cheek starts disappearing: the head is at
  // its widest just above this, so every step upward here adds a band of face
  // width to the mass and the beard turns into a hood.
  const top = BEARD_TOP;
  // How deep the growth is, which since 2026-08-09 is a depth rather than a
  // length: the bottom rides the jaw and this is how far it sinks below it. It
  // used to set how far a swung arc reached past the chin, which is why the
  // preset values dropped by more than half when the shape changed.
  const drop = pyMax(0.0, p.beard_length);
  // Everything below rides `_BEARD_SIDE_INSET`, which keeps the mass **on** the
  // skull's edge rather than inside it. Tucked inside, the face's own outline
  // runs across above the beard, the mass below reads as a separate object
  // hanging off the chin, and what comes out is a scarf. The cheek is kept clear
  // by *height* instead: `top` sits below the head's widest point, so there is
  // face above the beard rather than beside it.
  //
  // **The sideburns are what make it read as facial hair at all.** Without them
  // the mass hangs under the jaw connected to nothing, and every version of that
  // came out as a scarf, a collar or a neck warmer no matter how it was shaped
  // or toned. A strip running up the side of the face to the hairline is the
  // thing that says the beard grows out of the head, and it costs two points on
  // each side of the path.
  //
  // Narrow, and **following the skull's own edge point by point**, so the strip
  // hugs the cheek instead of standing off it. Both edges used to be one
  // quadratic apiece, which chords across a curve rather than riding it: the
  // control could set where the line bulged but not make it agree with the face,
  // and what came out was two straight diagonals. `_face_track` samples the same
  // contour the outline is drawn from, so the strip curves with the cheek at any
  // build for free.
  //
  // `_BEARD_SIDEBURN_Y` is where it reaches: high enough to meet the hair, and
  // no higher, since a strip climbing past the ear is a chinstrap.
  const burnY = BEARD_SIDEBURN_Y;
  // The inner edge runs lower than the outer one, down to where it meets the top
  // edge's dive, so it gets its own span rather than sharing the outer one.
  const joinY = top + 0.14;
  const outer = faceTrack(burnY, top, b, BEARD_SIDEBURN_OUT, BEARD_SIDE_INSET);
  const inner = faceTrack(
    burnY,
    joinY,
    b,
    BEARD_SIDEBURN_OUT,
    BEARD_SIDE_INSET,
    BEARD_SIDEBURN_W_TOP,
    BEARD_SIDEBURN_W_BOT,
    BEARD_SIDEBURN_W_EASE,
  );

  // Where the top edge turns: the moustache's outer end sits a touch below the
  // mouth so the two corners meet, which is where a beard and a moustache join
  // on a face.
  const xJoin = at(inner, -1)[0];
  // Both follow the grown face down (`docs/detail-plan.md`, D3): the corner with
  // the mouth, and the top edge sits under the nose's line at every face age,
  // a nose drawn or not, since a beard ends between the nose and the mouth
  // rather than growing round the nose.
  const grown = faceBuild(sk) - sk.build;
  const cornerY = MOUTH_Y + 0.02 + MOUTH_REALISTIC_DROP * grown;
  const tashHalf = BEARD_TASH_HALF;
  const tashY = noseY(sk) + BEARD_NOSE_GAP;

  const line = (pts: readonly Point[], s: number): string =>
    pts.map(([x, y]) => `L ${fmt1(cx + s * x * r)} ${fmt1(cy + y * r)} `).join("");

  // The bottom, from the left top corner round to the right one: the jaw's own
  // line, sunk by the depth of the growth.
  //
  // What was here was an arc swung wide of the jaw and squared off under the
  // chin, a shape with bulk of its own rather than one following the face, and
  // what it read as was hair on a neck. The jaw line is also the version that
  // survives being made short, which is what the owner asked for on 2026-08-09:
  // a shallow arc is a crescent that could be anything, while a jaw line is
  // still a jaw at any depth. The arc is kept in `harness/beard/hang.py` so the
  // two can be put side by side again.
  const jaw = jawTrack(top, b, drop, BEARD_SIDE_INSET);
  const bottomD = `${line(jaw, -1)}${line(pySlice(jaw, -2, null, -1), 1)}`;

  const d =
    // Down the outside: sideburn, then round the bottom and back up.
    `M ${fmt1(cx - (outer[0] as Point)[0] * r)} ${fmt1(cy + burnY * r)} ` +
    `${line(pySlice(outer, 1), -1)}` +
    `${bottomD}` +
    // Back up the right side, then across the top of the strip and down its
    // inner edge.
    `${line(pySlice(outer, -2, null, -1), 1)}` +
    `${line(inner, 1)}` +
    // The top edge, right to left. Four curves rather than one, because it has
    // to do two opposite things: stay off the cheek at the sides and climb
    // over the lip in the middle. One curve between the two joins can only
    // pick a single height and is wrong at one end whichever it picks, which
    // is how this part produced both a surgical mask and a neckbeard from the
    // same line. In from each join to the corner of the mouth, then up and
    // across the moustache.
    `Q ${fmt1(cx + xJoin * r * 0.99)} ${fmt1(cy + (cornerY + (joinY - cornerY) * 0.34) * r)} ` +
    `${fmt1(cx + tashHalf * r)} ${fmt1(cy + cornerY * r)} ` +
    `Q ${fmt1(cx + tashHalf * r * 0.55)} ${fmt1(cy + tashY * r)} ${fmt1(cx)} ${fmt1(cy + tashY * r)} ` +
    `Q ${fmt1(cx - tashHalf * r * 0.55)} ${fmt1(cy + tashY * r)} ` +
    `${fmt1(cx - tashHalf * r)} ${fmt1(cy + cornerY * r)} ` +
    `Q ${fmt1(cx - xJoin * r * 0.99)} ${fmt1(cy + (cornerY + (joinY - cornerY) * 0.34) * r)} ` +
    `${fmt1(cx - xJoin * r)} ${fmt1(cy + joinY * r)} ` +
    `${line(pySlice(inner, -2, null, -1), -1)}` +
    `Z`;
  const mass = `<path d="${d}" fill="${pyStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`;
  if (BEARD_LIP_W <= 0) return mass;
  // Outlined, at well under the usual weight. Unstroked was tried first, on the
  // reasoning that the mouth's own line lands on this a layer later and a second
  // ring round it would read as a second mouth, and that is true at full weight
  // and false at this one: an outline here reads as the edge of a lip. It also
  // has to be *some* outline, since a colour patch with no ink round it is the
  // one soft edge in a drawing where everything else is hard-edged.
  //
  // Both radii ride `mouth_width`, so the lozenge stays the same shape on a
  // character with a small mouth instead of turning into a different lozenge.
  const lip = 0.12 * p.face.mouth_width;
  // `cy` here has to track `_face`'s own `mouth_y`, which drops further at
  // the realistic build than `_MOUTH_Y` alone (`_MOUTH_REALISTIC_DROP`):
  // left at plain `_MOUTH_Y`, the actual mouth stroke drawn on top of this
  // moved out from under the hole meant to frame it and rendered as a
  // stray line inside the fur below the lip, on both bearded presets. The
  // lozenge's own width already clears the mouth's realistic-build widening
  // without needing the same treatment (`_BEARD_LIP_W` at 2.3 against the
  // mouth's own worst case of `mouth_width * 1.85`).
  const lipY = cy + (MOUTH_Y + MOUTH_REALISTIC_DROP * faceBuild(sk)) * r;
  return (
    `${mass}` +
    `<ellipse cx="${fmt1(cx)}" cy="${fmt1(lipY)}" ` +
    `rx="${fmt1(lip * BEARD_LIP_W * r)}" ry="${fmt1(lip * BEARD_LIP_H * r)}" ` +
    `fill="${pyStr(p.skin_tone)}" stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.4))}" />`
  );
}

// ---------------------------------------------------------------------------------------------------------
// Glasses

// How far outside the aperture's own bounding box the rim sits. A rounded rect
// is not an almond, so a rim drawn tight against the eye's exact extremes clips
// the corners; this is the same kind of clearance `_SCARF_CLEAR` gives a cap over
// hair, sized larger because a rim's rounded corner cuts in further than a cloth
// hem does.
export const GLASSES_CLEAR = 1.18;

/**
 * Fine wire spectacles: two rims and a bridge, no lenses.
 *
 * No fill, so the eyes read through them. A tinted lens would be a second tone
 * over the iris and would take the eye colour with it, and the eye is the one
 * thing on a face that has to survive being shrunk.
 *
 * Sized off the eye's own aperture rather than a second guess at it. This used
 * to carry its own copy of every number `_eye_placement` returns, at different
 * values, `eye_dx` 0.34 against the real 0.46 and `eye_y` at `+0.10` against
 * the real `+0.16` among them, so the rim sat closer to the nose and lower than
 * the eye it was meant to frame and the eye showed outside it on two sides.
 * `_eye_placement` is now the only definition of where an eye is, and
 * `_eye_shape`'s own half extents are the only definition of how big the
 * aperture is, so a rim built from both cannot drift off the eye however
 * a character's face is tuned.
 */
export function glasses(sk: Skeleton, p: CharacterParams): string {
  if (!truthy(p.face.glasses)) return "";
  const cx = sk.head_cx;
  const cy = sk.head_cy;
  const r = sk.head_r;
  const [eyeDx, eyeY, eyeR, f] = eyePlacement(sk, p);
  const sw = strokeW(sk);
  // The aperture's own half extents, in the same terms `_eye_shape` builds it
  // from: apex and base sit exactly at `top` and `bot`, and the inner and outer
  // corners exactly at `w`, so this is the aperture's true bounding box rather
  // than an approximation of it.
  const halfW = eyeR * f.eye_width * EYE_ASPECT * GLASSES_CLEAR;
  const topH = eyeR * f.eye_openness * GLASSES_CLEAR;
  const botH = eyeR * f.eye_lower_lid * GLASSES_CLEAR;
  const stroke = `fill="none" stroke="${OUTLINE}" stroke-width="${fmt2(interiorW(sw, 0.55))}"`;
  const parts = [-1, 1].map(
    (s) =>
      `<rect x="${fmt1(cx + s * eyeDx - halfW)}" y="${fmt1(eyeY - topH)}" ` +
      `width="${fmt1(halfW * 2)}" height="${fmt1(topH + botH)}" ` +
      `rx="${fmt1(pyMin(halfW, topH + botH) * 0.3)}" ${stroke} />`,
  );
  parts.push(
    `<path d="M ${fmt1(cx - eyeDx + halfW)} ${fmt1(eyeY)} ` + `L ${fmt1(cx + eyeDx - halfW)} ${fmt1(eyeY)}" ${stroke} />`,
  );
  // Arms to the temples, which is what stops the pair reading as two rings
  // floating on the cheeks. Read off the skull at the height the arm actually
  // leaves at, rather than a second guess at eye height: the arm used to query
  // the skull's edge at a fixed 0.10 head radii while the eye it left from sat
  // at 0.16, which is the same drift as everything else here.
  const armY = eyeY - topH * 0.35;
  const armYHr = pyDiv(armY - cy, r);
  for (const s of [-1, 1]) {
    parts.push(
      `<path d="M ${fmt1(cx + s * (eyeDx + halfW))} ${fmt1(eyeY)} ` +
        `L ${fmt1(cx + s * headEdgeX(armYHr, faceBuild(sk)) * r)} ${fmt1(armY)}" ${stroke} />`,
    );
  }
  return parts.join("");
}

// ---------------------------------------------------------------------------------------------------------
// Goggles

// How far above the eye the lenses rest, in eye radii. Pushed up onto the
// forehead rather than worn over the eyes, which is the one thing that tells a
// pair of goggles from a pair of glasses; too small a lift and they read as
// spectacles that missed the eyes rather than as a pair worn up.
export const GOGGLE_LIFT = 2.6;
// How much closer together the lenses sit than the eyes below them: two lenses
// on a bridge sit close, where two eyes sit apart for the face to read.
export const GOGGLE_DX_SCALE = 0.72;
export const GOGGLE_R_SCALE = 0.98;
// How far into the hairstyle's own edge each strap arm reaches, as a fraction
// of that edge: short of it, not past it. The arm has to disappear under the
// hair, and the hair mass only covers what is inside its own silhouette, so an
// arm run out to or beyond the edge `_hair_edge_x` reports lands partly in open
// air with nothing left to draw over it, which is what the first version of
// this did. Inset rather than run exactly to the edge, so the tip sits solidly
// inside the mass rather than riding its outline, where antialiasing or a
// hairstyle a pixel narrower than the one this was tuned against could still
// expose it.
export const GOGGLE_ARM_INSET = 0.85;

/**
 * `(lens_y, lens_r, lens_dx)`: where the lenses sit and how big they are.
 *
 * Shared between `_goggles_strap`, drawn under the hair, and `_goggles`,
 * drawn over it, so the two halves of one object agree on where it sits
 * without a second copy of the numbers drifting apart, the same reason
 * `_eye_placement` exists.
 */
export function goggleGeometry(sk: Skeleton, p: CharacterParams): [number, number, number] {
  const [eyeDx, eyeY, eyeR] = eyePlacement(sk, p);
  const lensR = eyeR * GOGGLE_R_SCALE;
  const lensDx = eyeDx * GOGGLE_DX_SCALE;
  const lensY = eyeY - eyeR * GOGGLE_LIFT;
  return [lensY, lensR, lensDx];
}

/**
 * The strap's two temple arms, drawn before the hair mass.
 *
 * A strap that goes around the head runs under the hair at the sides, not
 * across the top of it, so unlike the rest of the goggles this half is drawn
 * before `_hair_front` rather than after: the hair mass is a filled shape
 * that already reads as being in front of the ear and the beard's sideburns
 * for the same reason, and an arm drawn here inherits that for free instead
 * of needing to fake a cut edge of its own.
 *
 * Each arm starts at its own lens (`_goggle_geometry`'s `lens_dx`, so the
 * lens drawn later covers the seam) and runs out to a point inset from the
 * hairstyle's own edge, read with `_hair_edge_x` rather than `_head_edge_x`:
 * a strap sized to the skull stops well short of the hair, and it is
 * exactly this gap, between where the strap end sat and where the hair
 * actually is, that read as the strap stopping in mid-air rather than
 * continuing around the head.
 */
export function gogglesStrap(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.goggle_color === null) return "";
  const cx = sk.head_cx;
  const cy = sk.head_cy;
  const r = sk.head_r;
  const color = p.outfit.goggle_color;
  const sw = strokeW(sk);
  const [lensY, lensR, lensDx] = goggleGeometry(sk, p);
  const strapH = lensR * 0.5;
  const strapYHr = pyDiv(lensY - cy, r);
  const xFar = hairEdgeX(strapYHr, sk, p) * r * GOGGLE_ARM_INSET;
  const parts: string[] = [];
  for (const side of [-1, 1]) {
    const x0 = cx + side * lensDx;
    const x1 = cx + side * xFar;
    parts.push(
      `<path d="M ${fmt1(x0)} ${fmt1(lensY - strapH / 2)} ` +
        `L ${fmt1(x1)} ${fmt1(lensY - strapH / 2)} ` +
        `L ${fmt1(x1)} ${fmt1(lensY + strapH / 2)} ` +
        `L ${fmt1(x0)} ${fmt1(lensY + strapH / 2)} Z" ` +
        `fill="${pyStr(color)}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`,
    );
  }
  return parts.join("");
}

/**
 * A pair of lenses on a bridge, pushed up onto the forehead.
 *
 * Reads off `_eye_placement` the same way `_glasses` does, lifted above the
 * brow rather than framing the eye: this is what keeps the pair centred over
 * the face at every build, an eye that moves and a pair of goggles that does
 * not agree with it is the same drift `_glasses` was pulled off a second copy
 * of the eye to fix.
 *
 * This is the half of the goggles drawn over the hair: the lenses themselves
 * and the bridge joining them, which cross the bare forehead and have
 * nothing to disappear into. `_goggles_strap` draws the other half, the
 * strap's two temple arms, before the hair mass instead of after it. Glass
 * is a lighter, paler tone of the frame color rather than a second color of
 * its own: `shade()` already derives a shadow tone from a base one, and a
 * lens is the same derivation run the other way, so a goggle color always
 * ships with a glass that reads against it instead of needing one
 * hand-picked to match.
 */
export function goggles(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.goggle_color === null) return "";
  const cx = sk.head_cx;
  const color = p.outfit.goggle_color;
  const glass = shade(color, 1.8, 0.55);
  const sw = strokeW(sk);
  const [lensY, lensR, lensDx] = goggleGeometry(sk, p);
  const parts = [
    // The bridge joining the lenses, under them so their own rims cover
    // its ends rather than leaving a bar visible between two circles.
    `<path d="M ${fmt1(cx - lensDx)} ${fmt1(lensY)} L ${fmt1(cx + lensDx)} ${fmt1(lensY)}" ` +
      `fill="none" stroke="${color}" stroke-width="${fmt1(lensR * 0.5)}" stroke-linecap="round" />`,
  ];
  for (const side of [-1, 1]) {
    const lx = cx + side * lensDx;
    parts.push(
      `<circle cx="${fmt1(lx)}" cy="${fmt1(lensY)}" r="${fmt1(lensR)}" ` +
        `fill="${color}" stroke="${OUTLINE}" stroke-width="${fmt2(outlineW(sw))}" />`,
    );
    parts.push(`<circle cx="${fmt1(lx)}" cy="${fmt1(lensY)}" r="${fmt1(lensR * 0.72)}" fill="${glass}" />`);
    parts.push(
      `<circle cx="${fmt1(lx - lensR * 0.24)}" cy="${fmt1(lensY - lensR * 0.24)}" ` +
        `r="${fmt1(lensR * 0.16)}" fill="white" opacity="0.75" />`,
    );
  }
  return parts.join("");
}

// ---------------------------------------------------------------------------------------------------------
// The blindfold

// How far above the eye's centre the band's centreline rests, in eye radii: above
// the brow, clear of the goggles' own 2.6, so a band reads as pushed up onto the
// forehead rather than worn across the eyes.
export const BLINDFOLD_LIFT = 2.45;
// The band's half height in eye radii, and how far its two edges sag toward the
// face in the middle: a band round a head seen from the front dips at the centre,
// where level across it reads as a flat strip painted on.
export const BLINDFOLD_HALF_H = 0.72;
export const BLINDFOLD_SAG = 0.35;
// How far outside the hair the cloth stands, the headscarf's own reasoning: a
// band over hair is slightly proud of it, and at exactly the cut's width the
// two outlines land on each other.
export const BLINDFOLD_CLEAR = 1.03;

/**
 * A band of cloth pushed up onto the forehead, over the fringe.
 *
 * Placed off `_eye_placement` like the goggles, so it keeps its place over the
 * face at every build, and sized to the hair's own width with `_hair_edge_x`
 * like the headscarf, so it clears a long cut rather than sitting inside it.
 * Over the hair and under a scarf or hat. Two fold lines in a deeper tone of
 * the cloth say it is cloth and not a stripe; the band is otherwise one flat
 * colour, and the ends are straight where it goes round the head out of sight.
 */
export function blindfold(sk: Skeleton, p: CharacterParams): string {
  if (p.outfit.blindfold_color === null) return "";
  const cx = sk.head_cx;
  const cy = sk.head_cy;
  const r = sk.head_r;
  const color = p.outfit.blindfold_color;
  const sw = strokeW(sk);
  const [, eyeY, eyeR] = eyePlacement(sk, p);
  const midY = eyeY - eyeR * BLINDFOLD_LIFT;
  const halfH = eyeR * BLINDFOLD_HALF_H;
  const sag = eyeR * BLINDFOLD_SAG;
  const topY = midY - halfH;
  const botY = midY + halfH;
  const xEdge = hairEdgeX(pyDiv(midY - cy, r), sk, p) * r * BLINDFOLD_CLEAR;
  const leftX = cx - xEdge;
  const rightX = cx + xEdge;
  const d =
    `M ${fmt1(leftX)} ${fmt1(topY)} ` +
    `Q ${fmt1(cx)} ${fmt1(topY + sag * 2)} ${fmt1(rightX)} ${fmt1(topY)} ` +
    `L ${fmt1(rightX)} ${fmt1(botY)} ` +
    `Q ${fmt1(cx)} ${fmt1(botY + sag * 2)} ${fmt1(leftX)} ${fmt1(botY)} Z`;
  const fold = shade(color);
  const lines = [-0.34, 0.3]
    .map(
      (dx) =>
        `<path d="M ${fmt1(cx + dx * xEdge)} ${fmt1(midY + sag * (1 - dx * dx) - halfH * 0.55)} ` +
        `Q ${fmt1(cx + (dx + 0.06) * xEdge)} ${fmt1(midY + sag * (1 - dx * dx))} ` +
        `${fmt1(cx + dx * xEdge)} ${fmt1(midY + sag * (1 - dx * dx) + halfH * 0.55)}" ` +
        `fill="none" stroke="${fold}" stroke-width="${fmt2(interiorW(sw, 0.8))}" stroke-linecap="round" />`,
    )
    .join("");
  return (
    `<path d="${d}" fill="${color}" stroke="${OUTLINE}" ` +
    `stroke-width="${fmt2(outlineW(sw))}" stroke-linejoin="round" />${lines}`
  );
}
