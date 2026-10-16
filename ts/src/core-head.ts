// The core-head module: the hair registry (`Hairstyle`, `HAIRSTYLES`, `hairFall`), the skull's edge and the hair's, the head's
// paths, and the eyes' placement with the brow. Port of character.py's `Hairstyle` to `_hair_fall`, and `_head_edge_x` to
// `_brow`. The cuts themselves are in core-head-cuts.ts and core-head-crop.ts, the tables in core-head-tables.ts; all three
// are re-exported from here, so `import ... from "./core-head.ts"` reaches everything. Generated once by
// harness/ts_port/gen_core_head.py from the Python, then owned by hand.

import { curve, headPt, headShape, outlineW, strokeW } from "./character.ts";
import { shade } from "./colorutil.ts";
import { agedFace, replace } from "./model.ts";
import type { CharacterParams, FaceStyle } from "./params.ts";
import { plainParams } from "./plain.ts";
import { PyInt } from "./pyjson.ts";
import { PyError, fmt1, fmt2, pyDiv, pyMax, pyMin, sorted, truthy } from "./pynum.ts";
import { PyFloat, pyTypeName, pyValueRepr } from "./pyvalue.ts";
import { type Skeleton, faceBuild } from "./skeleton.ts";
import type { Chain, Point } from "./tables.ts";
import {
  EYE_ASPECT,
  EYE_CORNER_CLEAR,
  EYE_GAP,
  type Lock,
  MATURE_EYE_DROP,
  MATURE_EYE_SHARE,
} from "./core-head-tables.ts";
import {
  type Hairline,
  centerPartHairlineShape,
  centerPartStrands,
  cropLocks,
  fallEdge,
  hairMassShape,
  hairTipEdge,
  hairlineShape,
  longStrands,
  longTracedFallEdge,
  longTracedHairline,
  longTracedLocks,
  longTracedMass,
  longTracedStrands,
  longTracedTipEdge,
  mirrored,
  partedFallEdge,
  partedHairline,
  partedLocks,
  partedMass,
  partedTipEdge,
  partedTipLines,
  partedUnderside,
  shortFallEdge,
  shortHairlineShape,
  shortLocks,
  shortMassShape,
  shortStrands,
  shortTipEdge,
} from "./core-head-cuts.ts";
import {
  cropFallEdge,
  cropHairlineShape,
  cropMassShape,
  cropStrands,
  cropTipEdge,
  fringedFallEdge,
  fringedHairline,
  fringedLocks,
  fringedMass,
  fringedOpenings,
  fringedShade,
  fringedStrands,
  fringedTipEdge,
  fringedUnderside,
  tousleFallEdge,
  tousleHairlineShape,
  tousleMassShape,
  tousleStrands,
  tousleTipEdge,
} from "./core-head-crop.ts";

export * from "./core-head-tables.ts";
export * from "./core-head-cuts.ts";
export * from "./core-head-crop.ts";
// The tables a recorded call refers to by their Python name (`calls.test.ts` looks a registry object up by it, underscore
// and all); every other table is under its TypeScript name only.
export {
  CROP_REAL_START as _CROP_REAL_START,
  FRINGED_FRONT as _FRINGED_FRONT,
  FRINGED_MASS as _FRINGED_MASS,
  FRINGED_UNDERSIDE as _FRINGED_UNDERSIDE,
  LONG_LOCKS as _LONG_LOCKS,
  PARTED_EDGE as _PARTED_EDGE,
  PARTED_LINE as _PARTED_LINE,
  PARTED_LOCK_L as _PARTED_LOCK_L,
  PARTED_LOCK_R as _PARTED_LOCK_R,
  PARTED_LOCKS as _PARTED_LOCKS,
  PARTED_UNDER_L as _PARTED_UNDER_L,
  PARTED_UNDER_R as _PARTED_UNDER_R,
  TOUSLE_TEMPLE as _TOUSLE_TEMPLE,
} from "./core-head-tables.ts";

// ---------------------------------------------------------------------------------------------------------
// The registry of cuts

/**
 * One haircut, as the four outlines that have to agree with each other.
 *
 * The mass carries the entire outer contour; the fall edge is the stretch of it
 * the front lock has to retrace exactly, so the two strokes land on each other
 * where the mass shows and the lock carries the silhouette where the body hides
 * it; the hairline is the only line drawn inside the mass; and the tip edge is
 * where the two tones meet. Each takes the tip depth in head radii, which
 * `_hair_fall` derives from the body-relative `hair_length`.
 */
