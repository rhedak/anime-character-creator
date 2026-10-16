// The core-head module, part one: the helpers every cut shares (`fall`, `mirror`, `reverse`, `arc`), the long cut, the short
// layered cut, Satoko's traced cut with its clumps, and the parted cut. Port of character.py's hair block from `_fade_y`
// to `_parted_underside`. Generated once by harness/ts_port/gen_core_head.py from the Python (so no coordinate is typed),
// then owned by hand. Function names are the Python ones in camelCase, and every expression keeps Python's evaluation
// order, since a different order rounds differently. The tables are in core-head-tables.ts.

//@imports

/** `min(items)` and `max(items)` over an iterable: first of equal extremes wins, and an empty one raises as Python does. */
export function pyMinIter(items: readonly number[]): number {
  if (items.length === 0) throw new PyError("ValueError", "min() iterable argument is empty");
  return pyMin(items[0] as number, ...items.slice(1));
}
/** See `pyMinIter`. */
export function pyMaxIter(items: readonly number[]): number {
  if (items.length === 0) throw new PyError("ValueError", "max() iterable argument is empty");
  return pyMax(items[0] as number, ...items.slice(1));
}

/** A hairline: its start, the line drawn, and the edge that closes the front's fill back to the start. */
export type Hairline = readonly [Point, readonly Segment[], readonly Segment[]];

// ---------------------------------------------------------------------------------------------------------
// The shared helpers

//@lead _fade_y
//@doc _fade_y
export function fadeY(top: number, bottom: number): number {
  //@py 816-816
}

//@lead _fall
export function fall(f: number, length: number): number {
  //@py 828-828
}

//@lead _mirror
export function mirror(start: Point, segments: readonly Segment[]): Chain {
  const flip = (q: Point): Point => [-q[0], q[1]];
  return [flip(start), segments.map(([c, e]): Segment => [flip(c), flip(e)])];
}

//@lead _mirrored
//@doc _mirrored
export function mirrored(edge: Chain): Chain[] {
  //@py 844-844
}

//@lead _lerp
/**
 * `_lerp(a, b, f)` of character.py, on two points. skeleton.py has a `_lerp` of its own, on three numbers, and the call
 * recorder (and so `calls.test.ts`, which finds a function by its name alone) keeps both under the name `lerp`; so this one
 * also answers the scalar call, `a + (b - a) * t`, exactly as skeleton.py's does.
 */
export function lerp(a: number, b: number, t: number): number;
export function lerp(a: Point, b: Point, f: number): Point;
export function lerp(a: number | Point, b: number | Point, f: number): number | Point {
  if (typeof a === "number") return a + ((b as number) - a) * f;
  b = b as Point;
  //@py 2650-2650
}

//@lead _scale_point
//@doc _scale_point
export function scalePoint(pt: Point, k: number): Point {
  //@py 850-850
}

//@lead _reverse
//@doc _reverse
export function reverse(start: Point, segments: readonly Segment[]): Chain {
  const anchors = [start, ...segments.map(([, end]) => end)];
  const controls = segments.map(([ctrl]) => ctrl);
  const out: Segment[] = [];
  for (let i = controls.length - 1; i >= 0; i--) out.push([controls[i] as Point, anchors[i] as Point]);
  return [at(anchors, -1), out];
}

//@lead _arc
//@doc _arc
export function arc(r: number, fromDeg: number, toDeg: number, segments: number): Chain {
  const pt = (deg: number, radius: number): Point => {
    const a = radians(deg);
    return [radius * pySin(a), -radius * pyCos(a)];
  };

  const step = pyDiv(toDeg - fromDeg, segments);
  const ctrlR = pyDiv(r, pyCos(radians(step / 2)));
  const out: Segment[] = [];
  for (let i = 0; i < segments; i++) out.push([pt(fromDeg + step * (i + 0.5), ctrlR), pt(fromDeg + step * (i + 1), r)]);
  return [pt(fromDeg, r), out];
}

// ---------------------------------------------------------------------------------------------------------
// The long cut

//@lead _fall_edge
//@doc _fall_edge
export function fallEdge(length: number): Chain {
  const y = (f: number): number => fall(f, length);

  //@py 916-919
}

//@lead _hair_mass_shape
//@doc _hair_mass_shape
export function hairMassShape(length: number): Chain {
  const y = (f: number): number => fall(f, length);

  //@py 943-961
}

//@lead _hair_tip_edge
//@doc _hair_tip_edge
export function hairTipEdge(length: number): Chain[] {
  //@py 975-975

  //@py 977-980
  const hi = (d: number): number => fadeY(HAIR_CROWN_Y, length) - span * d;

  const lo = (d: number): number => fadeY(HAIR_CROWN_Y, length) + span * d;

  //@py 987-1006
}

