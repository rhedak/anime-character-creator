# Python test audit for the TypeScript port

Phase 2 deliverable of `docs/ts-port-plan.md` (decision D7). Date: 2026-10-16. Machine-readable twin: `harness/ts_port/test-audit.json` (one record per test function, plus the indexes).

What is verified and what is read. **Verified** (ran it): every count in section 1 and 2, the pass, skip and timing figures, the parametrisation counts, the registry sizes. **Read** (judgement): the class, the property each test protects, the recommendation. Whether a test is `COVERED-BY-ORACLE` is conditional on the corpus requirements in section 6, because the Phase 2 corpus does not exist yet in full (the mini corpus has 68 cases).

## 1. Verified counts

| Fact | Value | How obtained |
| --- | --- | --- |
| Test files | 14 | `ls tests/`: 14 `test_*.py` files and no `conftest.py`. The brief says 15; I count 14 files, 4,715 lines (`wc -l`) |
| Test functions | 288 | AST scan of every `def test_*` at module level (no test classes exist) |
| Collected items with parametrisation | 1,052 | pytest in collect-only quiet mode: `1052 tests collected` |
| Result of one full run | 1,051 passed, 0 failed, 1 skipped, 0 errors | pytest `-rA`, run once, read-only |
| Time | 4.06 s reported by pytest (4.2 s wall) | the same run |
| The one skip | `test_the_coats_lapel_actually_reaches_the_neck[chibi-keiko]` | explicit `pytest.skip` at `tests/test_smoke.py:1629`: Keiko wears a traced coat at chibi |
| Interpreter and import path | CPython 3.13.11, `anime_character_creator` resolved to this worktree's `src/` | `python -c 'import anime_character_creator; print(...__file__)'` |
| Registries that size the parametrisations | PRESETS 20, NEUTRAL_BASES 2, HAIRSTYLES 8, BUILDS 1, EXPRESSIONS 13, ROSTERS 6, SUPPORTING 3, HAND_STYLES 5, hairstyles with `locks` 5 | imported and counted |

Per file (functions, items):

| File | Functions | Items | PORT | PORT-WITH-FUNCTION | COVERED-BY-ORACLE | REWRITE | DROP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tests/test_catalogue.py | 22 | 22 | 5 | 0 | 13 | 4 | 0 |
| tests/test_colorutil.py | 6 | 10 | 6 | 0 | 0 | 0 | 0 |
| tests/test_comic_checks.py | 12 | 12 | 0 | 0 | 0 | 0 | 12 |
| tests/test_comic_layout.py | 14 | 14 | 0 | 0 | 0 | 0 | 14 |
| tests/test_comic_text.py | 9 | 9 | 0 | 0 | 0 | 0 | 9 |
| tests/test_consumers_stay_flat.py | 4 | 4 | 1 | 0 | 0 | 0 | 3 |
| tests/test_generate_cli.py | 6 | 6 | 0 | 0 | 0 | 0 | 6 |
| tests/test_ids.py | 1 | 44 | 1 | 0 | 0 | 0 | 0 |
| tests/test_metadata.py | 8 | 30 | 3 | 0 | 5 | 0 | 0 |
| tests/test_open_mouth.py | 12 | 12 | 2 | 1 | 9 | 0 | 0 |
| tests/test_smoke.py | 161 | 761 | 25 | 12 | 106 | 3 | 15 |
| tests/test_soft_finish.py | 7 | 28 | 3 | 0 | 3 | 0 | 1 |
| tests/test_soft_locks.py | 23 | 95 | 8 | 2 | 8 | 3 | 2 |
| tests/test_supporting.py | 3 | 5 | 1 | 0 | 1 | 1 | 0 |
| **total** | **288** | **1052** | **55** | **15** | **145** | **11** | **62** |

Note: the parametrisation counts hide a vestigial axis. `BUILDS` has one entry, so every `parametrize("build", sorted(BUILDS))` multiplies by 1 (the id is `chibi`). Counts below are per test function first and per collected item second.

## 2. Summary tables

### 2.1 By primary class

| Class | Meaning | Functions | Items | Functions carrying the tag (any role) |
| --- | --- | ---: | ---: | ---: |
| O | output-level: public API only (render_character, PRESETS, urlstate, catalogue), asserts on SVG text or values | 64 | 356 | 115 (629 items) |
| R | rule test parsing or regex-scanning the SVG for a structural property | 33 | 216 | 114 (747 items) |
| I | internal: calls or imports names with a leading underscore, or character.py module names that the package does not export (BODY_TYPES, COAT_CUTS, ADULT_FACE_AGE ...) | 108 | 329 | 116 (339 items) |
| REF | compares with committed ref-out files | 3 | 23 | 7 (27 items) |
| P | Python-only (CLI, filesystem, pytest fixtures, cover and sheet modules) | 29 | 50 | 33 (54 items) |
| C | comic package | 35 | 35 | 37 (37 items) |
| M | metadata, attribution or urlstate link behaviour | 11 | 32 | 17 (43 items) |
| E | asserts an exception class or message | 5 | 11 | 9 (15 items) |
| total | | 288 | 1052 | |

### 2.2 By recommendation

| Recommendation | Meaning | Functions | Items |
| --- | --- | ---: | ---: |
| PORT | port as written (or nearly) | 55 | 490 |
| PORT-WITH-FUNCTION | port the test together with the named private function, which must be exposed | 15 | 94 |
| COVERED-BY-ORACLE | the differential corpus makes it redundant, provided the corpus requirements in this audit are met | 145 | 355 |
| REWRITE | keep the intent, change the form | 11 | 49 |
| DROP | Python-only or deprecated | 62 | 64 |
| total | | 288 | 1052 |

### 2.3 Primary class by recommendation (functions)

| Class | PORT | PORT-WITH-FUNCTION | COVERED-BY-ORACLE | REWRITE | DROP |
| --- | ---: | ---: | ---: | ---: | ---: |
| O | 32 | 0 | 28 | 4 | 0 |
| R | 10 | 0 | 20 | 3 | 0 |
| I | 1 | 15 | 91 | 1 | 0 |
| REF | 3 | 0 | 0 | 0 | 0 |
| P | 0 | 0 | 0 | 2 | 27 |
| C | 0 | 0 | 0 | 0 | 35 |
| M | 5 | 0 | 6 | 0 | 0 |
| E | 4 | 0 | 0 | 1 | 0 |

### 2.4 By priority

| Priority | Meaning | Functions | Items |
| --- | --- | ---: | ---: |
| P1 | port in the first pass: cheap, and either a rule the oracle cannot express or a pin that must outlive the oracle | 53 | 488 |
| P2 | worth porting: a guard for authoring new parts or data after cutover | 29 | 146 |
| P3 | redundant with the oracle while it exists; port only if time allows | 144 | 354 |
| P0 | dropped | 62 | 64 |

### 2.5 What the port should carry (PORT, PORT-WITH-FUNCTION, REWRITE) by earliest gate

| Earliest gate | Functions | Items |
| --- | ---: | ---: |
| Phase 1 (colorutil and kernel) | 8 | 12 |
| Phase 3 (foundation: skeleton, presets, urlstate) | 26 | 310 |
| Phase 4 end (needs catalogue and the full render) | 8 | 9 |
| Phase 4 end / Phase 5 (needs the full render or the part function) | 39 | 302 |

### 2.6 Deprecated or out-of-scope features (all DROP)

| Area | Functions | Items | Where |
| --- | ---: | ---: | --- |
| comic | 35 | 35 | test_comic_checks.py, test_comic_layout.py, test_comic_text.py (all of them) |
| cli | 10 | 10 | test_generate_cli.py (all 6) and one each in test_soft_finish.py, test_consumers_stay_flat.py, two in test_soft_locks.py |
| cover | 9 | 9 | test_smoke.py (8) and test_consumers_stay_flat.py (1) |
| sheet | 8 | 10 | test_smoke.py (7) and test_consumers_stay_flat.py (1) |
| png | 0 | 0 | none: no test calls cairosvg or writes a PNG |

Only the comic files and test_generate_cli.py are wholly deprecated. The other 21 dropped functions sit inside files that are otherwise portable: 15 in test_smoke.py (8 cover, 7 sheet), 3 in test_consumers_stay_flat.py (cover, sheet, CLI), 2 in test_soft_locks.py (CLI) and 1 in test_soft_finish.py (CLI). A port that copies those files must cut them out by name.

## 3. Reading guide

The recommendation rule I applied, so a different taste can re-sort:

* **COVERED-BY-ORACLE** when the assertion is a property of one specific preset or parameter set's output (a z-order, a substring, a number parsed from a part) and the byte-for-byte corpus, with its per-layer stage record, would already fail if it broke. This is 145 of 288 functions, 91 of them internal tests (they reach `character._x` only to read back what the render already contains).
* **PORT** when the test needs no private function and asserts something the oracle cannot say: a rule that must outlive the oracle (flat has no gradients, ids unique, byte budget, adult floor), a value-level check of a registry, a codec behaviour, or a render pairing the corpus is not designed to contain.
* **PORT-WITH-FUNCTION** when the assertion is a family rule or a numeric contract of a function over inputs wider than the corpus, and it is worth keeping to guard authoring after cutover. These are the only tests that force a private name to be exposed (index in section 8).
* **REWRITE** when the intent stays but Python machinery (dataclass introspection, `monkeypatch.setitem` on a registry, private catalogue helpers, a `None` literal check) has no TS equivalent.
* **DROP** only for comic, CLI, cover, sheet.

Oracle redundancy ends at cutover: the corpus manifest stays as a regression fixture, but a deliberate look change regenerates it from the TS, so only rules and pins keep their value. That is what P1 and P2 mark.

## 4. Tests that cannot be replaced by the oracle (must be ported or re-created as rules)

78 functions, 610 items (every PORT, PORT-WITH-FUNCTION and REWRITE test except the 3 REF tests, which are direct file diffs). Grouped by what the test protects:

**Determinism across two TS calls (module state, caches)** (2 functions, 2 items)

* `test_smoke.py::test_render_is_deterministic` (PORT, P1)
* `test_soft_locks.py::test_the_clumps_are_deterministic` (PORT, P1)

**Structural rules on the SVG text (regex or string search, some need an XML parser)** (13 functions, 154 items)

* `test_ids.py::test_ids_are_defined_once_and_every_reference_resolves` x44 (PORT, P1)
* `test_metadata.py::test_metadata_embeds_a_working_character_link` (PORT, P1)
* `test_smoke.py::test_the_figure_is_drawn_on_transparency` x20 (PORT, P1)
* `test_smoke.py::test_every_preset_renders_with_its_tunic_off` x20 (REWRITE, P1)
* `test_smoke.py::test_the_underpants_have_height_on_every_preset` x20 (PORT, P2)
* `test_smoke.py::test_the_bare_knee_grows_in_without_a_jump` (PORT, P1)
* `test_smoke.py::test_every_garment_off_still_leaves_the_underwear` (PORT, P1)
* `test_smoke.py::test_the_wristband_text_is_text_and_never_markup` (PORT, P1)
* `test_soft_finish.py::test_flat_has_none_of_what_soft_adds` (PORT, P1)
* `test_soft_finish.py::test_every_preset_draws_soft_as_well_formed_svg_without_blur` x20 (PORT, P1)
* `test_soft_locks.py::test_every_preset_stays_within_the_byte_budget_soft` x20 (PORT, P1)
* `test_soft_locks.py::test_the_byte_budget_holds_with_a_tip_colour_on_each_authored_cut` x2 (PORT, P1)
* `test_soft_locks.py::test_a_tip_colour_on_a_big_preset_stays_within_the_budget` x3 (PORT, P1)

**Counterfactual or synthetic input that a field-driven corpus cannot produce** (4 functions, 4 items)

* `test_smoke.py::test_a_cuts_holes_are_left_open_under_the_even_odd_rule` (PORT-WITH-FUNCTION, P1)
* `test_soft_locks.py::test_a_cut_without_locks_draws_exactly_as_it_did` (REWRITE, P1)
* `test_soft_locks.py::test_an_unknown_role_is_refused` (REWRITE, P1)
* `test_soft_locks.py::test_a_clump_too_short_to_draw_is_skipped_not_a_crash` (REWRITE, P1)

**Skeleton and body-profile values (no SVG)** (13 functions, 17 items)

* `test_smoke.py::test_a_body_profile_applies_at_the_chibi_build` (PORT, P1)
* `test_smoke.py::test_waist_shift_moves_the_belt_line_and_nothing_above_or_below_it` x2 (PORT, P1)
* `test_smoke.py::test_tall_chibi_long_torso_is_tall_chibi_with_a_lower_belt_and_a_bigger_head` (PORT-WITH-FUNCTION, P1)
* `test_smoke.py::test_head_scaled_makes_the_head_bigger_against_the_same_body` (PORT-WITH-FUNCTION, P1)
* `test_smoke.py::test_a_skeleton_with_no_bust_is_the_skeleton_built_without_one` (PORT, P1)
* `test_smoke.py::test_the_bust_rides_a_profiled_body_rather_than_the_one_it_replaced` (PORT, P1)
* `test_smoke.py::test_the_crotch_reads_the_real_knee` (PORT-WITH-FUNCTION, P2)
* `test_smoke.py::test_face_age_up_to_one_matures_only_the_head` x3 (PORT, P1)
* `test_smoke.py::test_the_limbs_taper_with_the_height` (PORT-WITH-FUNCTION, P1)
* `test_smoke.py::test_the_height_stretches_below_the_shoulders_only` x2 (PORT-WITH-FUNCTION, P1)
* `test_smoke.py::test_a_body_profile_that_measures_the_wrist_moves_the_hand_and_the_rest_do_not` (PORT-WITH-FUNCTION, P2)
* `test_smoke.py::test_only_a_profile_that_measured_the_neck_narrows_it` (PORT, P1)
* `test_smoke.py::test_a_stretched_body_carries_its_measured_wrist_with_it` (PORT, P1)

**Colour kernel properties (clamps, monotonicity, hue and saturation preservation)** (9 functions, 32 items)

* `test_colorutil.py::test_hex_rgb01_round_trip` (PORT, P1)
* `test_colorutil.py::test_shade_darkens_by_default` (PORT, P1)
* `test_colorutil.py::test_shade_black_stays_black` (PORT, P1)
* `test_colorutil.py::test_shade_white_saturation_boost_clamps_at_one` (PORT, P1)
* `test_colorutil.py::test_shade_saturation_boost_clamps_on_saturated_color` (PORT, P1)
* `test_colorutil.py::test_shade_value_factor_scales_value_directly` x5 (PORT, P1)
* `test_soft_locks.py::test_the_tones_keep_the_hair_saturation` x20 (PORT-WITH-FUNCTION, P1)
* `test_soft_locks.py::test_a_yellow_green_colour_is_not_nudged_toward_green` (PORT, P1)
* `test_soft_locks.py::test_a_higher_strength_moves_every_tone_further_from_the_hair_colour` (PORT, P1)

**Errors and validation (class names and message fragments, D12)** (4 functions, 10 items)

* `test_metadata.py::test_decode_rejects_what_it_did_not_encode` x3 (PORT, P1)
* `test_soft_finish.py::test_an_unknown_finish_is_refused` (PORT, P1)
* `test_soft_locks.py::test_a_strength_out_of_range_is_refused` x2 (PORT, P1)
* `test_soft_locks.py::test_a_strength_that_is_not_a_number_is_refused_for_soft_and_in_a_link` x4 (PORT, P1)

**Project policy pins (adult floor, flat by default)** (4 functions, 4 items)

* `test_consumers_stay_flat.py::test_nothing_that_is_drawn_by_default_is_soft` (PORT, P1)
* `test_smoke.py::test_every_preset_is_at_least_twenty_one` (PORT, P1)
* `test_smoke.py::test_a_character_from_outside_is_never_drawn_below_the_floor` (PORT, P1)
* `test_smoke.py::test_the_gui_age_slider_starts_at_twenty_one` (PORT, P1)

**Registry and cross-registry data rules (guard new presets, expressions, catalogue entries)** (17 functions, 296 items)

* `test_catalogue.py::test_every_color_field_exists_on_character_params` (REWRITE, P2)
* `test_catalogue.py::test_every_garment_field_exists_on_outfit` (REWRITE, P2)
* `test_catalogue.py::test_every_face_field_exists_on_facestyle` (REWRITE, P2)
* `test_catalogue.py::test_hair_tail_and_knot_fields_exist_on_character_params` (REWRITE, P2)
* `test_catalogue.py::test_the_bust_slider_covers_every_preset_s_value` (PORT, P2)
* `test_catalogue.py::test_the_chest_slider_covers_every_preset_s_value` (PORT, P2)
* `test_catalogue.py::test_the_skin_swatches_include_the_default_and_render` (PORT, P2)
* `test_catalogue.py::test_the_height_slider_covers_every_preset_and_its_ends_render` (PORT, P2)
* `test_open_mouth.py::test_startled_opens_the_mouth_and_leaves_what_it_does_not_name` (PORT, P2)
* `test_open_mouth.py::test_the_comic_expressions_exist_and_each_changes_the_face` (PORT, P2)
* `test_smoke.py::test_neutral_bases_render_and_stay_out_of_the_cast` x2 (PORT, P2)
* `test_smoke.py::test_an_expression_changes_the_mood_and_nothing_else` x260 (PORT, P1)
* `test_smoke.py::test_an_outer_layer_is_visible_against_what_it_covers` x20 (PORT, P2)
* `test_smoke.py::test_every_character_has_a_display_name_and_a_roster` (PORT, P2)
* `test_smoke.py::test_the_satoshi_roster_is_satoshis_persona_not_satokos` (PORT, P2)
* `test_supporting.py::test_every_supporting_character_has_a_display_name` (PORT, P2)
* `test_supporting.py::test_none_of_them_is_a_preset_or_offered_by_the_web_tool` (REWRITE, P2)

