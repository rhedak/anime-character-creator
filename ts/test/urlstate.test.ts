// `urlstate.ts` against Python: the bytes of a link, the decoding of a link and the outcome of a bad one.

import assert from "node:assert/strict";
import { test } from "node:test";
import { characterParams } from "../src/model.ts";
import { PRESETS } from "../src/presets.ts";
import { PyInt, dumps } from "../src/pyjson.ts";
import { loadsText } from "../src/pyjsonload.ts";
import { PyError } from "../src/pynum.ts";
import { QUERY_PARAM, characterUrl, decodeParams, encodeParams, paramsFromDict, paramsJsonText, paramsToDict } from "../src/urlstate.ts";
import { fixture, outcomeOf, paramsFromDiff, sha256, wanted } from "./phase3.ts";

const fx = fixture("urlstate.json");
const TOOL_URL = "https://rhedak.github.io/anime-character-creator/";

test("encode_params, character_url and the decoded result are Python's on 300 and more characters", () => {
  assert.ok(fx.encode.length >= 300);
  const bad: string[] = [];
  let soft = 0;
  let intInFloatField = 0;
  for (const c of fx.encode) {
    const p = paramsFromDiff(c.diff);
    const enc = encodeParams(p);
    if (sha256(enc) !== c.encoded_sha256 || enc.length !== c.encoded_len) bad.push(`${c.label}: encoded`);
    if (c.encoded !== undefined && enc !== c.encoded) bad.push(`${c.label}: encoded text`);
    if (c.params !== undefined && paramsJsonText(p) !== c.params) bad.push(`${c.label}: params text`);
    if (sha256(characterUrl(p, TOOL_URL)) !== c.url_sha256) bad.push(`${c.label}: url`);
    const got = outcomeOf(() => decodeParams(enc));
    const want = c.decoded === "same" ? { ok_sha256: sha256(paramsJsonText(p)) } : wanted(c.decoded);
    if (JSON.stringify(got) !== JSON.stringify(want)) bad.push(`${c.label}: decoded ${JSON.stringify(got)} vs ${JSON.stringify(want)}`);
    if (c.diff.includes('"finish":"soft"')) soft++;
    if (/"(height|frame|chest|bust)":-?\d+[,}]/.test(c.diff)) intInFloatField++;
  }
  assert.deepEqual(bad, []);
  assert.ok(soft >= 50, `soft finish cases: ${soft}`);
  assert.ok(intInFloatField >= 3, `int spelling in a float field: ${intInFloatField}`);
});

test("character_url puts the encoded character after the base, whatever the base is", () => {
  const p = paramsFromDiff(fx.base_urls.params);
  for (const c of fx.base_urls.cases) assert.equal(characterUrl(p, c.base), c.url);
  assert.equal(QUERY_PARAM, "c");
});

test("malformed and odd links: the same outcome, class and (the ValueError wrapper's) message, as Python", () => {
  assert.ok(fx.malformed.length >= 60);
  const bad: string[] = [];
  const classes = new Set<string>();
  let ok = 0;
  for (const c of fx.malformed) {
    const got = outcomeOf(() => decodeParams(c.input));
    const want = wanted(c.want);
    if (got.err) classes.add(got.err);
    else ok++;
    if (JSON.stringify(got) !== JSON.stringify(want)) bad.push(`${c.label}: got ${JSON.stringify(got).slice(0, 200)} want ${JSON.stringify(want).slice(0, 200)}`);
  }
  assert.deepEqual(bad, []);
  assert.ok(ok >= 20 && classes.has("ValueError") && classes.has("TypeError"), `ok ${ok} classes ${[...classes]}`);
});

test("a decoded int stays an int where the registry says float, and a whole float stays a float where it says int", () => {
  const p = paramsFromDict(loadsText('{"height":2,"face":{"scar_side":1.0,"blush":1}}') as Map<string, unknown>);
  assert.ok((p.height as unknown) instanceof PyInt);
  assert.equal(paramsJsonText(p).includes('"height":2,'), true);
  assert.equal(paramsJsonText(p).includes('"scar_side":1.0'), true);
  assert.equal(paramsJsonText(p).includes('"blush":1,'), true);
  // The same numbers from a plain JS object mean what the registry says.
  const q = paramsFromDict({ height: 2, face: characterParams().face });
  assert.equal(paramsJsonText(q).includes('"height":2.0'), true);
  assert.equal(paramsJsonText(q).includes('"scar_side":0}'), true);
});

test("a link from before the retired fields loads as the default tall chibi", () => {
  const p = paramsFromDict(loadsText('{"heads":3,"body":null,"hairstyle":"long_traced_real","face":{"eye_style":"anime","eye_glow":1}}') as Map<string, unknown>);
  assert.equal(p.body, "tall_chibi_long_torso");
  assert.equal(p.hairstyle, "long_traced");
});

test("a face under the adult floor is lifted to it, and nothing else about it changes", () => {
  const p = paramsFromDict({ face_age: 0.2, hair_length: 0.3 });
  assert.equal(p.face_age, 0.9);
  assert.equal(p.hair_length, 0.3);
});

test("paramsToDict is the dict of the fields, nested, and a round trip through a link is the identity", () => {
  const p = PRESETS.katherina!;
  const d = paramsToDict(p);
  assert.equal(Object.keys(d).length, 32); // the registry: 29 fields until right_elbow and left_elbow, 31 until body_build
  assert.deepEqual(d.outfit, { ...p.outfit });
  assert.equal(paramsJsonText(decodeParams(encodeParams(p))), paramsJsonText(p));
  assert.ok(!encodeParams(p).includes("="));
});

test("a bad finish or strength raises ValueError with the documented text", () => {
  const link = (text: string): string => encodeParams(characterParams()).replace(/.*/, Buffer.from(text).toString("base64url"));
  assert.deepEqual(outcomeOf(() => decodeParams(link('{"finish":"x"}'))), { err: "ValueError", msg: "finish must be one of flat, soft, not 'x'" });
  assert.deepEqual(outcomeOf(() => decodeParams(link('{"finish":"soft","highlight_strength":2.5}'))), {
    err: "ValueError",
    msg: "highlight_strength must be between 0 and 2, not 2.5",
  });
  assert.ok(new PyError("ValueError", "m").pyType === "ValueError");
  void dumps;
});
