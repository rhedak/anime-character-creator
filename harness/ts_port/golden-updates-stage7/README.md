# How the golden files were updated for stage 7 (2026-10-19)

Stage 7 of `docs/python-removal-audit.md` added Franzi to `PRESETS`, folded the adult body and her cut into `BODY_TYPES` and `HAIRSTYLES`, and added the outfit field
`bodice_color`. The goldens under `ts/fixtures/` and `harness/ts_port/` were recorded from the Python, which is gone, so they were changed by mechanical rules from their old
content, never regenerated from the new code:

* **A new entry** (Franzi in `presets.json`, the catalogue text and sha): appended, with a check that nothing else moved (`gold7a.ts` computes the new values; the catalogue text may only gain lines).
* **A dict or a key-sorted JSON text of an outfit** (`rawfix.py`): `"bodice_color": null` inserted after `strap_color` (dict) or between `blindfold_color` and `boot_color` (sorted text). Applied to `presets.json` and the recorded calls.
* **A character link** (`linkfix.py`): the `c=` value is base64url of the key-sorted JSON text, so it is decoded, given the field by the same sorted-text rule, checked to differ from the old by that field alone, and encoded again. Applied to `metadata.json`, `urlstate.json`, the recorded results of `character_url` and `encode_params`, and `pages.json`.
* **A hash of a text that contains a link or an outfit** (`urlold.ts`, `modelold.ts`, `errold.ts`, `stagesold.ts`, `urlnew.py`): the old text was produced by the TypeScript as of the commit before the change (`git archive HEAD ts`), checked to hash to the old golden (so it is what the Python drew), given the rule, and hashed again.

The tests were red before each update and green after it. The scripts use `$TMPDIR/head` (that archive) and are kept as the record; they are not meant to run again.
