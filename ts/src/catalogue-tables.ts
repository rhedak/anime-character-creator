// Generated once by harness/ts_port/gen_catalogue_tables.py from `catalogue.py` (both are in the tag `python-final`), then owned by hand: the Python is gone, and the adult woman's
// body and cut (2026-10-19) are added here. The comments that say why each range has its bounds are in `catalogue.py` (lines 155 to 700 in that tag), which stays the record.

import { BODY_TYPES } from "./body.ts";
import "./body-adult-hair.ts"; // registers the swept ponytail in HAIRSTYLES, which HAIRSTYLE_LABELS must label
import { BOOT_CUTS, SKIRT_CUTS } from "./body-parts-tables.ts";
import { FINISHES } from "./character.ts";
import { HAIRSTYLES } from "./core-head.ts";
import { COAT_CUTS, SLEEVE_CUTS } from "./core-limbs-tables.ts";
import { BELT_CUTS, COLLAR_CUTS } from "./garments-tables.ts";
import { HAIR_CLIPS } from "./hair.ts";
import { ADULT_FACE_AGE } from "./model.ts";
import { sorted } from "./pynum.ts";
import {
  assertKeysEqual,
  bool,
  boolField,
  color,
  colorField,
  faceBool,
  faceRange,
  faceSelect,
  garmentSlot,
  range,
  rangeField,
  selectField,
} from "./catalogue-types.ts";
import type { BoolField, ColorField, GarmentSlot, RangeField, SelectField } from "./catalogue-types.ts";

// `character.py` HAND_STYLES and GRIP_STYLES. The TypeScript modules do not export them under these names, so
// they are generated here (a copy, not a link to another module). `assertKeysEqual` ties the labels to them.
export const HAND_STYLES: readonly string[] = ["mitten", "notched", "stroked", "curled", "traced"];
export const GRIP_STYLES: readonly string[] = ["mitten", "fist"];

