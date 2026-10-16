// Stage the cross-engine check page into `out/web-check/`, ready to serve as static files:
//
//   node web-check/stage.mjs [--serve]        (set TSC to a tsc binary if node_modules/.bin/tsc is absent)
//
// `tsc` compiles the TypeScript to JavaScript with the `.ts` import specifiers rewritten to `.js`, which is what a
// browser needs and what Node's type stripper does not do. Nothing is deleted; files are overwritten.

import { execFileSync } from "node:child_process";
import { cpSync, mkdirSync, copyFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ts = join(dirname(fileURLToPath(import.meta.url)), "..");
const repo = join(ts, "..");
const out = join(ts, "out", "web-check");
const tsc = process.env.TSC ?? join(ts, "node_modules", ".bin", "tsc");

execFileSync(tsc, ["-p", ts, "--noEmit", "false", "--outDir", join(out, "js"), "--rootDir", ts], { stdio: "inherit" });
mkdirSync(join(out, "fixtures"), { recursive: true });
for (const f of ["synthetic.json", "colors.json", "skeleton-sweep.json", "headshape-sweep.json"]) copyFileSync(join(ts, "fixtures", f), join(out, "fixtures", f));
mkdirSync(join(out, "harness", "ts_port", "corpus"), { recursive: true });
mkdirSync(join(out, "harness", "ts_port", "manifest"), { recursive: true });
copyFileSync(join(repo, "harness/ts_port/corpus/mini.json"), join(out, "harness/ts_port/corpus/mini.json"));
copyFileSync(join(repo, "harness/ts_port/manifest/mini.json"), join(out, "harness/ts_port/manifest/mini.json"));
copyFileSync(join(repo, "harness/ts_port/manifest/full.json"), join(out, "harness/ts_port/manifest/full.json"));
copyFileSync(join(repo, "harness/ts_port/corpus/full.json"), join(out, "harness/ts_port/corpus/full.json"));
copyFileSync(join(ts, "web-check", "index.html"), join(out, "index.html"));
console.log("staged at", out);
if (process.argv.includes("--serve")) {
  console.log("serving http://127.0.0.1:8765/ (Ctrl-C to stop)");
  execFileSync("python3", ["-m", "http.server", "8765", "--bind", "127.0.0.1", "--directory", out], { stdio: "inherit" });
}
void cpSync;
