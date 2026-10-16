# Function-level call oracle for the TypeScript port

The whole-document oracle (`manifest*.py`, stage hashes of the 53 part slots) cannot test a shared
helper on its own: `character.py` has 303 module-level `def`s (302 distinct names) in about 14,000 lines, many of them
used by several parts, and a helper has no stage until a root part that uses it is ported. This oracle
records REAL calls of every function (arguments and result) while a corpus renders, so a helper can be
replayed and compared in TypeScript by function name before any root part exists.

Everything is produced by `harness/ts_port/calls.py` from the FROZEN package in this worktree's `src/`
(tag v0.3.0, CPython 3.13.11). Nothing here is hand-written data.

## What is recorded

Every module-level `def` of `character.py`, `skeleton.py`, `colorutil.py`, `presets.py` and
`urlstate.py` (not `attribution`, not `catalogue`), plus the methods and properties of the dataclasses
defined in those modules (`Class.method`, dunders skipped). The result of `calls.py record` is in
`out/calls/` (not committed) and a sample in `fixtures/calls/` (committed).

<!-- BEGIN:summary -->
| | |
|---|---|
| corpora | wide, full (15615 cases, 15554 renders, 512 driver calls that raised: render, urlstate) |
| functions recorded | 329 (character function: 302, character method: 3, colorutil function: 7, presets function: 2, skeleton function: 4, skeleton method: 2, skeleton property: 4, urlstate function: 5) |
| called at least once | 328 |
| never called | 1 |
| with some unrecordable calls | 17 |
| called but no call kept | 12 |
| total calls | 52307671 |
| distinct calls | 2374556 |
| calls kept in `out/calls` | 37025 (156815943 bytes in 332 files) |
| calls in `fixtures/calls` | 852 (2886119 bytes in 318 files, limit 3,000,000; at most 3 calls and 41423 bytes per function file) |
| time | record 118.8 s of rendering and 0.4 s of import, single process |
<!-- END:summary -->

## Commands

Run from the worktree root, always with the venv Python and no bytecode:

```
PY=/Users/hanssen.henrik/git/self-study/anime-character-creator-dev/.venv/bin/python
export PYTHONDONTWRITEBYTECODE=1
$PY harness/ts_port/calls.py record [--corpus wide,full] [--limit N] [--out SCRATCH_DIR]
$PY harness/ts_port/calls.py check  [--limit N]
$PY harness/ts_port/calls.py selftest
$PY harness/ts_port/calls.py replay [--dir out|fixtures]
$PY harness/ts_port/calls.py list-uncalled
$PY harness/ts_port/calls.py sample
$PY harness/ts_port/calls.py doc
```

- `record`: records, writes `out/calls/*.json`, `out/calls/_index.json`, `out/calls/_registry.json`,
  `out/calls/_wrapped_hashes.json` and then the committed sample. `--corpus` is a comma list of `mini`
  (`corpus/mini.json`, 68 cases), `wide` (`corpus_wide.py`, each case rendered with `id_prefix` `""` and
  `"x"`) and `full` (`corpus/full.json` plus `corpus/errors.json`, which includes the raising renders and
  the urlstate operations). The default is `wide,full` when `corpus/full.json` exists, else `wide`.
  `--limit N` stops after N cases. `--out DIR` writes `DIR/calls` and `DIR/fixtures` instead (used for
  the determinism test: two runs give byte-identical files, apart from the two timing fields of the
  index meta).
- `check`: the byte-identity proof. It renders the same corpus in a process that never installs the
  hook (plain package) and compares the sha256 of every document, and of every exception text, with the
  hashes the recording run saved in `out/calls/_wrapped_hashes.json`. It then runs `selftest`.
- `selftest`: the wrapper on a synthetic module: internal calls are intercepted, values and exceptions
  pass through unchanged, a mutated argument is detected, callables and generators are flagged, `-0.0`,
  `0.0`, `1` and `True` are four distinct calls.
- `replay`: the Python reference for the TypeScript replay. In a plain process it decodes every
  recorded call (the decoder below), calls the real function, encodes the result and compares it with
  the recorded one; it also checks that the decoded arguments encode back to the recorded text and that
  the registry is unchanged. 0 mismatches is the expected output, and it is also the test that the
  functions are pure over the recorded calls.
- `list-uncalled`, `sample` (rebuild `fixtures/calls` from `out/calls`), `doc` (refresh the tables
  between the markers of this file).

## How the recording works

1. An AST import hook (the same idea as `instrument.py`; no `.pyc` is read or written) loads the five
   modules from source. After each module-level `def f` it inserts `f = __cw(f, __name__)` and after each
   module-level class `__cwc(Cls, __name__)`. `__cw` returns a recording wrapper (`functools.wraps`, so
   `inspect.signature` still works) and `__cwc` replaces the methods and properties of the class.
2. Because the name is rebound inside the module, every later use is the wrapper: internal calls (a
   global lookup at call time), `from .colorutil import shade` in `character.py`, and the functions kept
   in module-level tables. The self test proves interception on a synthetic module, and in the real
   run helpers that only other functions call, such as `_lerp`, have millions of recorded calls.
3. The wrapper returns exactly what the function returns and re-raises its exception unchanged. It
   raises the recursion limit to 3000 because a wrapper doubles the Python frames of a call.
4. Calls made while the package imports (module constants built by helpers: `_fist`, `_square_wrist`,
   `_before`, ...) and while the corpus code builds the next case (`Expression.applied_to`, the validators
   in `__post_init__`) are recorded too. The index counts them separately (`calls_by_phase`: import,
   build, drive). Recording is off between cases.
5. A call is keyed by a fast structural key (floats by their IEEE bits, so `0.0` and `-0.0` differ and `1`
   and `1.0` differ; the registry ref name is part of the key; a frozen dataclass key is cached by object
   id for the length of one case). That tells calls apart exactly as the sha256 of the canonical JSON of
   (args, kwargs) does, and `record` asserts that the kept calls of every function have distinct sha256.
6. Per function kept: the first 40 distinct calls (`why: first`); up to 40 more from a reservoir over
   the rest of the distinct calls with a fixed seed per function (`sample`); every distinct call that
   raised, up to 1000 per function (`raises`); the calls holding the minimum and the maximum of each
   float argument position, looking into tuples and lists (up to depth 3 and 64 items), dataclass
   fields and dict values (`min:a0`, `max:a2[1]`, `min:a0.head_r`, `max:k:saturation_boost`; at most
   160 positions per function); and up to 3 calls each with a `nan`, an infinity or a `-0.0` among the
   floats (`special:nan`, `special:inf`, `special:negzero`). A call that is kept for several reasons
   lists them all in `why`.
7. A call whose JSON (args, kwargs and result) would exceed 200,000 bytes is skipped and counted in
   `skipped_large` (for example `_soft_stroke_widths` and `_namespace_ids`, which take whole layer
   strings). A call with a function, class or other un-encodable value as an argument, or a callable,
   generator or other lazy result, is counted in `unrecordable` with its reason and not kept.
8. `count` of a kept call is how many times that exact call happened over the whole run.
   `total_calls` is every call, `distinct` the number of distinct calls (64-bit hash of the key; a
   collision is possible in theory, not expected at 2.4 million), `kept` the calls written.

The corpus records all renders of the chosen corpora, including the ones that raise: a function that
raises on a valid-looking input is data (`validate_finish`, `skeleton_for`, `_face`, ...).

## Encoding

| Python value | JSON |
|---|---|
| `float` | `"f:" + 16 hex digits`, the big-endian IEEE-754 bits (`"f:3ff0000000000000"` is 1.0; `-0.0`, infinities and nan keep their bits) |
| `int` | `"i:" + decimal` |
| `bool` | `"b:1"` / `"b:0"` |
| `str` | `"s:" + text` (ordinary JSON string escaping, ASCII only in the files) |
| `None` | `null` |
| `tuple` | `{"t": [...]}` |
| `list` | `{"l": [...]}` |
| `dict` | `{"d": [[key, value], ...]}` in insertion order |
| `set` / `frozenset` | `{"set": [...]}` members sorted by their compact JSON text; a frozenset also has `"frozen": true` |
| dataclass instance | `{"dc": "ClassName", "f": {field: value, ...}}` in field order |
| object that IS (by identity) a registered module-level constant | `{"ref": "HAIRSTYLES.long_blunt"}`, resolved with `_registry.json` |
| exception (result only) | `{"exc": "ClassName", "msg": "..."}` |

A bool is a bool and an int is an int: `True` and `1` are different calls. Only exact types are
encoded (`type(v) is float`, ...); a subclass would be reported as unrecordable, and none occurred.

Result of a recorded call: an encoded value, or the `exc` object when the call raised. Compare floats by
their bits (so `-0.0` and `0.0` differ and nan equals nan when the bits are equal).

## Files

`out/calls/<stem>.json` (and the same shape under `fixtures/calls/`, fewer calls):

```
{"function": "_hair_fall", "module": "character", "line": 1234, "kind": "function",
 "total_calls": n, "calls_by_phase": {"import": n, "build": n, "drive": n},
 "distinct": n, "unrecordable": n, "skipped_large": n, "raised_distinct": n, "kept": n,
 "calls": [{"args": [...], "kwargs": {...}, "result": ..., "count": n, "why": [...]}, ...]}
```

