# Bare body status

The record for `bare-body-plan.md`: what has been measured, predicted and
decided, newest first. The method lives in `bare-body-strategy.md`.

## RESUME (for a fresh context)

- **Now:** step 4c (the bare shoulder) built, waiting for the owner's
  sign-off. Step 3 signed off (`0f1097b`). Then 4d, the crotch reading the
  knee landmark, and the owner's call on the armpit slot.
- **Tree:** clean at `611c50b` when the plan was written.
- **Invariant:** `./refresh-ref-out.sh --check` byte-identical after every
  step; every preset wears a tunic and boots.
- **Run harness scripts** with `./harness/run.sh harness/bare/<script>.py`.
- **Owner sign-off** after each step before the next.
- **Commits:** one line, repo style, no trailer.

## Scoreboard

| step | state | acceptance met |
| --- | --- | --- |
| 1 audit | done | breakages listed, each with its step |
| 2 tunic optional, mannequin | done | 34 renders with no `None`; trim test; `ref-out/` byte-identical |
| 3 base layer | done, signed off | tests; 0 of 54 PNGs and the bases move, 7 SVGs' bytes and one base's do |
| 4 close the body | 4a, 4b done; 4c built (the shoulder) | tests; `ref-out/` byte-identical |
| 5 bare feet | | |
| 6 male torso minimum | | |
| 7 web tool and skin tones | | |
| 8 documentation | | |

## Findings, newest first

### Step 4c: the bare shoulder (2026-09-25)

**Cause:** with the tunic off the arm still takes the tunic's slanted cap as
its top (`_sleeve_under_cap` does not ask whether there is a tunic), and its
top edge is stroked, so a diagonal line crosses every bare arm from the cap's
tip to the armpit. `_torso`'s shoulder rounds its tip by `k * 2`, and `k` is
the inset, zero bare since 4a, so the tip is a square corner. Together: the
epaulette.

