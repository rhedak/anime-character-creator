# Tall chibi status

The record for `tall-chibi-plan.md`, newest first.

## RESUME (for a fresh context)

- **Now:** R0 done, waiting for the owner's sign-off and three calls
  (old links, `long_traced_real`, the eye block); then R1.
- **Tree:** clean at `2e549d2` when the plan was written.
- **Invariant:** every tall-chibi render byte-identical through R1 to R3
  (`./refresh-ref-out.sh --check`); only R4 may move a figure.
- **Owner sign-off** after each step; commits one line, no trailer.

## Scoreboard

| step | state | acceptance met |
| --- | --- | --- |
| R0 inventory | done | inventory below, each item classed and stepped |
| R1 remove the choices | | |
| R2 retire the realistic outputs | | |
| R3 delete the dead code | | |
| R4 the height slider | | |
| R5 docs and the downstream | | |

## Findings, newest first

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
