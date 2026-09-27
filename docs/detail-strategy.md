# Detail strategy

How to work this campaign (`detail-plan.md`). Everything in
`bust-strategy.md` and `bare-body-strategy.md` applies (predict before
measuring, one change per measurement, measure the drawn ink, look in the
right view, only the owner signs off); this file adds what is particular to
raising the detail level.

## Procedure

1. **The reference is a benchmark in spirit.** `ref-local/katherina_grok_real/`
   is compared by eye at one calibrated head size
   (`harness/detail/baseline.py`), never traced, never measured as a target.
   A number off it (the chin's depth, the line's weight) says which way to
   go, not where to stop.
2. **Judge every study in three views**: full size, the height range (0.8,
   1.0, 1.3), and the smallest size `../valley_of_mist` shows a figure at
   (`out/detail/smallest.png`: a four-column insert sheet at about 0.23 of
   its PNG, a figure about 180 px tall at 1x). A detail that reads only at
   full size is not done.
3. **Additive knobs are byte-identical at their default.** Face maturity at
   0 and the width follow-through at height 1.0 must leave
   `./refresh-ref-out.sh --check` and `harness/tall_chibi/snapshot.py` (with
   `cmp`) unchanged. Take the before snapshot from the committed tree (`git
   stash`), never after the edit.
4. **Continuous knobs.** A sweep at fine steps for every new slider, looked
   at for pops, before sign-off.
5. **A very different palette in every eye and hair study** (`CLAUDE.md`):
   a cool iris and a warm one, dark hair and light.

## Anti-patterns, with the incident behind each

- **A by-eye crop of the reference.** The 2026-09-27 review cropped the
  reference with a guessed head centre and radius (88 px). Calibrated on
  face width it is 83.9 px, centre (636, 293), and the second scale (widest
  row to chin, 127.7) disagrees by 52%: not an error, the reference's lower
  face is longer. Use the calibrated sheet.
- **Two inventory delegates on Sonnet came back at 109k and 131k tokens**,
  above the orchestrator skill's ~100k signal. Both read `character.py`
  (10k lines) broadly. Next time split by region of the file, or by one
  question per delegate.
- **A web tool staged before a preset change.** The ages were applied after
  the last `./web-stage.sh`, so the tool opened every preset at age 0 (the
  owner spotted it). Restage after any change to `presets.py` or the
  catalogue, not only after a web change.
