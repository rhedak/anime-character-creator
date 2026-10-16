// The hair domain's parts, by the Python name `render_character` calls them with. See `src/parts.ts`.
// The functions are in `hair.ts`; `_hair_lines` is the wrapper `render_character` applies to a hair layer's text.

import {
  browsOverHair,
  hairClip,
  hairDefs,
  hairFront,
  hairKnot,
  hairLines,
  hairMass,
  hairTail,
  hairTie,
} from "./hair.ts";
import type { PartTable } from "./parts.ts";

export const PARTS: PartTable = {
  _hair_defs: hairDefs,
  _hair_mass: hairMass,
  _hair_lines: hairLines,
  _hair_front: hairFront,
  _hair_tail: hairTail,
  _hair_knot: hairKnot,
  _hair_tie: hairTie,
  _hair_clip: hairClip,
  _brows_over_hair: browsOverHair,
};
