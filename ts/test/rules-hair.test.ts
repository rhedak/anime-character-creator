// Rules over the family of hairstyles and the parts worn on or beside hair: the hair and ear tests of tests/test_smoke.py.
// These are authoring guards. A new cut that breaks one wants its own geometry or the canvas headroom (`hair_margin`)
// fixed, not the rule loosened.

import assert from "node:assert/strict";
import { test } from "node:test";
import { HAIRSTYLES, hairEdgeX, hairFall, headEdgeX } from "../src/core-head.ts";
import { skeletonFor } from "../src/body.ts";
import { strokeW } from "../src/character.ts";
import { replace } from "../src/model.ts";
import type { CharacterParams } from "../src/params.ts";
import { PRESETS } from "../src/presets.ts";
import { SCARF_EDGE_Y } from "../src/props-tables.ts";
import { headscarf } from "../src/props.ts";
import { earOuter } from "../src/face.ts";
import { BUILDS, buildSkeletonWith } from "../src/skeleton.ts";
import type { Point, Segment } from "../src/tables.ts";
import { make, walk } from "./rules-util.ts";

// The swept ponytail is the adult body's cut: its front piece is drawn by `adultHairFront` from its mass (body-adult-hair.ts), not through the five-callable contract these rules walk,
// so it is not in the family; ts/test/adult-body.test.ts covers it.
const HAIRSTYLE_NAMES = Object.keys(HAIRSTYLES).filter((n) => n !== "swept_ponytail").sort();

test("there are eight hairstyles, the family the Python parametrisations were sized against", () => {
  assert.equal(HAIRSTYLE_NAMES.length, 8);
});

test("test_the_ear_stays_welded_to_the_skull", () => {
  // The ear's outer contour has to stay outside the skull it grows off. The ear is drawn under the head, so the only
  // part of it anyone ever sees is the part outside the skull; any stretch inside is painted over and simply is not there.
  const sk = buildSkeletonWith({ heads: BUILDS.chibi as number });
  const [start, segments] = earOuter(sk.build);
  let prev = start;
  for (const [ctrl, end] of segments) {
    for (let i = 1; i < 21; i++) {
      const t = i / 21;
      const x = (1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * ctrl[0] + t ** 2 * end[0];
      const y = (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * ctrl[1] + t ** 2 * end[1];
      const skull = headEdgeX(y, sk.build);
      assert.ok(x >= skull - 1e-9, `the ear dips ${(skull - x).toFixed(3)} head radii inside the skull at y=${y.toFixed(3)}; it would cut a line across the cheek`);
    }
    prev = end;
  }
});

for (const hairstyle of HAIRSTYLE_NAMES) {
  test(`test_the_front_hair_adds_no_silhouette[${hairstyle}]`, () => {
    // The mass carries the whole outer contour, and no other piece may cross it. The hairline's closing edge is a fill
    // boundary, never stroked, so when it strays outside the mass there is no line to give it away. A point passes if it
    // is inside the mass or within a hair's breadth of its outline. The mass is sampled at 150 points a segment so the
    // polygon's chords do not cut the corner off the curves they stand in for.
    const p = make({ hairstyle });
    const sk = skeletonFor(p);
    const fall = hairFall(sk, p);
    const style = HAIRSTYLES[hairstyle]!;
    const [mStart, mSegs] = style.mass(fall);
    const poly = walk(mStart, mSegs, 150);
    const edges: [Point, Point][] = poly.map((a, i) => [a, poly[(i + 1) % poly.length] as Point]);

    const inside = (px: number, py: number): boolean => {
      let hit = false;
      for (const [[ax, ay], [bx, by]] of edges) {
        if (ay > py !== by > py && px < ax + ((py - ay) / (by - ay)) * (bx - ax)) hit = !hit;
      }
      return hit;
    };
    const gap = (px: number, py: number): number => {
      let best = 9.9;
      for (const [[ax, ay], [bx, by]] of edges) {
        const [dx, dy] = [bx - ax, by - ay];
        const n = dx * dx + dy * dy;
        const t = n === 0 ? 0.0 : Math.max(0.0, Math.min(1.0, ((px - ax) * dx + (py - ay) * dy) / n));
        best = Math.min(best, Math.hypot(px - (ax + t * dx), py - (ay + t * dy)));
      }
      return best;
    };

    const [, line, back] = style.hairline(fall);
    const lastEnd = (line[line.length - 1] as Segment)[1];
    const closing = walk(lastEnd, back, 10);
    for (const [x, y] of closing) {
      assert.ok(inside(x, y) || gap(x, y) <= 0.006, `${hairstyle}: the hairline's closing edge reaches (${x.toFixed(3)}, ${y.toFixed(3)}), ${gap(x, y).toFixed(3)} head radii outside the mass, so the fill paints past its own outline with no stroke to show it`);
    }
  });
}

/** The topmost y a quadratic chain reaches. Not the topmost anchor and not the topmost control point: each segment is solved for its own extremum. */
function highestInk(start: Point, segments: readonly Segment[]): number {
  const ys = [start[1]];
  let prev = start;
  for (const [ctrl, end] of segments) {
    ys.push(end[1]);
    const [a, b, c] = [prev[1], ctrl[1], end[1]];
    const denom = a - 2 * b + c;
    if (denom !== 0) {
      const t = (a - b) / denom;
      if (0 < t && t < 1) ys.push((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t ** 2 * c);
    }
    prev = end;
  }
  return Math.min(...ys);
}

for (const hairstyle of HAIRSTYLE_NAMES) {
  test(`test_hair_stays_under_the_canvas_ceiling[${hairstyle}]`, () => {
    // A crown taller than the headroom comes out sliced flat, silently. A new hairstyle that fails here wants
    // `hair_margin` raised with it, not its crown flattened to fit.
    const p = make({ hairstyle });
    const sk = skeletonFor(p);
    const [start, segs] = HAIRSTYLES[hairstyle]!.mass(hairFall(sk, p));
    const topUnits = highestInk(start, segs);
    // The stroke straddles the path, so half of it paints above the curve.
    const inkY = sk.head_cy + sk.head_r * topUnits - strokeW(sk) / 2;
    assert.ok(inkY >= 0, `${hairstyle} paints ${-inkY}px above the canvas and is being sliced flat; raise hair_margin in build_skeleton`);
  });
}

for (const hairstyle of HAIRSTYLE_NAMES) {
  test(`test_the_cap_covers_the_hair_it_is_tied_over[${hairstyle}]`, () => {
    // The cloth has to be at least as wide as the cut under it. Read off the drawn arc rather than off the constant, so
    // it fails if the width goes back to being taken from the skull's edge, the specific regression worth catching.
    const p = replace(PRESETS.chiyo as CharacterParams, { hairstyle });
    const sk = skeletonFor(p);
    const d = /d="([^"]+)"/.exec(headscarf(sk, p))?.[1] as string;
    const rx = Number(/A ([\d.]+) /.exec(d)?.[1]) / sk.head_r;
    const hair = hairEdgeX(SCARF_EDGE_Y, sk, p);
    assert.ok(rx >= hair, `the cap is ${rx.toFixed(3)} head radii wide over ${hairstyle} hair that is ${hair.toFixed(3)} wide, so the cut stands outside the cloth tied over it`);
    // And still on the canvas. The dome grows with the hair, so a longer or fuller cut moves it.
    assert.ok(sk.head_cx + rx * sk.head_r <= 400, `the cap runs off the canvas at ${rx.toFixed(3)}`);
  });
}
