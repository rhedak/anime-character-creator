// Which controls of the catalogue change nothing in a body's drawing, found by drawing: used by the test that pins `BODY_IGNORES` (catalogue-tables.ts) to what is drawn, and printable
// with `node harness/franzi/ignored_fields.ts`. A field is ignored when, in every context that could make it matter, none of its values changes what is seen.

import { buildCatalogue } from "../src/catalogue.ts";
import { FACESTYLE_FIELDS, OUTFIT_FIELDS } from "../src/params.ts";
import { characterParams, faceStyle, outfit } from "../src/model.ts";
import type { CharacterParams } from "../src/params.ts";
import { FRANZI } from "../src/presets.ts";
import { renderCharacter } from "../src/render.ts";

/**
 * What a picture shows: the document without the definitions nothing refers to. A cut the body does not use still writes its clip paths, which changes the text and no pixel, so
 * a definition (a clip path, a gradient, a mask) whose id is never used is left out, and a `<defs>` left empty with it.
 */
export function visible(svg: string): string {
  let out = svg;
  for (let again = true; again; ) {
    again = false;
    const used = new Set([...out.matchAll(/url\(#([^)]+)\)/g), ...out.matchAll(/href="#([^"]+)"/g)].map((m) => m[1] as string));
    out = out.replace(/<(clipPath|linearGradient|radialGradient|mask)\b[^>]*\bid="([^"]+)"[^>]*>[\s\S]*?<\/\1>/g, (m, _tag, id) => {
      if (used.has(id as string)) return m;
      again = true;
      return "";
    });
  }
  return out.replace(/<defs>\s*<\/defs>\s*/g, "");
}

type Json = Record<string, any>;
const outfitF = new Set(OUTFIT_FIELDS.map((f) => f.name));
const faceF = new Set(FACESTYLE_FIELDS.map((f) => f.name));
const COLOUR_A = "#3a6ea5";
const COLOUR_B = "#8c5a2b";

const put = (p: CharacterParams, field: string, v: unknown): CharacterParams => {
  if (outfitF.has(field)) return characterParams({ ...p, outfit: outfit({ ...p.outfit, [field]: v }) });
  if (faceF.has(field)) return characterParams({ ...p, face: faceStyle({ ...p.face, [field]: v }) });
  return characterParams({ ...p, outfit: p.outfit, face: p.face, [field]: v });
};

/** Every field the page offers a control for, with the values to try and the settings that must be on for it to matter. */
export function controls(): { field: string; values: unknown[]; needs: [string, unknown][] }[] {
  const cat = buildCatalogue() as unknown as Json;
  const out: { field: string; values: unknown[]; needs: [string, unknown][] }[] = [];
  const ids = (xs: Json[]): unknown[] => xs.map((x) => x.id);
  const range = (r: Json): unknown[] => [r.min, (r.min + r.max) / 2, r.max];
  out.push({ field: "body", values: ids(cat.bodies), needs: [] });
  out.push({ field: "hand_style", values: ids(cat.hand_styles), needs: [] });
  out.push({ field: "grip_style", values: ids(cat.grip_styles), needs: [] });
  out.push({ field: "hairstyle", values: ids(cat.hairstyles), needs: [] });
  out.push({ field: "finish", values: ids(cat.finishes), needs: [] });
  for (const k of ["height", "face_age", "highlight_strength", "hair_length", "hair_tail", "waist_shift", "bust", "chest"]) out.push({ field: k, values: range(cat[k]), needs: k === "highlight_strength" ? [["finish", "soft"]] : [] });
  out.push({ field: "hair_knot", values: [true, false], needs: [] });
  for (const c of cat.colors as Json[]) {
    const needs: [string, unknown][] = c.field === "familiar_eye_color" ? [["familiar_color", COLOUR_B]] : c.field === "hair_tip_color" ? [] : [];
    out.push({ field: c.field, values: c.field === "hair_tip_color" ? [null, COLOUR_A] : [COLOUR_A, "#e8d44d"], needs });
  }
  for (const g of cat.garments as Json[]) {
    const parents: [string, unknown][] = [];
    for (let x: Json | undefined = g; x?.requires; ) {
      x = (cat.garments as Json[]).find((y) => y.id === x!.requires);
      parents.push([x!.color.field, COLOUR_B]);
    }
    out.push({ field: g.color.field, values: [null, COLOUR_A], needs: parents });
    const own: [string, unknown][] = [...parents, [g.color.field, COLOUR_A]];
    for (const r of g.ranges ?? []) out.push({ field: r.field, values: range(r), needs: own });
    for (const b of g.bools ?? []) out.push({ field: b.field, values: [true, false], needs: own });
    for (const s of g.selects ?? []) out.push({ field: s.field, values: (s.options as Json[]).map((o) => o.value), needs: own });
  }
  for (const r of cat.face.ranges as Json[]) out.push({ field: r.field, values: range(r), needs: [] });
  for (const b of cat.face.bools as Json[]) out.push({ field: b.field, values: [true, false], needs: [] });
  for (const s of cat.face.selects as Json[]) out.push({ field: s.field, values: (s.options as Json[]).map((o) => o.value), needs: [] });
  return out;
}

/** The fields with no visible effect on `body`, drawn as Franzi, in her dirndl and in her underwear alone. Sorted. */
export function ignoredFields(body: string): string[] {
  const dirndl = characterParams({ ...FRANZI, body });
  const bare = characterParams({ ...FRANZI, body, outfit: outfit({ ...FRANZI.outfit, tunic_color: null, bodice_color: null, skirt_color: null, apron_color: null }) });
  const ignored: string[] = [];
  for (const { field, values, needs } of controls()) {
    if (field === "body") continue;
    let effect = false;
    for (const base of [dirndl, bare]) {
      let ctx = base;
      for (const [f, v] of needs) ctx = put(ctx, f, v);
      const seen = new Set<string>();
      for (const v of values) {
        let svg: string;
        try {
          svg = renderCharacter(put(ctx, field, v), null, "white", false);
        } catch {
          svg = `throws ${String(v)}`;
        }
        seen.add(visible(svg));
      }
      if (seen.size > 1) effect = true;
    }
    if (!effect) ignored.push(field);
  }
  return ignored.sort();
}
