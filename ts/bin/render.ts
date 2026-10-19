// The SVG command line: render one character to `BASE.svg`. The TypeScript counterpart of the SVG half of
// `generate.py`, and byte for byte the same SVG for the same arguments (the metadata block included, which is on by default).
//
//   node ts/bin/render.ts --out out/satoko --preset satoko
//   node ts/bin/render.ts --out out/x --preset risa --finish soft --highlight-strength 0.7 --background white --no-metadata
//   node ts/bin/render.ts --list            the names --preset takes, one line (--list-presets, --list-bases: one kind)
//
// What it has: --preset (a name from PRESETS or NEUTRAL_BASES, or an ADULT_PRESETS name, which --list does not show), --out (a path prefix, no extension; directories are
// created), --background (any SVG paint), --metadata / --no-metadata, --finish, --highlight-strength and --id-prefix.
// `generate.py` has no --id-prefix, --params-json or --link; the first is added here because `render_character` takes it
// and a page of several figures needs it, the other two do not exist in the Python and are not invented.
//
// What it does not have, on purpose: PNG (scripts make it from this SVG with `harness/svg2png.py`), the colour, garment,
// face and shape flags, --expression and --flat (use a preset, or the TypeScript API), cover, sheet and comic.
//
// Exit codes follow the Python CLI's argparse: 2 for a bad argument (a message on stderr), 0 on success.

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, extname } from "node:path";
import { parseArgs } from "node:util";
import { FINISHES, characterParams, replace, validateFinish } from "../src/model.ts";
import type { CharacterParams } from "../src/params.ts";
import { ADULT_PRESETS, NEUTRAL_BASES, PRESETS } from "../src/presets.ts";
import { PyError, pyFloat } from "../src/pynum.ts";
import { renderCharacter } from "../src/render.ts";

const PROG = "render.ts";

function fail(message: string): never {
  process.stderr.write(`usage: node ts/bin/render.ts [--out BASE] [--preset NAME] [--finish {${FINISHES.join(",")}}]\n`);
  process.stderr.write(`       [--highlight-strength X] [--background PAINT] [--id-prefix PREFIX] [--metadata | --no-metadata]\n       [--list | --list-presets | --list-bases]\n`);
  process.stderr.write(`${PROG}: error: ${message}\n`);
  process.exit(2);
}

function main(): void {
  let values;
  try {
    ({ values } = parseArgs({
      options: {
        out: { type: "string" },
        preset: { type: "string" },
        background: { type: "string" },
        metadata: { type: "boolean" },
        "no-metadata": { type: "boolean" },
        finish: { type: "string" },
        "highlight-strength": { type: "string" },
        "id-prefix": { type: "string" },
        list: { type: "boolean" },
        "list-presets": { type: "boolean" },
        "list-bases": { type: "boolean" },
      },
      strict: true,
      allowPositionals: false,
    }));
  } catch (e) {
    fail((e as Error).message);
  }

  const starts: Record<string, CharacterParams> = { ...PRESETS, ...NEUTRAL_BASES };
  const listing = values.list ? starts : values["list-presets"] ? PRESETS : values["list-bases"] ? NEUTRAL_BASES : null;
  if (listing !== null) {
    process.stdout.write(`${Object.keys(listing).sort().join(" ")}\n`);
    return;
  }
  if (values.metadata && values["no-metadata"]) fail("argument --no-metadata: not allowed with argument --metadata");
  const metadata = !values["no-metadata"];

  let base: CharacterParams | undefined;
  if (values.preset !== undefined) {
    base = starts[values.preset] ?? ADULT_PRESETS[values.preset]; // an adult preset is taken by name but not listed (stage 7 lists it)
    if (base === undefined) fail(`argument --preset: invalid choice: '${values.preset}' (choose from ${Object.keys(starts).sort().map((n) => `'${n}'`).join(", ")})`);
  }
  if (values.finish !== undefined && !FINISHES.some((f) => f === values.finish)) {
    fail(`argument --finish: invalid choice: '${values.finish}' (choose from ${FINISHES.map((f) => `'${f}'`).join(", ")})`);
  }
  let strength: number | undefined;
  if (values["highlight-strength"] !== undefined) {
    try {
      strength = pyFloat(values["highlight-strength"]);
    } catch {
      fail(`argument --highlight-strength: invalid float value: '${values["highlight-strength"]}'`);
    }
  }

  // The same order as generate.py: the base, then shaded, finish and strength laid over it, then the finish checked.
  const start = base ?? characterParams();
  const params = replace(start, {
    shaded: true,
    finish: (values.finish ?? start.finish) as CharacterParams["finish"],
    highlight_strength: strength ?? start.highlight_strength,
  });
  try {
    validateFinish(params);
  } catch (e) {
    if (e instanceof PyError) fail(e.message.replace(/^ValueError: /, ""));
    throw e;
  }

  const svg = renderCharacter(params, null, values.background ?? null, metadata, values["id-prefix"] ?? "");
  // Python's `Path(out).with_suffix(".svg")`: an existing extension is replaced, not kept.
  const out = values.out ?? "out/character";
  const svgPath = `${out.slice(0, out.length - extname(out).length)}.svg`;
  mkdirSync(dirname(svgPath), { recursive: true });
  writeFileSync(svgPath, svg, "utf8");
  process.stdout.write(`wrote ${svgPath}\n`);
}

main();
