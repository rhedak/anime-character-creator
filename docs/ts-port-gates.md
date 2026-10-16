# The TypeScript port: gate results

2026-10-17, branch `ts-port`. The gates are the ones set in `docs/ts-port-plan.md` (sections 4, 5.1 and 7). Everything here was run on this
machine (macOS arm64, Node 22.22.3, CPython 3.13.11 as the reference) and can be run again with the command beside it. The oracle is
the Python package frozen at the tree of tag `v0.3.0`.

## The drawing

| Gate | Result | How to run it |
| --- | --- | --- |
| Whole documents, the 7,662-case corpus | 7,662 of 7,662 byte-equal; 444,396 stages (53 slots and the post-steps per case) equal | `cd ts && node --test "test/stages.test.ts"` |
| The committed art | the 20 presets and 2 neutral bases equal `ref-out/*.svg` byte for byte | `node --test "test/refout.test.ts"` |
| The catalogue | `toJson()` equals `ref-out/catalogue.json` (22,740 bytes) and a fresh Python run | `node --test "test/catalogue.test.ts"` |
| Inputs Python rejects | 333 of 333: 272 renders raise the same exception class, 61 link operations give the same result or class; the 29 links that succeed encode to the same bytes | `node --test "test/errors.test.ts"` |
| Function level | 330 Python functions replayed from recorded real calls (52.3 million calls made, 37,025 kept); 36,304 calls replayed, 546,507 floats bit-exact, 191 within 4 ulp (the engine's `sin`, `cos`, `**`, `atan2`), none outside | `node --test "test/calls.test.ts"` |
| Differential fuzzing, never seen by the porting | 100,000 random characters (seeds 777 and 2026, up to 20 fields each, 35 to 60 percent of values extreme or out of range): 100,000 identical, 1,583 of them raising Python exceptions with the same class | `harness/ts_port/fuzz.py N SEED`, then `node ts/tools/fuzz-check.ts <file>` |
| Mutation | 150 random single edits (a constant by 7 percent, an integer by one, an operator) to the drawing code, in a private copy: 138 caught by the corpus alone; the 11 survivors re-run against the whole suite: 9 caught more; 2 left, both dead or equivalent (`scallop = 0` against `1`, both mean no scallop; `hyp or 1.0`, a guard for a zero-length segment no input produces). One further run crashed and counts as caught | `node ts/tools/mutate.ts 150 1 3`; `ONLY=out/mutation-run1.json DETECTOR=full node ts/tools/mutate.ts` |
| Corpus coverage (of the Python) | 99.66 percent of the statements of `character.py` (3,519 of 3,531), 97.77 percent of line arcs; the 12 uncovered statements are dead (a shadowed duplicate `_straight`, unreachable branches) | `harness/ts_port/coverage_gate.py` (`docs/ts-port-coverage.md`) |
| The oracle's own stability | the manifest is byte-identical on CPython 3.11.14, 3.12.0, 3.12.12 and 3.13.11 (3.12 changed `sum()` of floats; no document changes) | `manifest_full.py verify` under each interpreter |
| Rules the oracle cannot express | 70 Python tests ported (602 items) as `ts/test/rules-*.test.ts`, 30 of them mutation-checked on a copy; the 22 catalogue tests | `node --test "test/rules-*.test.ts"` |
| Whole suite | 831 TypeScript tests, 0 failing; `tsc` strict clean with `erasableSyntaxOnly` | `cd ts && npm test && npm run typecheck` |

## The consumers and the build

| Item | Result |
| --- | --- |
| Real browser | headless Chrome 155 (V8) loads the web tool from a share link, builds the controls (129 inputs, 16 selects) and draws; the cross-engine page draws 1,916 whole characters (every 4th of the corpus) byte-equal, 15 of 15 checks. **Not run: Safari, Firefox** (their maths libraries differ from V8's; the page is `ts/web-check`) |
| Refresh scripts | `refresh-ref-out.sh`, `refresh-catalogue.sh` and `refresh-bases.sh` now draw through TypeScript and still report "matches the code"; `refresh-ref-out.sh --pixels`: 0 of 43 PNGs differ |
| Size | the whole drawing code compiles to about 570 KB of JavaScript (comments stripped), against about 5.5 MB of Pyodide plus about 800 KB of Python source before |
| Speed | the 7,662 corpus documents render in 5.9 s in Node: mean 0.77 ms, median 0.63, p95 1.4 ms (CPython: median 0.94 ms flat and 2.29 ms soft on the presets) |

## What the gates found along the way

The corpus caught real defects the first time it ran against each domain: an empty list treated as true in `neck`, a wrong-typed colour
printed as `null` instead of Python's `str()`, a whole float in the integer `shoulder_bars` that Python rejects at `range()`, a
falsy `background=0`, and `render_character`'s positional parameters. The independent kernel review found about ten silent edge cases
(`**`, JSON key order, code-point string order, `int(s, 16)`, non-integer indices, division by zero), all fixed and fixture-tested.

## Known limits (nothing hidden)

* **Maths library.** `sin`, `cos`, `acos`, `atan2` and `**` come from the engine, and differ from the C library Python used in the last bit
  on 0.2 to 24 percent of calls. No printed digit has ever differed (13.6 million numbers in one test, 100,000 whole characters in the
  fuzz). Where a cancellation amplifies the last bit (`_rounded_box`, `_eye_lash`) the port uses correctly rounded versions
  (`core-limbs-pow.ts`). A flip on another engine would be recorded, rasterised and signed, not hidden (plan, section 4).
* **Platform.** The reference is one machine (macOS libm). The manifest agrees across four CPython versions but has not been
  regenerated on Linux, and Python itself can differ from `x * x` in `x ** 2` on Apple's libm in 0.12 percent of calls.
* **Error text.** Exception classes equal Python's everywhere; the texts are the port's own where listed in `docs/ts-port-errors*.md`.
* **Python-only things left alone by decision:** the full command line (`generate.py`), `cover.py`, `sheet.py`, the comic package, PNG
  export (cairosvg), and the picture-pack tools of the companion.
