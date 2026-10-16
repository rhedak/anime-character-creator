# Error-text differences found in the hair domain (`ts/src/hair.ts`)

Rows to append to `docs/ts-port-errors.md`. The class names are CPython's in every row; only the text can differ.

| Raised by | Python (3.12 / 3.13) | TypeScript port | Why it differs |
| --- | --- | --- | --- |
| `_lock_shape` on a one-point clump line (`i / (n - 1)` with `n == 1`, int over int) | `ZeroDivisionError: division by zero` | `ZeroDivisionError: float division by zero` (`pyDiv`) | the kernel's `pyDiv` spells the float text; no cut has a one-point lock, so nothing reaches it |
| `_clip_crescent` with a zero head radius (`/ (2 * off)`, float over float) | `ZeroDivisionError: float division by zero` | the same text | reproduced (listed for completeness) |
| `HAIR_CLIPS[p.outfit.hair_clip]` with a name that is not a clip | `KeyError: 'name'` | `KeyError` with `pyValueRepr(name)` (`'name'`) | reproduced; an unhashable value (a list or dict from a link) raises `TypeError: unhashable type: 'list'` as Python does |
| `_soft_locks` with a lock role that is not `shadow` or `lit` | `ValueError: a lock's role is shadow or lit, not 'x'` | the same text | reproduced; no cut carries another role, so nothing reaches it |
| `_soft_lock_layers` with a cut that has no `locks` | `AssertionError` (no message) | `AssertionError` (empty message) | reproduced; only a direct call reaches it |
| `_lock_line` of an empty `points` | `IndexError: tuple index out of range` | the same text | reproduced; only a direct call reaches it |
