# TS port: the full corpus and its coverage of the Python source

This is the Phase 2 oracle (`docs/ts-port-plan.md` section 5.1) as built: a corpus drawn from the dataclass fields,
a stage manifest for it, and a coverage gate for the Python package it runs. Everything is in
`harness/ts_port/`. Python is CPython 3.13.11 unless a section says otherwise; the source is the frozen
`src/anime_character_creator/` (tag v0.3.0). "Verified" below means a command was run and its output read; "inferred"
means read from the code and not measured.

## 1. What was built

| File | What |
| --- | --- |
| `corpus_full.py` | Deterministic generator (`random.Random(20261016)`), `load_full_case(entry)`, round-trip assertion. `write`, `check`, `stats`, `roundtrip`. |
| `corpus/full.json` | 7,662 cases `{"id", "p", "kw"}`, 1,900,444 bytes (cap 2.5 MB). `p` is a diff from the defaults. |
| `corpus/errors.json` | 333 entries: 272 render cases that raise (exact class and message), 61 urlstate operations (`params_from_dict`, `decode_params`) with their outcome. 88,951 bytes. |
| `manifest_full.py` | `build`, `verify [--all]`, `check-docs`, `show CASE STAGE`, `dump CASE...`. |
| `manifest/full.json` | Committed. Header `{python, platform, src_sha256, corpus_sha256, case_count, error_count}`, per case `[doc_sha256[:20], stages_digest[:20]]`, per error `[class, sha256(message)[:20]]`. 606,160 bytes (cap 1.5 MB). |
| `out/full-stages.json` | Not committed (`out/` is ignored). Every stage's sha256 and length per case, for localising a mismatch. 38 MB. |
| `coverage_gate.py` | Statement, line-arc and branch-outcome coverage with `sys.monitoring`; `run`, `probes`, `show`. |

JSON conventions the TS reader must honour. `1` and `1.0` are different values and stay different in the text, so read
the corpus with a parser that keeps the source text of a number (Node 22: `JSON.parse(text, (k, v, ctx) => ...)`
and `ctx.source`) or a small tokenizer. `-0.0` is written `-0.0`. A float JSON cannot spell is
`{"$float": "nan" | "inf" | "-inf"}`. A string may hold a lone surrogate (`"\ud800"`).

A lone surrogate in the wristband text makes the rendered document impossible to encode as UTF-8 in Python
(`'utf-8' codec can't encode character '\ud800'`; verified on `aud-text-lone_hi-si1`). The manifest therefore
hashes text as UTF-8 with `surrogatepass`. The TS side must produce the same string and hash it the same way (a lone
surrogate becomes `ED A0 80`).

## 2. Cases per category

7,662 cases that render, 333 that raise or are url operations. Case ids are `[A-Za-z0-9_-]+`; the first dash-separated
word is the category.

