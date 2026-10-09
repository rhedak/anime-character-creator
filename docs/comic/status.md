# Webcomic status

The record for `webcomic-plan.md`. Procedure: `detail-strategy.md`.

## RESUME

The plan is written; nothing is built. Next is **W0, C0**: the owner chooses the scene,
the format and the language of the first page, and I turn it into a panel-by-panel
script and a gap list. Nothing is drawn before the owner confirms the script.

## Scoreboard

| step | state |
|---|---|
| W0 the slice | waiting on the owner (C0) |
| W1 the page, with what exists | not started |
| W2 acting range | not started, provisional |
| W3 poses | not started, provisional |
| W4 the scene layer in `src/` | not started, provisional |
| W5 a second page | not started, provisional |
| W6 the web tool | not started, provisional |
| W7 a study in angles | not started, provisional |

## Owner's answers

One line per checkpoint, dated, as the owner answers.

- **Direction, 2026-10-08.** Webcomic first, animation later. "Start with what works
  and then iterate": the cast stays the tall chibi, front-facing, and more angles come
  later by iteration.

## Findings

### The state of the repo at the start, 2026-10-08

Observed by reading, not measured:

- `cover.py` (408 lines) composes a flat backdrop, mist bands, one figure and title
  text as SVG, and its docstring records the owner's decision to keep it simple and not
  compete with painted art. `sheet.py` (305 lines) tiles presets with labels.
- `Expression` carries deltas for the brow and eyelids and the mouth's curve and
  width. Six named ones exist (`presets.py`): stern, grim, hollow, wry, sorrow,
  resolute. None is a happy, surprised or angry face.
- There is no pose system. An arm swing is a rotation of the whole arm group, seen in
  the SVG as a `rotate(...)` group; the head is rigid. `CLAUDE.md` says "poses do not".
- The hands campaign (`hands-plan.md`) added five relaxed hands and a fist on a held
  staff, and nothing else about bodies changed.

**Not verified.** Whether the mouth can draw an open mouth or teeth, which decides
how much of the acting range is parameters and how much is new shape code. The first
study in W2 answers it.
