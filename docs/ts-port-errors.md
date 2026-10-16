# Where the TypeScript port's errors differ from Python's

Decision D12 (2026-10-16): the port keeps Python's exception **class names** and defines its own stable
**messages**. The class names are the ones CPython 3.12 uses, since that is what the shipped Pyodide runs (3.12.1) and
what the companion's tests were written against. Every place the text differs from CPython is listed here as the port
grows, so a test or a consumer that asserts text can be found and changed on purpose.

| Raised by | Python (3.12 / 3.13) | TypeScript port | Why it differs |
| --- | --- | --- | --- |
| `re` template errors in `pySub` (a bad `id_prefix`) | `re.error: bad escape \q at position 7` (named `PatternError` in 3.13) | class `error`, message without the position | the position is the template parser's byte offset; not worth reproducing |
| `math` domain errors (`sqrt` of a negative, `acos` out of range) | `ValueError: math domain error` | the same text | reproduced exactly: the companion shows it to the model |
| validation errors from `validate_finish` | `ValueError` with the text in `character.py` | to be ported with the same text | text is part of the documented API |
| `x ** y` | `OverflowError: (34, 'Numerical result out of range')`, `ZeroDivisionError: 0.0 cannot be raised to a negative power` | the same text | reproduced |
| `x ** y`, negative base with a fractional exponent | returns a `complex` | `ValueError: complex result` | the port has no complex numbers; loud on purpose, nothing reaches it |
| division by a zero divisor (`pyDiv`) | `ZeroDivisionError: float division by zero` | the same text | reproduced, only where a site uses `pyDiv` |
| `int(s, 16)` on a malformed colour | `ValueError: invalid literal for int() with base 16: 'xy'` | the same text | reproduced; more than 13 significant digits raise `OverflowError` here |
| `float(s)` | accepts `1_0`, `inf`, `nan`, other scripts' digits | refuses them | stricter; its only caller feeds `[0-9.]+` |
| index or slice with a non-integer | `TypeError` with Python's text | `TypeError` with the same text | reproduced |
| unknown body or preset name | `KeyError: 'name'` | the same | reproduced |
| `sha1` of text with a lone surrogate | `UnicodeEncodeError` | `UnicodeEncodeError`, different text | |
| `round(x, n)` with negative `n` | works | `NotImplementedError` | not used |
| `validate_finish` (`model.ts`, phase 3) | `ValueError: finish must be one of flat, soft, not 'x'`, `ValueError: highlight_strength must be between 0 and 2, not 2.5` | the same text, class `ValueError` | reproduced on 76 finish and strength spellings. A caller who types a plain `number` for the strength means a float, so `3` reads `3.0` in the message where Python's int `3` reads `3`; a value decoded from a link keeps its int-ness (`PyInt`) and reads as Python's |
| `decode_params` wrapper (`urlstate.ts`) | `ValueError: not a valid character link: <inner text>` with the inner text of `JSONDecodeError`, `UnicodeDecodeError`, `binascii.Error`, `UnicodeEncodeError`, `RecursionError`, and the int digit limit `ValueError` | the same text | reproduced: 2,892 seeded JSON inputs (valid, mutated, random bytes, UTF-8, UTF-16, UTF-32), 3,300 base64 inputs and 248 whole links, zero differences. The inner class names are PyError names (`JSONDecodeError`, `Error` for `binascii.Error`) with no subclass relation, so a direct caller of `loadsBytes` that tests for `ValueError` does not catch `JSONDecodeError`; through `decodeParams` they are all `ValueError` as in Python |
| `params_from_dict` | `ValueError: not a valid character: <TypeError text>` for an unknown key, a non-mapping `outfit`, a non-string key; raw `TypeError` or `ValueError` from `dict(face)` and from `face_age < 0.9` | the same classes and text, including `CharacterParams.__init__() got an unexpected keyword argument 'x'` and `anime_character_creator.character.Outfit() argument after ** must be a mapping, not str` | reproduced on the malformed corpus; the first unknown key in insertion order is the one named |
| `json.loads` recursion limit | `RecursionError: maximum recursion depth exceeded while decoding a JSON array from a unicode string` at 9,999 nested containers on CPython 3.13.11 | the same text at the same depth (an explicit stack, not the JS stack) | measured here; another CPython build may use another limit |
| `encode_params` of a field holding a list or dict nested more than about 1,000 levels (only reachable through a hand-made link, since the registry has no such field) | encodes (Python's writer handles 9,000 levels) | `RangeError: Maximum call stack size exceeded` from `pyjson.dumps` and `urlstate.jsonValue` | not reproduced: the kernel's writer recurses. Nothing but a hostile link reaches it |
| assignment to a frozen dataclass | `dataclasses.FrozenInstanceError` (an `AttributeError`) | `TypeError: Cannot assign to read only property` (the constructors `Object.freeze`) | JS's own message; nothing in the port assigns |
| `dataclasses.replace(obj, x=None)` and a TS `undefined` | `None` sets the field | `null` sets the field; a key whose value is `undefined` is treated as not given | TS optional properties |
| `repr` of a str in the `finish` message | CPython 3.13's printable table (Unicode 15.1) | the `\p{C*}\p{Z*}` classes of the running V8 | identical on ASCII and the tested range; a character assigned after Unicode 15.1 could differ |
| an int field given a whole float by a link (`"scar_side": 1.0`), or a float field given an int (`"height": 2`) | kept as given and written back as given | kept (`PyFloat`, `PyInt` markers) and written back as given | reproduced; the renderer must read such values through `plainNumber` (`pyvalue.ts`), which Phase 4 has to do where it draws |
| `COAT_CUTS[name]` of an unknown cut (`core-limbs.ts`) | `KeyError: 'name'` (the repr of the key) | `KeyError` with the repr of a string key, `None` for a key that is not a string | the one case where a non-string reaches it is a `coat_cut` of the wrong type from a link |
| `len(text)` of a non-string `wristband_text` (`core-limbs-arms.ts`) | `TypeError: object of type 'int' has no len()`; a list or dict has a length and `escape` then raises `AttributeError: 'list' object has no attribute 'replace'` | the same classes and text (`pyTypeName` names the type) | reproduced; an empty list or dict is falsy and draws the band without text |
| `SLEEVE_CUTS.get(sleeve_cut or "")` with a list (`wornSleeve`) | `TypeError: unhashable type: 'list'` | the same text | reproduced; any other non-string is simply not a cut name |
| `zip(..., strict=True)` in `bustPieces`, `next()` without default in `squareWrist` | `ValueError: zip() argument 2 is longer than argument 1`, `StopIteration` | the same classes and text | unreachable from the drawing: the lengths are fixed by `_bust_shape` and the traced hand |
| `assert cut.shoulder_y is not None` (`raisedShoulder`, `raisedCuff`) | `AssertionError` | `AssertionError` with an empty message | the cut tables always set it |
| `HAIRSTYLES[p.hairstyle]` of an unknown cut (`hairstyleFor`, `core-head.ts`) | `KeyError: 'name'` (the repr of the key); `TypeError: unhashable type: 'list'` for a list or dict | the same classes and text (`pyValueRepr` spells the key, so an int key reads `5`) | reproduced; a name of any other type is simply a missing key |
| `min(...)` / `max(...)` of an empty generator (`pyMinIter`, `pyMaxIter`, `core-head-cuts.ts`) | `ValueError: min() iterable argument is empty` | the same text | unreachable: every traced chain has segments |
| `_arc` with `segments == 0`, `_fall_q` with `base_tip == 0.72` | `ZeroDivisionError: float division by zero` | the same (`pyDiv`) | unreachable: the callers pass constants |
| a wrong-typed number reaching `hairFall` or `eyePlacement` (a link's string in `hair_length` or `face_age`) | `TypeError: can't multiply sequence by non-int of type 'float'`; `TypeError: '<=' not supported between instances of 'str' and 'float'` | `TypeError` (same class) with the `BadValue` text `unsupported operand type(s): 'str' is not a number`. `hairFall` runs `plainParams` itself; `eyePlacement` does not, because it returns the face and Python keeps a wrong-typed flag in it as it was, so a direct caller passes a `plainParams` result, as `renderCharacter` does | class reproduced on the recorded calls; the text differs, as everywhere a `BadValue` raises |
| everything not yet ported | | | |

Anything that raises in Python but silently computes in JavaScript (`NaN`, `undefined`, `Infinity`) is turned into an
explicit error in the port, with the Python class name: a float where an `int` is needed, `zip(strict=True)` length
mismatches, `next()` on an empty iterator, a malformed hex colour. Each is listed above when it is ported.

## Per-domain notes from Phase 4

Each porting agent kept its own table of where the TypeScript differs from CPython's error text; the classes always equal
Python's. See `docs/ts-port-errors-hair.md`, `docs/ts-port-errors-face.md`, `docs/ts-port-errors-body.md`,
`docs/ts-port-errors-garments.md` and `docs/ts-port-errors-props.md`. The common cases: a number field that holds a string or
a list raises `TypeError` at the first arithmetic on it with the kernel's `BadValue` text; a division by zero from an integer
count says `float division by zero` where Python says `division by zero`.
