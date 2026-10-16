// Rule from tests/test_ids.py: every id a drawing defines is defined once, and every reference to one resolves, in
// both finishes, for every preset and both neutral bases.

import assert from "node:assert/strict";
import { test } from "node:test";
import { replace } from "../src/model.ts";
import type { CharacterParams } from "../src/params.ts";
import { NEUTRAL_BASES, PRESETS } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

const EVERYONE: Record<string, CharacterParams> = { ...PRESETS, ...NEUTRAL_BASES };

for (const finish of ["flat", "soft"] as const) {
  for (const name of Object.keys(EVERYONE).sort()) {
    test(`test_ids_are_defined_once_and_every_reference_resolves[${name}-${finish}]`, () => {
      const svg = renderCharacter(replace(EVERYONE[name] as CharacterParams, { finish }));
      const ids = [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1] as string);
      assert.ok(ids.length > 0, "the control needs ids");
      const counts = new Map<string, number>();
      for (const i of ids) counts.set(i, (counts.get(i) ?? 0) + 1);
      assert.deepEqual([...counts].filter(([, n]) => n > 1).map(([i]) => i), []);
      const refs = [...[...svg.matchAll(/url\(#([^)]+)\)/g)].map((m) => m[1] as string), ...[...svg.matchAll(/href="#([^"]+)"/g)].map((m) => m[1] as string)];
      assert.deepEqual(
        refs.filter((r) => !ids.includes(r)),
        [],
      );
    });
  }
}
