// `catalogue.ts` against Python: `toJson()` is `ref-out/catalogue.json` byte for byte (the committed file), and it is
// Python's own `to_json()` byte for byte (a fixture made by `harness/ts_port/gen_catalogue_expected.py`, and, when a
// Python is at hand, a fresh run of that script).

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import {
  BELT_CUT_LABELS,
  BODY_LABELS,
  COAT_CUT_LABELS,
  COLLAR_CUT_LABELS,
  GARMENTS,
  GRIP_STYLES,
  HAIR_CLIP_LABELS,
  HAND_STYLES,
  SKIRT_CUT_LABELS,
  SLEEVE_CUT_LABELS,
  BOOT_CUT_LABELS,
  basePoints,
  boolJson,
  buildCatalogue,
  castPoints,
  color,
  faceRange,
  lookup,
  outfitFieldsNamed,
  rangeField,
  rangeJson,
  selectJson,
  toJson,
} from "../src/catalogue.ts";
import { dumps } from "../src/pyjson.ts";
import { PyError } from "../src/pynum.ts";
import { REPO_ROOT, TS_ROOT } from "./fixtures.ts";
import { commentLines } from "./phase3.ts";

interface Expected {
  text: string;
  sha256: string;
  bytes: number;
  cast_points: [string, string][];
  base_points: [string, string][];
  hand_styles: string[];
  grip_styles: string[];
  outfit_fields_named: string[];
}
const expected = JSON.parse(readFileSync(join(TS_ROOT, "fixtures", "catalogue-expected.json"), "utf8")) as Expected;
const committed = readFileSync(join(REPO_ROOT, "ref-out", "catalogue.json"), "utf8");

test("toJson() is the committed ref-out/catalogue.json, byte for byte", () => {
  const got = toJson();
  assert.equal(got.length, committed.length);
  assert.ok(got === committed, "ref-out/catalogue.json differs from the TypeScript catalogue");
  assert.ok(got.endsWith("}\n"));
});

test("toJson() is the text Python's to_json() produced (fixture), with its sha256 and length", () => {
  const got = toJson();
  assert.ok(got === expected.text, "the fixture text differs");
  assert.equal(createHash("sha256").update(got, "utf8").digest("hex"), expected.sha256);
  assert.equal(Buffer.byteLength(got, "utf8"), expected.bytes);
  assert.equal(expected.text, committed, "the fixture is stale against ref-out/catalogue.json");
});

