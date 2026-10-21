# How the catalogue golden was updated for Risa's adult hair (2026-10-20)

The adult woman has a second cut, `long_straight_fringed` (Risa's, `docs/risa-adult-plan.md`), and the hair clip a new shape, `bracket`. Both are new entries in the catalogue's
lists, so the committed `ref-out/catalogue.json` and its recorded copy `ts/fixtures/catalogue-expected.json` moved. The Python that recorded the fixture is gone, so the update is
mechanical, not a regeneration of the recorded text:

* `ref-out/catalogue.json` was re-emitted by `./refresh-catalogue.sh`; `git diff` shows only added lines: one hairstyle entry (`long_straight_fringed`, "Long, straight, blunt fringe") and one hair clip entry (`bracket`, "Bracket frame"). Nothing else moved, and `body_ignores` is unchanged (`hairstyle` stays hidden on the adult woman, now through `BODY_HIDDEN_EXTRA`).
* `ts/fixtures/catalogue-expected.json`: its `text` is that file, its `sha256` and `bytes` are recomputed from it, and the other keys (the starting points, the hand and grip styles, the outfit field names) are untouched. Written with the file's own formatting (`indent=1`).

The tests that were red before the update (`catalogue.test.ts`, `cli.test.ts`) are green after it. The owner's call on moving the catalogue fixture is noted in `ts/src/catalogue-tables.ts` (`BODY_HIDDEN_EXTRA`); this change moves it for these two entries only.