export interface Hairstyle {
  readonly mass: (fall: number) => Chain;
  readonly hairline: (fall: number) => Hairline;
  // One chain per side. A list rather than one chain the drawing code mirrors,
  // because mirroring is an assumption that a cut is symmetric and it fails
  // without a sound: an asymmetric cut gets one side's lock edge stamped onto
  // the other, standing off the silhouette where the mass does not agree.
  // Symmetric cuts say so explicitly, with `_mirrored`.
  readonly fall_edge: (fall: number) => readonly Chain[];
  // One or more closed regions whose union is the tip-toned area. A list rather
  // than one region because a tone boundary that runs level across a whole head
  // can only say "pale below this height", and the canon says "pale from here to
  // the tip of *this lock*", which is a different region per lock and cannot be
  // one curve unless the locks happen to line up. A clip path is the union of
  // its children, so per-lock regions compose with no other machinery.
  //
  // It stays a list, never a set or a dict's values: `ref-out/` is compared byte
  // for byte, so the order these come out in has to be the order they went in.
  readonly tip_edge: (fall: number) => readonly Chain[];
  // Open chains drawn inside the mass, dividing it into locks. One flat shape
  // with no interior line reads as an object the colour of hair rather than as
  // hair, which is the difference between a haircut and a helmet. None leaves
  // the cut undivided, so a style that does not want them says nothing.
  readonly strands: ((fall: number) => readonly Chain[]) | null;
  // What hair_length 0 and 1 mean for this cut, as depth below the head centre
  // in head radii. None measures the body instead, chin to hip, which is what
  // keeps a long haircut the same haircut across builds.
  //
  // A cut that ends on the head needs its own range, because the body-relative
  // one cannot express anything above the chin: chin is its zero. It is also
  // the more correct unit for short hair, which is pinned to the skull and so
  // should not change length when the body gets longer.
  readonly tip_range: readonly [number, number] | null;
  // How much bigger the whole cut is at the chibi end than at the adult end, as
  // a multiplier on `tip_range`'s answer. None leaves a cut the same size against
  // its head at every build, which is what every cut here did before this and
  // what the two older ones still do.
  //
  // It exists because the canon does not work that way. Measured off both
  // Satoshi references in head-radius units, the chibi's hair stands 0.73 head
  // radii clear of its skull where the adult's stands 0.29, and the ratio
  // between the two contours is 1.32 across the crown with a standard deviation
  // of 0.008. So a chibi wears visibly more hair for the same head, one scalar
  // describes it, and a cut that ignores this comes out with an adult's volume
  // on a child's head. See `docs/gap-analysis.md` gap 1.
  //
  // A cut that raises this needs `build_skeleton`'s `hair_margin` to have room
  // for it at the chibi end, and the ceiling test is what says so.
  readonly volume: readonly [number, number] | null;
  // Whether the cut hangs in front of the ears. Such a cut's side locks were
  // fitted to the chibi skull, so they meet the face at face maturity 0 and
  // an ear under them never showed; a narrower, older face opens a gap
  // between lock and jaw that the ear would show through. The short cuts
  // show their ears.
  readonly covers_ears: boolean;
  // Hair behind in a second, darker tone: a region of the mass to paint in it
  // (clipped by the mass, so it may run outside), and the lines bounding it
  // where it shows, drawn with the mass behind the body. A darker tone on a
  // small part of the hair that lies behind, the owner's call under the
  // flat-colour rule (2026-09-29). None paints the mass in one tone.
  readonly underside: ((fall: number) => readonly [Chain, readonly Chain[]]) | null;
  // The line that runs on past each lock's tip, tapering to nothing, as the
  // drawn line does in the reference rather than stopping with the colour:
  // (apex, end) pairs, those behind drawn with the mass, those in front with
  // the front. Without it the tip is closed by the outline's round join, a
  // blunt end. None draws none.
  readonly tip_lines: ((fall: number) => readonly [readonly (readonly [Point, Point])[], readonly (readonly [Point, Point])[]]) | null;
  // Patches of skin showing through the front hair, closed chains drawn over it in the
  // skin tone with a thin outline: an ear peeping out between two locks, a gap in the
  // fringe. A hole in the hair's own outline would do for a gap, but not for an ear,
  // which has to be there whatever the head's own ear does, so they are drawn, not cut.
  readonly openings: ((fall: number) => readonly Chain[]) | null;
  // Regions of the front hair painted in a second, darker tone (clipped to the front):
  // the hair behind it showing through, as a strip down the outer side of a curtain
  // of locks. A darker tone on a small part of the hair that lies behind, which the
  // flat-colour rule allows (`underside`, the same call).
  readonly front_shade: ((fall: number) => readonly Chain[]) | null;
  // How heavy the strand lines are against the outline. A cut traced from a reference
  // that draws its locks' edges boldly says so.
  readonly strand_weight: number;
  // The clumps the soft finish lays over the front hair, `Lock`s given at the tip depth. None
  // leaves the cut without them, so a cut that has not been authored says nothing and the soft
  // finish draws it as before. The flat finish never reads this.
  readonly locks: ((fall: number) => readonly Lock[]) | null;
  // Whether the clumps are laid on the mass behind the head as well as on the front piece. A short
  // cut's crown is the mass, since the front piece is only the fringe and the temples, so a clump
  // there has to be drawn on both, in the same shape, and meets itself at the seam.
  readonly mass_locks: boolean;
}