const PYTHON = process.env.CATALOGUE_PYTHON ?? "/Users/hanssen.henrik/git/self-study/anime-character-creator-dev/.venv/bin/python";
const SCRIPT = join(REPO_ROOT, "harness", "ts_port", "gen_catalogue_expected.py");
test(
  "toJson() is a fresh Python run's to_json() (runs the expected-fixture script with --print)",
  { skip: !existsSync(PYTHON) && `no Python at ${PYTHON} (set CATALOGUE_PYTHON)` },
  () => {
    const run = spawnSync(PYTHON, [SCRIPT, "--print"], { encoding: "utf8", env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" } });
    assert.equal(run.status, 0, run.stderr);
    const fresh = JSON.parse(run.stdout) as Expected;
    assert.ok(toJson() === fresh.text, "differs from a fresh Python run");
    assert.equal(createHash("sha256").update(toJson(), "utf8").digest("hex"), fresh.sha256);
    // the committed fixture is current
    assert.deepEqual(fresh, expected, "ts/fixtures/catalogue-expected.json is stale: run gen_catalogue_expected.py");
  },
);

test("the starting points and the helpers the tests name are Python's", () => {
  assert.deepEqual(castPoints().map((s) => [s.id, s.label]), expected.cast_points);
  assert.deepEqual(basePoints().map((s) => [s.id, s.label]), expected.base_points);
  assert.deepEqual([...outfitFieldsNamed()].sort(), expected.outfit_fields_named);
  assert.deepEqual([...HAND_STYLES], expected.hand_styles);
  assert.deepEqual([...GRIP_STYLES], expected.grip_styles);
});

test("buildCatalogue() is a fresh object each call and dumps to the same text", () => {
  const a = buildCatalogue();
  const b = buildCatalogue();
  assert.notEqual(a, b);
  assert.equal(dumps(a, { indent: 2 }), dumps(b, { indent: 2 }));
});

test("ints print as ints and whole floats as floats", () => {
  // `RangeField("shoulder_bars", "Bars", 1, 4)` is the one range with int ends; every other whole end is a float.
  assert.match(committed, /"field": "shoulder_bars",\n\s+"label": "Bars",\n\s+"min": 1,\n\s+"max": 4\n/);
  assert.match(committed, /"field": "hair_length",\n\s+"label": "Hair length",\n\s+"min": 0\.0,\n\s+"max": 1\.0\n/);
  assert.equal(dumps(rangeJson(rangeField("x", "X", 1, 4, true))), '{"field": "x", "label": "X", "min": 1, "max": 4}');
  assert.equal(dumps(rangeJson(rangeField("x", "X", 1, 4))), '{"field": "x", "label": "X", "min": 1.0, "max": 4.0}');
  // select values that are numbers are ints (scar_side, wristband_side)
  assert.equal(
    dumps(selectJson({ field: "f", label: "F", options: [[-1, "L"], [null, "N"], ["0000", "T"]] })),
    '{"field": "f", "label": "F", "options": [{"value": -1, "label": "L"}, {"value": null, "label": "N"}, {"value": "0000", "label": "T"}]}',
  );
  assert.equal(dumps(boolJson({ field: "a", label: "b" })), '{"field": "a", "label": "b"}');
});

test("the cut selects are the label tables, sorted, after the shared garment's own option", () => {
  const sel = (slot: string, field: string) => {
    const g = GARMENTS.find((x) => x.id === slot)!;
    return g.selects.find((s) => s.field === field)!.options;
  };
  const sortedPairs = (t: Readonly<Record<string, string>>) => Object.entries(t).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  assert.deepEqual(sel("tunic", "sleeve_cut"), [[null, "Plain"], ...sortedPairs(SLEEVE_CUT_LABELS)]);
  assert.deepEqual(sel("boots", "boot_cut"), [[null, "Boot"], ...sortedPairs(BOOT_CUT_LABELS)]);
  assert.deepEqual(sel("belt", "belt_cut"), [[null, "Band"], ...sortedPairs(BELT_CUT_LABELS)]);
  assert.deepEqual(sel("skirt", "skirt_cut"), [[null, "Gathered"], ...sortedPairs(SKIRT_CUT_LABELS)]);
  assert.deepEqual(sel("collar", "collar_cut"), [[null, "Band"], ...sortedPairs(COLLAR_CUT_LABELS)]);
  assert.deepEqual(sel("coat", "coat_cut"), [[null, "Two panels"], ...sortedPairs(COAT_CUT_LABELS)]);
  // the hair clip keeps the label table's own order
  assert.deepEqual(sel("hair_clip", "hair_clip"), Object.entries(HAIR_CLIP_LABELS));
});

test("the field helpers raise AssertionError for a field the dataclass lacks, as the Python asserts do", () => {
  assert.throws(() => color("no_such_color", "X"), (e: unknown) => e instanceof PyError && e.pyType === "AssertionError" && e.message === "AssertionError: Outfit has no field 'no_such_color'");
  assert.throws(() => faceRange("tunic_color", "X", 0, 1), (e: unknown) => e instanceof PyError && e.pyType === "AssertionError" && e.message.endsWith("FaceStyle has no field 'tunic_color'"));
});

test("a label table is read like a dict: a missing key is a KeyError with the key's repr", () => {
  assert.throws(() => lookup(BODY_LABELS, "nope"), (e: unknown) => e instanceof PyError && e.pyType === "KeyError" && e.message === "KeyError: 'nope'");
  assert.equal(lookup(BODY_LABELS, "tall_chibi"), "Tall chibi (Katherina's)");
  assert.throws(() => lookup(BODY_LABELS, "toString"), (e: unknown) => e instanceof PyError && e.pyType === "KeyError");
});

// The Python's whole-line comments are the design record. Every one is in the TypeScript, in one of the three files.
const pyPath = join(REPO_ROOT, "src/anime_character_creator/catalogue.py");
test("catalogue.ts, catalogue-types.ts and catalogue-tables.ts keep every whole-line comment of catalogue.py", { skip: !existsSync(pyPath) && "the Python source is gone" }, () => {
  const py = commentLines(readFileSync(pyPath, "utf8"), "#");
  const ts = ["catalogue.ts", "catalogue-types.ts", "catalogue-tables.ts"].flatMap((f) => commentLines(readFileSync(join(TS_ROOT, "src", f), "utf8"), "//"));
  const pool = new Map<string, number>();
  for (const c of ts) pool.set(c, (pool.get(c) ?? 0) + 1);
  const missing: string[] = [];
  for (const c of py) {
    const n = pool.get(c) ?? 0;
    if (n === 0) missing.push(c);
    else pool.set(c, n - 1);
  }
  assert.deepEqual(missing, []);
});
