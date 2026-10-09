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
