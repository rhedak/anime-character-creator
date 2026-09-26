# Bare body status

The record for `bare-body-plan.md`: what has been measured, predicted and
decided, newest first. The method lives in `bare-body-strategy.md`.

## RESUME (for a fresh context)

- **Now:** the plan is done and signed off (2026-09-26). Open: the men's
  armpit slot (a small bare-only change if wanted) and the realistic build's
  own fix pass. Follow-on: `tunic-bust-plan.md`, making the clothed bust
  agree with the bare one: done (T1 to T4); `../valley_of_mist` regenerated
  and waiting for the owner's commit call there.
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
| 4 close the body | done (4a to 4d) | tests; `ref-out/` byte-identical |
| 5 bare feet | done, signed off | 34 barefoot renders with no `None`; the audit clean; `ref-out/` byte-identical |
| 6 male torso minimum | done, signed off | tests; catalogue slider; `ref-out/` byte-identical |
| 7 web tool and skin tones | done, signed off | catalogue test; `app.js` parses; the served catalogue checked |
| 8 documentation | done | `api.md`, README, STATUS, the plan's summary |

## Findings, newest first

### Outer layers: valley_of_mist regenerated (2026-09-26)

At the owner's say-so, after the coat line: 32 files, every one with pixels
moved and each one Keiko, Kyoko or Reika (their references 254, 4164 and
320 pixels; the inserts they appear in 146 to 327). Katherina is not in the
book; the men and the cover did not move. Committed there.

### Outer layers: the line across open coats (2026-09-26)

