// Run the STAGED, compiled JavaScript (what a browser would load) in Node, as plain ES modules: no type stripping.
//   node web-check/stage.mjs && node web-check/run-staged.mjs
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const out = join(dirname(fileURLToPath(import.meta.url)), "..", "out", "web-check");
const { runChecks } = await import(pathToFileURL(join(out, "js", "web-check", "check.js")).href);
const results = await runChecks(async (p) => JSON.parse(await readFile(join(out, p.replace(/^\.\.\//, "")), "utf8")));
let failed = 0;
for (const r of results) {
  console.log(`${r.bad === 0 ? "ok  " : "FAIL"} ${r.name}: ${r.total - r.bad}/${r.total}`);
  if (r.bad) failed++;
}
console.log(failed === 0 ? `compiled JS: all ${results.length} checks match Python` : `${failed} checks differ`);
process.exitCode = failed ? 1 : 0;
