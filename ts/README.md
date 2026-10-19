# The TypeScript drawing code

This is the package that draws the characters: version 0.4.0, source of truth since the port from Python
(`docs/ts-port-plan.md` is the plan, `docs/ts-port-spike.md` the first measurements). The Python in `../src/` is
frozen at the tag `python-final` and goes in the next release (`../docs/python-removal-audit.md`); it is only the
reference the golden files were recorded from, and nothing runs it. Output is **byte-identical** to what it drew,
which is the contract; a deliberate change to the look has its own rules (see "The oracle" below).

Erasable TypeScript only (no enums, namespaces or parameter properties), so Node 22.18 or newer runs the `.ts`
files directly. There are no runtime dependencies. `typescript` and `@types/node` are dev dependencies, for the
typecheck and for compiling the web build.

## Commands

From `ts/`:

```bash
npm ci                      # once, from package-lock.json
npm run typecheck           # tsc --noEmit, strict
npm test                    # node --test "test/*.test.ts", with a larger heap
npm run build:web           # node ../web-stage.mjs: compile with tsc and stage the web tool into ../out/web-stage
node bin/render.ts --out ../out/satoko --preset satoko      # the SVG command line
node bin/catalogue.ts > ../out/catalogue.json               # the web tool's catalogue
node bin/cover.ts --out ../out/cover --no-metadata           # the book cover (SVG; PNG is harness/svg2png.py)
node bin/sheet.ts --out ../out/sheet --roster satoshi        # a cast sheet (--members a,b,c for your own)
```

The test command is a glob, not a directory (`node --test test/` does not work on Node 22). One file:
`node --test test/cli.test.ts`. From the repository root, the checks that prove nothing moved are
`./refresh-ref-out.sh --check`, `./refresh-catalogue.sh --check`, `./refresh-bases.sh --check` and
`./refresh-ref-out.sh --pixels`; they need the PNG toolchain (`uv sync --project tools`, and cairo) for the PNGs. The cover and the sheets are
`bin/cover.ts` and `bin/sheet.ts`.

## Layout

`src/`, by role. A Python function `_hair_fall` is the export `hairFall`; a module-level table keeps its name
(`HAIRSTYLES`). Parameter keys stay snake_case because they are the wire format (links, JSON, the catalogue).
There is no index file: import from the module that has the name.

