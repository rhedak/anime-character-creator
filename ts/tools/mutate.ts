// The mutation gate (docs/ts-port-plan.md, section 5.1). Small random edits to the drawing code, one at a time, in a PRIVATE COPY
// of `ts/` (the real tree is never touched): a constant nudged by 7 percent, an integer moved by one, an operator flipped. The
// corpus must notice each. A survivor is either dead or equivalent code, or a hole in the oracle: each is listed.
//
//   node tools/mutate.ts COUNT [seed] [K]      mutations, seed (default 1), detector stride K (default 7)
//
// Output: `out/mutation.json` and a summary on stdout. Run from `ts/`.
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, symlinkSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { join } from "node:path";
import { tmpdir } from "node:os";

const count = Number(process.argv[2] ?? 50);
const seed0 = Number(process.argv[3] ?? 1);
const stride = process.argv[4] ?? "7";
const TS = process.cwd();
const REPO = join(TS, "..");

// The drawing code: every module except the kernel (tested on its own against CPython) and the generated tables.
const EXCLUDE = /^(pynum|pyjson|pyjsonload|pycodecs|pyre|pyvalue|sha1|plain|model|urlstate|attribution|supporting|presets|params|tables)\.ts$|-tables\.ts$|^parts(-[a-z]+)?\.ts$|^render\.ts$|^body\.ts$/;
const files = readdirSync(join(TS, "src")).filter((f) => f.endsWith(".ts") && !EXCLUDE.test(f));

function rng(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

type Site = { file: string; line: number; col: number; len: number; text: string; kind: string; repl: string };

function sitesOf(file: string, src: string): Site[] {
  const out: Site[] = [];
  const lines = src.split("\n");
  let inBlock = false;
  lines.forEach((ln, i) => {
    const t = ln.trim();
    if (inBlock) {
      if (t.includes("*/")) inBlock = false;
      return;
    }
    if (t.startsWith("/*")) {
      if (!t.includes("*/")) inBlock = true;
      return;
    }
    if (t.startsWith("//") || t.startsWith("*") || t.startsWith("import ") || t.startsWith("export type") || t.startsWith("export interface")) return;
    const code = ln.replace(/\/\/.*$/, (m, off) => " ".repeat(m.length));
    for (const m of code.matchAll(/(?<![\w.$])(\d+\.\d+)(?![\w.])/g)) {
      const v = Number(m[1]);
      if (v === 0) continue;
      const decimals = (m[1]!.split(".")[1] ?? "").length;
      let r = (v * 1.07).toFixed(decimals);
      if (r === m[1]) r = (v + Math.pow(10, -decimals)).toFixed(decimals);
      out.push({ file, line: i, col: m.index!, len: m[1]!.length, text: m[1]!, kind: "float", repl: r });
    }
    for (const m of code.matchAll(/ (\+|-|\*|<|>) /g)) {
      const flip: Record<string, string> = { "+": "-", "-": "+", "*": "/", "<": "<=", ">": ">=" };
      out.push({ file, line: i, col: m.index! + 1, len: m[1]!.length, text: m[1]!, kind: "op", repl: flip[m[1]!]! });
    }
    for (const m of code.matchAll(/(?<![\w.$"'#-])(\d+)(?![\w.]|px)/g)) {
      const v = Number(m[1]);
      if (v > 1000) continue;
      out.push({ file, line: i, col: m.index!, len: m[1]!.length, text: m[1]!, kind: "int", repl: String(v + 1) });
    }
  });
  return out;
}

// A private copy: ts/ without node_modules and out/, the harness data by symlink.
const root = join(tmpdir(), `mutroot-${process.pid}`);
const copyTs = join(root, "ts");
mkdirSync(root, { recursive: true });
cpSync(TS, copyTs, { recursive: true, filter: (p) => !/\/(node_modules|out)(\/|$)/.test(p) });
symlinkSync(join(REPO, "harness"), join(root, "harness"));
symlinkSync(join(REPO, "ref-out"), join(root, "ref-out"));
if (existsSync(join(TS, "node_modules"))) symlinkSync(join(TS, "node_modules"), join(copyTs, "node_modules"));

const all: Site[] = [];
const originals = new Map<string, string>();
for (const f of files) {
  const text = readFileSync(join(TS, "src", f), "utf8");
  originals.set(f, text);
  all.push(...sitesOf(f, text));
}
console.log(`${files.length} files, ${all.length} mutation sites; copy at ${root}`);

if (process.env.ONLY) {
  // Re-test the survivors of an earlier run, with whatever detector is now selected.
  const prev = JSON.parse(readFileSync(process.env.ONLY, "utf8")) as (Site & { result: string })[];
  all.length = 0;
  all.push(...prev.filter((r) => r.result === "survived"));
}
const detector = process.env.DETECTOR === "full" ? ["--max-old-space-size=8192", "--test", "test/*.test.ts"] : ["--max-old-space-size=4096", "tools/quick.ts", stride];
const rand = rng(seed0);
const results: (Site & { result: string; detail: string })[] = [];
const tried = new Set<number>();
const limit = process.env.ONLY ? all.length : count;
while (results.length < limit && tried.size < all.length) {
  const idx = Math.floor(rand() * all.length);
  if (tried.has(idx)) continue;
  tried.add(idx);
  const s = all[idx]!;
  const orig = originals.get(s.file)!;
  const lines = orig.split("\n");
  const ln = lines[s.line]!;
  lines[s.line] = ln.slice(0, s.col) + s.repl + ln.slice(s.col + s.len);
  const path = join(copyTs, "src", s.file);
  writeFileSync(path, lines.join("\n"));
  const r = spawnSync("node", detector, { cwd: copyTs, encoding: "utf8", timeout: 900000, maxBuffer: 1 << 28 });
  writeFileSync(path, orig);
  const out = `${r.stdout ?? ""}${r.stderr ?? ""}`;
  let result: string;
  if (process.env.DETECTOR === "full") {
    result = r.status === 0 ? "survived" : "detected";
    if (/SyntaxError|ERR_MODULE_NOT_FOUND|does not provide an export/.test(out) && !/# fail [1-9]|not ok/.test(out)) result = "invalid";
  } else if (/SyntaxError|ERR_MODULE_NOT_FOUND|does not provide an export/.test(out) && !/DETECTED|SURVIVED/.test(out)) result = "invalid";
  else if (/DETECTED/.test(out)) result = "detected";
  else if (/SURVIVED/.test(out)) result = "survived";
  else result = "crashed";
  if (result === "invalid") continue;
  const detail = (out.match(/(DETECTED|SURVIVED)[^\n]*/)?.[0] ?? (out.match(/^not ok[^\n]*/m)?.[0] ?? out.slice(0, 120))).slice(0, 140);
  results.push({ ...s, result, detail });
  console.log(`${String(results.length).padStart(3)} ${result.padEnd(9)} ${s.file}:${s.line + 1} ${s.text} -> ${s.repl}  ${detail}`);
}
mkdirSync(join(TS, "out"), { recursive: true });
writeFileSync(join(TS, "out", process.env.ONLY ? "mutation-survivors.json" : "mutation.json"), JSON.stringify(results, null, 1));
const tally = (k: string): number => results.filter((r) => r.result === k).length;
console.log(`\n${results.length} mutations: ${tally("detected")} detected, ${tally("survived")} survived, ${tally("crashed")} crashed`);
