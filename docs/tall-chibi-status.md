# Tall chibi status

The record for `tall-chibi-plan.md`, newest first.

## RESUME (for a fresh context)

- **Now:** R2 done; R3 next (the owner said to keep going autonomously,
  stopping only for input; R4's study is the next stop).
- **Tree:** clean at `2e549d2` when the plan was written.
- **Invariant:** every tall-chibi render byte-identical through R1 to R3
  (`./refresh-ref-out.sh --check`); only R4 may move a figure.
- **Owner sign-off** after each step; commits one line, no trailer.

## Scoreboard

| step | state | acceptance met |
| --- | --- | --- |
| R0 inventory | done, signed off | inventory below, each item classed and stepped |
| R1 remove the choices | done, signed off | `ref-out/` and bases byte-identical; old link test; browser checked |
| R2 retire the realistic outputs | done | `ref-out/` chibi, bases, catalogue unchanged; 606 passed |
| R3 delete the dead code | | |
| R4 the height slider | | |
| R5 docs and the downstream | | |

## Findings, newest first

### R2: the realistic outputs retired (2026-09-26)

`ref-out/real/` removed (34 files); `presets.REALISTIC_REFS` and its export
removed; `refresh-ref-out.sh` renders the one build (`builds=chibi`), drops
the realistic list and its checks, no longer passes `--build`, and reports
anything left under `ref-out/real/` as an orphan. The CLI's `--build` and
`--heads` removed from `generate.py`, and `--build` and the `build` field
from `sheet.py` and `cover.py`, which now call `skeleton_for(character)`: the
character's own `heads` is the same 2.4. The `gap-analysis` skill moved to
`harness/gap_analysis_skill/` as a record (`docs/gap-analysis.md` kept).
Tests: the snapshot set is the chibi only; the leftover check covers
`real/`; the cover test is no longer parametrized; the CLI test asserts the
retired options fail. The tests parametrized over `BUILDS` still run both
builds, since the realistic code exists until R3.

**Predicted:** every chibi render, the cover, the sheets, the bases and the
catalogue unchanged. **Measured:** so (`--check` matches, bases and catalogue
unchanged); 606 passed.

### R1: the choices removed (2026-09-26)

The owner's calls on R0: old links load as the default tall chibi;
`long_traced_real` goes (R3); the eye block is frozen as it renders today
(R3).

Removed: `catalogue.BUILD`, `BuildField`, `_build_json` and the catalogue's
`build` key; the `None` ("Chibi") entry in `bodies`; the web tool's build
slider and snaps, the body select's `""`-to-`null` handling. Old links:
`urlstate.params_from_dict` drops `heads` and a `body` of `None`, so they
load as the default tall chibi. **Moved to R2:** the CLI's `--build` and
`--heads`, since `refresh-ref-out.sh` renders `ref-out/real/` through
`render.sh --build`; they retire with those renders.

**Predicted:** `ref-out/` and the bases byte-identical, the catalogue JSON
the only committed output to change. **Measured:** so; 624 passed. One test
read `heads` back through `decode_params`, which now maps it away; it reads
the link's raw JSON instead, what `main()` resolved. Browser: an old link
(Krista at `heads=6`, `body=null`) loads as the tall chibi, the Build
section shows the body select and the belt, bust and chest sliders, no build
slider.

### R0: the inventory (2026-09-26, at `6c1b275`)

A read-only delegate (sonnet, 79k tokens) over both repositories; the
riskiest claims checked by hand.

**The pin.** On the tall-chibi path `sk.build` is 0.1: `_skeleton_at`
applies a body profile only at `heads == BUILDS["chibi"]` (2.4), and
`BodyProfile.applied` sets `build` to a throwaway unprofiled skeleton's value
at 2.4 heads, `(2.4 - 2.0) / 4.0`. `_KOU_CHIBI_BUILD = 0.1` already relies on
it.

**Classes, with the step that takes each:**

| item | where | class | step |
| --- | --- | --- | --- |
| build slider (`BUILD`, a 2 to 7 heads range with two snaps) | `catalogue.py:460`, `web/app.js` | replaced by height | R1, R4 |
| body select's empty option (the compressed chibi) | `web/app.js:277`, `BODY_LABELS` | remove | R1 |
| `--build` / `--heads` | `generate.py:85,90,134`, `sheet.py:213,267`, `cover.py:215,351`, `render.sh`, `cover.sh` | remove (`--heads` may carry height later) | R1 |
| `urlstate` | generic `asdict` round trip, no clamp | old `heads`/`body=None` mapped onto the tall chibi | R1 |
| `REALISTIC_REFS`, `ref-out/real/` | `presets.py:1229`, `refresh-ref-out.sh:41,118,323` | remove | R2 |
| tests over builds | 21 parametrizations in `test_smoke.py`, 6 in `test_catalogue.py`, realistic asserts at `test_smoke.py:226,228,2037,2170`, `test_catalogue.py:99` (snaps equal `BUILDS`), `test_generate_cli.py:46` | rewrite with the removal they test | R1, R2 |
| `gap-analysis` skill | `.claude/skills/gap-analysis/` | retire; `docs/gap-analysis.md` kept as record | R2 |
| `body=None` branch | `character.py:4110` (`return build_skeleton(...)` unprofiled) | remove | R3 |
| `BUILDS["realistic"]` | `skeleton.py:21`, `character.py:10102`, readers above | remove; `BUILDS` keeps the chibi or becomes a constant | R3 |
| realistic-only branches (never true at 0.1) | `character.py:2908, 7562, 8108, 8130, 8256, 9457, 10013` | delete | R3 |
| always-true halves (`sk.build < 0.5`) | `_wears_cuts` (`4318`, six callers), `6076, 8151, 8185` | drop the half, keep the other operand | R3 |
| lerps evaluated at 0.1 (arm, leg, hat, hair, head shape, mouth, nose, eyes, stroke width at `43`, the moustache at `5335`, and about 25 more) | many | **freeze at their 0.1 value, never delete** | R3 |
| `long_traced_real` | `character.py:2431`, `catalogue.py:534` | no preset uses it; tuned for the realistic build | owner's call, R3 |
| docs | `CLAUDE.md:18,32,95,123`, `docs/api.md:152,218`, `README.md`, `STATUS.md` (a new dated section, history left) | reword | R5 |
| `../valley_of_mist` | `generate_assets.py`, `trailer/figures.py` | no `heads`, `build` or `body` anywhere: nothing to change | R5 (pixel check only) |

**Checked by hand, against the delegate:**

1. **The eye block at `character.py:9301` is live at the chibi.** It is
   gated `if sk.build > 0`, true at 0.1, so every tall chibi's eyes are
   already trimmed by the realistic tuning (openness by 4%, the lower lid by
   2%); its comment ("`sk.build` gates it to 0 there") is wrong. R3 must
   freeze it, not delete it, and correct the comment.
2. **`CLAUDE.md` does need rewording** (the delegate said not): it still
   describes `--build realistic` and the realistic-only `gap-analysis`
   direction.
3. No preset sets `heads` or `long_traced_real`.

**Riskiest for byte-identity:** the lerps (freeze, never delete); the eye
block; `_wears_cuts`' callers (an inlined `and` can change precedence); the
throwaway skeleton in `_skeleton_at` (inline 0.1 only with the invariant
written down).