/** `Hairstyle(mass, hairline, fall_edge, tip_edge, ...)`: the four outlines positionally, the rest by name with Python's defaults. */
export function makeHairstyle(
  mass: Hairstyle["mass"],
  hairline: Hairstyle["hairline"],
  fall_edge: Hairstyle["fall_edge"],
  tip_edge: Hairstyle["tip_edge"],
  rest: Partial<Hairstyle> = {},
): Hairstyle {
  return Object.freeze({
    mass,
    hairline,
    fall_edge,
    tip_edge,
    strands: null,
    tip_range: null,
    volume: null,
    covers_ears: false,
    underside: null,
    tip_lines: null,
    openings: null,
    front_shade: null,
    strand_weight: 0.55,
    locks: null,
    mass_locks: false,
    ...rest,
  });
}

export function longFallEdges(length: number): Chain[] {
  return mirrored(fallEdge(length));
}

export function shortFallEdges(tip: number): Chain[] {
  return mirrored(shortFallEdge(tip));
}

export function tousleFallEdges(tip: number): Chain[] {
  return mirrored(tousleFallEdge(tip));
}

/** The cuts by name. A null-prototype object, so that a name like `constructor` is a missing cut, not an inherited one. */
export const HAIRSTYLES: Readonly<Record<string, Hairstyle>> = Object.assign(Object.create(null) as Record<string, Hairstyle>, {
  long_blunt: makeHairstyle(hairMassShape, hairlineShape, longFallEdges, hairTipEdge, {
    strands: longStrands,
    covers_ears: true,
  }),
  short_layered: makeHairstyle(shortMassShape, shortHairlineShape, shortFallEdges, shortTipEdge, {
    strands: shortStrands,
    locks: shortLocks,
    mass_locks: true,
    // Where the side tips end: a tight crop pinned to the skull at 0, a
    // shaggy ear-length cut at 1. The old (0.42, 1.00) range described the
    // bob this used to be, with locks reaching for the jaw.
    tip_range: [0.25, 0.7],
  }),
  long_center_part: makeHairstyle(hairMassShape, centerPartHairlineShape, longFallEdges, hairTipEdge, {
    strands: centerPartStrands,
    // No `tip_range` and no `volume`, same as `long_blunt`: same mass, same
    // fall, so the same body-relative `hair_length` measure applies.
    covers_ears: true,
  }),
  long_traced: makeHairstyle(longTracedMass, longTracedHairline, longTracedFallEdge, longTracedTipEdge, {
    strands: longTracedStrands,
    locks: longTracedLocks,
    // No `tip_range`, so `hair_length` measures the body, chin to hip. That
    // is what keeps a long haircut the same haircut when the build changes;
    // a head-relative range would freeze her hair at one length and it would
    // ride up the adult's back.
    covers_ears: true,
  }),
  // Body-relative like `long_traced`, and no strands: the owner's call on
  // 2026-09-29 was no strand lines, and the lock edges and the underside's
  // lines are the reference's own line work at its main divisions.
  long_parted: makeHairstyle(partedMass, partedHairline, partedFallEdge, partedTipEdge, {
    covers_ears: true,
    underside: partedUnderside,
    tip_lines: partedTipLines,
    locks: partedLocks,
  }),
  // Blunt fringe across the brow, long straight locks in front of the shoulders and
  // the ears peeping out between them, traced off Risa's reference
  // (`docs/risa-plan.md`, M8). Body-relative like `long_traced`.
  long_fringed: makeHairstyle(fringedMass, fringedHairline, fringedFallEdge, fringedTipEdge, {
    strands: fringedStrands,
    covers_ears: true,
    openings: fringedOpenings,
    front_shade: fringedShade,
    underside: fringedUnderside,
    strand_weight: 0.8,
    locks: fringedLocks,
  }),
  short_crop: makeHairstyle(cropMassShape, cropHairlineShape, cropFallEdge, cropTipEdge, {
    strands: cropStrands,
    locks: cropLocks,
    mass_locks: true,
    // Where the side tips reach. `hair_length` 0.65, which is what Satoshi
    // carries, puts the cut at exactly the size it was traced at.
    tip_range: [0.8, 0.911],
    volume: [1.3, 1.0],
  }),
  short_tousled: makeHairstyle(tousleMassShape, tousleHairlineShape, tousleFallEdges, tousleTipEdge, {
    strands: tousleStrands,
    tip_range: [0.25, 0.7],
  }),
});

