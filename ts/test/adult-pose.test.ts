// Raised arms on the adult woman (docs/franzi-expressions-plan.md, steps 3 and 4): the companion sends `right_arm_out` and `left_arm_out`, an arm is raised by turning the hanging arm about
// the shoulder, and the hand is the traced open palm or, with `grip_style` "fist", the fist. At 0 (the default) nothing changes, which the baseline test pins byte for byte.

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";
import { adultArmPoses } from "../src/body-adult-pose.ts";
import { HAND_FIST_OUTLINE, HAND_OPEN_OUTLINE } from "../src/body-adult-hand-poses-data.ts";
import { HAND_D_CUT } from "../src/body-adult-hand-data.ts";
import { characterParams, outfit } from "../src/model.ts";
import { FRANZI } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

/** Franzi in her underwear alone: no sleeve is in the way of a raised arm. */
const BARE = characterParams({ ...FRANZI, outfit: outfit({ ...FRANZI.outfit, tunic_color: null, bodice_color: null, skirt_color: null, apron_color: null }) });
const pose = (o: Record<string, unknown>, base = BARE) => characterParams({ ...base, ...o });
const draw = (p: ReturnType<typeof pose>): string => renderCharacter(p, null, null, false);
const sha = (s: string): string => createHash("sha256").update(s).digest("hex");
const turns = (svg: string): number[] => [...svg.matchAll(/<g transform="rotate\((-?\d+(?:\.\d+)?) /g)].map((m) => Number(m[1]));
const ids = (svg: string): string[] => [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);

test("an arm at 0, or below a degree, hangs: the drawing is the default one", () => {
  const rest = draw(BARE);
  assert.equal(draw(pose({ right_arm_out: 0 })), rest);
  assert.equal(draw(pose({ right_arm_out: 0.4, left_arm_out: -30 })), rest);
  assert.deepEqual(adultArmPoses(BARE), []);
});

test("a raised arm turns the hanging arm about the shoulder: the viewer's-left arm clockwise, the right one the other way, by the angle sent", () => {
  assert.deepEqual(turns(draw(pose({ right_arm_out: 130 }))).slice(0, 1), [130]);
  assert.deepEqual(turns(draw(pose({ left_arm_out: 130 }))).slice(0, 1), [-130]);
  const both = turns(draw(pose({ right_arm_out: 125, left_arm_out: 150 })));
  assert.ok(both.includes(125) && both.includes(-150), `both arms: ${both.join(", ")}`);
  assert.equal(turns(draw(pose({ right_arm_out: 400 }))).slice(0, 1)[0], 180, "straight up is the furthest");
});

test("raising an arm changes only its side: the other arm's hand, the legs and the head are drawn as before", () => {
  const rest = draw(BARE);
  const up = draw(pose({ right_arm_out: 130 }));
  assert.notEqual(up, rest);
  assert.ok(up.length > rest.length - 20000 && up.length < rest.length + 40000, "about the same size");
  // the body's outline is defined once and now has no viewer's-left arm, so it is shorter; the left side's arm would have carried the hand's several hundred segments
  const outline = (svg: string): number => (svg.match(/<path id="adult-body-outline" d="([^"]+)"/) ?? [])[1]!.length;
  assert.ok(outline(up) < outline(rest) - 2000, "the outline lost the arm and its hand");
  const both = draw(pose({ right_arm_out: 130, left_arm_out: 130 }));
  assert.ok(outline(both) < outline(up) - 2000, "and the other arm's too");
});

test("the hand is the open palm, or the fist with grip_style fist, and each is its own picture", () => {
  const open = draw(pose({ right_arm_out: 130 }));
  const fist = draw(pose({ right_arm_out: 130, grip_style: "fist" }));
  assert.notEqual(open, fist);
  assert.equal(adultArmPoses(pose({ right_arm_out: 130 }))[0]!.hand, "open");
  assert.equal(adultArmPoses(pose({ right_arm_out: 130, grip_style: "fist" }))[0]!.hand, "fist");
  assert.equal(adultArmPoses(pose({ left_arm_out: 130, grip_style: "mitten" }))[0]!.hand, "open");
  // a hanging arm's hand does not change with it: the fist grip is for a raised arm
  assert.equal(draw(pose({ grip_style: "fist" })), draw(BARE));
});

test("ids stay unique and every reference resolves with raised arms, both hands, one or both arms, in both finishes", () => {
  for (const finish of ["flat", "soft"] as const) {
    for (const o of [{ right_arm_out: 130 }, { left_arm_out: 90, grip_style: "fist" }, { right_arm_out: 125, left_arm_out: 150, grip_style: "fist" }, { right_arm_out: 40, left_arm_out: 40 }]) {
      const svg = draw(pose({ ...o, finish }));
      const defined = ids(svg);
      assert.equal(new Set(defined).size, defined.length, `${JSON.stringify(o)} ${finish}: an id is defined twice`);
      for (const u of [...svg.matchAll(/url\(#([^)]+)\)/g), ...svg.matchAll(/href="#([^"]+)"/g)].map((m) => m[1] as string)) assert.ok(defined.includes(u), `${JSON.stringify(o)} ${finish}: ${u} is used and never defined`);
    }
  }
});

test("a raised arm keeps her SVG small", () => {
  assert.ok(draw(pose({ right_arm_out: 125, left_arm_out: 125, grip_style: "fist" })).length < 400_000);
});

test("the traced hands: an open chain from the wrist cut round the fingers back to it, about as long as the relaxed hand", () => {
  for (const [name, chain, lowest] of [["open", HAND_OPEN_OUTLINE, 2.53], ["fist", HAND_FIST_OUTLINE, 2.45]] as const) {
    const [start, segs] = chain;
    assert.equal(start[1], HAND_D_CUT, `${name} starts at the wrist cut`);
    assert.equal(segs[segs.length - 1]![1][1], HAND_D_CUT, `${name} ends at the wrist cut`);
    const d = [start[1], ...segs.map(([, e]) => e[1])];
    assert.ok(Math.abs(Math.max(...d) - lowest) < 0.02, `${name}: lowest point ${Math.max(...d)}`);
    assert.ok(start[0] > segs[segs.length - 1]![1][0], `${name}: the outer edge is first, so it is farther from the centre line than the inner`);
  }
});

test("the dirndl's blouse sleeve goes up with the arm: the blouse is split along the seam and the sleeve is turned by the same transform as the arm", () => {
  const down = draw(FRANZI);
  const up = draw(pose({ right_arm_out: 130 }, FRANZI));
  assert.notEqual(up, down);
  assert.deepEqual(adultArmPoses(pose({ right_arm_out: 130 }, FRANZI)).map((a) => a.sign), [-1], "a blouse is no reason to keep an arm down");
  // the arm's own group and the blouse's sleeve group carry the same turn
  const t = turns(up);
  assert.ok(t.length >= 2 && t.every((v) => v === 130), `the arm and the sleeve turn together: ${t.join(", ")}`);
  assert.ok(up.includes('id="adult-blouse-body"') && up.includes('id="adult-blouse-sleeve-l"') && !up.includes('id="adult-blouse-sleeve-r"'), "a body piece and the raised side's sleeve");
  const both = draw(pose({ right_arm_out: 125, left_arm_out: 125, grip_style: "fist" }, FRANZI));
  assert.ok(both.includes('id="adult-blouse-sleeve-l"') && both.includes('id="adult-blouse-sleeve-r"'));
  // with no arm raised the blouse is the one piece it was: her dirndl is her v0.5.0 dirndl
  assert.equal(sha(down), "0f61e4d3f85303f57a4c26c9be2c36525210c32063331162e50c7b7d98f76890");
  assert.ok(!down.includes("adult-blouse-body"));
});

test("the dirndl with raised arms keeps unique ids and resolved references in both finishes, and a tucked blouse (a skirt is worn) splits the same way", () => {
  for (const finish of ["flat", "soft"] as const) {
    for (const o of [{ right_arm_out: 130 }, { right_arm_out: 125, left_arm_out: 150, grip_style: "fist" }, { left_arm_out: 90 }]) {
      const svg = draw(pose({ ...o, finish }, FRANZI));
      const defined = ids(svg);
      assert.equal(new Set(defined).size, defined.length, `${JSON.stringify(o)} ${finish}: an id is defined twice`);
      for (const u of [...svg.matchAll(/url\(#([^)]+)\)/g), ...svg.matchAll(/href="#([^"]+)"/g)].map((m) => m[1] as string)) assert.ok(defined.includes(u), `${JSON.stringify(o)} ${finish}: ${u} is used and never defined`);
    }
  }
  // not tucked: a blouse over trousers, drawn in the chest layers
  const loose = characterParams({ ...FRANZI, right_arm_out: 130, outfit: outfit({ ...FRANZI.outfit, bodice_color: null, skirt_color: null, apron_color: null, tunic_color: "#faf6f5", trouser_color: "#6b5a44" }) });
  assert.ok(draw(loose).includes('id="adult-blouse-sleeve-l"'));
});

test("while a coat or a robe is worn the arms stay down, whatever the angle (their sleeves are cut for the hanging arm)", () => {
  for (const o of [{ coat_color: "#444444" }, { robe_color: "#553366" }]) {
    const dressed = characterParams({ ...BARE, right_arm_out: 130, outfit: outfit({ ...BARE.outfit, ...o }) });
    assert.deepEqual(adultArmPoses(dressed), [], JSON.stringify(o));
    assert.equal(draw(dressed), draw(characterParams({ ...dressed, right_arm_out: 0 })));
  }
});
