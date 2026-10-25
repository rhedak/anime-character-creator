// A raised arm's side of the adult shirt and blazer (body-adult-shirt.ts `outline`, body-adult-blazer.ts `panel`): the sleeve goes with the arm and that side's outline runs down the torso, inked,
// instead of the whole garment being clipped along the armhole (which left a wedge of the sleeve under the arm, cut along straight chords with no ink). A hanging arm's side is drawn as before.

import assert from "node:assert/strict";
import { test } from "node:test";
import { OUTLINE } from "../src/character.ts";
import { outfit, replace } from "../src/model.ts";
import { RISA } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const draw = (o: Partial<typeof RISA>): string => renderCharacter(replace(RISA, o), null, null, false);
const dupes = (svg: string): string[] => {
  const ids = [...svg.matchAll(/ id="([^"]+)"/g)].map((m) => m[1] as string);
  return ids.filter((id, i) => ids.indexOf(id) !== i);
};
const POSES = [
  { right_arm_out: 130, right_elbow: 40, left_arm_out: 35, left_elbow: 100 },
  { right_arm_out: 6, right_elbow: 150, left_arm_out: 6, left_elbow: 150 },
  { right_arm_out: 160, left_arm_out: 90 },
];

test("with an arm raised, neither the blazer nor the shirt is clipped along the armhole, and the ids stay unique", () => {
  for (const pose of POSES) {
    for (const o of [pose, { ...pose, outfit: outfit({ ...RISA.outfit, coat_color: null }) }]) {
      const svg = draw(o);
      assert.ok(!svg.includes("adult-blazer-torso") && !svg.includes("adult-shirt-torso"), JSON.stringify(o));
      assert.deepEqual(dupes(svg), [], JSON.stringify(o));
    }
  }
});

test("a raised side's panel is one inked outline down the torso: it is shorter than the hanging side's, which runs down the sleeve and back", () => {
  // the blazer draws its two panels first, then the pockets (navy and inked too)
  const panels = (svg: string): string[] => [...svg.matchAll(new RegExp(`<path d="(M [^"]+Z)" fill="#212940" stroke="${OUTLINE}"`, "g"))].map((m) => m[1] as string).slice(0, 2);
  const hanging = panels(draw({}));
  const raised = panels(draw({ right_arm_out: 130, right_elbow: 40 }));
  // the viewer's left panel is the character's right: raised, it no longer carries the sleeve's two edges
  assert.ok((raised[0] as string).length < (hanging[0] as string).length);
  assert.equal(raised[1], hanging[1]);
});
