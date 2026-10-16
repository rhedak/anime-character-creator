# Error-text differences from the parts-body port (rows for `docs/ts-port-errors.md`)

None found. The places where the body parts raise, and what they raise, are:

| Raised by | Python | TypeScript port | Why it differs |
| --- | --- | --- | --- |
| `SKIRT_CUTS[name]`, `BOOT_CUTS[name]` (`_skirt`, `_skirt_bottom_y`, `_boot`) with a name that is not a cut | `KeyError: 'nope'` | the same class and text (`body-parts-legs.ts` `cutNamed`) | reproduced; a list as the name is `TypeError: unhashable type: 'list'`, as in Python |
| `_bust_shape(...).peak` in `_underwear_top` when the shape is `None` | `AttributeError: 'NoneType' object has no attribute 'peak'` | the same | reproduced (not reached by the corpus: a figure with a bare-breast spine always has a bust shape) |
| `max(ys)`, `min(ys)` of an empty cut | `ValueError: max() iterable argument is empty` | the same (via `maxOf`, `minOf`) | reproduced (a cut always has a fill) |
| a number field holding a string or list (`sleeve_drop`, `boot_shaft`, `chest`) | `TypeError` at the first arithmetic or comparison | `TypeError` from `BadValue` (class equal, text is the kernel's) | the text of the kernel's `BadValue` differs from CPython's operand message |
