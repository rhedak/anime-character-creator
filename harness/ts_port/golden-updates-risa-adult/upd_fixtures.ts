// Updates the two recorded fixtures that held the old Risa (docs/risa-adult-plan.md): her entry in fixtures/presets.json and the three cases of fixtures/pages.json that draw her. Run from ts/:
//
//     node ../harness/ts_port/golden-updates-risa-adult/upd_fixtures.ts
//
// The Python these were recorded from is gone and Risa is not the same character any more (a new body, hair, face and every garment), so the entries are not derived from the old ones by a rule: they are
// computed from the new code, in the way the tests read them (`paramsJsonText` and a JSON round trip of the preset for presets.json; the page scripts run as pages.test.ts runs them, with ACC_LOCAL_DIR pointing at nowhere,
// for pages.json). Nothing else in either file is touched; the script prints every key it changed and checks the rest is byte for byte as it was.
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { PRESETS } from "../../../ts/src/presets.ts";
import { paramsJsonText } from "../../../ts/src/urlstate.ts";

const TS = join(import.meta.dirname, "..", "..", "..", "ts");

// ---- presets.json: only the text of Risa's entry in `presets` is replaced (the file keeps float spellings like 1.0 that JSON.stringify would lose, so it is not re-serialised)
const pPath = join(TS, "fixtures", "presets.json");
const text = readFileSync(pPath, "utf8");
const start = text.indexOf('\n  "risa": {') + 1;
let depth = 0;
let end = start;
let inStr = false;
for (let i = text.indexOf("{", start); i < text.length; i++) {
  const ch = text[i] as string;
  if (inStr) {
    if (ch === "\\") i++;
    else if (ch === '"') inStr = false;
  } else if (ch === '"') inStr = true;
  else if (ch === "{") depth++;
  else if (ch === "}" && --depth === 0) {
    end = i + 1;
    break;
  }
}
const entry = { dict: JSON.parse(JSON.stringify(PRESETS["risa"])), json: paramsJsonText(PRESETS["risa"] as never) };
const body = JSON.stringify(entry, null, 1).split("\n").map((l, i) => (i === 0 ? l : "  " + l)).join("\n");
const updated = text.slice(0, start) + '  "risa": ' + body + text.slice(end);
writeFileSync(pPath, updated);
const was = JSON.parse(text);
const now = JSON.parse(updated);
console.log("presets.json: risa entry replaced; every other preset, and every other section, untouched:", Object.keys(was).every((k) => k === "presets" || JSON.stringify(was[k]) === JSON.stringify(now[k])) && Object.keys(was.presets).filter((k) => k !== "risa").every((k) => JSON.stringify(was.presets[k]) === JSON.stringify(now.presets[k])));

// ---- pages.json
const gPath = join(TS, "fixtures", "pages.json");
const pages = JSON.parse(readFileSync(gPath, "utf8"));
const work = mkdtempSync(join(tmpdir(), "pages-"));
let n = 0;
pages.cases.forEach((c: any, i: number) => {
  if (!c.args.some((a: string) => a.includes("risa"))) return;
  const base = join(work, `c${i}`);
  const script = join(TS, "bin", c.kind === "cover" ? "cover.ts" : "sheet.ts");
  const r = spawnSync(process.execPath, [script, ...c.args, "--out", base], { encoding: "utf8", env: { ...process.env, ACC_LOCAL_DIR: "/nonexistent" } });
  if (r.status !== 0) throw new Error(r.stderr);
  const svg = readFileSync(`${base}.svg`, "utf8");
  console.log(`pages.json case ${i} (${c.kind} ${c.args.join(" ")}): ${c.bytes} bytes -> ${Buffer.byteLength(svg)}`);
  c.bytes = Buffer.byteLength(svg);
  c.sha256 = createHash("sha256").update(svg, "utf8").digest("hex");
  n++;
});
writeFileSync(gPath, JSON.stringify(pages, null, 1));
console.log("pages.json:", n, "cases updated");
