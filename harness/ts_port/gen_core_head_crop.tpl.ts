// The core-head module, part two: Satoshi's traced crop, his tousled crop, and Risa's fringed cut. Port of character.py's
// hair block from `_crop_real_point` to `_fringed_shade`. Generated once by harness/ts_port/gen_core_head.py from the Python
// (so no coordinate is typed), then owned by hand. See core-head-cuts.ts for the conventions.

//@imports -fall

// ---------------------------------------------------------------------------------------------------------
// Satoshi's traced crop

//@lead _crop_real_point
//@doc _crop_real_point
export function cropRealPoint(i: number, pt: Point): Point {
  let [x, y] = pt;
  // A chained comparison, `lo <= y <= hi`, written as the two tests it is.
  const atEarHeight = EAR_TOP_Y - CROP_REAL_EAR_BUFFER <= y && y <= EAR_BOT_Y + CROP_REAL_EAR_BUFFER;
  if (atEarHeight) {
    const floor = CROP_REAL_EAR_X[1] + CROP_REAL_EAR_MARGIN;
    x = copysign(pyMax(Math.abs(x), floor), x);
  } else if (inRange(i, CROP_REAL_SIDEBURN_L) || inRange(i, CROP_REAL_SIDEBURN_R)) {
    x = x * CROP_REAL_SIDEBURN_PUSH;
  }
  return scalePoint([x, y], CROP_REAL_SCALE);
}

//@lead _crop_outline
//@doc _crop_outline
export function cropOutline(fall: number): Chain {
  if (Math.abs(fall - CROP_REAL_FALL) < CROP_REAL_TOL) {
    return [
      cropRealPoint(-1, CROP_REAL_START),
      CROP_REAL_EDGE.map(([c, e], i): Segment => [cropRealPoint(i, c), cropRealPoint(i, e)]),
    ];
  }
  //@py 2444-2445 start:Point
  return [start, CROP_EDGE.map(([c, e]): Segment => [[c[0] * v, c[1] * v], [e[0] * v, e[1] * v]])];
}

//@lead _crop_indices
//@doc _crop_indices
export function cropIndices(fall: number): readonly [number, number, number] {
  if (Math.abs(fall - CROP_REAL_FALL) < CROP_REAL_TOL) {
    return [CROP_REAL_TEMPLE_L, CROP_REAL_TEMPLE_R, CROP_REAL_CROWN_AT];
  }
  return [CROP_TEMPLE_L, CROP_TEMPLE_R, CROP_CROWN_AT];
}

//@lead _crop_mass_shape
//@doc _crop_mass_shape
export function cropMassShape(fall: number): Chain {
  //@py 2465-2465
  const end = at(edge, -1)[1];
  //@py 2467-2468 nape:Point
}

//@lead _crop_fall_edge
//@doc _crop_fall_edge
export function cropFallEdge(fall: number): Chain[] {
  //@py 2480-2481
  return [
    reverse(at(edge, crownAt)[1], pySlice(edge, crownAt + 1)),
    [start, pySlice(edge, null, crownAt + 1)],
  ];
}

//@lead _crop_hairline_shape
//@doc _crop_hairline_shape
export function cropHairlineShape(fall: number): Hairline {
  //@py 2509-2510
  const leftTemple = at(edge, templeL)[1];
  const rightTemple = at(edge, templeR)[1];
  const [lx, ly] = CROP_FRINGE_START;
  const [rx, ry] = at(CROP_FRINGE, -1)[1];
  const line: Segment[] = [
    // out to the temple, past where the forehead ends and the trace with it
    [[(leftTemple[0] + lx) / 2, ly - 0.10], [lx, ly]],
    ...CROP_FRINGE,
    [[(rightTemple[0] + rx) / 2, ry - 0.10], rightTemple],
  ];
  //@py 2521-2529
  const crown = reverse(at(edge, templeL)[1], pySlice(edge, templeL + 1, templeR + 1))[1];
  const k = 1.0 - CROP_FILL_INSET;
  const back: Segment[] = crown.map(([c, e]): Segment => [[c[0] * k, c[1] * k], [e[0] * k, e[1] * k]]);
  // The last end has to be the temple itself, not the pulled-in copy of it, so
  // the fill closes exactly where the fringe's stroke started.
  back[back.length - 1] = [at(back, -1)[0], leftTemple];
  return [leftTemple, line, back];
}

