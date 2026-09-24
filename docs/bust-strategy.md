# Bust strategy

How to work this campaign, and the mistakes that earned each rule. The record
of what was measured is `bust-status.md`; the plan is `bust-plan.md`. Update
this when a method lesson lands, not when a number changes.

## Procedure

1. **Grep the readers first.** Before changing an anchor, list every place
   that reads it (`src/`, `tests/`, `harness/`). The status file keeps the
   current list.
2. **Write the predicted numbers into `bust-status.md` before running.** The
   gap between prediction and measurement is the next clue.
3. **Measure the drawn ink**, with `harness/bust/drawn_widths.py` or a script
   like it: rasterize the part on its own, read the row. A `Skeleton` field is
   an input to a part, not what the part draws.
4. **One change per measurement.** The anchor, the tunic's curve and the
   bust's height are three variables; change and measure them one at a time.
5. **Check the zero case twice**: `refresh-ref-out.sh` for bytes where the
   SVG should not change, the step 2 pixel check where it may. Then the
   continuity test: `bust = 0.01` moves nothing by more than 0.01.
6. **Look, in the right view.** The bust is under the arm until step 5, so
   judge shape with the arms at a third (`why_hidden.py`) and appearance as
   rendered. Both builds, white and black. Check the crop actually contains
   the torso before judging anything in it.
7. **Only the owner signs a step off.** Show a before/after sheet and stop.

## Anti-patterns, with the incident behind each

- **Quoting an anchor as a measurement.** The first draft's table put
  `arm_x - arm_half_w` (0.752) where the drawn arm starts at 0.587, and
  `bust_half_w` (0.930) where the drawn torso is 0.583. Two of its conclusions
  inverted as a result (`bust-plan.md`, retractions 2 and 3).
- **A no-op that holds only because nothing reads it.** `bust_half_w` matched
  `_body_knots`' line and not `_tunic`'s curve; it looked safe at zero and
  jumped 0.37 at 0.01. The rule: a no-op is proved by a consumer drawing it at
  a tiny nonzero value, not by the zero case alone.
- **A test that cannot fail.** L1's first form drew a copy of a shape under
  the same shape and called pixel identity its acceptance. Ask of every
  acceptance check: what change would make this fail?
- **A status line claiming a test that does not exist.** B1 said a test
  asserted `bust=0` equals no argument; none was written. Grep for the test
  before recording it as done.
- **A crop that hides the subject.** `bare.py` cut the realistic row at the
  collarbone and it was reported on as if the torso had been seen. Derive
  crops from the figure's extent, and look at the sheet before quoting it.
- **Arithmetic stated from memory.** "A quadratic reaches a quarter of the
  way to its control" was wrong by two, in a sentence warning about exactly
  that error. Check against a curve already in the code.
- **Reading an offset tuple in the wrong order** (Keiko's campaign): segment
  offsets came back `(y, x)` and were read as `(x, y)`, so three correct crops
  "failed". Ask delegates to name the order, and test both when a result is
  implausible.
- **Diagnosing by memory of an earlier note** (Keiko's campaign): the missing
  lapel notch was blamed on line work because an earlier note mentioned it;
  the cause was a vertical closing in the mask. Reproduce before explaining.

## Delegation

Per the orchestrator skill: `model` set on every `Agent` call. Reports and
mechanical edits go to `sonnet`; shape, calibration and sign-off decisions
stay here. A delegate brief states, in order: what it must not touch (with
"another run may be executing in this tree"), where everything is, what is
observed with numbers, numbered questions asking for file:line, known traps
(this file), and the deliverable with "flag every step INFERRED rather than
OBSERVED".