| Prefix | Cases | Content |
| --- | ---: | --- |
| `pre` | 50 | Every preset (20), both neutral bases and the three supporting characters, flat and soft. Roster members are presets (checked: every name in `ROSTERS` is in `PRESETS`). |
| `aud` | 418 | The seven things the test audit asks for (section 4). |
| `exp` | 117 | Each of the 13 expressions applied to three bases, flat and soft; flat also with `eyes_closed`. |
| `sw` | 2,345 | One field at a time, every field of `CharacterParams` (27 plain fields), `Outfit` (71) and `FaceStyle` (27). Neutral base with the fullest pools, a long-haired woman in a coat (flat) and a short-haired man (soft) with shorter pools. Booleans both ways and as `1`/`0`; optional colours None to set and set to None; enums over every name found in `HAIRSTYLES`, `BODY_TYPES`, `FINISHES`, `HAND_STYLES` (plus the legacy `grip`), `GRIP_STYLES`, `BELT_CUTS`, `SKIRT_CUTS`, `SLEEVE_CUTS`, `COLLAR_CUTS`, `BOOT_CUTS`, `COAT_CUTS`, `HAIR_CLIPS`; floats at the default, 0.0 and int 0, 1.0 and int 1, ties (0.125, 0.25, 0.375), 1e-9, the catalogue lo, hi and midpoint, a value half a span beyond either end, minus 1, plus and minus 20; non-finite floats and `-0.0` on every float field; ints over -20 to 20 plus 0.5, 1.0 and 2.5; wristband text over 13 strings. |
| `act` | 528 | A garment switched on (with the garment the catalogue says it requires), then its own knobs one at a time; each optional colour of a "kitted" character (every garment on) set to None; every cut name on every body, with a hat and in soft. |
| `rm` | 282 | The base-layer code: tunic off, boots off, both, with and without skirt, trousers and coat, on three bases; tunic off on every body with bust 0, 0.3, 1, chest 0, 1, underwear top both ways, boots on and off; arm angles with tunic off; the kitted character stripped; closed eyes beside other eye settings and ages. |
| `hr` | 919 | Every hairstyle x finish x hair_length (0, 0.2, 0.45, 1, 1.5) x hair_tip_color (None, pale, dark) x highlight_strength (0, 0.001, 0.5, 1, 2; flat only 1 and 0.5), hair colours rotating over five; tails and knots; soft with a hat, scarf, goggles, blindfold and clip on every cut. |
| `rnd` | 1,491 | 1,500 seeded random combinations (9 dropped as duplicates), 2 to 14 fields each, each field from a pool of in-range (62%), extreme (28%) and out-of-range (10%) values. 3 of the 1,500 raise and are in `errors.json`. |
| `sk` | 399 | Skeleton sweep: 360 seeded draws from body x height x frame x bust x waist_shift x face_age, with a hat on a quarter, plus each axis on its own and hat headroom per body and height. |
| `ro` | 107 | `id_prefix` in `""`, `p`, `a$&b`, `x\1`, `\g<1>z`, `é`, `a.b` on six characters, 18 more odd prefixes; `background` in 7 paints (white, `#fff`, red, `url(#g)`, empty, a string with a quote and `<&`, `rgba`). |
| `md` | 54 | `metadata=True`: every preset, every supporting character, 20 odd-value characters (ints for floats, -0.0, 5e-324, 1e22, 0.1+0.2, astral and markup text, non-finite floats, odd colours, the kitted character) and 12 sweep cases. 62 cases in all carry `metadata`. |
| `err` | 546 | Inputs that look wrong and render anyway: unknown names where a cut is not looked up, type confusion, colours of every odd shape, negative and huge numbers (cases that raise are in `errors.json`, 251 of them). |
| `cov` | 406 | Added for coverage (section 3). |

Of the 7,662 cases, 2,359 are soft finish, 62 carry `metadata`, 84 an `id_prefix`, 45 a `background`.
The 272 render errors, by class: 124 `ValueError`, 78 `TypeError`, 35 `KeyError`, 31 `AttributeError`, 4 `ZeroDivisionError`.
By source: 107 colour parse errors (`hex_to_rgb01` and its generator: a bad string raises `ValueError`, a non-string `AttributeError`),
40 `validate_finish` (finish not flat or soft, or a soft finish with a strength outside 0 to 2), 35 `KeyError` (an unknown hairstyle, body, cut or clip name),
8 `ValueError: math domain error` (`_fall_q`: `hair_length` below 0 on `long_parted` and `long_fringed` only; every other cut takes a negative length),
4 `ZeroDivisionError` (`height` = inf, -inf), and 78 `TypeError`s from a wrong type where a number or an int is needed
(`range()` in `_shoulder_bars`, a string times a float, `None` where a float is compared).
The 61 url operations: 32 `params_from_dict`, 29 `decode_params`; 29 of the 61 succeed (they record the sha256 of the re-encoded link).

The mini corpus was thin exactly where the spike said. In 68 cases `_underwear_top`, `_navel` and `_chest_lines` produced
output in 0; in the full corpus they produce output in 118, 268 and 58 of 7,662 (verified from the stage lengths):

| Layer | Mini (of 68) | Full (of 7,662) | Layer | Mini | Full |
| --- | ---: | ---: | --- | ---: | ---: |
| `_underwear_top` | 0 | 118 | `_shoulder_bars` | 2 | 86 |
| `_navel` | 0 | 268 | `_mask` | 2 | 214 |
| `_chest_lines` | 0 | 58 | `_ribbon` | 2 | 211 |
| `_glasses` | 2 | 169 | `_goggles` | 2 | 215 |
| `_blindfold` | 2 | 225 | `_headscarf` | 2 | 222 |

## 3. Coverage

