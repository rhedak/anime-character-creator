// Shared helpers of the rule tests (ts/test/rules-*.test.ts). Not a test file itself.

import assert from "node:assert/strict";
import { characterParams, replace } from "../src/model.ts";
import type { CharacterParams, FaceStyle, Outfit } from "../src/params.ts";
import { NEUTRAL_BASES, PRESETS, RISA_TALL_SLENDER } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";
import { rgbToHsv, hexToRgb01 } from "../src/colorutil.ts";
import { HAIRSTYLES, type Hairstyle } from "../src/core-head.ts";
import type { Chain, Point } from "../src/tables.ts";

/** Every preset name, sorted like Python's `sorted(PRESETS)`. */
export const PRESET_NAMES: string[] = Object.keys(PRESETS).sort();
export const BASE_NAMES: string[] = Object.keys(NEUTRAL_BASES).sort();

/** `pytest.approx(expected, abs=...)` or the default (rel 1e-6, abs 1e-12) when `abs` is not given. */
export function approx(actual: number, expected: number, abs?: number): boolean {
  if (abs !== undefined) return Math.abs(actual - expected) <= abs;
  return Math.abs(actual - expected) <= Math.max(1e-6 * Math.abs(expected), 1e-12);
}

/** `assert actual == pytest.approx(expected, abs=...)` with a message that shows both numbers. */
export function assertApprox(actual: number, expected: number, abs?: number, msg = ""): void {
  assert.ok(approx(actual, expected, abs), `${msg} ${actual} is not approximately ${expected}`.trim());
}

/** `dataclasses.replace(p, **changes)` on a character, for the common case of one outfit or face change. */
export const withOutfit = (p: CharacterParams, changes: Partial<Outfit>): CharacterParams => replace(p, { outfit: replace(p.outfit, changes) });
export const withFace = (p: CharacterParams, changes: Partial<FaceStyle>): CharacterParams => replace(p, { face: replace(p.face, changes) });

/** `render_character(replace(PRESETS[name], finish="soft"), **kw)` of the soft-finish tests. */
/**
 * The presets plus the old chibi Risa (`risa_tall_slender`, `RISA_TALL_SLENDER`): she was the only preset on the tall slender body and the only one with the `long_fringed` cut and its locks, so the tests of those
 * (and of the traced chibi garments she wore) draw her as this fixture now that the `risa` preset is on the adult woman's body (docs/risa-adult-plan.md).
 */
export const FIXTURES: Record<string, CharacterParams> = { ...PRESETS, risa_tall_slender: RISA_TALL_SLENDER };
export const soft = (name: string, idPrefix = ""): string => renderCharacter(replace(FIXTURES[name] as CharacterParams, { finish: "soft" }), null, null, false, idPrefix);

/** A character with the defaults and these fields set. */
export const make = (changes: Partial<CharacterParams> = {}): CharacterParams => characterParams(changes);

/** `colorsys.rgb_to_hsv(*hex_to_rgb01(c))`. */
export const hsvOf = (hex: string): readonly [number, number, number] => rgbToHsv(...hexToRgb01(hex));

/** `_walk` of the Python tests: a quadratic chain as a dense point list. */
export function walk(start: Point, segments: readonly (readonly [Point, Point])[], per = 24): Point[] {
  const pts: Point[] = [start];
  let prev = start;
  for (const [ctrl, end] of segments) {
    for (let i = 1; i <= per; i++) {
      const t = i / per;
      pts.push([(1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * ctrl[0] + t ** 2 * end[0], (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * ctrl[1] + t ** 2 * end[1]]);
    }
    prev = end;
  }
  return pts;
}

/** The chain as `[start, segments]`, as the Python tests unpack `style.mass(fall)`. */
export const chainParts = (c: Chain): [Point, readonly (readonly [Point, Point])[]] => [c[0], c[1]];

/** Python's `re.findall(pattern, s)` for a pattern with one group: the group of every match. */
export const findall = (re: RegExp, s: string): string[] => [...s.matchAll(new RegExp(re.source, re.flags.includes("g") ? re.flags : re.flags + "g"))].map((m) => m[1] as string);

/** Every number in a string as Python's `-?\d+\.?\d*` finds them. */
export const numbersIn = (s: string): number[] => (s.match(/-?\d+\.?\d*/g) ?? []).map(Number);

/** Run `fn` and return the PyError class name and message it raised, or `null` if it did not raise. */
export function raised(fn: () => unknown): { type: string; message: string } | null {
  try {
    fn();
  } catch (e) {
    const err = e as { pyType?: string; message?: string };
    return { type: err.pyType ?? (e as Error).constructor.name, message: String(err.message) };
  }
  return null;
}

/** `pytest.raises(cls, match=fragment)`: it raised that Python class and the message contains the fragment (a search). */
export function assertRaises(fn: () => unknown, cls: string, fragment?: string): void {
  const r = raised(fn);
  assert.ok(r !== null, `expected ${cls}, nothing was raised`);
  assert.equal(r.type, cls, `expected ${cls}, got ${r.type}: ${r.message}`);
  if (fragment !== undefined) assert.ok(r.message.includes(fragment), `message ${JSON.stringify(r.message)} lacks ${JSON.stringify(fragment)}`);
}

/**
 * `monkeypatch.setitem(HAIRSTYLES, name, style)` for the length of `fn`: the cut is replaced in the shared table the
 * drawing code reads (`hairstyleFor`) and put back in `finally`, whatever `fn` does. `HAIRSTYLES` is typed read-only but is a plain
 * object, so the assignment works at run time.
 */
export function withHairstyle<T>(name: string, replacement: Hairstyle, fn: () => T): T {
  const table = HAIRSTYLES as unknown as Record<string, Hairstyle>;
  const original = table[name] as Hairstyle;
  table[name] = replacement;
  try {
    return fn();
  } finally {
    table[name] = original;
  }
}

/** `dataclasses.replace(HAIRSTYLES[name], **changes)`: a copy of the cut with fields changed. */
export const hairstyleWith = (name: string, changes: Partial<Hairstyle>): Hairstyle => ({ ...(HAIRSTYLES[name] as Hairstyle), ...changes });
