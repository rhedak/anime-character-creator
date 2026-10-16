// Write the web tool's catalogue (`ref-out/catalogue.json`) from the TypeScript package: `toJson()` of `catalogue.ts`, which is
// `python -m anime_character_creator.catalogue` byte for byte.
//
//   node ts/bin/catalogue.ts                 to stdout
//   node ts/bin/catalogue.ts out/cat.json    to a file (directories are created)

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { toJson } from "../src/catalogue.ts";

const args = process.argv.slice(2);
if (args.length > 1 || args[0] === "--help" || args[0] === "-h") {
  process.stderr.write("usage: node ts/bin/catalogue.ts [PATH]\n");
  process.exit(args.length > 1 ? 2 : 0);
}
const path = args[0];
if (path === undefined) {
  process.stdout.write(toJson());
} else {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, toJson(), "utf8");
}
