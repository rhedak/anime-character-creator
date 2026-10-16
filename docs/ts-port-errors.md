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
| everything not yet ported | | | |

Anything that raises in Python but silently computes in JavaScript (`NaN`, `undefined`, `Infinity`) is turned into an
explicit error in the port, with the Python class name: a float where an `int` is needed, `zip(strict=True)` length
mismatches, `next()` on an empty iterator, a malformed hex colour. Each is listed above when it is ported.
