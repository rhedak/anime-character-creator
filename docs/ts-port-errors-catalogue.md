# Where `catalogue.ts` differs from `catalogue.py` in error text

Rows for `docs/ts-port-errors.md` (decision D12: the class names are Python's, the text is the port's where it
cannot match). The module raises only at import time (its asserts tie the label tables to the tables of
`character.py` and to the field registry) and in `lookup`, which stands for `table[key]` on a dict.

| Raised by | Python | TypeScript port | Why it differs |
| --- | --- | --- | --- |
| `assert _outfit_fields_named() == _OUTFIT_FIELDS, f"... missing {set}, extra {set}"` (`catalogue.py:501`) | `AssertionError: GARMENTS and Outfit have drifted apart: missing frozenset({'x'}), extra frozenset()` (the repr of two frozensets) | `AssertionError: GARMENTS and Outfit have drifted apart: missing ["x"], extra []` (a JSON list, in registry order) | a frozenset's repr has no stable order and no TypeScript twin; the message is a diagnostic only. Not reachable while the generated tables and the registry agree (a test pins that) |
| `_color`, `_range`, `_bool`, `_face_*` with an unknown field (`catalogue.py:123-148`) | `AssertionError: Outfit has no field 'x'` | the same text, class `AssertionError`, the key repr from `pyStrRepr` | reproduced (tested) |
| `set(LABELS) == set(TABLE)` asserts (`catalogue.py:156-634`) | `AssertionError` with no text, or the "have drifted apart" text for the hairstyles and the bodies | the same (empty text, or the same sentence) | reproduced |
| `LABELS[name]` for a name the table lacks | `KeyError: 'name'` | `KeyError: 'name'` (`lookup`, which also refuses inherited names such as `toString`) | reproduced; unreachable while the asserts hold |
| `python -O` strips the asserts | the module loads without checking | not applicable: the checks always run | the port has no optimised mode |

Not an error difference but a limit worth stating: `HAND_STYLES` and `GRIP_STYLES` (`character.py:10507-10509`) are not exported
by any `ts/src` module, so `catalogue-tables.ts` carries generated copies. `assertKeysEqual(HAND_LABELS, HAND_STYLES)` then
checks the labels against the copy, not against the module that draws the hands; the expected fixture
(`ts/fixtures/catalogue-expected.json`) and the fresh-Python test check the copies against Python's own tuples.
