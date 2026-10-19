// The two whole-page compositions, the cover and the cast sheet, and their command lines (`bin/cover.ts`, `bin/sheet.ts`).
//
// The committed pages (`ref-out/cover.svg`, `sheet.svg`, `sheet_satoshi.svg`) are the golden output, drawn as
// `refresh-ref-out.sh` draws them: `--no-metadata`, with `ACC_LOCAL_DIR` pointing at nowhere. `fixtures/pages.json` holds the
// SHA-256 of what the frozen Python `cover.py` and `sheet.py` drew for a spread of other arguments (members, roster, columns,
// metadata, titles, sizes, expressions, a local face-age file), so the options stay pinned after the Python is gone.

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import { coverParams, mistBand, renderCover } from "../src/cover.ts";
import { replace } from "../src/model.ts";
import { PRESETS, ROSTERS } from "../src/presets.ts";
import { renderSheet, sheetParams } from "../src/sheet.ts";
import { REPO_ROOT, TS_ROOT, loadJson } from "./fixtures.ts";

const REF_OUT = join(REPO_ROOT, "ref-out");
const COVER = join(TS_ROOT, "bin", "cover.ts");
const SHEET = join(TS_ROOT, "bin", "sheet.ts");
const OUT = join(TS_ROOT, "out", "pages-test");
mkdirSync(OUT, { recursive: true });
const WORK = mkdtempSync(join(OUT, "run-"));

const read = (path: string): string => readFileSync(path, "utf8");
const ref = (name: string): string => read(join(REF_OUT, name));
const sha256 = (text: string): string => createHash("sha256").update(text, "utf8").digest("hex");

/** A folder holding the untracked `cover_faces.json`, as `ACC_LOCAL_DIR` can point at. */
const LOCAL = join(WORK, "local");
mkdirSync(LOCAL, { recursive: true });
writeFileSync(join(LOCAL, "cover_faces.json"), '{"satoko": 0.55, "kyoko": 1, "tomohiro": "0.7"}');
const NOWHERE = "/nonexistent";

/** Run a command line with `ACC_LOCAL_DIR` set, the way `refresh-ref-out.sh` does. */
function run(script: string, args: readonly string[], localDir = NOWHERE) {
  return spawnSync(process.execPath, [script, ...args], { encoding: "utf8", env: { ...process.env, ACC_LOCAL_DIR: localDir } });
}

