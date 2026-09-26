# Bare body plan

A figure that can be drawn with nothing worn over its skin, so the tunic and
the boots become toggles like every other garment, and skin tones can be
judged on more than a face and two hands. First written 2026-09-25 at the
owner's request, straight after the bust campaign (`bust-plan.md`), whose
body layer (`_torso`) is most of the foundation.

The record is `bare-body-status.md`; the procedure and its anti-patterns are
`bare-body-strategy.md`, which leans on `bust-strategy.md` for everything the
two campaigns share.

## Where it stands

Every step is done (2026-09-26): the tunic and the boots optional, the bare
body closed where it shows (the breasts as their own shape, the shoulder,
the crotch), the base layer, bare feet, chest lines and a navel, and in the
web tool the toggles, a chest slider, skin tone swatches and a blush that
follows the skin. The record is `bare-body-status.md`. Left open: the
men's armpit reads as a narrow flat-topped slot (a small bare-only change if
wanted), and the realistic build, judged after its own fix pass.

## Owner's decisions (2026-09-25)

1. **No anatomical detail.** No nipples, no genitals: the body is a smooth
   silhouette with flat skin, the way the project draws it already.
2. **The default "nothing worn" is the body plus a base layer**, plain
   underwear drawn as an ordinary garment. The cast includes a 14 and a 15
   year old (Katherina, Linnea), and the web tool can undress any preset; the
   base layer is what "tunic off" shows for everyone.
3. **A fully bare "mannequin" view exists for proportion work only**, as a
   harness script, adults only, never a web tool toggle.
4. **Chibi first.** The realistic build still waits for its own fix pass
   (`bust-plan.md`, deferred); here it must not crash, and is not judged.

## Owner's decisions (2026-09-25, after step 2)

1. Steps 1 and 2 signed off.
2. Commits as the plan goes, one line each, no trailer.
3. Step 4's first item, the body's bust over the arms (4a), goes before
   step 3, since the base top cannot be judged while the bust is hidden.
4. Step 3's top follows the bust by default (`underwear_top: bool | None`,
   `None` drawing it when `bust > 0`), as recommended.
5. The mannequin stays adults only; every character gets the base-layer
   view.

## Owner's decisions (2026-09-25, after step 3)

1. Step 3 signed off. `underwear_top` stays a plain bool for now (a top
   always with a bust, and on request without one), not the tri-state first
   recorded; revisit later if needed.
2. The campaign holds here and resumes later with the rest of step 4.

## What already exists (read off the code at `611c50b`)

- `_torso`: the body under every garment, from the neck to `hip_y + sw`, with
  the bust, a rounded shoulder and a notch at the crotch (bust plan, step 3c).
- `_bare_seat`: bare legs as one silhouette, drawn whenever there are no
  trousers, with `_underpants` (a fixed `_UNDERWEAR_COLOR`) on top. So the
  lower half of a base layer is already drawn.