/**
 * `HAIRSTYLES[name]`: a name that is not a cut raises `KeyError` with the repr of the key, and a list or dict raises
 * `TypeError` (unhashable), as the dictionary does.
 */
export function hairstyleFor(name: unknown): Hairstyle {
  if (typeof name === "string") {
    const style = HAIRSTYLES[name];
    if (style !== undefined) return style;
  } else if (Array.isArray(name) || name instanceof Map || (typeof name === "object" && name !== null && !(name instanceof PyInt) && !(name instanceof PyFloat))) {
    throw new PyError("TypeError", `unhashable type: '${pyTypeName(name)}'`);
  }
  throw new PyError("KeyError", pyValueRepr(name));
}

/**
 * How far below the head center the hair ends, in head radii, which is the
 * unit the hair shapes are built in.
 *
 * Which range `hair_length` spans is the haircut's own business: a cut that
 * falls past the chin is measured against the body, so it survives a change of
 * build, and a cut that ends on the head is measured against the head. Doing
 * the conversion in one place is what lets both kinds share one knob.
 */
export function hairFall(sk: Skeleton, typed: CharacterParams): number {
  // The drawing reads plain numbers; `renderCharacter` has already made them (idempotent), and a direct caller (a link's
  // `hair_length` may be a string) gets Python's `TypeError` at the multiplication below, not `NaN`.
  const p = plainParams(typed);
  const style = hairstyleFor(p.hairstyle);
  if (style.tip_range !== null) {
    const [lo, hi] = style.tip_range;
    let fall = lo + p.hair_length * (hi - lo);
    if (style.volume !== null) {
      const [chibi, adult] = style.volume;
      fall *= adult + (chibi - adult) * (1.0 - sk.build);
    }
    return fall;
  }
  const chinY = sk.head_cy + sk.head_r;
  const tipY = chinY + p.hair_length * (sk.hip_y - chinY);
  return pyDiv(tipY - sk.head_cy, sk.head_r);
}

// ---------------------------------------------------------------------------------------------------------
// The skull's edge and the hair's

/**
 * How far off centre the skull's edge sits at height `y`, in head radii.
 *
 * Walks the right half of the profile a degree at a time and interpolates,
 * which is exact enough at this scale and, more to the point, cannot drift
 * away from the drawn outline the way a second formula would. Heights outside
 * the skull clamp to its ends rather than raising, since the callers are
 * placing a part against the head, not asking a question about geometry.
 */
export function headEdgeX(y: number, build: number): number {
  let prev = headPt(0.0, 1.0, build);
  for (let deg = 1; deg < 181; deg++) {
    const cur = headPt(deg, 1.0, build);
    // A chained comparison, `a <= y <= b`, written as the two tests it is.
    if (prev[1] <= y && y <= cur[1]) {
      const span = cur[1] - prev[1];
      const f = truthy(span) ? (y - prev[1]) / span : 0.0;
      return prev[0] + (cur[0] - prev[0]) * f;
    }
    prev = cur;
  }
  return prev[0];
}

