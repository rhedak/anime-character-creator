// Generated once by harness/ts_port/gen_types.py from the Python dataclasses, then owned by hand.
// The registry is the one thing TypeScript cannot reflect: field names, type tags and defaults.

export type FieldType = "str" | "float" | "int" | "bool" | "Outfit" | "FaceStyle";

export interface FieldSpec {
  readonly name: string;
  readonly type: FieldType;
  readonly nullable: boolean;
  readonly default: string | number | boolean | null;
}

/**
 * What the character wears, one field per garment.
 *
 * A garment is present when its color is set, so a character states only the
 * layers it has rather than carrying a flag per piece, and the parts that draw
 * absent garments return nothing. Colors default to the plain tunic-and-skirt
 * the generator started with; the layered values live on the presets.
 */
export interface Outfit {
  /**
   * None takes the tunic off, and its trim with it (the placket, the chest
   * pockets): the body shows (`bare-body-plan.md`).
   */
  readonly tunic_color: string | null;
  /**
   * None takes the boots off, and the foot is bare (`bare-body-plan.md`,
   * step 5).
   */
  readonly boot_color: string | null;
  /** Long sleeve worn under the tunic's short one. None leaves the arm bare. */
  readonly undersleeve_color: string | null;
  readonly belt_color: string | null;
  /**
   * A keeper loop either side of the buckle, set out from it and standing
   * proud of the band, in place of the single small loop beside it: what a
   * dress belt carries rather than a working one. Keiko's reference
   * (`docs/keiko-clothes-plan.md`, K3).
   */
  readonly belt_keeper_pair: boolean;
  /**
   * How far the belt reaches across, as a multiple of its usual half-width.
   * A belt worn over an open coat has to reach the coat's own front edge, not
   * just the waist it would wrap on a bare figure.
   */
  readonly belt_reach: number;
  /** A traced cut from `BELT_CUTS`; `None` is the shared band. */
  readonly belt_cut: string | null;
  /** Front panel hanging from the belt, over the skirt. */
  readonly apron_color: string | null;
  readonly skirt_color: string | null;
  /** A traced cut from `SKIRT_CUTS`; `None` is the shared parametric skirt. */
  readonly skirt_cut: string | null;
  /** A second, longer skirt under the first, so its hem shows below the other's. */
  readonly underskirt_color: string | null;
  /** Trousers instead of a skirt. Fills the legs, which are otherwise bare skin. */
  readonly trouser_color: string | null;
  /**
   * A pouch on each hip, hanging from the belt band. Working-outfit detail
   * the canon keeps even at chibi. Needs a belt to hang from.
   */
  readonly pouch_color: string | null;
  /**
   * Skirt hem, measured hip (0) to ankle (1), the way hair_length is measured
   * chin to hip, so one garment keeps its length across builds. None takes the
   * skeleton's own hem anchor, which is where a hem sits when nobody asks for
   * anything in particular.
   */
  readonly skirt_length: number | null;
  /**
   * An independent hem for the chibi end of the build range, blended toward
   * `skirt_length` as the build climbs to realistic. None (the default) uses
   * `skirt_length` unchanged at every build, which is `_skirt_hem_y`'s plain
   * reading of "length is measured hip to ankle". This field exists because
   * a character's realistic-build length can be measured and correct (the
   * cast's own gap analysis only ever checked that build) while its chibi
   * rendering is a separate design choice: see `_skirt_hem_y`'s own
   * docstring and docs/character-roster-plan.md's Phase 6 task 32 note for
   * why the two stopped being tied together.
   */
  readonly skirt_length_chibi: number | null;
  /**
   * Tunic tucked in at the belt rather than hanging over it: the tunic's hem
   * stops inside the belt band and whatever is worn below rises to meet it, so
   * the belt is the boundary between the two garments. Both Satoshi
   * references wear it this way, with the tunic's green ending above the
   * belt's lower edge rather than below it. One flag moves both garments,
   * which is the point: they have to agree on the line they meet at, and the
   * belt is only wide enough to hide a disagreement of a few pixels.
   */
  readonly tunic_tucked: boolean;
  /**
   * A crew neckline in place of the tunic's default open V. Off by default
   * since the V is what every shipped preset wears; a garment with a
   * standing collar (`collar_color`) already shrinks the V to a hidden seam
   * and ignores this, so the two never fight over the same neckline.
   */
  readonly neckline_round: boolean;
  /**
   * The undersleeve's tone trimming the tunic's V, a thin line just inside the
   * neckline. On by default, since the canon drew it; off for a plain neckline
   * with nothing showing under it. Only drawn with an undersleeve and no collar.
   */
  readonly neckline_trim: boolean;
  /**
   * A small stand collar on the tunic's V: a short tab rises on each side of the
   * neck and the V's edges start at the neck's own, instead of the neckline
   * starting at the shoulder line and cutting into it. On by default; `False` is
   * the plain V the roster was first drawn with. Ignored under a standing collar
   * (`collar_color`) and with a round neckline, which have their own necks, and
   * it replaces the undersleeve trim (`neckline_trim`) on the V.
   */
  readonly neckline_stand: boolean;
  /**
   * How deep the tunic's V cuts, in head radii, for a garment that closes higher
   * than its collar's default leaves it: Risa's shirt is buttoned to the throat
   * under a shirt collar whose wings cross above the point where the default V
   * for a traced collar bottoms out, so the V's skin showed below them. `None`
   * keeps the depth each case already had.
   */
  readonly neckline_notch: number | null;
  /**
   * The tunic's sleeve reads its own sleeve colour all the way to the
   * wrist cuff instead of stopping at the short hem and handing off to
   * `undersleeve_color`/bare skin. Off by default, the short sleeve every
   * shipped preset wears.
   */
  readonly sleeve_long: boolean;
  /**
   * The tunic's cap sleeve lies over the arm instead of stopping in a flat
   * shelf above it: the cap's underside slants from its tip in to the armpit,
   * the tip stands only a little past the arm's outer edge, and the arm's top
   * follows the same slant so the sleeve reads as coming out from under the
   * cap. On by default; `False` is the flat shelf the roster was first drawn with.
   */
  readonly sleeve_under_cap: boolean;
  /**
   * A traced sleeve and cuff from `SLEEVE_CUTS`, in the sleeve's colour, in place of
   * the plain tube; `None` is the tube.
   */
  readonly sleeve_cut: string | null;
  /**
   * --- Uniform trim. Five fields rather than one `uniform=True`, because the
   * cast does not wear the uniform as a unit: Tenno has the cut without the
   * strap, Elara and Krista hang crystals off the belt that nobody else
   * carries, and a coat wants the collar without any of the rest. Each is off
   * by default and draws nothing, which is what keeps them general.
   *
   * What is here is the minimum that reads at the size a character is seen on
   * a sheet: a closed collar, a line of buttons, a pocket on each breast, a
   * strap across the chest, a boot that climbs the calf. Rank tabs, shoulder
   * boards, cuff piping and hip pockets are all in the references and all
   * below that line; see `docs/character-roster-plan.md`.
   *
   * A standing collar closing at the throat, in place of the open V. Its own
   * colour, so a uniform's collar can differ from the tunic it sits on.
   */
  readonly collar_color: string | null;
  /**
   * A traced cut from `COLLAR_CUTS` in place of the standing band; `None` is
   * the band.
   */
  readonly collar_cut: string | null;
  /**
   * The collar hugs the neck as a mock (turtle) neck rather than standing out
   * over the shoulders. The standing band is 1.70 neck half-widths across,
   * which is right for a uniform's collar and wrong for knitwear: Keiko's
   * reference puts her dress's collar at 0.276 head radii against a neck of
   * 0.269, so the cloth simply takes the neck's own silhouette. It also drops
   * the band's centre notch, which says "two halves meeting" about a garment
   * that has no opening at all.
   */
  readonly collar_mock: boolean;
  /** A row of buttons down the centre front, from collar to belt. */
  readonly placket_color: string | null;
  /** A flapped pocket on each breast. */
  readonly chest_pocket_color: string | null;
  /**
   * A strap from one shoulder across to the opposite hip. Worn over the tunic
   * and under the arms, which is where a real one sits and also the only place
   * it does not clip a hand.
   */
  readonly strap_color: string | null;
  /** The adult woman's dirndl bodice, a corset with lacing and buttons over the blouse (docs/franzi-outfits-plan.md). Drawn only on an adult body; the chibi bodies draw nothing for it. */
  readonly bodice_color: string | null;
  /**
   * How far up the shin the boot climbs, on top of the ankle boot every
   * character already has: 0 leaves it alone, 1 takes it to the knee.
   */
  readonly boot_shaft: number;
  /**
   * A traced foot from `BOOT_CUTS`, in `boot_color`, in place of the ankle boot;
   * `None` is the boot.
   */
  readonly boot_cut: string | null;
  /**
   * A knee sock over the leg, from just under the knee to the shoe, in this
   * colour (`KNEE_SOCK_CUT`). `None` is a bare leg above the boot.
   */
  readonly knee_sock_color: string | null;
  /**
   * A bow at the throat, over the collar, in this colour (`RIBBON_CUT`). `None`
   * draws nothing.
   */
  readonly ribbon_color: string | null;
  /**
   * --- The base layer, what shows with the tunic off (`bare-body-plan.md`,
   * step 3). Not optional: with nothing else worn it is what the figure
   * wears, for every character (the owner's call, 2026-09-25); a fully bare
   * figure is a harness view only. The underpants are drawn under every
   * bare leg; the top with the tunic off, with a bust, or without one when
   * `underwear_top` asks for it.
   */
  readonly underwear_color: string;
  readonly underwear_top: boolean;
  /**
   * --- Robe. Three fields, and between them they carry the whole cluster:
   * what says "kimono" at tile size is a front that crosses, a sleeve that
   * hangs, and a wide sash. Embroidery, the checked panels, layered inner
   * collars and sword furniture are all in the references and all below the
   * first-draft line.
   *
   * A panel crossing the chest, right over left, in place of the tunic's
   * symmetric front. Its own colour so an outer robe can sit over an inner one.
   */
  readonly robe_color: string | null;
  /**
   * How far the sleeve hangs below the tunic's own short one, shoulder (0) to
   * hip (1). A kimono sleeve is a bag of cloth, not a tube on an arm, so this
   * hangs from the shoulder rather than following the arm inside it.
   */
  readonly sleeve_drop: number;
  /**
   * How much taller the belt band is than the default. An obi is the same
   * object as a belt, three or four times the height, and giving it a scalar
   * rather than its own garment means a buckle and a sash cannot disagree
   * about where the waist is.
   */
  readonly belt_scale: number;
  /**
   * A wide pleated lower garment worn over the legs, under an open kimono or
   * robe: Haruto and Reika both wear one. Its own field rather than a pleat
   * count on `skirt_color`, because the two are not the same shape at the
   * same length: nobody wears both, but Haruto wears trousers under a hakama
   * that stops short of his boots, which only works if the two are
   * independent layers rather than one field pulling double duty.
   */
  readonly hakama_color: string | null;
  /**
   * Same hip(0)-ankle(1) measure `skirt_length` uses. A hakama reads close to
   * floor-length in both references; `None` takes the skeleton's own hem,
   * which is shorter, so a hakama that wants the reference's length has to
   * ask for it explicitly the way `skirt_length` already does.
   */
  readonly hakama_length: number | null;
  /**
   * The hakama's own `skirt_length_chibi`: an independent chibi-end hem,
   * blended toward `hakama_length` as the build climbs. See that field's
   * comment for why the two builds can want different lengths.
   */
  readonly hakama_length_chibi: number | null;
  /**
   * A cloth tied over the head, covering the crown and leaving the face and a
   * little hair showing. Worn rather than grown, so it is here and not on
   * `CharacterParams` beside the hair.
   */
  readonly headscarf_color: string | null;
  /**
   * A pair of lenses on a strap, pushed up onto the forehead rather than worn
   * over the eyes. Frame and strap color only; the lens tone is derived from
   * it with `shade()` the same way a shadow tone is, lighter rather than
   * darker, so a goggle color always ships with a glass that reads against it.
   */
  readonly goggle_color: string | null;
  /**
   * A strip of cloth worn pushed up onto the forehead, a blindfold put by once
   * it is done with: a loose band across the brow over the fringe, with the
   * fold a pushed-up cloth takes. Worn over the hair like a headband and under
   * a scarf or a hat, so it is the same slot in the draw order as the goggles
   * it is the alternative to; a character does not wear both.
   */
  readonly blindfold_color: string | null;
  /**
   * A pleated face mask worn pulled down under the chin, hanging at the throat
   * with its ear loops running up behind the jaw: put by, not worn over the
   * mouth. The one garment here drawn before the head, so the jaw covers the
   * mask's top edge and it reads as tucked under the chin.
   */
  readonly mask_color: string | null;
  /**
   * A band of paper or cloth round one wrist, over the sleeve's end: its color,
   * `None` for none, the side it is worn on (-1 the viewer's left, 1 the
   * viewer's right, as `_arms` loops it), and a short text printed across it,
   * a number or a name, in a deeper tone of the band. At cover scale the text
   * is a few pixels, so a band is a band first and the text a bonus.
   */
  readonly wristband_color: string | null;
  readonly wristband_text: string | null;
  readonly wristband_side: number;
  /**
   * A shoulder board with rank bars on one shoulder of the coat: the bars' color
   * (`None` for none), how many (one to four read at chibi scale), and the side
   * it is worn on, as for the wristband. Needs a coat (the parametric one, not a
   * traced cut), the way the pouches need a belt.
   */
  readonly shoulder_bars_color: string | null;
  readonly shoulder_bars: number;
  readonly shoulder_bars_side: number;
  /**
   * A pointed witch's hat: crown, brim and the band at the crown's base. Its
   * own color rather than reusing `hair_color`/`coat_color`, because a hat
   * is not necessarily dyed to match either, and the reference this shipped
   * for (`ref-local/katherina_grok/`) wears a
   * near-black hat over purple hair and a navy coat, three tones, not one.
   * `None` draws nothing, same convention as every optional garment above.
   */
  readonly hat_color: string | null;
  /**
   * The band around the crown's base, and the bow tied on it, in the same
   * color: the reference's bow is the band's own cloth, not hardware.
   * Independent of `hat_color` because the reference's band
   * reads closer to the hair's own purple than to the crown's near-black,
   * the same "trim differs from the body" relationship `collar_color` has
   * to `tunic_color`. `None` with `hat_color` set would draw a hat with no
   * band, which nothing currently asks for but costs nothing to allow.
   */
  readonly hat_band_color: string | null;
  /**
   * A clip worn in the hair at the right temple (the viewer's right), below a
   * hat's brim: its colour, `None` for none, and its shape from `HAIR_CLIPS`.
   * Katherina's took the place of the band her side tail was tied with (the
   * owner, 2026-10-03).
   */
  readonly hair_clip_color: string | null;
  readonly hair_clip: string;
  /**
   * A wizard's staff, held in the character's own right hand (the viewer's
   * left): the wood, and the crystal set in its prongs. Only a shape and two
   * colours, not a general prop: it is placed by `_hand_centre`, so it wants
   * `CharacterParams.right_arm_out` to hold it clear of the body, the way
   * KATHERINA's is. `None` draws nothing; a staff without a crystal is bare
   * wood.
   */
  readonly staff_color: string | null;
  readonly staff_crystal_color: string | null;
  /**
   * A katana worn at the character's left hip (the viewer's right), hung from the
   * belt, sheathed: the scabbard's colour, `None` for none. The handle's wrap and
   * the ring bands are tones of it, and the diamonds showing through the wrap are
   * a fixed cream, like the buckle's metal.
   */
  readonly katana_color: string | null;
  /** Its pommel cap, collar, guard and end cap; `None` is brass. */
  readonly katana_fittings_color: string | null;
  /**
   * How long it is, against the traced sword's own 1.0, which is a short sword
   * (about 0.46 of the reference figure's height, a kozashi's length): 1.35 is a
   * full katana's. Only the scabbard grows: the handle, guard, collar and end cap
   * keep their size, so a longer sword is a longer blade in its scabbard and not
   * an enlarged one.
   */
  readonly katana_length: number;
  /**
   * An outer layer hanging open over whatever is worn under it: a cropped
   * jacket, a lab coat, a long coat, or (at the short end of `coat_length`)
   * an open vest or cardigan over a tunic. One garment rather than four,
   * because they differ only in where the hem lands: task 31 of
   * `docs/character-roster-plan.md` went looking for a new "light outer
   * layer" part and found this already drew one at a short enough length,
   * so nothing new was built for it.
   */
  readonly coat_color: string | null;
  /** A traced cut from `COAT_CUTS`; `None` is the shared two-panel coat. */
  readonly coat_cut: string | null;
  /**
   * The arm's sleeve is the coat's, in the coat's colour, rather than the
   * garment underneath showing below a cap sleeve. A lab coat has full
   * sleeves to the wrist and nothing of the dress shows on the arm at all;
   * without this Keiko's charcoal dress ran down both arms under a white
   * coat. A traced sleeve (`sleeve_cut`) already does this for itself.
   */
  readonly coat_sleeves: boolean;
  /**
   * Where the coat's hem falls, shoulder (0) to ankle (1). Roughly: 0.20 an
   * open vest or cardigan over a tunic, 0.30 a jacket cropped at the waist,
   * 0.62 below the knee, 0.75 mid-calf.
   */
  readonly coat_length: number;
  /**
   * A flapped pocket on each hip of a traced coat, in this colour (`HIP_POCKET_CUT`).
   * `None` draws none.
   */
  readonly hip_pocket_color: string | null;
  /**
   * A line of buttons down the front of a traced coat, in this colour
   * (`_COAT_BUTTONS`): separate discs, not the tunic's placket. `None` draws none.
   */
  readonly coat_button_color: string | null;
  /**
   * Four mana crystals clipped to the belt, two a side, the carrying rig
   * Elara and Krista wear instead of a pouch: a crystal is dangerous to grip
   * bare-handed (a file in the consumer repo, "Donarsblut"), so it rides
   * in a loop rather than a pocket, and stays visible rather than stowed.
   * Four fields rather than one `crystal_color`, because the point of a
   * working mage's rig is that the stock is not all the same type; each
   * slot is independently optional, so a character can wear fewer than
   * four, same as any other garment here. Left outer, left inner, right
   * inner, right outer. Needs a belt to clip to, same as `pouch_color`.
   */
  readonly crystal_color_1: string | null;
  readonly crystal_color_2: string | null;
  readonly crystal_color_3: string | null;
  readonly crystal_color_4: string | null;
  /**
   * A small cutting/handling tool clipped beside the rig, standard Crystal
   * Conclave kit for a stock nobody grips bare-handed. Optional and off by
   * default: it is a second read at a scale where the crystals alone are
   * already close to the floor, so it only earns its keep on a character
   * deliberate enough about the kit to ask for it explicitly. Draws nothing
   * unless a belt is worn.
   */
  readonly crystal_tongs: boolean;
}