- `stem` is the function name, except that a name defined in two modules gets `module.name`
  (`skeleton._lerp.json` and `character._lerp.json`). A method is `Class.method.json`.
- `kind` is `function`, `method` or `property`. A property call has the instance as `args[0]` and no
  other arguments; a method call has the instance as `args[0]`.
- `kwargs` is keyed by the Python parameter name, sorted by name, values encoded. Arguments passed
  positionally are in `args`, as the real call spelled them (the recording is of the call, not of the
  bound signature).
- `line` is the line of the `def` in the frozen source.
- `out/calls/_index.json`: `{"meta": {...}, "functions": [one entry per function]}`; each entry has the
  counts above plus `stem`, `signature` (from `inspect`, annotations as strings), `unrecordable_reasons`,
  `lazy_results`, `mutates_arguments`, `large_examples`, `float_positions`, `kept_reasons`, and for a
  function defined twice `shadowed_def`.
- `out/calls/_registry.json`: `{"constants": {name: {"module", "kind", "level", "value"}}}`. `value` is
  the constant encoded BY VALUE (its children are refs where they are registered themselves, so
  `PRESETS` is a dict of refs to `SATOKO` and so on). A TypeScript decoder resolves
  `{"ref": name}` to `constants[name].value` (decoded recursively) or to its own constant of the same
  name. `{"fn": "character._clip_bar"}` appears only inside registry values: a `Hairstyle` and a `HAIR_CLIPS`
  entry hold functions (`mass`, `hairline`, `fall_edge`, ... are function fields), so a call that takes
  `HAIRSTYLES.long_blunt` is recordable as a ref and the TS table must map the name to the TS function.
- `out/calls/_wrapped_hashes.json`: `[[case id, sha256 of the document or "EXC Type: message"], ...]`
  for every render of the run (used by `check`).

## The committed sample

`fixtures/calls/` has one file per called function with at most 12 calls and at most 60 KB per file
(same shape as `out/calls`; `_index.json` and `_registry.json` are copied beside them), chosen from the
kept calls: every raising call first (up to half of the file), then a greedy cover of the min and max
tags, one `special` call, then calls spread evenly over the rest. The number of calls per file is
lowered together with the per-file byte limit until all files fit 2.45 MB (the registry and the index
take the rest of the 3 MB), so the summary above says how many calls per function this run could
afford. A function whose calls are all unrecordable or too large has no file. `sample` rebuilds the
directory from `out/calls` without rerunning the corpus; files of an earlier run that are no longer
written are removed.

## Replaying in TypeScript

The Python decoder is `py_decode` in `calls.py` (about 30 lines), the TS decoder is its mirror:

1. Read the JSON text so that floats are the 16 hex digits, never a JS number; decode `"f:"` with a
   `DataView` (`setBigUint64` then `getFloat64`). Compare results by bits.
2. Decode each argument by the table above. Tuples and lists are both arrays on the TS side; keep the
   distinction if the function tests it. A `dc` becomes the TS object of that class (the field names are
   the Python field names). A `ref` becomes the TS constant of that name.
3. Call the function whose `function` field is the Python name (the port's naming convention applies, for
   example `_hair_fall` is `hairFall`; this oracle records only the Python name, `module`, `kind` and, for
   methods and properties, `Class.name`). Call it with `args` and `kwargs` (kwargs by Python parameter
   name).