// Optional since `docs/bare-body-plan.md` step 2: off, the body shows, and the
// tunic's trim (placket, chest pockets) goes with it. `TUNIC_TUCKED` rides
// with it because it only changes where the tunic's own hem sits.
export const SLEEVE_CUT_LABELS: Readonly<Record<string, string>> = {
  "wide": "Wide, turned cuff (traced)",
};
assertKeysEqual(SLEEVE_CUT_LABELS, SLEEVE_CUTS);
export const TUNIC: GarmentSlot = garmentSlot(
  "tunic",
  "Tunic",
  color("tunic_color", "Tunic"),
  { ranges: [range("neckline_notch", "Neckline depth", 0, 0.6)], bools: [bool("tunic_tucked", "Tucked in"), bool("neckline_round", "Round neckline"), bool("neckline_trim", "Neckline trim"), bool("neckline_stand", "Stand collar"), bool("sleeve_long", "Long sleeves"), bool("sleeve_under_cap", "Sleeve under cap")], selects: [selectField("sleeve_cut", "Sleeve cut", [[null, "Plain"], ...sorted(Object.entries(SLEEVE_CUT_LABELS), (e) => e[0])])] },
);
// Optional since `docs/bare-body-plan.md` step 5: off, the foot is bare.
// `boot_shaft` is 0 (ankle) to 1 (knee) across the
// whole cast, Tenno's 0.55 through the uniform's 1.0, so the full declared
// range is one that has actually been looked at.
export const BOOT_CUT_LABELS: Readonly<Record<string, string>> = {
  "loafer": "Loafer (traced)",
};
assertKeysEqual(BOOT_CUT_LABELS, BOOT_CUTS);
export const BOOTS: GarmentSlot = garmentSlot(
  "boots",
  "Boots (and shoes)",
  color("boot_color", "Boots (and shoes)"),
  { ranges: [range("boot_shaft", "Boot height", 0, 1)], selects: [selectField("boot_cut", "Shape", [[null, "Boot"], ...sorted(Object.entries(BOOT_CUT_LABELS), (e) => e[0])])] },
);
// Over the bare leg and under the shoe or boot: a sock from just under the knee.
export const KNEE_SOCK: GarmentSlot = garmentSlot("knee_sock", "Knee socks", color("knee_sock_color", "Knee socks"));
// The base layer, likewise always worn: what shows with the tunic off, for
// every character (`docs/bare-body-plan.md`, step 3). The top comes with a
// bust by itself; the toggle adds one without.
export const UNDERWEAR: GarmentSlot = garmentSlot(
  "underwear",
  "Underwear",
  color("underwear_color", "Underwear", false),
  { bools: [bool("underwear_top", "Top without a bust")] },
);
// Optional layers. Each is off (draws nothing) until its color is set, which
// is `Outfit`'s own presence rule and the reason none of these need a separate
// on/off field.
export const UNDERSLEEVE: GarmentSlot = garmentSlot(
  "undersleeve",
  "Undersleeves (long sleeves underneath)",
  color("undersleeve_color", "Undersleeves (long sleeves underneath)"),
);
export const BELT_CUT_LABELS: Readonly<Record<string, string>> = {
  "buckled": "Buckled, with keeper (traced)",
};
assertKeysEqual(BELT_CUT_LABELS, BELT_CUTS);
// 1.0 (the default) through 2.8, Chiyo's obi and the tallest in the cast.
// Capped a little above that rather than left open, since nothing wider has
// been rendered and judged. `belt_reach` is how far it goes across: 1.0 is
// the waist it would wrap on a bare figure, more for a belt worn over a coat.
export const BELT: GarmentSlot = garmentSlot(
  "belt",
  "Belt",
  color("belt_color", "Belt"),
  { ranges: [range("belt_scale", "Belt height", 1, 3), range("belt_reach", "Belt reach", 0.8, 1.4)], bools: [bool("belt_keeper_pair", "Keeper either side")], selects: [selectField("belt_cut", "Cut", [[null, "Band"], ...sorted(Object.entries(BELT_CUT_LABELS), (e) => e[0])])] },
);
export const APRON: GarmentSlot = garmentSlot("apron", "Apron", color("apron_color", "Apron"));
export const CRYSTAL_1: GarmentSlot = garmentSlot(
  "crystal_1",
  "Crystal (outer left)",
  color("crystal_color_1", "Crystal (outer left)"),
  { requires: "belt" },
);
export const CRYSTAL_2: GarmentSlot = garmentSlot(
  "crystal_2",
  "Crystal (inner left)",
  color("crystal_color_2", "Crystal (inner left)"),
  { requires: "belt" },
);
export const CRYSTAL_3: GarmentSlot = garmentSlot(
  "crystal_3",
  "Crystal (inner right)",
  color("crystal_color_3", "Crystal (inner right)"),
  { requires: "belt" },
);
export const CRYSTAL_4: GarmentSlot = garmentSlot(
  "crystal_4",
  "Crystal (outer right)",
  color("crystal_color_4", "Crystal (outer right)"),
  { bools: [bool("crystal_tongs", "Handling tongs (a small clipped tool)")], requires: "belt" },
);
export const SKIRT_CUT_LABELS: Readonly<Record<string, string>> = {
  "a_line": "A-line (traced)",
  "column": "Narrow column",
  "pleated": "Box-pleated (traced)",
};
assertKeysEqual(SKIRT_CUT_LABELS, SKIRT_CUTS);
// Hip (0) to ankle (1), same measure `hair_length` uses chin to hip. Used
// to be a knob that visibly did nothing at the chibi build: `_skirt_hem_y`
// pulled a requested length back toward the skeleton's own hem so hard
// that 0.60 and 0.95 landed within four pixels of each other, the finding
// `harness/hem/pullback.py` recorded. Task 32 (2026-08-19) removed that
// pull-back entirely, so `skirt_length` now lands exactly at every build.
// `skirt_length_chibi`, added the same day, is the opt-in second number
// for a character who wants a shorter hem at chibi specifically than at
// realistic; unset, the main length applies everywhere.
export const SKIRT: GarmentSlot = garmentSlot(
  "skirt",
  "Skirt",
  color("skirt_color", "Skirt"),
  { ranges: [range("skirt_length", "Skirt length", 0, 1), range("skirt_length_chibi", "Skirt length at chibi (overrides above)", 0, 1)], selects: [selectField("skirt_cut", "Cut", [[null, "Gathered"], ...sorted(Object.entries(SKIRT_CUT_LABELS), (e) => e[0])])] },
);
export const UNDERSKIRT: GarmentSlot = garmentSlot(
  "underskirt",
  "Underskirt (a second, longer skirt underneath)",
  color("underskirt_color", "Underskirt (a second, longer skirt underneath)"),
  { requires: "skirt" },
);
export const TROUSER: GarmentSlot = garmentSlot("trouser", "Trousers (Pants)", color("trouser_color", "Trousers (Pants)"));
export const POUCH: GarmentSlot = garmentSlot("pouch", "Pouch", color("pouch_color", "Pouch"), { requires: "belt" });
// Cut labels for `COLLAR_CUTS`, asserted in sync the way the hairstyles' are.
export const COLLAR_CUT_LABELS: Readonly<Record<string, string>> = {
  "pointed": "Pointed",
  "shirt": "Shirt collar (traced)",
};
assertKeysEqual(COLLAR_CUT_LABELS, COLLAR_CUTS);
export const COLLAR: GarmentSlot = garmentSlot(
  "collar",
  "Collar",
  color("collar_color", "Collar"),
  { bools: [bool("collar_mock", "Mock neck")], selects: [selectField("collar_cut", "Cut", [[null, "Band"], ...sorted(Object.entries(COLLAR_CUT_LABELS), (e) => e[0])])] },
);
export const RIBBON: GarmentSlot = garmentSlot("ribbon", "Ribbon (a bow at the throat)", color("ribbon_color", "Ribbon"));
export const PLACKET: GarmentSlot = garmentSlot("placket", "Buttons", color("placket_color", "Buttons"));
export const CHEST_POCKET: GarmentSlot = garmentSlot("chest_pocket", "Chest pocket", color("chest_pocket_color", "Chest pocket"));
export const STRAP: GarmentSlot = garmentSlot("strap", "Strap (cross-body strap)", color("strap_color", "Strap (cross-body strap)"));
// The adult woman's dirndl corset (docs/franzi-outfits-plan.md); the chibi bodies draw nothing for it.
export const BODICE: GarmentSlot = garmentSlot("bodice", "Bodice (adult woman only)", color("bodice_color", "Bodice"));
// Shoulder (0) to hip (1). The cast spans 0.44 (Tomohiro's jacket) to 0.70
// (Reika's), and the docstring states the endpoints as meaningful rather
// than merely legal, so the full range is exposed.
export const ROBE: GarmentSlot = garmentSlot(
  "robe",
  "Robe (open outer layer, kimono-style)",
  color("robe_color", "Robe (open outer layer, kimono-style)"),
  { ranges: [range("sleeve_drop", "Sleeve drop", 0, 1)] },
);
// Same hip-to-ankle measure as `skirt_length`, and the same two-field
// split: `hakama_length_chibi` is the opt-in chibi-only override.
export const HAKAMA: GarmentSlot = garmentSlot(
  "hakama",
  "Hakama (wide pleated trousers/skirt)",
  color("hakama_color", "Hakama (wide pleated trousers/skirt)"),
  { ranges: [range("hakama_length", "Hakama length", 0, 1), range("hakama_length_chibi", "Hakama length at chibi (overrides above)", 0, 1)] },
);
export const HEADSCARF: GarmentSlot = garmentSlot("headscarf", "Headscarf", color("headscarf_color", "Headscarf"));
export const GOGGLES: GarmentSlot = garmentSlot("goggles", "Goggles", color("goggle_color", "Goggles"));
export const BLINDFOLD: GarmentSlot = garmentSlot("blindfold", "Blindfold", color("blindfold_color", "Blindfold"));
export const MASK: GarmentSlot = garmentSlot("mask", "Face mask", color("mask_color", "Face mask"));
// The field holds any short text; the web tool offers a plain band or a
// numbered one, and a preset may carry whatever it prints.
export const WRISTBAND: GarmentSlot = garmentSlot(
  "wristband",
  "Wristband",
  color("wristband_color", "Wristband"),
  { selects: [selectField("wristband_side", "Side", [[-1, "Viewer's left"], [1, "Viewer's right"]]), selectField("wristband_text", "Print", [[null, "Plain"], ["0000", "Numbered"]])] },
);
export const SHOULDER_BARS: GarmentSlot = garmentSlot(
  "shoulder_bars",
  "Shoulder bars",
  color("shoulder_bars_color", "Shoulder bars"),
  { ranges: [range("shoulder_bars", "Bars", 1, 4, true)], selects: [selectField("shoulder_bars_side", "Side", [[-1, "Viewer's left"], [1, "Viewer's right"]])], requires: "coat" },
);
export const HAT: GarmentSlot = garmentSlot("hat", "Witch hat", color("hat_color", "Witch hat"));
// The shape is a choice rather than a fixed part: all five candidates were drawn
// for Katherina's and the owner kept them (2026-10-03).
export const HAIR_CLIP_LABELS: Readonly<Record<string, string>> = {
  "bar": "Bar",
  "crescent": "Crescent moon",
  "crossed": "Crossed pins",
  "snap": "Snap clip",
  "star": "Star",
};
assertKeysEqual(HAIR_CLIP_LABELS, HAIR_CLIPS);
export const HAIR_CLIP: GarmentSlot = garmentSlot(
  "hair_clip",
  "Hair clip",
  color("hair_clip_color", "Hair clip"),
  { selects: [selectField("hair_clip", "Shape", Object.entries(HAIR_CLIP_LABELS))] },
);
// A separate slot rather than a `ranges`/`bools` companion on `HAT`, because
// the band carries its own color, not a toggle or a number: the crystal rig's
// four independently-colored slots are the existing precedent for "more than
// one color belongs to one worn thing", and `requires="hat"` is the same
// dependency `UNDERSKIRT` has on `SKIRT`.
export const HAT_BAND: GarmentSlot = garmentSlot(
  "hat_band",
  "Hat band and buckle",
  color("hat_band_color", "Hat band and buckle"),
  { requires: "hat" },
);
export const STAFF: GarmentSlot = garmentSlot("staff", "Staff (held, right hand)", color("staff_color", "Staff"));
// Same shape as `HAT_BAND`: a second colour belonging to one thing.
export const STAFF_CRYSTAL: GarmentSlot = garmentSlot(
  "staff_crystal",
  "Staff crystal",
  color("staff_crystal_color", "Staff crystal"),
  { requires: "staff" },
);
// 1.0 is the traced short sword's length (a kozashi), 1.25 a katana's on a
// chibi. The top is 1.4, where the tilt cap that keeps the tip off the floor
// runs out on the shortest legs.
export const KATANA: GarmentSlot = garmentSlot(
  "katana",
  "Katana (sheathed, left hip)",
  color("katana_color", "Katana scabbard"),
  { ranges: [range("katana_length", "Katana length", 0.8, 1.4)] },
);
export const KATANA_FITTINGS: GarmentSlot = garmentSlot(
  "katana_fittings",
  "Katana fittings",
  color("katana_fittings_color", "Katana fittings"),
  { requires: "katana" },
);
export const COAT_CUT_LABELS: Readonly<Record<string, string>> = {
  "open_jacket": "Open jacket (traced)",
  "lab_coat": "Lab coat (notched lapel)",
  "blazer": "Blazer (closed, notched lapels)",
};
assertKeysEqual(COAT_CUT_LABELS, COAT_CUTS);
// The docstring's own four named lengths run 0.20 to 0.75; the cast's
// widest span is Tomohiro's 0.44 to Keiko's 0.80, so the range is bounded a
// little past both rather than left at the type's full domain. 0.20 opens
// the floor down to the vest/cardigan length task 31 found already worked.
export const COAT: GarmentSlot = garmentSlot(
  "coat",
  "Coat (open outer layer; short for a vest or cardigan)",
  color("coat_color", "Coat (open outer layer; short for a vest or cardigan)"),
  { ranges: [range("coat_length", "Coat length", 0.2, 0.85)], bools: [bool("coat_sleeves", "Full sleeves")], selects: [selectField("coat_cut", "Cut", [[null, "Two panels"], ...sorted(Object.entries(COAT_CUT_LABELS), (e) => e[0])])] },
);
export const HIP_POCKET: GarmentSlot = garmentSlot(
  "hip_pocket",
  "Hip pockets (on a traced coat)",
  color("hip_pocket_color", "Hip pockets"),
  { requires: "coat" },
);
export const COAT_BUTTON: GarmentSlot = garmentSlot(
  "coat_button",
  "Coat buttons (on a traced coat)",
  color("coat_button_color", "Coat buttons"),
  { requires: "coat" },
);
// Order here is display order: the two always-worn layers first, then
// everything else in the rough order a figure is dressed, innermost to
// outermost. Not alphabetical, because "add and remove garment slots" reads
// better as an outfit than as a word list.
export const GARMENTS: readonly GarmentSlot[] = [
  TUNIC,
  BOOTS,
  KNEE_SOCK,
  UNDERWEAR,
  UNDERSLEEVE,
  TROUSER,
  SKIRT,
  UNDERSKIRT,
  BELT,
  POUCH,
  CRYSTAL_1,
  CRYSTAL_2,
  CRYSTAL_3,
  CRYSTAL_4,
  APRON,
  BODICE,
  COLLAR,
  RIBBON,
  PLACKET,
  CHEST_POCKET,
  STRAP,
  HAKAMA,
  ROBE,
  COAT,
  HIP_POCKET,
  COAT_BUTTON,
  HEADSCARF,
  GOGGLES,
  BLINDFOLD,
  MASK,
  WRISTBAND,
  SHOULDER_BARS,
  HAIR_CLIP,
  HAT,
  HAT_BAND,
  STAFF,
  STAFF_CRYSTAL,
  KATANA,
  KATANA_FITTINGS,
];
// Character-level colors, the ones every figure has regardless of what it
// wears. `hair_tip_color` is optional the same way a garment is: unset means
// single-tone hair.
// The bat familiar flying beside the figure: setting his fur draws him at
// all, so this is how the web tool turns him on and off.
export const COLORS: readonly ColorField[] = [
  colorField("skin_tone", "Skin", false),
  colorField("hair_color", "Hair", false),
  colorField("hair_tip_color", "Tip colour", true),
  colorField("eye_color", "Eyes", false),
  colorField("familiar_color", "Familiar (bat)", true),
  colorField("familiar_eye_color", "Familiar's eyes", true),
];
// Chin (0) to hip (1), the same measure documented on `CharacterParams`.
// Every haircut maps its own end of this range to where it actually falls
// (`_hair_fall`), so 0..1 is meaningful for all five rather than only some.
export const HAIR_LENGTH: RangeField = rangeField("hair_length", "Hair length", 0, 1);
// How the figure is finished, and how strong the soft finish's hair shading is
// (`docs/api.md`, "The soft finish"). The house style is flat; soft is for a figure
// set beside painted art. The strength only means anything for soft, so the web
// layer shows its slider only then. 0 draws no clumps, 1 is the default the owner picked,
// 2 is the strength they were first drawn at.
export const FINISH_LABELS: Readonly<Record<string, string>> = {
  "flat": "Flat (house style)",
  "soft": "Soft (for painted art)",
};
assertKeysEqual(FINISH_LABELS, FINISHES);
export const HIGHLIGHT_STRENGTH: RangeField = rangeField("highlight_strength", "Hair shading strength", 0, 2);
// A gathered tail and a crown knot: both drawn over any cut (`_hair_tail`,
// `_hair_knot`), not part of `Hairstyle` itself, and both already carried by a
// real preset (Krista's tail, Daizen's and Haruto's knots) but never exposed
// here before now. Shoulder (0) to hip (1), same as `HAIR_LENGTH`'s own scale.
export const HAIR_TAIL: RangeField = rangeField("hair_tail", "Tail (ponytail/braid)", 0, 1);
// Where the belt sits, in head radii, up or down from the build's own. Offered
// to experiment with the upper/lower body split (`docs/satoshi-tall-chibi-plan.md`);
// the range is what has been rendered and looked at on Satoshi, not a limit
// anything else enforces.
export const WAIST_SHIFT: RangeField = rangeField("waist_shift", "Belt line (up / down)", -1, 1.5);
// How much bust the figure carries, 0 for none (`docs/bust-plan.md`). The range
// is the one swept and judged, and the cast's own values sit inside it: Krista
// at the top, the men at zero.
// Skin tones offered as one-click swatches beside the free colour picker, very
// light to very dark (`docs/bare-body-plan.md`, step 7): the range swept on the
// cast in the base-layer view (`harness/bare/skin_tones.py`), where the outline
// and the line work held at every one. The second is `CharacterParams`' default.
export const SKIN_SWATCHES: readonly (readonly [string, string])[] = [
  ["Very light", "#fbe6d6"],
  ["Light", "#f2c9a1"],
  ["Light warm", "#e6b38a"],
  ["Medium", "#c98d62"],
  ["Medium dark", "#a8704a"],
  ["Dark", "#865335"],
  ["Very dark", "#633a24"],
  ["Deepest", "#442617"],
];
// How tall the figure stands against its head (`docs/tall-chibi-plan.md`, R4b):
// the range the owner picked from the study, young at 0.8 to adult at 1.3.
export const HEIGHT: RangeField = rangeField("height", "Height", 0.8, 1.3);
// One axis from child to old (`CharacterParams.face_age`): 0 to 1 the face
// growing up, 1 to 2 it ageing.
export const AGE: RangeField = rangeField("face_age", "Age (adult to old)", ADULT_FACE_AGE, 2);
export const BUST: RangeField = rangeField("bust", "Bust", 0, 1);
// Chest definition bare, 0 for none (`docs/bare-body-plan.md`, step 6): the
// men at the top, everyone else at zero. Shows only with the tunic off.
export const CHEST: RangeField = rangeField("chest", "Chest", 0, 1);
export const HAIR_KNOT: BoolField = boolField("hair_knot", "Top-knot");
// `HAIRSTYLES` is the real registry; this only labels it. A new cut appears in
// one place, here and in `HAIRSTYLES` itself, and needs no companion edit.
export const HAIRSTYLE_LABELS: Readonly<Record<string, string>> = {
  "long_blunt": "Long, blunt",
  "short_layered": "Short, layered",
  "long_traced": "Long",
  "long_parted": "Long, front locks",
  "long_fringed": "Long, blunt fringe and side locks",
  "short_crop": "Short crop",
  "short_tousled": "Short, tousled",
  "long_center_part": "Long, center part",
  "swept_ponytail": "Swept ponytail",
};
assertKeysEqual(HAIRSTYLE_LABELS, HAIRSTYLES, "HAIRSTYLE_LABELS and HAIRSTYLES have drifted apart; a cut was added or removed on one side without the other");
// `BODY_TYPES` is the registry; these label it, the same arrangement as the
// hairstyles above. The tall chibi is the one figure (`docs/tall-chibi-plan.md`):
// the shared compressed chibi (`body=None`) and the build slider are retired, so
// these two are the whole choice.
export const BODY_LABELS: Readonly<Record<string, string>> = {
  "tall_chibi": "Tall chibi (Katherina's)",
  "tall_chibi_long_torso": "Tall chibi (long torso)",
  "tall_slender": "Tall and slender (about 4.4 heads)",
  "adult_female": "Adult woman (about 6.4 heads)",
};
assertKeysEqual(BODY_LABELS, BODY_TYPES, "BODY_LABELS and BODY_TYPES have drifted apart; a body type was added or removed on one side without the other");
// How the hands are drawn (`docs/hands-plan.md`): the chibi's mitten, three small
// variations on it, or the open hand taken off the reference, and separately how a
// hand that holds a staff is drawn. A choice per character, the owner's call, not
// tied to the height.
export const HAND_LABELS: Readonly<Record<string, string>> = {
  "mitten": "Mitten (chibi)",
  "notched": "Mitten, notched fingers",
  "stroked": "Mitten, finger strokes",
  "curled": "Half-closed hand",
  "traced": "Open hand (drawn)",
};
assertKeysEqual(HAND_LABELS, HAND_STYLES);
export const GRIP_LABELS: Readonly<Record<string, string>> = {
  "mitten": "Same hand as the other",
  "fist": "Fist round the staff",
};
assertKeysEqual(GRIP_LABELS, GRIP_STYLES);
// `FaceStyle` carries fourteen floats, and `docs/web-gui-plan.md` calls the
// whole set "a mixing desk, not a limited set of choices" and keeps it out of
// the catalogue entirely. What follows is a deliberately smaller, curated
// subset: the fields that read as "what shape are the eyes and mouth" and
// "is there a scar", not the ones that read as "what mood is this face making
// right now" (`brow_tilt`, `mouth_curve`, `blush`, ...) or duplicate what a
// preset already states at rest (`eye_openness`, `eye_lower_lid`,
// `brow_weight`).
// Bounds are the min and max actually used across the presets (see
// `presets.py`; Risa's face, drawn on her own measurements, widened several), the same "rendered and judged" rule `skirt_length` and
// `coat_length` already follow above, widened by a small margin so the
// default chibi face sits inside every range rather than at its edge.
// `mouth_width`'s default (1.0, `BASE_FEMALE`/`BASE_MALE`'s own value) sits
// above every named preset's own 0.66-0.80, which is why its own high end
// is 1.05 rather than a margin over the cast alone.
//
// `eye_corner` reads differently at the two builds now that `_eye_placement`
// doubles it at the realistic one (`STATUS.md`, 2026-08-12): this range's own
// top of 0.65 becomes an effective 1.3 there. Checked directly rather than
// derated for it, since the "malformed combinations are the visitor's own
// responsibility" call in `docs/web-gui-plan.md` already covers a sharper
// corner than either reference draws: 0.65 at the realistic build renders a
// sharp but intact corner, not a self-intersecting one, at both ends of every
// other range here too.
// Risa's face (`docs/risa-plan.md`, M9) added these. `eye_gap` is None for a preset
// that keeps the cast's spacing, which the web tool shows as the slider's middle.
export const FACE_RANGES: readonly RangeField[] = [
  faceRange("eye_size", "Eye size", 0.8, 1.1),
  faceRange("eye_width", "Eye width (round to narrow)", 0.65, 1.1),
  faceRange("eye_tilt", "Eye tilt", -0.1, 0.2),
  faceRange("eye_corner", "Eye corner (round to sharp)", 0.15, 0.65),
  faceRange("iris_size", "Iris size", 0.6, 1.05),
  faceRange("lash", "Lash (soft to winged)", 0, 1.7),
  faceRange("mouth_width", "Mouth width", 0.4, 1.05),
  faceRange("eye_gap", "Eye spacing", 0.2, 1.3),
  faceRange("iris_inset", "Iris toward the nose", 0, 1),
  faceRange("iris_aspect", "Iris height (round to tall)", 1, 1.6),
  faceRange("lid_shadow", "Shadow under the upper lid", 0, 0.25),
  faceRange("mouth_drop", "Mouth lower in the face", 0, 0.1),
  faceRange("brow_length", "Brow length", 0.4, 1),
];
export const FACE_BOOLS: readonly BoolField[] = [
  faceBool("glasses", "Glasses"),
  faceBool("chin_shadow", "Shadow under the chin"),
  faceBool("nose_dot", "Nose as a dot"),
  faceBool("brows_over_hair", "Brows over the fringe"),
];
// Stated from the viewer's side, matching `FaceStyle.scar_side`'s own
// docstring: "Right cheek" here is the viewer's right, the character's left.
export const FACE_SCAR: SelectField = faceSelect("scar_side", "Scar", [[0, "None"], [-1, "Left cheek"], [1, "Right cheek"]]);
export const FACE_SELECTS: readonly SelectField[] = [FACE_SCAR];