//@lead _hairline_shape
//@doc _hairline_shape
export function hairlineShape(length: number): Hairline {
  const y = (f: number): number => fall(f, length);

  //@py 1025-1074
}

//@lead _long_strands
//@doc _long_strands
export function longStrands(length: number): Chain[] {
  const y = (f: number): number => fall(f, length);

  //@py 1088-1123
}

//@lead _center_part_hairline_shape
//@doc _center_part_hairline_shape
export function centerPartHairlineShape(length: number): Hairline {
  const y = (f: number): number => fall(f, length);

  //@py 1140-1166
}

//@lead _center_part_strands
//@doc _center_part_strands
export function centerPartStrands(length: number): Chain[] {
  const y = (f: number): number => fall(f, length);

  //@py 1178-1205
}

// ---------------------------------------------------------------------------------------------------------
// The short layered cut

//@lead _short_mass_shape
//@doc _short_mass_shape
export function shortMassShape(tip: number): Chain {
  //@py 1233-1250
}

//@lead _short_fall_edge
//@doc _short_fall_edge
export function shortFallEdge(tip: number): Chain {
  //@py 1257-1257
  const rightTemple = at(crown, -1)[1];
  //@py 1259-1264
}

//@lead _short_tip_edge
//@doc _short_tip_edge
export function shortTipEdge(tip: number): Chain[] {
  //@py 1286-1310
}

//@lead _short_hairline_shape
//@doc _short_hairline_shape
export function shortHairlineShape(tip: number): Hairline {
  //@py 1331-1339
  //@comments 1340-1341
  const start: Point = at(back, -1)[1];
  //@py 1343-1362
}

//@lead _short_strands
//@doc _short_strands
export function shortStrands(tip: number): Chain[] {
  //@py 1376-1396
}

// ---------------------------------------------------------------------------------------------------------
// Satoko's traced cut

//@lead _long_scaled
//@doc _long_scaled
export function longScaled(fall: number): Chain {
  const span = LONG_BASE_TIP - HAIR_CHEEK_Y;
  const k = truthy(span) ? pyDiv(fall - HAIR_CHEEK_Y, span) : 1.0;

  const q = (pt: Point): Point => {
    const y = pt[1];
    return y > HAIR_CHEEK_Y ? [pt[0], HAIR_CHEEK_Y + (y - HAIR_CHEEK_Y) * k] : pt;
  };

  return [q(LONG_EDGE_START), LONG_EDGE.map(([c, e]): Segment => [q(c), q(e)])];
}

//@lead _long_line
//@doc _long_line
export function longLine(fall: number): Chain {
  const span = LONG_BASE_TIP - HAIR_CHEEK_Y;
  const k = truthy(span) ? pyDiv(fall - HAIR_CHEEK_Y, span) : 1.0;

  const q = (pt: Point): Point => {
    const y = pt[1];
    return y > HAIR_CHEEK_Y ? [pt[0], HAIR_CHEEK_Y + (y - HAIR_CHEEK_Y) * k] : pt;
  };

  const line: Segment[] = LONG_LINE.map(([c, e]): Segment => [q(c), q(e)]);
  //@py 1506-1510
  const start: Point = [q(LONG_LINE_START)[0] + LONG_LINE_TUCK, q(LONG_LINE_START)[1]];
  const [ctrl, end] = at(line, -1);
  line[line.length - 1] = [ctrl, [end[0] - LONG_LINE_TUCK, end[1]]];
  return [start, line];
}

//@lead _long_traced_mass
//@doc _long_traced_mass
export function longTracedMass(fall: number): Chain {
  //@py 1519-1519
  const end = at(edge, -1)[1];
  //@py 1521-1521
}

//@lead _long_traced_fall_edge
//@doc _long_traced_fall_edge
export function longTracedFallEdge(fall: number): Chain[] {
  //@py 1528-1528
  return [
    reverse(at(edge, LONG_CROWN_AT)[1], pySlice(edge, LONG_CROWN_AT + 1)),
    [start, pySlice(edge, null, LONG_CROWN_AT + 1)],
  ];
}

//@lead _long_traced_hairline
//@doc _long_traced_hairline
export function longTracedHairline(fall: number): Hairline {
  //@py 1560-1561
  const end = at(hg, -1)[1];
  //@py 1563-1571
}

//@lead _long_traced_tip_edge
//@doc _long_traced_tip_edge
export function longTracedTipEdge(fall: number): Chain[] {
  //@py 1590-1591
}

