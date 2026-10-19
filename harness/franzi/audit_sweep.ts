import { readFileSync, writeFileSync } from "node:fs";
// Every control of ref-out/catalogue.json applied to Franzi (in the dirndl, and in her underwear alone) and rendered, with a check of each result for an exception, malformed XML,
// NaN or undefined in the text, a duplicated id, a dangling reference, and whether the picture changed (docs/adult-body-audit.md). Writes rows.json, labels.json and an SVG for each variant that
// changes her into $TMPDIR/audit/ (the folder must exist). Run: mkdir -p $TMPDIR/audit && node harness/franzi/audit_sweep.ts
const R = new URL("../../ts", import.meta.url).pathname;
const { PRESETS } = await import(`${R}/src/presets.ts`);
const { characterParams, faceStyle, outfit } = await import(`${R}/src/model.ts`);
const { OUTFIT_FIELDS, FACESTYLE_FIELDS } = await import(`${R}/src/params.ts`);
const { renderCharacter } = await import(`${R}/src/render.ts`);
const { fromstring } = await import(`${R}/test/svg-scan.ts`);
const cat = JSON.parse(readFileSync(`${R}/../ref-out/catalogue.json`, "utf8"));
const outfitF = new Set(OUTFIT_FIELDS.map((f: any) => f.name));
const faceF = new Set(FACESTYLE_FIELDS.map((f: any) => f.name));
const BASES: Record<string, any> = {
  dirndl: PRESETS.franzi,
  bare: characterParams({ ...PRESETS.franzi, outfit: outfit({ ...PRESETS.franzi.outfit, tunic_color: null, bodice_color: null, skirt_color: null, apron_color: null }) }),
};
const apply = (base: any, field: string, v: any) => {
  if (outfitF.has(field)) return characterParams({ ...base, outfit: outfit({ ...base.outfit, [field]: v }) });
  if (faceF.has(field)) return characterParams({ ...base, face: faceStyle({ ...base.face, [field]: v }) });
  return characterParams({ ...base, outfit: base.outfit, face: base.face, [field]: v });
};
type Row = { base: string; group: string; control: string; value: string; status: string; note: string; bytes: number; same: boolean };
const rows: Row[] = [];
const labels: Record<number, string> = {};
const sig = (s: string) => s;
function check(baseName: string, group: string, control: string, value: any, p: any, baseSvg: string, extra?: any) {
  let status = "ok", note = "", svg = "";
  try {
    svg = renderCharacter(p, null, "white", false);
    try { fromstring(svg); } catch (e) { status = "BAD XML"; note = String(e).slice(0, 100); }
    if (/NaN|undefined|Infinity/.test(svg)) { status = status === "ok" ? "BAD NUMBER" : status; note += " NaN/undefined in output"; }
    const ids = [...svg.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]);
    const dup = ids.filter((v, i) => ids.indexOf(v) !== i);
    if (dup.length) { status = status === "ok" ? "DUP IDS" : status; note += ` dup ${[...new Set(dup)].slice(0, 3)}`; }
    const refs = [...svg.matchAll(/url\(#([^)]+)\)/g)].map((m) => m[1]);
    const miss = refs.filter((r) => !ids.includes(r));
    if (miss.length) { status = status === "ok" ? "MISSING REF" : status; note += ` missing ${[...new Set(miss)].slice(0, 3)}`; }
  } catch (e: any) { status = "THROWS"; note = String(e.message ?? e).slice(0, 120); }
  if (svg && svg !== baseSvg && !(baseName === "dirndl" && group.startsWith("garment")) && !(baseName === "bare" && !group.startsWith("garment"))) { const n = rows.length; writeFileSync(`${process.env.TMPDIR}/audit/v${n}.svg`, svg); labels[n] = `${group}: ${control}=${value}`; }
  rows.push({ base: baseName, group, control, value: String(value), status, note: note.trim(), bytes: svg.length, same: svg === baseSvg });
}
for (const [bn, base] of Object.entries(BASES)) {
  const baseSvg = renderCharacter(base, null, "white", false);
  const t = (group: string, field: string, vals: any[]) => { for (const v of vals) check(bn, group, field, v, apply(base, field, v), baseSvg); };
  t("body", "body", cat.bodies.map((b: any) => b.id));
  t("hair", "hairstyle", cat.hairstyles.map((b: any) => b.id));
  t("hands", "hand_style", cat.hand_styles.map((b: any) => b.id));
  t("hands", "grip_style", cat.grip_styles.map((b: any) => b.id));
  t("finish", "finish", cat.finishes.map((b: any) => b.id));
  for (const k of ["highlight_strength", "hair_length", "hair_tail", "waist_shift", "bust", "chest", "height", "face_age"]) {
    const r = cat[k] ?? cat[k === "height" ? "height" : k] ; if (!r) continue;
    t("range", r.field, [r.min, (r.min + r.max) / 2, r.max]);
  }
  t("hair", "hair_knot", [true, false]);
  for (const sw of cat.skin_swatches) check(bn, "skin", "skin_tone", sw.label, apply(base, "skin_tone", sw.value), baseSvg);
  for (const c of cat.colors) t("colour", c.field, ["#3a6ea5", "#e8d44d"]);
  for (const g of cat.garments) {
    const f = g.color.field;
    // a garment worn alone, and its options
    const worn = apply(apply(base, f, "#3a6ea5"), f, "#3a6ea5");
    check(bn, `garment ${g.id}`, f, "#3a6ea5", worn, baseSvg);
    if (g.requires) {
      const rf = cat.garments.find((x: any) => x.id === g.requires).color.field;
      check(bn, `garment ${g.id}`, `${f} with ${g.requires}`, "#3a6ea5", apply(apply(base, rf, "#8c5a2b"), f, "#3a6ea5"), baseSvg);
    }
    const wornBase = apply(base, f, "#3a6ea5");
    const wbSvg = renderCharacter(wornBase, null, "white", false);
    for (const r of g.ranges ?? []) for (const v of [r.min, r.max]) check(bn, `garment ${g.id}`, r.field, v, apply(wornBase, r.field, v), wbSvg);
    for (const b of g.bools ?? []) for (const v of [true, false]) check(bn, `garment ${g.id}`, b.field, v, apply(wornBase, b.field, v), wbSvg);
    for (const s of g.selects ?? []) for (const o of s.options) check(bn, `garment ${g.id}`, s.field, o.value, apply(wornBase, s.field, o.value), wbSvg);
  }
  for (const r of cat.face.ranges) for (const v of [r.min, r.max]) check(bn, "face", r.field, v, apply(base, r.field, v), baseSvg);
  for (const b of cat.face.bools) for (const v of [true, false]) check(bn, "face", b.field, v, apply(base, b.field, v), baseSvg);
  for (const s of cat.face.selects) for (const o of s.options) check(bn, "face", s.field, o.value, apply(base, s.field, o.value), baseSvg);
}
writeFileSync(process.env.TMPDIR + "/audit/rows.json", JSON.stringify(rows));
writeFileSync(process.env.TMPDIR + "/audit/labels.json", JSON.stringify(labels));
const bad = rows.filter((r) => r.status !== "ok");
console.log("variants:", rows.length, " problems:", bad.length);
for (const r of bad) console.log(r.base, "|", r.group, "|", r.control, "=", r.value, "|", r.status, r.note);