/**
 * How far off centre the *silhouette* sits at height `y`, in head radii.
 *
 * The hair's own contour where the hair reaches that height, the skull's where
 * it does not, so a caller gets the outline a viewer actually sees rather than
 * the bone under it. `_head_edge_x` answers the other question and the two are
 * a head radius apart at the temples on a long cut.
 *
 * Which is the distinction three parts have now got wrong in the same
 * direction. A hat, a tie or a knot sized against the skull sits inside the
 * hair it is supposed to be on, and what it reads as is a shape painted on the
 * hair rather than an object placed over it.
 *
 * The widest crossing rather than the first: the contour can cross a height
 * more than once, at a lock's edge or a notch, and what a garment has to clear
 * is the outermost of them.
 *
 * Walks the mass's quadratics rather than taking the style's word for it, for
 * the reason `_head_edge_x` walks the skull's: a second formula agrees with the
 * drawing until somebody retunes one of them.
 */
export function hairEdgeX(y: number, sk: Skeleton, p: CharacterParams): number {
  const [start, segments] = hairstyleFor(p.hairstyle).mass(hairFall(sk, p));
  let widest = headEdgeX(y, faceBuild(sk));
  let prev = start;
  for (const [ctrl, end] of segments) {
    let here = prev;
    for (let i = 1; i < 25; i++) {
      const t = i / 24;
      const u = 1.0 - t;
      const nxt: Point = [
        u * u * prev[0] + 2 * u * t * ctrl[0] + t * t * end[0],
        u * u * prev[1] + 2 * u * t * ctrl[1] + t * t * end[1],
      ];
      const [lo, hi] = sorted([here[1], nxt[1]]) as [number, number];
      // A chained comparison, `lo <= y <= hi`, written as the two tests it is.
      if (lo <= y && y <= hi && nxt[1] !== here[1]) {
        const f = pyDiv(y - here[1], nxt[1] - here[1]);
        widest = pyMax(widest, Math.abs(here[0] + (nxt[0] - here[0]) * f));
      }
      here = nxt;
    }
    prev = end;
  }
  return widest;
}

/**
 * The head as path data: its filled shape, the silhouette line round the skull and
 * cheeks, and the lighter line under the chin (`_head` says why they are two).
 */
export function headPaths(sk: Skeleton): readonly [string, string, string] {
  const [start, segments] = headShape(faceBuild(sk));
  const [cx, cy, r] = [sk.head_cx, sk.head_cy, sk.head_r];
  const anchors = [start, ...segments.map(([, end]) => end)];
  const [chinFrom, chinTo] = [3, 5]; // the two segments either side of the chin
  const fill = curve(cx, cy, r, start, segments);
  const silhouette = curve(
    cx,
    cy,
    r,
    anchors[chinTo] as Point,
    [...segments.slice(chinTo), ...segments.slice(0, chinFrom)],
    false,
  );
  const underChin = curve(cx, cy, r, anchors[chinFrom] as Point, segments.slice(chinFrom, chinTo), false);
  return [fill, silhouette, underChin];
}

// ---------------------------------------------------------------------------------------------------------
// The eyes' placement and the brow

/**
 * The build the eye is drawn at: `face_build`, but only
 * `_MATURE_EYE_SHARE` of the way from the figure's own build.
 */
export function eyeBuild(sk: Skeleton): number {
  return sk.build + MATURE_EYE_SHARE * (faceBuild(sk) - sk.build);
}

/**
 * Where an eye sits and how big it is: `(eye_dx, eye_y, eye_r, face)`.
 *
 * One source for both `_face` and `_glasses`, which is what `_glasses` claimed
 * to be reading and was not: it carried its own copy of every number here, at
 * different values, so the rims sat closer together and lower than the eyes
 * they were meant to frame. A second definition agrees with the first on the
 * day it is written and stops agreeing the moment either one is retuned, which
 * is the same failure `_MOUTH_Y` was pulled out to stop.
 *
 * Returns the build-adjusted `FaceStyle` along with the geometry, not just the
 * numbers, because a caller sizing the aperture itself, the way `_glasses`
 * does, needs the lids at the values they are actually drawn at. The canon
 * lids the adult eye, almond where the chibi gets a round-open aperture, so
 * the adjustment happens once, here, rather than once per caller.
 */