//@lead _lifted_tip_edge
//@doc _lifted_tip_edge
export function liftedTipEdge(start: Point, edge: readonly Segment[], lift: number): Chain[] {
  const top = pyMinIter(edge.map(([, e]) => e[1]));
  const bottom = pyMaxIter(edge.map(([, e]) => e[1]));
  //@py 1602-1603
  const wide = pyMaxIter(edge.map(([, e]) => Math.abs(e[0]))) + 0.25;

  //@py 1606-1606
  const pts: Point[] = [];
  let prev = start;
  for (const [ctrl, end] of edge) {
    for (let i = 1; i < 7; i++) {
      const t = i / 6;
      // `x ** 2` is `x * x` here (the kernel's rule for an integer exponent).
      const x = (1 - t) * (1 - t) * prev[0] + 2 * (1 - t) * t * ctrl[0] + t * t * end[0];
      const y = (1 - t) * (1 - t) * prev[1] + 2 * (1 - t) * t * ctrl[1] + t * t * end[1];
      pts.push([x, pyMax(y - lift, fade)]);
    }
    prev = end;
  }

  const chain: Segment[] = [];
  let here: Point = [-wide, fade];
  const ring: Point[] = [...pts, [wide, fade], [wide, floor], [-wide, floor], [-wide, fade]];
  for (const q of ring) {
    chain.push([[(here[0] + q[0]) / 2, (here[1] + q[1]) / 2], q]);
    here = q;
  }
  return [[[-wide, fade], chain]];
}

// ---------------------------------------------------------------------------------------------------------
// The clumps the soft finish lays over the cuts (`Hairstyle.locks`)

//@lead _restretch_locks
//@doc _restretch_locks
export function restretchLocks(locks: readonly Lock[], authoredFall: number, fall: number): Lock[] {
  const k = pyDiv(fall - HAIR_CHEEK_Y, authoredFall - HAIR_CHEEK_Y);

  const q = (pt: Point): Point => {
    const y = pt[1];
    return y > HAIR_CHEEK_Y ? [pt[0], HAIR_CHEEK_Y + (y - HAIR_CHEEK_Y) * k] : pt;
  };

  return locks.map(([role, pts, w, ln]): Lock => [role, pts.map(q), w, ln]);
}

export function longTracedLocks(fall: number): Lock[] {
  return restretchLocks(LONG_LOCKS, LONG_LOCKS_FALL, fall);
}

export function shortLocks(fall: number): Lock[] {
  return [...SHORT_LOCKS];
}

export function cropLocks(fall: number): Lock[] {
  return [...CROP_LOCKS];
}

export function partedLocks(fall: number): Lock[] {
  return restretchLocks(PARTED_LOCKS, PARTED_LOCKS_FALL, fall);
}