//@lead _crop_tip_edge
//@doc _crop_tip_edge
export function cropTipEdge(fall: number): Chain[] {
  //@py 2557-2557
  const lift = CROP_TONE_LIFT;
  const edge = 1.35 * v;
  const floor = fall + 1.5;
  const [sx, sy] = CROP_FRINGE_START;
  const [ex, ey] = at(CROP_FRINGE, -1)[1];
  return [
    [
      [-edge, sy - lift],
      [
        [[(-edge + sx) / 2, sy - lift], [sx, sy - lift]],
        ...CROP_FRINGE.map(([c, e]): Segment => [[c[0], c[1] - lift], [e[0], e[1] - lift]]),
        [[(ex + edge) / 2, ey - lift], [edge, ey - lift]],
        [[edge, floor * 0.6], [edge, floor]],
        [[0.0, floor], [-edge, floor]],
      ],
    ],
  ];
}

//@lead _crop_strands
//@doc _crop_strands
export function cropStrands(fall: number): Chain[] {
  //@py 2584-2585
  for (const [x, y] of CROP_NOTCHES) {
    //@comments 2587-2589
    const top: Point = [x + CROP_SWEEP, y - CROP_STRAND_RUN];
    out.push([[x, y], [[[(x + top[0]) / 2 + CROP_SWEEP * 0.5, (y + top[1]) / 2], top]]]);
  }
  //@py 2592-2593
  for (const [x0, y0, x1, y1] of [
    [-0.62, -0.72, -1.00, -0.24],
    [0.70, -0.70, 1.04, -0.22],
  ] as const) {
    out.push([
      [x0 * v, y0 * v],
      [[[((x0 + x1) / 2) * v, ((y0 + y1) / 2) * v], [x1 * v, y1 * v]]],
    ]);
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------------
// Satoshi's tousled crop

//@lead _tousle_side
//@doc _tousle_side
export function tousleSide(tip: number): Segment[] {
  //@py 2657-2661
}

//@lead _polar
export function polar(deg: number, radius: number): Point {
  const a = radians(deg);
  return [radius * pySin(a), -radius * pyCos(a)];
}

//@lead _chain
export function chain(start: Point, points: readonly Point[]): Segment[] {
  const segments: Segment[] = [];
  let prev = start;
  for (const q of points) {
    segments.push(straight(prev, q));
    prev = q;
  }
  return segments;
}

//@lead _tousle_mass_shape
//@doc _tousle_mass_shape
export function tousleMassShape(tip: number): Chain {
  const leftSide = tousleSide(tip).map(([c, e]): Segment => [mirrorPt(c), mirrorPt(e)]);
  const leftTemple: Point = [-TOUSLE_TEMPLE[0], TOUSLE_TEMPLE[1]];
  return [
    leftTemple,
    [
      ...chain(leftTemple, TOUSLE_CROWN.map(([d, r]) => polar(d, r))),
      straight(polar(...at(TOUSLE_CROWN, -1)), TOUSLE_TEMPLE),
      ...tousleSide(tip),
      //@items 2722-2730
      ...reverse(leftTemple, leftSide)[1],
    ],
  ];
}

//@lead _mirror_pt
export function mirrorPt(q: Point): Point {
  //@py 2736-2736
}

//@lead _tousle_fall_edge
//@doc _tousle_fall_edge
export function tousleFallEdge(tip: number): Chain {
  //@py 2742-2742
}

//@lead _tousle_hairline_shape
//@doc _tousle_hairline_shape
export function tousleHairlineShape(tip: number): Hairline {
  //@py 2754-2755
  //@comments 2756-2762
  const [, innerCrown] = arc(pyMinIter(TOUSLE_CROWN.map(([, r]) => r)) - 0.04, CROWN_TO_TEMPLE, -CROWN_TO_TEMPLE, 4);
  const back: Segment[] = [...rightEdge[1], ...innerCrown, ...leftDown[1]];
  const start: Point = at(back, -1)[1];
  //@py 2768-2777
}

//@lead _tousle_fringe_line
//@doc _tousle_fringe_line
export function tousleFringeLine(): Segment[] {
  const segments: Segment[] = [];
  TOUSLE_TIPS.forEach((point, i) => {
    const [left, right] = [TOUSLE_NOTCHES[i] as Point, TOUSLE_NOTCHES[i + 1] as Point];
    segments.push([lerp(left, point, 0.55), point]);
    segments.push([lerp(right, point, 0.55), right]);
  });
  return segments;
}

//@lead _tousle_tip_edge
//@doc _tousle_tip_edge
export function tousleTipEdge(tip: number): Chain[] {
  const regions: Chain[] = [];
  TOUSLE_TIPS.forEach((point, i) => {
    const [left, right] = [TOUSLE_NOTCHES[i] as Point, TOUSLE_NOTCHES[i + 1] as Point];
    //@comments 2804-2812
    const a: Point = [left[0], left[1] + (point[1] - left[1]) * (1.0 - HAIR_FADE)];
    const b: Point = [right[0], right[1] + (point[1] - right[1]) * (1.0 - HAIR_FADE)];
    //@comments 2815-2815
    const far = lerp(lerp(left, right, 0.5), point, 1.35);
    //@comments 2817-2817
    regions.push([a, [[lerp(a, b, 0.5), b], [lerp(b, far, 0.5), far], [lerp(far, a, 0.5), a]]]);
  });
  //@comments 2828-2829
  const floor = tip + 1.5;
  regions.push(
    //@items 2832-2841
  );
  return regions;
}

//@lead _tousle_strands
//@doc _tousle_strands
export function tousleStrands(tip: number): Chain[] {
  //@py 2855-2864
}

// ---------------------------------------------------------------------------------------------------------
// Risa's fringed cut

//@lead _fringed
//@doc _fringed
export function fringed(chain: Chain, fall: number): Chain {
  const q = fallQ(fall, FRINGED_BASE_TIP);
  const [start, segs] = chain;
  return [q(start), segs.map(([c, e]): Segment => [q(c), q(e)])];
}

//@lead _fringed_mass
export function fringedMass(fall: number): Chain {
  return fringed(FRINGED_MASS, fall);
}

//@lead _fringed_hairline
//@doc _fringed_hairline
export function fringedHairline(fall: number): Hairline {
  const [start, line] = fringed(FRINGED_FRONT, fall);
  return [start, line, []];
}

//@lead _fringed_fall_edge
export function fringedFallEdge(fall: number): Chain[] {
  return [];
}

//@lead _fringed_tip_edge
export function fringedTipEdge(fall: number): Chain[] {
  return [fringedMass(fall)];
}

//@lead _fringed_strands
export function fringedStrands(fall: number): Chain[] {
  return FRINGED_STRANDS.map((c) => fringed(c, fall));
}

//@lead _fringed_locks
export function fringedLocks(fall: number): Lock[] {
  const q = fallQ(fall, FRINGED_BASE_TIP);
  return FRINGED_LOCKS.map(([role, pts, w, ln]): Lock => [role, pts.map(q), w, ln]);
}

//@lead _fringed_underside
export function fringedUnderside(fall: number): readonly [Chain, readonly Chain[]] {
  return [fringed(FRINGED_UNDERSIDE, fall), []];
}

//@lead _fringed_openings
export function fringedOpenings(fall: number): Chain[] {
  return FRINGED_OPENINGS.map((c) => fringed(c, fall));
}

//@lead _fringed_shade
export function fringedShade(fall: number): Chain[] {
  return FRINGED_SHADE.map((c) => fringed(c, fall));
}

