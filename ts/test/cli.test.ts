// The two command line tools in `bin/`, run as the scripts run them (`node bin/render.ts`, `node bin/catalogue.ts`).
//
// `bin/render.ts` has to write the committed art (`ref-out/`, made with `--no-metadata`) byte for byte, and keep the options
// it documents. The files under `ref-out/` are the golden output.

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import { NEUTRAL_BASES, PRESETS } from "../src/presets.ts";
import { REPO_ROOT, TS_ROOT } from "./fixtures.ts";

const RENDER = join(TS_ROOT, "bin", "render.ts");
const CATALOGUE = join(TS_ROOT, "bin", "catalogue.ts");
const OUT = join(TS_ROOT, "out", "cli-test");
mkdirSync(OUT, { recursive: true });

const node = (script: string, args: readonly string[]) => spawnSync(process.execPath, [script, ...args], { encoding: "utf8" });
const render = (args: readonly string[]) => node(RENDER, args);
const read = (path: string): string => readFileSync(path, "utf8");

for (const name of Object.keys(PRESETS).sort()) {
  test(`render.ts --preset ${name} --no-metadata is ref-out/${name}.svg`, () => {
    const base = join(OUT, name);
    const r = render(["--out", base, "--preset", name, "--no-metadata"]);
    assert.equal(r.status, 0, r.stderr);
    assert.equal(r.stdout, `wrote ${base}.svg\n`);
    assert.equal(read(`${base}.svg`), read(join(REPO_ROOT, "ref-out", `${name}.svg`)));
  });
}

for (const name of Object.keys(NEUTRAL_BASES).sort()) {
  test(`render.ts --preset ${name} --no-metadata is ref-out/bases/${name}.svg`, () => {
    const base = join(OUT, `base-${name}`);
    assert.equal(render(["--out", base, "--preset", name, "--no-metadata"]).status, 0);
    assert.equal(read(`${base}.svg`), read(join(REPO_ROOT, "ref-out", "bases", `${name}.svg`)));
  });
}

test("render.ts creates the directories of --out", () => {
  const base = join(OUT, "deep", "er", "satoko");
  assert.equal(render(["--out", base, "--preset", "satoko", "--no-metadata"]).status, 0);
  assert.ok(existsSync(`${base}.svg`));
});

test("render.ts replaces an extension on --out, as Path.with_suffix does", () => {
  const base = join(OUT, "ext");
  assert.equal(render(["--out", `${base}.png`, "--preset", "satoko", "--no-metadata"]).status, 0);
  assert.ok(existsSync(`${base}.svg`));
});

test("render.ts embeds the metadata block unless told not to", () => {
  const withMeta = join(OUT, "meta-on");
  const without = join(OUT, "meta-off");
  assert.equal(render(["--out", withMeta, "--preset", "satoko"]).status, 0);
  assert.equal(render(["--out", without, "--preset", "satoko", "--no-metadata"]).status, 0);
  assert.equal(render(["--out", join(OUT, "meta-flag"), "--preset", "satoko", "--metadata"]).status, 0);
  assert.equal(read(`${withMeta}.svg`), read(join(OUT, "meta-flag.svg")));
  assert.match(read(`${withMeta}.svg`), /<metadata>/);
  assert.doesNotMatch(read(`${without}.svg`), /<metadata>/);
});

test("render.ts with no preset draws the default character, with metadata", () => {
  const base = join(OUT, "default");
  assert.equal(render(["--out", base]).status, 0);
  assert.match(read(`${base}.svg`), /<metadata>/);
});

test("render.ts --finish, --highlight-strength and --background change the drawing the way they say", () => {
  const draw = (name: string, args: readonly string[]): string => {
    const base = join(OUT, `opts-${name}`);
    const r = render(["--out", base, "--preset", "risa", "--no-metadata", ...args]);
    assert.equal(r.status, 0, r.stderr);
    return read(`${base}.svg`);
  };
  const flat = draw("flat", []);
  const soft = draw("soft", ["--finish", "soft"]);
  const strong = draw("strong", ["--finish", "soft", "--highlight-strength", "2"]);
  const none = draw("none", ["--finish", "soft", "--highlight-strength", "0"]);
  assert.notEqual(soft, flat);
  assert.notEqual(strong, soft);
  assert.notEqual(none, soft);
  assert.equal(draw("flat2", ["--finish", "flat", "--highlight-strength", "1.5"]), flat, "flat ignores the strength");
  assert.notEqual(draw("white", ["--background", "white"]), flat);
  assert.notEqual(draw("ink", ["--background", "#101820"]), draw("white", ["--background", "white"]));
  assert.match(draw("transparent", ["--background", "none"]), /<rect width="100%" height="100%" fill="none" \/>/);
});

test("render.ts --id-prefix puts the prefix on every id it defines, and takes it literally", () => {
  // (A backslash followed by a digit is not taken literally: the prefix goes through a replacement template, as it did in Python, so `back\1` is mangled. Not pinned here.)
  for (const prefix of ["a", "fig-1", "x$&y"]) {
    const base = join(OUT, "prefix");
    assert.equal(render(["--out", base, "--preset", "satoko", "--no-metadata", "--id-prefix", prefix]).status, 0);
    const ids = [...read(`${base}.svg`).matchAll(/ id="([^"]*)"/g)].map((m) => m[1]!);
    assert.ok(ids.length > 0);
    for (const id of ids) assert.ok(id.startsWith(`${prefix}-`), `${id} lacks the prefix ${prefix}`);
  }
});

test("render.ts refuses bad arguments with exit code 2", () => {
  for (const args of [
    ["--preset", "nobody"],
    ["--finish", "rough"],
    ["--finish", "soft", "--highlight-strength", "3"],
    ["--finish", "soft", "--highlight-strength=-0.5"],
    ["--highlight-strength", "abc"],
    ["--bogus"],
    ["--metadata", "--no-metadata"],
  ]) {
    const r = render(["--out", join(OUT, "never"), ...args]);
    assert.equal(r.status, 2, args.join(" "));
    assert.match(r.stderr, /render\.ts: error: /);
  }
  assert.equal(existsSync(join(OUT, "never.svg")), false);
});

test("render.ts --list names every preset and neutral base", () => {
  const r = render(["--list"]);
  assert.equal(r.status, 0);
  assert.deepEqual(r.stdout.trim().split(" "), [...Object.keys(PRESETS), ...Object.keys(NEUTRAL_BASES)].sort());
});

test("render.ts --list-presets and --list-bases name each kind, sorted", () => {
  assert.equal(render(["--list-presets"]).stdout, `${Object.keys(PRESETS).sort().join(" ")}\n`);
  assert.equal(render(["--list-bases"]).stdout, `${Object.keys(NEUTRAL_BASES).sort().join(" ")}\n`);
});

test("catalogue.ts to stdout is ref-out/catalogue.json", () => {
  const r = node(CATALOGUE, []);
  assert.equal(r.status, 0, r.stderr);
  assert.equal(r.stdout, read(join(REPO_ROOT, "ref-out", "catalogue.json")));
});

test("catalogue.ts to a file is ref-out/catalogue.json", () => {
  const path = join(OUT, "sub", "catalogue.json");
  assert.equal(node(CATALOGUE, [path]).status, 0);
  assert.equal(read(path), read(join(REPO_ROOT, "ref-out", "catalogue.json")));
});
