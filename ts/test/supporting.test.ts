// `supporting.ts` against Python.

import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import { DISPLAY_NAMES, SUPPORTING } from "../src/supporting.ts";
import { DISPLAY_NAMES as PRESET_NAMES, PRESETS } from "../src/presets.ts";
import { paramsJsonText } from "../src/urlstate.ts";
import { REPO_ROOT, TS_ROOT } from "./fixtures.ts";
import { commentLines, fixture } from "./phase3.ts";

const fx = fixture("presets.json");

test("SUPPORTING: kenzo, dieter and driver, every field and every number spelling as Python", () => {
  assert.deepEqual(Object.keys(SUPPORTING), ["kenzo", "dieter", "driver"]);
  for (const [name, p] of Object.entries(SUPPORTING)) {
    assert.deepEqual(JSON.parse(JSON.stringify(p)), fx.supporting[name].dict, name);
    assert.equal(paramsJsonText(p), fx.supporting[name].json, name);
  }
});

test("DISPLAY_NAMES, and none of the three is offered as a preset", () => {
  assert.deepEqual(DISPLAY_NAMES, fx.supporting_display_names);
  for (const name of Object.keys(SUPPORTING)) {
    assert.ok(!(name in PRESETS));
    assert.ok(!(name in PRESET_NAMES));
  }
});

const pyPath = join(REPO_ROOT, "src/anime_character_creator/supporting.py");
test("supporting.ts keeps every whole-line comment of supporting.py", { skip: !existsSync(pyPath) && "the Python source is gone" }, () => {
  const py = commentLines(readFileSync(pyPath, "utf8"), "#");
  const ts = readFileSync(join(TS_ROOT, "src/supporting.ts"), "utf8");
  const got = commentLines(ts.slice(ts.indexOf("// Kenzo:")), "//");
  assert.deepEqual(got, py);
});
