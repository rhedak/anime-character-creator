// The two command line tools in `bin/`, run as the scripts run them (`node bin/render.ts`, `node bin/catalogue.ts`).
//
// `bin/render.ts` has to write the SVG the Python CLI writes for the same arguments: the committed art (`ref-out/`, made
// with `--no-metadata`), and, wherever the frozen Python is installed (`.venv` at the repository root, as `uv sync` makes it),
// a fresh run of it, which is the only place the default with metadata and the soft options can be compared.

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

const PYTHON = join(REPO_ROOT, ".venv", "bin", "python");
const havePython = existsSync(PYTHON);
const skipNoPython = havePython ? false : "no .venv at the repository root (uv sync makes it)";
const pyEnv = { ...process.env, PYTHONDONTWRITEBYTECODE: "1", PYTHONPATH: join(REPO_ROOT, "src") };

/** The Python CLI, through `render.sh` as the scripts use it (it also writes a PNG, which is ignored here). */
function pythonCli(base: string, args: readonly string[]): string {
  const r = spawnSync(join(REPO_ROOT, "render.sh"), ["--out", base, ...args], { encoding: "utf8", env: pyEnv });
  assert.equal(r.status, 0, r.stderr);
  return read(`${base}.svg`);
}

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

test("render.ts with metadata (the default) is what the Python CLI writes", { skip: skipNoPython }, () => {
  for (const name of ["satoko", "katherina", "risa"]) {
    const base = join(OUT, `py-${name}`);
    assert.equal(render(["--out", `${base}-ts`, "--preset", name]).status, 0);
    assert.equal(read(`${base}-ts.svg`), pythonCli(`${base}-py`, ["--preset", name]), name);
  }
});

test("render.ts with no preset is what the Python CLI writes for the default character", { skip: skipNoPython }, () => {
  const base = join(OUT, "py-default");
  assert.equal(render(["--out", `${base}-ts`]).status, 0);
  assert.equal(read(`${base}-ts.svg`), pythonCli(`${base}-py`, []));
});

test("render.ts --finish, --highlight-strength and --background are what the Python CLI writes", { skip: skipNoPython }, () => {
  const cases: string[][] = [
    ["--preset", "risa", "--finish", "soft", "--highlight-strength", "0.7", "--background", "white"],
    ["--preset", "satoko", "--finish", "soft"],
    ["--preset", "keiko", "--finish", "soft", "--highlight-strength", "0", "--no-metadata"],
    ["--preset", "tenno", "--finish", "soft", "--highlight-strength", "2", "--background", "#101820"],
    ["--preset", "elara", "--finish", "flat", "--highlight-strength", "1.5"],
    ["--preset", "viktor", "--background", "none", "--no-metadata"],
  ];
  cases.forEach((args, i) => {
    const base = join(OUT, `py-opts-${i}`);
    assert.equal(render(["--out", `${base}-ts`, ...args]).status, 0, args.join(" "));
    assert.equal(read(`${base}-ts.svg`), pythonCli(`${base}-py`, args), args.join(" "));
  });
});

test("render.ts --id-prefix is what render_character(id_prefix=) writes", { skip: skipNoPython }, () => {
  for (const prefix of ["a", "fig-1", "x$&y", "back\\1"]) {
    const base = join(OUT, "prefix");
    assert.equal(render(["--out", base, "--preset", "satoko", "--no-metadata", "--id-prefix", prefix]).status, 0);
    const code = "import sys\nfrom anime_character_creator import PRESETS, render_character\nsys.stdout.write(render_character(PRESETS['satoko'], id_prefix=sys.argv[1]))\n";
    const py = spawnSync(PYTHON, ["-c", code, prefix], { encoding: "utf8", env: pyEnv });
    assert.equal(py.status, 0, py.stderr);
    assert.equal(read(`${base}.svg`), py.stdout, prefix);
  }
});

test("render.ts refuses what the Python CLI refuses, with exit code 2", () => {
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

test("catalogue.ts equals the Python catalogue module", { skip: skipNoPython }, () => {
  const py = spawnSync(PYTHON, ["-m", "anime_character_creator.catalogue"], { encoding: "utf8", env: pyEnv });
  assert.equal(py.status, 0, py.stderr);
  assert.equal(node(CATALOGUE, []).stdout, py.stdout);
});