**Link and URL behaviour** (3 functions, 4 items)

* `test_metadata.py::test_character_url_carries_the_base_and_the_encoding` (PORT, P1)
* `test_smoke.py::test_an_old_link_loads_as_the_tall_chibi` (PORT, P1)
* `test_smoke.py::test_an_old_link_with_an_eye_style_loads_with_the_one_eye` x2 (PORT, P1)

**Authoring guards over a family of cuts, styles or ranges (matter after cutover, when new parts are drawn in TS)** (7 functions, 66 items)

* `test_open_mouth.py::test_an_opening_beyond_the_width_does_not_make_the_mouth_taller_than_wide` (PORT-WITH-FUNCTION, P2)
* `test_smoke.py::test_the_ear_stays_welded_to_the_skull` (PORT-WITH-FUNCTION, P2)
* `test_smoke.py::test_the_front_hair_adds_no_silhouette` x8 (PORT-WITH-FUNCTION, P2)
* `test_smoke.py::test_hair_stays_under_the_canvas_ceiling` x8 (PORT-WITH-FUNCTION, P2)
* `test_smoke.py::test_the_cap_covers_the_hair_it_is_tied_over` x8 (PORT-WITH-FUNCTION, P2)
* `test_smoke.py::test_every_relaxed_hand_keeps_a_hands_footprint` x15 (PORT-WITH-FUNCTION, P2)
* `test_soft_locks.py::test_every_lock_is_well_formed_and_under_the_ceiling` x25 (PORT-WITH-FUNCTION, P2)

**Repository hygiene on committed files** (2 functions, 21 items)

* `test_smoke.py::test_the_retired_builds_left_nothing_behind` (REWRITE, P2)
* `test_smoke.py::test_the_readme_shows_every_character` x20 (REWRITE, P2)

## 5. Tests that assert exact error text or exception class (D12)

Only five portable functions (11 items) assert an error, and none asserts a full message: `pytest.raises(..., match=...)` is a regex search, so each asserts a fragment. The full CPython text is given so the TS message can keep the fragment on purpose.

| Test | Items | Asserts | Python text for reference | Port note |
| --- | ---: | --- | --- | --- |
| `test_metadata.py::test_decode_rejects_what_it_did_not_encode` | 3 | class ValueError only, no message | not a valid character link: <Python exception text> (urlstate.py:105); not a valid character: <TypeError text> (urlstate.py:68) | Keep the class ValueError. The three inputs are bad base64, an empty string and valid JSON with an unknown field. decode_params catches any exception from the base64 and JSON decode and re-raises ValueError, and params_from_dict turns a TypeError from an unknown field into ValueError, so TS must wrap every codec failure (a RangeError, a SyntaxError) in ValueError. Message text is not asserted (urlstate.py embeds Python messages). |
| `test_soft_finish.py::test_an_unknown_finish_is_refused` | 1 | ValueError, regex search for the fragment: finish must be one of | finish must be one of flat, soft, not 'glossy' (character.py:94) | The fragment plus the join of FINISHES must survive; the trailing part quotes the value with Python repr (single quotes). |
| `test_soft_locks.py::test_an_unknown_role_is_refused` | 1 | ValueError, fragment: shadow or lit | a lock's role is shadow or lit, not 'glow' (character.py:13378) | Raised only by the soft finish while drawing clumps; the test swaps a Hairstyle with a synthetic lock, so TS needs an injectable registry. |
| `test_soft_locks.py::test_a_strength_out_of_range_is_refused` | 2 | ValueError, fragment: highlight_strength | highlight_strength must be between 0 and 2, not -0.1 (character.py:99); highlight_strength must be between 0 and 2, not 2.1 | The value is formatted with Python repr (hazard 15: float repr). |
| `test_soft_locks.py::test_a_strength_that_is_not_a_number_is_refused_for_soft_and_in_a_link` | 4 | ValueError, fragment: highlight_strength, on two paths (render_character and params_from_dict) | highlight_strength must be between 0 and 2, not '1'; ... not None; ... not True; ... not nan | Inputs: the string 1, None, True and nan. A JS boolean is not a number here, and nan fails the range test. Both paths end in validate_finish, so one function serves both. |
| `test_comic_layout.py::test_a_panel_too_wide_for_the_strip_is_refused` | 1 | ValueError, fragment: does not fit | n/a | Comic, dropped. |
| `test_comic_layout.py::test_a_gap_is_a_number_or_a_name_and_the_first_panel_has_none` | 1 | ValueError, fragment: no gap called | n/a | Comic, dropped. |
| `test_generate_cli.py::test_the_retired_build_options_are_gone` | 1 | SystemExit (argparse), no text | n/a | CLI, dropped. |
| `test_soft_locks.py::test_the_cli_refuses_a_strength_out_of_range` | 1 | SystemExit (argparse), no text | n/a | CLI, dropped. |

Four more error assertions sit in dropped tests (two comic, two CLI `SystemExit`). `docs/ts-port-errors.md` already has a row for `validate_finish` ("to be ported with the same text"), which covers the finish and highlight_strength fragments. Not yet listed there: the `shadow or lit` text, which is raised from the soft-finish drawing code rather than from `validate_finish`, and the wrapper texts of `urlstate` (`not a valid character link` and `not a valid character`, which embed Python exception text but are not asserted).

## 6. Corpus requirements that this audit puts on Phase 2

Each `COVERED-BY-ORACLE` verdict above assumes these cases exist in the corpus. If one is not added, the named tests move to PORT.

1. Catalogue extremes: for every garment range (with its colour switched on), every face range, hair_length, hair_tail and every scar option, render the catalogue lo and hi. The corpus is built from dataclass fields, not the catalogue, so test_catalogue's seven render tests are covered only if these are added explicitly.
2. Render option background (None, a colour): the corpus design in the plan names id_prefix, metadata and supporting but not background; test_the_figure_is_drawn_on_transparency is recommended PORT unless background cases are added.
3. Hostile and non-ASCII user text in wristband_text (markup, quotes, ampersand, non-BMP characters): hazard 19, and test_the_wristband_text_is_text_and_never_markup.
4. Height 0.8 and a value just above it (0.8001) on a figure with every optional garment colour off: the continuity test pairs two renders.
5. Combinations the tests use that one-field-at-a-time sweeps do not reach: every preset with tunic off; with tunic and trousers off together; with boots off; chiyo (headscarf) on every hairstyle; every preset at face_age 0, 1 and 2 with eye_size 1.05 and eye_width 1.10; gaze of plus and minus 1 on Risa and Satoshi; right_arm_out 125 and 128 with left_arm_out on Risa and Keiko.
6. highlight_strength 0, 0.3, 9.0 and minus 1 in flat (must not validate) and minus 0.1, 2.1, a string, None, True and nan in soft (must raise).
7. Soft finish with hair_tip_color on every authored cut (short_layered, long_traced, long_parted, long_fringed, short_crop) and on the three big-preset cuts of test_a_tip_colour_on_a_big_preset_stays_within_the_budget.

## 7. Dependencies on the web tool, the companion, `local/` and other files

* **web tool**: No test imports or runs anything under web/. Tests whose contract is the web tool: catalogue.py (the middle tier the web tool reads) and ref-out/bases.
* **companion**: No test touches the companion repo or its worker. Only docstrings mention a companion app (a_character_from_outside_is_never_drawn_below_the_floor); the hit in test_catalogue.py _turned_on is about a garment companion range. The behaviours the companion consumes (params_from_dict, validate_finish error text, render_character) are the tests listed under error text and links.
* **local folder**: Two tests monkeypatch ACC_LOCAL_DIR to a tmp path so cover.py cannot read the untracked local/cover_faces.json; no local/ directory exists in this worktree and the suite passes without it. Both are cover tests (dropped).
* **readme**: Reads README.md at the repository root and checks it links ref-out/on-white/<preset>.png for each preset (20 items). The PNGs themselves are not opened.
* **ref out files**: Committed files compared: 20 preset SVGs, 2 base SVGs (ref-out/bases), catalogue.json (REF, portable) and cover.svg, sheet.svg, sheet_satoshi.svg (REF, dropped); one test scans ref-out for retired *_real files.
* **optional python extra**: The 35 comic tests need uharfbuzz (optional extra comic). test_comic_checks and test_comic_text call importorskip; test_comic_layout does not. uharfbuzz is installed in the dev venv, so all 35 ran.
* **png export**: No test calls cairosvg or writes a PNG. The only mentions are one comment and the README link check.

The ids behind each bullet are in the JSON under `external_dependencies`.

## 8. Indexes of private and internal names

The tests touch 165 distinct names: 108 private functions (105 used by live tests, plus the 3 below), 47 private constants, 10 non-underscore names that `character.py` or `skeleton.py` holds but `__init__` does not export (`BODY_TYPES`, `COAT_CUTS`, `SKIRT_CUTS`, `COLLAR_CUTS`, `BOOT_CUTS`, `KNEE_SOCK_CUT`, `RIBBON_CUT`, `ADULT_FACE_AGE`, `HAND_STYLES`, `GarmentCut`), and the 3 private functions of cover.py that only dropped tests use (section 8.4). Names are `module.name`. A name is a function, a constant or a class by reading its definition line in `src/`.

Method: an AST walk of each test and of the module-level helpers it calls (`_walk`, `_highest_ink`, `_torso_widest`, `_hand_numbers`, `_tunic_off`, `_path_xs`, `_soft`, `_irises`), collecting attribute reads on `character`, `catalogue`, `skeleton` and `cover` and imports of underscore names; I checked the result against my reading of every test. It cannot see an attribute reached through a registry entry (`HAIRSTYLES[name].mass`, `BODY_TYPES[...].head_scaled`), so those are listed by hand under `needs.extra` in the JSON.

The head of the distribution is flat. The most-used private function is needed by 11 tests if all are ported as written; 102 live tests touch at least one private name, and most names are touched by exactly one test. So the tests do not give a strong dependency order for Phase 4: the order comes from the part-call graph, and what the audit adds is the short list in 8.1 that the port must expose.

### 8.1 Names the port must expose: needed by a PORT or PORT-WITH-FUNCTION test

| Name | Kind | Defined at | Tests recommended to port | Of which PORT-WITH-FUNCTION | Tests if all live tests are ported as written | Tests |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `character.BODY_TYPES` | constant | 5397 | 5 | 3 | 6 | a_body_profile_applies_at_the_chibi_build, tall_chibi_long_torso_is_tall_chibi_with_a_lower_belt_and_a_bigger_head, head_scaled_makes_the_head_bigger_against_the_same_body, a_body_profile_that_measures_the_wrist_moves_the_hand_and_the_rest_do_not |
| `character.ADULT_FACE_AGE` | constant | 605 | 3 | 0 | 3 | every_preset_is_at_least_twenty_one, a_character_from_outside_is_never_drawn_below_the_floor, the_gui_age_slider_starts_at_twenty_one |
| `character._stroke_w` | function | 44 | 2 | 2 | 9 | hair_stays_under_the_canvas_ceiling, the_crotch_reads_the_real_knee |
| `character._arm_line` | function | 8291 | 2 | 2 | 6 | every_relaxed_hand_keeps_a_hands_footprint, a_body_profile_that_measures_the_wrist_moves_the_hand_and_the_rest_do_not |
| `character._hair_fall` | function | 3614 | 2 | 2 | 4 | the_front_hair_adds_no_silhouette, hair_stays_under_the_canvas_ceiling |
| `character._draw_cut` | function | 6054 | 1 | 1 | 5 | a_cuts_holes_are_left_open_under_the_even_odd_rule |
| `character._head_edge_x` | function | 12043 | 1 | 1 | 5 | the_ear_stays_welded_to_the_skull |
| `character._crotch_y` | function | 10994 | 1 | 1 | 3 | the_crotch_reads_the_real_knee |
| `character.GarmentCut` | class | 5698 | 1 | 1 | 2 | a_cuts_holes_are_left_open_under_the_even_odd_rule |
| `character.HAND_STYLES` | constant | 10507 | 1 | 1 | 2 | every_relaxed_hand_keeps_a_hands_footprint |
| `character._hair_edge_x` | function | 12063 | 1 | 1 | 2 | the_cap_covers_the_hair_it_is_tied_over |
| `character._limb_build` | function | 10909 | 1 | 1 | 2 | every_relaxed_hand_keeps_a_hands_footprint |
| `character._LONG_TORSO_HEAD_SCALE` | constant | 5425 | 1 | 1 | 1 | tall_chibi_long_torso_is_tall_chibi_with_a_lower_belt_and_a_bigger_head |
| `character._SCARF_EDGE_Y` | constant | 5055 | 1 | 1 | 1 | the_cap_covers_the_hair_it_is_tied_over |
| `character._SOFT_LOCK_HIGH_RISE` | constant | 13230 | 1 | 1 | 1 | the_tones_keep_the_hair_saturation |
| `character._ear_outer` | function | 12340 | 1 | 1 | 1 | the_ear_stays_welded_to_the_skull |
| `character._hand` | function | 10733 | 1 | 1 | 1 | every_relaxed_hand_keeps_a_hands_footprint |
| `character._headscarf` | function | 5063 | 1 | 1 | 1 | the_cap_covers_the_hair_it_is_tied_over |
| `character._limb_taper_at` | function | 10904 | 1 | 1 | 1 | the_limbs_taper_with_the_height |
| `character._mouth_depth_share` | function | 7039 | 1 | 1 | 1 | an_opening_beyond_the_width_does_not_make_the_mouth_taller_than_wide |
| `skeleton._WIDTH_FOLLOW` | constant | 257 | 1 | 1 | 1 | the_height_stretches_below_the_shoulders_only |

Also needed by those tests but not underscore-named: the `Hairstyle` fields `mass`, `hairline`, `locks`, `covers_ears`, the `BodyProfile` methods `head_scaled` and `applied`, `Expression.applied_to`, runtime field lists for `Outfit`, `CharacterParams` and `FaceStyle`, and (for the 3 REWRITE tests and the 1 COVERED test that monkeypatch `HAIRSTYLES`) a mutable or injectable registry. From `colorutil`: `hex_to_rgb01`, `rgb01_to_hex`, `shade`, `lit_tone`, `soft_shadow_tone`, `highlight_rise`, plus a TS `colorsys` for the checks.

### 8.2 Every private function, by number of tests (all live tests, as written)

