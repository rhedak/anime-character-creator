# Porting the drawing core to TypeScript: plan

Status: DRAFT 2 for the owner, 2026-10-16, after two independent reviews (section 10). Nothing here is decided or
started. The owner chose "option 2" in conversation: the port replaces Python as the source of truth after
cutover, it covers only the code that draws characters, and the harness is not ported.

Marks: **(verified)** means read or run on 2026-10-16, by me or by a reviewer, with the place named.
**(inferred)** means reasoned, not run, and is a thing to test. Numbers from the cold-audit reviewer were
measured in its scratch copy of the package, not durably kept; Phase 0 rebuilds that tooling in the repo so the
numbers can be reproduced.

## 1. Why, and what "done" means

The owner's reasons: the web tool and the companion demo run Python in the browser (Pyodide), and a Windows or
Android release would have to bundle Python. (The repos do not mention Windows or Android anywhere; those are the
owner's stated direction, not a documented plan. Pyodide's cost is quoted at 5.5 MB, 6.5 MB with the demo, and
about 10 MB in three places in the companion's docs, so the spike measures it.) The companion also needs Python
3.11+ beside Node: `README.md`, `check.sh`, `src/doctor.ts`.

Done means:

1. A TypeScript package draws every character the Python package draws, with byte-identical SVG for the same
   input, on the corpus, within the policy of section 4.
2. The web tool, the companion server, the companion demo and a node CLI all run it, with no Python on any
   shipped path. Python stays as dev tooling only where it is irreplaceable (PNG with cairosvg, PIL pack tools).
3. TypeScript is the source of truth. The Python package is frozen at a tag and is only a reference.

## 2. Scope

Port (line counts verified):

| Python | Lines | Becomes |
| --- | --- | --- |
| `character.py` | 14,265 | the drawing: 303 module-level functions, 9 classes, 264 annotated fields (175 in classes, 89 module level), about 8,000 lines of actual code |
| `presets.py` | 1,547 | 20 characters, 13 expressions, 6 rosters, 2 neutral bases |
| `skeleton.py` | 455 | proportion anchors (but `skeleton_for` and `BODY_TYPES` live in `character.py`) |
| `colorutil.py` | 70 | colour maths, with `colorsys` re-implemented |
| `urlstate.py` | 114 | state to and from a URL |
| `supporting.py` | 135 | supporting cast |
| `catalogue.py` | 802 | the JSON that drives the web controls |
| `attribution.py` (metadata block only) | about 50 of 126 | the `<metadata>` block, which embeds a URL |
| companion `python/render_ops.py` | 223 | the request handling the server and demo share |

Not ported: `harness/`, the pair-judging tools, mock-ups, the `comic/` package (990 lines; D6), PNG export and
the PNG text-chunk helpers in `attribution.py` (zlib, struct), and the companion's offline pack tools
`finish_pack.py` and `make_sample_pack.py` (PIL, numpy, cairosvg; they will read SVG from the node CLI).

Undecided, and the owner's to answer: `generate.py` (211), `cover.py` (430), `sheet.py` (308), about 950 lines
in all. `CLAUDE.md` says a sibling project consumes this repo's output through `render.sh`, `cover.sh` and
`sheet.sh` (there is also `sheet_satoshi.sh`), details in an untracked `local/` folder. **`local/` does not exist
in either checkout on this machine** (verified), so D5 cannot be answered from here. `cover.py` reads
`local/cover_faces.json` and honours `ACC_LOCAL_DIR`, which `refresh-ref-out.sh` sets to `/nonexistent`; a port
must keep that hook.

## 3. What the code looks like (verified)

* `render_character` (`character.py:14028-14265`) builds a `layers` list of about 53 part expressions, joined
  with `"\n  "`, then runs `_soft_stroke_widths`, `_namespace_ids` and the document wrapper. **The parts are not
  uniform `(sk, p) -> str` calls.** `_hair_lines(svg, p)` wraps a part's output; `_without_raised_sleeves(layer,
  p)` wraps `_torso`; `_bust_over_arms(sk, p, chest)` takes the concatenated output of about 14 garment parts;
  `_arms` and `_traced_coat_and_belt` are each called twice with different arguments; `_belt` and `_collar` are
  conditional and can appear twice; `_hands_after_coat` returns a flag. `_belt` and `_traced_coat_and_belt`
  (garments) call `_hands_after_coat` (arms), and `_bust_over_arms` calls `_arms`, so garments and arms cannot be
  ported and gated as two separate steps.
* `_soft_stroke_widths` (`:118-128`) re-parses every `stroke-width` in the joined body and reprints it with a
  second rounding (`:.2f`). So a part's own output is not a slice of the final document; the post-steps can only be
  compared on the whole body.
* Numbers reach the output through fixed-precision f-strings: `:.1f` 952, `:.2f` 190, `:.0f` 10, `:.3f` 1, plus
  `02x` in `colorutil`. **Exceptions:** `:13361` prints `opacity="{opacity}"` where `opacity` is
  `round(_SOFT_LOCK_SEP_OPACITY * gain, 3)` (a Python float repr), `:13209` prints the constant 0.55, and `:6733`
  prints `rotate({a})` for ints.
* No `random`, no `functools`, no `@property`, no mutable default arguments, no mutation of module state, no set
  iteration whose order reaches the output (sets are sorted or used for membership), no `//` or `divmod`. All
  dataclasses are frozen. `hashlib.sha1` is used four times for ids (`:4225`, `:4252`, `:4258`, `:5565`).
