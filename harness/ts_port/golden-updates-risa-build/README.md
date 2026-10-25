# How the recorded fixtures were updated when Risa took the slender build (2026-10-24)

`RISA` in `ts/src/presets.ts` now sets `body_build: "slender"` (`ts/src/body-adult-build.ts`, `docs/risa-polish-plan.md` stage 2): her body's outline is warped to her bikini reference's
proportions, and everything drawn on it follows, so her drawing changed on purpose, with the owner's say (the plan's decision 2: only Risa may change). The field itself was added first, with
every drawing unchanged (`../golden-updates-build/README.md`). As when she moved onto the adult body (`../golden-updates-risa-adult/README.md`), the new values are computed from the new code
in the way the tests read them, not derived from the old ones by a rule.

| file | what changed | how |
|---|---|---|
| `ref-out/risa.svg`, `risa.png`, `on-white/risa.png` | the drawing | `./refresh-ref-out.sh` (24 renders, 1 changed: only `risa`) |
| `ts/fixtures/presets.json` | the `risa` entry under `presets` (its `dict` and its `json` text: `body_build` is `"slender"`) | `upd_fixtures.ts` (run from `ts/`): the entry's text only is replaced; every other preset and section checked unchanged |
| `ts/fixtures/pages.json` | the three cases that draw her: `cover --preset risa`, `sheet --roster risa`, `sheet --members risa,...` | `upd_fixtures.ts`: each run as `pages.test.ts` runs it, `ACC_LOCAL_DIR` pointing at nowhere |

`upd_fixtures.ts` is a copy of `../golden-updates-risa-adult/upd_fixtures.ts` (kept there as its record) that keeps `pages.json`'s last newline. Eight tests were red after the preset
switch and before the update (her render, her preset entry, her three pages, and the two web-bridge tests that read them), and the whole suite is green after it.

`upd_fixtures.ts` is run again, with `./refresh-ref-out.sh`, for each later change of her drawing in the campaign (stages 2 to 5 of the plan: the arm fix, the uniform's refit, the front locks,
and the `fine` line style, `line_style: "fine"` in her preset); each time only her entry and her three pages move.
