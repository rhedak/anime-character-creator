// The web tool's bridge (`src/web-bridge.ts`): the four functions `web/app.js` calls. Against Python's own values for the presets
// (fixtures/presets.json: `asdict` of each) and against the committed art.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import { NEUTRAL_BASES, PRESETS } from "../src/presets.ts";
import { PyError } from "../src/pynum.ts";
import { decode, encode, render, stateForStart } from "../src/web-bridge.ts";
import { REPO_ROOT, TS_ROOT, loadJson } from "./fixtures.ts";

const fixtures = loadJson<{ presets: Record<string, { dict: unknown }>; neutral_bases: Record<string, { dict: unknown }> }>(join(TS_ROOT, "fixtures", "presets.json"));

test("stateForStart is Python's asdict, as JSON text, for every starting point", () => {
  for (const [name, f] of [...Object.entries(fixtures.presets), ...Object.entries(fixtures.neutral_bases)]) {
    assert.deepEqual(JSON.parse(stateForStart(name)), f.dict, name);
  }
  assert.throws(() => stateForStart("nobody"), (e: unknown) => e instanceof PyError && e.pyType === "ValueError");
});

test("render draws the committed art from a state, as the page asks for it", () => {
  for (const name of ["satoko", "katherina", "risa"]) {
    assert.equal(render(stateForStart(name), null, false), readFileSync(join(REPO_ROOT, "ref-out", `${name}.svg`), "utf8"), name);
  }
  assert.equal(render(stateForStart("female"), null, false), readFileSync(join(REPO_ROOT, "ref-out/bases/female.svg"), "utf8"));
  assert.ok(render(stateForStart("satoko"), "white", false).includes('fill="white"'));
  assert.ok(render(stateForStart("satoko"), null, true).includes("<metadata>"));
});

test("a state survives the page's own round trip (JSON.stringify of a parsed state) and a link", () => {
  for (const name of Object.keys(PRESETS).concat(Object.keys(NEUTRAL_BASES))) {
    const state = JSON.parse(stateForStart(name));
    const sent = JSON.stringify(state); // the page writes floats like 1.0 as 1
    assert.equal(render(sent, null, false), render(stateForStart(name), null, false), `${name}: the page's JSON draws the same`);
    assert.deepEqual(JSON.parse(decode(encode(sent))), JSON.parse(decode(encode(stateForStart(name)))), `${name}: a link decodes to the same character`);
  }
});

test("a bad link or state is an error the page can catch", () => {
  assert.throws(() => decode("not a link"), (e: unknown) => e instanceof PyError);
  assert.throws(() => render("[]", null, false), (e: unknown) => e instanceof PyError);
});
