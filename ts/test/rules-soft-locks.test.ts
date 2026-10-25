// Rules of the soft finish's clumps (`Hairstyle.locks`): tests/test_soft_locks.py, the portable and rewritten ones.
// The clumps are drawn only for the soft finish and only for a cut that has been authored, inside the hair's own
// silhouette, small, deterministic, and in tones that keep the hair's saturation (the tone tests are in rules-colour).
// The three tests that swapped a cut in Python (`monkeypatch.setitem(HAIRSTYLES, ...)`) assign into the exported
// HAIRSTYLES object and restore it in `finally` (`withHairstyle`).

import assert from "node:assert/strict";
import { test } from "node:test";
import { ADULT_BODY_TYPES } from "../src/body-adult.ts";
import { HAIRSTYLES, type Lock } from "../src/core-head.ts";
import { replace } from "../src/model.ts";
import type { CharacterParams } from "../src/params.ts";
import { PRESETS, RISA_TALL_SLENDER } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";
import { paramsFromDict } from "../src/urlstate.ts";
import { fromstring } from "./svg-scan.ts";
import { FIXTURES, PRESET_NAMES, assertRaises, hairstyleWith, soft, withHairstyle } from "./rules-util.ts";

const AUTHORED = Object.keys(HAIRSTYLES)
  .filter((name) => HAIRSTYLES[name]!.locks !== null)
  .sort();
// Per soft document, in bytes. A guard against runaway output, not a design limit (the Python's own note: raise it on
// purpose, with the frame-time check re-run, not to silence a failure).
const BYTE_BUDGET = 150_000;
/**
 * An adult woman's soft drawing: a 46 KB body outline, traced hands and feet and traced hair (Franzi's is 184 KB, docs/adult-body-status.md). Raised from 400 KB to 440 KB on 2026-10-25 for Risa's
 * soft clumps (docs/risa-polish-plan.md, stage 6: her soft drawing is about 414 KB, her flat one 389 KB); the owner expects it to rise as detail is added. Her flat drawings keep their own limit
 * of 400 KB (ts/test/adult-body.test.ts).
 */
const ADULT_BYTE_BUDGET = 440_000;
const bytes = (s: string): number => Buffer.byteLength(s, "utf8");
const FRONT_GROUP = '<g clip-path="url(#hair-front)">';

test("the authored cuts are the five the Python tests were written against", () => {
  assert.deepEqual(AUTHORED, ["long_fringed", "long_parted", "long_traced", "short_crop", "short_layered"]);
});

test("test_a_cut_without_locks_draws_exactly_as_it_did", () => {
  const withLocks = soft("risa_tall_slender");
  const without = withHairstyle("long_fringed", hairstyleWith("long_fringed", { locks: null }), () => soft("risa_tall_slender"));
  const start = withLocks.indexOf(FRONT_GROUP);
  assert.ok(start >= 0, "the control needs the clump group");
  const end = withLocks.indexOf("</g>", start) + "</g>".length;
  assert.equal(withLocks.slice(0, start) + withLocks.slice(end), without);
  assert.notEqual(withLocks, without);
});

for (const name of PRESET_NAMES) {
  test(`test_every_preset_stays_within_the_byte_budget_soft[${name}]`, () => {
    const n = bytes(soft(name));
    const budget = Object.hasOwn(ADULT_BODY_TYPES, (PRESETS[name] as CharacterParams).body) ? ADULT_BYTE_BUDGET : BYTE_BUDGET;
    assert.ok(n <= budget, `${name} is ${n} bytes`);
  });
}

test("test_the_clumps_are_deterministic", () => {
  assert.equal(soft("risa_tall_slender"), soft("risa_tall_slender"));
});

