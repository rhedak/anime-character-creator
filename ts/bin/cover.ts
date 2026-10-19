// The cover command line: render a book cover around one character to `BASE.svg`. The TypeScript counterpart of the SVG half
// of `cover.py`, and byte for byte the same SVG for the same arguments (the metadata block included, which is on by default).
//
//   node ts/bin/cover.ts
//   node ts/bin/cover.ts --out out/x --preset satoko --title "THE HERO" --title "OF THE MIST" --no-metadata
//
// Flags as `cover.py`: --out, --preset, --title (repeat it, the line breaks are yours), --subtitle, --author, --expression,
// --no-expression, --width, --height, --metadata / --no-metadata. The one place a face age is overridden is
// `local/cover_faces.json`, and `ACC_LOCAL_DIR` moves that folder (`refresh-ref-out.sh` points it at nowhere).
//
// What it does not have: PNG, which a script makes from this SVG with `harness/svg2png.py`, as for `render.ts`.
//
// Exit codes follow the Python CLI's argparse: 2 for a bad argument (a message on stderr), 0 on success.

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { parseArgs } from "node:util";
import { coverParams, renderCover } from "../src/cover.ts";
import { replace } from "../src/model.ts";
import { choiceArg, floatArg, lastOf, runMain, withSuffix } from "../src/pagecli.ts";
import { EXPRESSIONS, PRESETS } from "../src/presets.ts";
import { sorted } from "../src/pynum.ts";

const PROG = "cover.ts";
const USAGE =
  `usage: node ts/bin/${PROG} [-h] [--out OUT] [--preset PRESET] [--title TITLE] [--subtitle SUBTITLE] [--author AUTHOR]\n` +
  `       [--expression EXPRESSION] [--no-expression] [--width WIDTH] [--height HEIGHT] [--metadata | --no-metadata]\n`;

function fail(message: string): never {
  process.stderr.write(USAGE);
  process.stderr.write(`${PROG}: error: ${message}\n`);
  process.exit(2);
}

function main(): void {
  let parsed;
  try {
    parsed = parseArgs({
      options: {
        help: { type: "boolean", short: "h" },
        out: { type: "string" },
        preset: { type: "string" },
        title: { type: "string", multiple: true },
        subtitle: { type: "string" },
        author: { type: "string" },
        expression: { type: "string" },
        "no-expression": { type: "boolean" },
        width: { type: "string" },
        height: { type: "string" },
        metadata: { type: "boolean" },
        "no-metadata": { type: "boolean" },
      },
      strict: true,
      allowPositionals: false,
      tokens: true,
    });
  } catch (e) {
    fail((e as Error).message);
  }
  const { values, tokens } = parsed;
  if (values.help) {
    process.stdout.write(`${USAGE}\nRender a book cover around one character.\n`);
    return;
  }

  let p = coverParams();
  const presetNames = sorted(Object.keys(PRESETS));
  const preset = choiceArg("--preset", values.preset ?? "satoshi", presetNames, fail);
  const expressionNames = sorted(Object.keys(EXPRESSIONS));
  const expression = values.expression === undefined ? undefined : choiceArg("--expression", values.expression, expressionNames, fail);
  const width = values.width === undefined ? 1000.0 : floatArg("--width", values.width, fail);
  const height = values.height === undefined ? 1500.0 : floatArg("--height", values.height, fail);
  p = replace(p, { preset, width, height });
  if (values.title && values.title.length > 0) p = replace(p, { title: values.title });
  p = replace(p, { subtitle: values.subtitle ?? "" });
  if (values.author !== undefined) p = replace(p, { author: values.author });
  if (values["no-expression"]) p = replace(p, { expression: null });
  else if (expression) p = replace(p, { expression });

  const metadata = lastOf(tokens, "metadata", "no-metadata", true);
  const svg = renderCover(p, metadata);
  const svgPath = withSuffix(values.out ?? "out/cover/cover", ".svg");
  mkdirSync(dirname(svgPath), { recursive: true });
  writeFileSync(svgPath, svg, "utf8");
  process.stdout.write(`wrote ${svgPath}\n`);
}

runMain(main);