/** The same, with the API: the lookup reads the environment when it is called. */
function withLocal<T>(localDir: string, fn: () => T): T {
  const before = process.env["ACC_LOCAL_DIR"];
  process.env["ACC_LOCAL_DIR"] = localDir;
  try {
    return fn();
  } finally {
    if (before === undefined) delete process.env["ACC_LOCAL_DIR"];
    else process.env["ACC_LOCAL_DIR"] = before;
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// The committed pages

test("ref-out/cover.svg is what the TypeScript draws", () => {
  assert.equal(
    withLocal(NOWHERE, () => renderCover()),
    ref("cover.svg"),
  );
});

test("ref-out/sheet.svg and sheet_satoshi.svg are what the TypeScript draws", () => {
  assert.equal(renderSheet(), ref("sheet.svg"));
  assert.equal(renderSheet(sheetParams({ roster: "satoshi" })), ref("sheet_satoshi.svg"));
});

test("cover.ts and sheet.ts write the committed pages, run as refresh-ref-out.sh runs them", () => {
  const cases: readonly [string, readonly string[], string][] = [
    [COVER, [], "cover"],
    [SHEET, [], "sheet"],
    [SHEET, ["--roster", "satoshi"], "sheet_satoshi"],
  ];
  for (const [script, extra, name] of cases) {
    const base = join(WORK, "committed", name);
    const r = run(script, [...extra, "--out", base, "--no-metadata"]);
    assert.equal(r.status, 0, r.stderr);
    assert.equal(r.stdout, `wrote ${base}.svg\n`);
    assert.equal(read(`${base}.svg`), ref(`${name}.svg`), name);
  }
});

// ---------------------------------------------------------------------------------------------------------------------
// What the frozen Python drew for other arguments

interface Case {
  kind: "cover" | "sheet";
  args: string[];
  local_faces: boolean;
  sha256: string;
  bytes: number;
}
const CASES = loadJson<{ cases: Case[] }>(join(TS_ROOT, "fixtures", "pages.json")).cases;

CASES.forEach((c, i) => {
  test(`${c.kind}.ts ${c.args.map((a) => JSON.stringify(a)).join(" ")}${c.local_faces ? " (with cover_faces.json)" : ""} is what the Python drew`, () => {
    const base = join(WORK, `fx${i}`);
    const r = run(c.kind === "cover" ? COVER : SHEET, [...c.args, "--out", base], c.local_faces ? LOCAL : NOWHERE);
    assert.equal(r.status, 0, r.stderr);
    const svg = read(`${base}.svg`);
    assert.equal(Buffer.byteLength(svg), c.bytes, "size");
    assert.equal(sha256(svg), c.sha256);
  });
});

// ---------------------------------------------------------------------------------------------------------------------
// The cover's options

test("a cover carries the metadata block only when asked, and it names the featured character", () => {
  const plain = withLocal(NOWHERE, () => renderCover());
  const meta = withLocal(NOWHERE, () => renderCover(null, true));
  assert.ok(!plain.includes("<metadata>"));
  assert.match(meta, /^<svg [^\n]*\n  <metadata>\n/);
  assert.equal(meta.replace(/  <metadata>\n[\s\S]*?  <\/metadata>\n/, ""), plain);
  assert.equal((meta.match(/<character>/g) ?? []).length, 1);
});

test("the cover's lines: a title line each, a subtitle under them, a byline at the foot, each drawn twice", () => {
  const count = (svg: string): number => (svg.match(/<text /g) ?? []).length;
  const one = coverParams({ title: ["ONE"], author: "", subtitle: "" });
  assert.equal(withLocal(NOWHERE, () => count(renderCover(one))), 2);
  assert.equal(withLocal(NOWHERE, () => count(renderCover(replace(one, { title: ["A", "B", "C"] })))), 6);
  assert.equal(withLocal(NOWHERE, () => count(renderCover(replace(one, { subtitle: "sub" })))), 4);
  assert.equal(withLocal(NOWHERE, () => count(renderCover(replace(one, { author: "me" })))), 4);
});

test("the expression is laid over the character, and none leaves the resting face", () => {
  const hollow = withLocal(NOWHERE, () => renderCover());
  const none = withLocal(NOWHERE, () => renderCover(coverParams({ expression: null })));
  const wry = withLocal(NOWHERE, () => renderCover(coverParams({ expression: "wry" })));
  assert.notEqual(hollow, none);
  assert.notEqual(hollow, wry);
  assert.throws(() => withLocal(NOWHERE, () => renderCover(coverParams({ expression: "nope" }))), /KeyError/);
});

test("an explicit character overrides the preset", () => {
  const risa = PRESETS["risa"]!;
  const a = withLocal(NOWHERE, () => renderCover(coverParams({ character: risa })));
  const b = withLocal(NOWHERE, () => renderCover(coverParams({ preset: "risa" })));
  assert.equal(a, b);
});

test("cover_faces.json in ACC_LOCAL_DIR sets a face age, and only for the preset it names", () => {
  const satoko = PRESETS["satoko"]!;
  const aged = withLocal(LOCAL, () => renderCover(coverParams({ preset: "satoko" })));
  assert.equal(aged, withLocal(NOWHERE, () => renderCover(coverParams({ character: replace(satoko, { face_age: 0.55 }) }))));
  assert.notEqual(aged, withLocal(NOWHERE, () => renderCover(coverParams({ preset: "satoko" }))));
  // A preset the file does not name is drawn as shipped, and so is an explicit character, whatever the file says.
  assert.equal(
    withLocal(LOCAL, () => renderCover(coverParams({ preset: "satoshi" }))),
    withLocal(NOWHERE, () => renderCover(coverParams({ preset: "satoshi" }))),
  );
  assert.equal(
    withLocal(LOCAL, () => renderCover(coverParams({ character: satoko }))),
    withLocal(NOWHERE, () => renderCover(coverParams({ character: satoko }))),
  );
  // The value may be an int, a float or a numeric string, as Python's `float()` takes it.
  const kyoko = PRESETS["kyoko"]!;
  assert.equal(
    withLocal(LOCAL, () => renderCover(coverParams({ preset: "kyoko" }))),
    withLocal(NOWHERE, () => renderCover(coverParams({ character: replace(kyoko, { face_age: 1 }) }))),
  );
});

test("a mist bank runs off both edges and is deterministic", () => {
  const a = mistBand(1000, 700, 800, "#2b3d41", 3, 0.055, 0.3);
  assert.equal(a, mistBand(1000, 700, 800, "#2b3d41", 3, 0.055, 0.3));
  assert.match(a, /^<path d="M -100\.0 1500\.0 L -100\.0 700\.0 A /);
  assert.match(a, / Z" fill="#2b3d41" \/>$/);
});

// ---------------------------------------------------------------------------------------------------------------------
// The sheet's options

const textsOf = (svg: string): string[] => [...svg.matchAll(/font-weight="bold" fill="#ffffff">([^<]*)<\/text>/g)].map((m) => m[1]!);

test("a sheet draws its roster, in order, one labelled tile each", () => {
  for (const roster of Object.keys(ROSTERS)) {
    const names = ROSTERS[roster]!;
    const svg = renderSheet(sheetParams({ roster }));
    assert.equal((svg.match(/fill="#f2f2f0" \/>/g) ?? []).length, names.length, roster);
    assert.equal(textsOf(svg).length, names.length, roster);
  }
  assert.deepEqual(textsOf(renderSheet(sheetParams({ roster: "everglow" }))), ["Gero", "Linnea"]);
});

test("--members overrides the roster, keeps its order, and a name twice is two tiles", () => {
  const svg = renderSheet(sheetParams({ members: ["viktor", "satoko", "viktor"], roster: "katherina" }));
  assert.deepEqual(textsOf(svg), ["Viktor Grau", "Satoko", "Viktor Grau"]);
});

test("a member that is not a preset is a KeyError naming it, not a shorter sheet", () => {
  assert.throws(() => renderSheet(sheetParams({ members: ["satoko", "nobody"] })), /KeyError: "roster names \['nobody'\], which are not in PRESETS"/);
  assert.throws(() => renderSheet(sheetParams({ roster: "nope" })), /KeyError: 'nope'/);
});

test("the page grows with the columns and the rows", () => {
  const size = (svg: string): [number, number] => {
    const m = svg.match(/^<svg [^>]*width="(\d+)" height="(\d+)"/)!;
    return [Number(m[1]), Number(m[2])];
  };
  // 14 tiles: width is margins + columns * tile + gaps, height is margins + rows * (label + tile) + gaps.
  assert.deepEqual(size(renderSheet()), [40 + 4 * 300 + 3 * 16, 40 + 4 * 460 + 3 * 16]);
  assert.deepEqual(size(renderSheet(sheetParams({ columns: 5 }))), [40 + 5 * 300 + 4 * 16, 40 + 3 * 460 + 2 * 16]);
  assert.deepEqual(size(renderSheet(sheetParams({ columns: 20 }))), [40 + 20 * 300 + 19 * 16, 40 + 460]);
  assert.deepEqual(size(renderSheet(sheetParams({ members: [] }))), [40 + 4 * 300 + 3 * 16, 40 + 460]);
  assert.throws(() => renderSheet(sheetParams({ columns: 0 })), /ZeroDivisionError/);
});

test("a long description breaks at a word boundary into tspans", () => {
  const svg = renderSheet(sheetParams({ members: ["krista"] }));
  assert.equal((svg.match(/<tspan /g) ?? []).length, 2);
  assert.match(svg, /Woden Crystal specialist and Woden head<\/tspan><tspan [^>]*>researcher, rank Magus-Sergeant<\/tspan>/);
});

test("a sheet's metadata names every member with its own link, and only when asked", () => {
  const members = ["satoko", "viktor", "risa"];
  const plain = renderSheet(sheetParams({ members }));
  const meta = renderSheet(sheetParams({ members }), true);
  assert.ok(!plain.includes("<metadata>"));
  assert.deepEqual(
    [...meta.matchAll(/<character name="([^"]*)">/g)].map((m) => m[1]),
    members,
  );
  assert.equal(meta.replace(/  <metadata>\n[\s\S]*?  <\/metadata>\n/, ""), plain);
});

// ---------------------------------------------------------------------------------------------------------------------
// The command lines

test("--metadata is on unless --no-metadata, and the last of the two on the line wins", () => {
  const draw = (script: string, args: string[], name: string): string => {
    const base = join(WORK, "flags", name);
    assert.equal(run(script, [...args, "--out", base]).status, 0);
    return read(`${base}.svg`);
  };
  for (const [script, kind] of [
    [COVER, "cover"],
    [SHEET, "sheet"],
  ] as const) {
    assert.match(draw(script, [], `${kind}-default`), /<metadata>/);
    assert.match(draw(script, ["--metadata"], `${kind}-on`), /<metadata>/);
    assert.doesNotMatch(draw(script, ["--no-metadata"], `${kind}-off`), /<metadata>/);
    assert.doesNotMatch(draw(script, ["--metadata", "--no-metadata"], `${kind}-last-off`), /<metadata>/);
    assert.match(draw(script, ["--no-metadata", "--metadata"], `${kind}-last-on`), /<metadata>/);
  }
});

test("--out replaces an extension, as Path.with_suffix does, and creates the directories", () => {
  for (const script of [COVER, SHEET]) {
    const base = join(WORK, "deep", "er", script === COVER ? "c" : "s");
    const r = run(script, ["--out", `${base}.png`, "--no-metadata"]);
    assert.equal(r.status, 0, r.stderr);
    assert.equal(r.stdout, `wrote ${base}.svg\n`);
    assert.ok(read(`${base}.svg`).startsWith("<svg "));
  }
});

test("a bad argument exits 2 with a message, as argparse does", () => {
  const bad: readonly [string, string[], RegExp][] = [
    [COVER, ["--preset", "zzz"], /argument --preset: invalid choice: 'zzz' \(choose from chiyo, /],
    [COVER, ["--expression", "zzz"], /argument --expression: invalid choice: 'zzz'/],
    [COVER, ["--width", "wide"], /argument --width: invalid float value: 'wide'/],
    [SHEET, ["--roster", "zzz"], /argument --roster: invalid choice: 'zzz' \(choose from bureaucracy, cast, /],
    [SHEET, ["--columns", "four"], /argument --columns: invalid int value: 'four'/],
    [SHEET, ["--nope"], /nope/],
  ];
  for (const [script, args, message] of bad) {
    const r = run(script, [...args, "--out", join(WORK, "bad")]);
    assert.equal(r.status, 2, args.join(" "));
    assert.match(r.stderr, message);
  }
});

test("an unknown member is Python's KeyError line and exit 1, not a Node stack", () => {
  const r = run(SHEET, ["--members", "satoko,nobody", "--out", join(WORK, "bad")]);
  assert.equal(r.status, 1);
  assert.equal(r.stderr, `KeyError: "roster names ['nobody'], which are not in PRESETS"\n`);
});