export const OUTFIT_FIELDS: readonly FieldSpec[] = [
  { name: "tunic_color", type: "str", nullable: true, default: "#4f7a52" },
  { name: "boot_color", type: "str", nullable: true, default: "#5b4632" },
  { name: "undersleeve_color", type: "str", nullable: true, default: null },
  { name: "belt_color", type: "str", nullable: true, default: null },
  { name: "belt_keeper_pair", type: "bool", nullable: false, default: false },
  { name: "belt_reach", type: "float", nullable: false, default: 1 },
  { name: "belt_cut", type: "str", nullable: true, default: null },
  { name: "apron_color", type: "str", nullable: true, default: null },
  { name: "skirt_color", type: "str", nullable: true, default: "#4f7a52" },
  { name: "skirt_cut", type: "str", nullable: true, default: null },
  { name: "underskirt_color", type: "str", nullable: true, default: null },
  { name: "trouser_color", type: "str", nullable: true, default: null },
  { name: "pouch_color", type: "str", nullable: true, default: null },
  { name: "skirt_length", type: "float", nullable: true, default: null },
  { name: "skirt_length_chibi", type: "float", nullable: true, default: null },
  { name: "tunic_tucked", type: "bool", nullable: false, default: false },
  { name: "neckline_round", type: "bool", nullable: false, default: false },
  { name: "neckline_trim", type: "bool", nullable: false, default: true },
  { name: "neckline_stand", type: "bool", nullable: false, default: true },
  { name: "neckline_notch", type: "float", nullable: true, default: null },
  { name: "sleeve_long", type: "bool", nullable: false, default: false },
  { name: "sleeve_under_cap", type: "bool", nullable: false, default: true },
  { name: "sleeve_cut", type: "str", nullable: true, default: null },
  { name: "collar_color", type: "str", nullable: true, default: null },
  { name: "collar_cut", type: "str", nullable: true, default: null },
  { name: "collar_mock", type: "bool", nullable: false, default: false },
  { name: "placket_color", type: "str", nullable: true, default: null },
  { name: "chest_pocket_color", type: "str", nullable: true, default: null },
  { name: "strap_color", type: "str", nullable: true, default: null },
  { name: "bodice_color", type: "str", nullable: true, default: null },
  { name: "boot_shaft", type: "float", nullable: false, default: 0 },
  { name: "boot_cut", type: "str", nullable: true, default: null },
  { name: "knee_sock_color", type: "str", nullable: true, default: null },
  { name: "ribbon_color", type: "str", nullable: true, default: null },
  { name: "underwear_color", type: "str", nullable: false, default: "#e8e4dc" },
  { name: "underwear_top", type: "bool", nullable: false, default: false },
  { name: "robe_color", type: "str", nullable: true, default: null },
  { name: "sleeve_drop", type: "float", nullable: false, default: 0 },
  { name: "belt_scale", type: "float", nullable: false, default: 1 },
  { name: "hakama_color", type: "str", nullable: true, default: null },
  { name: "hakama_length", type: "float", nullable: true, default: null },
  { name: "hakama_length_chibi", type: "float", nullable: true, default: null },
  { name: "headscarf_color", type: "str", nullable: true, default: null },
  { name: "goggle_color", type: "str", nullable: true, default: null },
  { name: "blindfold_color", type: "str", nullable: true, default: null },
  { name: "mask_color", type: "str", nullable: true, default: null },
  { name: "wristband_color", type: "str", nullable: true, default: null },
  { name: "wristband_text", type: "str", nullable: true, default: null },
  { name: "wristband_side", type: "int", nullable: false, default: 1 },
  { name: "shoulder_bars_color", type: "str", nullable: true, default: null },
  { name: "shoulder_bars", type: "int", nullable: false, default: 3 },
  { name: "shoulder_bars_side", type: "int", nullable: false, default: 1 },
  { name: "hat_color", type: "str", nullable: true, default: null },
  { name: "hat_band_color", type: "str", nullable: true, default: null },
  { name: "hair_clip_color", type: "str", nullable: true, default: null },
  { name: "hair_clip", type: "str", nullable: false, default: "bar" },
  { name: "staff_color", type: "str", nullable: true, default: null },
  { name: "staff_crystal_color", type: "str", nullable: true, default: null },
  { name: "katana_color", type: "str", nullable: true, default: null },
  { name: "katana_fittings_color", type: "str", nullable: true, default: null },
  { name: "katana_length", type: "float", nullable: false, default: 1 },
  { name: "coat_color", type: "str", nullable: true, default: null },
  { name: "coat_cut", type: "str", nullable: true, default: null },
  { name: "coat_sleeves", type: "bool", nullable: false, default: false },
  { name: "coat_length", type: "float", nullable: false, default: 0.55 },
  { name: "hip_pocket_color", type: "str", nullable: true, default: null },
  { name: "coat_button_color", type: "str", nullable: true, default: null },
  { name: "crystal_color_1", type: "str", nullable: true, default: null },
  { name: "crystal_color_2", type: "str", nullable: true, default: null },
  { name: "crystal_color_3", type: "str", nullable: true, default: null },
  { name: "crystal_color_4", type: "str", nullable: true, default: null },
  { name: "crystal_tongs", type: "bool", nullable: false, default: false },
];

