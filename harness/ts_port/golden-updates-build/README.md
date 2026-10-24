# How the golden files were updated for the body_build field (2026-10-24)

The owner allowed a new top-level field on `CharacterParams`, `body_build` (a nullable string, null the traced body: the adult woman's builds, `ts/src/body-adult-build.ts`,
`docs/risa-polish-plan.md` stage 2), on the condition that only Risa's drawing changes. Every character now carries it, so every recorded text that holds a character changed, while no
drawing did (a skeleton without a build has no `adult_build` key, so the recorded skeletons are untouched). As for the elbow fields (`../golden-updates-elbow/README.md`), the goldens were
changed by mechanical rules from their old content, never regenerated from the new code, and each result was checked against what the new code draws. Risa's own switch to the build is a
separate change, recorded in `../golden-updates-risa-build/README.md`.

`buildfix.py` holds the rules:

* **DICT**: a `CharacterParams` as a dict, in the registry's order: `body_build` (null) right after `body`.
* **TEXT**: its key-sorted compact JSON text (also inside JSON strings, with escaped quotes): `body_build` sorts right after `body`, which no other key starts with.
* **LINK**: a character link's `c=` value is the base64url of that text: decoded, given the field by TEXT, checked to differ by that field alone, encoded again.

The updaters are the elbow ones with these rules (run from `ts/`; the ones that need the old outputs use the tree at `$TMPDIR/head`, `git archive HEAD ts` of the commit before the change,
with `harness/ts_port` and `ref-out` of the same commit beside it at `$TMPDIR`, which each old-output script first checks reproduces the recorded golden):

| updater | file | change | checked against |
|---|---|---|---|
| `upd_presets.py` | `fixtures/presets.json` | DICT and TEXT in 26 entries (presets, neutral bases, supporting characters), TEXT in the defaults | the presets tests |
| `upd_model.py` (`modelold.ts`) | `fixtures/model.json` | the 78 expression hashes: sha256 of the old text with the field added | the model test |
| `upd_urlstate.py` (`urlold.ts`) | `fixtures/urlstate.json` | text, link and url hashes for 373 cases, the hashes of 118 decoded links, the base-url cases | the url tests |
| `upd_metadata.py` | `fixtures/metadata.json` | the link in each of the 70 metadata blocks | the attribution test |
| `upd_errors.py` (`errold.ts`) | `harness/ts_port/corpus/errors.json` | the hash of the link each of the 29 succeeding cases encodes to, by text substitution | the errors test |
| `upd_calls.py`, `upd_calls2.py` | `harness/ts_port/fixtures/calls/*.json` | 311 recorded characters in 114 files (the field after `body`, spelled as the recorder spells None, a bare `null`), and the results of `character_url`, `encode_params` and `params_to_dict` | the calls tests |
| `upd_pages.py` | `fixtures/pages.json` | the 4 pages of 22 that carry metadata: the old tree's page with its links fixed, which must equal the new tree's page | the pages tests |
| `upd_manifest.py` (`stagesold.ts`) | `harness/ts_port/manifest/full.json` | the 62 documents with metadata: the old document with its links fixed, hashed as the corpus hashes | the stages test |

One test pinned the number of fields (`urlstate.test.ts`, 31, now 32) and was changed by hand. `ref-out/` and the catalogue did not move (no metadata there, and the build is not a page
control). The tests were red before the update (19 failing) and green after it. The scripts are kept as the record and are not meant to run again.