//@lead _long_traced_strands
//@doc _long_traced_strands
export function longTracedStrands(fall: number): Chain[] {
  const v = fall / LONG_BASE_TIP;
  const out: Chain[] = [];
  for (const [x0, y0, cx0, cy0, x1, y1] of [
    [-0.30, -0.72, -0.62, -0.42, -0.86, -0.05],
    [0.34, -0.74, 0.66, -0.44, 0.90, -0.08],
  ] as const) {
    out.push([[x0, y0], [[[cx0, cy0], [x1, y1]]]]);
  }
  for (const side of [-1, 1]) {
    out.push([
      [side * 1.02 * v, 0.10 * v],
      [[[side * 1.10 * v, 0.70 * v], [side * 1.06 * v, 1.30 * v]]],
    ]);
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------------
// The parted cut

//@lead _fall_q
//@doc _fall_q
export function fallQ(fall: number, baseTip: number): (pt: Point) => Point {
  const span = baseTip - HAIR_CHEEK_Y;
  const k = pyDiv(fall - HAIR_CHEEK_Y, span);
  const kz = pyMin(1.0, pySqrt(k), 1.8 * k);
  const km = 2 * k - kz;

  const q = (pt: Point): Point => {
    const [x, y] = pt;
    const u = y - HAIR_CHEEK_Y;
    if (u <= 0) return pt;
    if (u <= span) return [x, HAIR_CHEEK_Y + km * u + pyDiv((kz - km) * u * u, 2 * span)];
    return [x, HAIR_CHEEK_Y + k * span + kz * (u - span)];
  };

  return q;
}

//@lead _parted_q
//@doc _parted_q
export function partedQ(fall: number): (pt: Point) => Point {
  return fallQ(fall, PARTED_BASE_TIP);
}

//@lead _parted
//@doc _parted
export function parted(chain: Chain, fall: number): Chain {
  const q = partedQ(fall);
  const [start, segs] = chain;
  return [q(start), segs.map(([c, e]): Segment => [q(c), q(e)])];
}

//@lead _anchor
//@doc _anchor
export function anchor(chain: Chain, i: number): Point {
  return i === 0 ? chain[0] : at(chain[1], i - 1)[1];
}

//@lead _sub_chain
//@doc _sub_chain
export function subChain(chain: Chain, a: number, b: number): Chain {
  return [anchor(chain, a), pySlice(chain[1], a, b)];
}

// character.py defines `_straight` twice (a bisecting-control one at line 1990 and this one, further down): Python binds the
// later one before any call, so only this one is ported.
//@lead _straight
//@doc _straight
export function straight(a: Point, b: Point): Segment {
  //@py 2701-2701
}

//@lead _parted_mass
//@doc _parted_mass
export function partedMass(fall: number): Chain {
  //@py 1997-1997
  const end = at(edge, -1)[1];
  //@py 1999-1999
}

//@lead _parted_hairline
//@doc _parted_hairline
export function partedHairline(fall: number): Hairline {
  //@py 2008-2012
  const back: Segment[] = [
    ...upRight,
    straight(at(upRight, -1)[1], qR),
    ...over,
    straight(at(over, -1)[1], lockL[0]),
    ...lockL[1],
  ];
  return [start, line, back];
}

//@lead _parted_fall_edge
//@doc _parted_fall_edge
export function partedFallEdge(fall: number): Chain[] {
  //@py 2027-2033
}

//@lead _parted_tip_edge
//@doc _parted_tip_edge
export function partedTipEdge(fall: number): Chain[] {
  let [start, edge] = parted(PARTED_EDGE, fall);

  const out = (pt: Point): Point => [pt[0] * PARTED_TONE_WIDEN, pt[1]];

  edge = edge.map(([c, e]): Segment => [out(c), out(e)]);
  return liftedTipEdge(out(start), edge, PARTED_TONE_LIFT * (fall / PARTED_BASE_TIP));
}

//@lead _parted_tip_lines
//@doc _parted_tip_lines
export function partedTipLines(fall: number): readonly [readonly (readonly [Point, Point])[], readonly (readonly [Point, Point])[]] {
  const q = partedQ(fall);

  const lines = (tips: readonly (readonly [Point, Point])[]): [Point, Point][] => {
    const out: [Point, Point][] = [];
    for (const [[ax, ay], [dx, dy]] of tips) {
      out.push([q([ax, ay]), q([ax + dx * HAIR_TIP_LINE, ay + dy * HAIR_TIP_LINE])]);
    }
    return out;
  };

  return [lines(PARTED_TIPS_BEHIND), lines(PARTED_TIPS_FRONT)];
}

//@lead _parted_underside
//@doc _parted_underside
export function partedUnderside(fall: number): readonly [Chain, readonly Chain[]] {
  const edge = parted(PARTED_EDGE, fall);
  const lines: Chain[] = [];
  const sides: [Chain, number][] = [];
  for (const [lock0, apex, under] of [
    [PARTED_LOCK_L, PARTED_APEX_L, PARTED_UNDER_L],
    [PARTED_LOCK_R, PARTED_APEX_R, PARTED_UNDER_R],
  ] as const) {
    const lock = parted(lock0, fall);
    const [uStart, uSegs] = parted(under, fall);
    const merge = anchor(lock, apex);
    lines.push([merge, [straight(merge, uStart), ...uSegs]]);
    sides.push([lock, apex]);
  }
  const [[lockL, apexL], [lockR, apexR]] = sides as [[Chain, number], [Chain, number]];
  const qL = anchor(edge, PARTED_SEAM_L + 1);
  const qR = anchor(edge, PARTED_SEAM_R + 1);
  const [tL, tR] = [lockL[0], lockR[0]];
  const far = pyMaxIter(edge[1].map(([, e]) => Math.abs(e[0]))) + 1.0;
  const top = pyMinIter(edge[1].map(([, e]) => e[1])) - 1.0;
  const floor = fall + 1.0;
  const lift = PARTED_SEAM_LIFT;

  //@comments 2097-2098
  const [downLStart, downL] = reverse(...(lines[0] as Chain));
  const [, upLockL] = reverse(...subChain(lockL, 0, apexL));
  const path: Segment[] = [...downL, ...upLockL];
  for (const q of [
    [tL[0], tL[1] - lift],
    [qL[0] - far, qL[1] - lift],
    [-far, top],
    [far, top],
    [qR[0] + far, qR[1] - lift],
    [tR[0], tR[1] - lift],
    tR,
  ] as Point[]) {
    path.push(straight(at(path, -1)[1], q));
  }
  path.push(...subChain(lockR, 0, apexR)[1]);
  path.push(...(lines[1] as Chain)[1]);
  const end = at(path, -1)[1];
  for (const q of [[end[0], floor], [downLStart[0], floor], downLStart] as Point[]) {
    path.push(straight(at(path, -1)[1], q));
  }
  return [[downLStart, path], lines];
}

