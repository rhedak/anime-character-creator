# TypeScript port: Phase 0 and 1 results (the Gate 1 report)

2026-10-16, branch `ts-port` (commits `51af030`, `4e4a19e`, `9063239` on top of the plan). The plan is
`docs/ts-port-plan.md`. This report is what the mini-oracle and the spike measured, so the owner can decide at Gate 1
on numbers. Nothing under `src/` (the Python) was touched; the oracle is pinned to the tree of tag `v0.3.0`
(`git diff v0.3.0 HEAD` of the Python tree is empty).

**(verified)** means a test or command run on this machine in this session, named below. **(inferred)** means not run.

## 1. What exists

| Piece | Where | State |
| --- | --- | --- |
| Stage oracle (Python) | `harness/ts_port/instrument.py`, `manifest.py`, `cases.py`, `corpus/mini.json`, `manifest/mini.json` | 68 cases, 58 stages each (the 53 part slots, the joined body, the body after each post-step, the final document). `manifest.py check-docs` proves the instrumented document equals the plain one on all 68; `verify` passes twice in a row. |
| Real-call recorder (Python) | `record.py`, `corpus_wide.py`, `fixtures/real-calls.sample.json` | 3,810 characters, 7,620 renders, all byte-identical to an uninstrumented run; 25.1 M format calls, 9.7 M `**`, 9.8 M `sin` and so on recorded; 1,559,322 distinct format calls, 64,616 distinct `hypot` calls. |
| Hazard ledger | `hazards.py`, `hazards.json` | 2,549 entries over 8 files. Every number the plan quoted reproduces (sum 11, sin 19, cos 20, hypot 13, atan2 4, acos 2, copysign 4, `**` 25, sha1 4, `.1f` 952, `.2f` 190, `.0f` 10, `.3f` 1, round 3, chained comparisons 7). |
| Table and type generators | `gen_tables.py`, `gen_types.py` | Hat tables and `ts/src/params.ts` (the field registry with defaults and each field's comment as JSDoc) are generated once, then hand-owned. The registry is small: 134 fields, four scalar type tags plus the two nested types. |
| The kernel | `ts/src/pynum.ts`, `sha1.ts`, `pyre.ts`, `pyjson.ts` | Float formatting, `round`, `round(x, n)`, float repr, `%`, `sum`, `hypot`, slices, sha1, `re.sub` templates, `json.dumps`. |
| Ported slice | `colorutil.ts` (with `colorsys`), `skeleton.ts`, `body.ts`, `character.ts` | `colorutil`, `skeleton`, `skeleton_for` and the body profiles, `_neck`, `_mask`, `_hat_underside`, the head outline, `_soft_stroke_widths`, `_namespace_ids`, the document wrapper. |
| Tests | `ts/test/*.test.ts` | 43 tests, all passing; `tsc` strict with `erasableSyntaxOnly`, no errors. Run: `cd ts && node --max-old-space-size=8192 --test "test/*.test.ts"`. |
| Cross-engine page | `ts/web-check/` | Staged and run as compiled JavaScript in Node (14 of 14 checks). **Not yet run in a real browser** (section 6). |

## 2. Does the kernel reproduce CPython? (verified)

Against Python's own answers, zero differences in every class that must match:

| Class | Synthetic (adversarial) | Real calls from the corpus |
| --- | --- | --- |
| `f"{x:.Nf}"`, ties, `-0.0`, nan, inf, 1e21+, tiny, neighbours of ties | 240,000 | 1,559,322 |
| `round(x)` (half to even) | 60,000 | 19,138 (177 exact ties among them) |
| `round(x, n)` | 240,000 | in the 19,138 |
| float `repr` | 60,000 | (not on the real path except `:13361`) |
| `%` | 108,000 + 427 ints | 243 |
| `sum` (CPython 3.12 compensated) | 4,002 | 2,060 |
| `math.hypot`, bit for bit | 40,000 | 64,616 |
| `sqrt`, `radians`, `degrees`, `copysign` | | 6,067, 217, 113, 82 |
| `sha1`, slices, `re.sub` templates with odd prefixes (`a$&b`, `x\1`, `\g<1>z`), `float()`, `int(s, 16)` | 210, 594, 17, 17, 12 | |
| colour tones: 13 operations over 1,972 colours, including pink and magenta and malformed strings | | 25,636 results |

`pyHypot` is CPython's own algorithm, reproduced from memory of `mathmodule.c` and confirmed bit for bit; V8's
`Math.hypot` would have been wrong on 35.4% of the real calls and `sqrt(x*x+y*y)` on 16.6%.

## 3. The maths library: how often a last bit differs, and whether it ever reaches a digit (verified)

Real Apple-libm results from the corpus, replayed through V8 (Node 22.22.3, V8 12.4):

| Function | Distinct real calls | V8 differs | |
| --- | --- | --- | --- |
| `**` / `Math.pow` | 98,407 | 198 (0.20%) | `x*x` for `x**2` differs on 0.12% of 97,152 |
| `sin` | 1,800 | 56 (3.1%) | |
| `cos` | 745 | 20 (2.7%) | |
| `acos` | 40 | 3 (7.5%) | |
| `atan2` | 594 | 142 (23.9%) | |

These agree with the cold-audit reviewer's separate measurement (0.19%, 2.9%, 2.2%, 4.7%, 22.4%).

**The question that matters is whether this changes the printed text.** Tested end to end on the one ported path that
uses `sin`, `cos` and a fractional power, the head outline: **400,000 random outlines, 13,600,000 printed numbers,
0 differ from Python.** Also 0 differences in the 8,000-outline committed sweep, the 7,560-combination skeleton sweep
and the three layers on 68 cases. So the plan's policy holds so far (port exactly what can be ported exactly, take the
rest from the engine, keep a signed list of any flip that appears). The expected rate of a flip is far below
what 13.6 M numbers can resolve (my estimate, inferred: about 1e-13 per number), so this shows the risk is
small, not that it is zero. It does not speak for Safari or Firefox (section 6).

