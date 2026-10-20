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

test("an arm at 0, or below six degrees, hangs: the drawing is the default one", () => {
  const rest = draw(BARE);
  assert.equal(draw(pose({ right_arm_out: 0 })), rest);
  assert.equal(draw(pose({ right_arm_out: 0.4, left_arm_out: -30 })), rest);
  assert.equal(draw(pose({ right_arm_out: 5.9, left_arm_out: 3 })), rest, "a separate arm turned a few degrees left a sliver of page beside the ribs");
  assert.notEqual(draw(pose({ right_arm_out: 6 })), rest);
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
});

test("a hanging arm is a fist too when grip_style says so: the traced fist is in the body outline, with its nails and finger separations drawn over it, and a hanging arm is the same below six degrees", () => {
  const relaxed = draw(BARE);
  const fist = draw(pose({ grip_style: "fist" }));
  assert.notEqual(fist, relaxed);
  assert.equal(draw(pose({ grip_style: "fist", right_arm_out: 4, left_arm_out: 5 })), fist);
  const outline = (svg: string): string => (svg.match(/<path id="adult-body-outline" d="([^"]+)"/) ?? [])[1]!;
  assert.notEqual(outline(fist), outline(relaxed), "the fist's outline replaces the relaxed hand's in the body's path");
  // the same default as the relaxed hand: grip_style at its default, or anything but "fist", leaves the relaxed hand
  assert.equal(draw(pose({ grip_style: "mitten" })), relaxed);
  assert.equal(draw(pose({ grip_style: "fist" }, FRANZI)).includes('id="adult-hand-body"'), true);
});

test("the viewer's-right arm is the mirror image of the viewer's-left one, point for point: the hand is walked the same way on both sides (it was once walked backwards, which drew a jump across the wrist)", () => {
  const edge = (svg: string, tag: string): number[] => [...((svg.match(new RegExp(`<path id="adult-pose-${tag}-edge" d="([^"]+)"`)) ?? [])[1] ?? "").matchAll(/-?\d+(?:\.\d+)?/g)].map((m) => Number(m[0]));
  for (const grip of ["mitten", "fist"]) {
    const svg = draw(pose({ right_arm_out: 110, left_arm_out: 110, grip_style: grip }));
    const l = edge(svg, "l");
    const r = edge(svg, "r");
    assert.ok(l.length > 200 && l.length === r.length, `${grip}: both arms have the same path (${l.length} and ${r.length} numbers)`);
    for (let i = 0; i + 1 < l.length; i += 2) {
      assert.ok(Math.abs((r[i] as number) - (400 - (l[i] as number))) < 0.25 && Math.abs((r[i + 1] as number) - (l[i + 1] as number)) < 0.25, `${grip}: point ${i / 2} is not the mirror of the other side's`);
    }
  }
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

test("the hands go in front of the skirt and the apron: a hanging fist is drawn again after them, and so is a raised arm's hand", () => {
  const skin = "#ffd0b5";
  const after = (svg: string, from: string): string => svg.slice(svg.indexOf(from));
  // a hanging fist: the traced outline filled with skin, once for each hand, after the apron's sash (the last of the dirndl's skirt layers)
  const fist = draw(pose({ grip_style: "fist" }, FRANZI));
  const overlays = (svg: string): number => (svg.match(new RegExp(`<path d="M [^"]+Z" fill="${skin}" />`, "g")) ?? []).length;
  assert.ok(fist.includes('id="adult-apron-sash"'));
  assert.equal(overlays(after(fist, 'id="adult-apron-sash"')), 2, "both fists are drawn after the apron");
  assert.equal(overlays(after(draw(FRANZI), 'id="adult-apron-sash"')), 0, "the relaxed hand keeps its zone redraw and adds no overlay");
  // a raised arm's hand, below the wrist, is drawn again after the apron too (a hand at 15 degrees hangs over the skirt)
  const raised = draw(pose({ right_arm_out: 15, grip_style: "fist" }, FRANZI));
  assert.ok(after(raised, 'id="adult-apron-sash"').includes(`<use href="#adult-pose-l-edge" fill="${skin}" stroke="none" clip-path="url(#adult-pose-l-hand)"`));
});

test("with a blouse a raised arm gets a sleeve head over the shoulder, so the sleeve does not read as a cutout; without a blouse it does not", () => {
  const dressed = draw(pose({ right_arm_out: 110, left_arm_out: 110 }, FRANZI));
  for (const tag of ["l", "r"]) {
    assert.ok(dressed.includes(`id="adult-pose-${tag}-head-clip"`), `${tag}: a clip to the body and the arm`);
    assert.ok(dressed.includes(`<clipPath id="adult-pose-${tag}-head-clip"><use href="#adult-body-outline" /><use href="#adult-pose-${tag}-edge"`), `${tag}: the clip is the body without its arm and the arm`);
  }
  // the head's cloth is the blouse's colour, and it is drawn in the torso layer, before the blouse's own pieces
  assert.ok(dressed.indexOf('id="adult-pose-l-head-clip"') < dressed.indexOf('id="adult-blouse-body"'));
  assert.ok(dressed.includes(`fill="#faf6f5" /></g>`), "the head is filled with the blouse's colour");
  // one raised arm, one head
  assert.ok(draw(pose({ right_arm_out: 110 }, FRANZI)).includes('id="adult-pose-l-head-clip"') && !draw(pose({ right_arm_out: 110 }, FRANZI)).includes('id="adult-pose-r-head-clip"'));
  // bare arms (no blouse) have none; neither does a hanging arm
  assert.ok(!draw(pose({ right_arm_out: 110 })).includes("-head-clip"));
  assert.ok(!draw(FRANZI).includes("-head-clip"));
});
