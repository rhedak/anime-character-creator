# Porting guide for Phase 4 (read before porting any function)

You are porting part of `src/anime_character_creator/character.py` (CPython, frozen at tag `v0.3.0`) to TypeScript in
`ts/src/`. The output must be byte-identical to Python's. This guide is the contract; `docs/ts-port-plan.md` is the why.

## 1. Rules of the work

* Never run `rm` in any form. Use Write and Edit. Do not `git add`, commit or push; the orchestrator commits.
* Do not edit the Python (`src/`, `tests/`). Do not edit files you do not own (section 6).
* No em dashes or double hyphens in prose or comments you write (hyphens in compound words and CLI flags are fine).
* Keep the Python's comments with the code they describe. They are the design record. A function's docstring becomes a JSDoc.
* Scratch files go under `$TMPDIR`, never in the repo.

## 2. Where things are and how to run

* Worktree `/Users/hanssen.henrik/git/self-study/anime-character-creator-ts`, branch `ts-port`. TypeScript in `ts/`.
* Typecheck (must be clean, strict): `cd ts && node_modules/.bin/tsc --noEmit -p .`
* Tests (a glob, not a directory): `cd ts && node --max-old-space-size=8192 --test "test/*.test.ts"`
* Python (CPython 3.13.11): `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<worktree>/src /Users/hanssen.henrik/git/self-study/anime-character-creator-dev/.venv/bin/python script.py`.
  Scripts should import `harness/ts_port/_bootstrap.py`, which asserts the package comes from this worktree.
* Module assignment (what you own): `docs/ts-port-modules.md` and `harness/ts_port/modules.json` (every top-level name with its
  Python line numbers, kind and size). Python line numbers refer to `src/anime_character_creator/character.py`.

## 3. Naming and shape

* A Python function `_hair_fall` is the TypeScript export `hairFall` (strip leading underscores, camelCase). `skeleton_for` is
  `skeletonFor`. A module-level constant or table keeps its Python name (`HAIRSTYLES`, `_SOFT_LOCK_POINTS` becomes
  `SOFT_LOCK_POINTS`; strip only the underscore). The function-level oracle finds your function by that name.
* Dataclass fields, parameter keys and anything that crosses JSON stay snake_case. `Skeleton`, `CharacterParams`, `Outfit`,
  `FaceStyle` and their defaults exist (`params.ts`, `skeleton.ts`, `model.ts`). Use `replace` from `model.ts` or `skeleton.ts`.
* Erasable TypeScript only: no `enum`, `namespace`, parameter properties, decorators. Imports use the `.ts` extension.
* Tuples are `readonly [number, number]`; a `Point` is `[x, y]`; `Chain`, `Segment` are in `tables.ts`.
* Data tables (coordinates) are generated from Python by a script, never typed: see `harness/ts_port/gen_tables.py` and add your
  tables to its `TABLES` list (write a variant script of your own, `gen_tables_<module>.py`, if you own a large set; it writes
  your own file). Hand-own the output afterwards. Tables built at import time by Python code (computed constants, `_fist()`
  style) are computed at import time in TypeScript too, by the ported code, not pasted.

## 4. The rules that keep the bytes equal

**Numbers into text, only through the kernel (`ts/src/pynum.ts`).** Never `toFixed`, `toString` or a bare `${x}` of a float.
`f"{x:.1f}"` is `fmt1(x)`, `.2f` is `fmt2`, `.0f` `fmt0`, `.3f` `fmt3`, `02x` is `fmtHex2`. A bare `f"{x}"` of a float is `pyRepr(x)`;
of an int it is `String(x)`. `round(x)` is `pyRound`, `round(x, n)` is `roundTo`, `int(x)` is `pyInt`, `math.radians` is `radians`,
`math.sqrt` is `pySqrt`, `math.acos` `pyAcos`, `math.sin` `pySin`, `math.cos` `pyCos`, `math.atan2` is `Math.atan2`,
`math.hypot` is `pyHypot` (never `Math.hypot`), `math.copysign` is `copysign`, `math.pi` is `Math.PI`, `x ** 2` is `x * x`, any other
`x ** y` is `pyPow(x, y)`, `a % b` is `pyMod` (float) or `pyModInt` (int; for a possibly negative `a`, as in `(i - 1) % n`),
`sum(...)` is `pySum(items, leadingInts)` (say how many leading items are ints; 0 when all are floats), `max`/`min` are `pyMax`/`pyMin`
(first wins on ties), `max(range(n), key=...)` is `argMax(keys)`, `sorted` is the kernel's `sorted` (never `Array.sort` without a
comparator), `s.replace(a, b)` is `pyReplace`, `x[-1]` and negative indices are `at`, `x[a:b:c]` is `pySlice`, `a / b` where `b` can
be zero is `pyDiv` (see 5), a container in a boolean position is `truthy(x)`, `a == b` on tuples or lists is `deepEqual`, `sha1` is `sha1Hex`.

**Keep the arithmetic exactly as written.** Floating point is not associative. Do not simplify, reorder, hoist or factor an
expression, do not fold constants, do not replace `x * 0.5` by `x / 2`. Keep every parenthesis that Python's precedence implies:
`a * b / c` is `(a * b) / c`. Python's unary minus binds tighter than `**` in the other direction: `-x ** 2` is `-(x ** 2)`.

