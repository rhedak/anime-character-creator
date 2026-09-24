# Bust status

The record for `bust-plan.md`: what has been measured, predicted and decided,
newest first. The plan says what to do; this says where it stands. The method
lessons live in `bust-strategy.md`.

## RESUME (for a fresh context)

- **Now:** step 1 of `bust-plan.md`. 1a (reach rather than width) and 1b
  (height from the armpit) done; 1c (the shape below the bust) next.
- **Tree:** clean at `e3b65e5` when preparation began.
- **Measure** with `harness/bust/drawn_widths.py` (the drawn ink). Never quote
  a `Skeleton` field as a body measurement.
- **Run harness scripts** with
  `DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:/usr/local/lib" .venv/bin/python harness/bust/<script>.py`.
  `harness/run.sh` only adds `/opt/homebrew/lib`, and this machine's cairo is
  under `/usr/local/lib`, so it fails here (open, see below).
- **Owner sign-off** is needed after each step before the next.
- **Commits:** one line, repo style, no trailer.

## Scoreboard

| step | state | acceptance met |
| --- | --- | --- |
| B0 sweep harness | done, readings void | harness stands |
| B1 parameter and anchor | done, `bust_half_w` to be replaced | plumbing only |
| 1 reach, not width | 1a, 1b done; 1c (shape below the bust) next | continuity test green |
| 2 pixel check | not started | |
| 3 body layer | not started | |
| 4 line under the bust | not started | |
| 5 bust over the arm | not started | |
| 6 traced cuts follow | not started | |
| 7 cast values | not started | |
| 8 integration | not started | |

## Step 1 preparation

### Who reads the anchor (grep at `e3b65e5`)

- `character.py` `_tunic`, the `rib()` closure: the only reader of
  `bust_half_w` and `bust_y` in `src/`.
- `skeleton.py`: `_BUST_ALONG`, `_BUST_REACH`, the two `Skeleton` fields and
  their computation in `build_skeleton`.
- `harness/bust/bare.py` prints `sk.bust_half_w`; `sweep.py`, `why_hidden.py`
  and `drawn_widths.py` set `bust=` only.
- **No test mentions bust.** B1's status said a test asserts
  `build_skeleton(bust=0.0) == build_skeleton()`; it was never written. Step 1
  writes it, along with the continuity test.

### Where the bust sits (measured at `e3b65e5`, head radii below the head centre)

| body | shoulder | armpit (`_sleeve_hem_y`) | `bust_y` | waist |
| --- | --- | --- | --- | --- |
| chibi, long torso (satoko, keiko, satoshi) | 1.118 | 1.788 | 1.905 | 2.713 |
| chibi, `tall_chibi` (katherina) | 1.130 | 1.657 | 1.981 | 2.384 |
| realistic | 1.280 | 2.561 | 2.653 | 4.330 |

`bust_y` is 45% of shoulder to waist, which puts it 13% of the way from the
armpit to the waist on the long-torso chibi and 5% at the realistic build: hard
up under the armpit, where a bulge merges with the sleeve cap. On `tall_chibi`
it is 60% of the way, so one constant lands differently on two chibi bodies.
**Open for step 1:** measure `bust_y` from the armpit. The armpit today is a
garment function (`_sleeve_hem_y`), not an anchor, so either it becomes one or
the bust's height is expressed in a way that does not need it. Decide by
reading `_sleeve_hem_y` first.

### Predictions for step 1, written before any change

With `bust_reach = head_r * lerp(0.10, 0.20, t) * bust` added to the torso
curve's own width at the bust row, chibi half-widths at that row:

| `bust` | 0 | 0.01 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- |
| torso now | 0.583 | 0.950 | 1.013 | 1.080 |
| torso predicted | 0.583 | 0.584 | 0.633 | 0.683 |

Realistic: 1.077 at zero to about 1.277 at 1.0. The arm's ink starts at 0.587
(chibi) and 0.631 (realistic), so **as rendered, the whole bulge is predicted
to be under the arm at both builds for every value above about 0.04.** Step 1
is judged in `why_hidden.py`'s view (arms at a third), and the owner should
expect the rendered sweep to look unchanged.