| Role | Files |
| --- | --- |
| The kernel (every Python behaviour JavaScript lacks) | `pynum.ts` (formatting, `round`, `sum`, `hypot`, `%`, slices, errors), `pyjson.ts` and `pyjsonload.ts` (`json.dumps`, `json.loads`), `pycodecs.ts` (base64, ASCII), `pyre.ts` (`re.sub` templates), `pyvalue.ts`, `sha1.ts` |
| The model | `params.ts` (the field registry: `CharacterParams`, `Outfit`, `FaceStyle`, `Expression`, with defaults and type tags; generated once, then hand-owned), `model.ts` (constructors, `replace`, `validateFinish`, `agedFace`), `plain.ts` (wrong-typed input from a link) |
| Proportions and colour | `skeleton.ts` (`Skeleton`, `buildSkeleton`), `body.ts` (`BODY_TYPES`, `skeletonFor`), `colorutil.ts` (`shade`, `tint`, with `colorsys`) |
| The drawing core | `character.ts` (stroke widths, the document wrapper, the post-steps), `core-head*.ts` (the hair system, `HAIRSTYLES`, the head's paths), `core-limbs*.ts` (sleeves, arms, hands, the traced garment cuts) |
| The parts | `hair.ts`, `face.ts`, `face-wear.ts` (beard, glasses, goggles), `body-parts.ts`, `body-parts-legs.ts`, `garments.ts`, `props.ts` (hat, staff, katana, familiar) |
| Data tables | `*-tables.ts`: traced coordinates, generated from the Python once and owned by hand since |
| The assembly | `parts.ts` and `parts-*.ts` (the registry of parts by Python name), `render.ts` (`renderCharacter`, `renderStages`) |
| Characters and links | `presets.ts` (`PRESETS`, `NEUTRAL_BASES`, `EXPRESSIONS`, `ROSTERS`), `supporting.ts`, `urlstate.ts` (`?c=` links), `attribution.ts` (the `<metadata>` block), `catalogue*.ts` (what the web tool shows) |
| The web tool | `web-bridge.ts`, the four functions `../web/app.js` imports |

Elsewhere in `ts/`: `bin/` (the two command lines), `test/` (`node:test`), `tools/` (the mutation gate,
`mutate.ts`), `bench/`, `web-check/` (a cross-engine page and its Node runner), `fixtures/` (data the tests
read), `out/` (ignored scratch).

## The oracle

The port was proved against the Python, and the tests keep that proof running from recordings. The generators that
made them are in `../harness/ts_port/` (they ran the frozen package, never the TypeScript, and need the
`python-final` tag now); the corpus and manifests are committed there and under `fixtures/`, so the tests need no
Python and nothing regenerates them:

* **The corpus**: `corpus/full.json`, 7,662 documents (444,396 stages) built from the dataclass fields, every
  preset, base and roster member in both finishes, every field value, random combinations including out of range,
  odd `id_prefix` values, metadata, supporting cast, URL round trips. `manifest/full.json` holds Python's hashes.
  `test/stages.test.ts` and `test/corpus.ts` compare stage by stage, so a mismatch names the first differing part.
* **Function level**: `test/calls.test.ts` replays 52 million recorded calls of 329 functions; `real-calls.test.ts`
  replays the kernel against every number CPython formatted or computed.
* **Committed art**: `test/refout.test.ts` and `test/cli.test.ts` compare with `ref-out/` and the catalogue.
* **Errors**: `test/errors.test.ts`, 333 inputs on which Python raises, each raising the same exception class
  (the text is the port's own, listed in `docs/ts-port-errors*.md`).
* **Coverage and mutation**: the corpus reaches 99.66 percent of `character.py`'s statements
  (`docs/ts-port-coverage.md`); `tools/mutate.ts` edits the TypeScript at random and the corpus must notice (of
  150 mutations 138 were caught by the corpus alone, the survivors re-tested against the full suite).
* **Rules**: `test/rules-*.test.ts` hold what the Python suite held (ids unique, the hair stays under the canvas
  ceiling, flat stays flat, validation, the README's table), on the TypeScript output.

Measured results, 2026-10-16: the corpus byte-equal; the 20 presets and 2 bases equal to `ref-out/`; `catalogue.json`
equal; the same results on CPython 3.11, 3.12 and 3.13; headless Chrome 155 draws 1,916 whole characters byte-equal;
the drawing compiles to about 570 KB of JavaScript, against about 5.5 MB of Pyodide plus about 800 KB of Python
before the port.

**After a deliberate change to the look the oracle stops applying to what changed.** The manifests, the recorded
calls and `ref-out/` say what the Python drew. A part that draws nothing for every character in the corpus
leaves every comparison green; a change that moves a drawn byte turns the document and stage tests red on purpose,
and that is the signal to decide, case by case, which baseline to refresh (see `CLAUDE.md` for the rule).
The manifest can only be rebuilt from the Python (the tag `python-final`), so after a look change it describes the old look.

## The kernel

`pynum.ts` is the one place that does what Python does and JavaScript does differently. In `src/`, nothing else
calls `toFixed`, `Math.round`, `Math.hypot`, a bare `Array.sort`, `%` on a value that can be negative, `x[-1]`,
`===` on arrays, or tests a container for truthiness (verified: only `pynum.ts` calls `toFixed`). The rules, one
line each:

* A number reaches the text only through `fmt0`, `fmt1`, `fmt2`, `fmt3`, `fmtHex2` or `pyRepr`. `f"{x:.1f}"` is
  `fmt1(x)`. Python rounds half to even on the exact binary value and `toFixed` does not.
* `round(x)` is `pyRound`, `round(x, n)` is `roundTo`, `sum` is `pySum(items, leadingInts)`, `hypot` is `pyHypot`
  (CPython's own algorithm, not V8's), `max` and `min` keep the first on ties (`pyMax`, `pyMin`).
* Keep the arithmetic exactly as written: floating point is not associative, so no hoisting, reordering or
  folding. `x ** 2` is `x * x`; other powers are `pyPow`.
* `sqrt` of a negative and division by zero raise as in Python (`pySqrt`, `pyAcos`, `pyDiv`), not a silent `NaN`.
* `a or b` and `a and b` return an operand: use `truthy()`. A `None` is `null`, never `undefined`.
* `sin`, `cos`, `atan2` and fractional powers come from V8. They can differ from Apple's or glibc's libm in the
  last bit and have never changed a printed digit (0 of 13.6 million numbers; `docs/ts-port-spike.md`, section 3).
* `docs/ts-port-guide.md` sections 3 to 5 are the full porting rules and the hazard ledger is
  `harness/ts_port/hazards.json`.

## How a part is added

A part is a function `(sk, p) -> string` that returns `""` when the character does not have it.

1. Write `fooBar(sk: Skeleton, p: CharacterParams): string` in the file of its role (`garments.ts`, `props.ts`,
   `face.ts`). Position it from `sk.*` anchors and `p.*` parameters, never fixed pixels. Numbers go through the
   kernel's formatters.
2. Export it from the domain's `parts-*.ts` table under its Python-style name (`_foo_bar`), which is how
   `render.ts` calls it.
3. Place it in `render.ts`, in the `slots` list at the z-order you want (`ordered` is built in list order). Give it
   a fresh slot number rather than renumbering, because the slot number is its stage name in the oracle.
4. A new field goes in the registry (`params.ts`) with a neutral default, and in `catalogue*.ts` if the web tool
   should offer it. A garment is worn when its colour is set, so a new garment is `Outfit.<name>_color`, `null` by
   default.
5. Run `npm run typecheck && npm test`, then the refresh scripts in `--check` mode, and look at the render
   (`node bin/render.ts --out ../out/tmp --preset satoko`, then view it): coordinates that are right in the
   arithmetic are routinely wrong on screen.

A new part that defaults to nothing changes no existing byte, which is what keeps the oracle green. New realism or
finish work goes behind `finish = "soft"` (`CLAUDE.md`).

**A hairstyle.** Write the five callables of the contract (`mass`, `hairline`, `fall_edge`, `tip_edge`, `strands`,
all in `core-head*.ts`; the rules are in `docs/architecture.md`), put the traced numbers in `core-head-tables.ts`,
and add a `Hairstyle` to `HAIRSTYLES` in `core-head.ts`. The parts that draw hair do not change. Give it a
`tip_range` if the cut ends on the head, and check the hair ceiling rule (`test/rules-hair.test.ts`).

**A character.** Add a `characterParams({...})` to `PRESETS` in `presets.ts` and run `./refresh-ref-out.sh`, which
re-renders every character through `bin/render.ts`. The `ref-out/` files, the README's table and the web gallery
follow from `PRESETS`.

**A command line option.** `bin/render.ts` takes the options in `parseArgs` at the top of `main()`; add the flag
there, and a case to `test/cli.test.ts`.

## The web tool

`../web/app.js` imports `js/web-bridge.js`, which is `src/web-bridge.ts` compiled. `../web-stage.mjs` (run by
`npm run build:web`, `../web-stage.sh` and the Pages workflow) compiles `src/` with `tsc -p tsconfig.web.json`
(it rewrites the `.ts` import specifiers to `.js`, which a browser needs) and copies `web/` and `ref-out/` beside
the output. Set `TSC` to use another tsc binary.