## 4. What the first slice matched on the first try (verified)

* `skeleton_for` over all 68 cases and a 7,560-combination sweep (3 bodies, 7 heights, 5 frames, 3 busts, 3 belt
  shifts, 4 face ages, with and without a hat): every field of every skeleton, by sha256 of Python's compact JSON.
* Layers `_neck` (all 68 cases), `_mask` and `_hat_underside` (non-empty on a few, empty on the rest, per the
  manifest), byte for byte.
* `_soft_stroke_widths`, `_namespace_ids` (including the odd prefixes) and the document wrapper on the recorded
  strings of all 68 cases, including soft finish and `background`.

## 5. Speed and size

* **Render speed is not the problem (verified).** CPython renders a whole character in a median 0.94 ms (flat) and
  2.29 ms (soft), p95 about 6 ms (`time_layers.py`, 68 cases). V8 does the one non-trivial ported layer, `_neck`,
  in 1.14 µs against CPython's 2.50 µs (2.2 times faster), and `fmtFixed` takes 70 ns a call. The other two layers return
  early on most cases and tell nothing. So a port will not be slower and will be somewhat faster, but speed is not a
  reason to port.
* **The cost is startup and download (not measured here).** The companion's notes put Pyodide at 5.5 MB, 6.5 MB
  with the demo, and in one place about 10 MB; I could not measure it (no network to the CDN from the sandbox, and the
  browser extension was not connected). The Python the web tool fetches is about 800 KB raw
  (`character.py` 669 KB, 202 KB gzipped). The ported slice compiles to 70 KB (20 KB gzipped, comments kept) for
  roughly the share of the code that `colorutil`, `skeleton` and a few layers are; I do not extrapolate it. The
  claim to test later is that the whole package, comments stripped, compiles to well under a megabyte.

## 6. Distribution (verified unless marked)

* **The companion can import the creator's `.ts` directly**, from its own directory, with no build: Node 22.22.3,
  35 ms for the import including the module graph.
* **The creator sources pass the companion's strict `tsconfig`** (`NodeNext`, `strict`, `erasableSyntaxOnly`) with no
  errors, when the creator's `ts/package.json` says `"type": "module"`.
