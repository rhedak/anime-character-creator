# How the golden files were updated for the line_style field (2026-10-25)

The owner picked a line style for Risa (`docs/risa-polish-plan.md`, stage 5: variant c of `harness/risa_adult/line_variants.ts`), made a top-level field on `CharacterParams`, `line_style` (a
nullable string, null the house lines: `LINE_STYLES` in `ts/src/character.ts`), on the condition that only Risa's drawing changes. Every character now carries it, so every recorded text
that holds a character changed, while no drawing did. As for `body_build` (`../golden-updates-build/README.md`), the goldens were changed by mechanical rules from their old content, never
regenerated from the new code, and each result was checked against what the new code draws. Risa's switch to the style is recorded with her other changes
(`../golden-updates-risa-build/README.md`).

`linefix.py` holds the rules:

* **DICT**: a `CharacterParams` as a dict, in the registry's order: `line_style` (null) last, right after `highlight_strength`.
* **TEXT**: its key-sorted compact JSON text (also inside JSON strings, with escaped quotes): `line_style` sorts right after `left_elbow` and before `outfit`.
* **LINK**: a character link's `c=` value is the base64url of that text: decoded, given the field by TEXT, checked to differ by that field alone, encoded again.

The updaters are the `body_build` ones with these rules (run from `ts/`; the ones that need the old outputs use the tree at `$TMPDIR/head`, `git archive HEAD ts` of the commit before the
change, with `harness/ts_port` and `ref-out` of the same commit beside it at `$TMPDIR`, which each old-output script first checks reproduces the recorded golden: 78 expressions, 373 encode
cases, 29 link outcomes and 63 documents did):

| updater | file | change |
|---|---|---|
| `upd_presets.py` | `fixtures/presets.json` | DICT and TEXT in 26 entries, TEXT in the defaults |
| `upd_model.py` (`modelold.ts`) | `fixtures/model.json` | the 78 expression hashes |
| `upd_urlstate.py` (`urlold.ts`) | `fixtures/urlstate.json` | 373 encode cases, 118 decoded links, the base-url cases |
| `upd_metadata.py` | `fixtures/metadata.json` | the link in each of the 70 metadata blocks |
| `upd_errors.py` (`errold.ts`) | `harness/ts_port/corpus/errors.json` | the 29 succeeding cases' link hashes |
| `upd_calls.py`, `upd_calls2.py` | `harness/ts_port/fixtures/calls/*.json` | 311 recorded characters in 114 files (the field after `highlight_strength`, a bare `null`), and the results of `character_url`, `encode_params` and `params_to_dict` |
| `upd_pages.py` | `fixtures/pages.json` | the 4 pages of 22 that carry metadata |
| `upd_manifest.py` (`stagesold.ts`) | `harness/ts_port/manifest/full.json` | the 62 documents with metadata |

One test pinned the number of fields (`urlstate.test.ts`, 32, now 33) and was changed by hand. The mini corpus holds characters recorded before the field, without it, so `lineStyleOf` reads
a missing one as none. The tests were red before the update (20 failing) and green after it. The scripts are kept as the record and are not meant to run again.