The owner asked for Keiko's lab coat to be checked against her bust
(`harness/bare/keiko_coat.py`, `out/bare/keiko_coat.png`): the traced coat
widens at the bust only at its outer sides, under her hair and arms, and the
lapels cover most of each breast, so the only cue left was the dress's line
cut to two stray hooks in the opening (Kyoko's coat the same). The owner's
conditions for carrying the line across: never on the lapel, and as subtle
as the robe's.

`_bust_panel_line`: `_bust_fold` at `_COAT_BUST_LINE` = 0.6 (the robe's),
masked to the coat's panels; `GarmentCut.bust_line_after` draws it after the
panels and before the lab coat's lapels (2, and 2 on Katherina's jacket,
which has no separate lapels), and the parametric coat after its panels.
**Predicted:** Keiko, Kyoko and Katherina move, clothed and tunic-off (their
coats stay on), the men's coats (Gero, Tomohiro) byte-identical. **Measured**
by `cmp`: exactly those six files; `ref-out/` the three at both builds and
the sheets; 628 passed. At 4x (`out/bare/coat_line.png`, before above after,
Reika's robe for comparison): Keiko's curve shows on the coat body from the
side to the lapel and passes under it, the dress's inner part in the opening,
about as light as Reika's; Kyoko's likewise; Katherina's very faint (her
bust is 0.2 and the line fades in to 0.5).

### Outer layers over the bust: built (2026-09-26)

The owner: the coat's bow as recommended, and the robe's line the tunic's
**whole** curve, lighter. `_bust_fold(sk, weight, sides)` lifted out of
`_bust_lines` (which calls it as before); `_robe_front` draws it at
`_ROBE_BUST_LINE` = 0.6 on the breast the panel covers; `_COAT_BUST_BOW` =
1.0. The robe's diagonal bow and `_ROBE_BUST_BOW` taken out of the code.

**Predicted:** only Kyoko's and Reika's clothed renders change. **Measured,
wider, both explained:** by `cmp`, their tunic-off renders changed too,
since those take off only the tunic and the coat and robe still answer the
bust over bare breasts, correctly; and `ref-out/` moved `real/keiko` and
`real/katherina` as well: traced cuts draw only at the chibi
(`_wears_cuts`), so at the realistic build both wear the parametric coat,
which now bows. Nothing else moved; the men and the bases byte-identical;
627 passed. Before and after: `out/bare/outer_layers.png`.

### Outer layers over the bust: the study (2026-09-26)

The owner asked for Kyoko's open coat and Reika's robe front, the two
parametric garments that did not answer the bust, subtly. Strength constants
added to `character.py` at zero (`_COAT_BUST_BOW`, `_ROBE_BUST_BOW`,
`_ROBE_BUST_LINE`), which emit the original path text exactly: all 34 clothed
and bare renders byte-identical by `cmp`, `ref-out/` matches. Study:
`harness/bare/outer_layers.py`, `out/bare/outer_layers.png`.

- **Coat:** each front edge bows out by a share of the tunic's drape
  (`_bust_bulge`), pushed aside by the breast; no line under it. At 0.5
  barely visible at tile size; at 1.0 the opening widens over the chest and
  reads right, still subtle.
- **Robe, the diagonal's bow:** on the drape profile it kinked at the top of
  the chest; on a smooth bump over the breast's height it wobbles instead.
  Either way the straight diagonal reads better.
- **Robe, a faint line** (0.6 of a stroke, the outer half under the breast
  the panel covers): balances her. Now only the uncovered breast shows a
  line (the tunic's, beside the panel), and she reads lopsided.

### Tunic bust plan, T4: the cast and the downstream (2026-09-26)

T3 signed off. The cast sheet (`ref-out/sheet.png`) looked at: the busts
read alike across the tunics, nothing else moved. `../valley_of_mist`
regenerated (`generate-refs`, `generate-covers`, `generate-inserts`): 52
files. Per file, pixels and PNG metadata compared with `HEAD`: every man's
reference, the cover (Satoshi) and chapter 26 (no woman in it) change **0
pixels**, their metadata only, the embedded reproducing link now carrying
`chest`; every file whose pixels moved has a woman with a bust in it (183 to
2648 pixels an insert, 205 to 1664 a reference). Left uncommitted there.

### Tunic bust plan, T3: the side (2026-09-26)

`_bust_shape(drape=True)`: the piece from the armpit to the fullest point on
the bare breast's curve (control at the widest point's x, half way down),
arriving vertical there, blended in up to a bust of 0.2 so the continuity
test holds (the old and new curves differ even as the reach goes to zero).
Everything reading the drape follows: the tunic, the lobe over the arm at
the chibi, the traced cuts.

**Predicted:** the nine clothed presets with a bust change, bare and men
byte-identical, the continuity test green, Keiko's coat and Katherina's
jacket moving slightly. **Measured:** exactly the nine clothed files by
`cmp`, every bare render and every man byte-identical; 626 pass once
`ref-out/` is refreshed, the continuity test among them. `ref-out/`: the nine
at the chibi (Katherina's SVG only, her PNG pixel-identical under the jacket)
and the sheets. **Not predicted:** at the realistic build only Reika's SVG
changed, and not its pixels: there the tunic's side does not reach the
piece changed (not judged in this plan, cause not traced). At 4x
(`out/bare/t3_sides.png`, before above after): Krista's and Satoko's side
now rounds out of the armpit into the fullest point instead of leaving it
at the torso's angle; Keiko's lab coat and Reika's robe front unchanged to
the eye. Tile size: `out/bare/t3_cast.png`.

### Tunic bust plan, T2: the line (2026-09-26)

The owner picked d. `_breast_ellipse(sk, inset)`, the bare breast's ellipse
lifted out of `_bare_breast_spine`, which now reads it; `_bust_lines`' clothed
branch draws on it from the tunic's side at the fullest point round the
bottom and up to `_BREAST_STOP`, tapered at both ends as a fold. Its weight
still fades in with the bust up to 0.5 (the fade-in test, and what keeps
Katherina's and Linnea's light), so Elara's is a little lighter than in the
study's full-weight row.

**Predicted:** the clothed SVGs of the nine presets with a bust change, the
bare ones and the men byte-identical, `ref-out/` moving only for those nine
at both builds and the sheets. **Measured** (every preset rendered clothed and
bare before and after, compared with `cmp`): exactly the nine clothed files;
every bare render byte-identical, so the refactor moved nothing bare;
`refresh-ref-out.sh` updated the nine at both builds and the two sheets, the
cover and the bases unchanged. 626 passed. Before and after as worn:
`out/bare/t2_cast.png` (rounder on Satoko, Chiyo, Krista, Linnea; covered, as
before, under Kyoko's and Keiko's coats, Katherina's jacket, Reika's robe
front).

### Tunic bust plan, T1: the study (2026-09-26)

`harness/bare/tunic_bust.py`, `out/bare/tunic_bust.png` (the six adult
women, tunic on, every other garment off; the bare row first), Krista's side
in a, b and d at `out/bare/tunic_bust_krista.png`. **a** the current fold,
shallow and high. **b** the line from the bare ellipse at the bare depth,
from the tunic's side at the fullest point, tapered as a fold: round, and the
breast reads as the bare one does, but the side still leaves the armpit at
the drape's old angle, a slight dent above the fullest point. **c** as b at
0.85 of the depth: barely different from b at tile size. **d** b plus the
side from the armpit to the widest point on the bare outline's curve
(wrapping `_bust_shape(drape=True)`, so the lobe over the arm follows): the
side rounds cleanly out of the armpit and the line continues the silhouette
round the bottom; the closest to the bare figure. Recommendation: d at the
bare depth.

### Step 7: skin tones and the web tool (2026-09-26)

**No skin-derived tones.** Nothing reads `shade(skin_tone)`: everything on
the skin is in the outline colour (the line work, the chest lines, the
navel) except the blush, a fixed pink (`#e8879a`) at 0.45 opacity.

**The sweep** (`harness/bare/skin_tones.py`, `out/bare/skin_tones.png`, dark
rows `out/bare/skin_dark.png`): eight tones, very light `#fbe6d6` to deepest
`#442617`, on Krista, Gero, Satoko and Linnea in the base layer. The outline
holds at every tone. The line work inside the body (under the breasts, the
chest lines, the navel, the mouth) gets faint at the deepest but stays
visible; light brows (blonde, pink) nearly vanish on dark skin, as light
brows do. **The blush turns muddy maroon from "dark" down**: a question for
the owner, not changed here.

**Swatches:** `catalogue.SKIN_SWATCHES`, the eight tones (the default among
them), as `skin_swatches` in the catalogue JSON; `app.js` draws them as a
row of round buttons under the Skin picker (`swatchRow`), the picker still
free. Test: the default is among them and each renders. `app.js` passes
`node --check`; the staged server's catalogue carries the tunic and boots as
optional, the underwear as always on with its top toggle, the chest range and
the swatches. **Not yet checked in the browser**: the extension was not
connected.

**The owner:** the web tool checked in the browser and working; the blush to
follow the skin, as recommended. `_blush(skin)`: the fixed pink at 0.45
where the skin's luminance is 0.70 or more (every preset shipped, the
darkest `#e0c0a4` at 0.77), moving linearly to `#ff8a8a` at 0.60 by
luminance 0.20. Three target roses compared on Krista from "light warm" to
deepest (`out/bare/blush.png`): `#f2667a` at 0.55 rosier, `#e0506a` at 0.6
deeper and muddy again at the bottom, `#ff8a8a` at 0.6 a warm flush at every
tone. **Predicted** `ref-out/` byte-identical; **measured** so, 625 passed.

### Step 6: the minimum male torso, proposal (2026-09-26)

**At the chibi a man's bare silhouette is the women's exactly.** `frame`
separates the cast (+0.4 to +1.0 on the men, negative on most women) but
rides the build (`f = frame * t`) and moves a width by well under a percent
at 2.4 heads, and `tall_chibi_long_torso` sets the waist and hip widths
itself. Widening the shoulders would move the arms, which the skeleton
places. So the lever is line work, as it was for the bust at the chibi.

**Proposal** (`harness/bare/male_torso.py`, `out/bare/male_torso.png`, the
eight men in underwear): a `chest` knob, 0 to 1, a trait beside `bust`
rather than a sex flag, drawn only bare and only with no bust: two soft
arcs under the pectorals at the canon's half way from shoulder line to waist,
tapering at both ends, a gap at the sternum, depth and weight scaling with
the knob. Rows: none, 0.5, 1.0, 1.0 with a navel. Both strengths read as a
male chest; 1.0 is the clearer at the chibi; the navel helps the torso read
as skin rather than a block. Questions for the owner: the knob and the men's
values, and whether the navel goes on every bare figure.

**The owner's call:** as recommended. `CharacterParams.chest` (0 to 1),
1.0 on the eight men (Tomohiro through `_before`) and on `BASE_MALE`;
`_chest_lines` (only bare, only with no bust) and `_navel` (every bare
figure) in the chest after the underwear top; a catalogue range beside the
bust, a web row, an `api.md` row. **Predicted:** `ref-out/` byte-identical,
since both are bare-only and no clothed SVG carries a chest. **Measured:**
623 passed; `ref-out/` matches; the cast in `out/bare/6_cast.png`.

### Step 5: bare feet (2026-09-26)

`Outfit.boot_color: str | None`; `None` draws `_bare_foot`, the boot's
silhouette without the shaft: heel, sole, a rounder toe pointing a little
outward in the same stance, 0.85 of the boot's width, skin, no toes. The
catalogue's boots are optional. **Predicted:** every preset renders barefoot
at both builds with no `None`, `ref-out/` byte-identical.

Two joins fixed by looking at 2x on Satoko: the outline first started above
the ankle at full weight and stepped out of the leg's, reading as a sock's
top; then a full-width fill strip reaching above the ankle cut through the
leg's side lines. Now the outline starts at the ankle at the leg's weight
(0.85 of a stroke) and the fill covers only the leg's end line, reaching to
the inner edge of its side lines.

**Measured:** 621 passed (34 new); the audit has no failing line at either
build for the first time, "all off" included; `ref-out/` matches; the cast
barefoot in `out/bare/5_barefoot.png` (the third row of `base_layer.png`).
The realistic build renders and is not judged.

### Step 4d: the crotch (2026-09-26)

**Cause:** `_bare_seat` and `_torso`'s notch put the crotch `_CROTCH_AT`
(0.28) of the way from the hip to `sk.knee_y`, a landmark above the hip on
the long-torso profile, so the bare legs part at the hip itself (1.1 px above
it on 15 presets). The underpants have hidden it since step 3.

**Change:** `_crotch_y(sk, p)`, reading `_real_knee_y` with the tunic off and
the landmark otherwise, for `_bare_seat` (the legs and the underpants' hem)
and `_torso`'s notch. Trousers keep their own, clothed.

**Predicted:** on the long-torso presets the crotch moves from 331.8 to about
351 (hip 332.9, real knee about 397), the underpants' hem from about 346 to
about 361, the notch in `_torso` flattens (it is `min(hip + sw, crotch - sw)`);
on Katherina the crotch from 324.3 to about 337.9. `ref-out/` byte-identical.

**Measured:** Satoko 331.8 to 350.8, hem 361.0; Katherina 324.3 to 337.8,
hem 349.4; the legs now part below the briefs' hem, the briefs deeper
(`out/bare/4d_base_layer.png`, Katherina, Gero, Satoko, Chiyo, Krista, before
above after). 587 passed; `ref-out/` matches. Step 2's finding 2, the bare
seat's stroked top edge across the hip, is now always under the briefs; it
shows only in the mannequin, a harness view, and is left.

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