/**
 * Expression knobs. Every default reproduces the stock chibi face, so a
 * character only states what it differs on.
 */
export interface FaceStyle {
  readonly eye_size: number;
  /**
   * Aperture width against its height. Below 1 gives a tall eye, above 1 a
   * long narrow one.
   */
  readonly eye_width: number;
  /**
   * How high the upper lid rides. 1.0 is wide open, lower is half-lidded.
   * The iris keeps its size and gets cropped, which is what reads as lidded
   * rather than simply small-eyed.
   */
  readonly eye_openness: number;
  /** How far the lower lid drops. Below 1 flattens the underside. */
  readonly eye_lower_lid: number;
  /** Raises the outer corner above the inner one. */
  readonly eye_tilt: number;
  /**
   * The gap between the eyes, as a share of an eye's half-width (the cast's median,
   * `_EYE_GAP`, when None). A narrow eye keeps the gap proportionate to itself, which
   * puts a tall narrow pair close together; a face that draws them wide apart says so.
   */
  readonly eye_gap: number | null;
  /** 0 is a rounded oval, 1 pulls all four corners out to sharp points. */
  readonly eye_corner: number;
  /**
   * Iris against the aperture's smaller half-axis. Below 1 leaves white
   * sclera showing all the way around it.
   */
  readonly iris_size: number;
  /**
   * How far each iris sits toward the nose, as a share of the room it has in the
   * aperture (its half-width less its radius): 0 centred, 1 against the inner corner.
   * The white then shows on the outer side only, as a face drawn with the iris
   * tucked in draws it. Both eyes move toward the nose, which `gaze` cannot do: it
   * sends both the same way.
   */
  readonly iris_inset: number;
  /**
   * The iris's height against its width: 1 a circle, above 1 a tall oval, which fills a
   * tall aperture from lid to lid without growing wider than the eye has room for.
   */
  readonly iris_aspect: number;
  /**
   * How deep the upper lid's shadow lies on the white of the eye, as a share of the eye's
   * height: a band of the white in a second, greyer tone along the lid, which takes the
   * glare off a wide eye. 0 leaves the white clean.
   */
  readonly lid_shadow: number;
  /**
   * How far the upper lash thickens toward the outer corner and how long its
   * flick runs past it: 1 the full lash (`_LASH_OUTER`, `_LASH_FLICK`), 0 a
   * lash of even, inner-corner weight with no flick. The men draw less of it,
   * where the flick read as winged eyeliner (`docs/detail-status.md`, D2).
   */
  readonly lash: number;
  /** 0 is level. Positive drops the inner ends (stern), negative raises them. */
  readonly brow_tilt: number;
  readonly brow_weight: number;
  /**
   * How long each brow runs, against the eye's own width: 1.0 the stock line, shorter a
   * short brow over a big eye.
   */
  readonly brow_length: number;
  /** 1.0 is the stock smile, 0 is a flat line, negative frowns. */
  readonly mouth_curve: number;
  readonly mouth_width: number;
  /**
   * How far the mouth sits below its usual place, in head radii: a longer lower
   * face, a smaller mouth set low in it.
   */
  readonly mouth_drop: number;
  /**
   * The nose as one small dot at its usual height, in place of the two ticks an older
   * face draws, for a face that reads younger and softer with it.
   */
  readonly nose_dot: boolean;
  /**
   * Whether the brows are drawn over the fringe rather than under it, for a face
   * whose reference draws them through the hair (a blunt fringe that comes down
   * to the lids).
   */
  readonly brows_over_hair: boolean;
  /**
   * How far the mouth hangs open: 0 is the shut line it has always been, 1 a
   * mouth about as deep as it is wide, and it grows only a little past that (a mouth
   * taller than wide reads as a slot). The upper edge is the same curve as the
   * shut mouth, so a face moves between the two without the lip jumping.
   */
  readonly mouth_open: number;
  /**
   * Where the eyes look, sideways: 0 straight at the viewer, 1 as far to the
   * viewer's right as the aperture lets the iris go, -1 to the left. Both eyes
   * move together. A figure that cannot turn can still look at the person it is
   * talking to, which is what this is for; it is a moment more than a mood, so
   * like `eyes_closed` it is not on `Expression`.
   */
  readonly gaze: number;
  readonly blush: number;
  /**
   * Fine wire spectacles. On `FaceStyle` rather than `Outfit` because they are
   * part of a face the way a scar is: nobody in this cast is drawn once with
   * them and once without, and an expression must not be able to remove them.
   */
  readonly glasses: boolean;
  /**
   * The cel shadow the head casts on the neck: a band of darker skin under
   * the jaw, following it. Off by default, the owner's call that skin stays
   * flat (`docs/detail-plan.md`, decision 2) with this as an option.
   */
  readonly chin_shadow: boolean;
  /**
   * Both eyes shut: each drawn as one lash line instead of an aperture. Not a
   * mood, so not on `Expression`: it is a moment (a blink, a frame of an
   * animation built from stills) rather than a face someone wears, and a
   * still that means "asleep" or "at peace" can set it directly. Why
   * `eye_openness` cannot reach this on its own: it moves only the upper lid,
   * and at 0 the lower half of the almond, white and iris, is still there.
   */
  readonly eyes_closed: boolean;
  /**
   * Which cheek carries a scar, **stated from the viewer's side**: -1 the left
   * of the picture, 1 the right, 0 none. The figure faces us, so the viewer's
   * right is the character's left, and a description written the other way
   * round ("a burn along her left cheek") means 1 here, not -1. Worth spelling
   * out because both frames are in use: this file counts in picture space and
   * every character description counts in body space, and the two disagree on
   * every single scar without ever disagreeing visibly enough to notice.
   */
  readonly scar_side: number;
}