### Delegation plan

- Step 1's shape, the continuity test and the `bare.py` crop: kept, since the
  shape is the judgment and the rest is a few lines.
- Step 2's pixel check: independent of step 1 and fully specifiable, so it
  can go to a `general-purpose` agent on `sonnet` in a worktree while step 1
  runs, brief in `bust-strategy.md`'s template.
- Nothing is read-only-trace shaped yet; no `Explore` needed.

## Open items outside the steps

- `harness/run.sh` exports only `/opt/homebrew/lib`. A one-line fix
  (`:/opt/homebrew/lib:/usr/local/lib`), not made yet because it is outside
  the plan; the owner's call.

## Findings, newest first

### 2026-09-24: step 1b, the bust's height from the armpit

**Change.** `Skeleton.armpit_y` (0.42 of shoulder to waist, the arithmetic
`_sleeve_hem_y` already used, which now reads it) and `bust_y` at
`_BUST_ALONG = 0.30` of armpit to waist, a first guess. Previously 0.45 of
shoulder to waist.

**Predicted vs measured** (torso half-width at the bust row):

| | 0 | 0.01 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- |
| chibi predicted, row 2.066 | 0.580 | 0.581 | 0.635 | 0.690 |
| chibi measured, row 2.065 | 0.579 | 0.579 | 0.631 | 0.687 |
| realistic predicted, row 3.092 | 1.073 | 1.075 | 1.173 | 1.273 |
| realistic measured | 1.070 | 1.070 | 1.172 | 1.274 |

Within 0.004 everywhere: the split now lands about 28% along the curve, no
clamp, and the full reach shows at the row. The arm's ink at the new row still
starts at 0.587 (chibi) and 0.637 (realistic), so as predicted the bulge is
under the arm at every value above about 0.07 (chibi).

**Zero case.** `refresh-ref-out.sh --check`: nothing changed, so moving
`_sleeve_hem_y` onto `armpit_y` changed no float.

### 2026-09-24: step 1a, reach rather than width

**Change.** `Skeleton` stores only the knob, `bust`; `bust_y` and
`bust_reach` are properties derived from the final shoulder, waist and build.
`_tunic` splits its armpit-to-waist quadratic where it crosses `bust_y` and
moves the split point and both neighbouring controls out by the reach, so the
join stays smooth and the halves become the original curve as the reach goes
to zero. At zero it still emits the original single curve.

**Second defect found and fixed with it.** `BodyProfile.applied` and
`waist_shift` replace the shoulder and waist, but the stored `bust_y` and
`bust_half_w` were computed from the unprofiled skeleton, so on every
profiled body the bust sat at a height unrelated to that body's own waist, and
its reach rode the profile's `heads` rather than the chibi build the figure is
pinned to. Derived properties make both impossible.

**Predicted vs measured** (torso half-width at the bust row, head radii,
`drawn_widths.py`):

| | 0 | 0.01 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- |
| chibi predicted | 0.584 | 0.585 | 0.639 | 0.694 |
| chibi measured | 0.583 | 0.583 | 0.624 | 0.668 |
| realistic predicted | 1.077 | 1.079 | 1.177 | 1.277 |
| realistic measured | 1.077 | 1.077 | 1.153 | 1.236 |

Continuity holds. The shortfall at 1.0 (0.026 chibi, 0.041 realistic) is the
bust height: `bust_y` sits so close to the armpit that the crossing lands at
about 5% of the way along the curve, and the split is clamped at 10%, so the
peak lies below the row being measured. That is step 1b's variable, and this
number is the evidence for it.

**Zero case.** `refresh-ref-out.sh --check`: nothing changed. Suite: 513
passed, 1 skipped, before the new tests; the three new tests (skeleton
equality, the bust following a profile and a waist shift, continuity and
monotonic growth) pass.

### 2026-09-24: the first draft read anchors as the figure

Mechanism, measurement and scope in `bust-plan.md`, "What the first draft got
wrong". Taken with `harness/bust/drawn_widths.py` at `504edc3`.