| Name | Defined at | Tests | Items | Recommended to port | Sample tests |
| --- | ---: | ---: | ---: | ---: | --- |
| `character._eye_placement` | 12842 | 11 | 74 | 0 | a_look_to_the_side_keeps_the_i, the_blush_sits_below_the_eye_i, the_glasses_frame_the_eye_rath |
| `character._stroke_w` | 44 | 9 | 79 | 2 | a_mock_collar_hugs_the_neck_an, hair_stays_under_the_canvas_ce, the_topknot_is_visible_and_sti |
| `character._tunic` | 4764 | 8 | 12 | 0 | neckline_stand_raises_a_tab_ei, a_belt_worn_with_an_open_coat_, a_mock_collar_is_worn_under_an |
| `character._arm_line` | 8291 | 6 | 23 | 2 | sleeve_under_cap_slants_the_ca, the_katana_hangs_from_the_belt, the_bare_breasts_are_their_own |
| `character._arms` | 9890 | 6 | 8 | 0 | a_coat_sleeve_runs_to_the_wris, keikos_belt_is_worn_over_her_c, the_bare_arm_has_no_cap_and_no |
| `character._head_edge_x` | 12043 | 5 | 66 | 1 | the_ear_stays_welded_to_the_sk, the_sideburn_rides_the_jaw_rat, the_sideburn_never_narrows_on_ |
| `character._belt_band` | 11599 | 5 | 12 | 0 | a_dress_belt_carries_a_keeper_, a_sash_stays_a_wide_flat_band_, the_crystals_clear_the_buckle_ |
| `character._coat` | 6941 | 5 | 9 | 0 | a_belt_worn_with_an_open_coat_, the_lab_coat_leaves_the_shared, the_coats_lapel_actually_reach |
| `character._draw_cut` | 6054 | 5 | 5 | 1 | keikos_dress_is_a_column_not_a, keikos_belt_is_worn_over_her_c, an_open_coat_carries_the_line_ |
| `character._hair_fall` | 3614 | 4 | 18 | 2 | the_front_hair_adds_no_silhoue, hair_stays_under_the_canvas_ce, only_risa_wears_the_fringed_ha |
| `character._leg_gap_and_top` | 10861 | 4 | 9 | 0 | the_belt_covers_the_trouser_to, a_sock_hangs_on_each_leg_and_t, underwear_never_hangs_below_a_ |
| `character._torso` | 4605 | 4 | 8 | 0 | the_body_reads_no_garment, the_bare_body_is_closed_where_, the_bare_arm_has_no_cap_and_no |
| `character._face` | 13094 | 4 | 7 | 0 | the_beard_reaches_over_the_mou, the_drawn_lash_keeps_its_flick, eyes_set_wide_apart_a_mouth_se |
| `character._sleeve_hem_y` | 3844 | 4 | 4 | 0 | sleeve_under_cap_slants_the_ca, a_small_bust_moves_the_torso_a, the_bare_arm_has_no_cap_and_no |
| `character._boot` | 11457 | 3 | 23 | 0 | a_tall_boot_stops_below_the_kn, every_preset_renders_barefoot, the_loafers_sole_is_a_second_t |
| `character._belt_drawn` | 11633 | 3 | 8 | 0 | a_dress_belt_carries_a_keeper_, keikos_belt_is_worn_over_her_c, the_belt_covers_the_trouser_to |
| `character._belt` | 11625 | 3 | 5 | 0 | a_belt_worn_with_an_open_coat_, keikos_belt_is_worn_over_her_c, a_tucked_tunic_and_its_trouser |
| `character._hand_centre` | 8343 | 3 | 5 | 0 | staff_stays_in_hand_and_on_the, the_traced_hands_draw_and_the_, the_fist_grips_a_held_staff_on |
| `character._traced_coat` | 5955 | 3 | 5 | 0 | keikos_belt_is_worn_over_her_c, the_coats_lapel_actually_reach, a_blazer_wearers_arm_shows_the |
| `character._legs_and_boots` | 10914 | 3 | 4 | 0 | a_tucked_tunic_and_its_trouser, the_hakama_is_drawn_over_whate, the_bare_leg_stops_at_the_sock |
| `character._bust_lines` | 4270 | 3 | 3 | 0 | the_line_under_the_bust_sits_u, the_bare_breasts_are_their_own, the_tunic_s_line_follows_the_b |
| `character._collar` | 7696 | 3 | 3 | 0 | a_mock_collar_hugs_the_neck_an, a_mock_collar_is_worn_under_an, the_shirt_collar_is_two_open_w |
| `character._crotch_y` | 10994 | 3 | 3 | 1 | the_crotch_reads_the_real_knee, underwear_never_hangs_below_a_, a_bare_risa_tucks_the_waist_th |
| `character._garment_placement` | 5673 | 3 | 3 | 0 | garment_placement_is_the_ident, a_traced_cut_widens_at_the_bus, a_cut_is_the_identity_on_the_b |
| `character._traced_coat_and_belt` | 5959 | 3 | 3 | 0 | keikos_belt_is_worn_over_her_c, a_mock_collar_is_worn_under_an, the_hip_pockets_and_the_button |
| `character._outline_w` | 131 | 2 | 64 | 0 | the_moustache_is_thicker_than_, the_eye_stays_inside_the_face |
| `character._eye_quads` | 12497 | 2 | 63 | 0 | the_eye_stays_inside_the_face, the_drawn_lash_keeps_its_flick |
| `character._hair_mass` | 3692 | 2 | 21 | 0 | the_ear_is_over_the_back_hair_, the_topknot_is_visible_and_sti |
| `character._limb_build` | 10909 | 2 | 18 | 1 | the_traced_hands_draw_and_the_, every_relaxed_hand_keeps_a_han |
| `character._katana_placement` | 9161 | 2 | 10 | 0 | the_katana_hangs_from_the_belt, a_longer_katana_keeps_its_tip_ |
| `character._hair_edge_x` | 12063 | 2 | 9 | 1 | the_cap_covers_the_hair_it_is_, the_goggle_strap_arms_end_insi |
| `character._katana` | 9216 | 2 | 9 | 0 | a_katana_is_worn_only_when_ask, a_longer_katana_keeps_its_tip_ |
| `character._katana_stretched` | 9144 | 2 | 9 | 0 | katana_length_stretches_the_sc, a_longer_katana_keeps_its_tip_ |
| `character._cap_tip_y` | 3905 | 2 | 4 | 0 | sleeve_under_cap_slants_the_ca, a_bust_changes_nothing_above_t |
| `character._hakama` | 8100 | 2 | 4 | 0 | the_hakama_is_pleated_not_a_pl, the_hakama_is_drawn_over_whate |
| `character._traced_placement` | 10642 | 2 | 4 | 0 | the_traced_hands_draw_and_the_, the_fist_stays_level_as_the_ar |
| `character._beard` | 7190 | 2 | 3 | 0 | the_sideburn_rides_the_jaw_rat, the_beard_reaches_over_the_mou |
| `character._neck` | 3786 | 2 | 3 | 0 | the_bare_body_is_closed_where_, a_bare_risa_raises_the_shoulde |
| `character._body_knots` | 5605 | 2 | 2 | 0 | garment_placement_is_the_ident, a_traced_cut_widens_at_the_bus |
| `character._bust_over_arms` | 4175 | 2 | 2 | 0 | the_bust_comes_over_the_arms_a, the_bare_breasts_are_their_own |
| `character._bust_shape` | 4088 | 2 | 2 | 0 | a_loose_garment_hangs_from_the, the_line_under_the_bust_sits_u |
| `character._eye` | 12626 | 2 | 2 | 0 | an_iris_set_against_the_inner_, a_dot_nose_and_a_shaded_lid_ar |
| `character._skirt` | 8153 | 2 | 2 | 0 | keikos_dress_is_a_column_not_a, the_pleated_skirt_is_traced_on |
| `character._eye_lash` | 12579 | 1 | 60 | 0 | the_eye_stays_inside_the_face |
| `character._ears` | 12354 | 1 | 20 | 0 | the_ear_is_over_the_back_hair_ |
| `character._head` | 12422 | 1 | 20 | 0 | the_ear_is_over_the_back_hair_ |
| `character._hand` | 10733 | 1 | 15 | 1 | every_relaxed_hand_keeps_a_han |
| `character._headscarf` | 5063 | 1 | 8 | 1 | the_cap_covers_the_hair_it_is_ |
| `character._belt_line_half_w` | 11585 | 1 | 6 | 0 | a_sash_stays_a_wide_flat_band_ |
| `character._apron` | 8051 | 1 | 4 | 0 | an_apron_is_no_taller_than_it_ |
| `character._nose_y` | 13030 | 1 | 4 | 0 | the_moustache_is_thicker_than_ |
| `character._glasses` | 7355 | 1 | 3 | 0 | the_glasses_frame_the_eye_rath |
| `character._grip_channel` | 10566 | 1 | 3 | 0 | the_traced_hands_draw_and_the_ |
| `character._hand_traced` | 10592 | 1 | 3 | 0 | the_traced_hands_draw_and_the_ |
| `character._crystal_layout` | 11873 | 1 | 2 | 0 | the_crystals_clear_the_buckle_ |
| `catalogue._base_points` | 712 | 1 | 1 | 0 | none_of_them_is_a_preset_or_of |
| `catalogue._cast_points` | 708 | 1 | 1 | 0 | none_of_them_is_a_preset_or_of |
| `character._bare_breast_spine` | 4371 | 1 | 1 | 0 | the_bare_breasts_are_their_own |
| `character._bare_breasts` | 4418 | 1 | 1 | 0 | the_bare_breasts_are_their_own |
| `character._bare_shoulder_sk` | 3935 | 1 | 1 | 0 | a_bare_risa_raises_the_shoulde |
| `character._blindfold` | 7601 | 1 | 1 | 0 | the_blindfold_is_off_by_defaul |
| `character._blush` | 12985 | 1 | 1 | 0 | the_blush_warms_on_dark_skin_a |
| `character._breast_ellipse` | 4351 | 1 | 1 | 0 | the_tunic_s_line_follows_the_b |
| `character._brow` | 13065 | 1 | 1 | 0 | eyes_set_wide_apart_a_mouth_se |
| `character._brows_over_hair` | 13087 | 1 | 1 | 0 | eyes_set_wide_apart_a_mouth_se |
| `character._bust_fold` | 4298 | 1 | 1 | 0 | the_outer_layers_answer_the_bu |
| `character._cap_underside_y` | 3891 | 1 | 1 | 0 | sleeve_under_cap_slants_the_ca |
| `character._chain_points` | 10529 | 1 | 1 | 0 | the_open_hand_is_squared_at_th |
| `character._chest_lines` | 4514 | 1 | 1 | 0 | the_chest_lines_and_the_navel_ |
| `character._chest_pockets` | 7789 | 1 | 1 | 0 | the_tunic_s_own_parts_go_with_ |
| `character._coat_buttons` | 6008 | 1 | 1 | 0 | the_hip_pockets_and_the_button |
| `character._draw_leg_cut` | 6147 | 1 | 1 | 0 | a_sock_hangs_on_each_leg_and_t |
| `character._ear_outer` | 12340 | 1 | 1 | 1 | the_ear_stays_welded_to_the_sk |
| `character._eye_closed` | 12779 | 1 | 1 | 0 | closed_eyes_are_a_lash_line_sp |
| `character._eye_shape` | 12529 | 1 | 1 | 0 | closed_eyes_are_a_lash_line_sp |
| `character._face_track` | 12134 | 1 | 1 | 0 | the_sideburn_never_narrows_on_ |
| `character._fist_grips` | 10582 | 1 | 1 | 0 | the_fist_grips_a_held_staff_on |
| `character._goggle_geometry` | 7431 | 1 | 1 | 0 | the_goggle_strap_arms_end_insi |
| `character._goggles` | 7487 | 1 | 1 | 0 | the_goggles_lift_off_the_eye_r |
| `character._goggles_strap` | 7446 | 1 | 1 | 0 | the_goggle_strap_arms_end_insi |
| `character._hair_front` | 13417 | 1 | 1 | 0 | the_fringed_hair_draws_its_dar |
| `character._hair_knot` | 6806 | 1 | 1 | 0 | the_topknot_is_visible_and_sti |
| `character._hands_after_coat` | 10223 | 1 | 1 | 0 | a_blazer_wearers_arm_shows_the |
| `character._hip_pockets` | 6000 | 1 | 1 | 0 | the_hip_pockets_and_the_button |
| `character._jaw_track` | 12105 | 1 | 1 | 0 | the_sideburn_never_narrows_on_ |
| `character._katana_stretch_factor` | 9136 | 1 | 1 | 0 | katana_length_stretches_the_sc |
| `character._leg_tuck_top_y` | 11010 | 1 | 1 | 0 | underwear_never_hangs_below_a_ |
| `character._limb_taper_at` | 10904 | 1 | 1 | 1 | the_limbs_taper_with_the_heigh |
| `character._mask` | 7545 | 1 | 1 | 0 | the_mask_hangs_from_under_the_ |
| `character._mouth_depth_share` | 7039 | 1 | 1 | 1 | an_opening_beyond_the_width_do |
| `character._navel` | 4563 | 1 | 1 | 0 | the_chest_lines_and_the_navel_ |
| `character._placket` | 7754 | 1 | 1 | 0 | the_tunic_s_own_parts_go_with_ |
| `character._quad_x_at` | 5574 | 1 | 1 | 0 | a_loose_garment_hangs_from_the |
| `character._rib_skeleton` | 4582 | 1 | 1 | 0 | a_bare_risa_tucks_the_waist_th |
| `character._ribbon` | 7744 | 1 | 1 | 0 | the_ribbon_is_five_pieces_tied |
| `character._robe_front` | 6842 | 1 | 1 | 0 | the_outer_layers_answer_the_bu |
| `character._shoulder_bars` | 10171 | 1 | 1 | 0 | the_shoulder_bars_are_counted_ |
| `character._skirt_bottom_y` | 11154 | 1 | 1 | 0 | underwear_never_hangs_below_a_ |
| `character._skirt_half_w` | 7859 | 1 | 1 | 0 | keikos_dress_is_a_column_not_a |
| `character._skirt_hem_y` | 7869 | 1 | 1 | 0 | the_chibi_hem_pull_back_is_flo |
| `character._sleeve_under_cap` | 3863 | 1 | 1 | 0 | the_bare_arm_has_no_cap_and_no |
| `character._staff_placement` | 8727 | 1 | 1 | 0 | staff_stays_in_hand_and_on_the |
| `character._tail_tie` | 5028 | 1 | 1 | 0 | the_goggles_do_not_leave_the_p |
| `character._underpants` | 11167 | 1 | 1 | 0 | underwear_never_hangs_below_a_ |
| `character._underwear_top` | 4460 | 1 | 1 | 0 | the_underwear_top_is_drawn_bar |

### 8.3 Private constants and unexported module names

| Name | Kind | Defined at | Tests (live) | Recommended to port |
| --- | --- | ---: | ---: | ---: |
| `character.BODY_TYPES` | constant | 5397 | 6 | 5 |
| `character.COAT_CUTS` | constant | 6411 | 6 | 0 |
| `character.ADULT_FACE_AGE` | constant | 605 | 3 | 3 |
| `character.SKIRT_CUTS` | constant | 6254 | 3 | 0 |
| `character.HAND_STYLES` | constant | 10507 | 2 | 1 |
| `character._KATANA_TIP_U` | constant | 9131 | 2 | 0 |
| `character._MOUTH_REALISTIC_DROP` | constant | 7081 | 2 | 0 |
| `character._MOUTH_Y` | constant | 7054 | 2 | 0 |
| `character._EYE_ASPECT` | constant | 12473 | 2 | 0 |
| `character.COLLAR_CUTS` | constant | 6159 | 2 | 0 |
| `character.GarmentCut` | class | 5698 | 2 | 1 |
| `character.KNEE_SOCK_CUT` | constant | 9275 | 2 | 0 |
| `character._BEARD_TOP` | constant | 7104 | 2 | 0 |
| `character._FRINGED_SHADE` | constant | 3271 | 2 | 0 |
| `character._GARMENT_REF_BODY` | constant | 5530 | 2 | 0 |
| `character._EYE_EDGE_CLEAR` | constant | 13062 | 1 | 0 |
| `character._EYE_OUTLINE_W` | constant | 12485 | 1 | 0 |
| `character._SOFT_LOCK_HIGH_RISE` | constant | 13230 | 1 | 1 |
| `character._SCARF_EDGE_Y` | constant | 5055 | 1 | 1 |
| `character._BEARD_LIP_H` | constant | 7187 | 1 | 0 |
| `character._BEARD_NOSE_GAP` | constant | 7175 | 1 | 0 |
| `character._BODY_INSET` | constant | 4750 | 1 | 0 |
| `character._KATANA_GUARD_HALF_V` | constant | 9112 | 1 | 0 |
| `skeleton._WIDTH_FOLLOW` | constant | 257 | 1 | 1 |
| `character.BOOT_CUTS` | constant | 9303 | 1 | 0 |
| `character.RIBBON_CUT` | constant | 9550 | 1 | 0 |
| `character._BARE_NECK_BELOW_CHIN` | constant | 3918 | 1 | 0 |
| `character._BARE_PELVIS` | constant | 10991 | 1 | 0 |
| `character._BEARD_SIDEBURN_OUT` | constant | 7113 | 1 | 0 |
| `character._BEARD_SIDEBURN_W_BOT` | constant | 7134 | 1 | 0 |
| `character._BEARD_SIDEBURN_W_EASE` | constant | 7144 | 1 | 0 |
| `character._BEARD_SIDEBURN_W_TOP` | constant | 7133 | 1 | 0 |
| `character._BEARD_SIDEBURN_Y` | constant | 7109 | 1 | 0 |
| `character._BEARD_SIDE_INSET` | constant | 7105 | 1 | 0 |
| `character._BLUSH` | constant | 12978 | 1 | 0 |
| `character._BLUSH_DARK` | constant | 12980 | 1 | 0 |
| `character._BLUSH_DARK_OPACITY` | constant | 12981 | 1 | 0 |
| `character._BLUSH_OPACITY` | constant | 12979 | 1 | 0 |
| `character._BUST_KNOTS` | constant | 5535 | 1 | 0 |
| `character._COAT_BUTTONS` | constant | 9882 | 1 | 0 |
| `character._FRINGED_BASE_TIP` | constant | 2872 | 1 | 0 |
| `character._FRINGED_OPENINGS` | constant | 3240 | 1 | 0 |
| `character._FRINGED_STRANDS` | constant | 3063 | 1 | 0 |
| `character._GOGGLE_DX_SCALE` | constant | 7417 | 1 | 0 |
| `character._GOGGLE_LIFT` | constant | 7414 | 1 | 0 |
| `character._GOGGLE_R_SCALE` | constant | 7418 | 1 | 0 |
| `character._HAND_FIST_UPRIGHT` | constant | 10496 | 1 | 0 |
| `character._HAND_OPEN` | constant | 10563 | 1 | 0 |
| `character._KATANA_STRETCH_FROM` | constant | 9128 | 1 | 0 |
| `character._KATANA_STRETCH_TO` | constant | 9129 | 1 | 0 |
| `character._KATANA_TRACED_LENGTH` | constant | 9130 | 1 | 0 |
| `character._LEG_CUT_OUT` | constant | 6113 | 1 | 0 |
| `character._LONG_TORSO_HEAD_SCALE` | constant | 5425 | 1 | 1 |
| `character._ROBE_BUST_LINE` | constant | 5549 | 1 | 0 |
| `character._SCLERA_SHADOW` | constant | 12567 | 1 | 0 |
| `character._STAFF_GRIP` | constant | 8381 | 1 | 0 |
| `character._STAFF_WOOD` | constant | 8386 | 1 | 0 |