export const FACESTYLE_FIELDS: readonly FieldSpec[] = [
  { name: "eye_size", type: "float", nullable: false, default: 1 },
  { name: "eye_width", type: "float", nullable: false, default: 0.88 },
  { name: "eye_openness", type: "float", nullable: false, default: 1 },
  { name: "eye_lower_lid", type: "float", nullable: false, default: 1 },
  { name: "eye_tilt", type: "float", nullable: false, default: 0.1 },
  { name: "eye_gap", type: "float", nullable: true, default: null },
  { name: "eye_corner", type: "float", nullable: false, default: 0.35 },
  { name: "iris_size", type: "float", nullable: false, default: 0.72 },
  { name: "iris_inset", type: "float", nullable: false, default: 0 },
  { name: "iris_aspect", type: "float", nullable: false, default: 1 },
  { name: "lid_shadow", type: "float", nullable: false, default: 0 },
  { name: "lash", type: "float", nullable: false, default: 1 },
  { name: "brow_tilt", type: "float", nullable: false, default: 0 },
  { name: "brow_weight", type: "float", nullable: false, default: 1 },
  { name: "brow_length", type: "float", nullable: false, default: 1 },
  { name: "mouth_curve", type: "float", nullable: false, default: 1 },
  { name: "mouth_width", type: "float", nullable: false, default: 1 },
  { name: "mouth_drop", type: "float", nullable: false, default: 0 },
  { name: "nose_dot", type: "bool", nullable: false, default: false },
  { name: "brows_over_hair", type: "bool", nullable: false, default: false },
  { name: "mouth_open", type: "float", nullable: false, default: 0 },
  { name: "gaze", type: "float", nullable: false, default: 0 },
  { name: "blush", type: "float", nullable: false, default: 1 },
  { name: "glasses", type: "bool", nullable: false, default: false },
  { name: "chin_shadow", type: "bool", nullable: false, default: false },
  { name: "eyes_closed", type: "bool", nullable: false, default: false },
  { name: "scar_side", type: "int", nullable: false, default: 0 },
];

