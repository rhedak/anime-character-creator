// Assemble the deployable site into out/web-stage/, flat. The replacement of web-stage.sh for the TypeScript package.
//
// web/index.html fetches "ref-out/catalogue.json" and imports the drawing from "js/web-bridge.js" as plain relative paths, which
// only resolve if those sit beside index.html at whatever root serves the page. They are not siblings in the repository, on
// purpose (CLAUDE.md keeps the site out of anything that looks like working notes), so this copies the page, ref-out/ and the
// compiled package into one flat directory, which is what a local test server and the GitHub Actions deploy both serve.
//
//   node web-stage.mjs            stage into out/web-stage/
//   node web-stage.mjs --serve    stage, then serve it on http://127.0.0.1:8000
//   node web-stage.mjs --adult    also offer the adult woman (Franzi, her body and cut) in the staged copy only: a local preview.
//                                 ref-out/ and the deployed site do not change.
//
// The package is compiled with `tsc` (ts/tsconfig.web.json): it rewrites the `.ts` import specifiers to `.js`, which a browser
// needs and Node's type stripper does not do. Set TSC to a tsc binary if ts/node_modules/.bin/tsc is not there. Nothing is deleted:
// files are overwritten.

import { execFileSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const stage = join(root, "out", "web-stage");
const tsc = process.env.TSC ?? join(root, "ts", "node_modules", ".bin", "tsc");
if (!existsSync(tsc)) throw new Error(`no tsc at ${tsc}: run "npm install" in ts/, or set TSC`);

mkdirSync(stage, { recursive: true });
execFileSync(tsc, ["-p", join(root, "ts", "tsconfig.web.json")], { stdio: "inherit" });
for (const f of readdirSync(join(root, "web"))) {
  if (/\.(html|css|js)$/.test(f)) cpSync(join(root, "web", f), join(stage, f));
}
cpSync(join(root, "ref-out"), join(stage, "ref-out"), { recursive: true });
if (process.argv.includes("--adult")) {
  // The staged copy's catalogue gains Franzi, the adult body and her cut, and her gallery picture is drawn beside the others.
  execFileSync(process.execPath, [join(root, "ts", "bin", "catalogue.ts"), "--adult", join(stage, "ref-out", "catalogue.json")], { stdio: "inherit" });
  execFileSync(process.execPath, [join(root, "ts", "bin", "render.ts"), "--out", join(stage, "ref-out", "franzi"), "--preset", "franzi", "--no-metadata"], { stdio: "inherit" });
}
console.log("staged at", stage);

if (process.argv.includes("--serve")) {
  console.log("serving http://127.0.0.1:8000/ (Ctrl-C to stop)");
  execFileSync("python3", ["-m", "http.server", "8000", "--bind", "127.0.0.1", "--directory", stage], { stdio: "inherit" });
}
