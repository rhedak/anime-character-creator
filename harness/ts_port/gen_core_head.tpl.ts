// The core-head module: the hair registry (`Hairstyle`, `HAIRSTYLES`, `hairFall`), the skull's edge and the hair's, the head's
// paths, and the eyes' placement with the brow. Port of character.py's `Hairstyle` to `_hair_fall`, and `_head_edge_x` to
// `_brow`. The cuts themselves are in core-head-cuts.ts and core-head-crop.ts, the tables in core-head-tables.ts; all three
// are re-exported from here, so `import ... from "./core-head.ts"` reaches everything. Generated once by
// harness/ts_port/gen_core_head.py from the Python, then owned by hand.

//@imports -fall

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

//@lead Hairstyle
//@doc Hairstyle
export interface Hairstyle {
  readonly mass: (fall: number) => Chain;
  readonly hairline: (fall: number) => Hairline;
  //@comments 3414-3418
  readonly fall_edge: (fall: number) => readonly Chain[];
  //@comments 3420-3428
  readonly tip_edge: (fall: number) => readonly Chain[];
  //@comments 3430-3433
  readonly strands: ((fall: number) => readonly Chain[]) | null;
  //@comments 3435-3442
  readonly tip_range: readonly [number, number] | null;
  //@comments 3444-3458
  readonly volume: readonly [number, number] | null;
  //@comments 3460-3464
  readonly covers_ears: boolean;
  //@comments 3466-3470
  readonly underside: ((fall: number) => readonly [Chain, readonly Chain[]]) | null;
  //@comments 3472-3476
  readonly tip_lines: ((fall: number) => readonly [readonly (readonly [Point, Point])[], readonly (readonly [Point, Point])[]]) | null;
  //@comments 3480-3483
  readonly openings: ((fall: number) => readonly Chain[]) | null;
  //@comments 3485-3488
  readonly front_shade: ((fall: number) => readonly Chain[]) | null;
  //@comments 3490-3491
  readonly strand_weight: number;
  //@comments 3493-3495
  readonly locks: ((fall: number) => readonly Lock[]) | null;
  //@comments 3497-3499
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

//@lead _long_fall_edges
export function longFallEdges(length: number): Chain[] {
  //@py 3504-3504
}

//@lead _short_fall_edges
export function shortFallEdges(tip: number): Chain[] {
  //@py 3508-3508
}

//@lead _tousle_fall_edges
export function tousleFallEdges(tip: number): Chain[] {
  //@py 3512-3512
}

//@lead HAIRSTYLES
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

//@lead _hair_fall
//@doc _hair_fall
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

//@lead _head_edge_x
//@doc _head_edge_x
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

//@lead _hair_edge_x
//@doc _hair_edge_x
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

//@lead _head_paths
//@doc _head_paths
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

//@lead _eye_build
//@doc _eye_build
export function eyeBuild(sk: Skeleton): number {
  return sk.build + MATURE_EYE_SHARE * (faceBuild(sk) - sk.build);
}

//@lead _eye_placement
//@doc _eye_placement
export function eyePlacement(sk: Skeleton, p: CharacterParams): readonly [number, number, number, FaceStyle] {
  const r = sk.head_r;
  const cy = sk.head_cy;
  let f = p.face_age <= 1.0 ? p.face : agedFace(p.face, pyMin(1.0, p.face_age - 1.0));
  //@comments 12861-12874
  f = replace(f, {
    eye_openness: f.eye_openness * (1.0 - 0.4 * eyeBuild(sk)),
    eye_lower_lid: f.eye_lower_lid * (1.0 - 0.2 * eyeBuild(sk)),
    //@comments 12879-12914
    eye_width: f.eye_width * (1.0 - 0.21 * eyeBuild(sk)),
    //@comments 12916-12928
    eye_corner: f.eye_corner * (1.0 + 1.0 * eyeBuild(sk)),
  });
  //@comments 12931-12946
  const eyeY = cy + r * (0.16 + MATURE_EYE_DROP * sk.face_maturity);
  //@comments 12948-12954
  const eyeR = r * 0.26 * (1.0 - 0.12 * eyeBuild(sk)) * f.eye_size;
  //@comments 12956-12964
  const w = eyeR * f.eye_width * EYE_ASPECT;
  const edge = headEdgeX(pyDiv(eyeY - cy, r), faceBuild(sk)) * r;
  const gap = f.eye_gap === null ? EYE_GAP : f.eye_gap;
  const eyeDx = pyMin(w * (1.0 + gap), edge - w - EYE_CORNER_CLEAR * r);
  return [eyeDx, eyeY, eyeR, f];
}

//@lead _brow
//@doc _brow
export function brow(sk: Skeleton, p: CharacterParams, side: number): string {
  const [eyeDx, eyeY, eyeR, f] = eyePlacement(sk, p);
  const sw = strokeW(sk);
  //@comments 13069-13072
  const browColor = shade(p.hair_color, 0.45);
  const ex = sk.head_cx + side * eyeDx;
  //@comments 13075-13077
  const browY = eyeY - eyeR * 1.3;
  const tilt = f.brow_tilt * eyeR * 0.28;
  return (
    `<line x1="${fmt1(ex - side * eyeR * f.brow_length)}" y1="${fmt1(browY + tilt)}" ` +
    `x2="${fmt1(ex + side * eyeR * f.brow_length)}" y2="${fmt1(browY - tilt)}" ` +
    `stroke="${browColor}" stroke-width="${fmt2(outlineW(sw, f.brow_weight))}" stroke-linecap="round" />`
  );
}