* Runtime reflection exists in `catalogue.py` (`dataclasses.fields`), `urlstate`, `skeleton` (`getattr`),
  `character` (`asdict` in `Expression`), and in the companion's `render_ops.coerce`, which reads annotation
  strings such as `"int | None"`. TypeScript has no runtime types, so a **field registry** (name, type tag,
  default, allowed values) is needed as data. It is the one new design element.
* The companion already runs TypeScript with no build step: `MIN_NODE = "22.18.0"` (`bin/check-node.js`), Node
  here is v22.22.3. `module.stripTypeScriptTypes` exists in 22.22.3 (experimental). **But it keeps `"./b.ts"`
  import specifiers** (a reviewer ran it), and static hosts commonly serve `.ts` as `video/mp2t`, which a
  browser refuses as a module (inferred for Pages). So the browser copy needs specifier rewriting or `tsc` with
  `rewriteRelativeImportExtensions`, not just a type strip.
* The creator has no JavaScript toolchain: `web/` is plain classic-script JS (`app.js` 922 lines, loaded by
  `<script src>` at `web/index.html:126-127`), staged by `web-stage.sh`, deployed by the only workflow,
  `.github/workflows/pages.yml` (push to `main` and `workflow_dispatch`; it runs `uv sync`, pytest and the
  refresh checks on ubuntu).
* Tests: 288 test functions in 14 files (35 are `test_comic_*`, outside scope). `test_smoke.py` is 3,256 lines and
  calls private `_names` about 330 times. **No test rasterises** (`cairosvg` appears once, in a comment at
  `test_soft_finish.py:54`); raster checks live in `harness/` and in `refresh-ref-out.sh --pixels`
  (`compare_pixels.py`). Tests that call internals (for example `test_the_front_hair_adds_no_silhouette`,
  `test_smoke.py:378`, which calls `_hair_mass` and `_hair_front`) are tied to functions, not to output.
* `__version__` in `__init__.py:60` says 0.2.3; `pyproject.toml` says 0.3.0; nothing reads `__version__`. Not touched.

## 4. The contract, stated so it can fail

1. **Drawing.** For every case in the corpus, `renderCharacter` returns the Python reference's string byte for
   byte, and every stage hash matches (section 5.1).
