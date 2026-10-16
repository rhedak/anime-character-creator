// Run the cross-engine check in Node: `node web-check/run.ts` from `ts/`.

import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { runChecks } from "./check.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const results = await runChecks(
  async (p) => JSON.parse(await readFile(join(root, p), "utf8")),
  (p) => readFile(join(root, p), "utf8"),
);
let failed = 0;
for (const r of results) {
  console.log(`${r.bad === 0 ? "ok  " : "FAIL"} ${r.name}: ${r.total - r.bad}/${r.total}${r.first.length ? "  e.g. " + r.first.join(" | ") : ""}`);
  if (r.bad) failed++;
}
console.log(`node ${process.version} (V8 ${process.versions.v8}): ${failed === 0 ? "all checks pass" : failed + " checks fail"}`);
process.exitCode = failed ? 1 : 0;
