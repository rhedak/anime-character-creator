// The face domain's parts, by the Python name `render_character` calls them with. See `src/parts.ts`.

import { mask, neck } from "./character.ts";
import { ears, face, head } from "./face.ts";
import { beard, blindfold, glasses, goggles, gogglesStrap } from "./face-wear.ts";
import type { PartTable } from "./parts.ts";

export const PARTS: PartTable = {
  _neck: neck,
  _mask: mask,
  _ears: ears,
  _head: head,
  _beard: beard,
  _face: face,
  _glasses: glasses,
  _goggles_strap: gogglesStrap,
  _goggles: goggles,
  _blindfold: blindfold,
};
