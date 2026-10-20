# How the golden files were updated for the elbow fields (2026-10-20)

The owner asked for two new top-level fields on `CharacterParams`, `right_elbow` and `left_elbow` (degrees, 0 neutral: the bend of a raised arm's forearm on the adult woman's body). Every
character now carries them, so every recorded text that holds a character changed. The goldens under `ts/fixtures/` and `harness/ts_port/` were recorded from the Python, which is gone, so,
as for `bodice_color` (`../golden-updates-stage7/README.md`), they were changed by mechanical rules from their old content, never regenerated from the new code, and each result was checked
against what the new code draws.

`elbowfix.py` holds the rules:

* **DICT**: a `CharacterParams` as a dict, in the registry's order: `right_elbow`, `left_elbow` (0.0) right after `left_arm_out`.
* **TEXT**: its key-sorted compact JSON text (also inside JSON strings, with escaped quotes): `left_elbow` sorts right after `left_arm_out`, `right_elbow` right after `right_arm_out`.
* **LINK**: a character link's `c=` value is the base64url of that text: decoded, given the fields by TEXT, checked to differ by those two fields alone, encoded again.

What each updater does (run from `ts/`; the ones that need the old outputs use the tree at `$TMPDIR/head`, `git archive HEAD ts` of the commit before the change, which each old-output script first checks
reproduces the recorded golden):

| updater | file | change | checked against |
|---|---|---|---|
| `upd_presets.py` | `fixtures/presets.json` | DICT and TEXT in every preset, base and supporting character, TEXT in the defaults | the tests that compare the new code's presets deep-equal |
| `upd_model.py` (`modelold.ts`) | `fixtures/model.json` | the 78 expression hashes: sha256 of the old text with the fields added | the model test |
| `upd_urlstate.py` (`urlold.ts`) | `fixtures/urlstate.json` | text, link and url hashes for 373 cases, the hashes of 118 decoded links, the base-url cases | the url tests |
| `upd_metadata.py` | `fixtures/metadata.json` | the link in each of the 70 metadata blocks | the attribution test |
| `upd_errors.py` (`errold.ts`) | `harness/ts_port/corpus/errors.json` | the hash of the link each succeeding case encodes to, by text substitution | the errors test |
| `upd_calls.py`, `upd_calls2.py` | `harness/ts_port/fixtures/calls/*.json` | 311 recorded characters (the two fields after `left_arm_out`, spelled as the recorder spells 0.0), and the results of `character_url`, `encode_params` and `params_to_dict` | the calls tests |
| `upd_pages.py` | `fixtures/pages.json` | the four pages that carry metadata: the old tree's page with its links fixed, which must equal the new tree's page | the pages tests |
| `upd_manifest.py` (`stagesold.ts`) | `harness/ts_port/manifest/full.json` | the 62 documents with metadata: the old document with its links fixed, hashed as the corpus hashes (surrogate-pass UTF-8) | the stages test |

One test pinned the number of fields (`urlstate.test.ts`, 29, now 31) and was changed by hand. `ref-out/` and the catalogue did not move (no metadata there, and the elbow is not a page control). The tests were
red before each update and green after it. The scripts are kept as the record and are not meant to run again.
