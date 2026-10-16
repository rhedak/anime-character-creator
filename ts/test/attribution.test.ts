// `attribution.ts` against Python: the `<metadata>` block, the header it shares, `escape`, and what
// `render_character(metadata=True)` puts after the `<svg>` line.

import assert from "node:assert/strict";
import { test } from "node:test";
import { skeletonFor } from "../src/body.ts";
import { documentWrap } from "../src/character.ts";
import { LICENSE_STATEMENT, NOVEL_TITLE, NOVEL_URL, REPOSITORY_URL, TOOL_URL, escape, metadataBlock, metadataHeader } from "../src/attribution.ts";
import { characterUrl } from "../src/urlstate.ts";
import { fixture, paramsFromDiff } from "./phase3.ts";

const fx = fixture("metadata.json");

test("the constants and the shared header are Python's", () => {
  assert.equal(TOOL_URL, fx.constants.TOOL_URL);
  assert.equal(REPOSITORY_URL, fx.constants.REPOSITORY_URL);
  assert.equal(LICENSE_STATEMENT, fx.constants.LICENSE_STATEMENT);
  assert.equal(NOVEL_TITLE, fx.constants.NOVEL_TITLE);
  assert.equal(NOVEL_URL, fx.constants.NOVEL_URL);
  assert.equal(metadataHeader(), fx.constants.header);
});

test("escape equals xml.sax.saxutils.escape, plain and with an entity table", () => {
  assert.ok(fx.escapes.length >= 10);
  for (const c of fx.escapes) {
    assert.equal(escape(c.text), c.plain, c.text);
    assert.equal(escape(c.text, { '"': "&quot;" }), c.quot, c.text);
    assert.equal(escape(c.text, { '"': "&quot;", "'": "&apos;" }), c.two, c.text);
  }
});

test("metadata_block is byte for byte Python's for 60 and more characters, and sits in the document where Python puts it", () => {
  assert.ok(fx.cases.length >= 60);
  const bad: string[] = [];
  for (const c of fx.cases) {
    const p = paramsFromDiff(c.diff);
    const block = metadataBlock(p);
    if (block !== c.block) bad.push(`${c.label}: block`);
    // `render_character` writes `"  " + block + "\n"` straight after the `<svg ...>` line: the wrapper does the same.
    const doc = documentWrap(skeletonFor(p), "", null, block);
    if (!doc.startsWith(`${c.svg_line}\n  ${c.block}\n`)) bad.push(`${c.label}: document`);
    if (!block.includes(`<character>${characterUrl(p, TOOL_URL).replace(/&/g, "&amp;")}</character>`)) bad.push(`${c.label}: url`);
  }
  assert.deepEqual(bad, []);
});

test("the characters of the metadata fixture are varied: soft and flat, presets and made-up ones", () => {
  const blocks = new Set(fx.cases.map((c: { block: string }) => c.block));
  assert.equal(blocks.size, fx.cases.length);
  assert.ok(fx.cases.some((c: { diff: string }) => c.diff.includes('"finish":"soft"')));
});