**Python's `and` and `or` return an operand**, not a boolean: `a or b` is `truthy(a) ? a : b`; `a and b` is `truthy(a) ? b : a`. A
`None` default (`x = x or 1.0`) is the same trap. Chained comparisons `a <= b <= c` are `a <= b && b <= c` (TypeScript rejects
the literal form, which is a good tripwire). `x if c else y`, `in`, `not in` (on a list of numbers or strings `includes`; on tuples of numbers use `deepEqual`
over the elements), `is None` is `=== null` (a `None` that can be absent in the data is `null`, never `undefined`).

**Lists and tuples copy; JS arrays alias.** A function that mutates a list it received, or returns one of its arguments, or slices
`x[:]`, needs the copy made explicitly. `list(x)`, `x + y`, `x[::-1]` produce new lists. Comprehensions run once; a generator
that is iterated twice in Python is a bug there, do not reproduce a lazy semantics you do not need.

**Dictionaries keep insertion order and a JS object does not for integer-like keys.** Use `Map` for any table whose keys can look
like integers, and iterate in the order Python does. `dict.fromkeys(x)` is a `Set` of the items in order.

**Strings:** `"".join(x)` is `x.join("")`; `str * n` is `repeat`; `len(s)` counts code points, not UTF-16 units (use `[...s].length` if
the text can contain astral characters; the wristband text can); `s.upper()` etc. are not used. Regex: only through `pyre.ts` for
`re.sub` templates; `re.findall` and friends are ported by hand with the `u` flag and Python's `\b` semantic via lookarounds.

**Errors:** a function that raises in Python raises `new PyError("ValueError", message)` (class names are Python's, from
`pynum.ts`; the message is yours, but where the Python text is part of the documented API keep it exactly). `next(...)` with no
default on an empty iterator is `StopIteration`; `zip(..., strict=True)` of unequal lengths is `ValueError`; a float where
`range` or an index needs an int is `TypeError`. Add every place your text differs from CPython's to `docs/ts-port-errors.md`
(append rows).

**Types of numbers.** JavaScript has one number type. Where Python's behaviour depends on int against float (`isinstance`, `//`,
`str(x)`, `x == 1` on a bool), the registry in `params.ts` tells you which a parameter is; for local values decide from the
Python and say so in a comment. A `bool` is a JS `boolean`, never a number.

## 5. The hazard ledger (`harness/ts_port/hazards.json`)

Every site in `character.py` that can behave differently in JavaScript is listed: entries have `file`, `line`, `end_line`, `class`,
`detail`, `snippet`. Classes include `div` (164 sites with a variable divisor: use `pyDiv` unless the divisor provably cannot be zero
for any valid or out-of-range parameter; say in a comment when you decide that), `round`, `sum`, `mod`, `pow`, `chain`
(chained comparison), `neg_index`, `slice_step`, `sorted`, `minmax`, `str_replace`, `str_format`, `re`, `hashlib`, `eq_nonconst`,
`truthy` candidates, `augassign` (list mutation candidates) and `math.*` by function. **For every function you port, find its ledger
entries (by line range) and handle each one.** Your report lists any entry you judged harmless and why.

## 6. How to verify, and what you own

Three oracles, from cheap to strict. Use all that apply.

1. **Function level, `ts/test/calls.test.ts`.** Python recorded real calls (arguments and result) of every function over the corpus
   (`harness/ts_port/calls.py`; samples committed under `harness/ts_port/fixtures/calls/`, the full set regenerated under
   `harness/ts_port/out/calls/`). The test finds your function by its camelCase name in any `ts/src/*.ts` export and replays every
   call. Floats must match bit for bit, or within 4 ulp where `sin`, `cos`, `acos`, `**` or `atan2` from the maths library are involved. To
   debug one function: write a scratch script that decodes `out/calls/<function>.json` with `ts/test/calls-codec.ts`.
2. **Stage level, `ts/test/stages.test.ts`.** Every part slot of `render_character` (53 of them, named `chest[3]`, `layers[26]`)
   is compared by sha256 and length with Python's on the 68 mini cases (and on the full corpus once it exists), the moment the parts
   it needs are present. A part is registered by adding it to the `PARTS` table of your domain module under its Python name.
3. **Document level.** When every part exists, `renderCharacter` equals Python's whole SVG.

You own the files named in your assignment (`ts/src/core-*.ts` or `ts/src/parts-*.ts`, plus any `ts/src/<yourmodule>-*.ts` you add
and your own tests in `ts/test/`). You may import from the kernel and from modules listed as your dependencies. You may NOT edit
`render.ts`, `parts.ts`, the kernel, `character.ts`, another module's files or the shared fixtures; if you need something changed
there, do not work around it silently: say so in your report. If you need a kernel function that is missing, write it in your own
file and tell me.

## 7. Method that works

Port in dependency order inside your module (callees first; `modules.json` lines and the Python calls give the order). Port a
function, typecheck, replay its recorded calls, fix, go on. Never leave a failing function ported: if one will not match, say which
and why in the report and leave it unexported rather than wrong. A function with no recorded calls was never called by the corpus:
port it carefully anyway and list it in the report as untested. After each batch run the whole suite, not only your tests.

## 8. The report

Under 60 lines: the functions ported (counts), the tests and commands, how many recorded calls were replayed and how many
mismatched (and which), each ledger entry you judged harmless, each place you could not match Python, each kernel function you
missed, each file you created, and what you did not do.