* **`tsc` with `rewriteRelativeImportExtensions` is the browser build.** It emits `.js` files with `.js`
  specifiers; Node's `module.stripTypeScriptTypes` keeps the `.ts` specifiers, which a browser would fetch with the
  wrong content type on common static hosts (inferred). Use `tsc`. It needs `typescript` as a dev dependency of the
  creator (I used the companion's 5.9.3 through a symlink; the creator has no `node_modules`).
* **The compiled output runs as plain ES modules in Node** and passes all 14 checks (`web-check/run-staged.mjs`).
* **Not done: a real browser.** The Chrome extension was not connected, so the page has not been opened in Chrome,
  Firefox or Safari. To do it yourself, from the `ts-port` worktree:
  `cd ts && TSC=<path to a tsc binary> node web-check/stage.mjs --serve`, then open `http://127.0.0.1:8765/`.
  Every row should be green; the page prints the browser's user agent. Safari and Firefox are the interesting ones
  (their maths libraries differ from V8's). Please send me the red rows, if any.
* **Not done: whether a non-`main` branch can deploy to GitHub Pages**, and the Linux CI history of the
  `ref-out` comparison (the sandbox blocks GitHub's API). Both are one look in the repository's Actions page.

## 7. What the spike changed in the plan

1. **The corpus has holes the plan did not predict.** In the 68 mini cases, `_underwear_top`, `_navel` and `_chest_lines`
   never produce output (no tunic-off character), and `_mask`, `_ribbon`, `_glasses`, `_goggles`, `_blindfold`,
   `_headscarf` and the shoulder bars each appear in 2 of 68. The Phase 2 corpus must be built from the dataclass fields
   and must include tunic-off, bare-foot and closed-eye cases, as the plan says; the mini corpus is not a substitute.
2. **`sum` needs to know how many leading items are ints** (`pySum(items, leadingInts)`): CPython adds the first float
   after ints plainly, with no compensation for that one step. Each of the 11 sites has to say. Done in the kernel; the
   ledger sites are to be checked off one by one in Phase 4.
3. **Error class names are Python-version-specific**: `re.error` is `PatternError` from 3.13 and `error` before, so
   the error text the companion shows the model differs between the shipped Pyodide (3.12) and a 3.13 reference. The
   TS port should pick one set of names deliberately (decision D12 below).
4. **`re.sub` needs a template expander** (`pyre.ts`), because `id_prefix` is interpolated into a Python template;
   a prefix such as `a$&b` or `x\1` means something different in each language. Done and tested.
5. **A Python-compatible JSON writer is needed earlier than Phase 3**, for the skeleton hashes (`pyjson.ts`). Done.
6. **The field registry is smaller and more regular than the plan feared**: four scalar type tags, 134 fields, defaults
   and per-field comments generated from the dataclasses. This de-risks the registry decision.
7. **`node --test` takes a glob** (`"test/*.test.ts"`), not a directory, on Node 22.
8. **A repo `.gitignore` line `MANIFEST` also ignores `harness/ts_port/manifest/`** on this case-insensitive
   filesystem; `harness/ts_port/.gitignore` carries `!manifest/`.

New decision for the owner: **D12 (error text).** Whether the port reproduces Python's exception names and
messages where the model sees them (`ValueError: math domain error`, `PatternError: ...`), or defines its own
stable messages and updates the few tests that assert them. Recommend: define the port's own, keep the class
names the companion's tests use, and list the differences.

## 8. What I could not verify, plainly

* Behaviour in a real browser, and in any engine other than V8.
* The manifest on a second platform or a second Python version (only macOS arm64, CPython 3.13.11 was run).
* Pyodide's real cold-start time and download size.
* That a worker thread with a timeout is needed or sufficient in the companion (renders take about 1 ms).
* The Linux CI history, and Pages deployment from a branch.
* Anything about the remaining roughly 300 functions beyond the slice ported: the first slice was chosen to be
  small and self-contained, and every function in it matched at once, which is encouraging and is not a forecast.

## 9. Where this leaves Gate 1

The measurable risks the plan was most worried about (float formatting, `round`, `sum`, `hypot`, `%`, `re`
templates, the colour pipeline, the skeleton, maths-library ulps reaching digits) are tested against Python on real
and adversarial data and are clean. What remains unknown is mostly breadth (the other 300 functions), the browser
engines you will open the page in, and the decisions only you can make (D5 the sibling project, D6 the comic package,
D10 the freeze, D12 the error text).

My recommendation, for you to overrule: **continue to Phase 2** once you have opened the check page in Safari and
Firefox (the one cheap test that could still change the answer) and answered D5, D6 and D10. If a browser shows red
rows in code that uses `sin`, `cos` or `**`, stop and read them before anything else.
