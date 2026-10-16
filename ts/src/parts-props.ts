// The props and headgear domain's parts, by the Python name `render_character` calls them with. See `src/parts.ts`.

import { hatUnderside } from "./character.ts";
import type { PartTable } from "./parts.ts";
import { familiar, hat, headscarf, katana, staff } from "./props.ts";

export const PARTS: PartTable = {
  _hat_underside: hatUnderside,
  _hat: hat,
  _headscarf: headscarf,
  _staff: staff,
  _katana: katana,
  _familiar: familiar,
};
