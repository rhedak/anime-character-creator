// Straightening a traced head cut (docs/risa-adult-plan.md, "Her face made straight"). Risa's reference has her head tilted and turned a little: her right eye is 12 px above her left, and
// her chin sits right of the line through her eyes. A character that emotes needs a face whose two sides are the same, so her cut is built from the traced one: the eyes level about a
// midline, the left brow mirrored for the right, and the jaw made symmetric about the midline. Chains are in head radii about the head's centre (reference pixels over 175.7, from the
// calibration origin (660, 270.5)); the functions here take and return them.

import type { Chain } from "./tables.ts";

type Pt = readonly [number, number];

const ORIGIN_X = 660;
const ORIGIN_Y = 270.5;
const R = 175.7;
/** A point in reference pixels to head radii, and back. */
export const toRadii = ([x, y]: Pt): [number, number] => [(x - ORIGIN_X) / R, (y - ORIGIN_Y) / R];
const toPx = ([x, y]: Pt): [number, number] => [ORIGIN_X + x * R, ORIGIN_Y + y * R];

/** A chain moved by (dx, dy) reference pixels. */
export function shiftChain([start, segs]: Chain, dx: number, dy: number): Chain {
  const [rx, ry] = [dx / R, dy / R];
  const mv = (q: Pt): [number, number] => [q[0] + rx, q[1] + ry];
  return [mv(start), segs.map(([c, e]) => [mv(c), mv(e)] as [Pt, Pt])];
}

/** A chain mirrored about the vertical line at reference x `mid`, and walked from the other end so it still runs left to right. Its per-point `widths` are reversed the same way. */
export function mirrorChain([start, segs]: Chain, mid: number, widths?: readonly number[]): { chain: Chain; widths: readonly number[] | undefined } {
  const m = (q: Pt): [number, number] => [2 * ((mid - ORIGIN_X) / R) - q[0], q[1]];
  const points: [number, number][] = [m(start), ...segs.flatMap(([c, e]) => [m(c), m(e)])];
  const back = [...points].reverse();
  const first = back[0] as [number, number];
  const rest: [Pt, Pt][] = [];
  for (let i = 1; i + 1 < back.length; i += 2) rest.push([back[i] as Pt, back[i + 1] as Pt]);
  return { chain: [first, rest], widths: widths === undefined ? undefined : [...widths].reverse() };
}

/**
 * A closed face contour made symmetric about the vertical line at reference x `mid` from `y0` down: at each row below it the two edges are put the same distance either side of the line (half
 * the traced width), blended in over `ramp` pixels so the contour above (the hairline, which the hair decides and not the face) is as traced. The chin is then on the line. The result is
 * straight-edged quadratics a pixel or so long.
 */
export function symmetricJaw(chain: Chain, mid: number, y0: number, ramp: number): Chain {
  const [start, segs] = chain;
  const pts = [start, ...segs.map(([, e]) => e)].map(toPx);
  let i1 = pts.findIndex((p) => p[1] >= y0);
  let i2 = pts.length - 1;
  while (i2 > 0 && (pts[i2] as Pt)[1] < y0) i2--;
  if (i1 < 1 || i2 <= i1) return chain;
  const crossings = (y: number): number[] => {
    const xs: number[] = [];
    for (let i = 0; i + 1 < pts.length; i++) {
      const [p, q] = [pts[i] as Pt, pts[i + 1] as Pt];
      if (p[1] !== q[1] && (p[1] - y) * (q[1] - y) <= 0) xs.push(p[0] + ((q[0] - p[0]) * (y - p[1])) / (q[1] - p[1]));
    }
    return xs;
  };
  const yMax = Math.max(...pts.map((p) => p[1]));
  const rows: { y: number; l: number; r: number }[] = [];
  const N = 80;
  for (let k = 0; k <= N; k++) {
    const t = k / N;
    const y = y0 + (yMax - y0) * (1 - (1 - t) ** 3);
    const xs = crossings(Math.min(y, yMax - 1e-6));
    const [lo, hi] = [Math.min(...xs), Math.max(...xs)];
    const hw = k === N ? 0 : (hi - lo) / 2;
    const w = Math.min(1, Math.max(0, (y - y0) / ramp));
    const s = w * w * (3 - 2 * w);
    rows.push({ y, l: lo + s * (mid - hw - lo), r: hi + s * (mid + hw - hi) });
  }
  rows[N] = { y: yMax, l: mid, r: mid };
  // the chain goes down whichever side it reaches first (Risa's runs down the viewer's right)
  const downRight = (pts[i1] as Pt)[0] > mid;
  const [down, up] = downRight ? [(q: (typeof rows)[number]) => q.r, (q: (typeof rows)[number]) => q.l] : [(q: (typeof rows)[number]) => q.l, (q: (typeof rows)[number]) => q.r];
  const jaw: [number, number][] = [...rows.map((q): [number, number] => [down(q), q.y]), ...[...rows].reverse().slice(1).map((q): [number, number] => [up(q), q.y])];
  const all: [number, number][] = [...pts.slice(0, i1), ...jaw, ...pts.slice(i2 + 1)];
  const rad = all.map(toRadii);
  const mids = rad.slice(1).map((e, i): [Pt, Pt] => [[((rad[i] as Pt)[0] + e[0]) / 2, ((rad[i] as Pt)[1] + e[1]) / 2], e]);
  return [rad[0] as [number, number], mids];
}
