// The body domain's parts, by the Python name `render_character` calls them with. See `src/parts.ts`.

import { bustLines, bustOverArms, chestLines, hangingSleeves, navel, torso, underwearTop, withoutRaisedSleeves } from "./body-parts.ts";
import { hakama, legsAndBoots, skirt, underskirt } from "./body-parts-legs.ts";
import type { PartTable } from "./parts.ts";

export const PARTS: PartTable = {
  _torso: torso,
  _without_raised_sleeves: withoutRaisedSleeves,
  _legs_and_boots: legsAndBoots,
  _underskirt: underskirt,
  _skirt: skirt,
  _hakama: hakama,
  _hanging_sleeves: hangingSleeves,
  _navel: navel,
  _underwear_top: underwearTop,
  _chest_lines: chestLines,
  _bust_lines: bustLines,
  _bust_over_arms: bustOverArms,
};