### 8.4 Names needed only by dropped tests

`cover._mist_band`, `cover._placement`, `cover._preset_for_cover`.

## 9. TypeScript-side needs the tests reveal

* **An XML parser.** 26 live functions call `ET.fromstring`; 5 read structure (children of the root, namespaced `<metadata>` lookups, `itertext`, stroke widths) and the rest only check well-formedness. Node has no built-in XML parser (verified: `DOMParser` and `XMLSerializer` are `undefined` on Node v22.22.3) and `ts/node_modules` holds none (marked, qrcode-generator, typescript, undici-types, ws). Options: add a dev dependency (any small SAX or DOM parser), or replace the structural checks with regexes (the five tree-reading tests can be done with regexes on `<rect`, `<metadata>` and `stroke-width`), and replace well-formedness by byte equality. No test needs a CSS or XPath engine.
* **Regex only** for the rule tests that matter most (`test_ids`, flat has no gradients, byte budget): they need no parser.
* **`colorsys`** in the test code itself (colorutil and soft locks use `colorsys.rgb_to_hsv` as the checker): the kernel's hand-written `colorsys` serves.
* **Runtime field lists** for `Outfit`, `CharacterParams`, `FaceStyle` (Python `dataclasses.fields`, `__dataclass_fields__`); 9 live functions use them, in the catalogue checks and in tests that switch every `*_color` off. `ts/src/params.ts` already generates a 134-field registry (docs/ts-port-spike.md), which serves.
* **UTF-8 byte length** (`Buffer.byteLength`) for the byte budgets (150,000 bytes per soft document).
* **A mutable or injectable `HAIRSTYLES`** for the 4 tests that swap a `Hairstyle` with a different or synthetic `locks` callable (pytest `monkeypatch.setitem`).
* **Object identity** (`is`) of the skeleton returned by `_rib_skeleton` and `_bare_shoulder_sk` is asserted in 2 tests, both COVERED-BY-ORACLE; a TS port need not keep the shortcut.

## 10. Surprises and what could not be determined

1. **The plan's figure of 288 is functions, not items.** Collected items are 1,052; 44 ids come from one function (`test_ids`) and 260 from one (`test_an_expression_changes_the_mood_and_nothing_else`).
2. **I count 14 test files, not 15** (4,715 lines).
3. **`test_open_mouth.py` is not comic code**, although its docstring says "the comic's first expressions". It imports nothing from `comic/`; all 12 are render tests (9 COVERED-BY-ORACLE, 2 PORT, 1 PORT-WITH-FUNCTION).
4. **The roster is 20 presets**, while `CLAUDE.md` and several docstrings say fourteen or seventeen. Parametrised counts follow the code.
5. **The comic tests ran** only because `uharfbuzz` is installed in the dev venv. Two of the three comic files call `importorskip`; `test_comic_layout.py` does not, and I did not check whether it imports without the extra.
6. **17 live functions lean on Python vocabulary** the TS will not have: 9 on `dataclasses.fields`, 4 on `monkeypatch.setitem`, 2 on `is` identity of a returned skeleton, and 2 on a `"None"` literal check (the TS equivalent of the leak is `undefined`). All are marked.
7. **No test reads a web or companion path**; the only `local/` access is in two cover tests (dropped). The web tool's contract is guarded only indirectly, by the catalogue tests and ref-out/bases.
8. **Two guard tests protect a hard project constraint** (adult floor: `test_every_preset_is_at_least_twenty_one`, `test_a_character_from_outside_is_never_drawn_below_the_floor`, plus the age slider). They are cheap and must outlive the oracle.
9. **One test guards a Python-only bug class**: `test_the_drawn_lash_keeps_its_flick_inside_the_face` exists because a local shadowed a parameter. It stays COVERED-BY-ORACLE.

Could not determine:

* Whether each COVERED-BY-ORACLE test would fail under the mutation gate; I did not run mutations, and the claim rests on reading each assertion against the stage record described in the plan.
* Which of the 105 private functions used by live tests the TS parts will expose under their camelCase names (plan 5.2 says one TS file per module with the same names); the index is by Python name.
* The test sensitivity of the Python tests themselves (I did not break the Python to see which tests catch it).
* Behaviour on a second platform: the run is macOS arm64 only.
* Whether the web tool's `catalogue.json` consumer needs more guards than the byte-equal file; no web test exists to read.

## 11. Per-file sections

Columns: `n` is collected items; class is primary, with other tags in brackets; needs lists every private or unexported name the test reaches, transitively through its local helpers (module prefix dropped, `character` unless shown; the public names, the earliest port gate and the full reason are in the JSON) and markers `[xml]` (parser), `[fx]` (pytest fixture), `[fs]` (file system), `[local]` (local/ folder). The last column is the property protected, then the reason for the recommendation.

### test_smoke.py

161 functions, 761 items. PORT 25, PORT-WITH-FUNCTION 12, COVERED-BY-ORACLE 106, REWRITE 3, DROP 15.

