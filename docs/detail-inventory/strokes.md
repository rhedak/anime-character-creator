# Line-weight inventory for character.py (D1 prep)

`_stroke_w(sk)` is defined at character.py:33 as `sk.head_r * (0.041 + 0.017 * sk.build)`.
All line-numbers below are in `src/anime_character_creator/character.py`.

Columns: File:Line | Enclosing function (outer / inner closure) | Multiplier actually applied | Class | Note

## 1. All `_stroke_w` call / stroke-width sites

| Line | Function | Multiplier | Class | Note |
|---|---|---|---|---|
| 2355 | `_hair_mass` | 1.0 | SILHOUETTE | hair-mass outline |
| 2387 | `_neck` | 1.0 | SILHOUETTE | neck outline |
| 2730 | `_bust_over_arms` | (assign `sw`) | - | plumbing, not a drawn stroke |
| 2743 | `_bust_over_arms` | 1.5 | OTHER | **not visible ink** - widens a `<mask>` shape (white-on-white) so the mask's edge sits inside the bust fill; see Q4 |
| 2779 | `_bust_over_arms` (`pt`) | 1.0 | SILHOUETTE | visible bust-over-arm outline, clipped |
| 2819 | `_bust_fold` | (assign) | - | plumbing |
| 2820 | `_bust_fold` | 0.95×(bust factor)×weight | INTERIOR | fold-line weight variable (`heaviest`), UNSURE - not grepped, found via secondary search |
| 2938 | `_bare_breasts` | (assign) | - | plumbing |
| 2939 | `_bare_breasts` | ×(bust factor) | INTERIOR | fold-line weight variable, harness-only |
| 2982 | `_underwear_top` | (assign) | - | plumbing |
| 2985 | `_underwear_top` | full sw (offset, not stroke) | GEOMETRY | `side = _torso_at_armpit(sk) - sw`; see Q4 |
| 2995 | `_underwear_top` | 1.0 | SILHOUETTE | underwear-top cup outline |
| 3008 | `_underwear_top` | 1.0 | SILHOUETTE | underwear-top cup outline (other side) |
| 3010 | `_underwear_top` | 0.6 | INTERIOR | fold/dip line |
| 3030 | `_chest_lines` | (assign) | - | plumbing |
| 3037 | `_chest_lines` | 0.8×(amount factor) | INTERIOR | chest-definition line weight var, found via secondary search |
| 3069 | `_navel` | (assign) | - | plumbing |
| 3072 | `_navel` | rx 0.45 / ry 0.7 (size, not stroke) | GEOMETRY/OTHER | navel ellipse **radius** sized from `sw`, not a stroke; UNSURE class (no silhouette/interior/feature fits a body mark) |
| 3124 | `_torso` | 1.5 (offset) | GEOMETRY | `under_y` computed from stroke width; see Q4 |
| 3169 | `_torso` | 1.0 (offset) | GEOMETRY | hip notch geometry; see Q4 |
| 3175 | `_torso` | 2.0 and 1.0 (offsets) | GEOMETRY | hip notch geometry; see Q4 |
| 3206 | `_torso` | 1.0 | SILHOUETTE | torso outline |
| 3224 | `_body_inset` | 1.5 (`_BODY_INSET`) | GEOMETRY | inset of the nude body drawn under a garment; see Q4 |
| 3414 | `_tunic` (`shoulder_up`) | 1.0 | SILHOUETTE | tunic outline |
| 3433 | `_tunic` (`shoulder_up`) | 0.9 | SILHOUETTE/INTERIOR (UNSURE) | undersleeve edge stroke - could be read as a garment-piece edge or a seam |
| 3437 | `_tunic` (`shoulder_up`) | 0.9 | SILHOUETTE/INTERIOR (UNSURE) | undersleeve edge stroke, other side |
| 3458 | `_hair_tail` | (assign) | - | plumbing |
| 3486 | `_hair_tail` | 1.0 | SILHOUETTE | hair-tail outline |
| 3544 | `_headscarf` | (assign) | - | plumbing |
| 3585 | `_headscarf` | 1.0 | SILHOUETTE | scarf knot lobe outline |
| 3588 | `_headscarf` | 1.0 | SILHOUETTE | scarf outline |
| 4202 | `_draw_cut` | (assign, ×`weight` param) | - | plumbing; `weight` is caller-supplied, not a fixed constant |
| 4210 | `_draw_cut` (`d`) | 1.0×weight | INTERIOR | decorative fabric-cut edge |
| 4219 | `_draw_cut` (`d`) | 0.7×weight | INTERIOR | cut's secondary line |
| 4708 | `_hat_underside` | 1.0 | SILHOUETTE | hat brim underside outline |
| 4729 | `_hat` | (assign) | - | plumbing |
| 4733 | `_hat` (`shape`) | 1.0 | SILHOUETTE | hat outline |
| 4743 | `_hat` (`shape`) | 0.8 | INTERIOR | hat band/detail line (UNSURE) |
| 4761 | `_hair_tie` | (assign) | - | plumbing |
| 4765 | `_hair_tie` | 1.0 | SILHOUETTE | tie outline |
| 4768 | `_hair_tie` | 0.7 | INTERIOR | tie detail line |
| 4786 | `_hair_knot` | (assign) | - | plumbing |
| 4801 | `_hair_knot` | 1.0 | SILHOUETTE | knot outline |
| 4804 | `_hair_knot` | 0.7 | INTERIOR | knot detail line |
| 4826 | `_robe_front` | (assign) | - | plumbing |
| 4848 | `_robe_front` | 0.8 | INTERIOR | fold line |
| 4857 | `_robe_front` | **0.7** | SILHOUETTE | robe-front outline itself is already drawn at 0.7×, lighter than default - notable precedent, see summary |
| 4878 | `_hanging_sleeves` | (assign) | - | plumbing |
| 4894 | `_hanging_sleeves` | 1.0 | SILHOUETTE | sleeve outline |
| 4938 | `_coat` | (assign) | - | plumbing |
| 4986 | `_coat` | 1.0 | SILHOUETTE | coat panel outline |
| 5147 | `_beard` | (assign) | - | plumbing |
| 5248 | `_beard` (`line`) | 1.0 | SILHOUETTE | beard mass outline |
| 5274 | `_beard` (`line`) | 0.4 | INTERIOR (UNSURE) | fill=skin_tone stroke - a chin/mouth gap line inside the beard mass |
| 5307 | `_glasses` | (assign) | - | plumbing |
| 5315 | `_glasses` | 0.55 | FEATURE | glasses frame stroke |
| 5399 | `_goggles_strap` | (assign) | - | plumbing |
| 5413 | `_goggles_strap` | 1.0 | FEATURE (UNSURE) | goggles strap outline - not literally "glasses" but same face-prop role |
| 5442 | `_goggles` | (assign) | - | plumbing |
| 5448 | `_goggles` | **not from `_stroke_w`** | FEATURE | lens rim width = `lens_r * 0.5`, sized off the lens radius, not `_stroke_w(sk)` at all - will NOT track a global stroke-weight change |
| 5454 | `_goggles` | 1.0 | FEATURE | goggles body outline |
| 5513 | `_mock_collar` | 1.0 | SILHOUETTE | collar outline |
| 5515 | `_mock_collar` | 0.7 | INTERIOR | collar seam line |
| 5538 | `_collar` | (assign) | - | plumbing |
| 5556 | `_collar` | 1.0 | SILHOUETTE | collar outline |
| 5558 | `_collar` | 0.7 | INTERIOR | collar seam line |
| 5576 | `_placket` | (assign) | - | plumbing |
| 5586 | `_placket` | 0.7 | INTERIOR | placket seam line down front |
| 5593 | `_placket` | r=0.62 (size, not stroke) | GEOMETRY/OTHER | button **radius** sized from `sw`, filled circle, no stroke at all; see Q4 |
| 5611 | `_chest_pockets` | (assign) | - | plumbing |
| 5629 | `_chest_pockets` | 0.7 | SILHOUETTE (UNSURE) | pocket-flap outline (small applique piece; could be read as INTERIOR) |
| 5649 | `_strap` | (assign) | - | plumbing |
| 5664 | `_strap` | 0.8 | SILHOUETTE | strap outline |
| 5820 | `_underskirt` | 4.0 (threshold, not a stroke) | GEOMETRY | `deep = hem_y - skirt_hem > _stroke_w(sk)*4`; decides whether pleats draw at all - see Q4 |
| 5824 | `_underskirt` | 1.0 | SILHOUETTE | underskirt outline |
| 5847 | `_underskirt` | 0.45 (floor 1.0) | INTERIOR | pleat weight var `pleat_sw` |
| 5854 | `_underskirt` | derived from 5847 | INTERIOR | pleat line |
| 5905 | `_apron` | 1.0 | SILHOUETTE | apron outline |
| 5934 | `_hakama` | (assign) | - | plumbing |
| 5938 | `_hakama` | 1.0 | SILHOUETTE | hakama outline |
| 5944 | `_hakama` | 4.0 (threshold, not a stroke) | GEOMETRY | same pleat-depth guard as `_underskirt`; see Q4 |
| 5954 | `_hakama` | derived (0.4, from line 5946 `pleat_sw`) | INTERIOR | pleat line |
| 5970 | `_skirt` | 1.0 | SILHOUETTE | skirt outline |
| 5984 | `_skirt` | 0.45 (floor 1.0) | INTERIOR | pleat line |
| 6562 | `_staff_placement` (`placed`) | 1.0 (offset) | GEOMETRY | canvas-edge clamp so the staff prop's own stroke stays on-canvas; see Q4 |
| 6585 | `_staff` | (assign) | - | plumbing |
| 6593 | `_staff` (`d`) | 1.0 | SILHOUETTE | staff wood outline |
| 6596 | `_staff` (`d`) | 0.6 | INTERIOR | wood-grain strand line |
| 6608 | `_staff` (`d`) | **1.0, same `sw` as line 6593** | INTERIOR (UNSURE) | crystal facet line, `fill="none"` - see Q3, no separate multiplier from the silhouette call |
| 6989 | `_katana_placement` | 1.0 (offset, `/r`) | GEOMETRY | placement clamp so blade/guard clears the arm by one stroke; see Q4 |
| 7023 | `_katana` | (assign) | - | plumbing |
| 7041 | `_katana` (`shape`) | ×`weight` (caller-supplied per part) | SILHOUETTE | blade/hilt piece outline, explicitly parameterized per call (not a shared literal) |
| 7198 | `_arms` (`traced`) | 1.0 | SILHOUETTE | sleeve outline |
| 7211 | `_arms` (`traced`) | 1.0 | SILHOUETTE | sleeve outline, second path |
| 7215 | `_arms` (`traced`) | 1.0 | SILHOUETTE | sleeve outline, third path |
| 7285 | `_arm_joint_cap` | 0.5 (offset) | GEOMETRY | `r = w_top + sw*0.5`, cap radius grown by half a stroke to cover the seam; see Q4 |
| 7288 | `_arm_joint_cap` | 1.0 | SILHOUETTE | joint-cap outline |
| 7307 | `_cuff_line` | (assign) | - | plumbing |
| 7310 | `_cuff_line` | 0.7 | INTERIOR | cuff line |
| 7335 | `_wrist_cuff` | 0.85 | SILHOUETTE | cuff outline |
| 7367 | `_hand` (`x`) | (assign) | - | plumbing |
| 7369 | `_hand` (`x`) | 0.85 | SILHOUETTE | hand outline |
| 7449 | `_legs_and_boots` | n/a | n/a | comment text only ("...is a stroke-width below..."), not a code site |
| 7595 | `_trousers` | 1.0 | SILHOUETTE | trouser outline |
| 7630 | `_underpants` | 0.85 | SILHOUETTE | underpants outline |
| 7668 | `_bare_seat` | 0.85 | SILHOUETTE | bare-mannequin seat outline (harness-only) |
| 7693 | `_trouser_seams` | 0.45 (floor 1.0) | INTERIOR | seam weight var `seam_sw` |
| 7696 | `_trouser_seams` | derived | INTERIOR | seam line |
| 7703 | `_trouser_seams` | derived | INTERIOR | seam line, other leg |
| 7744 | `_bare_foot` (`x`) | 0.85 (assign) | - | plumbing (note: `sw` here is already `_stroke_w(sk)*0.85`, not the raw value) |
| 7747 | `_bare_foot` (`x`) | 0.5 and 1.5 of the already-scaled `sw` (offsets) | GEOMETRY | ankle-cover patch fill sized off stroke width; see Q4 |
| 7754 | `_bare_foot` (`x`) | 1.0 (of the 0.85-scaled `sw`) | SILHOUETTE | foot outline |
| 7832 | `_boot` (`x`) | 1.0 | SILHOUETTE | boot outline |
| 7854 | `_boot` (`x`) | 0.7 | INTERIOR | boot-cuff turn line (matches CLAUDE.md's explicit "boot cuff" shade()-thickness example) |
| 7864 | `_boot` (`x`) | 0.55 | INTERIOR | sole/highlight line |
| 7872 | `_boot` (`x`) | 0.4 (floor 1.0) | INTERIOR | lace weight var `lace_sw` |
| 7880 | `_boot` (`x`) | derived | INTERIOR | lace line |
| 7955 | `_belt_drawn` | 0.5 (offset) | GEOMETRY | `half_w` clamp widened by half a stroke; see Q4 |
| 7972 | `_belt_drawn` | /2 (offset) | GEOMETRY | `half_w = edge - sw/2`; see Q4 |
| 7987 | `_belt_drawn` | 1.0 | SILHOUETTE | belt band outline |
| 7993 | `_belt_drawn` | 1.0 | SILHOUETTE | buckle rect outline |
| 8025 | `_belt_drawn` | (assign) | - | plumbing |
| 8031 | `_belt_drawn` | 0.85 | SILHOUETTE | buckle metal-piece outline |
| 8049 | `_belt_drawn` | 0.5 | INTERIOR | buckle detail line |
| 8069 | `_belt_drawn` | 0.55 | INTERIOR | stitch line |
| 8076 | `_belt_drawn` | 0.55 | INTERIOR | stitch line, other side |
| 8088 | `_belt_drawn` | (assign) | - | plumbing |
| 8096 | `_belt_drawn` | 0.7 | SILHOUETTE (UNSURE) | pouch/tab outline on belt |
| 8113 | `_belt_drawn` | 0.7 | SILHOUETTE (UNSURE) | pouch/tab outline on belt, shaded |
| 8129 | `_pouches` | (assign) | - | plumbing |
| 8150 | `_pouches` | 0.85 | SILHOUETTE | pouch outline |
| 8155 | `_pouches` | 0.85 | SILHOUETTE | pouch flap outline (shaded) |
| 8195 | `_crystal_layout` | 0.5 (spacing, not a stroke) | GEOMETRY | `gap = sw*0.5` between crystals; see Q4 |
| 8227 | `_crystal_harness` | (assign) | - | plumbing |
| 8251 | `_crystal_harness` | 0.8 | SILHOUETTE | harness strap outline |
| 8258 | `_crystal_harness` | 0.5 | INTERIOR | strap shade line |
| 8264 | `_crystal_harness` | 0.6 | INTERIOR | buckle/loop line |
| 8275 | `_crystal_harness` | 0.6 | INTERIOR | buckle/loop line |
| 8290 | `_crystal_harness` | 0.7 | INTERIOR | rivet line |
| 8295 | `_crystal_harness` | 0.7 | INTERIOR | rivet line |
| 8674 | `_ears` | (assign) | - | plumbing |
| 8696 | `_ears` (`fold`) | 1.0 | INTERIOR | ear fold/crease line |
| 8700 | `_ears` (`fold`) | 0.55 | INTERIOR | inner-ear detail line |
| 8731 | `_head` | (assign) | - | plumbing |
| 8733 | `_head` | 1.0 | SILHOUETTE | **head silhouette** - the primary candidate D1 means to lighten |
| 8737 | `_head` | 0.6 | INTERIOR | under-chin line - already thinner than the silhouette; a working precedent for D1's split |
| 8848 | `_eye_realistic` | 1.0 (×`_EYE_OUTLINE_W`=0.85) | FEATURE | eye white outline |
| 8877 | `_eye_realistic` | 1.0 (×0.85) | FEATURE | eyelid line |
| 8944 | `_eye_anime` (`local`) | 1.0 (×0.85) | FEATURE | eye white outline |
| 8974 | `_eye_anime` (`local`) | 1.0 (×0.85) | FEATURE | eyelid line |
| 9007 | `_eye_closed` | 1.0 (×0.85) | FEATURE | closed-eye line |
| 9028 | `_scar` | (assign) | - | plumbing |
| 9034 | `_scar` (`line`) | 0.6 or 0.45 (via param `w`) | INTERIOR (UNSURE) | scar mark; not listed in the given FEATURE set, not a garment/body silhouette either |
| 9187 | `_face` | (assign) | - | plumbing |
| 9206 | `_face` | ×`f.brow_weight` (data-driven, not a fixed literal) | FEATURE | brow stroke - weight comes from `FaceStyle`, not a hardcoded fraction |
| 9220 | `_face` | 0.85 | FEATURE | mouth/nose line (UNSURE exactly which; in `_face`, so FEATURE either way) |
| 9243 | `_hair_front` | (assign) | - | plumbing |
| 9255 | `_hair_front` | 1.0 | SILHOUETTE | hair-front lock edge |
| 9270 | `_hair_front` | 1.0 | SILHOUETTE | hair-front lock edge |
| 9280 | `_hair_front` | 0.55 | INTERIOR | strand/part detail line |
| 9742 | `_familiar` | (assign) | - | plumbing |
| 9760 | `_familiar` (`placed`) | 1.0 (offset) | GEOMETRY | canvas-edge clamp, same pattern as `_staff_placement`; see Q4 |
| 9775 | `_familiar` (`d`) | 1.0 | SILHOUETTE | familiar body outline |
| 9779 | `_familiar` (`d`) | 0.5 | INTERIOR | fur/cell texture line |
| 9784 | `_familiar` (`d`) | 1.0 | SILHOUETTE | familiar body outline (second shape) |
| 9792 | `_familiar` (`d`) | 0.5 | INTERIOR | texture line |
| 9810 | `_familiar` (`shrink`) | 0.7 | INTERIOR | texture line |

## 2. Non-`_stroke_w` geometry/margin uses found via secondary search (`grep '\bsw\b'` minus assign/stroke-width lines)

Already folded into the table above (2763 lobe-close offset is described at 2779's row; 2985; 3072; 5593; 5820/5944 threshold; 6562/6989/9760 clamps; 7285; 7747; 7955/7972; 8195). One more, not tied to a `sw` variable at all:

| Line | Function | Note |
|---|---|---|
| 4679-4692 | `hat_hair_margin(p)` | Headroom margin for a hat, in head-radii. Approximates "the stroke's outer half" with a **hardcoded literal `0.06`**, not a call to `_stroke_w`. Will NOT move if D1 changes the `_stroke_w` formula - a silent drift risk. |

## 3. Summary (see chat reply for the table, counts, and Q3/Q4 write-up)
