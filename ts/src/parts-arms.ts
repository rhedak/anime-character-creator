// The arms domain's parts, by the Python name `render_character` calls them with. See `src/parts.ts`.

import { arms, handsAfterCoat } from "./core-limbs-arms.ts";
import type { PartTable } from "./parts.ts";

export const PARTS: PartTable = { _arms: arms, _hands_after_coat: handsAfterCoat };
