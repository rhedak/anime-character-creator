// usage: node posefig.ts OUTDIR '{"name":{overrides}}' [viewBox]
// Renders Franzi once per named override set into OUTDIR/name.svg, cropped to the viewBox (default: the whole figure with room above the canvas).
// An override set is a CharacterParams patch, plus `outfit` and `face` patches merged into hers. She is in her underwear alone unless DRESS=1 (her dirndl).
import { writeFileSync, mkdirSync } from "node:fs";
import { characterParams, faceStyle, outfit } from "../../../ts/src/model.ts";
import { FRANZI } from "../../../ts/src/presets.ts";
import { renderCharacter } from "../../../ts/src/render.ts";

const [out, json, vb = "0 -90 400 590"] = process.argv.slice(2);
if (!out || !json) throw new Error("usage: node posefig.ts OUTDIR '{\"name\":{...}}' [viewBox]");
mkdirSync(out, { recursive: true });
const dress = process.env.DRESS === "1";
for (const [name, o] of Object.entries(JSON.parse(json) as Record<string, any>)) {
  const base = dress ? FRANZI.outfit : outfit({ ...FRANZI.outfit, tunic_color: null, bodice_color: null, skirt_color: null, apron_color: null });
  const p = characterParams({ ...FRANZI, ...o, outfit: outfit({ ...base, ...(o.outfit ?? {}) }), face: faceStyle({ ...FRANZI.face, ...(o.face ?? {}) }) });
  const [, , w = "400", h = "500"] = vb.split(" ");
  const svg = renderCharacter(p, null, "#f0f0f0", false).replace('width="400" height="500" viewBox="0 0 400 500"', `width="${Number(w) * 2}" height="${Number(h) * 2}" viewBox="${vb}"`);
  writeFileSync(`${out}/${name}.svg`, svg);
}
