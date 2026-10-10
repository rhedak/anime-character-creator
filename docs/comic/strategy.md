# Comic strategy

The procedure for `plan.md` and `status.md`, kept short. The general method is `../detail-strategy.md`
and the orchestrator skill; this file holds what this campaign taught.

## Rules

- **Build only what a panel needs** (the owner, 2026-10-09). Name the panel before the capability.
  Speculative items are written down as deferred, not built.
- **Functionality here, application in `../valley_of_mist`.** Page primitives, text, props, faces,
  poses in this repo; the script, the strips, the places and the build in the book's repo.
- **Defaults stay byte-identical.** Every new knob at its default leaves every existing render
  unchanged; the suite's `ref-out/` comparison is the control.
- **Look at it.** A shape or a panel is judged by rendering it at the size it will be read at, on a
  phone-sized crop as well as at full size.
- **Delegate reports, keep judgment.** Cheap models trace and measure; the choice of what to build
  and what to show the owner stays with the orchestrator.

## Lessons

- **Make the cheap sample before delegating the expensive trace.** The elbow trace was launched
  before anyone had checked whether swinging an arm past horizontal already gives hands raised. A
  five-minute sample (`samples.py`, sheet S6) did, and made most of the trace unnecessary: it asked
  for the elbow for three panels and one of them did not need it. Measure the need first, then brief
  the delegate on the part that is left.
- **A lettering check earned its keep on its first run.** Four real problems, all visible, in the
  first redraw. Writing a convention as code costs little and is not argued with.
- **Measure on the real reader.** Proof two looked good on a desktop image and was dense on a phone
  (four or five panels at once). The phone crop is now a standing view.
- **Delegate budget:** one trace used 127k tokens. Narrow the scope next time (one function, one
  outfit) so a report stays under about 100k.

## Faces carry the thoughts (owner, 2026-10-10)

The strip has no interior monologue, so expressions are pushed further than the prose implies: a script
line that says "still" or "undecided" may still get a hard, readable face. Judge a panel by reading only
the pictures. Chapter 1 panel 8 is the case (`menacing` for "he has not decided to do anything").

## Figure sizes agree with where they stand (owner, 2026-10-10)

Seen on the owner's phone: Chiyo looked like a dwarf beside Satoshi in panel 5 (heads 0.70 of his
with her feet at his depth). The rule: unless it is apparent that one figure is further back, all
relative sizes match. A taller character is taller, not bigger.

- **How it is measured.** The head is the yardstick: every head is one real size, so at one depth
  two heads are one size, and `Placement.height` is the canvas, which a taller figure fits with a
  smaller head (the driver, `height` 1.05, has 0.97 of Satoshi's head at one canvas size).
- **What "further back" means.** `Panel.horizon` is the scene y of the eye line. A figure's head size
  is proportional to how far its feet are below it, so a figure further back stands higher in the
  picture and is smaller by that ratio. No horizon says one depth.
- **The check.** `comic/checks.check_scale`, part of `check_panel`, names a pair whose head ratio is
  off its feet's ratio by more than 12%, and feet above the horizon. The build prints it with the
  lettering problems. Run for every panel with two or more figures, so a new panel needs its
  horizon stated or its figures at one size.
- **Not covered.** Sizes across panels (the camera zooms on purpose), and a character whose head is
  meant to differ in real size (a child). Build a `head_scale` when a panel needs one.
- **Found on the first run:** panel 5 (0.70 against 1.00) and panel 7 (the driver at 0.61 with no
  horizon stated; horizon 207 explains it). Panel 10 was fine (1.03 against 1.00).