/**
 * A mood, as a **delta** on whatever face a character already has.
 *
 * Not a `FaceStyle`, and the distinction is the whole point. A `FaceStyle`
 * carries two different kinds of thing: what a face *is* (`eye_size`,
 * `eye_width`, `eye_corner`, `eye_tilt`, `iris_size`) and what it is *doing*
 * right now (`brow_tilt`, `mouth_curve`, `eye_openness`). Satoshi's aperture is
 * 0.92 wide and 1.08 long because that is his face at rest, in every scene, and
 * an expression that arrived as a whole `FaceStyle` would quietly overwrite it
 * with the stock values and hand back a different character wearing the right
 * mood.
 *
 * So every field here is `None` by default, meaning *leave that one alone*, and
 * only the named fields are written. `None` rather than a neutral number
 * because there is no number that means "unchanged": 0.0 is a real brow tilt,
 * and a level brow is a choice a mood can make.
 *
 * Fields are limited to the ones a mood moves. Adding `eye_size` here would be
 * a way to make a character stop being themselves.
 */
export interface Expression {
  /**
   * 0 is level. Positive drops the inner ends (stern), negative raises them,
   * which is the grief reading rather than more of the same.
   */
  readonly brow_tilt: number | null;
  readonly brow_weight: number | null;
  /**
   * How high the upper lid rides. This is the one that survives being shrunk:
   * a brow is a thin stroke and washes out at thumbnail size, where a lid
   * changes the shape of a filled mass. Measured at about four times the
   * signal of `brow_tilt` on the cover, at both sizes.
   */
  readonly eye_openness: number | null;
  readonly eye_lower_lid: number | null;
  readonly mouth_curve: number | null;
  readonly mouth_width: number | null;
  readonly mouth_open: number | null;
}