4. Encode the result with the same table and compare it with `result` as bits. A recorded `exc` means
   the call raised that exception class with that message (Python's message text).

A function with `unrecordable` calls only (see below) has to be tested through the stages that use it.

## Findings

- 302 character functions are defined, but `_straight` is defined twice (lines 1990 and 2697). The later
  def wins everywhere at call time (the first one is never called, `shadowed_def` in the index).
- Functions returning or taking a callable cannot be recorded (table below). All of them are
  placement or path-builder helpers: they return a transform `Callable[[Point], Point]` or take one.
- No function mutated an argument over the whole corpus (`mutates_arguments` is 0 everywhere) and no
  function returned a generator or other lazy object.
- `Hairstyle`, `GarmentCut`, `BeltCut`, `SleeveCut` are frozen dataclasses; `Hairstyle` fields hold
  functions. Registry values show them as `{"fn": ...}`.
- The registry value check at the end of the run found no changed constant (`registry_mutated` in the
  index meta is empty).
- A raise is recorded by every wrapper on the stack that it passes through, so a bad input shows up as
  a raising call of the function that raised and of each caller up to `render_character`.

## Functions

Columns: total calls over the run, calls made at import and while building cases, distinct calls, calls
kept in `out/calls`, unrecordable calls, calls skipped as too large, distinct raising calls, and whether
a file exists in `fixtures/calls`.

<!-- BEGIN:functions -->
| function | module | line | total calls | import / corpus build | distinct | kept | unrecordable | skipped large | raising (distinct) | in fixtures |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `_stroke_w` | character | 44 | 622114 | 0 / 0 | 1768 | 93 | 0 | 0 | 0 | yes |
| `validate_finish` | character | 89 | 46615 | 0 / 0 | 11383 | 269 | 0 | 0 | 61 | yes |
| `_soft` | character | 102 | 149445 | 0 / 0 | 11012 | 200 | 0 | 0 | 0 | yes |
| `_soft_locks_on` | character | 107 | 26166 | 0 / 0 | 10894 | 196 | 0 | 0 | 0 | yes |
| `_soft_lines` | character | 113 | 6264 | 0 / 0 | 2582 | 80 | 0 | 0 | 0 | yes |
| `_soft_stroke_widths` | character | 118 | 3115 | 0 / 0 | 2375 | 76 | 0 | 21 | 0 | yes |
| `_outline_w` | character | 131 | 545667 | 0 / 0 | 3033 | 89 | 0 | 0 | 0 | yes |
| `_interior_w` | character | 136 | 601112 | 0 / 0 | 2155 | 86 | 0 | 0 | 0 | yes |
| `Expression.on` | character | 277 | 286 | 0 / 286 | 286 | 85 | 0 | 0 | 0 | yes |
| `Expression.applied_to` | character | 282 | 286 | 0 / 286 | 286 | 80 | 0 | 0 | 0 | yes |
| `_head_units` | character | 750 | 9016815 | 0 / 0 | 603001 | 95 | 0 | 0 | 0 | yes |
| `_curve` | character | 756 | 458237 | 0 / 0 | 32460 | 120 | 0 | 0 | 0 | yes |
| `_fade_y` | character | 812 | 5886 | 0 / 0 | 178 | 82 | 0 | 0 | 0 | yes |
| `_fall` | character | 827 | 275385 | 0 / 0 | 4176 | 87 | 0 | 0 | 0 | yes |
| `_mirror` | character | 831 | 39240 | 0 / 0 | 792 | 88 | 0 | 0 | 0 | yes |
| `_mirrored` | character | 838 | 7580 | 0 / 0 | 421 | 83 | 0 | 0 | 0 | yes |
| `_scale_point` | character | 847 | 4590 | 0 / 0 | 85 | 80 | 0 | 0 | 0 | yes |
| `_reverse` | character | 853 | 41748 | 0 / 0 | 1416 | 94 | 0 | 0 | 0 | yes |
| `_arc` | character | 862 | 20716 | 0 / 0 | 3 | 3 | 0 | 0 | 0 | yes |
| `_fall_edge` | character | 907 | 24558 | 0 / 0 | 350 | 83 | 0 | 0 | 0 | yes |
| `_hair_mass_shape` | character | 922 | 5685 | 0 / 0 | 350 | 82 | 0 | 0 | 0 | yes |
| `_hair_tip_edge` | character | 964 | 313 | 0 / 0 | 66 | 66 | 0 | 0 | 0 | yes |
| `_hairline_shape` | character | 1009 | 9203 | 0 / 0 | 311 | 83 | 0 | 0 | 0 | yes |
| `_long_strands` | character | 1077 | 4537 | 0 / 0 | 308 | 83 | 0 | 0 | 0 | yes |
| `_center_part_hairline_shape` | character | 1126 | 648 | 0 / 0 | 68 | 68 | 0 | 0 | 0 | yes |
| `_center_part_strands` | character | 1169 | 319 | 0 / 0 | 64 | 64 | 0 | 0 | 0 | yes |
| `_short_mass_shape` | character | 1208 | 3113 | 0 / 0 | 47 | 47 | 0 | 0 | 0 | yes |
| `_short_fall_edge` | character | 1253 | 12137 | 0 / 0 | 47 | 47 | 0 | 0 | 0 | yes |
| `_short_tip_edge` | character | 1267 | 277 | 0 / 0 | 23 | 23 | 0 | 0 | 0 | yes |
| `_short_hairline_shape` | character | 1313 | 4856 | 0 / 0 | 47 | 47 | 0 | 0 | 0 | yes |
| `_short_strands` | character | 1365 | 2425 | 0 / 0 | 46 | 46 | 0 | 0 | 0 | yes |
| `_long_scaled` | character | 1460 | 15829 | 0 / 0 | 283 | 82 | 0 | 0 | 0 | yes |
| `_long_line` | character | 1494 | 6924 | 0 / 0 | 283 | 82 | 0 | 0 | 0 | yes |
| `_long_traced_mass` | character | 1517 | 4824 | 0 / 0 | 283 | 82 | 0 | 0 | 0 | yes |
| `_long_traced_fall_edge` | character | 1524 | 3461 | 0 / 0 | 282 | 81 | 0 | 0 | 0 | yes |
| `_long_traced_hairline` | character | 1535 | 6924 | 0 / 0 | 283 | 82 | 0 | 0 | 0 | yes |
| `_long_traced_tip_edge` | character | 1574 | 620 | 0 / 0 | 57 | 57 | 0 | 0 | 0 | yes |
| `_lifted_tip_edge` | character | 1594 | 914 | 0 / 0 | 91 | 81 | 0 | 0 | 0 | yes |
| `_restretch_locks` | character | 1643 | 624 | 0 / 0 | 120 | 80 | 0 | 0 | 0 | yes |
| `_long_traced_locks` | character | 1655 | 424 | 0 / 0 | 81 | 80 | 0 | 0 | 0 | yes |
| `_short_locks` | character | 1675 | 480 | 0 / 0 | 34 | 34 | 0 | 0 | 0 | yes |
| `_crop_locks` | character | 1694 | 1850 | 0 / 0 | 40 | 40 | 0 | 0 | 0 | yes |
| `_parted_locks` | character | 1713 | 200 | 0 / 0 | 39 | 39 | 0 | 0 | 0 | yes |
| `_long_traced_strands` | character | 1717 | 3461 | 0 / 0 | 282 | 81 | 0 | 0 | 0 | yes |
| `_fall_q` | character | 1934 | 46585 | 0 / 0 | 231 | 16 | 46551 | 0 | 16 | yes |
| `_parted_q` | character | 1968 | 21941 | 0 / 0 | 131 | 8 | 21923 | 0 | 8 | yes |
| `_parted` | character | 1973 | 19957 | 0 / 0 | 743 | 89 | 0 | 0 | 8 | yes |
| `_anchor` | character | 1980 | 15118 | 0 / 0 | 857 | 81 | 0 | 0 | 0 | yes |
| `_sub_chain` | character | 1985 | 7150 | 0 / 0 | 604 | 81 | 0 | 0 | 0 | yes |
| `_parted_mass` | character | 1995 | 1961 | 0 / 0 | 123 | 81 | 0 | 0 | 0 | yes |
| `_parted_hairline` | character | 2002 | 1194 | 0 / 0 | 123 | 82 | 0 | 0 | 3 | yes |
| `_parted_fall_edge` | character | 2023 | 988 | 0 / 0 | 119 | 81 | 0 | 0 | 0 | yes |
| `_parted_tip_edge` | character | 2036 | 294 | 0 / 0 | 34 | 34 | 0 | 0 | 0 | yes |
| `_parted_tip_lines` | character | 2051 | 1984 | 0 / 0 | 123 | 80 | 0 | 0 | 0 | yes |
| `_parted_underside` | character | 2065 | 2006 | 0 / 0 | 130 | 85 | 0 | 0 | 7 | yes |
| `_crop_real_point` | character | 2313 | 4590 | 0 / 0 | 85 | 80 | 0 | 0 | 0 | yes |
| `_crop_outline` | character | 2430 | 11663 | 0 / 0 | 63 | 63 | 0 | 0 | 0 | yes |
| `_crop_indices` | character | 2449 | 7639 | 0 / 0 | 63 | 63 | 0 | 0 | 0 | yes |
| `_crop_mass_shape` | character | 2458 | 4024 | 0 / 0 | 63 | 63 | 0 | 0 | 0 | yes |
| `_crop_fall_edge` | character | 2471 | 2541 | 0 / 0 | 59 | 59 | 0 | 0 | 0 | yes |
| `_crop_hairline_shape` | character | 2488 | 5098 | 0 / 0 | 63 | 63 | 0 | 0 | 0 | yes |
| `_crop_tip_edge` | character | 2539 | 633 | 0 / 0 | 29 | 29 | 0 | 0 | 0 | yes |
| `_crop_strands` | character | 2577 | 2541 | 0 / 0 | 59 | 59 | 0 | 0 | 0 | yes |
| `character._lerp` | character | 2649 | 45242 | 0 / 0 | 676 | 83 | 0 | 0 | 0 | yes |
| `_tousle_side` | character | 2653 | 2567 | 0 / 0 | 32 | 32 | 0 | 0 | 0 | yes |
| `_polar` | character | 2692 | 6288 | 0 / 0 | 11 | 11 | 0 | 0 | 0 | yes |
| `_straight` | character | 2697 | 32572 | 0 / 0 | 627 | 82 | 0 | 0 | 0 | yes |
| `_chain` | character | 2704 | 524 | 0 / 0 | 1 | 1 | 0 | 0 | 0 | yes |
| `_tousle_mass_shape` | character | 2713 | 524 | 0 / 0 | 32 | 32 | 0 | 0 | 0 | yes |
| `_mirror_pt` | character | 2735 | 3144 | 0 / 0 | 99 | 81 | 0 | 0 | 0 | yes |
| `_tousle_fall_edge` | character | 2739 | 1519 | 0 / 0 | 32 | 32 | 0 | 0 | 0 | yes |
| `_tousle_hairline_shape` | character | 2745 | 610 | 0 / 0 | 32 | 32 | 0 | 0 | 0 | yes |
| `_tousle_fringe_line` | character | 2780 | 610 | 0 / 0 | 1 | 1 | 0 | 0 | 0 | yes |
| `_tousle_tip_edge` | character | 2792 | 118 | 0 / 0 | 16 | 16 | 0 | 0 | 0 | yes |
| `_tousle_strands` | character | 2846 | 299 | 0 / 0 | 32 | 32 | 0 | 0 | 0 | yes |
| `_fringed` | character | 3336 | 24464 | 0 / 0 | 3242 | 89 | 0 | 0 | 8 | yes |
| `_fringed_mass` | character | 3343 | 1392 | 0 / 0 | 93 | 81 | 0 | 0 | 1 | yes |
| `_fringed_hairline` | character | 3347 | 1236 | 0 / 0 | 99 | 82 | 0 | 0 | 7 | yes |
| `_fringed_fall_edge` | character | 3354 | 606 | 0 / 0 | 87 | 81 | 0 | 0 | 0 | yes |
| `_fringed_tip_edge` | character | 3358 | 177 | 0 / 0 | 22 | 22 | 0 | 0 | 1 | yes |
| `_fringed_strands` | character | 3362 | 606 | 0 / 0 | 87 | 80 | 0 | 0 | 0 | yes |
| `_fringed_locks` | character | 3383 | 180 | 0 / 0 | 36 | 36 | 0 | 0 | 0 | yes |
| `_fringed_underside` | character | 3388 | 1232 | 0 / 0 | 92 | 81 | 0 | 0 | 0 | yes |
| `_fringed_openings` | character | 3392 | 606 | 0 / 0 | 87 | 81 | 0 | 0 | 0 | yes |
| `_fringed_shade` | character | 3396 | 606 | 0 / 0 | 87 | 81 | 0 | 0 | 0 | yes |
| `_long_fall_edges` | character | 3503 | 4856 | 0 / 0 | 344 | 83 | 0 | 0 | 0 | yes |
| `_short_fall_edges` | character | 3507 | 2425 | 0 / 0 | 46 | 46 | 0 | 0 | 0 | yes |
| `_tousle_fall_edges` | character | 3511 | 299 | 0 / 0 | 32 | 32 | 0 | 0 | 0 | yes |
| `_hair_fall` | character | 3614 | 50177 | 0 / 0 | 11057 | 221 | 0 | 0 | 12 | yes |
| `_hair_tip_tone` | character | 3636 | 50671 | 0 / 0 | 11045 | 202 | 0 | 0 | 0 | yes |
| `_hair_lines` | character | 3643 | 30522 | 0 / 0 | 21869 | 201 | 0 | 0 | 0 | yes |
| `_hair_defs` | character | 3650 | 15420 | 0 / 0 | 11062 | 246 | 0 | 0 | 38 | yes |
| `_two_tone_hair` | character | 3681 | 30522 | 0 / 0 | 21869 | 201 | 0 | 0 | 0 | yes |
| `_hair_mass` | character | 3692 | 15346 | 0 / 0 | 11001 | 208 | 0 | 0 | 0 | yes |
| `_hair_tip_lines` | character | 3711 | 1984 | 0 / 0 | 406 | 96 | 0 | 0 | 0 | yes |
| `_hair_underside` | character | 3742 | 1612 | 0 / 0 | 971 | 157 | 0 | 0 | 0 | yes |
| `_chin_shadow` | character | 3775 | 289 | 0 / 0 | 208 | 104 | 0 | 0 | 0 | yes |
| `_neck` | character | 3786 | 15346 | 0 / 0 | 11001 | 208 | 0 | 0 | 0 | yes |
| `_sleeve_hem_y` | character | 3844 | 1047650 | 0 / 0 | 1779 | 94 | 0 | 0 | 0 | yes |
| `_sleeve_half_w` | character | 3851 | 163316 | 0 / 0 | 1772 | 94 | 0 | 0 | 0 | yes |
| `_sleeve_under_cap` | character | 3863 | 59370 | 0 / 0 | 11105 | 213 | 0 | 0 | 0 | yes |
| `_cap_tip_x` | character | 3880 | 62689 | 0 / 0 | 1007 | 94 | 0 | 0 | 0 | yes |
| `_cap_underside_y` | character | 3891 | 52268 | 0 / 0 | 2003 | 99 | 0 | 0 | 0 | yes |
| `_cap_tip_y` | character | 3905 | 26134 | 0 / 0 | 1002 | 95 | 0 | 0 | 0 | yes |
| `_shoulder_slope` | character | 3909 | 56665 | 0 / 0 | 1772 | 93 | 0 | 0 | 0 | yes |
| `_bare_neck_lift` | character | 3921 | 1137 | 0 / 0 | 35 | 35 | 0 | 0 | 0 | yes |
| `_bare_shoulder_sk` | character | 3935 | 53597 | 0 / 0 | 11001 | 206 | 0 | 0 | 0 | yes |
| `_torso_at_armpit` | character | 3951 | 802006 | 0 / 0 | 1775 | 94 | 0 | 0 | 0 | yes |
| `_armpit_x` | character | 3966 | 327826 | 0 / 0 | 4553 | 106 | 0 | 0 | 4 | yes |
| `_rib_ctrl_y` | character | 3975 | 466925 | 0 / 0 | 1771 | 91 | 0 | 0 | 0 | yes |
| `_under_bust_y` | character | 3989 | 29508 | 0 / 0 | 1014 | 94 | 0 | 0 | 0 | yes |
| `_quad_crossing` | character | 3998 | 265454 | 0 / 0 | 2670 | 86 | 0 | 0 | 0 | yes |
| `_quad_split` | character | 4008 | 273702 | 0 / 0 | 2890 | 89 | 0 | 0 | 0 | yes |
| `_rib` | character | 4016 | 61046 | 0 / 0 | 7114 | 102 | 0 | 0 | 0 | yes |
| `_Bust.pieces` | character | 4082 | 230220 | 0 / 0 | 1692 | 88 | 0 | 0 | 0 | yes |
| `_bust_shape` | character | 4088 | 510963 | 0 / 0 | 7087 | 102 | 0 | 0 | 0 | yes |
| `_redefine_ids` | character | 4164 | 5620 | 0 / 0 | 1344 | 80 | 0 | 0 | 0 | yes |
| `_bust_over_arms` | character | 4175 | 15317 | 0 / 0 | 10972 | 207 | 0 | 0 | 0 | yes |
| `_bust_lines` | character | 4270 | 15445 | 0 / 0 | 11087 | 213 | 0 | 0 | 0 | yes |
| `_bust_fold` | character | 4298 | 20836 | 0 / 0 | 2863 | 95 | 0 | 0 | 0 | yes |
| `_breast_ellipse` | character | 4351 | 21584 | 0 / 0 | 1805 | 94 | 0 | 0 | 0 | yes |
| `_bare_breast_spine` | character | 4371 | 748 | 0 / 0 | 267 | 96 | 0 | 0 | 0 | yes |
| `_bare_breasts` | character | 4418 | 268 | 0 / 0 | 267 | 97 | 0 | 0 | 0 | yes |
| `_underwear_top` | character | 4460 | 15445 | 0 / 0 | 11087 | 213 | 0 | 0 | 0 | yes |
| `_chest_lines` | character | 4514 | 15445 | 0 / 0 | 11087 | 213 | 0 | 0 | 0 | yes |
| `_navel` | character | 4563 | 15445 | 0 / 0 | 11087 | 212 | 0 | 0 | 0 | yes |
| `_rib_skeleton` | character | 4582 | 1122 | 0 / 0 | 45 | 45 | 0 | 0 | 0 | yes |
| `_torso` | character | 4605 | 15346 | 0 / 0 | 11001 | 208 | 0 | 0 | 0 | yes |
| `_body_inset` | character | 4753 | 31546 | 0 / 0 | 11001 | 208 | 0 | 0 | 0 | yes |
| `_tunic` | character | 4764 | 15453 | 0 / 0 | 11095 | 221 | 0 | 0 | 8 | yes |
| `_hair_tail` | character | 4982 | 15354 | 0 / 0 | 11009 | 214 | 0 | 0 | 8 | yes |
| `_tail_tie` | character | 5028 | 2380 | 0 / 0 | 285 | 85 | 0 | 0 | 0 | yes |
| `_headscarf` | character | 5063 | 15156 | 0 / 0 | 10848 | 203 | 0 | 0 | 0 | yes |
| `skeleton_for` | character | 5478 | 39873 | 0 / 0 | 11132 | 237 | 0 | 0 | 35 | yes |
| `_skeleton_at` | character | 5492 | 39873 | 0 / 0 | 11132 | 234 | 0 | 0 | 29 | yes |
| `_quad_point` | character | 5538 | 4278748 | 124 / 0 | 117858 | 89 | 0 | 0 | 0 | yes |
| `_bust_panel_line` | character | 5555 | 3973 | 0 / 0 | 796 | 91 | 0 | 0 | 0 | yes |
| `_quad_x_at` | character | 5574 | 534588 | 0 / 0 | 22940 | 88 | 0 | 0 | 0 | yes |
| `_bust_bulge` | character | 5587 | 412910 | 0 / 0 | 11995 | 97 | 0 | 0 | 0 | yes |
| `_body_knots` | character | 5605 | 48770 | 0 / 0 | 602 | 90 | 0 | 0 | 0 | yes |
| `_interp` | character | 5652 | 2493911 | 0 / 0 | 147466 | 91 | 0 | 0 | 0 | yes |
| `_interp_flat` | character | 5665 | 1516874 | 0 / 0 | 78426 | 91 | 0 | 0 | 0 | yes |
| `_garment_placement` | character | 5673 | 20715 | 0 / 0 | 846 | 0 | 20715 | 0 | 0 | no |
| `_arm_swing` | character | 5759 | 10140 | 0 / 0 | 774 | 137 | 0 | 0 | 0 | yes |
| `_raised_coat_sleeve` | character | 5764 | 118406 | 0 / 0 | 22002 | 200 | 0 | 0 | 0 | yes |
| `_raised_shoulder` | character | 5772 | 42768 | 0 / 0 | 20822 | 210 | 0 | 0 | 0 | yes |
| `_chain_until_y` | character | 5793 | 183 | 0 / 0 | 2 | 2 | 0 | 0 | 0 | yes |
| `_reversed_chain` | character | 5822 | 100 | 0 / 0 | 2 | 2 | 0 | 0 | 0 | yes |
| `_sleeve_cutaway` | character | 5834 | 1687 | 0 / 0 | 1041 | 160 | 0 | 0 | 0 | yes |
| `_without_raised_sleeves` | character | 5937 | 15346 | 0 / 0 | 11001 | 199 | 0 | 0 | 0 | yes |
| `_cutaway_side_lines` | character | 5945 | 1687 | 0 / 0 | 1041 | 152 | 0 | 0 | 0 | yes |
| `_traced_coat` | character | 5955 | 165598 | 0 / 0 | 11087 | 213 | 0 | 0 | 0 | yes |
| `_traced_coat_and_belt` | character | 5959 | 30741 | 0 / 0 | 22038 | 215 | 0 | 0 | 4 | yes |
| `_hip_pockets` | character | 6000 | 1687 | 0 / 0 | 1041 | 157 | 0 | 0 | 0 | yes |
| `_coat_buttons` | character | 6008 | 1687 | 0 / 0 | 1041 | 159 | 0 | 0 | 0 | yes |
| `_cut_half_w_at` | character | 6026 | 199 | 0 / 0 | 101 | 82 | 0 | 0 | 0 | yes |
| `_draw_cut` | character | 6054 | 10622 | 0 / 0 | 1770 | 93 | 3222 | 0 | 0 | yes |
| `_leg_placement` | character | 6116 | 3670 | 0 / 0 | 940 | 0 | 3670 | 0 | 0 | no |
| `_leg_cut_top_y` | character | 6137 | 448 | 0 / 0 | 80 | 80 | 0 | 0 | 0 | yes |
| `_draw_leg_cut` | character | 6147 | 3222 | 0 / 0 | 1054 | 93 | 0 | 0 | 0 | yes |
| `hat_hair_margin` | character | 6607 | 39873 | 0 / 0 | 11132 | 209 | 0 | 0 | 0 | yes |
| `_hat_underside` | character | 6623 | 15369 | 0 / 0 | 11024 | 224 | 0 | 0 | 15 | yes |
| `_hat` | character | 6639 | 15156 | 0 / 0 | 10848 | 203 | 0 | 0 | 0 | yes |
| `_hair_tie` | character | 6679 | 15176 | 0 / 0 | 10868 | 203 | 0 | 0 | 0 | yes |
| `_clip_bar` | character | 6716 | 708 | 0 / 0 | 235 | 82 | 0 | 0 | 0 | yes |
| `_clip_crossed` | character | 6727 | 40 | 0 / 0 | 21 | 21 | 0 | 0 | 0 | yes |
| `_clip_snap` | character | 6738 | 51 | 0 / 0 | 26 | 26 | 0 | 0 | 0 | yes |
| `_clip_crescent` | character | 6749 | 473 | 0 / 0 | 39 | 39 | 0 | 0 | 0 | yes |
| `_clip_star` | character | 6762 | 55 | 0 / 0 | 28 | 28 | 0 | 0 | 0 | yes |
| `_hair_clip` | character | 6789 | 15176 | 0 / 0 | 10868 | 210 | 0 | 0 | 5 | yes |
| `_hair_knot` | character | 6806 | 15176 | 0 / 0 | 10868 | 205 | 0 | 0 | 0 | yes |
| `_robe_front` | character | 6842 | 15445 | 0 / 0 | 11087 | 212 | 0 | 0 | 0 | yes |
| `_hanging_sleeves` | character | 6894 | 15321 | 0 / 0 | 10976 | 209 | 0 | 0 | 1 | yes |
| `_coat` | character | 6941 | 15445 | 0 / 0 | 11087 | 214 | 0 | 0 | 1 | yes |
| `_mouth_depth_share` | character | 7039 | 109 | 0 / 0 | 41 | 41 | 0 | 0 | 0 | yes |
| `_beard` | character | 7190 | 15226 | 0 / 0 | 10918 | 209 | 0 | 0 | 1 | yes |
| `_glasses` | character | 7355 | 15176 | 0 / 0 | 10868 | 205 | 0 | 0 | 0 | yes |
| `_goggle_geometry` | character | 7431 | 1985 | 0 / 0 | 591 | 149 | 0 | 0 | 0 | yes |
| `_goggles_strap` | character | 7446 | 15176 | 0 / 0 | 10868 | 204 | 0 | 0 | 0 | yes |
| `_goggles` | character | 7487 | 15171 | 0 / 0 | 10863 | 219 | 0 | 0 | 15 | yes |
| `_mask` | character | 7545 | 15226 | 0 / 0 | 10918 | 208 | 0 | 0 | 0 | yes |
| `_blindfold` | character | 7601 | 15156 | 0 / 0 | 10848 | 204 | 0 | 0 | 0 | yes |
| `_mock_collar` | character | 7643 | 439 | 0 / 0 | 218 | 127 | 0 | 0 | 0 | yes |
| `_collar` | character | 7696 | 15240 | 0 / 0 | 10927 | 212 | 0 | 0 | 4 | yes |
| `_ribbon` | character | 7744 | 15226 | 0 / 0 | 10918 | 207 | 0 | 0 | 0 | yes |
| `_placket` | character | 7754 | 15445 | 0 / 0 | 11087 | 213 | 0 | 0 | 0 | yes |
| `_chest_pockets` | character | 7789 | 15445 | 0 / 0 | 11087 | 213 | 0 | 0 | 0 | yes |
| `_strap` | character | 7826 | 15445 | 0 / 0 | 11087 | 213 | 0 | 0 | 0 | yes |
| `_skirt_half_w` | character | 7859 | 82893 | 0 / 0 | 3816 | 97 | 0 | 0 | 0 | yes |
| `_skirt_hem_y` | character | 7869 | 19112 | 0 / 0 | 1559 | 101 | 0 | 0 | 1 | yes |
| `_skirt_corner_y` | character | 7911 | 14597 | 0 / 0 | 1656 | 95 | 0 | 0 | 0 | yes |
| `_skirt_path` | character | 7920 | 11838 | 0 / 0 | 2022 | 101 | 0 | 0 | 0 | yes |
| `_underskirt` | character | 7993 | 15322 | 0 / 0 | 10977 | 207 | 0 | 0 | 0 | yes |
| `_apron` | character | 8051 | 15445 | 0 / 0 | 11087 | 212 | 0 | 0 | 0 | yes |
| `_hakama` | character | 8100 | 15322 | 0 / 0 | 10977 | 209 | 0 | 0 | 1 | yes |
| `_skirt` | character | 8153 | 15322 | 0 / 0 | 10977 | 206 | 0 | 0 | 0 | yes |
| `_sleeve_placement` | character | 8265 | 10207 | 0 / 0 | 332 | 0 | 10207 | 0 | 0 | no |
| `_arm_line` | character | 8291 | 137108 | 0 / 0 | 1767 | 93 | 0 | 0 | 0 | yes |
| `_hand_length` | character | 8316 | 43623 | 0 / 0 | 1731 | 93 | 0 | 0 | 0 | yes |
| `_worn_sleeve` | character | 8323 | 179181 | 0 / 0 | 11077 | 212 | 0 | 0 | 0 | yes |
| `_arm_pivot` | character | 8327 | 4695 | 0 / 0 | 1569 | 154 | 0 | 0 | 0 | yes |
| `_hand_centre` | character | 8343 | 1027 | 0 / 0 | 613 | 152 | 0 | 0 | 0 | yes |
| `_staff_placement` | character | 8727 | 1027 | 0 / 0 | 613 | 0 | 1027 | 0 | 0 | no |
| `_staff` | character | 8778 | 15319 | 0 / 0 | 10974 | 208 | 0 | 0 | 0 | yes |
| `_katana_stretch_factor` | character | 9136 | 3365 | 0 / 0 | 78 | 78 | 0 | 0 | 1 | yes |
| `_katana_stretched` | character | 9144 | 3365 | 0 / 0 | 78 | 1 | 3364 | 0 | 1 | yes |
| `_katana_placement` | character | 9161 | 1683 | 0 / 0 | 415 | 1 | 1682 | 0 | 1 | yes |
| `_katana` | character | 9216 | 15320 | 0 / 0 | 10975 | 209 | 0 | 0 | 1 | yes |
| `_arms` | character | 9890 | 22039 | 0 / 0 | 15047 | 210 | 0 | 0 | 2 | yes |
| `_wristband` | character | 10136 | 44078 | 0 / 0 | 21948 | 212 | 0 | 0 | 2 | yes |
| `_shoulder_bars` | character | 10171 | 15317 | 0 / 0 | 10972 | 256 | 0 | 0 | 50 | yes |
| `_hands_after_coat` | character | 10223 | 38437 | 0 / 0 | 10995 | 208 | 0 | 0 | 0 | yes |
| `_raised_cuff` | character | 10231 | 309 | 0 / 0 | 117 | 81 | 0 | 0 | 0 | yes |
| `_arm_joint_cap` | character | 10267 | 949 | 0 / 0 | 113 | 84 | 0 | 0 | 0 | yes |
| `_cuff_line` | character | 10288 | 2688 | 0 / 0 | 360 | 91 | 0 | 0 | 0 | yes |
| `_wrist_cuff` | character | 10310 | 17390 | 0 / 0 | 1832 | 94 | 0 | 0 | 0 | yes |
| `_bspline_closed` | character | 10448 | 2 | 2 / 0 | 2 | 2 | 0 | 0 | 0 | yes |
| `_rounded_box` | character | 10459 | 2 | 2 / 0 | 2 | 2 | 0 | 0 | 0 | yes |
| `_fist` | character | 10475 | 1 | 1 / 0 | 1 | 1 | 0 | 0 | 0 | yes |
| `_chain_points` | character | 10529 | 5153 | 1 / 0 | 3 | 3 | 0 | 0 | 0 | yes |
| `_square_wrist` | character | 10540 | 1 | 1 / 0 | 1 | 1 | 0 | 0 | 0 | yes |
| `_grip_channel` | character | 10566 | 272 | 0 / 0 | 1 | 1 | 0 | 0 | 0 | yes |
| `_traced_wrist_half` | character | 10571 | 950 | 0 / 0 | 1 | 1 | 0 | 0 | 0 | yes |
| `_hand_pose` | character | 10577 | 128112 | 0 / 0 | 10974 | 199 | 0 | 0 | 0 | yes |
| `_fist_grips` | character | 10582 | 90763 | 0 / 0 | 21946 | 200 | 0 | 0 | 0 | yes |
| `_hand_traced` | character | 10592 | 86504 | 0 / 0 | 21946 | 200 | 0 | 0 | 0 | yes |
| `_principal` | character | 10598 | 8404 | 0 / 0 | 632 | 80 | 0 | 0 | 0 | yes |
| `_cuff_opening` | character | 10610 | 5570 | 0 / 0 | 1508 | 153 | 0 | 0 | 0 | yes |
| `_traced_placement` | character | 10642 | 1752 | 0 / 0 | 512 | 0 | 1752 | 0 | 0 | no |
| `_traced_hand` | character | 10680 | 1480 | 0 / 0 | 512 | 134 | 0 | 0 | 0 | yes |
| `_mitten_placement` | character | 10711 | 43623 | 0 / 0 | 21593 | 0 | 43623 | 0 | 0 | no |
| `_hand` | character | 10733 | 44076 | 0 / 0 | 21946 | 210 | 0 | 0 | 0 | yes |
| `_mitten_path` | character | 10769 | 41628 | 0 / 0 | 0 | 0 | 41628 | 0 | 0 | no |
| `_hand_shape` | character | 10782 | 2654 | 0 / 0 | 873 | 147 | 0 | 0 | 0 | yes |
| `_hand_stroke` | character | 10789 | 4234 | 0 / 0 | 778 | 82 | 0 | 0 | 0 | yes |
| `_hand_notched` | character | 10796 | 968 | 0 / 0 | 0 | 0 | 968 | 0 | 0 | no |
| `_hand_stroked` | character | 10818 | 824 | 0 / 0 | 0 | 0 | 824 | 0 | 0 | no |
| `_hand_curled` | character | 10831 | 862 | 0 / 0 | 0 | 0 | 862 | 0 | 0 | no |
| `_leg_gap_and_top` | character | 10861 | 36986 | 0 / 0 | 3622 | 98 | 0 | 0 | 0 | yes |
| `_limb_taper_at` | character | 10904 | 39844 | 0 / 0 | 179 | 82 | 0 | 0 | 0 | yes |
| `_limb_build` | character | 10909 | 60792 | 0 / 0 | 1762 | 92 | 0 | 0 | 0 | yes |
| `_legs_and_boots` | character | 10914 | 15346 | 0 / 0 | 11001 | 232 | 0 | 0 | 24 | yes |
| `_crotch_y` | character | 10994 | 23829 | 0 / 0 | 11001 | 208 | 0 | 0 | 0 | yes |
| `_leg_tuck_top_y` | character | 11010 | 15144 | 0 / 0 | 10800 | 208 | 0 | 0 | 0 | yes |
| `_seat_notch_d` | character | 11020 | 15346 | 0 / 0 | 1921 | 96 | 0 | 0 | 0 | yes |
| `_trousers` | character | 11109 | 6863 | 0 / 0 | 3964 | 199 | 0 | 0 | 14 | yes |
| `_skirt_bottom_y` | character | 11154 | 8483 | 0 / 0 | 7037 | 213 | 0 | 0 | 5 | yes |
| `_underpants` | character | 11167 | 8478 | 0 / 0 | 1117 | 98 | 0 | 0 | 0 | yes |
| `_knee_strength` | character | 11225 | 16840 | 0 / 0 | 863 | 91 | 0 | 0 | 0 | yes |
| `_bare_ankle` | character | 11230 | 8357 | 0 / 0 | 716 | 96 | 0 | 0 | 0 | yes |
| `_quad_u_at` | character | 11236 | 8248 | 0 / 0 | 247 | 84 | 0 | 0 | 0 | yes |
| `_knee_notch_d` | character | 11253 | 8248 | 0 / 0 | 757 | 99 | 0 | 0 | 0 | yes |
| `_bare_seat` | character | 11325 | 8483 | 0 / 0 | 7037 | 212 | 0 | 0 | 5 | yes |
| `_trouser_seams` | character | 11371 | 6863 | 0 / 0 | 3964 | 198 | 0 | 0 | 14 | yes |
| `_bare_foot` | character | 11406 | 352 | 0 / 0 | 350 | 106 | 0 | 0 | 0 | yes |
| `_boot` | character | 11457 | 30649 | 0 / 0 | 21959 | 215 | 0 | 0 | 5 | yes |
| `_belt_line_half_w` | character | 11585 | 6634 | 0 / 0 | 557 | 89 | 0 | 0 | 0 | yes |
| `_belt_band` | character | 11599 | 41404 | 0 / 0 | 3011 | 97 | 0 | 0 | 0 | yes |
| `_belt` | character | 11625 | 15445 | 0 / 0 | 11087 | 231 | 0 | 0 | 20 | yes |
| `_belt_drawn` | character | 11633 | 15427 | 0 / 0 | 11076 | 230 | 0 | 0 | 20 | yes |
| `_pouches` | character | 11818 | 15424 | 0 / 0 | 11066 | 212 | 0 | 0 | 0 | yes |
| `_crystal_layout` | character | 11873 | 2247 | 0 / 0 | 567 | 92 | 0 | 0 | 0 | yes |
| `_crystal_harness` | character | 11907 | 15424 | 0 / 0 | 11066 | 211 | 0 | 0 | 0 | yes |
| `_head_pt` | character | 12021 | 14837593 | 0 / 0 | 2250 | 82 | 0 | 0 | 0 | yes |
| `_head_edge_x` | character | 12043 | 135757 | 0 / 0 | 847 | 83 | 0 | 0 | 0 | yes |
| `_hair_edge_x` | character | 12063 | 4240 | 0 / 0 | 2468 | 164 | 0 | 0 | 0 | yes |
| `_jaw_track` | character | 12105 | 1288 | 0 / 0 | 23 | 23 | 0 | 0 | 0 | yes |
| `_face_track` | character | 12134 | 2576 | 0 / 0 | 14 | 14 | 0 | 0 | 0 | yes |
| `_head_shape` | character | 12172 | 29751 | 0 / 0 | 16 | 16 | 0 | 0 | 0 | yes |
| `_ear_span` | character | 12311 | 10530 | 0 / 0 | 9 | 9 | 0 | 0 | 0 | yes |
| `_ear_place` | character | 12319 | 10530 | 0 / 0 | 9 | 0 | 10530 | 0 | 0 | no |
| `_ear_outer` | character | 12340 | 5265 | 0 / 0 | 9 | 9 | 0 | 0 | 0 | yes |
| `_ears` | character | 12354 | 15226 | 0 / 0 | 10918 | 208 | 0 | 0 | 0 | yes |
| `_head_paths` | character | 12407 | 29462 | 0 / 0 | 1724 | 93 | 0 | 0 | 0 | yes |
| `_head` | character | 12422 | 15226 | 0 / 0 | 10918 | 208 | 0 | 0 | 0 | yes |
| `_eye_quads` | character | 12497 | 90304 | 0 / 0 | 2844 | 129 | 0 | 0 | 0 | yes |
| `_eye_shape` | character | 12529 | 30112 | 0 / 0 | 5688 | 131 | 0 | 0 | 0 | yes |
| `_lid_points` | character | 12570 | 60192 | 0 / 0 | 3376 | 86 | 0 | 0 | 0 | yes |
| `_eye_lash` | character | 12579 | 30096 | 0 / 0 | 2844 | 128 | 0 | 0 | 0 | yes |
| `_eye` | character | 12626 | 30112 | 0 / 0 | 6510 | 148 | 0 | 0 | 16 | yes |
| `_eye_closed` | character | 12779 | 290 | 0 / 0 | 212 | 103 | 0 | 0 | 0 | yes |
| `_scar` | character | 12799 | 1546 | 0 / 0 | 305 | 89 | 0 | 0 | 0 | yes |
| `aged_face` | character | 12816 | 13626 | 0 / 0 | 841 | 121 | 0 | 0 | 0 | yes |
| `_eye_placement` | character | 12842 | 64378 | 0 / 0 | 10917 | 208 | 0 | 0 | 0 | yes |
| `_blush` | character | 12985 | 22258 | 0 / 0 | 315 | 94 | 0 | 0 | 16 | yes |
| `_eye_build` | character | 13012 | 337115 | 0 / 0 | 1724 | 93 | 0 | 0 | 0 | yes |
| `_nose_y` | character | 13030 | 16235 | 0 / 0 | 1583 | 93 | 0 | 0 | 0 | yes |
| `_nose_dot` | character | 13036 | 626 | 0 / 0 | 134 | 86 | 0 | 0 | 0 | yes |
| `_nose` | character | 13044 | 14321 | 0 / 0 | 1471 | 94 | 0 | 0 | 0 | yes |
| `_brow` | character | 13065 | 30418 | 0 / 0 | 21802 | 224 | 0 | 0 | 16 | yes |
| `_brows_over_hair` | character | 13087 | 15176 | 0 / 0 | 10868 | 205 | 0 | 0 | 0 | yes |
| `_face` | character | 13094 | 15225 | 0 / 0 | 10917 | 253 | 0 | 0 | 49 | yes |
| `_soft_brow_shadow` | character | 13203 | 3115 | 0 / 0 | 2659 | 190 | 0 | 0 | 0 | yes |
| `_lock_line` | character | 13236 | 53348 | 0 / 0 | 634 | 90 | 0 | 0 | 0 | yes |
| `_lock_normals` | character | 13267 | 53348 | 0 / 0 | 634 | 84 | 0 | 0 | 0 | yes |
| `_lock_side` | character | 13278 | 53348 | 0 / 0 | 634 | 102 | 0 | 0 | 0 | yes |
| `_smooth_path` | character | 13285 | 106696 | 0 / 0 | 5736 | 95 | 0 | 0 | 0 | yes |
| `_lock_shape` | character | 13297 | 53348 | 0 / 0 | 2868 | 94 | 0 | 0 | 0 | yes |
| `_soft_locks` | character | 13338 | 3394 | 0 / 0 | 891 | 101 | 0 | 0 | 0 | yes |
| `_soft_lock_layers` | character | 13385 | 3134 | 0 / 0 | 2673 | 183 | 0 | 0 | 0 | yes |
| `_hair_front` | character | 13417 | 15176 | 0 / 0 | 10868 | 204 | 0 | 0 | 0 | yes |
| `_mirrored_y` | character | 13525 | 460 | 0 / 0 | 1 | 1 | 0 | 0 | 0 | yes |
| `_familiar` | character | 13929 | 15156 | 0 / 0 | 10848 | 204 | 0 | 0 | 0 | yes |
| `_namespace_ids` | character | 14017 | 3824 | 0 / 0 | 2745 | 81 | 0 | 1 | 0 | yes |
| `render_character` | character | 14028 | 15554 | 0 / 0 | 15072 | 590 | 0 | 0 | 398 | yes |
| `hex_to_rgb01` | colorutil | 10 | 454682 | 0 / 0 | 7057 | 96 | 0 | 0 | 16 | yes |
| `rgb01_to_hex` | colorutil | 16 | 424252 | 0 / 0 | 12322 | 86 | 0 | 0 | 0 | yes |
| `shade` | colorutil | 21 | 395019 | 0 / 0 | 10978 | 145 | 0 | 0 | 61 | yes |
| `tint` | colorutil | 30 | 18438 | 0 / 0 | 492 | 80 | 0 | 0 | 0 | yes |
| `lit_tone` | colorutil | 37 | 6788 | 0 / 0 | 504 | 82 | 0 | 0 | 0 | yes |
| `highlight_rise` | colorutil | 54 | 3394 | 0 / 0 | 225 | 80 | 0 | 0 | 0 | yes |
| `soft_shadow_tone` | colorutil | 60 | 3394 | 0 / 0 | 252 | 82 | 0 | 0 | 0 | yes |
| `_before` | presets | 215 | 2 | 2 / 0 | 2 | 2 | 0 | 0 | 0 | yes |
| `skeleton._lerp` | skeleton | 31 | 2216102 | 0 / 0 | 3031 | 82 | 0 | 0 | 0 | yes |
| `Skeleton.face_build` | skeleton | 93 | 512955 | 0 / 0 | 1731 | 93 | 0 | 0 | 0 | yes |
| `Skeleton.armpit_y` | skeleton | 102 | 1537728 | 0 / 0 | 1779 | 93 | 0 | 0 | 0 | yes |
| `Skeleton.bust_y` | skeleton | 109 | 245039 | 0 / 0 | 1018 | 95 | 0 | 0 | 0 | yes |
| `Skeleton.bust_reach` | skeleton | 116 | 877378 | 0 / 0 | 1776 | 95 | 0 | 0 | 4 | yes |
| `BodyProfile.head_scaled` | skeleton | 170 | 2 | 2 / 0 | 2 | 2 | 0 | 0 | 0 | yes |
| `BodyProfile.applied` | skeleton | 208 | 39860 | 0 / 0 | 693 | 88 | 0 | 0 | 0 | yes |
| `stretched` | skeleton | 260 | 1466 | 0 / 0 | 0 | 0 | 1466 | 0 | 0 | no |
| `default_hair_margin` | skeleton | 310 | 121054 | 0 / 0 | 244 | 83 | 0 | 0 | 0 | yes |
| `build_skeleton` | skeleton | 359 | 81186 | 0 / 0 | 2006 | 98 | 0 | 0 | 4 | yes |
| `params_to_dict` | urlstate | 34 | 46576 | 0 / 0 | 11183 | 207 | 0 | 0 | 0 | yes |
| `params_from_dict` | urlstate | 41 | 31079 | 0 / 0 | 22340 | 252 | 0 | 0 | 77 | yes |
| `encode_params` | urlstate | 81 | 31096 | 0 / 0 | 11183 | 208 | 0 | 0 | 0 | yes |
| `decode_params` | urlstate | 92 | 15583 | 0 / 0 | 11209 | 158 | 0 | 0 | 78 | yes |
| `character_url` | urlstate | 111 | 15542 | 0 / 0 | 11180 | 208 | 0 | 0 | 0 | yes |
<!-- END:functions -->

### Never called by the corpus

<!-- BEGIN:uncalled -->
- `presets.aged` (line 307), `(face: 'FaceStyle', years: 'float' = 1.0) -> 'FaceStyle'`
<!-- END:uncalled -->

### Unrecordable calls (a function as an argument or as the result)

Every other call of these functions that was recordable is in `out/calls`.

<!-- BEGIN:unrecordable -->
| function | unrecordable calls | total calls | reasons |
|---|---:|---:|---|
| `_fall_q` | 46551 | 46585 | callable result (function) x46551 |
| `_parted_q` | 21923 | 21941 | callable result (function) x21923 |
| `_garment_placement` | 20715 | 20715 | callable result (function) x20715 |
| `_draw_cut` | 3222 | 10622 | callable argument (function) x3222 |
| `_leg_placement` | 3670 | 3670 | callable result (function) x3670 |
| `_sleeve_placement` | 10207 | 10207 | callable result (function) x10207 |
| `_staff_placement` | 1027 | 1027 | callable result (function) x1027 |
| `_katana_stretched` | 3364 | 3365 | callable result (function) x3364 |
| `_katana_placement` | 1682 | 1683 | callable result (function) x1682 |
| `_traced_placement` | 1752 | 1752 | callable result (function) x1752 |
| `_mitten_placement` | 43623 | 43623 | callable result (function) x43623 |
| `_mitten_path` | 41628 | 41628 | callable argument (function) x41628 |
| `_hand_notched` | 968 | 968 | callable argument (function) x968 |
| `_hand_stroked` | 824 | 824 | callable argument (function) x824 |
| `_hand_curled` | 862 | 862 | callable argument (function) x862 |
| `_ear_place` | 10530 | 10530 | callable result (function) x10530 |
| `stretched` | 1466 | 1466 | callable argument (function) x1466 |
<!-- END:unrecordable -->

### Called, but no call kept

<!-- BEGIN:nokept -->
- `_garment_placement`: 20715 calls, 20715 unrecordable, 0 skipped as large
- `_leg_placement`: 3670 calls, 3670 unrecordable, 0 skipped as large
- `_sleeve_placement`: 10207 calls, 10207 unrecordable, 0 skipped as large
- `_staff_placement`: 1027 calls, 1027 unrecordable, 0 skipped as large
- `_traced_placement`: 1752 calls, 1752 unrecordable, 0 skipped as large
- `_mitten_placement`: 43623 calls, 43623 unrecordable, 0 skipped as large
- `_mitten_path`: 41628 calls, 41628 unrecordable, 0 skipped as large
- `_hand_notched`: 968 calls, 968 unrecordable, 0 skipped as large
- `_hand_stroked`: 824 calls, 824 unrecordable, 0 skipped as large
- `_hand_curled`: 862 calls, 862 unrecordable, 0 skipped as large
- `_ear_place`: 10530 calls, 10530 unrecordable, 0 skipped as large
- `stretched`: 1466 calls, 1466 unrecordable, 0 skipped as large
<!-- END:nokept -->

### Functions that changed an argument

<!-- BEGIN:mutating -->
- none
<!-- END:mutating -->

## Registry refs found

<!-- BEGIN:registry -->
| ref name | module | kind | level |
|---|---|---|---:|
| `BASE_FEMALE` | presets | CharacterParams | 0 |
| `BASE_MALE` | presets | CharacterParams | 0 |
| `BELT_CUTS` | character | dict | 0 |
| `BELT_CUTS.buckled` | character | BeltCut | 1 |
| `BODY_TYPES` | character | dict | 0 |
| `BODY_TYPES.tall_chibi` | character | BodyProfile | 1 |
| `BODY_TYPES.tall_chibi_long_torso` | character | BodyProfile | 1 |
| `BODY_TYPES.tall_slender` | character | BodyProfile | 1 |
| `BOOT_CUTS` | character | dict | 0 |
| `BOOT_CUTS.loafer` | character | GarmentCut | 1 |
| `BUILDS` | character | dict | 0 |
| `CHIYO` | presets | CharacterParams | 0 |
| `COAT_CUTS` | character | dict | 0 |
| `COAT_CUTS.blazer` | character | GarmentCut | 1 |
| `COAT_CUTS.lab_coat` | character | GarmentCut | 1 |
| `COAT_CUTS.open_jacket` | character | GarmentCut | 1 |
| `COLLAR_CUTS` | character | dict | 0 |
| `COLLAR_CUTS.pointed` | character | GarmentCut | 1 |
| `COLLAR_CUTS.shirt` | character | GarmentCut | 1 |
| `CRYSTAL_KIT` | presets | tuple | 0 |
| `DAIZEN` | presets | CharacterParams | 0 |
| `DISPLAY_NAMES` | presets | dict | 0 |
| `DRITAN` | presets | CharacterParams | 0 |
| `ELARA` | presets | CharacterParams | 0 |
| `EXPRESSIONS` | presets | dict | 0 |
| `EXPRESSIONS.alert` | presets | Expression | 1 |
| `EXPRESSIONS.at_ease` | presets | Expression | 1 |
| `EXPRESSIONS.exasperated` | presets | Expression | 1 |
| `EXPRESSIONS.grim` | presets | Expression | 1 |
| `EXPRESSIONS.hollow` | presets | Expression | 1 |
| `EXPRESSIONS.menacing` | presets | Expression | 1 |
| `EXPRESSIONS.resolute` | presets | Expression | 1 |
| `EXPRESSIONS.smile` | presets | Expression | 1 |
| `EXPRESSIONS.sorrow` | presets | Expression | 1 |
| `EXPRESSIONS.startled` | presets | Expression | 1 |
| `EXPRESSIONS.stern` | presets | Expression | 1 |
| `EXPRESSIONS.unyielding` | presets | Expression | 1 |
| `EXPRESSIONS.wry` | presets | Expression | 1 |
| `FINISHES` | character | tuple | 0 |
| `GERO` | presets | CharacterParams | 0 |
| `GRIP_STYLES` | character | tuple | 0 |
| `HAIRSTYLES` | character | dict | 0 |
| `HAIRSTYLES.long_blunt` | character | Hairstyle | 1 |
| `HAIRSTYLES.long_center_part` | character | Hairstyle | 1 |
| `HAIRSTYLES.long_fringed` | character | Hairstyle | 1 |
| `HAIRSTYLES.long_parted` | character | Hairstyle | 1 |
| `HAIRSTYLES.long_traced` | character | Hairstyle | 1 |
| `HAIRSTYLES.short_crop` | character | Hairstyle | 1 |
| `HAIRSTYLES.short_layered` | character | Hairstyle | 1 |
| `HAIRSTYLES.short_tousled` | character | Hairstyle | 1 |
| `HAIR_CLIPS` | character | dict | 0 |
| `HAIR_CLIPS.bar` | character | tuple | 1 |
| `HAIR_CLIPS.crescent` | character | tuple | 1 |
| `HAIR_CLIPS.crossed` | character | tuple | 1 |
| `HAIR_CLIPS.snap` | character | tuple | 1 |
| `HAIR_CLIPS.star` | character | tuple | 1 |
| `HAND_STYLES` | character | tuple | 0 |
| `HARUTO` | presets | CharacterParams | 0 |
| `HIP_POCKET_CUT` | character | GarmentCut | 0 |
| `KATHERINA` | presets | CharacterParams | 0 |
| `KEIKO` | presets | CharacterParams | 0 |
| `KNEE_SOCK_CUT` | character | GarmentCut | 0 |
| `KRISTA` | presets | CharacterParams | 0 |
| `KYOKO` | presets | CharacterParams | 0 |
| `LINDITA` | presets | CharacterParams | 0 |
| `LINNEA` | presets | CharacterParams | 0 |
| `NEUTRAL_BASES` | presets | dict | 0 |
| `PRESETS` | presets | dict | 0 |
| `REIKA` | presets | CharacterParams | 0 |
| `REINHARD` | presets | CharacterParams | 0 |
| `RIBBON_CUT` | character | GarmentCut | 0 |
| `RISA` | presets | CharacterParams | 0 |
| `ROSTERS` | presets | dict | 0 |
| `ROSTERS.bureaucracy` | presets | tuple | 1 |
| `ROSTERS.cast` | presets | tuple | 1 |
| `ROSTERS.everglow` | presets | tuple | 1 |
| `ROSTERS.katherina` | presets | tuple | 1 |
| `ROSTERS.risa` | presets | tuple | 1 |
| `ROSTERS.satoshi` | presets | tuple | 1 |
| `SATOKO` | presets | CharacterParams | 0 |
| `SATOSHI` | presets | CharacterParams | 0 |
| `SKIRT_CUTS` | character | dict | 0 |
| `SKIRT_CUTS.a_line` | character | GarmentCut | 1 |
| `SKIRT_CUTS.column` | character | GarmentCut | 1 |
| `SKIRT_CUTS.pleated` | character | GarmentCut | 1 |
| `SLEEVE_CUTS` | character | dict | 0 |
| `SLEEVE_CUTS.wide` | character | SleeveCut | 1 |
| `TENNO` | presets | CharacterParams | 0 |
| `TOMOHIRO` | presets | CharacterParams | 0 |
| `VIKTOR` | presets | CharacterParams | 0 |
| `_BUST_KNOTS` | character | tuple | 0 |
| `_BUST_REACH` | skeleton | tuple | 0 |
| `_COAT_BUTTONS` | character | tuple | 0 |
| `_CROP_EDGE` | character | list | 0 |
| `_CROP_FRINGE` | character | list | 0 |
| `_CROP_FRINGE_START` | character | tuple | 0 |
| `_CROP_LOCKS` | character | list | 0 |
| `_CROP_NOTCHES` | character | list | 0 |
| `_CROP_REAL_EAR_X` | character | tuple | 0 |
| `_CROP_REAL_EDGE` | character | list | 0 |
| `_CROP_REAL_START` | character | tuple | 0 |
| `_CROP_START` | character | tuple | 0 |
| `_CRYSTAL_X_FRACS` | character | tuple | 0 |
| `_EAR_ARC` | character | list | 0 |
| `_EAR_ARC_START` | character | tuple | 0 |
| `_EAR_FOLD` | character | list | 0 |
| `_EAR_FOLD_START` | character | tuple | 0 |
| `_FRINGED_FRONT` | character | tuple | 0 |
| `_FRINGED_LOCKS` | character | list | 0 |
| `_FRINGED_MASS` | character | tuple | 0 |
| `_FRINGED_OPENINGS` | character | list | 0 |
| `_FRINGED_SHADE` | character | list | 0 |
| `_FRINGED_STRANDS` | character | list | 0 |
| `_FRINGED_UNDERSIDE` | character | tuple | 0 |
| `_HAIR_CLIP_AT` | character | tuple | 0 |
| `_HAND_BUILDERS` | character | dict | 0 |
| `_HAND_FIST` | character | tuple | 0 |
| `_HAND_FIST_CHANNEL` | character | tuple | 0 |
| `_HAND_FIST_INTO` | character | tuple | 0 |
| `_HAND_OPEN` | character | tuple | 0 |
| `_HAND_RELAXED` | character | tuple | 0 |
| `_HAND_RELAXED_INTO` | character | tuple | 0 |
| `_HAT_BAND` | character | tuple | 0 |
| `_HAT_BRIM` | character | tuple | 0 |
| `_HAT_BUCKLE` | character | list | 0 |
| `_HAT_CREASES` | character | list | 0 |
| `_HAT_CROWN` | character | tuple | 0 |
| `_HAT_UNDERSIDE` | character | tuple | 0 |
| `_KATANA_DIAMONDS` | character | list | 0 |
| `_KATANA_FUCHI` | character | tuple | 0 |
| `_KATANA_KASHIRA` | character | tuple | 0 |
| `_KATANA_KOJIRI` | character | tuple | 0 |
| `_KATANA_RING_BROWN` | character | tuple | 0 |
| `_KATANA_RING_DARK` | character | tuple | 0 |
| `_KATANA_SAYA` | character | tuple | 0 |
| `_KATANA_TSUBA` | character | tuple | 0 |
| `_KATANA_TSUKA` | character | tuple | 0 |
| `_KEEP_WS` | skeleton | tuple | 0 |
| `_KEEP_YS` | skeleton | tuple | 0 |
| `_KOU_BODY` | character | tuple | 0 |
| `_KOU_CENTRE_CHIBI` | character | tuple | 0 |
| `_KOU_CENTRE_REAL` | character | tuple | 0 |
| `_KOU_EYES` | character | list | 0 |
| `_KOU_LINES` | character | list | 0 |
| `_KOU_WINGS` | character | list | 0 |
| `_KOU_WING_CELLS` | character | list | 0 |
| `_LAB_COAT_LAPEL_LEFT` | character | tuple | 0 |
| `_LAB_COAT_LAPEL_RIGHT` | character | tuple | 0 |
| `_LAB_COAT_PANEL_LEFT` | character | tuple | 0 |
| `_LAB_COAT_PANEL_RIGHT` | character | tuple | 0 |
| `_LAB_DRESS_COLUMN` | character | tuple | 0 |
| `_LONG_EDGE` | character | list | 0 |
| `_LONG_EDGE_START` | character | tuple | 0 |
| `_LONG_LINE` | character | list | 0 |
| `_LONG_LINE_START` | character | tuple | 0 |
| `_LONG_LOCKS` | character | list | 0 |
| `_PARTED_EDGE` | character | tuple | 0 |
| `_PARTED_LINE` | character | tuple | 0 |
| `_PARTED_LOCKS` | character | list | 0 |
| `_PARTED_LOCK_L` | character | tuple | 0 |
| `_PARTED_LOCK_R` | character | tuple | 0 |
| `_PARTED_TIPS_BEHIND` | character | list | 0 |
| `_PARTED_TIPS_FRONT` | character | list | 0 |
| `_PARTED_UNDER_L` | character | tuple | 0 |
| `_PARTED_UNDER_R` | character | tuple | 0 |
| `_SHORT_LOCKS` | character | list | 0 |
| `_SOFT_LOCK_LIGHT` | character | tuple | 0 |
| `_STAFF_CRYSTAL` | character | tuple | 0 |
| `_STAFF_FACETS_DARK` | character | list | 0 |
| `_STAFF_FACETS_LIGHT` | character | list | 0 |
| `_STAFF_GRIP` | character | tuple | 0 |
| `_STAFF_STRANDS` | character | list | 0 |
| `_STAFF_TIP` | character | tuple | 0 |
| `_STAFF_WOOD` | character | tuple | 0 |
| `_STRETCH_YS` | skeleton | tuple | 0 |
| `_TOUSLE_CROWN` | character | list | 0 |
| `_TOUSLE_NOTCHES` | character | list | 0 |
| `_TOUSLE_TEMPLE` | character | tuple | 0 |
| `_TOUSLE_TIPS` | character | list | 0 |
<!-- END:registry -->

## Not done

- Closures: a function that returns a transform (`_fall_q`, `_parted_q`, `_garment_placement`,
  `_leg_placement`, `_sleeve_placement`, `_staff_placement`, `_traced_placement`, `_mitten_placement`,
  `_katana_stretched`, `_katana_placement`, `_ear_place`) or takes one (`_mitten_path`, `_hand_notched`,
  `_hand_stroked`, `_hand_curled`, `stretched`, `_draw_cut` with `xf`) has no recorded call. They are
  covered only by the stages of the parts that use them. A follow-up that records the composition
  (factory arguments, then the arguments and result of one call of the returned function) would close
  this; it was not done because the brief says to mark such calls unrecordable and not to guess.
- Calls larger than 200 KB (`_soft_stroke_widths` and `_namespace_ids` for the largest corpus cases).
- Corpora other than `mini`, `wide` and `full`; `catalogue.py`, `attribution.py` and the comic, cover and
  sheet modules are outside the oracle.