**Change**, all behind `tunic_color is None`: no cap without a tunic (the
arm's top goes flat); a bare arm, no sleeve of any kind, stroked everywhere
but across its top; `_torso`'s shoulder rounded by the arm's own width
rather than the inset, and its underside dropped a stroke and a half inside
the arm, where the arm's fill covers it, except in the gap at the armpit.

**Predicted:** the shoulder one rounded line from the neck down the arm's
outer edge, nothing across the arm's top, a short crease at the armpit on the
men and the breast's outline on the women; `ref-out/` byte-identical.

**First measurement:** the line across the arm gone, but two joins off at 6x
on Gero: the shoulder's descent curved inward to its underside while the
arm's outline started straight below it (a hook), and the underside rose on
the diagonal to the arm's top, showing half its stroke as a nub at the
armpit. Bare, the shoulder now runs straight down the arm's outer edge to its
underside, and the underside runs level inside the arm to its inner edge, up
it, and across the gap.

**Measured:** as predicted at 6x on Gero and Krista (Krista's breast still
joins the arm's corner, now at the flat top); 586 passed; `ref-out/` matches.
Before and after: `out/bare/4c_mannequin.png`, `out/bare/4c_base_layer.png`.
Left: the armpit on the men reads as a flat-topped slot, the sliver between
arm and torso side (present since 4a) closed at the top; a question for the
owner, not fixed here.

### Step 3: the base layer (2026-09-25)

`Outfit.underwear_color` (the old `_UNDERWEAR_COLOR`, same default) for both
halves, and `underwear_top: bool = False`. **A deviation from the decision as
recorded** (`bool | None`, `None` following the bust): as a plain bool meaning
"a top even without a bust", a character with a bust always wears one. The
tri-state's `False` would have made any preset with a bust topless in the web
tool, the minors included, against decision 5 (bare is a harness view only).
Flagged to the owner. The catalogue has an Underwear slot, colour not
optional.

`_underwear_top`: only with the tunic off. A plain band down each breast's
outer outline (`_bare_breast_spine`) to its lowest point, straight across
under both, closed by a shallow dip from armpit to armpit, with a thin line
along each breast's inner lower curve for the cups. In the chest after the
breasts, so garments lie over it and at the chibi it comes over the arms with
them. Without a bust, when asked, a flat band.

Found on the cast sheet (`harness/bare/base_layer.py`,
`out/bare/base_layer.png`), fixed here rather than in step 4, since the base
layer cannot ship without them:

1. **Satoko, Chiyo and Reika had no underpants** (step 1, finding 3): the
   hem read the knee landmark, above the hip on the long-torso profile.
   `_real_knee_y`, lifted out of `_boot`, now gives both. This moves the
   underpants' path under every skirt: **predicted** 0 pixels, **measured**
   `--pixels` 0 of 54, the female base 0 of 800x1000 by hand; 7 SVGs and
   `bases/female.svg` refreshed for their bytes.
2. **Tucked presets wore shorts, untucked ones briefs**: the seat started
   where a tucked tunic would end. With no tunic it starts at the hip.
3. **At the hip the briefs were a strip, and the torso's crotch notch showed
   above them** (the crotch still reads the landmark knee; step 4). With no
   tunic the underpants start a third of the way from the hip to the waist.

### Step 4b: the bare breast's shape (2026-09-25)

The owner, on 4a: the breasts look made to read through the tunic, not bare.
Agreed for the line under the bust (a cloth fold's hint: tapering at both
ends, shallow, fading in with the bust); the side outline had been built for
the body.

**Line variants** (`harness/bare/bust_line.py`, `out/bare/bust_line.png`): a
full-weight contour, rounder and deeper, stopping short of the sternum, and
two continuing the side outline from its tuck. Each continuing variant read
as one outline per breast, but kept a dent where the side's S returns to the
torso before the line leaves it.

**The owner's question: why dents, not a round shape?** Because the bust is
the torso's side bent out and brought back in an S (`_bust_shape`), pinned at
the armpit; right for a garment, which is the silhouette, not for a round
form lying on the chest.

**Own shape** (`harness/bare/breast.py`, `out/bare/breast.png`): each breast
its own ellipse, over the torso and (chibi) the arms, sized from the existing
anchors (widest at `bust_y`, reaching `bust_reach` past the plain side, the
fold's drop times `depth`, inner edge 0.15 of the way out from the sternum).
The outline fades in below the armpit, runs round the outside and bottom, and
tapers up the inner side; the arm's inner edge stops at it. The start angle:
-55 curled into a hook at the armpit's corner, -40 still touched it, -28 is
clean (`out/bare/breast_top.png`). Depth sweep 0.8, 1.0, 1.25, 1.5 on the six
adult women, for the owner to pick.

**The owner picked 1.25**, and asked about the join at the top: the stub of
the arm's inner edge and the outline's fade-in tail sat side by side at the
armpit, unjoined. The outline now starts at the arm's own inner top corner (as
`_arms` draws it; the shared armpit point sat a few pixels outside it and the
arm's top edge overshot), at full weight, and curves down and a little out to
the ellipse's widest point, arriving vertical. Joined at -20 degrees instead,
the ellipse there lay inside the armpit and the curve wiggled in and out.
Result: arm top, armpit and breast side are one line with a clean corner at
the armpit (`out/bare/breast_join.png`, Krista and Satoko, before and after).

**Built** (the owner approved the join): `_bare_breast_spine` and
`_bare_breasts`, the prototype's geometry at depth 1.25, gap 0.15, stop 170,
plus a weight fade-in up to bust 0.2 for continuity near zero (no preset is
below 0.2). With no tunic `_bust_lines` returns the breasts, so they sit in
the chest where a strap or belt lies over them, and `_bust_over_arms` masks
the chest to them at the chibi (fill and stroke). At the realistic build they
stay under the arms, as the clothed bust does. The 4a lobe route for the bare
body is gone. **Predicted:** the mannequin as the prototype; `ref-out/`
byte-identical. **Measured:** as predicted; Krista with only the tunic off
has her strap over the breast (`out/bare/krista_strap.png`); 567 passed; the
audit clean at both builds but the boots. The test was written after the
code this time, not failing first.

### Step 4a: the body's bust over the arms (2026-09-25)

With no tunic, `_bust_over_arms` draws the body itself under whatever else is
worn on the chest, masked to the body's own tucked lobe, and `_bust_lines`
draws the line under the bust from the body's edge instead of the tunic's.

**First pass**, the body at its usual inset (1.5 strokes inside the tunic's
outline): the line under the bust drew, but the lobe barely cleared the arm's
inner edge, and the inset's small step showed at the armpit. The inset exists
only to keep the body's edge off the tunic's; bare, it made the figure a
stroke and a half narrower than the one it replaces.

**Second pass**, one variable: `_body_inset(sk, p)`, zero with no tunic,
read by `_torso`, `_neck`'s line ends and both bust parts. **Predicted:** the
bust crosses the arm by about 1.5 strokes more, the armpit step goes, clothed
output byte-identical. **Measured:** as predicted at 5x on Krista; 567
passed; `ref-out/` matches. Left for later sub-steps: a small point where the
bust's outline leaves the armpit, and the arm's inner edge running close
beside the torso's side below the bust (two lines a sliver apart).

### Step 2: the tunic optional (2026-09-25)

`Outfit.tunic_color: str | None`. Off, `_tunic`, `_placket`,
`_chest_pockets` and `_bust_lines` draw nothing; a long sleeve goes with the
tunic, and a coat's sleeve over no tunic takes the coat's colour; the belt
keeper pair's buckle opening falls back to the belt's own shade. The
catalogue's tunic slot is optional (`ref-out/catalogue.json`: one `false` to
`true`).

**Predicted:** the 35 new tests pass, `ref-out/` byte-identical (every preset
wears a tunic, and each change is behind `tunic_color is None`).
**Measured:** 566 passed, 1 skipped; `refresh-ref-out.sh --check` matches; the
audit rerun leaves only `_boot` (step 5).

**Looked at: the mannequin** (`harness/bare/mannequin.py`, adults, nothing
worn, underpants stubbed), three things for step 4 that the audit's unfilled
tunic outline had hidden:

1. **The women read flat.** At the chibi the bust shows over the arms only
   because `_bust_over_arms` redraws the *garments* masked to the lobe; with
   nothing worn there is nothing to redraw, and the body's bust stays under
   the arm. `harness/bust/bare_proportions.py` got round this by swapping
   the tucked body shape in. The body has to come over the arms itself when
   bare, with its own line under the bust.
2. **A box edge at the hip.** `_bare_seat` starts at `_leg_tuck_top_y` with
   its own stroked top edge, a horizontal line across the body at the hip
   (untucked) or the belt (tucked), so the legs read as shorts. With the
   knee above the hip (step 1, finding 3) the crotch notch also runs up
   almost to that line.
3. **The shoulder reads boxy**: the body's rounded shoulder (bust plan, 3c)
   meets the arm's slanted top in a stepped corner, like an epaulette.

### Step 1: the audit (2026-09-25, at `611c50b`)

`harness/bare/audit.py`, every preset at both builds in three outfits: the
tunic off; every `*_color` off, boots included; the same with the boots on.
Output `out/bare/audit.txt` and, adults only, `out/bare/audit_<build>.png`.

**Predicted:** the tunic's fill as a literal `None` on every preset, the long
sleeve's too, a crash in `shade(None)` on a belt keeper pair, and `_boot`
crashing with no colour.

**Measured:**

| finding | where | presets | fixed by |
| --- | --- | --- | --- |
| `fill="None"` on the tunic, its outline still stroked | `_tunic` | all 17, both builds | step 2 |
| raises in `shade(None)` | `_belt_drawn` keeper pair (7785) | Keiko, both builds | step 2 |
| raises in the long sleeve's cuff | `_wrist_cuff` (7112), from `_arms` reading `tunic_color` | Katherina, realistic | step 2 |
| raises with no boot colour | `_boot` (7570) | all 17, both builds | step 5 |

The prediction held but for two details: the long sleeve raised only at the
realistic build (the chibi's sleeve path passes the colour through as a
string and it lands as a `None` fill), and nothing else raised: every other
garment already draws nothing at `None`.

**Looked at (adults, chibi):**

1. The unfilled tunic's outline still draws: the V neck, the sides running
   down inside the arms, and at the shoulder a white wedge between that
   outline and the body. Nothing about the shoulder can be judged until step
   2 removes it.
2. The tunic's trim stays on bare skin with the tunic gone: Tenno's placket
   and chest pockets float on his chest. They are the tunic's, and go with it
   (step 2).
3. **The long-torso profile's knee is above its hip** (`knee_y` 328.9 against
   `hip_y` 332.9 on 15 of the 17 presets; `tall_chibi`, Katherina's, has it
   below at 341.9 against 317.5). `_boot` already knows (its comment at 7521)
   and aims at a "real knee", the lower of the landmark and mid-leg. The
   crotch (`_bare_seat`, `_torso`'s notch) and `_underpants` still read the
   landmark, so on an untucked preset the underpants come out with negative
   height and vanish: Satoko, Chiyo and Reika bare show a line at the hip and
   no underpants. A skirt or trousers has always covered it. Step 4, with the
   pixel check: the bare legs show below a skirt, so this may move clothed
   pixels and be the owner's call.
4. The bust reads, and has no line under it once the tunic is off: the line
   is `_bust_lines`', which hangs off the tunic. Step 4.
5. Garments over bare skin otherwise behave (Gero's and Daizen's coats, the
   straps, the belts, Reika's robe front, Chiyo's apron).
6. An undersleeve with no tunic reads as a pair of sleeves with no garment
   (Elara, Krista). It is a garment of its own in the catalogue and stays one.

The mannequin moves to the end of step 2: it is the same outfit route with
the underpants stubbed, and before step 2 it would show the tunic's outline.