export function eyePlacement(sk: Skeleton, p: CharacterParams): readonly [number, number, number, FaceStyle] {
  const r = sk.head_r;
  const cy = sk.head_cy;
  let f = p.face_age <= 1.0 ? p.face : agedFace(p.face, pyMin(1.0, p.face_age - 1.0));
  // Tuned for the realistic build, now retired, and still applied at the
  // tall chibi's pinned `sk.build` (about 0.1): every figure's eyes are open
  // 4% less and their lower lid 2% less than the face asks for. It is how the
  // cast has always looked, so it is kept as it renders (the owner's call,
  // `docs/tall-chibi-plan.md`, R0); an earlier comment here said the chibi
  // was unaffected, which was wrong. The heights were measured off
  // ref/satoko-real.jpg and ref/satoshi-real.jpg (aperture width/height read
  // by eye off a pixel grid, since the automated `eyes` probe finds the iris
  // highlight dot on this art rather than the aperture). What did not hold up on a re-measurement (`docs/gap-analysis.md`
  // gap 10) was the aspect ratio quoted to justify them: "about 2.2
  // times wider than tall" is not reproducible on either reference by
  // measuring width and height each as their own fraction of figure
  // height, which comes to 1.6 on Satoko and 1.4 on Satoshi. Height
  // was never the problem.
  f = replace(f, {
    eye_openness: f.eye_openness * (1.0 - 0.4 * eyeBuild(sk)),
    eye_lower_lid: f.eye_lower_lid * (1.0 - 0.2 * eyeBuild(sk)),
    // The width was: unlike the height, nothing had ever narrowed
    // it for the realistic build, so it carries the chibi's own
    // wide-aperture value (`_EYE_ASPECT`, deliberately widened for
    // the chibi's own reference in gap 6) straight into the adult
    // face, 60% to 90% too wide against either reference measured
    // the same way. `ref/satoko-real.jpg` is the owner's pick
    // between the two references, which also happens to be this
    // file's own tie-break rule when they disagree.
    //
    // Two wrong numbers were tried before this one, both from
    // measuring ink on a render instead of the path it comes from.
    // Matching our own ink width to the reference's ink width
    // arithmetically points at a reduction near 0.99: a stroke
    // bulges past a sharp corner by roughly its own width no
    // matter how narrow the path underneath is, so past some point
    // the number being matched is the stroke, not the aperture,
    // and 0.99 renders as a black sliver with no almond left. A
    // render sweep chosen by eye against that same ink-corrupted
    // signal landed on 0.50, which looked like a narrower almond in
    // a small crop but is actually the aperture's *width* passing
    // *below* its already-correct height (`docs/gap-analysis.md`
    // confirmed height was already close): the path comes out
    // 10.1 x 10.1, round again rather than flattened, and reads
    // exactly as round and crowded as the gap this was fixing,
    // caught on a full-face overlay a tight crop did not show.
    // `_eye_shape`'s aperture is closed-form, so there is no need to
    // measure our own ink at all: solve `2w / (top+bot) = 1.6`,
    // Satoko's own measured aspect, for the reduction, since
    // `top+bot` (the height) is already right. That is 0.21, not
    // 0.50, confirmed both by reading the emitted path's own bounds
    // (16.1 x 10.1, aspect 1.59) and by the same full-face overlay.
    // Satoshi's own reference wants narrower still (his measured
    // aspect is 1.4 against Satoko's 1.6), left as a residual
    // against his own photo rather than a second knob, the same
    // way gap 8 leaves per-character residuals against the shared
    // Satoko-anchored silhouette elsewhere.
    eye_width: f.eye_width * (1.0 - 0.21 * eyeBuild(sk)),
    // The canon's outer corner comes to a real point; ours rounded
    // off well short of it (gap 11, seen but not measured there).
    // `reach = 0.55 * eye_corner` in `_eye_shape` is what controls
    // it, so doubling `eye_corner` at full build doubles how far
    // the control point slides toward the apex/base, which is what
    // sliding it does: 0 sits it on the corner (round), further
    // along leaves the corner shallower (pointed). Picked by
    // render sweep against `ref/satoko-real.jpg`: 0.45 doubled to
    // 0.90 matches her corner; past about 1.0 it starts reading as
    // a point rather than a corner. Satoshi's own reference is
    // rounder than hers (his measured aspect is 1.4 against her
    // 1.6), so this is the same anchored-to-Satoko tradeoff gap 10
    // already made for width, not a new decision.
    eye_corner: f.eye_corner * (1.0 + 1.0 * eyeBuild(sk)),
  });
  // Canon face geometry, shared by every character; what differs per
  // character stays in FaceStyle. Eyes sit below the head's centre line and
  // well apart (the canon puts them at about half the face's half-width,
  // where they used to crowd the middle), and shrink relative to the head
  // as the build climbs: the canon draws the realistic iris about a quarter
  // smaller against the head than the chibi's, which is how an adult face
  // avoids going saucer-eyed while the chibi stays big-eyed.
  //
  // The 0.46 itself is gap 6's own canon measurement for the chibi, kept
  // exactly as it was there; narrowed only at higher `sk.build` rather
  // than changed outright, the same shape of fix as `eye_width` above.
  // Measured off `ref/satoko-real.jpg` as a ratio to the eye's own
  // (already-corrected) aperture width, scale-free so no cross-image
  // assumption is needed: hers comes to 0.82 against our 1.12 before this,
  // a 27% reduction to land on it, confirmed by full-face overlay rather
  // than trusted from the ratio alone (gap 11).
  const eyeY = cy + r * (0.16 + MATURE_EYE_DROP * sk.face_maturity);
  // Was 0.22 (this comment's own history, above). Not a reference match:
  // the owner's call on 2026-08-12 was bigger eyes than either photo
  // draws, after the rest of gap 11 landed, so there was no ratio to
  // solve for here, only a render sweep (0.22 down to 0.00) picked by eye
  // for "slightly larger" without crowding the brow or the two eyes into
  // each other. 0.12 still shrinks the realistic eye from the chibi's
  // own size, just by less than before.
  const eyeR = r * 0.26 * (1.0 - 0.12 * eyeBuild(sk)) * f.eye_size;
  // The spacing follows the eye (`docs/detail-plan.md`, D3; the owner,
  // 2026-09-27): held at 0.46 head radii whatever the eye's size, a smaller
  // eye (an older face, a preset's own `eye_size`) left a gap between the eyes
  // half again as wide against the eye as a larger one's, and on the Everglow
  // cover Gero's eyes read far apart beside Linnea's. So the half-gap is
  // `_EYE_GAP` of the eye's half-width, the cast's median, and an eye never
  // comes nearer the face's edge than `_EYE_CORNER_CLEAR`: a very large, wide
  // eye sits closer to its neighbour instead of running over the face
  // (`harness/detail/eye_spacing_study.py`).
  const w = eyeR * f.eye_width * EYE_ASPECT;
  const edge = headEdgeX(pyDiv(eyeY - cy, r), faceBuild(sk)) * r;
  const gap = f.eye_gap === null ? EYE_GAP : f.eye_gap;
  const eyeDx = pyMin(w * (1.0 + gap), edge - w - EYE_CORNER_CLEAR * r);
  return [eyeDx, eyeY, eyeR, f];
}