export const EXPRESSION_FIELDS: readonly FieldSpec[] = [
  { name: "brow_tilt", type: "float", nullable: true, default: null },
  { name: "brow_weight", type: "float", nullable: true, default: null },
  { name: "eye_openness", type: "float", nullable: true, default: null },
  { name: "eye_lower_lid", type: "float", nullable: true, default: null },
  { name: "mouth_curve", type: "float", nullable: true, default: null },
  { name: "mouth_width", type: "float", nullable: true, default: null },
  { name: "mouth_open", type: "float", nullable: true, default: null },
];

/**
 * Everything about a character that is not its proportions.
 *
 * The public interface of the package: colours, the garments in `outfit`, the
 * expression in `face`, which haircut and how long, plus the two skeleton knobs
 * (`heads`, `frame`) used when `render_character` is not handed a skeleton of
 * its own. Frozen, so a variant is `dataclasses.replace(base, ...)` and a
 * preset can be shared without anything downstream editing it.
 *
 * Anything a character needs to differ on belongs here, on `Outfit` or on
 * `FaceStyle` with a neutral default, never hardcoded into a part function:
 * that is what keeps this a generator rather than one character's renderer.
 */
export interface CharacterParams {
  readonly skin_tone: string;
  readonly hair_color: string;
  /** Tone the hair fades into below the jaw. None means single-tone hair. */
  readonly hair_tip_color: string | null;
  /**
   * Where the hair ends, measured chin (0) to hip (1), so it stays the same
   * haircut across builds. Roughly: 0.15 jaw, 0.45 chest, 1.0 hip.
   */
  readonly hair_length: number;
  /** Which haircut, by name from HAIRSTYLES. */
  readonly hairstyle: string;
  readonly eye_color: string;
  /**
   * Hair that leaves the skull and comes back: a tail hanging behind the head,
   * and a knot gathered on the crown. Both are separate parts rather than
   * `Hairstyle` entries, which is what makes them cheap: a `Hairstyle` is five
   * callables that have to agree with each other and with the ceiling test,
   * while these two compose with *any* cut, so one shape gives Krista her
   * ponytail and Haruto and Daizen their topknots without touching the five
   * existing cuts at all.
   *
   * How far the tail falls, shoulder (0) to hip (1). 0 is no tail.
   */
  readonly hair_tail: number;
  /** A knot gathered on the crown, sitting proud of the skull. */
  readonly hair_knot: boolean;
  /**
   * Facial hair. None leaves the face bare, which is everybody but two.
   * Its own colour rather than reading `hair_color`, because a beard greys
   * before the head does on one of the two who wear one, and because a
   * character could dye one and not the other.
   */
  readonly beard_color: string | null;
  /**
   * How far the beard drops below the chin, in head radii: 0.07 is the short
   * groomed beard Reinhard wears, 0.17 the fuller one Daizen does.
   */
  readonly beard_length: number;
  readonly outfit: Outfit;
  readonly face: FaceStyle;
  /**
   * A named body type from `BODY_TYPES`: the tall chibi is the one figure
   * (`docs/tall-chibi-plan.md`), and this picks its proportions. A name rather
   * than the numbers, like `hairstyle`, so a character stays a flat, linkable
   * set of fields. `heads` and the compressed chibi (`body=None`) are retired;
   * an old link carrying either loads as the default (`urlstate`).
   */
  readonly body: string;
  /**
   * How tall the figure stands against its head, 1.0 the body as measured:
   * below the shoulder line the figure is this many times as long, two thirds
   * of the difference in the legs (`BodyProfile.stretched`,
   * `docs/tall-chibi-plan.md`, R4b). The web tool offers 0.8 to 1.3, young
   * to adult inside the one style; on its own canvas a taller figure has a
   * smaller head, the canvas being a fixed size.
   */
  readonly height: number;
  /**
   * Which relaxed hand the figure is drawn with (`HAND_STYLES`, `docs/hands-plan.md`):
   * "mitten", the chibi's own and the default; "notched", the mitten with its tip
   * cut into three fingers; "stroked", its silhouette with two finger strokes;
   * "curled", a half-closed hand; "traced", the open hand taken off the reference
   * (`docs/detail-plan.md`, D4d), widened and squared at the wrist. "grip" is the
   * old name for a mitten with a fist on a held staff, kept so a saved character
   * still reads: it means `hand_style="mitten"` with `grip_style="fist"`.
   */
  readonly hand_style: string;
  /**
   * How the hand that holds a staff is drawn (`GRIP_STYLES`): "mitten", the same
   * hand as the other (the default), or "fist", the canon's rounded fist with its
   * finger rolls on the pole side.
   */
  readonly grip_style: string;
  /**
   * How old the face reads, one axis from child to old (`docs/detail-plan.md`,
   * D3). 0 to 1 is face maturity, the chibi face growing up: the skull narrows
   * to a jaw, the eyes grow smaller, narrower and lower, the mouth drops, a
   * nose grows in (`Skeleton.face_maturity`). 1 to 2 ages the grown face the
   * way `aged_face` says. Its own slider rather than following `height`, since
   * short adults and tall teenagers both exist.
   */
  readonly face_age: number;
  /**
   * A bat familiar in flight beside the figure's left shoulder: his fur (and
   * membranes, which the reference draws in the same tone) and his eyes.
   * `None` draws nothing. Two fields rather than one because the book's two
   * familiars are the same creature colour-inverted, Kou black with black
   * eyes and Mori pale with silver ones.
   */
  readonly familiar_color: string | null;
  readonly familiar_eye_color: string | null;
  /**
   * Turns the familiar's mouth up. His reference draws it turned down, which
   * is his book register early on (dry, sarcastic, worn); this is for the
   * later one, and for a cover that wants to look friendly.
   */
  readonly familiar_smile: boolean;
  /**
   * Shoulder against hip: -1 narrow-shouldered and wide-hipped, 0 neutral, +1
   * the other way. Only bites at taller builds. Ignored when handed a skeleton.
   */
  readonly frame: number;
  /**
   * How far the figure's bust carries, 0 flat. A character trait rather than a
   * proportion of the build, which is why it lives here and not on the
   * skeleton: the skeleton says where a bust sits, this says how much of one
   * there is. Male characters stay at 0 and render byte-identically to before
   * the anchor existed (`docs/bust-plan.md`).
   */
  readonly bust: number;
  /**
   * How much chest definition shows bare, 0 none: two soft arcs under the
   * pectorals, drawn only with the tunic off and no bust, which replaces them.
   * A trait beside `bust` rather than a sex flag; the men carry 1.0
   * (`docs/bare-body-plan.md`, step 6). No clothed figure reads it.
   */
  readonly chest: number;
  /**
   * Where the upper body ends and the lower begins, in head radii: shifts the
   * waist and hip lines together, so the belt (and everything hung from it)
   * rides up (negative) or down (positive) while the shoulders, knees and
   * soles stay put. 0 is the build's own. Ignored when handed a skeleton.
   */
  readonly waist_shift: number;
  /**
   * Outward swing of an arm below the sleeve hem, in degrees. 0 is the
   * default hang, straight down; positive pivots the tube, cuff and hand as
   * one rigid piece about the sleeve hem so the hand moves away from the
   * body and up, the way an arm lifts to hold something out at the side.
   * Named **from the viewer's side**, the same frame `FaceStyle.scar_side`
   * documents and for the same reason: `right_arm_out` is the character's
   * own right arm, which is the viewer's left, and `left_arm_out` is the
   * character's own left arm, the viewer's right.
   */
  readonly right_arm_out: number;
  readonly left_arm_out: number;
  readonly shaded: boolean;
  /**
   * How the figure is finished. "flat" is the house style and the only one the
   * presets, `ref-out/` and the web tool use: flat colour, hard edges, one black
   * line. "soft" is an opt-in experiment for a caller that wants the figure to sit
   * beside painted art (a companion app's picture packs): see `_soft` and the
   * `_SOFT_*` constants. It adds gradients and tinted lines and changes no shape.
   */
  readonly finish: string;
  /**
   * How strong the soft finish's hair clumps are: the lit steps and the highlights rise by this
   * much and the shadow steps sink by it, and 0 draws none. 1 is the default look, the owner's pick
   * from five strengths on five hair colours (2026-10-16): half the strength the clumps were
   * first judged at, which was a bit strong on pale colours. 2 is that first strength. The flat
   * finish ignores it.
   */
  readonly highlight_strength: number;
}

