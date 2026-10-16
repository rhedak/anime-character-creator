// The garments domain's parts, by the Python name `render_character` calls them with. See `src/parts.ts`.

import {
  apron,
  belt,
  chestPockets,
  coat,
  collar,
  crystalHarness,
  placket,
  pouches,
  ribbon,
  robeFront,
  shoulderBars,
  strap,
  tracedCoatAndBelt,
  tunic,
} from "./garments.ts";
import type { PartTable } from "./parts.ts";

export const PARTS: PartTable = {
  _tunic: tunic,
  _robe_front: robeFront,
  _placket: placket,
  _chest_pockets: chestPockets,
  _strap: strap,
  _apron: apron,
  _coat: coat,
  _pouches: pouches,
  _crystal_harness: crystalHarness,
  _traced_coat_and_belt: tracedCoatAndBelt,
  _belt: belt,
  _collar: collar,
  _shoulder_bars: shoulderBars,
  _ribbon: ribbon,
};