/** One brow: a line just above the lash line, on `side` (-1 left, 1 right). */
export function brow(sk: Skeleton, p: CharacterParams, side: number): string {
  const [eyeDx, eyeY, eyeR, f] = eyePlacement(sk, p);
  const sw = strokeW(sk);
  // Brows are hair, so they carry the hair's own darker tone rather than the
  // outline color. On dark hair the difference vanishes, which is correct.
  // 0.45 rather than a softer tint because the brows are what carry
  // expression now the eyes stay open: too faint and the face goes blank.
  const browColor = shade(p.hair_color, 0.45);
  const ex = sk.head_cx + side * eyeDx;
  // Just above the lash line, nearly touching it. The canon's sternness
  // lives in that closeness: a brow floating high off the eye reads as
  // mild surprise whatever its tilt says.
  const browY = eyeY - eyeR * 1.3;
  const tilt = f.brow_tilt * eyeR * 0.28;
  return (
    `<line x1="${fmt1(ex - side * eyeR * f.brow_length)}" y1="${fmt1(browY + tilt)}" ` +
    `x2="${fmt1(ex + side * eyeR * f.brow_length)}" y2="${fmt1(browY - tilt)}" ` +
    `stroke="${browColor}" stroke-width="${fmt2(outlineW(sw, f.brow_weight))}" stroke-linecap="round" />`
  );
}