// The controls a body does not use, by body type: the page hides them there (`catalogue.body_ignores`, web/app.js). The adult woman's head, hair, hands and feet are traced, not driven by
// the chibi's settings, so a control that changes nothing in her drawing is a control that only misleads. `BODY_IGNORES` is what drawing her showed (ts/test/ignored-fields.ts finds
// it again and ts/test/catalogue.test.ts pins it: `node harness/franzi/ignored_fields.ts` prints it), and `BODY_HIDDEN_EXTRA` is what draws something wrong on her (docs/adult-body-audit.md, D1 to
// D3: a chibi ponytail root and a chibi bun on her traced hair, and a waist shift the traced head and hands do not follow), hidden on purpose.
export const BODY_HIDDEN_EXTRA: Readonly<Record<string, readonly string[]>> = {
  adult_female: ["hair_knot", "hair_tail", "waist_shift"],
};
export const BODY_IGNORES: Readonly<Record<string, readonly string[]>> = {
  adult_female: sorted([
    ...BODY_HIDDEN_EXTRA["adult_female"]!,
    "boot_color",
    "boot_cut",
    "boot_shaft",
    "brow_length",
    "bust",
    "chest",
    "chin_shadow",
    "coat_button_color",
    "coat_sleeves",
    "eye_corner",
    "eye_gap",
    "eye_size",
    "eye_tilt",
    "eye_width",
    "face_age",
    "grip_style",
    "hair_length",
    "hair_tip_color",
    "hairstyle",
    "hakama_length_chibi",
    "hand_style",
    "highlight_strength",
    "hip_pocket_color",
    "iris_aspect",
    "iris_inset",
    "iris_size",
    "knee_sock_color",
    "lash",
    "lid_shadow",
    "mouth_drop",
    "mouth_width",
    "neckline_notch",
    "neckline_round",
    "neckline_stand",
    "neckline_trim",
    "nose_dot",
    "scar_side",
    "skirt_cut",
    "skirt_length",
    "skirt_length_chibi",
    "sleeve_cut",
    "sleeve_long",
    "sleeve_under_cap",
    "underskirt_color",
    "undersleeve_color",
    "underwear_top",
    "wristband_color",
    "wristband_side",
    "wristband_text"
  ]),
};