export const CHARACTERPARAMS_FIELDS: readonly FieldSpec[] = [
  { name: "skin_tone", type: "str", nullable: false, default: "#f2c9a1" },
  { name: "hair_color", type: "str", nullable: false, default: "#e8b84b" },
  { name: "hair_tip_color", type: "str", nullable: true, default: null },
  { name: "hair_length", type: "float", nullable: false, default: 0.45 },
  { name: "hairstyle", type: "str", nullable: false, default: "long_blunt" },
  { name: "eye_color", type: "str", nullable: false, default: "#4a9c6d" },
  { name: "hair_tail", type: "float", nullable: false, default: 0 },
  { name: "hair_knot", type: "bool", nullable: false, default: false },
  { name: "beard_color", type: "str", nullable: true, default: null },
  { name: "beard_length", type: "float", nullable: false, default: 0.15 },
  { name: "outfit", type: "Outfit", nullable: false, default: null },
  { name: "face", type: "FaceStyle", nullable: false, default: null },
  { name: "body", type: "str", nullable: false, default: "tall_chibi_long_torso" },
  { name: "height", type: "float", nullable: false, default: 1 },
  { name: "hand_style", type: "str", nullable: false, default: "mitten" },
  { name: "grip_style", type: "str", nullable: false, default: "mitten" },
  { name: "face_age", type: "float", nullable: false, default: 0 },
  { name: "familiar_color", type: "str", nullable: true, default: null },
  { name: "familiar_eye_color", type: "str", nullable: true, default: null },
  { name: "familiar_smile", type: "bool", nullable: false, default: false },
  { name: "frame", type: "float", nullable: false, default: 0 },
  { name: "bust", type: "float", nullable: false, default: 0 },
  { name: "chest", type: "float", nullable: false, default: 0 },
  { name: "waist_shift", type: "float", nullable: false, default: 0 },
  { name: "right_arm_out", type: "float", nullable: false, default: 0 },
  { name: "left_arm_out", type: "float", nullable: false, default: 0 },
  { name: "shaded", type: "bool", nullable: false, default: true },
  { name: "finish", type: "str", nullable: false, default: "flat" },
  { name: "highlight_strength", type: "float", nullable: false, default: 1 },
];

