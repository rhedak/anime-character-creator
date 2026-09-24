# Bust status

The record for `bust-plan.md`: what has been measured, predicted and decided,
newest first. The plan says what to do; this says where it stands. The method
lessons live in `bust-strategy.md`.

## RESUME (for a fresh context)

- **Now:** step 1 of `bust-plan.md`, reach rather than width. Prepared
  2026-09-24, not started.
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
| 1 reach, not width | prepared | |
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

### 2026-09-24: the first draft read anchors as the figure

Mechanism, measurement and scope in `bust-plan.md`, "What the first draft got
wrong". Taken with `harness/bust/drawn_widths.py` at `504edc3`.
