// Rules over garments, the always-worn underwear and the figure's bare parts: the garment tests of tests/test_smoke.py that
// a differential oracle cannot say (a tone gap between two layers, a hem that must have height, a fill rule, a hostile
// string). The base layer rule of CLAUDE.md applies throughout: whatever is switched off, the underwear stays.

import assert from "node:assert/strict";
import { test } from "node:test";
import { skeletonFor } from "../src/body.ts";
import { strokeW } from "../src/character.ts";
import { armLine, drawCut, limbBuild } from "../src/core-limbs.ts";
import { hand } from "../src/core-limbs-hands.ts";
import { garmentCut } from "../src/core-limbs-tables.ts";
import { crotchY } from "../src/body-parts-legs.ts";
import { FIELDS, outfit, replace } from "../src/model.ts";
import type { CharacterParams, Outfit } from "../src/params.ts";
import { PRESETS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";
import type { Chain } from "../src/tables.ts";
import { PRESET_NAMES, numbersIn, withOutfit } from "./rules-util.ts";
import { fromstring, iterNodes, itertext } from "./svg-scan.ts";

const preset = (name: string): CharacterParams => PRESETS[name] as CharacterParams;
const tunicOff = (p: CharacterParams): CharacterParams => withOutfit(p, { tunic_color: null });

/** The names of the Outfit fields that hold a colour (`n.endswith("_color")`). */
const COLOUR_FIELDS = FIELDS.Outfit.map((f) => f.name).filter((n) => n.endsWith("_color"));

test("test_a_cuts_holes_are_left_open_under_the_even_odd_rule", () => {
  // A hole is an extra subpath of its fill's own path, so what is behind the garment shows through it (the shirt behind a bow's slit).
  const sk = skeletonFor(preset("risa"));
  const square: Chain = [[-0.4, 2.0], [[[0.4, 2.0], [0.4, 2.0]], [[0.4, 3.0], [0.4, 3.0]], [[-0.4, 3.0], [-0.4, 3.0]]]];
  const hole: Chain = [[-0.1, 2.4], [[[0.1, 2.4], [0.1, 2.4]], [[0.1, 2.6], [0.1, 2.6]], [[-0.1, 2.6], [-0.1, 2.6]]]];
  const plain = garmentCut({ fills: [square], ref_body: "tall_slender" });
  const holed = garmentCut({ fills: [square], holes: [[0, hole]], ref_body: "tall_slender" });
  assert.ok(!drawCut(sk, plain, "#456789").includes('fill-rule="evenodd"'));
  const svg = drawCut(sk, holed, "#456789");
  assert.ok(svg.includes('fill-rule="evenodd"'));
  assert.equal(svg.split("M ").length - 1, 2, "the fill's path should carry two subpaths");
});

const luminance = (hex: string): number => {
  const h = hex.replace(/^#+/, "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};

for (const name of PRESET_NAMES) {
  test(`test_an_outer_layer_is_visible_against_what_it_covers[${name}]`, () => {
    // A coat or a robe needs a tone gap, or the garment is drawn and invisible: both are built around a boundary and
    // vanish completely, while rendering perfectly, when the layer under them is the same tone. 12 sits under the two that
    // read and above the three that did not.
    const o = preset(name).outfit;
    for (const field of ["coat_color", "robe_color"] as const) {
      const outer = o[field];
      if (outer === null) continue;
      const gap = Math.abs(luminance(outer) - luminance(o.tunic_color as string));
      assert.ok(gap >= 12.0, `${name}: ${field} ${outer} against tunic ${o.tunic_color} is a gap of ${gap.toFixed(1)}; the garment is drawn but nothing shows`);
    }
  });
}

for (const name of PRESET_NAMES) {
  test(`test_every_preset_renders_with_its_tunic_off[${name}]`, () => {
    // The tunic is optional like every other garment: off, it draws nothing and nothing that reads it gets a `None`.
    // Python's check is for the text `"None"`; the TypeScript equivalent of a leaked `None` is `null` or `undefined` (or a NaN) in a value.
    const p = tunicOff(preset(name));
    const svg = renderCharacter(p, skeletonFor(p));
    for (const leak of ['"None"', '"null"', '"undefined"', "NaN", "undefined"]) assert.ok(!svg.includes(leak), `${name}: the drawing contains ${leak}`);
    assert.ok(svg.startsWith("<svg") && svg.trimEnd().endsWith("</svg>"));
  });
}

for (const name of PRESET_NAMES) {
  test(`test_the_underpants_have_height_on_every_preset[${name}]`, () => {
    // The hem reads the real knee (`Skeleton.knee_y`): on the long-torso profile the knee landmark is above the hip, and
    // the underpants came out with the hem above the top, gone entirely on every untucked figure. Trousers off too: under
    // them there are none to draw.
    let p = tunicOff(preset(name));
    p = withOutfit(p, { trouser_color: null });
    const svg = renderCharacter(p);
    const color = p.outfit.underwear_color as string;
    const re = new RegExp(`<path d="([^"]+)" fill="${color.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}"`, "g");
    const paths = [...svg.matchAll(re)].map((m) => m[1] as string);
    assert.ok(paths.length > 0, `${name}: no underwear path was drawn`);
    const nums = numbersIn(paths[paths.length - 1] as string);
    const ys = nums.filter((_, i) => i % 2 === 1);
    assert.ok(Math.max(...ys) - Math.min(...ys) > skeletonFor(p).head_r * 0.1, `${name}: the underpants have no height`);
  });
}

test("test_the_crotch_reads_the_real_knee", () => {
  // The legs part below the hip, off the real knee (`Skeleton.knee_y`, half way from the hip to the ankle), dressed or bare
  // alike. The long-torso profile's old knee landmark, which the boots still measure off as `boot_y`, sits above the hip,
  // and the legs used to part at the hip itself.
  for (const p of [preset("satoko"), tunicOff(preset("satoko"))]) {
    const sk = skeletonFor(p);
    assert.ok(sk.boot_y < sk.hip_y && sk.hip_y < sk.knee_y, `boot ${sk.boot_y} hip ${sk.hip_y} knee ${sk.knee_y}`);
    assert.ok(Math.abs(sk.knee_y - (sk.hip_y + (sk.ankle_y - sk.hip_y) * 0.5)) <= 1e-6 * sk.knee_y);
    assert.ok(crotchY(sk, p) > sk.hip_y + strokeW(sk) * 4, `the crotch at ${crotchY(sk, p)} is not below the hip ${sk.hip_y}`);
  }
});

test("test_the_bare_knee_grows_in_without_a_jump", () => {
  // `docs/detail-plan.md`, D4: the bare leg's knee follows the limb taper from nothing at height 0.8. Just past it, where
  // the leg's inside becomes two curves, nothing in the drawing moves by more than a rounding step.
  const krista = preset("krista");
  const off = COLOUR_FIELDS.filter((n) => n !== "underwear_color");
  assert.ok(off.length > 10, "the outfit's colour fields");
  const bare = replace(krista, { outfit: replace(krista.outfit, Object.fromEntries(off.map((n) => [n, null])) as Partial<Outfit>) });
  const tags = (svg: string): string[] => svg.match(/<[a-zA-Z][^>]*>/g) ?? [];
  const a = tags(renderCharacter(replace(bare, { height: 0.8 })));
  const b = tags(renderCharacter(replace(bare, { height: 0.8001 })));
  assert.equal(a.length, b.length);
  assert.ok(a.length > 20);
  let compared = 0;
  a.forEach((x, i) => {
    const nx = (x.match(/-?\d+\.\d+/g) ?? []).map(Number);
    const ny = ((b[i] as string).match(/-?\d+\.\d+/g) ?? []).map(Number);
    if (nx.length === ny.length) {
      compared++;
      const worst = nx.reduce((m, v, k) => Math.max(m, Math.abs(v - (ny[k] as number))), 0.0);
      assert.ok(worst <= 0.25, `${x.slice(0, 80)} moved by ${worst}`);
    }
  });
  assert.ok(compared > 20);
});

test("test_every_garment_off_still_leaves_the_underwear", () => {
  // The coverage floor: whatever a consumer switches off, the figure keeps the underwear, so the least that is ever drawn
  // is what it already draws. Anything added later (swimwear, a nightgown) must not draw less than this.
  const off = Object.fromEntries(COLOUR_FIELDS.map((n) => [n, null])) as Partial<Outfit>;
  const o = outfit({ ...off, underwear_color: "#123456" });
  const svg = renderCharacter(replace(preset("satoko"), { outfit: o }));
  const n = svg.split("#123456").length - 1;
  assert.ok(n >= 2, `the briefs and the top are both drawn, found ${n}`);
});

test("test_the_wristband_text_is_text_and_never_markup", () => {
  // Hostile text is drawn as letters: the SVG stays well-formed and gains no elements.
  const hostile = '</text><script>alert(1)</script><text a="&';
  const worn = withOutfit(preset("linnea"), { wristband_color: "#f2efe6", wristband_text: hostile, wristband_side: 1 });
  const svg = renderCharacter(worn);
  assert.ok(!svg.includes("<script"));
  const root = fromstring(svg);
  assert.deepEqual([...iterNodes(root)].filter((e) => e.tag === "script"), []);
  assert.ok(itertext(root).includes(hostile), "the text should still be drawn, as letters");
});

/** The (x, y) numbers in a drawn hand's path data, in pixels, control points included, so the box is a little generous, the same for every style. */
function handNumbers(p: CharacterParams, side: number): { head_r: number; xs: number[]; ys: number[] } {
  const sk = skeletonFor(p);
  const [, , centreWrist, wristY] = armLine(sk);
  const wWrist = sk.arm_half_w * (1.0 - 0.34 * limbBuild(sk));
  const svg = hand(sk, p, sk.head_cx + side * centreWrist, wristY, wWrist, side);
  const d = [...svg.matchAll(/d="([^"]+)"/g)].map((m) => m[1]).join(" ");
  const nums = numbersIn(d);
  return { head_r: sk.head_r, xs: nums.filter((_, i) => i % 2 === 0), ys: nums.filter((_, i) => i % 2 === 1) };
}

// character.HAND_STYLES, which no TypeScript module exports: the five styles of the Python tuple, in its order.
const HAND_STYLES = ["mitten", "notched", "stroked", "curled", "traced"];
for (const style of HAND_STYLES) {
  for (const name of ["krista", "gero", "satoko"]) {
    test(`test_every_relaxed_hand_keeps_a_hands_footprint[${style}-${name}]`, () => {
      // `docs/hands-plan.md`, the footprint gate: whichever hand a figure is given, it is the chibi's size, not the thin
      // adult hand the first traced one was. Height 0.28 to 0.46 head radii and height over width 0.6 to 1.3.
      const p = replace(preset(name), { hand_style: style });
      const { head_r, xs, ys } = handNumbers(p, 1);
      const height = (Math.max(...ys) - Math.min(...ys)) / head_r;
      const width = (Math.max(...xs) - Math.min(...xs)) / head_r;
      assert.ok(0.28 <= height && height <= 0.46, `${style}: height ${height}`);
      assert.ok(0.6 <= height / width && height / width <= 1.3, `${style}: height over width ${height / width}`);
    });
  }
}
