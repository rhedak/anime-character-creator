# How the recorded fixtures were updated when Risa moved onto the adult body (2026-10-21)

The `risa` preset is now a different character in every respect (the adult woman's body, her own head cut, face, bust and every garment: `docs/risa-adult-plan.md`), so everything recorded from the old one moved. The
Python the fixtures were recorded from is gone and the change is not a field added to every character, so, unlike `../golden-updates-elbow/` and `../golden-updates-stage7/`, the new values are not derived from the old
by a rule: they are computed from the new code, in the way the tests read them. `upd_fixtures.ts` does it (run from `ts/`: `node ../harness/ts_port/golden-updates-risa-adult/upd_fixtures.ts`) and prints what it checked.

| file | what changed | how |
|---|---|---|
| `ref-out/risa.svg`, `risa.png`, `on-white/risa.png` | the drawing | `./refresh-ref-out.sh` (24 renders, 1 changed: only `risa`) |
| `ref-out/catalogue.json`, `ts/fixtures/catalogue-expected.json` | the hairstyle and clip entries added earlier (`../golden-updates-risa/README.md`) | already recorded then |
| `ts/fixtures/presets.json` | the `risa` entry under `presets` (its `dict`, and its `json`, the text with the int and float spellings) | the entry's text only is replaced (the file keeps `1.0`-style spellings that a JSON round trip would lose); every other preset and section checked unchanged |
| `ts/fixtures/pages.json` | three cases that draw her: `cover --preset risa`, `sheet --roster risa`, `sheet --members risa,...` (their byte count and sha256) | each run as `pages.test.ts` runs it, `ACC_LOCAL_DIR` pointing at nowhere |

Tests that used Risa as a chibi, not as a character, were pointed at the old definition (`RISA_TALL_SLENDER`, through `FIXTURES` in `ts/test/rules-util.ts`): the soft-finish clump tests (she was the only preset with the `long_fringed`
cut and its locks), the skeleton, garment and catalogue-rule tests that need the tall slender body. The bust-slider test no longer holds the adult woman's `bust` (an offset from her traced bust, hidden in the page) to the
slider's range, and `cli.test.ts`'s soft-finish options test draws `satoko`, since the strength scales hair clumps that Risa's adult cut has none of.

Her drawing is now 350 KB (Franzi's is 184 KB): the hair silhouette is 481 segments, with 90 strand lines, and the cover and the sheets that hold her grew with it. It is inside the adult budget (400 KB, `rules-soft-locks`).
`tall_slender` and the traced chibi cuts are **not removed** (they are in the recorded Python calls, `harness/ts_port/fixtures/calls/`, which would need rewriting): that is a separate decision.