- `_arms` falls back to `skin_tone` for a bare arm when there is no
  undersleeve; the arm's top edge is a slanted cut that a sleeve cap has
  always covered (on `bust-plan.md`'s deferred list).
- **The tunic and the boots are not optional.** `Outfit.tunic_color` and
  `boot_color` are `str`, and the catalogue marks both `optional=False` with
  the comment that a character without them "is not something the generator
  can draw".
- The existing `harness/bust/bare_proportions.py` stubs every garment
  function out to draw a bare figure. That is the thing this plan replaces
  with a real outfit.

## Invariant

**Every preset wears a tunic and boots, so `ref-out/` must stay
byte-identical at every step** (`./refresh-ref-out.sh --check`). A step that
moves a clothed preset has leaked; it is a bug, not a refresh. The same holds
for `../valley_of_mist`, which needs no regeneration from this plan.

## The order

### 1. Audit, and the mannequin

`harness/bare/audit.py`: every preset at both builds, rendered with the tunic
off, then with every optional garment and the boots off too. Record every
exception, every `None` that reaches the SVG, and a contact sheet to look at.
The mannequin (below) was planned here and moved to the end of step 2,
since before it the tunic's outline still draws.

**Acceptance:** a list of breakages by part in the status file, each with the
step below that fixes it. No source change.

### 2. The tunic becomes optional

`tunic_color: str | None`. With `None` the tunic draws nothing and every
reader of it copes: the long sleeve, the belt keeper's shade, the bust's line
work (`_bust_lines` hangs off the tunic), anything the audit finds. The
catalogue slot gets a toggle.

The tunic's trim goes with it: the placket and the chest pockets are sewn on
the tunic (the audit found Tenno's floating on bare skin).

Then `harness/bare/mannequin.py`: the adults, nothing worn and no underpants,
arms at full opacity, the view later steps are judged in (replacing the
stubbing in `bare_proportions.py`).

**Acceptance:** every preset renders with the tunic off at both builds with no
`None` in the SVG (a test); `ref-out/` byte-identical.

### 3. The base top

The upper half of the base layer, drawn **only when there is no tunic** (so
clothed output cannot move): a plain band over the bust, following
`_bust_shape` so it sits on the body at any bust, in the underpants' colour.
`_UNDERWEAR_COLOR` becomes an `Outfit` field with the same default so the
two halves agree and can be recoloured.

**Owner's call, with a recommendation:** when is the top drawn? Recommended:
an `Outfit.underwear_top: bool | None = None`, where `None` follows the bust
(drawn when `bust > 0`) and `True`/`False` force it. No preset changes, men
(bust 0) get none, and a flat-chested female character can set `True`.

**Acceptance:** tunic-off sheet of the whole cast looked at; clothed output
byte-identical.

### 4. Close the body where the tunic hid it

Everything the audit finds open or wrong once the tunic is off, at the chibi.
Found so far (`bare-body-status.md`, steps 1 and 2): the bust stays under the
arms with nothing worn, since `_bust_over_arms` redraws garments and there
are none; the seat's stroked top edge across the hip; the long-torso
profile's knee above its hip, which the crotch and the underpants read; the
stepped shoulder.
Expected from the code: the arm's slanted top against the shoulder; the join
from `_torso` (ends at `hip_y + sw`) to `_bare_seat` (starts at
`_leg_tuck_top_y`); the line under the bust, which today belongs to the tunic
and has to belong to the body when nothing is worn; the neck's lines. One
sub-step per region, each looked at in the mannequin view and the base-layer
view.

**Acceptance:** the adults' mannequin and the cast's base-layer sheet
signed off by the owner; a test per closed region (the bust campaign's
`test_the_bare_body_is_closed_where_it_shows` is the pattern).

### 5. Bare feet

`boot_color: str | None`, with `None` drawing a foot: a small rounded shape
off the ankle, front facing, no toes drawn at the chibi. Catalogue toggle.

**Acceptance:** the cast barefoot at the chibi looked at; `ref-out/`
byte-identical.

### 6. A male torso, the minimum

With the tunic off, a man is the female body at bust 0 and reads
androgynous. The minimum: what separates them in the silhouette and line work
(shoulder width, a straighter waist, a line or two for the chest), and what
decides it. That needs a field, since `bust = 0` does not say "male".
**Owner's call on a proposal with renders** before anything is built.

### 7. The web tool and skin tones

The tunic and boot toggles in the GUI (they come from the catalogue), and a
row of skin tone swatches spanning very light to very dark beside the free
colour picker. A sweep sheet of the cast at those tones, checking every
`shade()` of the skin (blush, the ear, the line under the bust) and that the
outline still reads on dark skin. Checked in the browser.

### 8. Documentation

`docs/api.md`, the catalogue's comments, `README.md`'s status and
`STATUS.md`.

## Deferred

- The realistic build: judged after its own fix pass.
- Anything beyond the minimum male torso (musculature, the chest in detail).