export const DEFAULT_OUTFIT: Outfit = { tunic_color: "#4f7a52", boot_color: "#5b4632", undersleeve_color: null, belt_color: null, belt_keeper_pair: false, belt_reach: 1, belt_cut: null, apron_color: null, skirt_color: "#4f7a52", skirt_cut: null, underskirt_color: null, trouser_color: null, pouch_color: null, skirt_length: null, skirt_length_chibi: null, tunic_tucked: false, neckline_round: false, neckline_trim: true, neckline_stand: true, neckline_notch: null, sleeve_long: false, sleeve_under_cap: true, sleeve_cut: null, collar_color: null, collar_cut: null, collar_mock: false, placket_color: null, chest_pocket_color: null, strap_color: null, bodice_color: null, boot_shaft: 0, boot_cut: null, knee_sock_color: null, ribbon_color: null, underwear_color: "#e8e4dc", underwear_top: false, robe_color: null, sleeve_drop: 0, belt_scale: 1, hakama_color: null, hakama_length: null, hakama_length_chibi: null, headscarf_color: null, goggle_color: null, blindfold_color: null, mask_color: null, wristband_color: null, wristband_text: null, wristband_side: 1, shoulder_bars_color: null, shoulder_bars: 3, shoulder_bars_side: 1, hat_color: null, hat_band_color: null, hair_clip_color: null, hair_clip: "bar", staff_color: null, staff_crystal_color: null, katana_color: null, katana_fittings_color: null, katana_length: 1, coat_color: null, coat_cut: null, coat_sleeves: false, coat_length: 0.55, hip_pocket_color: null, coat_button_color: null, crystal_color_1: null, crystal_color_2: null, crystal_color_3: null, crystal_color_4: null, crystal_tongs: false };
export const DEFAULT_FACESTYLE: FaceStyle = { eye_size: 1, eye_width: 0.88, eye_openness: 1, eye_lower_lid: 1, eye_tilt: 0.1, eye_gap: null, eye_corner: 0.35, iris_size: 0.72, iris_inset: 0, iris_aspect: 1, lid_shadow: 0, lash: 1, brow_tilt: 0, brow_weight: 1, brow_length: 1, mouth_curve: 1, mouth_width: 1, mouth_drop: 0, nose_dot: false, brows_over_hair: false, mouth_open: 0, gaze: 0, blush: 1, glasses: false, chin_shadow: false, eyes_closed: false, scar_side: 0 };
export const DEFAULT_EXPRESSION: Expression = { brow_tilt: null, brow_weight: null, eye_openness: null, eye_lower_lid: null, mouth_curve: null, mouth_width: null, mouth_open: null };
export const DEFAULT_CHARACTERPARAMS: CharacterParams = { skin_tone: "#f2c9a1", hair_color: "#e8b84b", hair_tip_color: null, hair_length: 0.45, hairstyle: "long_blunt", eye_color: "#4a9c6d", hair_tail: 0, hair_knot: false, beard_color: null, beard_length: 0.15, outfit: DEFAULT_OUTFIT, face: DEFAULT_FACESTYLE, body: "tall_chibi_long_torso", height: 1, hand_style: "mitten", grip_style: "mitten", face_age: 0, familiar_color: null, familiar_eye_color: null, familiar_smile: false, frame: 0, bust: 0, chest: 0, waist_shift: 0, right_arm_out: 0, left_arm_out: 0, shaded: true, finish: "flat", highlight_strength: 1 };
