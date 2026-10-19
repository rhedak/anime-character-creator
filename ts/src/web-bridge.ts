// The web tool's bridge to the drawing: the four functions `web/app.js` calls, which used to be Python run in the visitor's
// browser by Pyodide. They do nothing `renderCharacter`, `urlstate` and the presets do not already do; they exist so the page
// never serialises a character by hand or reimplements the link encoding.
//
// A state travels as JSON text. The page builds it with `JSON.stringify`, which writes the float `1.0` as `1`; reading it back
// with `loadsText` (Python's `json.loads`) keeps that `1` an int, exactly as the Python bridge did, so a link made from a
// dragged slider carries what it always carried.

import { renderCharacter } from "./render.ts";
import { loadsText } from "./pyjsonload.ts";
import { NEUTRAL_BASES, PRESETS } from "./presets.ts";
import { PyError } from "./pynum.ts";
import { decodeParams, encodeParams, paramsFromDict, paramsJsonText } from "./urlstate.ts";

function stateFrom(stateJson: string): ReturnType<typeof paramsFromDict> {
  const loaded = loadsText(stateJson);
  if (!(loaded instanceof Map)) throw new PyError("ValueError", "a character state is a JSON object");
  return paramsFromDict(loaded as Map<string, unknown>);
}

/** The state of a starting point (a preset or a neutral base) as JSON text. */
export function stateForStart(startId: string): string {
  const p = PRESETS[startId] ?? NEUTRAL_BASES[startId];
  if (p === undefined) throw new PyError("ValueError", `no such starting point: ${startId}`);
  return paramsJsonText(p);
}

/** The SVG of the character in `stateJson`, on `background` (any SVG paint, or `null` for none), with the metadata block if asked. */
export function render(stateJson: string, background: string | null, metadata: boolean): string {
  return renderCharacter(stateFrom(stateJson), null, background, Boolean(metadata));
}

/** The shareable link value (the `c` query parameter) for the character in `stateJson`. */
export function encode(stateJson: string): string {
  return encodeParams(stateFrom(stateJson));
}

/** The state, as JSON text, of the character a link value stands for. */
export function decode(encoded: string): string {
  return paramsJsonText(decodeParams(encoded));
}
