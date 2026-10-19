// The sheet command line: render the cast as a labelled grid to `BASE.svg`. The TypeScript counterpart of the SVG half of
// `sheet.py`, and byte for byte the same SVG for the same arguments (the metadata block included, which is on by default).
//
//   node ts/bin/sheet.ts
//   node ts/bin/sheet.ts --out out/sheet/wide --columns 5 --roster satoshi --no-metadata
//   node ts/bin/sheet.ts --members satoko,viktor,reika
//
// Flags as `sheet.py`: --out, --roster, --columns, --members (comma-separated preset names, overrides --roster) and
// --metadata / --no-metadata.
//
// What it does not have: PNG, which a script makes from this SVG with `harness/svg2png.py`, as for `render.ts`.
//
// Exit codes follow the Python CLI's argparse: 2 for a bad argument (a message on stderr), 0 on success.

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { parseArgs } from "node:util";
import { replace } from "../src/model.ts";
import { choiceArg, intArg, lastOf, runMain, withSuffix } from "../src/pagecli.ts";
import { ROSTERS } from "../src/presets.ts";
import { sorted } from "../src/pynum.ts";
import { renderSheet, sheetParams } from "../src/sheet.ts";

const PROG = "sheet.ts";
const USAGE =
  `usage: node ts/bin/${PROG} [-h] [--out OUT] [--roster ROSTER] [--columns COLUMNS] [--members MEMBERS]\n` +
  `       [--metadata | --no-metadata]\n`;

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
        roster: { type: "string" },
        columns: { type: "string" },
        members: { type: "string" },
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
    process.stdout.write(`${USAGE}\nRender the cast as a labelled grid.\n`);
    return;
  }

  const roster = choiceArg("--roster", values.roster ?? "cast", sorted(Object.keys(ROSTERS)), fail);
  const columns = values.columns === undefined ? 4 : intArg("--columns", values.columns, fail);
  const members = values.members ? values.members.split(",").map((m) => m.trim()) : null;
  const p = replace(sheetParams(), { roster, columns, members });

  const metadata = lastOf(tokens, "metadata", "no-metadata", true);
  const svg = renderSheet(p, metadata);
  const svgPath = withSuffix(values.out ?? "out/sheet/sheet", ".svg");
  mkdirSync(dirname(svgPath), { recursive: true });
  writeFileSync(svgPath, svg, "utf8");
  process.stdout.write(`wrote ${svgPath}\n`);
}

runMain(main);