for (const cut of AUTHORED) {
  for (const fall of [1.4, 2.0, 2.8, 3.44, 4.0]) {
    test(`test_every_lock_is_well_formed_and_under_the_ceiling[${fall}-${cut}]`, () => {
      const locks = (HAIRSTYLES[cut]!.locks as (fall: number) => readonly Lock[])(fall);
      assert.ok(locks.length > 0);
      for (const [role, points, width, length] of locks) {
        assert.ok(role === "shadow" || role === "lit", `role ${role}`);
        assert.ok(points.length >= 3 && 0 < width && width < 0.5 && 0 < length && length <= 1, `${cut}: ${points.length} points, width ${width}, length ${length}`);
        for (const [x, y] of points) {
          assert.ok(Math.abs(x) < 2.0, `${cut} x ${x}`);
          // the same headroom `build_skeleton` leaves above the skull for hair ink
          assert.ok(y > -1.55, `${cut} y ${y}`);
        }
      }
    });
  }
}

test("test_an_unknown_role_is_refused", () => {
  const style = hairstyleWith("long_fringed", {
    locks: () => [["glow", [[0, 0], [0, 1], [0, 2]], 0.1, 1.0]] as unknown as readonly Lock[],
  });
  withHairstyle("long_fringed", style, () => assertRaises(() => soft("risa_tall_slender"), "ValueError", "shadow or lit"));
});

for (const cut of ["satoko", "risa_tall_slender"]) {
  test(`test_the_byte_budget_holds_with_a_tip_colour_on_each_authored_cut[${cut}]`, () => {
    const p = replace(FIXTURES[cut] as CharacterParams, { finish: "soft", hair_tip_color: "#33aaff" });
    const n = bytes(renderCharacter(p));
    assert.ok(n <= BYTE_BUDGET, `${cut} is ${n} bytes`);
  });
}

test("test_a_clump_too_short_to_draw_is_skipped_not_a_crash", () => {
  const tooShort = hairstyleWith("long_fringed", {
    locks: () =>
      [
        ["shadow", [[0, -1], [0, 0], [0, 1]], 0.1, 0.05],
        ["lit", [[0, -1], [0, 0], [0, 1]], 0.1, 0.02],
      ] as unknown as readonly Lock[],
  });
  const drawn = withHairstyle("long_fringed", tooShort, () => soft("risa_tall_slender"));
  assert.ok(drawn.startsWith("<svg") && drawn.length > 1000);
  fromstring(drawn); // whatever is drawn for them, the document is well-formed
});

for (const bad of [-0.1, 2.1]) {
  test(`test_a_strength_out_of_range_is_refused[${bad}]`, () => {
    assertRaises(() => renderCharacter(replace(RISA_TALL_SLENDER, { finish: "soft", highlight_strength: bad })), "ValueError", "highlight_strength");
  });
}

const NOT_A_NUMBER: [string, unknown][] = [
  ["'1'", "1"],
  ["None", null],
  ["True", true],
  ["nan", Number.NaN],
];
for (const [label, bad] of NOT_A_NUMBER) {
  test(`test_a_strength_that_is_not_a_number_is_refused_for_soft_and_in_a_link[${label}]`, () => {
    assertRaises(() => renderCharacter(replace(RISA_TALL_SLENDER, { finish: "soft", highlight_strength: bad as number })), "ValueError", "highlight_strength");
    assertRaises(() => paramsFromDict({ finish: "soft", highlight_strength: bad }), "ValueError", "highlight_strength");
  });
}

for (const cut of ["short_layered", "short_crop", "long_parted"]) {
  test(`test_a_tip_colour_on_a_big_preset_stays_within_the_budget[${cut}]`, () => {
    const p = replace(PRESETS.katherina as CharacterParams, { finish: "soft", hairstyle: cut, hair_tip_color: "#f8b890" });
    const n = bytes(renderCharacter(p));
    assert.ok(n <= BYTE_BUDGET, `${cut} is ${n} bytes`);
  });
}

// A control for the monkeypatch helper itself: the table is back as it was after each swap.
test("the cut swaps above leave HAIRSTYLES as they found it", () => {
  assert.deepEqual(AUTHORED, ["long_fringed", "long_parted", "long_traced", "short_crop", "short_layered"]);
  assert.ok(HAIRSTYLES.long_fringed!.locks !== null);
});