Method. coverage.py is not installed in the venv, so `coverage_gate.py` runs every case of `full.json` and `errors.json` through the plain,
uninstrumented package with `sys.monitoring` `LINE` and `BRANCH` events. A statement is an AST statement that owns a line
with bytecode (a docstring is not one; a compound statement owns its header lines only). Three measures:

* **statements**: percent of the 3,531 statements of `character.py` (14,265 raw lines);
* **line arcs**: the coverage.py kind of branch: a conditional jump's outcome that lands on a different line than the jump.
  Not identical to coverage.py (a multi-line `and` chain counts each operand);
* **outcomes**: every outcome of every conditional jump, including `a if c else b`, `x and y`, `hypot(...) or 1.0` on one
  line. The strictest, and the one that matters for a port, because a TS ternary needs the same cases.

| File | Raw lines | Statements | Mini corpus (68) | Corpus a to h, before | Final | Line arcs, final | Outcomes, final |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `character.py` | 14,265 | 3,531 | 86.66% | 96.88% | **99.66%** (3,519) | 97.77% (613 of 627) | 96.59% (1,360 of 1,408) |
| `skeleton.py` | 455 | 139 | 82.01% | 100% | 100% | 93.33% (14 of 15) | 96.43% (27 of 28) |
| `colorutil.py` | 70 | 39 | 94.87% | 100% | 100% | 100% | 100% |
| `presets.py` | 1,547 | 60 | 98.33% | 98.33% | 100% | 100% | 87.50% (7 of 8) |
| `urlstate.py` | 114 | 41 | 29.27% | 100% | 100% | 100% | 85.71% (12 of 14) |
| `attribution.py` | 126 | 38 | 50.00% | 60.53% | 60.53% | 100% | 0 of 4 |

"Corpus a to h, before" is the generator as first written (categories pre, exp, sw, act, rm, hr, rnd, sk, ro, md, err and the url
operations): `character.py` 96.88% of statements, 94.42% of line arcs, 92.26% of outcomes (3,421 of 3,531
statements; `corpus_full.py write --skip aud,cov` reproduces it exactly). The final run is the committed corpus plus
three harness-only calls (below). The corpus alone, without those calls, is 99.58% (3,516).
The first run was below the 98% target (96.88%). One block of code accounted for 93 of the 110 missing statements (the raised
blazer sleeve, section 3.1). The audit cases alone close it (corpus a to h plus `aud`: 99.52%) and so do the coverage cases alone (plus `cov`: 99.58%);
the committed corpus has both.

`attribution.py`: the 15 uncovered statements are `sheet_metadata_block` and the three PNG functions
(`inject_png_text`, `png_with_metadata`, `sheet_png_with_metadata`). They are not part of an SVG render. Not in the corpus.

### 3.1 Functions that were uncovered, and the parameter combinations that reached them

Verified by generating the corpus with and without the added categories and diffing the sets of uncovered statements.