| Test | n | Class | Needs | Recommendation | Protects. Why |
| --- | ---: | --- | --- | --- | --- |
| named_characters_render | 20 | R (O) | [xml] | COVERED-BY-ORACLE P3 | Every preset renders to well-formed XML with more than 10 top-level elements (parts did not drop out). Every preset is in the corpus and compared byte for byte; well-formedness and element count follow. |
| every_hairstyle_renders_on_a_default_character | 8 | R (O) | [xml] | COVERED-BY-ORACLE P3 | Every registered hairstyle renders to well-formed XML on a default character. Corpus sweeps every hairstyle value; byte equality implies well-formed. |
| neutral_bases_render_and_stay_out_of_the_cast | 2 | O (R) | [xml] | PORT P2 | The web tool neutral bases render, and a base name is never a PRESETS key. Registry-membership assertion is not an output diff; the render half is covered. Wellformedness check can become an endsWith check. |
| ref_out_bases_match_the_code | 2 | REF (O) | [fs] | PORT P1 | ref-out/bases/<id>.svg equals render_character(NEUTRAL_BASES[id]) byte for byte. Direct compare of TS output with committed SVGs (highest value). |
| render_is_deterministic | 1 | O | - | PORT P1 | Two renders of one preset in one process are identical. Oracle compares TS once to Python; it cannot see module-level state or cache leakage between two TS calls. |
| id_prefix_default_leaves_the_render_unchanged | 1 | O | - | COVERED-BY-ORACLE P3 | An empty id_prefix is the same document as no id_prefix. Both forms are corpus cases; Python has them equal so TS equal by transitivity. |
| id_prefix_namespaces_every_id_and_reference | 1 | R (O) | - | COVERED-BY-ORACLE P3 | Every defined id and every url(#..) reference gains the prefix, nothing dangles or is shared (regex over the SVG text). Corpus includes odd id_prefix values and byte equality; the rule holds in Python output so holds in TS. Regex only, no XML parser. |
| arm_out_default_leaves_the_render_unchanged | 1 | O (R) | - | COVERED-BY-ORACLE P3 | Arm swing 0 emits no rotate group and renders as the default; a non-zero swing emits one. right_arm_out/left_arm_out swept in corpus; build_skeleton(heads, frame) is public. |
| arm_out_swings_the_hand_away_from_the_body | 1 | R (O) | - | COVERED-BY-ORACLE P3 | A 40 degree right_arm_out moves some coordinate further left than the hanging arm reaches (regex over all x y pairs). Direction of the swing is a property of the specific output; sweep case plus byte equality covers it. |
| garment_placement_is_the_identity_on_the_traced_body | 1 | I | _GARMENT_REF_BODY, _body_knots, _garment_placement | COVERED-BY-ORACLE P3 | A traced cut maps to itself on the body it was traced from and landmark to landmark on the chibi. Placement maths is reached only through traced-cut renders; any error shows in stage hashes. |
| a_traced_cut_draws_at_the_chibi_build | 1 | O | - | COVERED-BY-ORACLE P3 | Setting collar_cut=None changes Katherina output (cuts replace the shared garment at the chibi build). collar_cut field sweep on a preset. |
| a_body_profile_applies_at_the_chibi_build | 1 | O | BODY_TYPES | PORT P1 | skeleton_for applies the BODY_TYPES profile waist and foot landmarks while keeping build. Value-level test of skeleton_for and BODY_TYPES, both Phase 3 foundation; no SVG involved. |
| staff_stays_in_hand_and_on_the_canvas | 1 | I (R) | _STAFF_GRIP, _STAFF_WOOD, _hand_centre, _staff_placement | COVERED-BY-ORACLE P3 | Staff wood control polygon stays inside the canvas, the grip sits on the hand and the foot on the ground; staff_color=None removes it. Specific to Katherina; staff geometry is output covered. |
| the_figure_is_drawn_on_transparency | 20 | R (O) | [xml] | PORT P1 | No full-size background rect unless background= is passed; then exactly one with that fill (eye sclera fill=white must not count). Render option background is not named in the corpus design; needs XML parse or a regex for rect width=100% height=100%. |
| ref_out_matches_the_code | 20 | REF (O) | [fs] | PORT P1 | ref-out/<preset>.svg equals render_character(preset, skeleton_for(preset)) byte for byte. Direct compare of TS output with committed SVGs (highest value). |
| the_retired_builds_left_nothing_behind | 1 | P (REF) | [fs] | REWRITE P2 | ref-out/ holds no *_real.* files and no real/ directory. Repo hygiene on committed files, language neutral; trivial fs.readdirSync node:test after cutover. |
| the_ear_stays_welded_to_the_skull | 1 | I (R) | _ear_outer, _head_edge_x | PORT-WITH-FUNCTION P2 | The ear outer contour stays outside the skull edge at every sampled point, so an ear never loses its lower half. Family rule that guards later retuning of jaw taper; port _ear_outer and _head_edge_x. |
| the_ear_is_over_the_back_hair_and_under_the_face | 20 | I (R) | _ears, _hair_mass, _head | COVERED-BY-ORACLE P3 | Z-order: hair mass, then ear, then head (substring index order in the SVG); cuts that cover ears draw no ear. The oracle records each layer by index so z-order is compared directly. Needs _hair_mass, _ears, _head only if ported as written. |
| the_front_hair_adds_no_silhouette | 8 | I (R) | _hair_fall | PORT-WITH-FUNCTION P2 | The hairline closing edge never leaves the hair mass polygon (pure geometry on the Hairstyle mass and hairline tables). Family rule over every hairstyle that guards authoring of new cuts after cutover (the oracle cannot judge a new cut); port _hair_fall and the Hairstyle.mass and .hairline callables. |
| sleeve_under_cap_slants_the_cap_and_the_arm_top_with_it | 1 | I (R) | _arm_line, _cap_tip_y, _cap_underside_y, _sleeve_hem_y [xml] | COVERED-BY-ORACLE P3 | The arm top outer corner lands on the slanted cap underside, and that point is printed in the SVG. Specific numbers present in the output of one preset. |
| neckline_stand_raises_a_tab_either_side_of_the_neck | 1 | I (R) | _tunic [xml] | COVERED-BY-ORACLE P3 | Stand-collar tunic path passes through the neck edge at the shoulder line and raises a tab 0.06 head radii above it. Substring checks in the _tunic output of one preset. |
| neckline_stand_defers_to_a_collar_and_a_round_neckline | 1 | O | - | COVERED-BY-ORACLE P3 | neckline_stand is ignored when a collar colour or a round neckline is set. Param-pair equivalence; both sides are corpus cases. |
| waist_shift_moves_the_belt_line_and_nothing_above_or_below_it | 2 | O (R) | [xml] | PORT P1 | waist_shift moves waist_y and hip_y by 0.3 head radii and leaves other anchors alone; ignored when a skeleton is handed in. Value-level on skeleton_for (Phase 3) plus one render equivalence. |
| tall_chibi_long_torso_is_tall_chibi_with_a_lower_belt_and_a_bigger_head | 1 | I (O) | BODY_TYPES, _LONG_TORSO_HEAD_SCALE | PORT-WITH-FUNCTION P1 | BODY_TYPES long-torso profile equals tall_chibi with waist and hip +0.5 and head_scaled(1.1); default body names. Data-relationship rule on BODY_TYPES; needs _LONG_TORSO_HEAD_SCALE and BodyProfile.head_scaled. |
| head_scaled_makes_the_head_bigger_against_the_same_body | 1 | I | BODY_TYPES | PORT-WITH-FUNCTION P1 | BodyProfile.head_scaled(s) changes only the head against the body, by exactly s; head_scaled(1.0) is identity. Numeric contract of BodyProfile.head_scaled/applied (Phase 3), no SVG. |
| a_tall_boot_stops_below_the_knee_not_at_the_belt | 2 | I (R) | _boot | COVERED-BY-ORACLE P3 | With boot_shaft=1.0 on either body the boot path top is not above the real knee. boot_shaft field sweep and random combos; regex on path text. |
| a_belt_worn_with_an_open_coat_is_drawn_under_it | 3 | I (R) | _belt, _coat, _tunic | COVERED-BY-ORACLE P3 | Z-order: belt before coat when a coat is worn; coatless belt after the tunic. Layer order is part of the by-index stage record. |
| keikos_dress_is_a_column_not_a_flared_skirt | 1 | I (O) | SKIRT_CUTS, _draw_cut, _skirt, _skirt_half_w | COVERED-BY-ORACLE P3 | Keiko skirt is the column cut and stays inside the coat opening (cut data narrower than 0.40). Reached through Keiko render and SKIRT_CUTS data. |
| the_lab_coats_opening_pinches_at_the_waist | 1 | I | COAT_CUTS | COVERED-BY-ORACLE P3 | The lab_coat cut inner edge narrows toward the waist and widens again (data check on COAT_CUTS). Cut data is output covered; no independent logic. |
| the_lab_coat_leaves_the_shared_coat_alone | 1 | I (O) | COAT_CUTS, _coat | COVERED-BY-ORACLE P3 | COAT_CUTS holds open_jacket and lab_coat; gero, kyoko and tomohiro still draw the shared coat. Three presets in the corpus. |
| a_coat_sleeve_runs_to_the_wrist_in_the_coats_colour | 1 | I (R) | _arms | COVERED-BY-ORACLE P3 | Coat sleeves are filled in the coat colour, show no tunic colour, and carry a round-cap cuff line. Substring checks on _arms output of one preset. |
| a_dress_belt_carries_a_keeper_either_side_of_the_buckle | 1 | I (R) | _belt_band, _belt_drawn | COVERED-BY-ORACLE P3 | A dress belt has two keeper loops above the band and no shade band; other presets keep one keeper. Output properties of specific presets; belt_keeper_pair swept. |
| keikos_belt_is_worn_over_her_coat_and_her_arms_over_both | 1 | I (R) | COAT_CUTS, _arms, _belt, _belt_drawn, _draw_cut, _traced_coat, _traced_coat_and_belt | COVERED-BY-ORACLE P3 | Z-order for Keiko: coat, then belt, then arms; Katherina jacket after armless arms, hands after jacket; over_arms flags. Layer order recorded by index in stages; needs _hands_after_coat group only if ported as written. |
| a_mock_collar_hugs_the_neck_and_covers_the_tunics_v | 1 | I (R) | _collar, _stroke_w | COVERED-BY-ORACLE P3 | Mock collar is at 1.03 neck half-widths, two paths, a thin seam line, below the chin and reaching below the V. Substring and regex checks on _collar output of one preset. |
| a_mock_collar_is_worn_under_an_open_coat | 1 | I (R) | _collar, _traced_coat_and_belt, _tunic | COVERED-BY-ORACLE P3 | Z-order: the mock collar before the traced coat, the standing collar after the tunic. Layer order in stage record. |
| a_sash_stays_a_wide_flat_band_on_every_chibi_body | 6 | I (R) | _belt_band, _belt_line_half_w | COVERED-BY-ORACLE P3 | On each body a sash is at least 3.3 times as wide as deep and never thinner than a belt. Proportion guard on three specific presets. |
| an_apron_is_no_taller_than_it_is_wide_on_every_chibi_body | 4 | I (R) | _apron | COVERED-BY-ORACLE P3 | Apron path height is at most 1.02 times its width on both bodies. Regex over the _apron path of two presets. |
| the_crystals_clear_the_buckle_and_stay_on_the_belt | 2 | I | _belt_band, _crystal_layout | COVERED-BY-ORACLE P3 | Crystal layout keeps the middle pair off the buckle and the outer strap within the belt end. Layout maths of one preset. |
| the_belt_covers_the_trouser_tops | 6 | I (R) | _belt_drawn, _leg_gap_and_top | COVERED-BY-ORACLE P3 | The belt rect half-width reaches the trouser outer edge on both bodies. Regex on _belt_drawn output of three presets. |
| a_katana_is_worn_only_when_asked_for | 1 | I (O) | _katana | COVERED-BY-ORACLE P3 | katana_color None draws no sword; the cast values for satoshi and tomohiro. Field sweep plus preset values. |
| the_katana_hangs_from_the_belt_on_the_left_and_clears_the_arm | 2 | I | _KATANA_GUARD_HALF_V, _arm_line, _belt_band, _katana_placement | COVERED-BY-ORACLE P3 | Katana guard on the viewer right at the belt, tip above the soles, guard edge inside the arm inner edge. Geometry of one preset on two bodies. |
| a_sheet_tile_draws_the_figure_on_its_own_body | 3 | P (O,I) | - | DROP | sheet.render_sheet embeds the figure drawn on skeleton_for (not build_skeleton). sheet.py is out of port scope (D5); stays on frozen Python. |
| katana_length_stretches_the_scabbard_and_nothing_else | 1 | I | _KATANA_STRETCH_FROM, _KATANA_STRETCH_TO, _KATANA_TIP_U, _KATANA_TRACED_LENGTH, _katana_stretch_factor, _katana_stretched | COVERED-BY-ORACLE P3 | _katana_stretched(1.0) is identity; longer scales only the scabbard span; cap keeps its size. katana_length swept in corpus; maths reached only through render. |
| a_longer_katana_keeps_its_tip_off_the_floor | 8 | I | _KATANA_TIP_U, _katana, _katana_placement, _katana_stretched | COVERED-BY-ORACLE P3 | For lengths 0.8 to 1.4 on both bodies the tip stays above the soles. Generic over length but katana_length is a corpus sweep field. |
| haruto_and_daizen_carry_full_length_katanas_and_satoshi_the_short_one | 1 | O | - | COVERED-BY-ORACLE P3 | Preset values: satoshi katana_length 0.95; haruto and daizen more than 1.15. Gate 3 asdict deep-equal of every preset. |
| sleeve_under_cap_defers_to_a_traced_jacket | 1 | O | - | COVERED-BY-ORACLE P3 | sleeve_under_cap is ignored under a traced jacket. Param-pair equivalence on a preset. |
| a_tucked_tunic_and_its_trousers_meet_inside_the_belt | 1 | I (R) | _belt, _belt_band, _legs_and_boots, _tunic | COVERED-BY-ORACLE P3 | Tucked tunic hem and trouser top fall inside the belt band; belt drawn after trousers; untucked both meet at the hip. Numbers parsed from part output; part order in stage record. |
| hair_stays_under_the_canvas_ceiling | 8 | I (R) | _hair_fall, _stroke_w | PORT-WITH-FUNCTION P2 | The highest ink of every hairstyle crown stays at or below the canvas top (solves each quadratic for its extremum). Family rule that guards new or retuned cuts after cutover; port _hair_fall, _stroke_w and the Hairstyle.mass callables. Not an SVG parse. |
| ref_out_cover_matches_the_code | 1 | P (REF,C) | [fx][fs][local] | DROP | ref-out/cover.svg equals cover.render_cover() with ACC_LOCAL_DIR pointed away from local/. cover.py not ported (D5); monkeypatches ACC_LOCAL_DIR because cover.py reads local/cover_faces.json. |
| the_byline_is_not_the_subtitle | 1 | P | [xml] | DROP | Cover subtitle and byline y positions are ordered title < subtitle < byline. cover.py not ported. |
| the_cover_renders_and_stays_deterministic | 1 | P | - | DROP | Cover render is deterministic and contains the title lines. cover.py not ported. |
| the_cover_stays_flat | 1 | P (R) | - | DROP | No gradient, filter, blur or opacity in the cover page furniture before the figure group. cover.py not ported. |
| the_figure_stands_on_the_page | 1 | P (I) | cover._placement | DROP | Cover figure placement is inside the trim and mist keyed to the soles. cover.py not ported (uses cover._placement). |
| an_expression_changes_the_mood_and_nothing_else | 260 | O (R) | [xml] | PORT P1 | Expression.applied_to moves only mood fields and leaves face identity fields, hairstyle and outfit untouched; result renders. Value-level contract of EXPRESSIONS over every preset; the render half is covered. |
| the_readme_shows_every_character | 20 | P | [fs] | REWRITE P2 | README.md links ref-out/on-white/<preset>.png for every preset and no *_real copy. Repo hygiene reading README.md; keep as a node test (or fold into a docs check) after cutover. |
| the_disguise_changes_only_the_disguise | 2 | O | - | COVERED-BY-ORACLE P3 | Kyoko/Satoko and Tomohiro/Satoshi differ only by outfit, hair colour and scar side (same eye colour, face, frame). Gate 3 asdict deep-equal of every preset pins these relations. |
| an_outer_layer_is_visible_against_what_it_covers | 20 | O | - | PORT P2 | Every coat or robe colour differs from the tunic by at least 12 luminance (garment would otherwise be invisible). Data rule over PRESETS that also guards new presets after cutover; pure values, local luminance helper. |
| the_topknot_is_visible_and_still_fits | 1 | I (R) | _hair_knot, _hair_mass, _stroke_w | COVERED-BY-ORACLE P3 | The topknot crown sits above the cut under it (not buried) yet below the canvas margin at -1.36 head radii. Specific to Haruto; numbers parsed from _hair_knot output. |
| the_sideburn_rides_the_jaw_rather_than_chording_it | 1 | I (R) | _BEARD_TOP, _beard, _head_edge_x | COVERED-BY-ORACLE P3 | The beard strip outer edge keeps its share of the skull half-width (no chord across the cheek), read off the drawn path. Specific to Reinhard beard output. |
| the_sideburn_never_narrows_on_its_way_down | 1 | I | _BEARD_SIDEBURN_OUT, _BEARD_SIDEBURN_W_BOT, _BEARD_SIDEBURN_W_EASE, _BEARD_SIDEBURN_W_TOP, _BEARD_SIDEBURN_Y, _BEARD_SIDE_INSET, _BEARD_TOP, _face_track, _head_edge_x, _jaw_track | COVERED-BY-ORACLE P3 | The sideburn strip never narrows toward the jaw and its end meets the jaw track exactly (computed, not parsed). Geometry tracks of one beard; the _face_track/_jaw_track maths is output covered. |
| the_beard_reaches_over_the_mouth_and_the_mouth_survives_it | 2 | I (R) | _MOUTH_REALISTIC_DROP, _MOUTH_Y, _beard, _face | COVERED-BY-ORACLE P3 | Beard rises above the mouth line near the centre and is drawn before the face so the mouth survives (z-order). Two presets; layer order in stage record. |
| the_moustache_is_thicker_than_the_line_that_draws_it | 4 | I | _BEARD_LIP_H, _BEARD_NOSE_GAP, _MOUTH_REALISTIC_DROP, _MOUTH_Y, _nose_y, _outline_w, _stroke_w | COVERED-BY-ORACLE P3 | The band between the moustache lobe and the lip is at least twice the outline width, at face_age 0 and 1. Constant-relation guard for two presets; face_age swept in corpus. |
| the_cap_covers_the_hair_it_is_tied_over | 8 | I (R) | _SCARF_EDGE_Y, _hair_edge_x, _headscarf | PORT-WITH-FUNCTION P2 | For every hairstyle the headscarf arc is at least as wide as the hair edge and still on the canvas (read off the drawn arc). Family rule over every hairstyle (a scarf can be put on any cut) that guards new cuts after cutover. |
| the_glasses_frame_the_eye_rather_than_a_second_guess_at_it | 3 | I (R) | _EYE_ASPECT, _eye_placement, _glasses | COVERED-BY-ORACLE P3 | Each glasses rim rect contains the eye aperture for three face shapes (default, wide-small, asymmetric lids). Reached through glasses renders; eye_width, eye_openness, eye_lower_lid swept. |
| the_coats_lapel_actually_reaches_the_neck | 3 | I (R) | _coat, _traced_coat | COVERED-BY-ORACLE P3 | Each shared-coat panel top rises above the shoulder line and sits beside the neck, not at the shoulder (skipped when the preset wears a traced coat). Specific to three presets; skip is for Keiko (traced coat). |
| the_hakama_is_pleated_not_a_plain_panel | 2 | I (R) | _hakama | COVERED-BY-ORACLE P3 | _hakama output has exactly 7 pleat <line> elements. Count over one part output of two presets. |
| the_hakama_is_drawn_over_whatever_is_on_the_legs | 2 | I (R) | _hakama, _legs_and_boots | COVERED-BY-ORACLE P3 | Z-order: legs before hakama. Layer order in stage record. |
| the_chibi_hem_pull_back_is_floored_at_half | 1 | I | _skirt_hem_y | COVERED-BY-ORACLE P3 | A 0.95 hem lands more than 0.3 of the hip-to-ankle span below a 0.20 hem at chibi. Maths of one function, reached via skirt_length renders. |
| the_goggles_lift_off_the_eye_rather_than_frame_it | 1 | I (R) | _eye_placement, _goggles | COVERED-BY-ORACLE P3 | Goggle lens circles sit clearly above the brow line (regex on circle elements). Specific to Krista output. |
| the_goggles_do_not_leave_the_ponytail_tie_exposed | 1 | I | _GOGGLE_DX_SCALE, _GOGGLE_LIFT, _GOGGLE_R_SCALE, _eye_placement, _tail_tie | COVERED-BY-ORACLE P3 | Less than 5 percent of the tail tie bounding box overlaps the goggle lens box. Specific to Krista; constants and tie anchor. |
| the_goggle_strap_arms_end_inside_the_hair_not_past_it | 1 | I (R) | _goggle_geometry, _goggles_strap, _hair_edge_x | COVERED-BY-ORACLE P3 | Each goggle strap arm tip lies inside the hair edge (regex over path d). Specific to Krista output. |
| the_sheet_renders_and_stays_deterministic | 1 | P (R) | [xml] | DROP | sheet.render_sheet is deterministic and well formed. sheet.py not ported (D5). |
| every_roster_member_appears_once | 1 | P (O) | - | DROP | Every roster member is labelled exactly once on its sheet and no roster lists a name twice. The check renders sheets (not ported); the no-duplicate-member half is small and could join the roster data test. |
| every_character_has_a_display_name_and_a_roster | 1 | O | - | PORT P2 | Every preset has a DISPLAY_NAMES entry and appears on some ROSTERS entry. Cross-registry data rule over presets, DISPLAY_NAMES and ROSTERS; not an SVG diff; guards new presets. |
| ref_out_sheet_matches_the_code | 1 | P (REF) | [fs] | DROP | ref-out/sheet.svg equals sheet.render_sheet(). sheet.py not ported; the committed SVG stays Python-regenerated (D5). |
| ref_out_sheet_satoshi_matches_the_code | 1 | P (REF) | [fs] | DROP | ref-out/sheet_satoshi.svg equals the satoshi-roster sheet. sheet.py not ported (D5). |
| the_satoshi_roster_is_satoshis_persona_not_satokos | 1 | O | - | PORT P2 | ROSTERS["satoshi"] leads with satoshi, excludes satoko and kyoko, keeps tomohiro, is alphabetical after the lead and equals cast minus the swapped pair. Value test of ROSTERS in presets (ported); Gate 3 compares PRESETS only. |
| the_sheet_scales_every_figure_the_same | 1 | P (R) | - | DROP | All figures on the sheet use one scale(...) value. sheet.py not ported. |
| the_cover_wears_its_chosen_expression | 1 | P (O) | cover._placement, face | DROP | CoverParams default expression is hollow and the cover figure face equals EXPRESSIONS["hollow"].on(satoshi face). cover.py not ported; the Expression.on value contract is covered by the expression test. |
| mist_band_is_the_covers_own_bank | 1 | P (I) | cover._mist_band | DROP | cover.mist_band equals cover._mist_band. cover.py not ported. |
| closed_eyes_are_a_lash_line_spanning_the_open_aperture | 1 | I (R) | _eye_closed, _eye_shape | COVERED-BY-ORACLE P3 | Closed eyes draw no eye-l/eye-r ids; the lash line starts and ends on the open almond corners. eyes_closed is a corpus field; synthetic call of _eye_shape/_eye_closed adds nothing the stage compare does not see. |
| a_skeleton_with_no_bust_is_the_skeleton_built_without_one | 1 | O | - | PORT P1 | build_skeleton(bust=0.0) equals the default skeleton and bust_reach is 0.0. Value-level on build_skeleton (Phase 3); skeleton equality via deepEqual. |
| the_bust_rides_a_profiled_body_rather_than_the_one_it_replaced | 1 | O | - | PORT P1 | bust_y lies between shoulder_y and waist_y on a profiled body and moves down with waist_shift. Value-level on skeleton_for (Phase 3), no SVG. |
| a_small_bust_moves_the_torso_a_small_amount | 1 | I (R) | _sleeve_hem_y, _tunic | COVERED-BY-ORACLE P3 | The torso width is continuous at bust 0 and grows with the dial (regex over the _tunic path). bust swept in corpus; byte equality at each value implies the continuity. |
| a_bust_changes_nothing_above_the_armpit | 3 | I (R) | _cap_tip_y, _tunic | COVERED-BY-ORACLE P3 | Tunic path points above the sleeve cap tip are identical at bust 1.0 and 0.0. Specific to three presets; bust field swept. |
| the_body_reads_no_garment | 4 | I | _torso | COVERED-BY-ORACLE P3 | _torso output does not depend on the outfit. Outfit fields are swept; TS layer must equal Python layer in every case, so any read of the outfit shows. |
| the_bust_comes_over_the_arms_at_the_chibi | 1 | I (R) | _bust_over_arms | COVERED-BY-ORACLE P3 | _bust_over_arms is empty with no bust, uses a mask and a clip id, and ids differ between bust sizes. Substring checks on part output. |
| a_traced_cut_widens_at_the_bust_and_nowhere_else | 1 | I | _BUST_KNOTS, _GARMENT_REF_BODY, _body_knots, _garment_placement | COVERED-BY-ORACLE P3 | Garment placement moves out at the bust height only, not at shoulder or waist knots. Placement maths reached through bust x traced-cut renders. |
| a_loose_garment_hangs_from_the_bust_where_the_body_tucks_under_it | 1 | I | _bust_shape, _quad_x_at | COVERED-BY-ORACLE P3 | Below the fullest point a draped garment hangs clear of the body tuck and meets it at the waist. Bust shape object maths; output covered. |
| the_line_under_the_bust_sits_under_it_and_fades_in | 1 | I (R) | _bust_lines, _bust_shape | COVERED-BY-ORACLE P3 | No bust line at bust 0; otherwise two tapered paths under each breast whose thickness grows with the dial up to 0.5. Bust dial swept in corpus. |
| the_bare_body_is_closed_where_it_shows | 2 | I (R) | _BODY_INSET, _neck, _stroke_w, _torso | COVERED-BY-ORACLE P3 | With nothing covering it the neck lines stop at the body shoulder line and the torso runs down to the hip. Regex on part output of two presets. |
| every_preset_renders_with_its_tunic_off | 20 | R (O) | - | REWRITE P1 | With tunic_color None no Python "None" literal leaks into the SVG, for every preset. Keep the intent as a no-leak rule: no "undefined", "null", "NaN" or "None" token in any render of every preset with each optional colour off (the TS failure mode is undefined, not None). |
| the_tunic_s_own_parts_go_with_it | 1 | I | _chest_pockets, _placket, _tunic | COVERED-BY-ORACLE P3 | With the tunic off, _tunic, _placket and _chest_pockets draw nothing; worn they draw. Part output of two presets; tunic_color swept. |
| the_bare_breasts_are_their_own_shape_over_the_arms | 1 | I (R) | _arm_line, _bare_breast_spine, _bare_breasts, _bust_lines, _bust_over_arms | COVERED-BY-ORACLE P3 | With the tunic off the bare breast shape equals _bust_lines, starts at the arm inner top corner, and is masked over the arms. Part output of two presets. |
| the_underwear_top_is_drawn_bare_with_a_bust_or_when_asked | 1 | I (O) | _underwear_top | COVERED-BY-ORACLE P3 | The underwear top is drawn only with the tunic off and a bust, or when underwear_top asks, in underwear_color. underwear_top and underwear_color swept. |
| the_underpants_have_height_on_every_preset | 20 | R (O) | - | PORT P2 | With tunic and trousers off, the underwear path of every preset has non-trivial height (hem not above top). Public API plus a regex; a generic rule over every preset that the corpus may not combine (tunic and trousers off together). |
| the_bare_arm_has_no_cap_and_no_line_across_its_top | 1 | I (R) | _arms, _sleeve_hem_y, _sleeve_under_cap, _stroke_w, _torso | COVERED-BY-ORACLE P3 | With the tunic off the arm takes no cap slant and draws no top line; a tunic keeps both. Part output of one preset. |
| the_crotch_reads_the_real_knee | 1 | I | _crotch_y, _stroke_w | PORT-WITH-FUNCTION P2 | Skeleton knee_y is halfway hip to ankle, boot_y above hip, and the crotch sits below the hip. Skeleton value assertions are Phase 3; the _crotch_y part needs exposing (or the crotch line is output covered). |
| every_preset_renders_barefoot | 20 | I (R) | _boot | COVERED-BY-ORACLE P3 | With boot_color None every preset renders without a "None" and the foot is skin tone with no laces. The no-leak half moves to the REWRITE rule; the foot half is part output (_boot). |
| the_chest_lines_and_the_navel_are_bare_only | 1 | I | _chest_lines, _navel | COVERED-BY-ORACLE P3 | Chest lines and navel appear only with the tunic off, chest lines only with chest>0 and no bust. Part output of three presets. |
| the_blush_warms_on_dark_skin_and_holds_on_the_cast | 1 | I | _BLUSH, _BLUSH_DARK, _BLUSH_DARK_OPACITY, _BLUSH_OPACITY, _blush | COVERED-BY-ORACLE P3 | _blush returns the fixed pink on every preset skin, the dark rose on #442617 and an interpolated tone between. skin_tone swept; value is a colour kernel (round half to even hazard) the record-and-replay already tests. |
| the_tunic_s_line_follows_the_bare_breast | 1 | I (R) | _breast_ellipse, _bust_lines, _stroke_w | COVERED-BY-ORACLE P3 | The tunic line under the bust matches the bare breast ellipse extremes. Regex on bust line output of one preset. |
| the_outer_layers_answer_the_bust | 1 | I | _ROBE_BUST_LINE, _bust_fold, _coat, _robe_front | COVERED-BY-ORACLE P3 | A robe front carries the bust fold; an open coat differs with and without a bust; no bust gives no fold. Part output of two presets; bust swept. |
| an_open_coat_carries_the_line_on_its_panels_only | 1 | I (R) | COAT_CUTS, _coat, _draw_cut | COVERED-BY-ORACLE P3 | The lab coat bust line is masked and drawn between panels 1 and 2 of 4 coat paths; absent with no bust. Order inside one part output of two presets. |
| an_old_link_loads_as_the_tall_chibi | 1 | M (O) | - | PORT P1 | params_from_dict maps heads=6.0 and body=None to the default body and long_traced_real to long_traced, rendering as the preset. Legacy-link migration is codec behaviour; keep as a urlstate test (corpus has URL round trips but not necessarily these retired keys). |
| an_old_link_with_an_eye_style_loads_with_the_one_eye | 2 | M (O) | - | PORT P1 | A link carrying retired eye_style and eye_glow fields loads and renders as the preset. Legacy-link migration (unknown keys ignored) in urlstate.params_from_dict. |
| face_age_up_to_one_matures_only_the_head | 3 | O (R) | [xml] | PORT P1 | face_age up to 1 raises face_build above build and leaves the body (skeleton with face_maturity 0) equal to the age-0 one. Value-level on skeleton_for/Skeleton equality (Phase 3). |
| face_age_above_one_is_aged_on_the_grown_face | 2 | O | - | COVERED-BY-ORACLE P3 | face_age 1+y renders identically to presets.aged(face, y) with face_age 1. Param-pair equivalence; face_age is swept beyond range; presets.aged is a public presets function. |
| the_lash_renders_across_its_range | 3 | R (O) | [xml] | COVERED-BY-ORACLE P3 | FaceStyle.lash 0, 0.5 and 1.0 render; the default lash is 1.0. lash swept in corpus; default is covered by Gate 3. |
| the_eye_stays_inside_the_face | 60 | I (R) | _EYE_EDGE_CLEAR, _EYE_OUTLINE_W, _eye_lash, _eye_placement, _eye_quads, _head_edge_x, _outline_w, _stroke_w | COVERED-BY-ORACLE P3 | At every face age and at the top of the web tool eye size and width, the eye outer corner and the lash flick stay inside the face edge. Bounds at swept extremes; byte equality on those cases carries the property. |
| the_drawn_lash_keeps_its_flick_inside_the_face | 3 | I (R) | _eye_placement, _eye_quads, _face, _head_edge_x | COVERED-BY-ORACLE P3 | The lash flick, read off the rendered face, runs past the eye corner and stays inside the face. Guards a Python local-variable shadowing bug that cannot recur in the same form in TS; output covered. |
| the_bare_knee_grows_in_without_a_jump | 1 | R (O) | - | PORT P1 | Rendering a bare figure at height 0.8 and 0.8001 changes no tag numeric by more than 0.25 (continuity at the taper threshold). Cross-render continuity rule on the public API (regex over tags); not an output diff, and needs both heights in the corpus to be covered. Needs the Outfit colour-field list (Outfit.__dataclass_fields__). |
| the_limbs_taper_with_the_height | 1 | I | _limb_taper_at | PORT-WITH-FUNCTION P1 | _limb_taper_at is 0 up to height 0.8, 0.5 from 1.3, linear between; skeleton carries limb_taper. Pure numeric function plus Skeleton field (Phase 3); no SVG. |
| the_height_stretches_below_the_shoulders_only | 2 | I (R) | skeleton._WIDTH_FOLLOW [xml] | PORT-WITH-FUNCTION P1 | height stretches below the shoulder line: widths follow by _WIDTH_FOLLOW, neck does not, torso and legs split 1 to 2, knee halfway. Value-level on skeleton_for; imports skeleton._WIDTH_FOLLOW. |
| the_traced_hands_draw_and_the_mitten_is_the_default | 3 | I (R) | _arm_line, _arms, _grip_channel, _hand_centre, _hand_traced, _limb_build, _traced_placement [xml] | COVERED-BY-ORACLE P3 | hand_style traced differs from the mitten default; the old grip name reads; a bare wrist is left open under a drawn hand. hand_style swept; part functions only reached through render. Needs the Outfit field list. |
| every_relaxed_hand_keeps_a_hands_footprint | 15 | I (R) | HAND_STYLES, _arm_line, _hand, _limb_build | PORT-WITH-FUNCTION P2 | Every hand style draws a hand 0.28 to 0.46 head radii tall with height over width 0.6 to 1.3. Family rule over the HAND_STYLES registry that guards a new hand style after cutover; needs _hand, _arm_line, _limb_build and HAND_STYLES. |
| each_hand_style_draws_and_differs_from_the_mitten | 12 | R (O) | HAND_STYLES [xml] | COVERED-BY-ORACLE P3 | Every non-mitten hand style renders well formed and differs from the mitten; the default stays mitten. hand_style swept; HAND_STYLES registry is data. |
| the_fist_grips_a_held_staff_only_and_the_old_grip_name_still_reads | 1 | I (O,R) | _fist_grips, _hand_centre [xml] | COVERED-BY-ORACLE P3 | grip_style fist changes only the staff-holding hand; with no staff it draws as default; hand_style grip equals fist. Param-pair equivalences and part functions. |
| the_fist_stays_level_as_the_arm_swings | 1 | I | _HAND_FIST_UPRIGHT, _traced_placement | COVERED-BY-ORACLE P3 | The fist mapping turns back against the arm swing by _HAND_FIST_UPRIGHT of it. Rotation maths via _traced_placement, output covered at swept swings. |
| the_open_hand_is_squared_at_the_wrist | 1 | I | _HAND_OPEN, _chain_points | COVERED-BY-ORACLE P3 | The traced open hand wrist end is a flat cross-cut as wide as the sides (data check on _HAND_OPEN via _chain_points). Traced data table, rendered in the corpus. |
| every_preset_is_at_least_twenty_one | 1 | O | ADULT_FACE_AGE | PORT P1 | Every preset face_age is at least ADULT_FACE_AGE and every neutral base at least 1.0. Hard project constraint (adult floor); data rule that must outlive the oracle. Needs ADULT_FACE_AGE exposed. |
| a_character_from_outside_is_never_drawn_below_the_floor | 1 | M (O) | ADULT_FACE_AGE | PORT P1 | params_from_dict raises any face_age below the floor to ADULT_FACE_AGE and keeps 1.4. Hard project constraint at the URL, web and companion entry; urlstate behaviour, keep as a unit test even with URL corpus. |
| every_garment_off_still_leaves_the_underwear | 1 | O (R) | - | PORT P1 | With every *_color outfit field None except underwear_color, both briefs and top are drawn (two or more uses of the colour). Coverage-floor rule on the public API; needs the Outfit colour-field list (fields(Outfit)). |
| the_gui_age_slider_starts_at_twenty_one | 1 | O (M) | ADULT_FACE_AGE | PORT P1 | catalogue.AGE.lo equals ADULT_FACE_AGE. Hard project constraint at the web tool; catalogue value, needs ADULT_FACE_AGE exposed. |
| a_cover_reads_its_local_face_ages | 1 | P (I) | cover._preset_for_cover [fx][local] | DROP | cover._preset_for_cover reads local/cover_faces.json (via ACC_LOCAL_DIR) to change a face age. cover.py not ported; depends on the untracked local/ folder. |
| the_blindfold_is_off_by_default_and_sits_above_the_eyes | 1 | I (R) | _blindfold, _eye_placement | COVERED-BY-ORACLE P3 | No blindfold without blindfold_color; with it the band lowest point stays above the eye. Part output of one preset; blindfold_color swept. |
| the_mask_hangs_from_under_the_chin_and_is_off_by_default | 1 | I (R) | _mask | COVERED-BY-ORACLE P3 | No mask without mask_color; with it the top edge is above the chin and the hem hangs a quarter radius below. Part output of one preset. |
| the_wristband_is_worn_on_one_wrist_only_and_carries_its_text | 1 | I (R) | _arms | COVERED-BY-ORACLE P3 | One wristband on the chosen side with its text once; none without a colour; the two sides differ. Part output; wristband fields swept. |
| the_wristband_text_is_text_and_never_markup | 1 | R (O) | [xml] | PORT P1 | Hostile wristband text (</text><script>...) is drawn as letters: the SVG stays well formed and gains no script element. Security rule on user text; render-only API. XML parse (or entity-escape string check) needed; the corpus may not hold hostile text and hazard 19 says escape covers only & < >. |
| the_shoulder_bars_are_counted_on_one_shoulder_of_a_coat | 1 | I (R) | _shoulder_bars | COVERED-BY-ORACLE P3 | shoulder_bars=3 draws three bars; side flips the board; no coat or colour draws nothing. Part output of one preset; fields swept. |
| a_cut_is_the_identity_on_the_body_it_was_traced_on | 1 | I | _garment_placement | COVERED-BY-ORACLE P3 | _garment_placement(sk, body) returns traced points unchanged on tall_chibi and tall_slender. Placement maths via traced-cut renders (Risa and the cast). |
| the_older_cuts_still_read_the_tall_chibi_and_mios_read_her_own | 1 | I | BOOT_CUTS, COAT_CUTS, COLLAR_CUTS, KNEE_SOCK_CUT, SKIRT_CUTS | COVERED-BY-ORACLE P3 | COAT/COLLAR/SKIRT cut registries have ref_body tall_chibi except risa cuts (tall_slender); BOOT_CUTS and KNEE_SOCK_CUT per_leg. Registry data; a wrong ref_body changes the render of any cut-field case. |
| only_risa_wears_the_knee_sock_and_the_loafer | 1 | O | - | COVERED-BY-ORACLE P3 | Only the risa preset sets knee_sock_color and boot_cut; Outfit defaults are None. Gate 3 asdict deep-equal of every preset and Outfit defaults. |
| risa_stands_on_her_own_longer_body | 1 | I (O) | BODY_TYPES | COVERED-BY-ORACLE P3 | BODY_TYPES["tall_slender"].heads exceeds the long-torso heads by more than 1. Data value reached by the Risa render. |
| a_sock_hangs_on_each_leg_and_the_left_mirrors_the_right | 1 | I (R) | KNEE_SOCK_CUT, _LEG_CUT_OUT, _draw_leg_cut, _leg_gap_and_top | COVERED-BY-ORACLE P3 | The knee sock cut is mirrored about head_cx and sits on the leg centre line. Part output of Risa. |
| the_bare_leg_stops_at_the_sock_top | 1 | I | _legs_and_boots | COVERED-BY-ORACLE P3 | _legs_and_boots uses a leg-above-sock clip only when a knee sock is worn. Part output. |
| the_loafers_sole_is_a_second_tone_of_the_shoes_own_leather | 1 | I | _boot | COVERED-BY-ORACLE P3 | The loafer draws the boot colour and shade(boot_color, 0.78); without boot_cut it is the ankle boot. Part output; shade is the colour kernel. |
| the_pleated_skirt_is_traced_on_her_own_body_with_six_folds | 1 | I (R) | SKIRT_CUTS, _skirt | COVERED-BY-ORACLE P3 | The pleated cut has one fill and six fold lines; the skirt draws one fill colour and six fill-none lines. Cut data and part output. |
| underwear_never_hangs_below_a_skirts_hem | 1 | I (R) | _crotch_y, _leg_gap_and_top, _leg_tuck_top_y, _skirt_bottom_y, _underpants | COVERED-BY-ORACLE P3 | _underpants with the skirt bottom cap ends above the cap while uncapped it would hang below; no skirt means no cap. Part output of Risa; needs _skirt_bottom_y, _leg_gap_and_top, _crotch_y, _leg_tuck_top_y, _underpants if ported as written. |
| a_bare_risa_tucks_the_waist_the_blazer_had_hidden | 1 | I | _BARE_PELVIS, _crotch_y, _leg_gap_and_top, _rib_skeleton, _torso | COVERED-BY-ORACLE P3 | _rib_skeleton returns a narrower skeleton only for undressed Risa and the same object for everyone else (identity check). Output covered; the identity (is) assertion is a Python-ism, TS should assert reference equality only if it keeps the shortcut. |
| a_bare_risa_raises_the_shoulder_the_blazer_measured | 1 | I | _BARE_NECK_BELOW_CHIN, _bare_shoulder_sk, _neck, _sleeve_hem_y | COVERED-BY-ORACLE P3 | _bare_shoulder_sk raises the shoulder to the chin plus _BARE_NECK_BELOW_CHIN only for bare Risa and returns the same skeleton otherwise. Output covered; same identity caveat. |
| the_shirt_collar_is_two_open_wings_on_her_own_body | 1 | I (R) | COLLAR_CUTS, _collar | COVERED-BY-ORACLE P3 | COLLAR_CUTS["shirt"] has two fills; the collar draws two paths in the collar colour. Cut data and part output. |
| a_shallow_neckline_notch_closes_the_tunic_higher_and_only_risa_sets_one | 1 | I (O) | _tunic | COVERED-BY-ORACLE P3 | Only Risa sets neckline_notch and it changes the tunic. Gate 3 plus field sweep. |
| the_ribbon_is_five_pieces_tied_in_order_with_a_slit_in_each_loop | 1 | I (R) | RIBBON_CUT, _ribbon | COVERED-BY-ORACLE P3 | RIBBON_CUT has five fills and holes in loops 2 and 3; the ribbon draws five fills and two even-odd slits. Cut data and part output. |
| only_risa_wears_a_ribbon | 1 | O | - | COVERED-BY-ORACLE P3 | Only Risa has ribbon_color; Outfit default None. Gate 3. |
| the_blazer_is_one_garment_with_two_lapels_and_heavy_lines | 1 | I (R) | COAT_CUTS, GarmentCut, _draw_cut | COVERED-BY-ORACLE P3 | COAT_CUTS["blazer"] has three fills, three lines, line_weight 1.0 (GarmentCut default 0.7), over_arms; draws accordingly. Cut data and part output; GarmentCut default is data. |
| a_blazer_wearers_arm_shows_the_shirt_past_the_sleeve_without_a_band | 1 | I (R) | _arms, _hands_after_coat, _traced_coat | COVERED-BY-ORACLE P3 | Risa arms are two white sleeves with no second-tone cuff band, under a traced coat drawn with hands after. Part output; _hands_after_coat group. |
| only_risa_wears_a_blazer_with_pockets_and_buttons | 1 | O | - | COVERED-BY-ORACLE P3 | Only Risa sets hip_pocket_color, coat_button_color and coat_cut blazer. Gate 3. |
| the_hip_pockets_and_the_buttons_are_drawn_with_the_coat | 1 | I (R) | _COAT_BUTTONS, _coat_buttons, _hip_pockets, _traced_coat_and_belt | COVERED-BY-ORACLE P3 | Two pocket flaps and three buttons drawn after the garment; none without their colours or coat. Part output of Risa. |
| a_body_profile_that_measures_the_wrist_moves_the_hand_and_the_rest_do_not | 1 | I (O) | BODY_TYPES, _arm_line | PORT-WITH-FUNCTION P2 | Only tall_slender sets wrist_y; the arm line takes the measured wrist when set and derives it from the hip otherwise. Value-level over the BODY_TYPES registry and skeleton_for (Phase 3) plus _arm_line. |
| only_a_profile_that_measured_the_neck_narrows_it | 1 | I (O) | BODY_TYPES | PORT P1 | Only tall_slender sets neck_half_w, and it is at least a quarter narrower than the chibi neck. Value-level on BODY_TYPES and skeleton_for (Phase 3); needs BODY_TYPES exposed. |
| a_stretched_body_carries_its_measured_wrist_with_it | 1 | O | - | PORT P1 | At height 1.2 Risa wrist hangs lower in head radii yet keeps its place against the hip. Value-level on skeleton_for (Phase 3). |
| a_cuts_holes_are_left_open_under_the_even_odd_rule | 1 | I (R) | GarmentCut, _draw_cut | PORT-WITH-FUNCTION P1 | A GarmentCut hole is an extra subpath with fill-rule evenodd; no holes means no even-odd. Uses hand-built synthetic GarmentCut values, which the field-driven corpus cannot make; needs GarmentCut and _draw_cut. |
| only_risa_wears_the_fringed_hair_and_it_is_traced_to_her_own_length | 1 | I (O) | _FRINGED_BASE_TIP, _hair_fall | COVERED-BY-ORACLE P3 | Only Risa has long_fringed; her hair fall matches _FRINGED_BASE_TIP and the hairline is one closed outline. Gate 3 plus part data. |
| the_fringed_hair_draws_its_darker_tone_its_strands_and_its_ears_over_the_hair | 1 | I (R) | _FRINGED_OPENINGS, _FRINGED_SHADE, _FRINGED_STRANDS, _hair_front | COVERED-BY-ORACLE P3 | Fringed hair front draws two skin-colour ears and one clip per shade and strand; long_blunt draws none. Part output. |
| a_longer_haircut_stretches_the_fringed_tips_and_keeps_the_fringe | 1 | I | _hair_fall | COVERED-BY-ORACLE P3 | hair_length 0.9 lowers the fringed tips by more than 0.3 radii and leaves points above the cheek line unchanged. hair_length swept; Hairstyle.mass data. |
| the_new_face_fields_default_to_the_cast_and_only_risa_sets_them | 1 | O | - | COVERED-BY-ORACLE P3 | FaceStyle defaults for eye_gap, mouth_drop, brows_over_hair, brow_length; only Risa differs. Gate 3. |
| eyes_set_wide_apart_a_mouth_set_low_and_brows_over_the_hair | 1 | I (R) | _brow, _brows_over_hair, _eye_placement, _face | COVERED-BY-ORACLE P3 | eye_gap narrows the eyes; brows over hair draw two lines in their own part, none in the face; brow_length shortens; mouth_drop lowers the mouth. Part output; face fields swept. |
| an_iris_set_against_the_inner_corner_and_stretched_tall_only_on_risa | 1 | I (R) | _eye, _eye_placement | COVERED-BY-ORACLE P3 | Only Risa sets iris_inset and iris_aspect; her iris is scaled 1.5 tall and nearer the nose than the eye centre. Part output of _eye; Gate 3. |
| a_dot_nose_and_a_shaded_lid_are_opt_in_and_only_risa_has_them | 1 | I (O) | _SCLERA_SHADOW, _eye, _eye_placement, _face | COVERED-BY-ORACLE P3 | nose_dot and lid_shadow defaults off; only Risa sets them; the lid shadow draws _SCLERA_SHADOW. Gate 3 plus part output. |
| every_figure_on_a_sheet_has_its_own_ids | 1 | P (R) | - | DROP | Every figure on a sheet carries its preset name as an id prefix. sheet.py not ported; the id_prefix property itself is in the oracle corpus. |

### test_soft_locks.py

23 functions, 95 items. PORT 8, PORT-WITH-FUNCTION 2, COVERED-BY-ORACLE 8, REWRITE 3, DROP 2.

| Test | n | Class | Needs | Recommendation | Protects. Why |
| --- | ---: | --- | --- | --- | --- |
| the_flat_finish_ignores_the_clumps | 1 | R (I,P) | [fx] | COVERED-BY-ORACLE P3 | Replacing HAIRSTYLES["long_fringed"] with locks=None changes nothing in a flat render (pytest monkeypatch.setitem on the registry). Flat output equals Python flat output, which draws no clumps. A rewrite needs a mutable HAIRSTYLES registry or an injected style. |
| a_two_tone_cut_gets_its_clumps_again_in_the_tip_colour | 1 | R | - | COVERED-BY-ORACLE P3 | With hair_tip_color in soft there are two hair-front clump groups and a hair-tips clip. Soft plus tip colour param case. |
| a_near_white_tip_stays_clean_with_no_clumps_in_it | 2 | R | - | COVERED-BY-ORACLE P3 | A near-white tip takes no clumps and is repainted with #eceae3 under the hair-tips clip; one clump group remains. Soft preset cases. |
| the_clumps_are_one_group_clipped_to_the_front_hair | 1 | R | - | COVERED-BY-ORACLE P3 | Soft Risa has one hair-front clump group and a hair-front clip id. Soft preset case. |
| a_cut_without_locks_draws_exactly_as_it_did | 1 | R (I,P) | [fx] | REWRITE P1 | Soft Risa minus its clump group equals the soft render with locks=None (counterfactual via monkeypatch.setitem). A counterfactual the differential oracle cannot express (no Python output for a registry edit). Keep as a rule with an injectable or mutable HAIRSTYLES in TS. |
| every_preset_stays_within_the_byte_budget_soft | 20 | R | - | PORT P1 | Each preset soft document is at most 150000 UTF-8 bytes. Byte budget guard for runaway output (a rule, not a diff); measure with Buffer.byteLength. Budget 150000 raised on purpose by the owner. |
| the_clumps_are_deterministic | 1 | O | - | PORT P1 | Two soft Risa renders are identical. Determinism in TS across two calls (no RNG, no state); the oracle runs each case once. |
| every_lock_is_well_formed_and_under_the_ceiling | 25 | I (R) | - | PORT-WITH-FUNCTION P2 | Each authored cut locks(fall) returns roles shadow or lit with at least 3 points, width under 0.5, length in (0,1], \|x\|<2 and y>-1.55, for five falls. Family rule over authored cuts (Hairstyle.locks callables) that guards new cuts after cutover; Python filters AUTHORED by locks is not None. |
| an_unknown_role_is_refused | 1 | E (I,P) | [fx] | REWRITE P1 | A lock with role "glow" raises ValueError matching "shadow or lit" (text: a lock's role is shadow or lit, not 'glow'); registry swapped by monkeypatch. D12 error text with a synthetic lock (not oracle-expressible); needs an injectable HAIRSTYLES. |
| the_tones_keep_the_hair_saturation | 20 | I (O) | _SOFT_LOCK_HIGH_RISE | PORT-WITH-FUNCTION P1 | For every preset hair colour the lit tone keeps saturation (>=0.93 s0 when v0<0.7) and the shadow tone keeps >=0.9 s0 and lowers value. Design rule on colorutil.lit_tone, highlight_rise, soft_shadow_tone, hex_to_rgb01 and character._SOFT_LOCK_HIGH_RISE; checker uses colorsys. |
| the_front_shade_strips_sit_under_the_clumps_with_and_without_a_tip_colour | 1 | I (R) | _FRINGED_SHADE | COVERED-BY-ORACLE P3 | Soft Risa draws the front shade strips before the clump group (and again between the tip repaint and the tip clumps), clumps topmost; needs _FRINGED_SHADE count. Order of elements in one preset output. |
| the_byte_budget_holds_with_a_tip_colour_on_each_authored_cut | 2 | R | - | PORT P1 | Soft satoko and risa with hair_tip_color stay within 150000 bytes. Byte budget guard. |
| a_clump_too_short_to_draw_is_skipped_not_a_crash | 1 | R (I,P) | [fx] | REWRITE P1 | A synthetic lock set with tiny lengths (0.05, 0.02) renders without raising. Robustness against synthetic lock data the corpus cannot produce; needs an injectable HAIRSTYLES. |
| a_yellow_green_colour_is_not_nudged_toward_green | 1 | O | - | PORT P1 | lit_tone("#fff700", 0.0) keeps its hue within 0.002. Colour kernel property (colorsys hue); Phase 1 colorutil. |
| the_default_strength_is_the_authored_look_and_zero_draws_no_clumps | 1 | O | - | COVERED-BY-ORACLE P3 | highlight_strength defaults to 1.0, equals an explicit 1.0, and 0.0 draws no clump group. highlight_strength swept including 0. |
| a_higher_strength_moves_every_tone_further_from_the_hair_colour | 1 | O | - | PORT P1 | For five hair colours the shadow tone value falls and the lit tone value rises monotonically with gain 0, 0.5, 1. Monotonicity of colorutil.soft_shadow_tone and lit_tone (a rule the oracle checks only at sampled points). |
| the_strength_changes_the_drawing | 1 | O | - | COVERED-BY-ORACLE P3 | Soft Risa differs between strengths 1.0, 2.0 and 0.5. Strength sweeps. |
| a_strength_out_of_range_is_refused | 2 | E | - | PORT P1 | Soft render with highlight_strength -0.1 or 2.1 raises ValueError matching "highlight_strength" (text: highlight_strength must be between 0 and 2, not -0.1). D12; float repr of the value inside the message (hazard 15). |
| the_flat_finish_ignores_and_does_not_validate_the_strength | 3 | O | - | COVERED-BY-ORACLE P3 | Flat renders with strengths 0.3, 9.0 and -1.0 equal the default. Out-of-range strengths are corpus cases; the point is that validation does not run on flat. |
| a_strength_that_is_not_a_number_is_refused_for_soft_and_in_a_link | 4 | E (M) | - | PORT P1 | Soft render and params_from_dict both raise ValueError matching "highlight_strength" for "1", None, True and nan. D12; JS typeof rules differ (bool is not a number, nan is out of 0..2); includes the URL path. |
| the_cli_refuses_a_strength_out_of_range | 1 | P (E) | [fx] | DROP | generate.main with a highlight strength flag of 3 exits (argparse SystemExit). generate.py not ported. |
| the_cli_takes_a_strength | 1 | P | [fx][fs] | DROP | generate.main with a highlight strength flag of 0 writes an SVG with no clump group. generate.py not ported. |
| a_tip_colour_on_a_big_preset_stays_within_the_budget | 3 | R | - | PORT P1 | Katherina soft with a tip colour on short_layered, short_crop and long_parted stays within 150000 bytes. Byte budget guard on the heaviest cases. |

### test_catalogue.py

22 functions, 22 items. PORT 5, COVERED-BY-ORACLE 13, REWRITE 4.

| Test | n | Class | Needs | Recommendation | Protects. Why |
| --- | ---: | --- | --- | --- | --- |
| every_color_field_exists_on_character_params | 1 | O | - | REWRITE P2 | Every catalogue COLORS field names a CharacterParams field. In TS this is a compile-time keyof check plus a runtime field registry (Python reads dataclasses.fields); catalogue.json byte equality also catches it. |
| every_garment_field_exists_on_outfit | 1 | O | - | REWRITE P2 | Every garment colour, range and bool field in GARMENTS exists on Outfit. Same: compile-time keyof plus a runtime Outfit field list. |
| every_face_field_exists_on_facestyle | 1 | O | - | REWRITE P2 | Every FACE_RANGES, FACE_BOOLS and FACE_SELECTS field exists on FaceStyle. Same: compile-time keyof plus a runtime FaceStyle field list. |
| every_face_select_option_is_a_real_scar_side | 1 | O | - | COVERED-BY-ORACLE P3 | The scar_side select offers exactly {0, -1, 1}. Part of catalogue.json, which Gate 4 holds byte equal. |
| hair_tail_and_knot_fields_exist_on_character_params | 1 | O | - | REWRITE P2 | HAIR_TAIL.field and HAIR_KNOT.field are CharacterParams fields. Compile-time keyof plus runtime field list. |
| the_build_slider_and_the_compressed_chibi_are_retired | 1 | O | - | COVERED-BY-ORACLE P3 | build_catalogue() has no "build" key and every body id is non-null. catalogue.json byte equal (Gate 4). |
| every_hairstyle_label_is_a_real_hairstyle | 1 | O | - | COVERED-BY-ORACLE P3 | HAIRSTYLE_LABELS keys equal HAIRSTYLES keys. catalogue.json byte equal (Gate 4) and a TS typed registry. |
| every_cast_starting_point_is_in_presets | 1 | O | - | COVERED-BY-ORACLE P3 | Every cast starting point id is a PRESETS key. catalogue.json byte equal (Gate 4). |
| every_base_starting_point_is_a_neutral_base | 1 | O | - | COVERED-BY-ORACLE P3 | Catalogue base ids equal NEUTRAL_BASES keys in both directions. catalogue.json byte equal (Gate 4). |
| hair_length_extremes_render | 1 | R (O) | [xml] | COVERED-BY-ORACLE P3 | HAIR_LENGTH lo and hi render well formed SVG. Only if the corpus adds catalogue lo/hi extremes (it is built from dataclass fields, not the catalogue): add them explicitly. |
| hair_tail_extremes_render | 1 | R (O) | [xml] | COVERED-BY-ORACLE P3 | HAIR_TAIL lo and hi render well formed SVG. Same corpus requirement: catalogue extremes. |
| hair_knot_renders | 1 | R (O) | [xml] | COVERED-BY-ORACLE P3 | hair_knot=True renders well formed SVG. hair_knot swept in corpus. |
| every_garment_range_extreme_renders | 1 | R (O) | [xml] | COVERED-BY-ORACLE P2 | For every garment with ranges, each range lo and hi (with its colour switched on) renders well formed SVG. Same corpus requirement: add every catalogue garment range lo/hi with its colour on; otherwise PORT as a no-throw smoke. |
| face_range_extremes_render | 1 | R (O) | [xml] | COVERED-BY-ORACLE P3 | Every FACE_RANGES lo and hi renders well formed SVG. Same corpus requirement. |
| face_scar_options_render | 1 | R (O) | [xml] | COVERED-BY-ORACLE P3 | Every scar option renders well formed SVG. scar_side swept in corpus. |
| catalogue_json_matches_ref_out | 1 | REF (M) | [fs] | PORT P1 | to_json() equals the committed ref-out/catalogue.json byte for byte. Direct compare of TS output with a committed file (Gate 4); needs the Python-compatible JSON writer. |
| the_bust_slider_covers_every_preset_s_value | 1 | O | - | PORT P2 | The catalogue bust range is 0 to 1 and contains every preset bust. Cross-registry data rule that guards new presets after cutover. |
| the_chest_slider_covers_every_preset_s_value | 1 | O | - | PORT P2 | The catalogue chest range is 0 to 1 and contains every preset chest. Cross-registry data rule (guards new presets). |
| the_skin_swatches_include_the_default_and_render | 1 | O (R) | - | PORT P2 | The default skin tone is a swatch, and every swatch colour appears as a fill in the render. Public API plus catalogue; render half could be a corpus case, but the rule (swatch to fill) is cheap. |
| the_height_slider_covers_every_preset_and_its_ends_render | 1 | O (R) | [xml] | PORT P2 | The catalogue height range is 0.8 to 1.3, contains every preset height, and both ends render for every preset. Cross-registry rule; preset x height-extreme combos may not be in the corpus. |
| the_finish_controls_are_real_fields_with_a_label_for_every_finish | 1 | O | - | COVERED-BY-ORACLE P3 | FINISH_LABELS keys equal FINISHES; highlight_strength is a field with catalogue range 0 to 2; finishes listed in order. catalogue.json byte equal; field existence is a compile-time check. |
| a_soft_character_survives_a_link_and_renders | 1 | M (O) | - | COVERED-BY-ORACLE P3 | A soft Risa with highlight_strength 0.4 round trips through encode_params/decode_params and renders identically. URL round trips are corpus cases (Gate 3); float repr 0.4 is the hazard it exercises. |

### test_ids.py

1 functions, 44 items. PORT 1.

| Test | n | Class | Needs | Recommendation | Protects. Why |
| --- | ---: | --- | --- | --- | --- |
| ids_are_defined_once_and_every_reference_resolves | 44 | R (O) | - | PORT P1 | In flat and soft, for every preset and neutral base, no id is defined twice and every url(#..) and href="#.." resolves (regex only). Structural rule over the whole cast in both finishes; regex only so no XML parser; outlives the oracle as a guard for new parts. |

### test_metadata.py

8 functions, 30 items. PORT 3, COVERED-BY-ORACLE 5.

| Test | n | Class | Needs | Recommendation | Protects. Why |
| --- | ---: | --- | --- | --- | --- |
| presets_round_trip_through_a_url | 20 | M (O) | - | COVERED-BY-ORACLE P3 | decode_params(encode_params(p)) == p for every preset. Gate 3: every corpus URL decodes identically and encodes to the same bytes. |
| neutral_bases_round_trip_through_a_url | 2 | M (O) | - | COVERED-BY-ORACLE P3 | The same round trip for each neutral base. Gate 3. |
| encoding_is_deterministic | 1 | M | - | COVERED-BY-ORACLE P3 | encode_params is a pure function (sorted keys, no whitespace). Encodings are compared to Python bytes. |
| decode_rejects_what_it_did_not_encode | 3 | E (M) | - | PORT P1 | decode_params raises ValueError for bad base64, an empty string and valid JSON with an unknown field (asserts the class only). Class-only assertion (no message text), D12 keeps the name ValueError. TS must keep subclass semantics: Python JSONDecodeError and binascii.Error are ValueError subclasses. Also in the error corpus. |
| character_url_carries_the_base_and_the_encoding | 1 | M (O) | - | PORT P1 | character_url starts with TOOL_URL?c= and the tail decodes to the same params. Needs attribution.TOOL_URL (metadata block, in scope). |
| metadata_is_off_by_default_and_does_not_change_the_document | 1 | M (O) | - | COVERED-BY-ORACLE P3 | metadata=False equals the default render and the document has no <metadata>. Both forms are corpus cases. |
| metadata_embeds_a_working_character_link | 1 | M (R) | [xml] | PORT P1 | metadata=True embeds a <metadata> block (SVG namespace) whose <character> link decodes to the same params and whose source, repository and novel entries equal TOOL_URL, REPOSITORY_URL and NOVEL_URL. Semantic check of the attribution block; needs an XML parser with namespaces (or a regex on <character>) and attribution constants. |
| metadata_survives_a_character_with_no_optional_layers | 1 | M (R) | [xml] | COVERED-BY-ORACLE P3 | A default CharacterParams with metadata=True is well formed XML (nothing breaks the escaping). metadata=True is a corpus case; well-formedness follows from byte equality (escaping is the hazard). |

### test_soft_finish.py

7 functions, 28 items. PORT 3, COVERED-BY-ORACLE 3, DROP 1.

| Test | n | Class | Needs | Recommendation | Protects. Why |
| --- | ---: | --- | --- | --- | --- |
| flat_is_the_default_and_the_two_finishes_differ | 1 | O | - | COVERED-BY-ORACLE P3 | Default finish is flat, FINISHES is ("flat","soft"), explicit flat equals the default and soft differs. Finish sweeps in the corpus; FINISHES is catalogue data. |
| flat_has_none_of_what_soft_adds | 1 | R (O) | - | PORT P1 | A flat render has no linearGradient, radialGradient, feGaussianBlur, iris-grad, blush-grad or soft-face-clip. House-style rule (no gradients in flat output); string search only; outlives the oracle. |
| an_unknown_finish_is_refused | 1 | E | - | PORT P1 | render_character with finish "glossy" raises ValueError matching "finish must be one of" (full text: finish must be one of flat, soft, not 'glossy'). D12 keeps the class and the stable message prefix; note Python repr quoting of the value. |
| every_preset_draws_soft_as_well_formed_svg_without_blur | 20 | R (O) | [xml] | PORT P1 | Every preset in soft is well formed, has no feGaussianBlur and uses both linearGradient and radialGradient. Soft house rule (gradients only, no blur because cairosvg has none); well-formedness needs an XML parser, the rest is string search. |
| what_the_soft_finish_adds_is_defined_once_and_every_reference_resolves | 3 | R (O) | - | COVERED-BY-ORACLE P3 | Soft ids (iris-, blush-grad, soft-) are defined once, all ids carry the f1- prefix and all url(#..) resolve. Subsumed by test_ids (both finishes) plus the id_prefix corpus cases. |
| the_soft_lines_are_thinner_and_the_hair_has_its_own_tone | 1 | R (O) | [xml] | COVERED-BY-ORACLE P3 | Soft max stroke-width is 0.66 of flat (abs 0.02) and fewer strokes use the black outline colour. Pins soft numbers on Satoko; byte equality covers it. Reads stroke-width via an XML parse (regex works). |
| the_cli_takes_a_finish | 1 | P | [fx][fs] | DROP | generate.main with the finish flag set to soft writes an SVG containing iris-grad. generate.py not ported. |

### test_open_mouth.py

12 functions, 12 items. PORT 2, PORT-WITH-FUNCTION 1, COVERED-BY-ORACLE 9.

| Test | n | Class | Needs | Recommendation | Protects. Why |
| --- | ---: | --- | --- | --- | --- |
| a_shut_mouth_is_unchanged_by_the_open_mouth_existing | 1 | O | - | COVERED-BY-ORACLE P3 | mouth_open 0.0 renders as the default. Param-pair equivalence; mouth_open swept. |
| an_open_mouth_is_a_filled_shape_and_a_shut_one_is_a_line | 1 | O | - | COVERED-BY-ORACLE P3 | mouth_open 0.8 changes the render and introduces the mouth fill #6b2f2f absent when shut. mouth_open swept. |
| startled_opens_the_mouth_and_leaves_what_it_does_not_name | 1 | O | - | PORT P2 | EXPRESSIONS["startled"] sets mouth_open above 0 and leaves eye_size and scar_side. Value-level on the EXPRESSIONS registry (presets, in scope). |
| the_comic_expressions_exist_and_each_changes_the_face | 1 | O | - | PORT P2 | The seven named expressions exist in EXPRESSIONS and each changes the render of Satoshi. Registry membership and effect; not comic code (the name refers to the comic only in prose). |
| gaze_defaults_to_straight_ahead_and_moves_only_the_eyes | 1 | O (R) | - | COVERED-BY-ORACLE P3 | gaze 0.0 equals the default; left, straight and right differ; circle counts are identical. gaze swept in corpus. |
| a_look_to_the_side_keeps_the_iris_inside_the_eye_and_moves_both_eyes_together | 1 | I (R) | _EYE_ASPECT, _eye_placement | COVERED-BY-ORACLE P3 | At gaze extremes the iris cx stays within the eye aperture and both eyes move the way the look points (regex over the clipped eye group). Specific to Risa and Satoshi; gaze swept. Needs _EYE_ASPECT and _eye_placement if ported as written. |
| an_opening_beyond_the_width_does_not_make_the_mouth_taller_than_wide | 1 | I | _mouth_depth_share | PORT-WITH-FUNCTION P2 | _mouth_depth_share(o) is identity up to 0.8, non-decreasing to 2.0 and below 1.0. Pure monotone-and-bounded function, checked on a range the corpus may not sweep; port _mouth_depth_share. |
| the_blush_sits_below_the_eye_it_is_next_to | 1 | I (R) | _eye_placement | COVERED-BY-ORACLE P3 | Every blush ellipse top is below the eye lower lid (regex over <ellipse>), for three presets. blush swept; part geometry. |
| the_blush_is_clipped_to_the_face_outline | 1 | R (O) | - | COVERED-BY-ORACLE P3 | blush > 0 emits a blush-clip clip path wrapping exactly two ellipses; blush 0 emits none. blush swept. |
| a_raised_arm_takes_the_blazers_sleeve_with_it | 1 | O (R) | - | COVERED-BY-ORACLE P3 | At right_arm_out 128 Risa gets sleeve-cutaway and sleeve-cuff-l; at rest neither; both arms raised give both cuffs. right_arm_out swept, Risa blazer. |
| a_coat_whose_sleeves_are_the_arms_own_is_drawn_as_before_when_the_arm_is_raised | 1 | O | - | COVERED-BY-ORACLE P3 | Keiko at right_arm_out 128 draws no sleeve-cutaway or cuff. Param case. |
| a_raised_blazer_arm_turns_at_the_shoulder_not_at_the_sleeve_hem | 1 | R (O) | - | COVERED-BY-ORACLE P3 | The rotate() pivots for a raised blazer arm lie above two head radii below the head centre (regex). Param cases on Risa. |

### test_colorutil.py

6 functions, 10 items. PORT 6.

| Test | n | Class | Needs | Recommendation | Protects. Why |
| --- | ---: | --- | --- | --- | --- |
| hex_rgb01_round_trip | 1 | O | - | PORT P1 | rgb01_to_hex(hex_to_rgb01(c)) == c for five colours. Kernel-level property of colorutil (round half to even hazard 1); cheap, Phase 1 spike scope. |
| shade_darkens_by_default | 1 | O | - | PORT P1 | shade() lowers HSV value (checked with Python colorsys). Needs the hand-written colorsys of the TS kernel as the checker. |
| shade_black_stays_black | 1 | O | - | PORT P1 | shade("#000000") is "#000000". Edge case of colorutil. |
| shade_white_saturation_boost_clamps_at_one | 1 | O | - | PORT P1 | A huge saturation boost on white clamps and returns white. Clamp edge of colorutil. |
| shade_saturation_boost_clamps_on_saturated_color | 1 | O | - | PORT P1 | A boost of 5 on pure red stays at saturation 1.0. Clamp edge; needs the TS colorsys rgb_to_hsv. |
| shade_value_factor_scales_value_directly | 5 | O | - | PORT P1 | shade with value_factor 0.5 scales HSV value by 0.5 within one 8-bit step, for five hues. Colour maths across hues (CLAUDE.md asks for off-default hues); needs TS colorsys. |

### test_supporting.py

3 functions, 5 items. PORT 1, COVERED-BY-ORACLE 1, REWRITE 1.

| Test | n | Class | Needs | Recommendation | Protects. Why |
| --- | ---: | --- | --- | --- | --- |
| a_supporting_character_renders | 3 | O | - | COVERED-BY-ORACLE P3 | Each supporting character renders a document that starts with <svg and ends with </svg> and is deterministic. Supporting cast is a corpus group; determinism is the trivial render test. |
| every_supporting_character_has_a_display_name | 1 | O | - | PORT P2 | supporting.DISPLAY_NAMES keys equal SUPPORTING keys. Data registry rule. |
| none_of_them_is_a_preset_or_offered_by_the_web_tool | 1 | I (O) | catalogue._base_points, catalogue._cast_points | REWRITE P2 | No SUPPORTING name is a preset, nor a catalogue starting point (cast or base). Uses private catalogue._cast_points and _base_points; rewrite over the public build_catalogue()["starting_points"] to avoid exposing them. |

### test_consumers_stay_flat.py

4 functions, 4 items. PORT 1, DROP 3.

| Test | n | Class | Needs | Recommendation | Protects. Why |
| --- | ---: | --- | --- | --- | --- |
| nothing_that_is_drawn_by_default_is_soft | 1 | O | - | PORT P1 | CharacterParams().finish, every preset and every neutral base are "flat". Owner decision pin (changing the default must break a test on purpose); trivial values. |
| a_cover_draws_its_figure_flat | 1 | P (C) | [fx] | DROP | cover.render_cover calls render_character only with finish flat and the SOFT_MARKERS never appear. cover.py not ported. |
| a_sheet_draws_every_tile_flat | 1 | P | [fx] | DROP | sheet.render_sheet draws every tile flat with no soft markers. sheet.py not ported. |
| the_command_line_is_flat_unless_asked | 1 | P | [fx][fs] | DROP | generate.main for the risa preset writes an SVG with no soft markers. CLI (argparse, sys.argv monkeypatch, tmp files) not ported. |

### test_generate_cli.py

6 functions, 6 items. DROP 6.

Reason for every row: generate.py (argparse CLI, sys.argv, tmp_path) is not ported (D5).

| Test | n | Class | Protects |
| --- | ---: | --- | --- |
| preset_and_overrides_merge | 1 | P | The preset flag plus the hair-color override reaches the SVG. |
| the_retired_build_options_are_gone | 1 | P (M,E) | The retired build and heads flags exit with SystemExit; the link metadata carries no heads. |
| explicit_face_knob_wins_over_expression | 1 | P | An explicit brow-tilt flag survives the expression flag. |
| flat_disables_shading | 1 | P | The flat flag gives shorter output than the default. |
| no_metadata_flag_omits_metadata_block | 1 | P (M) | The no-metadata flag omits <metadata>. |
| outfit_color_alias_matches_tunic_color | 1 | P | The outfit-color flag is an alias of the tunic-color flag. |

### test_comic_checks.py

12 functions, 12 items. DROP 12.

Reason for every row: comic/ is deprecated (D6); also needs the optional uharfbuzz extra (importorskip).

| Test | n | Class | Protects |
| --- | ---: | --- | --- |
| a_clean_panel_has_nothing_to_report | 1 | C | Comic lettering check: a clean panel gives no problems. |
| a_bubble_over_a_face_is_found | 1 | C | Comic lettering check: a bubble covering a face is reported. |
| a_bubble_at_the_frame_is_found | 1 | C | Comic lettering check: a bubble at the frame edge is reported. |
| overlapping_bubbles_and_crossing_tails_are_found | 1 | C | Comic lettering check: overlapping bubbles and crossing tails are reported. |
| reading_order_is_top_left_first | 1 | C | Comic lettering check: reading order is checked top-left first. |
| too_many_bubbles_too_many_sentences_and_type_too_small_are_found | 1 | C | Comic lettering check: bubble count, sentence count and type size limits are reported. |
| a_strip_names_the_panel | 1 | C | Comic lettering check: strip problems are prefixed with the panel number. |
| the_shape_is_the_one_the_drawing_uses | 1 | C | Comic lettering check: Bubble.shape matches the drawn path. |
| two_figures_at_one_depth_must_be_one_size | 1 | C | Comic lettering check: figures at one depth must have one head size. |
| a_figure_further_back_may_be_smaller_by_what_the_horizon_says | 1 | C | Comic lettering check: perspective scaling by the horizon. |
| feet_above_the_horizon_are_named | 1 | C | Comic lettering check: feet above the horizon are reported. |
| a_lone_figure_has_nothing_to_compare | 1 | C | Comic lettering check: a single figure gives no size problem. |

### test_comic_layout.py

14 functions, 14 items. DROP 14.

Reason for every row: comic/ is deprecated (D6); the id and determinism properties are covered for single figures by test_ids and the id_prefix cases.

| Test | n | Class | Protects |
| --- | ---: | --- | --- |
| a_strip_is_deterministic | 1 | C | Comic layout: a strip renders deterministically. |
| no_id_is_defined_twice_on_a_page | 1 | C | Comic layout: no id is defined twice on a strip page. |
| every_reference_has_a_definition | 1 | C | Comic layout: every url(#..) reference on a strip resolves. |
| a_flipped_figure_is_mirrored_and_an_unflipped_one_is_not | 1 | C | Comic layout: a flipped placement is mirrored. |
| a_figure_may_stand_outside_the_panel_and_is_clipped_to_it | 1 | C | Comic layout: figures are clipped to the panel. |
| the_strip_is_as_tall_as_its_panels_gutters_and_margins | 1 | C | Comic layout: strip height is panels plus gutters plus margins. |
| a_panel_too_wide_for_the_strip_is_refused | 1 | C (E) | Comic layout: a panel wider than the strip raises ValueError matching "does not fit". |
| an_empty_strip_is_just_paper | 1 | C | Comic layout: an empty strip has no group. |
| a_hand_is_on_the_characters_own_side_and_mirrors_with_a_flip | 1 | C | Comic layout: Placement.hand sides and flip. |
| props_are_flat_shapes_where_they_are_put | 1 | C | Comic layout: comic props tray and mug are flat shapes. |
| a_shot_frames_the_figure_it_names | 1 | C | Comic layout: camera shots frame a figure. |
| a_view_moves_the_scene_and_leaves_the_overlay_alone | 1 | C | Comic layout: Panel view transform leaves the overlay alone. |
| a_gap_is_a_number_or_a_name_and_the_first_panel_has_none | 1 | C (E) | Comic layout: panel gaps by number or name; unknown name raises ValueError matching "no gap called". |
| a_placement_may_be_a_layer_of_svg_between_two_figures | 1 | C | Comic layout: a raw SVG layer between two placements. |

### test_comic_text.py

9 functions, 9 items. DROP 9.

Reason for every row: comic/ is deprecated (D6); needs the optional uharfbuzz extra.

| Test | n | Class | Protects |
| --- | ---: | --- | --- |
| a_longer_line_measures_wider_and_a_bigger_size_scales_it | 1 | C | Comic text and bubbles: text.measure scales with length and size. |
| wrap_keeps_every_line_inside_the_width_and_loses_no_word | 1 | C | Comic text and bubbles: text.wrap keeps lines inside the width and keeps every word. |
| text_is_drawn_as_paths_not_as_text_elements | 1 | C | Comic text and bubbles: outline text uses paths, not <text>. |
| a_caption_grows_with_its_text_and_reports_its_height | 1 | C | Comic text and bubbles: caption height grows with text. |
| a_bubble_with_a_tail_is_one_closed_path_reaching_the_target | 1 | C | Comic text and bubbles: a tailed bubble is one closed path reaching its target. |
| a_bubble_without_a_tail_or_aimed_inside_itself_is_a_plain_ellipse | 1 | C | Comic text and bubbles: a tail-less bubble is an ellipse. |
| a_bubble_fits_its_words_inside_the_ellipse | 1 | C | Comic text and bubbles: bubble rx fits the wrapped text. |
| head_gives_the_head_where_the_figure_is_placed_and_mirrors_with_a_flip | 1 | C | Comic text and bubbles: Placement.head mirrors with a flip. |
| a_panel_with_bubbles_still_has_no_repeated_id | 1 | C | Comic text and bubbles: a panel with bubbles has no repeated id. |

## 12. Reconciliation hook for Gate 5

The JSON key `tests` lists every one of the 288 functions by `file::name`; a TS test list reconciles against it by name, and a test left out is either `COVERED-BY-ORACLE` or `DROP` in this file, or it is a gap. The counts to hit: PORT 55, PORT-WITH-FUNCTION 15, REWRITE 11 functions to carry (81 total, 633 items); 145 covered by the oracle; 62 dropped.