2. **State.** Every URL the Python encoder makes decodes to the same params in TS. TS encoder output must also
   match Python's bytes, because `metadata=True` embeds `character_url(p)` in the SVG (`attribution.py:58`) and
   the web tool turns metadata on, so it is part of the corpus. That needs a Python-compatible JSON writer in
   the kernel: `sort_keys`, `separators=(",",":")`, `ensure_ascii`, and Python float spelling (`1.0`, `1e-05`,
   `-0.0`). Whole-valued floats are common (507 in the 22 bases' JSON, 34 in the catalogue), and JS cannot tell
   an int field from a float field by value, so the registry's type tags decide the spelling.
3. **Catalogue.** The TS catalogue equals `ref-out/catalogue.json` byte for byte (same JSON writer).
4. **Errors.** Python raises where JS yields `NaN`, `undefined` or silently accepts. The corpus includes inputs
   that must raise, and the port must raise at the same places, with the same error class and, where a consumer
   shows it, the same text. Known sites: `sqrt` of a negative (reached: 18 renders raise at `:1953` when
   `hair_length` is below 0; 7 of 300 random float combinations raised `math domain error` in the companion's
   range), `acos` (`:824`, `:9205`), `zip(strict=True)` x6, `next()` (`:10549`, `:12119`), `int(hex, 16)`, a float
   used as `range()` or an index (`shoulder_bars`), and `validate_finish` (`:94-99`), whose chained comparison
   `0.0 <= strength <= 2.0` becomes `(0 <= s) <= 2` in JS and accepts everything (TypeScript's type checker
   rejects boolean-to-number comparison, which is a useful tripwire). The companion's `op_patch` depends on
   `trial_render` raising to reject a bad change. The port uses explicit domain checks (`pySqrt`, `pyAcos`
   throw), not a NaN scan after the fact.
5. **Behaviour tests** that matter (ids unique, silhouette escape, flat stays flat, byte budget, validation) pass
   on TS output.

**Maths-library policy, decided now.** CPython calls the platform libm; V8 uses its own fdlibm-derived code.
Measured by the reviewer on 2026-10-16, replaying real Apple-libm results from the corpus in Node: `Math.pow`
differs on 0.19% of distinct inputs, `sin` 2.9%, `cos` 2.2%, `acos` 4.7%, `atan2` 22.4%, `Math.hypot` 35.5%
(`sqrt(x*x+y*y)` 15,180 of 91,618), `x*x` against Python's `x**2` 0.14% (201 of 144,323), `x*Math.PI/180` against
`math.radians` 38 of 187 (use `x*(Math.PI/180)`, which matched). Yet **0 of 5,560 renders changed**, so ulp
differences rarely reach a printed digit; the same replay also showed naive summation differing on 2,348 of 3,050
sums with 0 renders changed. Therefore:

* Port exactly what is exactly portable: CPython's `hypot` is its own algorithm, not libm, so `pyHypot` copies it;
  `sum` copies CPython 3.12's compensated algorithm; `radians` is `x*(π/180)`; `**` with integer exponents is
  reproduced by whatever matches in testing.
* `sin`, `cos`, `atan2`, `acos`, fractional `pow` come from the engine. Fdlibm is **not** a remedy: porting it
  reproduces V8, not Apple libm or glibc. The pre-registered rule: a mismatch traced to a maths-library ulp is
  recorded in `known-ulp-flips.json` with its case, the first differing offset and a check that the cairosvg
  rasters of both SVGs are pixel-identical; the owner signs the list. The contract is "identical except the
  listed flips".
* The reference itself depends on the platform libm (on this macOS machine `x**2` differs from `x*x` in 201 of
  144,323 cases), so goldens made here could differ from Linux CI at the same level. CI already runs the
  `ref-out` comparison on ubuntu (`pages.yml`), which is real evidence about Python's own reproducibility; I could
  not read its history (GitHub's API is blocked from this sandbox), so it is **unchecked**. Phase 0 reads it, and
  regenerates the manifest on a second platform before Gate 2.
* Firefox and Safari use other libms. A cross-engine page the owner opens in each (Phase 1) measures it. The
  contract is stated against Node/V8; other engines are reported, not promised.

## 5. Strategy

### 5.1 The oracle

Pinned to the **immutable tag `v0.3.0`** (verified: tag equals the dev worktree's HEAD), so building it needs no
freeze. CPython 3.13.11 here; CPython 3.12+ semantics required (`sum`); the repo declares `>=3.11`, which means
Python itself is not self-consistent on 3.11 (inferred; checked in Phase 2).

* **Stages, not parts.** An AST-rewritten copy of `render_character` (scratch, never edits the source; a reviewer
  built one whose output hashed identically to the original) records, per case: each element of `layers`,
  `chest` and `under_arms` by index and source text; the joined body; the body after `_soft_stroke_widths`; after
  `_namespace_ids`; the final document. TS must produce each stage. The post-steps are also tested as functions on
  recorded input strings. This replaces my earlier "call each part by name" idea, which does not work (section 3).
* **Record and replay.** The same instrumented copy records every format, `**`, `%`, `round`, `sum`, `min/max` and
  `math.*` call with its real inputs and result. The kernel is tested twice: on synthetic adversarial values
  (ties such as 0.25 and 2.5, `-0.0`, nan, inf, values at or above 1e21, tiny values) and on the recorded real
  inputs. The reviewer replayed 2,200,250 distinct `.Nf` pairs and found 0 mismatches against `toFixed`, so
  formatting is **not** the main risk; the main risks are below.
* **Cases are data.** Python's `random` cannot be reproduced in JS, so the manifest ships each case's input as
  JSON, not a recipe, and the TS side never regenerates cases from its own catalogue (a catalogue port error would
  silently shift the corpus).
* **Corpus built from the dataclass fields, not the catalogue.** The catalogue is the web-exposed middle tier; the
  reviewer's catalogue-driven corpus never ran `_eye_closed` (needs `eyes_closed`), `_bare_foot` (boots off) or
  `_straight`, and ran `_underwear_top` only partly. Cases: every preset, neutral base and roster member in flat
  and soft; every field value one at a time, including fields the tool never exposes (`scar_side`, `frame`,
  `hair_tip_color`); `highlight_strength` sweeps including tiny and out-of-range values; seeded random combinations
  from field ranges **and** from beyond them (the companion accepts floats to plus or minus 20); skeleton sweeps;
  render options with odd `id_prefix` values (`$`, `\`, `&`, non-ASCII); `metadata` on; `supporting` cast; every
  error input; URL round trips and malformed URLs; the companion's `frames`, `patch`, `base` and `schema` ops.
  Corpus size is fixed in Phase 2 (the reviewer's was 5,372 renders reaching 98.1% of statements).
* **Coverage gate.** Statement and branch coverage of `character.py` by the corpus (sys.monitoring or
  coverage.py), target at least 98% of statements (not of raw lines: about 8,000 of 14,265 lines are code), every
  uncovered statement listed with a reason or a new case. This is the Python half only; the TS half is the
  mutation gate below.
* **Mutation gate (the TS half).** Python lines do not map to TS lines, so equal line coverage cannot be asserted.
  Instead: automatically mutate 100 random numeric literals and operators in the TS parts, one at a time; the
  corpus must flag at least 95%, and each survivor is classified (dead code, equivalent mutation, or a missing
  case that is then added).
* **Reviewer-written adversarial cases** are added to the corpus; the pass criterion is that none of them shows a
  diff or reaches an uncovered statement. (Replaces my earlier open-ended "a reviewer tries to find a path".)
* **Localising a mismatch.** Given a case id, regenerate the Python stages, render TS, print the first differing
  stage and offset with context.

### 5.2 The port

* One TS file per Python module, same function names in camelCase (`_hair_mass` becomes `hairMass`). Wire-visible
  parameter keys stay snake_case (`hair_color`, `highlight_strength`) so JSON, URLs and the tool protocol need no
  mapping layer (D4). Erasable TypeScript only (no enums, namespaces, parameter properties;
  `erasableSyntaxOnly`), so Node runs the files directly.
* By hand with AI assistance, function by function, **not** a general transpiler (it would cost about as much as the
  port and leave Python-shaped code to maintain as the source of truth). Pure data tables (the `BEGIN`/`END` trace
  blocks, preset literals) are produced by a throwaway script that evaluates the Python and writes TS literals, then
  owned by hand.
* **Hazard ledger.** Phase 0 produces `hazards.json`: an AST scan listing every site of every class in section 6.
  Each ported function is checked off against it; a site with no recorded handling blocks the slice. This turns "we
  hope we remembered" into a list.
* **The kernel** (`pynum.ts`) holds every Python behaviour JS lacks, and nothing else may call `toFixed`,
  `Math.round`, `Math.hypot`, `%` on a possibly negative operand, default `sort`, `replace(string, ...)`, `x[-1]`,
  `===` on arrays, or truthiness on a container: `fmt0/1/2/3` (and `02x`), nan/inf/`-0.0` spellings, `pyRound` and
  `roundTo(x, n)` (round half to even on the exact value; `round(1.0005, 3)` is `1.0`, not `1.001`), `pyRepr`
  (Python float repr, `1.0`, `1e-05`), `pyMod`, `pySum`, `pyHypot`, `pySqrt`/`pyAcos` (throw on domain error),
  `copysign`, `at`/`sliceStep`, `isEmpty`, `deepEqual`, `replaceAll`, `sortNumeric`, `sha1` (synchronous), a Python-compatible JSON writer, lenient
  urlsafe base64 decode, and a hand-written `colorsys` (`rgb_to_hsv` ends in `(h / 6.0) % 1.0` with a negative `h`;
  `hsv_to_rgb` uses `int()` and `i % 6`). A grep test enforces the "nothing else" rule; `noUncheckedIndexedAccess`
  is considered and probably too noisy.
* Python slices copy and JS arrays alias; any function that mutates a list it received is flagged in review. `+=`
  on list parameters was not checked by the audit and is added to the ledger.

### 5.3 Branch and layout

The port lives on a long-lived branch `ts-port` off `dev`, in `ts/` (own `package.json`, `tsconfig.json`, lockfile),
leaving the Python tree untouched. Nothing is released from it until cutover. `CLAUDE.md` says every push to `main`
is a release with a tag and that the companion pins tags, so the port must not reach `main` early. At cutover `ts/`
becomes the package (the companion's `src/creator.ts` resolves `<creator>/src`, so the final layout matters and is
settled in Phase 6). Version source after cutover: `package.json`.

## 6. Python behaviours JavaScript does not reproduce

All lines are `character.py` unless stated. Counts and sites are the cold-audit reviewer's (verified by AST scan and
by running Python against Node), cross-checked by me where noted. "Renders" is how many of the reviewer's 5,560
render calls changed when that behaviour alone was swapped for the JS one.

| # | Hazard | Sites | Effect when swapped |
| --- | --- | --- | --- |
| 1 | **`round()` half to even vs `Math.round`** | `colorutil.py:17` (`round(c*255)`), `:13331`, `:13370` | 1,606 renders (28.9%) differ; exact ties on `colorutil:17` 9,362 of 586,752 calls, on `:13331` 20,306 of 137,160 (15%); 3 of 22 presets differ in flat, **21 of 22 in soft**; shows as colour drift, not a logic error |
| 2 | **`colorsys`** | `shade`, `tint`, `lit_tone`, `soft_shadow_tone`, `:13410` | JS `%` gives 117 wrong colours and 13 crashes over 2,652 derivations; `Math.round` 158 |
| 3 | **Chained comparisons** | `:98`, `:2317`, `:5577`, `:12055`, `:12097`, `colorutil:49`, `:68` | 6 of 7 change truth value on real data (`:12097`: 1,809,872 of 2,856,384 evaluations) |
| 4 | **Negative indices and slices** | 35 `x[-1]`; 36 slices, 9 with a negative bound, 7 stepped (`:4333`, `:4446`, `:4554`, `:7289`, `:7298`, `:7314`, `:13334`) | `undefined` or wrong data; visibly wrong SVG at once |
| 5 | **Container truthiness** | `:6086` (13,864 empty evaluations), `:5847`, `:4431`, `:4475`, `:4479` | wrong branch (an empty array is truthy in JS) |
| 6 | **List `!=`** | `:13405` | JS compares references; the branch flips in 10 of 98 evaluations |
| 7 | **`sorted()` default** | `:12096` (two floats), `:13330` (set of ints) | JS sorts as strings: 2,500 renders (45%) differ |
| 8 | **`str.replace` replaces all** | `:115`, `:4169-4171` | JS replaces the first only |
| 9 | **Regex** | `:123-128` (`_soft_stroke_widths`, `re.sub` with a callback), `:4168` (`re.findall`), `:14023-14025` | `\1`/`\g`/backslash templates vs `$1`/`$&`; `\b` is Unicode in Python; an `id_prefix` containing `$&` is rewritten differently |
| 10 | **`sum()` compensation** | 11 sites: `:5913`, `:10601-10605`, `:13281`, `:13528`, `:13923`, `:13996-13997` | naive sum differs on 77% of distinct sums, 0 renders changed so far; silent |
| 11 | **Maths library** | `sin` 19, `cos` 20, `radians` 16, `hypot` 13, `atan2` 4, `acos` 2, `copysign` 4, `**` 25 (16 integer exponents, 9 fractional: `:4329`, `:4442`, `:4550`, `:10468-10469`, `:12038`, `:12167`, `:12598`, `:13324`) | section 4; 0 renders changed so far |
| 12 | **`min`/`max` ties** | 72 and 73 calls; first-wins at `:13921-13923` (`max(range, key=...)`), `:4494`; zero-sign at `:5583`; mixed int/float at `skeleton.py:401`, `:10205` | JS must keep the first on ties |
| 13 | **`%` on negative or float operands** | `:10549` `(i-1) % n` (inert today: both sides miss `inside`), `urlstate.py:101` `-len % 4` (JS: `"=".repeat(-1)` throws RangeError for 3 of 4 lengths), `colorutil.py:50` | |
| 14 | **Formatting corners** | 1,153 `:.Nf` sites | `0.25` gives `0.2` in Python, `0.3` in JS; `-0.0`; nan/inf; 1e21 and up: none reached in the corpus, plausible at `:6733`, `:4326`, `:4441`, `:4549`, `:13273` when an input is exactly 0 |
| 15 | **Float repr** | `:13361` (`round(0.6*gain, 3)` printed bare: Python `0.0`, JS `0` when `highlight_strength` is below about 0.0017), `:13209`, `:6733` | |
| 16 | **`str.format` braces** | `:4723`, `:4730` | |
| 17 | **sha1** | 4 sites | no synchronous hash in browsers |
| 18 | **Errors** | section 4, item 4 | not visible to an SVG diff |
| 19 | **Text length and escaping** | `:10160-10167`: `len()` counts code points, JS UTF-16 units; `escape` covers `& < >` only | user text only |
| 20 | **Codecs** | `urlstate.py:48-111`, `catalogue.py:794`, `attribution.py` | section 4, item 2; lenient `urlsafe_b64decode`, `json.loads` accepts `NaN`; exception text embeds Python messages (`urlstate.py:68`, `:105`) |
| 21 | **Type coercion on URL data** | `params_from_dict` validates only `finish` and `highlight_strength` | `"3" * 2` is 6 in JS; `?c=` links are user input |
| 22 | **Import cycle** | `render_character` imports `attribution` lazily (`:14255`) | ES modules handle cycles differently |

The reviewer ranked "least likely to be caught by an SVG diff": error behaviour, the URL/JSON codec decode path,
ulp-level maths and `sum` differences (they pass now and fail on another platform or a bigger corpus), inputs the
corpus does not contain (`-0.0`, ties, tiny strengths, `$` in a prefix, 3-digit or upper-case hex), and code
reachable only through fields the catalogue never sets. The corpus design in 5.1 targets each.

## 7. Phases and gates

Gates that need taste are the owner's; nothing in this port needs taste because the output must be bytes-equal. A
deliberate visible change later goes through the blind-pair process of `soft-hair-plan.md`, after cutover.

**Phase 0. Mini-oracle and ledger (no freeze).**
The AST-instrumented renderer, a small corpus (every preset in flat and soft, plus the kernel fixtures), the hazard
ledger, record-and-replay of real format and maths calls. Read pages.yml history on Linux (the owner can glance if
the sandbox cannot).

**Phase 1. Spike, then Gate 1 (decides whether to continue).**
Kernel (without the codecs), `colorutil` with `colorsys`, `skeleton`, and two or three leaf layers with the three
post-steps, compared by stage on the mini corpus. Measure: the maths-library mismatch rates and what they do to
digits, render time per character in V8 against CPython and against Pyodide (cold and warm), package size against
Pyodide plus the `.py` files, whether the companion can import the `.ts` directly (and with `tsc` typechecking
strict NodeNext, which then typechecks creator sources too and needs the creator's `package.json` to say
`"type": "module"`), `stripTypeScriptTypes` against `tsc` with `rewriteRelativeImportExtensions` for the browser,
and a one-file cross-engine page for Safari and Firefox. Also check whether a non-`main` branch may deploy to
Pages (environment rules; inferred unknown).
Gate 1 (owner): continue, change course, or stop, on measured numbers. The cost sunk by then is Phase 0 and the
spike only; the freeze has not started.

**Phase 2. Full oracle, test audit, freeze starts.**
Full corpus as data, stage hashes, coverage gate, mutation harness, second platform manifest, audit of the 288
tests (output-level and portable, tied to a function, Python-only, comic). Freeze begins (section 11).
Gate 2: manifest reproduces on the second platform or the differences are understood and written down; coverage
and reviewer-case criteria met.

**Phase 3. Foundation.** Kernel complete (codecs included), registry and types for `CharacterParams`, `Outfit`,
`FaceStyle`, `Expression`; `validate_finish`; `skeleton_for`, `BODY_TYPES`, `aged_face`; `presets`, `supporting`;
`urlstate`.
Gate 3: `asdict` of every preset deep-equals the TS value; every corpus URL decodes identically and encodes to the
same bytes; validation and error cases raise equally. (`catalogue.json` is **not** gated here: `catalogue.py` imports
`HAIRSTYLES` and the cut tables from `character.py` and asserts on them at import, so it can only pass after
Phase 4.)

**Phase 4. The parts, dependency order, stage gate after each group.**
Order: shape helpers; head and face; hair (the five cuts, trace tables, soft finish, locks); body (torso, neck, bust,
legs, boots); arms and hands together with the garments that call `_hands_after_coat` (one group, per section 3);
remaining garments; props and head gear; assembly and post-steps. Because the stage list is by index, any group
can be compared while others are missing. A fresh reviewer reads each completed group against the Python for idiom
drift the corpus cannot see (aliased lists, a precedence slip that cancels on the corpus). No reviewer runs while a
hash or ref-out run is in progress on the same machine (a ref-out comparison failed intermittently under load
earlier in this project).
Gate 4: whole-SVG equality on 100% of the corpus; `catalogue.json` byte-equal; mutation gate passed; known-ulp
list (if any) signed.

**Phase 5. Tests.** Output-level and rule tests to `node:test`; tests of internals either ported with their
function or dropped by name against the audit; raster checks stay Python (`compare_pixels.py`, harness) reading
node output.
Gate 5: a deliberately broken TS part is caught by the ported tests as well as the hashes; the test list reconciles
against the audit with nothing dropped silently.

**Phase 6. Consumers.** Section 8 is the inventory. Sub-steps: 6a creator web tool; 6b node CLI, then `cover`,
`sheet` if D5 says so, `refresh-*` scripts and the tracing tools; 6c companion; 6d docs and CI of both repos.
Gate 6: companion `./check.sh --full` green; the owner tests the app, the demo and the live Pages page as for v0.7.0.

**Phase 7. Cutover.** Tag the last Python commit `python-final`; `CLAUDE.md`, `README.md`, `docs/api.md`,
`docs/architecture.md`, `STATUS.md` updated (the `CLAUDE.md` toolchain wording names ruff, pytest and uv; the new
text is the owner's to approve); release creator v0.4.0, companion v0.8.0 (owner's numbers); the Python source
stays one release, then goes on the owner's say.
Rollback: until the companion pin moves, nothing shipped changes; after, the previous pin and tags still work.
The creator's live Pages site deploys on each `main` push, so it has its own rollback: re-run the workflow on the
last Python commit.

## 8. Inventory of what touches Python or Pyodide (verified by the method reviewer's greps)

**Creator web tool and tooling.** `web/index.html:126` (loads `pyodide.js` from jsDelivr v0.26.4); `web/app.js`
`PACKAGE_FILES` (`:14-27`), `BRIDGE_PY` (`:37-65`), `loadPyodide` (`:866-905`), and the file being a classic script
that becomes a module; `web-stage.sh` (copies the `.py` files and all of `ref-out/`); `.github/workflows/pages.yml`
(needs Node and a TS build step, keeps Python for cairosvg); `refresh-ref-out.sh`, `refresh-bases.sh`,
`refresh-catalogue.sh` (the last two run inline Python), `render.sh`, `cover.sh`, `sheet.sh`, `sheet_satoshi.sh`,
`compare_pixels.py`. **The tracing tools emit Python source into `character.py`**: `.claude/skills/trace-reference`
(`trace_lib.py`) and `harness/hair_parted/emit.py` write the `BEGIN`/`END` trace blocks (`:1763`, `:1922`, `:2867`,
`:3333`). After cutover they must emit TS or be retired.

**Companion (`/Users/hanssen.henrik/git/self-study/anime_ai_companion`).**
* Runtime: `python/render_ops.py`, `python/render_worker.py`, `src/python.ts` (`pythonCommand`, `PYTHON`),
  `src/server.ts:9,61-62`, `src/cli.ts:9,24,46` (doctor and help text, `--version`), `src/doctor.ts`,
  `src/creator.ts` (resolves `<creator>/src`, a sibling `../anime-character-creator/src`, or a clone of the pinned
  tag into `~/.anaico/creator/<ref>`), `src/avatar.ts` (the 15 s kill and timeout at `:313-330`).
* **Behaviour that is easy to lose:** the worker is a separate process that is killed on timeout; in process, a
  stuck render blocks the event loop. Keep a `worker_threads` worker with termination (or a child process running
  the TS), measured in the spike. `render_ops.handle` returns `f"{type(exc).__name__}: {exc}"` to the model;
  `coerce` uses Python `float(raw)` (accepts `"1_0"`, `" 1e3 "`, `"inf"`) and half-even `round(x)` for int fields; `op_schema` returns the
  annotation strings. The port must decide the accepted number syntax (stricter is acceptable if announced) and
  produce equivalent error text where a test or the model sees it.
* Demo: `demo/render-bridge.js`, `demo/stage.mjs:25-95` (`pythonFiles`, `creator-files.json`), `demo/demo-boot.js`,
  `demo/local-socket.js:68` (an error message about fetching Pyodide), `demo/README.md`; the demo is documented as
  "plain JavaScript, no build step, no TypeScript" (`docs/plan.md:148`), so it needs the strip or `tsc` step in
  `stage.mjs`; `public/frames.js:1` (contract comment).
* CI and config: `.github/workflows/ci.yml:28-30` (`setup-python` 3.12), `.github/workflows/pages.yml:12,40-51`
  (path filter on `python/render_ops.py`, stages creator `.py`, sets `CREATOR_SRC`), `.python-version`,
  `.github/ISSUE_TEMPLATE/bug.md:10`, `check.sh:44-60,94` (creator at the pinned tag with a clean tree, the Python 3.11
  check, `stage_demo`), `package.json` (`creator.ref`), `pyproject.toml`, `uv.lock`, `tsconfig.json` and
  `tsconfig.frontend.json` (strict NodeNext with `erasableSyntaxOnly`: relative imports of creator `.ts` get
  typechecked by the companion's `npm run typecheck`).
* Docs and site: `README.md`, `AGENTS.md`, `CLAUDE.md:13`, `CONTRIBUTING.md:18`, `docs/plan.md`,
  `docs/frame-packs.md:61,99`, `packs/risa-dress/NOTICE.md:13`, `site/shots.mjs:14`, `site/pages/{index,
  getting-started,how-it-works,customising}.md`, `trailer/lib.mjs:21`, `trailer/compose.mjs:41`, `trailer/audio.py`.
* Tests: `test/render-worker.test.ts`, `test/avatar-service.test.ts` (JSON-lines protocol, timeout),
  `test/browser-demo.test.ts` (Python at `:654-655`), `test/doctor.test.ts`, `test/helpers/server.ts:19-37,187,240`,
  `test/cli.test.ts:25`, `test/docs.test.ts:83-88` (asserts README and site clone commands match `package.json
  creator.ref`, so a new pin changes them).

## 9. Risks

| Risk | Size (inferred unless stated) | Mitigation |
| --- | --- | --- |
| Silent drift from half-even `round`, `colorsys`, chained comparisons, negative indices, truthiness, list `!=`, default sort (rows 1 to 8) | near certain to occur once; each shows at once in a byte diff, except `round` (looks like colour drift) | kernel, hazard ledger, stage hashes, soft finish in the corpus from the first day |
| A maths-library ulp flips a digit on another platform or a larger corpus | rare per render (0 of 5,560), not impossible, hard to diagnose | known-ulp-flips list with raster check; second-platform manifest; cross-engine page |
| Error paths drift (rows 18, 21) | certain without work; invisible to SVG diffs | errors in the corpus; explicit domain checks |
| Corpus misses code reachable only through uncatalogued fields | real (the reviewer's missed three functions) | corpus from dataclass fields; coverage gate; mutation gate |
| The port is bigger than estimated | moderate; the real tall poles are the registry, 1,153 format sites, the data tables, the 330 internal-call tests and Phase 6's roughly 40 files in two repos, not any single function (the longest is `_arms` at 244 lines; `_katana` is 49, `_headscarf` 65) | Gate 1 measures speed on real slices; stopping is an allowed outcome |
| The owner keeps changing the look during the port | high (`CLAUDE.md` names more customisation and a bigger roster as the direction) | freeze rule and the queue in section 11, or D10 |
| In-process rendering loses the worker's timeout and crash isolation | certain | worker thread with termination, tested |
| Browser module loading (specifiers, MIME) | certain to need design | decided in the spike |
| The sibling project's consumer scripts cannot be assessed | unknown | D5, needs `local/` |

## 10. Review record

Two fresh agents reviewed draft 1 on 2026-10-16. The **method reviewer** found: the seam in draft 1 ("part functions
are `(sk, p) -> str`, hash them one by one") is false; the phase order had dependency inversions (Gate 2's
`catalogue.json` and `presets` need `character.py` tables, the spike needs the registry, the freeze started before
the go/no-go gate); Phase 5c named about a third of the places Python or Pyodide is touched; the oracle contradicted
itself on URL byte-equality; the fdlibm remedy was wrong; Python raising where JS yields NaN was uncovered; the
coverage gate was weaker than stated; the browser build had a `.ts` specifier and MIME trap; plus wrong facts (312
"functions", 349 fields, 49 `ref-out` files, `_katana` 674 lines, 10 `sum` sites, "no bare float", "tests that
raster"). I re-checked the function sizes, counts, bare floats and test claim myself and confirm them (my `awk` had
counted the constants after each function as part of it). The **cold audit reviewer**, working from the source alone,
produced the measurements in section 6 and the libm replay in section 4, and found that formatting is not the main
risk but half-even `round`, `colorsys`, chained comparisons, negative indices and sort order are. Draft 2 rebuilds
the oracle seam, the phase order, the consumer inventory and the hazard table on those findings.
Not yet independently reviewed: this draft 2. Run the same two reviews on it before the owner relies on it.

## 11. Freeze rule

Phases 0 and 1 need no freeze: the oracle is the immutable tag `v0.3.0`. From the start of Phase 2 (after Gate 1
says continue) until cutover: no change to anything the corpus covers, which is every output of `character.py`, the
presets, the catalogue and `ref-out`. Bug fixes are allowed in Python only if the manifest is regenerated and the
same fix is made in TS in the same change (before Phase 3 there is no TS yet, so such a fix waits and is recorded);
a fix that must reach users sooner is released as a creator v0.3.x tag and the companion pin moves, as today. New
design ideas, new characters and new options go on a written queue and are built after cutover, in TS. The cost is
real: adding a preset moves `ref-out`, the sheet and the manifest. Alternative policy (D10): do not freeze, keep
building in Python, and port the deltas at the end; this lowers the pause but grows the final merge and weakens the
oracle.

## 12. Decisions for the owner (my recommendation first)

* **D1 Language and build.** TypeScript, erasable syntax only. Browser copy by `tsc` with
  `rewriteRelativeImportExtensions` (adds `typescript` as a devDependency, which strict checking needs anyway), or
  by a small staging script, decided by the spike. Alternatives: JavaScript with JSDoc types; Rust to WASM (about
  twice the work, only worth it for native UIs).
* **D2 Distribution.** The companion keeps cloning the creator at a tag and imports its `.ts` directly (Node 22.18+
  already required). No build output committed. Alternatives: commit `dist/` with a staleness check, as `ref-out/` is;
  npm.
* **D3 Reference.** Tag `v0.3.0`, CPython 3.13.11, macOS arm64, plus a second platform for the manifest.
* **D4 Naming.** camelCase functions mirroring Python names; snake_case parameter keys on the wire.
* **D5 `generate`, `cover`, `sheet`, and the sibling project.** Recommend port them in Phase 6b so the README art and
  the sibling consumer both become "node renders the SVG, cairosvg makes the PNG". Needs your answer on what the
  sibling calls, because `local/` is not on this machine. Alternative: leave that consumer on the frozen Python.
* **D6 Comic.** `comic/` imports the Python renderer. It stays on the frozen Python and stops following look
  changes, unless you want it ported (adds harfbuzz) or retired. I do not know whether it is used.
* **D7 Python tests.** Port output and rule tests, drop tests of Python internals, reconcile against the audit.
* **D8 Python source after cutover.** Keep for one release under `python-final`, then remove on your say.
* **D9 Versions.** Creator v0.4.0, companion v0.8.0.
* **D10 Freeze or not,** section 11. Recommend freeze, starting after Gate 1.
* **D11 Companion rendering location.** Worker thread with a timeout (recommended) or in process.

## 13. Effort (inferred; Gate 1 replaces it with measurements)

A "session" is one working context of the length of the soft-hair sessions. Phase 0: 1 to 2. Phase 1: 1 to 2.
Phase 2: 2 to 3. Phase 3: 3 to 4. Phase 4: 8 to 14 (about 8,000 lines of code at roughly 600 to 1,000 a session
including diff fixing). Phase 5: 3 to 4. Phase 6: 5 to 7. Phase 7: 1 to 2. About 25 to 35 sessions, a few million
tokens. The spread is mostly Phase 4 and Phase 6. Draft 1 said 17 to 27; the reviewers found the extra work in
Phases 2, 3 and 6.