| Function (statements reached) | Reached by | Combination |
| --- | --- | --- |
| `_sleeve_cutaway` (42, and its helpers `px`, `curve`, `at`, `across`: 6), `_chain_until_y` (20), `_reversed_chain` (3), `_raised_shoulder` (5), `_raised_cuff` (10), `_without_raised_sleeves` (1), `_arm_pivot` (1), four statements of `_arms`, one of `_draw_cut`: 93 in all | `cov-blazer-arm-*` (and `aud-arm-risa-*`) | `coat_cut="blazer"` (the one cut with `arm_lines`) with any non-zero `right_arm_out` or `left_arm_out`, 0.07 to 90 degrees, on each body, with and without `sleeve_cut="wide"`. The first random search found it at `right_arm_out=0.07`: any swing at all raises the sleeve. |
| `_cuff_opening` (2: the two sign flips of the normals) | `cov-cuff-*` | `sleeve_cut="wide"` on `tall_slender` with `waist_shift` 1.5 (found by random search, reduced by deleting fields to those three; hand style is irrelevant). |
| `Expression.on`, `Expression.applied_to`, `presets.aged` (4 statements) | the "api" step of the gate | Not renders. The corpus stores the params an expression produced, not the expression, so these are called directly by the gate (`--no-api` leaves them out). |
| Branch outcome `_belt_drawn:11740` (keeper-pair belt with the tunic off) | `aud-pre-keiko-notunic` (audit item 5), `cov-keeper-tunic-*` | `belt_keeper_pair=True` (Keiko's dress belt) with `tunic_color=None`. The field sweeps could not reach it: it needs the belt colour, the keeper pair and the tunic off together. |
| Branch outcome `_hair_tip_tone:3638` (tip colour equal to hair colour) | `cov-tipsame-*` | `hair_tip_color == hair_color`, every cut, both finishes. |
| Branch outcome `_belt_drawn:11671` (`_cut_half_w_at` returns None: the belt row misses the coat's fills) | `cov-beltcoat-*` (verified: that block alone reaches it) | A belt over `open_jacket`, `blazer` or `lab_coat` with `waist_shift` from -3 to 5 and `belt_scale` 1 to 3. |

Two reachable gaps were found by a random search rather than by reading: the `_cuff_opening` flips (a geometry
interaction: a sleeve cut on a body whose belt line has moved) and `_belt_drawn:11740`. After the final corpus, 80,000 more
random draws (seeds 1, 7 and 11; 2 to 40 fields each; `probe2.py` in the session scratch, not committed) reached no new statement or outcome. That is
evidence the remaining gaps are not reachable by a combination of the fields, not proof.

### 3.2 Uncovered statements of `character.py` (12)

| Line | Function | Why not covered | Evidence |
| --- | --- | --- | --- |
| 1992 | `_straight` | Dead code: the function is defined twice, at 1990 and at 2697. The second replaces the first at import; every caller runs `_lerp(a, b, 0.5)`, not `(a + b) / 2`. **The port must port the second.** | `probes`: `functions_defined_twice = {'_straight': [1990, 2697]}` (verified). |
| 3723 | `_hair_tip_lines` | `if length == 0: continue`: a tip line of zero length. | Shortest tip line over 524 calls is 0.38 px (verified); all eight traced tips have a non-zero `dx` (read). Dead for the present tables. |
| 5655, 5657, 5662 | `_interp` | A value outside the knot range, and the loop falling through. The values are points of the traced cuts, a constant. | Over 621,143 calls the closest a value comes to the first knot is 0.001 and to the last knot 0.0026 (verified). Dead unless a cut gains a point beyond the landmarks. |
| 5667, 5669 | `_interp_flat` | The same two guards. | Closest approach 0.001 to the first knot, 1.282 to the last (verified). |
| 5948 | `_cutaway_side_lines` | `return set()` when there is no coat or no cut. Its only caller (line 5991) runs inside a traced coat. | Zero hits in 80,000 extra draws (verified); the caller's guard is read, so the reason is inferred. |
| 7319 | `_beard` | `if _BEARD_LIP_W <= 0: return mass`. The constant is 2.3. | Read from the module (verified). Dead constant guard. |
| 13312 | `_lock_shape` | A span under 0.05. | Shortest span over 40,620 calls is 0.52 (verified). |
| 13329 | `_lock_shape` | Fewer than 3 sample points. | Fewest over 40,620 calls is 15 (verified). |
| 13378 | `_soft_locks` | `raise ValueError(...)` for a lock role other than shadow or lit. | The roles in the lock tables of the six cuts that have locks are `lit` and `shadow` only (verified). Dead. |

So 11 of the 12 are dead by data or by a constant; 1 is the shadowed definition. None is waiting for a parameter combination.
After adding the three harness-only calls, 12 statements remain of the 15 that the corpus alone leaves.

### 3.3 Uncovered line arcs (14) and outcomes (48)

The 14 line arcs (`3722->3723`, `5654->5655`, `5656->5657`, `5658->5662`, `5666->5667`, `5668->5669`, `5798->5819`, `5947->5948`, `7318->7319`, `11792->11802`, `12619->12623`, `13311->13312`, `13328->13329`, `13371->13378`) are the same places as 3.2 and the table below: all fourteen are in the first rows of it.

The 48 outcomes, grouped. "Inferred" means not measured:

| Class | Count | Sites | Reason |
| --- | ---: | --- | --- |
| A constant or a table makes one side impossible | 16 | `_long_scaled:1485`, `_long_line:1499` (`span` is `base_tip - 0.72`), `_hair_defs:3662` (no cut has `front_shade` without `strands`), `_hair_defs:3678` (every cut yields a clip: all 8 have strands or an underside), `_hair_tip_lines:3722`, `_interp:5654, 5656, 5658`, `_interp_flat:5666, 5668`, `_coat:6998` (`_COAT_BUST_BOW` is 1.0), `_beard:7318`, `_lock_shape:13311, 13328`, `_soft_locks:13371`, `_soft_locks.add:13360` (`_lock_shape` never returns an empty path) | Measured or read from the module: `_interp`, `_lock_shape`, `_hair_tip_lines`, `_beard`, `_COAT_BUST_BOW`, the cut table (`probes`). |
| `x or 1.0` or `if span else 0.0`: a zero length | 6 | `_bust_fold:4326`, `_bare_breasts:4441`, `_chest_lines:4549`, `_lock_normals:13273`, `_quad_crossing:4004` (`abs(qa) < 1e-9`, a straight quadratic), `_head_edge_x:12057` | Geometry guards. Not reached by the corpus or by 80,000 extra draws; inferred. |
| Guard repeated by the caller, or implied by an earlier operand | 12 | `_sleeve_under_cap:3870` (`not _traced_coat` is false only with a coat, which an earlier operand excluded), `_arms:10048` (`long_sleeve` needs `coat_sleeves`, which the operand before takes), `_cutaway_side_lines:5947` x2, `_raised_shoulder:5780`, `_raised_cuff:10248`, `_soft_lock_layers:13399`, `_sleeve_cutaway:5850` x2 (asserts), `_hand_centre:8357`, `_traced_placement:10658` (a swing is read only for the fist grip, which is the viewer's left hand), `_bare_breast_spine:4402` (`_sleeve_under_cap` is false wherever the bare breasts are drawn) | Read. For the two side cases `probes` measured the sides passed: `hand_centre` -1 only. |
| Logically impossible | 3 | `_belt_drawn:11792, 11802, 11803` | `show_tie and show_buckle` needs `apron_color` both None and not None. Truth table over the four combinations in `probes`: `belt_both_shown = False` (verified). |
| Default argument never used | 4 | `_eye_lash:12613, 12619` (`reach` is always passed: 0 of 15,034 calls, verified), `render_character:14074` (`p=None`), `14076` (`sk` passed in) | The corpus never calls `render_character(None)` or hands it a `Skeleton`. A port that exposes `sk` needs its own test. `skeleton.build_skeleton:371` (`hair_margin` passed) is the same kind. |
| Geometry that never crosses | 5 | `_bust_bulge:5602` (`plain is None`), `_cut_half_w_at:6045` (a horizontal piece), `_hair_edge_x:12097`, `_sleeve_cutaway.across:5871`, `_chain_until_y:5798` (loop never runs out: 0 of 147 calls, verified) | Not reached by 80,000 extra draws, except the last, which is measured. Inferred. |
| Iterator never exhausted | 2 | `_square_wrist` and `_jaw_track` generator expressions (`next(...)` without a default) | The StopIteration side is an error no case reaches. |
| Not a render | 4 | `presets:1352` (the module-level `assert`), `urlstate:67`, `urlstate:104` (the false side of an `except` test), `skeleton:371` | `build_skeleton`'s `hair_margin` is for direct callers. |

The 48 outcomes of `character.py` are the first seven rows (16 + 6 + 12 + 3 + 4 + 5 + 2 = 48); the last row is the other four files.

## 4. The test audit's seven items (`docs/ts-port-test-audit.md` section 6)

All are in `full.json` or `errors.json` with the `aud-` prefix; 418 cases render, 11 raise.

| # | Ids | What |
| --- | --- | --- |
| 1 | `aud-cat-<garment>-<field>-lo|hi` (49 with every select option), `aud-cat-face-<field>-lo|hi`, `aud-cat-face-scar_side-{0,m1,1}`, `aud-cat-top-<field>-lo|hi` (height, face_age, bust, chest, waist_shift, highlight_strength in soft), `aud-cat-top-hair_length|hair_tail-lo|hi-<hairstyle>` | Catalogue lo and hi of every garment range with its colour on (and its `requires`), every face range, `hair_length` and `hair_tail` on every cut, every scar option. 113 cases. |
| 2 | `aud-bg-absent`, `aud-bg-null`, `aud-bg-{white,hex3,red,url,empty}` and `-c` (neutral base) | `background` absent, None, empty and four paints. |
| 3 | `aud-text-<n>-s{1,m1}`, `-soft`, `aud-text-<n>-lindita`, `aud-text-<n>-md` | 23 strings in `Outfit.wristband_text`: `</text><script>...`, quotes, entities, `<`, `>`, emoji, a ZWJ sequence, 400 characters, empty, a space, **lone surrogates** (`\ud800`, `ab\udc00cd`), NUL, newlines, CJK, combining, RTL, BOM, an escape code, backslash templates, `$&`. Each on both wrist sides and in soft; four with `metadata`; four on Lindita. 77 cases. |
| 4 | `aud-height-bare-<h>-{flat,soft}`, `aud-height-clothed-<h>` | `height` 0.79, 0.7999, 0.8, 0.8001, 0.81, 0.9, 0.9999, 1.0, 1.0001 on a figure with every optional garment colour None; and clothed. |
| 5 | `aud-pre-<name>-{notunic,notunic-notrou,noboots,trouoff}`, `aud-pre-<name>-age{0p0,1p0,2p0}-eye`, `aud-chiyo-<hairstyle>-{flat,soft}`, `aud-gaze-{risa,satoshi}-<g>`, `aud-arm-{risa,keiko}-*` | Every preset with tunic off, tunic and trousers off, boots off; every preset at `face_age` 0, 1, 2 with `eye_size` 1.05 and `eye_width` 1.10; Chiyo on all 8 cuts; gaze -1, -0.8, 0, 0.8, 1 on Risa and Satoshi; `right_arm_out` 128, and 125 with `left_arm_out` 125, on Risa and Keiko. |
| 6 | `aud-hs-flat-*` (12, all render), `aud-hs-soft-*` (16 values: 11 raise and are in `errors.json`; 3 render under this id and 2 more are the identical catalogue cases `aud-cat-top-highlight_strength-lo|hi`) | Flat with 0, 0.3, 9.0, -1, -1.0, 2.1, -0.1, 1e300, nan, inf: renders. Soft with -0.1, 2.1, `"1"`, None, True, False, nan, 9.0, -1, `[]`, inf: `ValueError: highlight_strength must be between 0 and 2, not ...`. Soft with 0, 0.0, 0.3, 2, 2.0 renders (all five are in the corpus). |
| 7 | `aud-tip-<cut>-{pale,peach,dark}` (15), `aud-tip-katherina-<cut>` (8) | Soft finish with `hair_tip_color` on the five authored cuts, and on Katherina with every cut including the three of `test_a_tip_colour_on_a_big_preset_stays_within_the_budget` (`short_layered`, `short_crop`, `long_parted`, tip `#f8b890`). |

The additions did not force the 2.5 MB cap up: `full.json` is 1.90 MB.

## 5. The oracle manifest

* **Instrumented equals plain, for every case.** `build`, `verify` and `check-docs` render each case through `instrument.render_stages` (unchanged)
  and compare the sha256 of the document with a second interpreter that never installs the hook (`manifest_full.py _plain`, started as a subprocess).
  Result: 7,662 of 7,662 documents equal; 333 of 333 error and url outcomes (class and message) equal.
  Commands (from the worktree root; `PY` is the dev venv python):
  `PYTHONDONTWRITEBYTECODE=1 $PY harness/ts_port/manifest_full.py build` then `... verify`, `... check-docs`.
* **Determinism.** `build` run with 8 worker processes and again with `MANIFEST_WORKERS=1`: `cmp` reports `manifest/full.json` and `out/full-stages.json` byte-identical (606,160 and 38,222,466 bytes). `corpus_full.py check` reports both corpus files unchanged on a re-derivation.
  No stage varied between runs.
* **Round trip.** `corpus_full.py write` rebuilds every case from its JSON text and compares field by field with `same()` (type and repr, so 1 against 1.0 and 0.0 against -0.0 count): 7,662 of 7,662 equal; `corpus_full.py roundtrip` repeats it from the files on disk, including the 272 error cases.
* **Time.** The whole corpus (7,995 renders) runs in 12.7 s under the coverage hook; `build` takes 4.8 s on 8 processes. The slowest single render is 15 ms (the first, `pre-katherina-flat`, 61 ms including warm-up).

## 6. Cross-version check

`manifest_full.py verify --all` under three interpreters against the manifest built on 3.13.11:

| Interpreter | Cases compared | Different documents | Same document, different stages | Different error outcomes |
| --- | ---: | ---: | ---: | ---: |
| CPython 3.13.11 | 7,662 + 333 | 0 | 0 | 0 |
| CPython 3.12.12 | 7,662 + 333 | 0 | 0 | 0 |
| CPython 3.11.14 | 7,662 + 333 | 0 | 0 | 0 |

No case differs. The 3.12 change to `sum()` of floats is real and is exercised: wrapping `sum` at its call sites, 55,201 calls
on the corpus are all over floats and 36,247 of them (65.7%) return a different bit pattern from a left-to-right sum on 3.12 and 3.13; on 3.11 none do. The
documents are still equal because every one of these sums is later printed at one or two decimals or compared with a margin.
The sites reached: `_sleeve_cutaway:5913` (147 calls, 86 differ), `_principal:10601-10605` (2,772 each, 2,047 to 2,480 differ), `_lock_side:13281` (40,620 calls, 24,294 differ), `_mirrored_y:13528` (118, 0),
`_familiar:13996-13997` (228 each, 114 and 228 differ). The eleventh site, `_KOU_MOUTH` at 13923, runs once at import: it gives 3 on 3.13.11, 3.12.12 and 3.11.14. So the answer to "which sum() site is responsible" is none, on this corpus.
A smaller risk remains for values that sit exactly on a rounding tie after the sum; the corpus found none.

One corpus entry was removed because it differed across versions: `decode_params` of a 5,000-deep nested JSON array gives
`ValueError: not a valid character link: not an object` on 3.13 and a `RecursionError` message on 3.11. It is a 100-deep array now (same text on all three). Python's recursion limit is not something a port should copy.

## 7. Things worth knowing

* `_straight` is defined twice in `character.py` (lines 1990 and 2697); the second is the live one (section 3.2).
* A lone surrogate in `wristband_text` renders without error in Python but the result cannot be written to a file as UTF-8 (section 1).
* `hair_length` below 0 raises `math domain error` on `long_parted` and `long_fringed` only; the other six cuts take it.
* `highlight_strength` is not validated in the flat finish: nan, inf, 1e300 and -1 render.
* Float parameters accept ints and the document differs (`hair_length=1` against `1.0`): the corpus has such cases and the TS side has to keep the int/float distinction in its loader.
* Colour strings are parsed by `int(s[i:i+2], 16)` after `lstrip("#")`, so `##ff0000`, `ff8800`, upper case, 8 digits, blanks and Arabic-Indic digits are accepted; they are in the corpus (`sw-C-*-s<hash>`, `rnd`, `md-odd-odd_colour`). Anything shorter than 6 characters raises.
* Soft finish also changes `stroke-width` of the whole document (`_soft_stroke_widths`), so most soft cases exercise that regex.

## 8. What is not covered

* Coverage is of this repository's Python, with the corpus as the only driver. The TS half is the mutation gate of the plan, not built here.
* `render_character(p=None)`, a caller-supplied `sk`, `build_skeleton(hair_margin=...)`, `render_sheet`, `render_cover`, `generate.py`, the PNG functions of `attribution.py` and the `comic` package are not in the corpus.
* urlstate: only 61 operations, 32 failures; success round trips are covered through `metadata=True` (62 cases encode a URL) and the 29 successful operations (hash of the re-encoded link). There is no exhaustive link fuzz and no companion `frames`/`patch`/`base`/`schema` ops.
* Branch numbers use my own definitions (section 3) and are not comparable with coverage.py's. `sys.monitoring` needs CPython 3.12 or later; the gate was run on 3.13.11 only.
* One machine (macOS arm64). The manifest is a statement about this libm. A second platform is the plan's Gate 2.

## 9. Commands

```
PY=/Users/hanssen.henrik/git/self-study/anime-character-creator-dev/.venv/bin/python
export PYTHONDONTWRITEBYTECODE=1
$PY harness/ts_port/corpus_full.py write            # regenerate corpus/full.json and errors.json (7,662 + 333)
$PY harness/ts_port/corpus_full.py check            # unchanged on re-derivation
$PY harness/ts_port/corpus_full.py roundtrip        # JSON text rebuilds the params exactly
$PY harness/ts_port/manifest_full.py build          # manifest/full.json and out/full-stages.json (+ doc check)
$PY harness/ts_port/manifest_full.py verify --all   # also under python3.12 and python3.11 (cross-version)
$PY harness/ts_port/manifest_full.py show CASE STAGE
$PY harness/ts_port/coverage_gate.py run            # --no-api, --skip aud,cov, --corpus mini, --dir D
$PY harness/ts_port/coverage_gate.py probes         # the measurements behind section 3.2
```
