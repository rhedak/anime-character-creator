"""Named characters.

A preset is just a CharacterParams, so a character is a checked-in artifact
that gets re-rendered as the shape code improves, rather than a pile of CLI
flags someone has to remember.
"""

from __future__ import annotations

from dataclasses import replace

from .character import CharacterParams, Expression, FaceStyle, Outfit

# Satoko and Satoshi are meant to read as related, so the palette they share
# lives here once rather than being duplicated per character. What tells them
# apart is the haircut, the lower body, and the frame, not the colors.
# Sampled off the canon as the modal exact colour inside a flat patch of hair,
# not from a quantised histogram, whose buckets are eight points a channel and so
# cannot settle a question this size. Every other surface came within four points
# of what we already had, which is not visible; this one was twelve points short
# of blue, enough to read as a shade more orange than the canon's.
HAIR = "#e3b448"
HAIR_TIPS = "#eceae3"
TUNIC = "#4a6845"
UNDERSLEEVE = "#ab9e86"
BELT = "#5f4f42"
BOOTS = "#6d4c33"

# Satoko: blonde fading to white at the ends, muted green eyes, green
# working tunic, brown leather boots. Colors sampled from ref/satoko.png.
# Guarded expression carried by stern brows and a flat mouth, per the canon,
# which keeps chibi eyes big and open even on a wary character. A burn along her
# left jaw and cheek, which is `scar_side=1`: that field counts from the
# viewer's side and she faces us, so her left is the right of the picture.
SATOKO = CharacterParams(
    skin_tone="#f6dbc2",
    hair_color=HAIR,
    hairstyle="long_traced",
    hair_tip_color=HAIR_TIPS,
    eye_color="#74905e",
    # Working clothes in layers: green tunic over tan undersleeves, brown
    # leather belt and apron, green skirt over a dark grey underskirt that
    # shows below its hem. The skirt runs to mid-calf in the reference, well
    # below where a hem sits by default.
    outfit=Outfit(
        tunic_color=TUNIC,
        boot_color=BOOTS,
        undersleeve_color=UNDERSLEEVE,
        belt_color=BELT,
        apron_color="#6f5c4e",
        skirt_color="#53654b",
        underskirt_color="#54534f",
        # Darker than both belt and apron so the pouches read against either,
        # whichever one they happen to hang over.
        pouch_color="#564737",
        skirt_length=0.70,
        # Keeps the pre-task-32 chibi silhouette the owner had gotten used to:
        # this reproduces the exact hem the old floor-at-half pull-back used
        # to land on at chibi, so the realistic build (measured against
        # `ref/satoko.png`, and unaffected by any of this since it never hit
        # the pull-back) is the only one whose length actually changed.
        skirt_length_chibi=0.499,
    ),
    # Slightly the narrower-shouldered of the two. Only bites at taller builds.
    frame=-0.3,
    face=FaceStyle(
        eye_size=0.95,
        eye_width=1.05,
        eye_openness=0.95,
        eye_lower_lid=0.95,
        eye_tilt=0.15,
        eye_corner=0.45,
        # Bigger than the 0.62 the canon's measured 0.116-of-head-width iris
        # implies: at that size the open aperture left a band of white above
        # the iris and the face read startled. Pushed further still, past the
        # aperture's own bound so the lids crop it top and bottom rather than
        # merely filling the white: that crop is what a sympathetic rather
        # than a startled stare needs (2026-08-19, same call across the cast).
        iris_size=1.06,
        brow_tilt=0.40,
        brow_weight=0.85,
        mouth_curve=0.0,
        mouth_width=0.75,
        blush=0.0,
        scar_side=1,
    ),
)

# Satoshi: the same palette and the same tunic as Satoko, deliberately. What
# differs is a short layered cut and trousers instead of skirt and apron.
# Colors sampled from ref/satoshi.png. He carries Satoko's scar, on the same
# cheek: they are the male and female reading of one character, so the scar is
# part of the face rather than something that tells them apart. It is absent
# from ref/satoshi.png only because the model that drew that reference dropped
# it, which makes this one of the few places the reference is not the target.
SATOSHI = CharacterParams(
    skin_tone="#f2d4bb",
    hair_color=HAIR,
    hair_tip_color=HAIR_TIPS,
    hairstyle="short_crop",
    # Within the crop's own range, so this is where the side tips flick, not
    # anything measured against the body. `short_crop`'s range is set so that
    # 0.65 is the size the cut was traced at, which makes this the neutral
    # value rather than a tuned one: shorter tightens the whole cut to the
    # skull, longer heads toward shaggy.
    hair_length=0.65,
    eye_color="#74905e",
    outfit=Outfit(
        tunic_color=TUNIC,
        boot_color=BOOTS,
        undersleeve_color=UNDERSLEEVE,
        belt_color=BELT,
        trouser_color="#55574c",
        skirt_color=None,
        # Both his references tuck it in, so the belt is the boundary between
        # the tunic and the trousers rather than a band across the tunic with
        # more tunic hanging below it.
        tunic_tucked=True,
    ),
    # Broader across the shoulder and narrow in the hip, which is the whole of
    # what tells him from Satoko below the neck once the clothes match.
    frame=1.0,
    face=FaceStyle(
        eye_size=0.92,
        eye_width=1.08,
        eye_openness=0.90,
        eye_lower_lid=0.92,
        eye_tilt=0.12,
        # A touch narrower and sharper-cornered than Satoko's, which is all
        # that is left of the lidded look now the canon opens the aperture.
        eye_corner=0.50,
        # Past the aperture's own bound so the lids crop it, same call as
        # Satoko's (see her comment).
        iris_size=1.02,
        brow_tilt=0.25,
        brow_weight=0.80,
        mouth_curve=0.0,
        mouth_width=0.70,
        blush=0.0,
        scar_side=1,
    ),
)

# Kyoko and Tomohiro are not two more characters. They are Satoko and Satoshi
# **before**, and the book they come from calls this "the single most important
# design": one person styled to read as two, where the resemblance should be
# visible once someone is told to look for it and should announce itself
# otherwise (`docs/mist-characters/character_designs.md`). The disguise is a
# maintained blonde dye over black regrowth, a burn scar, and plain clothes in
# place of a researcher's. It is not a different face.
#
# So these are `replace()` on the shipped presets rather than four numbers typed
# out again, and that is the whole point rather than a shortcut. A copied face
# agrees with its original on the day it is written and drifts every time
# somebody tunes an eye afterwards, silently, because nothing checks. A derived
# one cannot: change Satoshi's aperture and Tomohiro's changes with it, because
# there is only one aperture. The property the story needs is exactly the
# property `replace` enforces, which is the same argument `Expression` makes for
# being a delta rather than a whole `FaceStyle`.
#
# Three fields differ and the list is closed:
#
#   hair_color      jet black, the natural colour the dye covers
#   hair_tip_color  None, because black hair has no pale ends to fade into
#   scar_side       0, because the burn has not happened yet
#
# The haircut deliberately carries over. The design document lists the dye, the
# scar, the expression and the clothes as the disguise, and not the cut, so
# keeping it is correct as well as free. `ref/tomohiro.png` draws him shaggier
# than the same document's "sleek and neat", which is the reference disagreeing
# with its own text rather than a decision this file has to take.
#
# **The references drift on the one feature that cannot drift.** Measured inside
# the iris, `ref/satoshi.png` is #5a6654 and `ref/satoko.png` #5a6c54, both the
# pale jade-green the document specifies; `ref/tomohiro.png` is #303636 and
# `ref/kyoko.png` #303036, which is grey. The eyes are named there as the one
# feature the disguise does not touch, so that is drift landing precisely on the
# resemblance itself. Here the four share an `eye_color` by construction and the
# question cannot arise. Their hair, sampled the same way, came out #313437 and
# #313538, which is agreement to within a rounding step and the reason one
# constant covers both.
BLACK_HAIR = "#313538"


def _before(base: CharacterParams, outfit: Outfit) -> CharacterParams:
    """The same person before the dye and the burn, in the clothes of that life.

    The face and everything about it comes through untouched; the three fields
    listed above and the wardrobe are all that differ. The outfit is passed in
    rather than derived because it is the one thing that genuinely *is* different
    rather than a variation: a researcher's layers are not an innkeeper's with a
    colour changed.
    """
    return replace(
        base,
        hair_color=BLACK_HAIR,
        hair_tip_color=None,
        outfit=outfit,
        face=replace(base.face, scar_side=0),
    )


# Both references dress the pair the same way underneath: a navy tunic closed
# with a wide dark sash, over dark legs. What differs is the outer layer, which
# is Tomohiro's cropped jacket against Kyoko's coat to mid-calf, and that is one
# garment at two lengths. The agreement between the two references is worth
# noting rather than assuming: they were drawn separately, and getting the inner
# layer to match is the design working.
BEFORE_TUNIC = "#3a3e4a"
BEFORE_SASH = "#22242c"
BEFORE_LEG = "#2b2d34"

KYOKO = _before(
    SATOKO,
    Outfit(
        tunic_color=BEFORE_TUNIC,
        boot_color="#4a3a2c",
        undersleeve_color=BEFORE_TUNIC,
        belt_color=BEFORE_SASH,
        trouser_color=BEFORE_LEG,
        skirt_color=None,
        tunic_tucked=True,
        boot_shaft=0.75,
        coat_color="#575d67",
        coat_length=0.72,
    ),
)
TOMOHIRO = _before(
    SATOSHI,
    Outfit(
        tunic_color=BEFORE_TUNIC,
        boot_color="#4a3a2c",
        undersleeve_color=BEFORE_TUNIC,
        belt_color=BEFORE_SASH,
        trouser_color=BEFORE_LEG,
        skirt_color=None,
        tunic_tucked=True,
        coat_color="#4a5442",
        coat_length=0.44,
    ),
)

# ---------------------------------------------------------------------------
# The rest of the cast.
#
# **These are first drafts and several are deliberately underdressed.** Each one
# carries the colouring and the frame its design calls for, and the closest
# garments the generator can currently build, which for the five Wodensreich
# officers means a plain tunic where a uniform belongs and for the three robed
# characters means a tunic and trousers where a kimono belongs. That is a stated
# stage, not an oversight: the alternative was to build the uniform, the coat and
# the robe first and have nine of fourteen characters not exist for a long while,
# and a cast sheet with everyone on it in rough clothes answers questions a
# perfect quarter of a cast cannot. Which garment each is waiting for is on the
# preset. See `docs/character-roster-plan.md` for the order they get built in.
#
# Colours: the design document
# (`docs/mist-characters/character_designs.md`) is the authority on what a
# character *is*, and it names hair, eyes and garments per person. Where it says
# "slate gray-blue" rather than a number, the number was sampled off the
# reference as the modal exact colour inside a flat patch, the way Satoko's were
# (`harness/roster/palette.py`).


# One uniform tone for all five who wear it, rather than the five different ones
# the references measure (#38424b on Elara through #5d6a73 on Viktor). That
# spread is the reference images' lighting, not five designs: the document is
# explicit that they "share Reinhard's uniform base ... so the group reads
# visually as one expedition", and reading as one group is exactly what a cast
# sheet is for. Tenno wears the same cut in khaki, which is a design difference
# and so does get its own tone.
def aged(face: FaceStyle, years: float = 1.0) -> FaceStyle:
    """A face read older, as a scaling of the fields that already exist.

    The cast runs from teens to seventies and `FaceStyle` has no age field. It
    does not get one, because everything the references use to say "sixty" is
    brushwork: crow's feet, jowls, slack skin, the texture of a beard. That is
    the painterly half this project discards on purpose, and none of it survives
    a chibi head at tile size anyway. So age has to be re-said in the vocabulary
    a flat drawing has, and the vocabulary a flat drawing has is the aperture.

    **The eye carries almost all of it.** A younger face here is a large, wide
    open eye with a big iris, which is the whole chibi look; walking those three
    numbers down reads as age immediately and reads as nothing else. Brow weight
    adds a little on top. What does *not* work is a hairline or a wrinkle: one
    needs a field nothing else would use, and the other is a line so fine that at
    150 pixels it is a smudge.

    `years` is a dial rather than a flag, 0 leaving a face alone and 1 being the
    cast's oldest. Chiyo, Daizen and Tenno take the full amount; Keiko and Reika
    are written directly, since they read composed rather than old and want a
    smaller change than this makes at any setting.

    A function rather than an `Expression`, deliberately. An expression is a
    *mood*, something a character puts on and takes off, and every field it may
    touch is one that changes minute to minute. Age is the opposite: it belongs
    to `eye_size` and `iris_size`, which are the fields `Expression` is forbidden
    to move because they are who the face is. Same shape of idea, opposite half
    of the dataclass, so it stays a separate thing.
    """
    return replace(
        face,
        eye_size=face.eye_size * (1 - 0.14 * years),
        eye_openness=face.eye_openness * (1 - 0.16 * years),
        eye_lower_lid=face.eye_lower_lid * (1 - 0.07 * years),
        iris_size=face.iris_size * (1 - 0.09 * years),
        brow_weight=face.brow_weight * (1 + 0.18 * years),
    )


UNIFORM = "#55636d"
UNIFORM_BELT = "#2f2b28"
UNIFORM_BOOTS = "#241f1d"
# The four crystals every Wodensreich soldier in the cast carries clipped to
# the belt, standard-issue Donarsblut stock rather than a personal palette,
# so every uniformed character reads as drawing from the same kit. Chosen to
# read distinctly from each other rather than to match `design.md`'s
# type/attribute grid, which does not assign any type a canon color.
CRYSTAL_KIT = ("#c0524a", "#4a7ac0", "#5aa06a", "#d9b23c")
KHAKI = "#ae9f86"
# Weathered, for the faces the document describes as older or worn. A duller,
# slightly deeper skin than the young cast's, which is as much as a flat drawing
# can say about age through skin alone.
SKIN_WORN = "#e0c0a4"
SKIN = "#f2d4bb"

CHIYO = CharacterParams(
    skin_tone=SKIN_WORN,
    # Rust-copper rather than plain gray: the design document's "gray-streaked
    # dark hair" was one more instance of the reference-image drift toward a
    # narrow brown/black/gray band across nearly the whole side cast, not a
    # story-load-bearing color. Kept monocolor rather than fading to gray at
    # the tips (`hair_tip_color`, the mechanic built for Satoko's dye job):
    # her headscarf covers most of the length that fade would land on, so a
    # second tone would mostly be wasted. Warm amber eyes for the firm,
    # hearth-grounded read the face already carries.
    hair_color="#a85a35",
    hairstyle="long_traced",
    hair_length=0.16,
    eye_color="#c9963f",
    # Waiting on: a bib apron (hers covers the chest, where Satoko's hangs from
    # the belt) and a headscarf. Until then this is Satoko's layer stack in
    # innkeeper's browns, which is genuinely close: the reference is the same
    # tunic, sash, overskirt and underskirt.
    outfit=Outfit(
        tunic_color="#9c8f76",
        boot_color="#6b5541",
        undersleeve_color="#9c8f76",
        belt_color="#5b4a3c",
        apron_color="#6b5a48",
        skirt_color="#7a705c",
        underskirt_color="#4f5347",
        pouch_color="#4f4133",
        skirt_length=0.78,
        # See Satoko's `skirt_length_chibi` comment: same reasoning, her own
        # pre-task-32 chibi hem reproduced exactly.
        skirt_length_chibi=0.534,
        headscarf_color="#8d8064",
    ),
    frame=-0.2,
    # Firm and assessing rather than warm: the innkeeper who keeps the books,
    # the rooms and the people in line. Brows down, mouth set flat, then aged.
    face=aged(
        FaceStyle(
            eye_size=1.00,
            eye_width=1.06,
            eye_openness=0.86,
            eye_tilt=0.10,
            eye_corner=0.50,
            iris_size=1.04,
            brow_tilt=0.50,
            brow_weight=0.90,
            mouth_curve=-0.10,
            mouth_width=0.68,
            blush=0.0,
        )
    ),
)

DAIZEN = CharacterParams(
    skin_tone=SKIN_WORN,
    # Dark iron-blue-gray rather than plain gray, and gold eyes rather than
    # the pale blue an earlier reference image happened to render: his own
    # name carries this, 黒金 (Kurogane) pairing "black" with the character
    # for gold/metal, so dark "black metal" hair and genuinely golden eyes are
    # the character's own naming pun made literal rather than a departure
    # from it. Beard matched to the hair below, one tone rather than two.
    hair_color="#4a4f57",
    hairstyle="short_layered",
    hair_length=0.45,
    eye_color="#d4a83c",
    hair_knot=True,
    beard_color="#4a4f57",
    beard_length=0.17,
    # Waiting on: an open haori over a kimono, an obi, and a full beard. The
    # navy is the haori's, the dark green underneath is the kimono's.
    outfit=Outfit(
        tunic_color="#3d4a39",
        boot_color="#54402f",
        undersleeve_color="#2e352c",
        belt_color="#6b5334",
        trouser_color="#2e302b",
        skirt_color=None,
        tunic_tucked=True,
        robe_color="#293040",
        sleeve_drop=0.45,
        belt_scale=2.8,
    ),
    frame=1.0,
    # Shrewd and severe, and the oldest-looking man in the cast next to Tenno.
    face=aged(
        FaceStyle(
            eye_size=0.84,
            eye_width=1.10,
            eye_tilt=0.14,
            eye_corner=0.62,
            iris_size=1.09,
            brow_tilt=0.65,
            brow_weight=1.00,
            mouth_curve=-0.20,
            mouth_width=0.70,
            blush=0.0,
        )
    ),
)

ELARA = CharacterParams(
    skin_tone="#e8c8ab",
    # Deep wine-burgundy rather than the plain dark auburn a reference image
    # settled on: controlled and deep rather than bright, matching a
    # disciplined battle-mage rather than softening her. Moss-olive eyes,
    # steady rather than warm, for the same reason.
    hair_color="#6b2c35",
    hairstyle="short_layered",
    hair_length=0.34,
    eye_color="#7c8a52",
    # Her scar is not waiting on anything: it is the part Satoko already has,
    # which is why she is the one who proves it generalises.
    outfit=Outfit(
        tunic_color=UNIFORM,
        boot_color=UNIFORM_BOOTS,
        undersleeve_color=UNIFORM,
        belt_color=UNIFORM_BELT,
        trouser_color=UNIFORM,
        skirt_color=None,
        tunic_tucked=True,
        collar_color=UNIFORM,
        placket_color=UNIFORM_BELT,
        chest_pocket_color=UNIFORM,
        strap_color=UNIFORM_BELT,
        boot_shaft=1.0,
        # Issued kit, not personal style: every Wodensreich soldier in the
        # cast wears the same four (`CRYSTAL_KIT`), Krista included. What
        # tells a Crystal Conclave mage from a line officer is the cutting
        # tongs, which only she carries.
        crystal_color_1=CRYSTAL_KIT[0],
        crystal_color_2=CRYSTAL_KIT[1],
        crystal_color_3=CRYSTAL_KIT[2],
        crystal_color_4=CRYSTAL_KIT[3],
    ),
    frame=-0.1,
    face=FaceStyle(
        eye_size=0.90,
        eye_width=1.06,
        eye_openness=0.86,
        eye_tilt=0.18,
        eye_corner=0.50,
        iris_size=1.04,
        brow_tilt=0.55,
        brow_weight=0.95,
        mouth_curve=-0.15,
        mouth_width=0.68,
        blush=0.0,
        # From one eyebrow down across the cheek, per the reference art. Stated
        # from the viewer's side, so 1 is the right of the picture.
        scar_side=1,
    ),
)

HARUTO = CharacterParams(
    skin_tone=SKIN,
    # Deep bottle-green rather than plain dark hair: rich and refined, the
    # noble "liked by nearly everyone in the room." Burnt copper-orange eyes,
    # sharp and hot against it, for the calculating undertone underneath the
    # charm.
    hair_color="#2f4a3c",
    hairstyle="short_layered",
    hair_length=0.30,
    eye_color="#c3672e",
    hair_knot=True,
    # Waiting on: an obi buckle to match the reference's sword furniture.
    outfit=Outfit(
        tunic_color="#454639",
        boot_color="#4a3c2e",
        undersleeve_color="#2a2a26",
        belt_color="#4b4239",
        trouser_color="#2b2b27",
        skirt_color=None,
        tunic_tucked=True,
        robe_color="#2b2b26",
        sleeve_drop=0.55,
        belt_scale=2.6,
        # Same tone as the kimono: the reference's hakama and robe read as one
        # dark fabric, and it is the pleats and the outline that separate the
        # two planes rather than a second colour. Stops well short of the
        # boots, which is what leaves the dark trouser leg showing the way the
        # reference does.
        hakama_color="#2b2b26",
        hakama_length=0.60,
        # See Satoko's `skirt_length_chibi` comment: same reasoning, applied
        # to the hakama's own chibi-end field.
        hakama_length_chibi=0.454,
    ),
    frame=0.7,
    face=FaceStyle(
        eye_size=0.88,
        eye_width=1.10,
        eye_tilt=0.20,
        eye_corner=0.60,
        iris_size=1.12,
        brow_tilt=0.30,
        # The practised charming smile, which is the one thing about him that has
        # to survive being shrunk.
        mouth_curve=0.35,
        mouth_width=0.78,
        blush=0.15,
    ),
)

KEIKO = CharacterParams(
    skin_tone=SKIN,
    # Deep plum-violet rather than plain dark brown, with dusty rose-violet
    # eyes: a near-monochrome look for a researcher who reads as consumed by
    # her own work, haunted by what her trust in it cost. Warm and dusty
    # rather than cool, which is what separates her from Reika below: the
    # same violet family, opposite temperature.
    hair_color="#5a3a52",
    hairstyle="long_traced",
    hair_length=0.55,
    eye_color="#a58a92",
    # Waiting on: an open lab coat at full length, and spectacles. The charcoal
    # is the researcher's robes the coat hangs over.
    outfit=Outfit(
        tunic_color="#3f3f3a",
        boot_color="#232323",
        undersleeve_color="#e8e9e6",
        belt_color="#33332f",
        skirt_color="#3a3a35",
        skirt_length=0.82,
        # See Satoko's `skirt_length_chibi` comment: same reasoning.
        skirt_length_chibi=0.552,
        coat_color="#eceded",
        coat_length=0.80,
    ),
    frame=-0.3,
    face=FaceStyle(
        eye_size=0.90,
        eye_width=1.05,
        eye_openness=0.82,
        eye_tilt=0.10,
        eye_corner=0.45,
        iris_size=1.02,
        brow_tilt=0.10,
        brow_weight=0.70,
        mouth_curve=0.20,
        mouth_width=0.70,
        glasses=True,
        blush=0.25,
    ),
)

KRISTA = CharacterParams(
    skin_tone="#f4d3b6",
    hair_color="#a9763f",
    hairstyle="long_traced",
    hair_length=0.42,
    eye_color="#6fb0ae",
    hair_tail=1.0,
    outfit=Outfit(
        tunic_color=UNIFORM,
        boot_color=UNIFORM_BOOTS,
        undersleeve_color=UNIFORM,
        belt_color=UNIFORM_BELT,
        trouser_color=UNIFORM,
        skirt_color=None,
        tunic_tucked=True,
        collar_color=UNIFORM,
        placket_color=UNIFORM_BELT,
        chest_pocket_color=UNIFORM,
        strap_color=UNIFORM_BELT,
        boot_shaft=1.0,
        # Same leather as the belt and the cross-body strap, so the goggles
        # read as part of the same kit rather than a separate accessory in
        # its own color.
        goggle_color=UNIFORM_BELT,
        # The crystal harness canon gives her (`character_designs.md`):
        # "several glowing mana crystals" on the belt. Same issued kit every
        # Wodensreich soldier in the cast wears (`CRYSTAL_KIT`); what marks
        # her specifically as Crystal Conclave rather than a line officer is
        # the tongs below, hers alone.
        crystal_color_1=CRYSTAL_KIT[0],
        crystal_color_2=CRYSTAL_KIT[1],
        crystal_color_3=CRYSTAL_KIT[2],
        crystal_color_4=CRYSTAL_KIT[3],
        crystal_tongs=True,
    ),
    frame=-0.2,
    face=FaceStyle(
        eye_size=1.02,
        eye_width=1.06,
        eye_openness=0.86,
        eye_tilt=0.05,
        eye_corner=0.50,
        iris_size=1.04,
        brow_tilt=-0.10,
        brow_weight=0.70,
        # The one bright face in a cast that otherwise skews heavy and
        # controlled, which the document calls a deliberate counterweight.
        mouth_curve=0.55,
        mouth_width=0.80,
        blush=0.5,
    ),
)

REIKA = CharacterParams(
    skin_tone="#f6dcc6",
    # Indigo-violet-black rather than plain black, with pale cool lilac-grey
    # eyes in place of a merely "dark" iris: serene and ethereal rather than
    # somber, matching a dogmatic, uncompromising priestess whose authority
    # comes from faith rather than warmth. Same violet family as Keiko above,
    # cool where hers is warm.
    hair_color="#2a2438",
    hairstyle="long_traced",
    hair_length=0.95,
    eye_color="#b7abc4",
    # Waiting on: a trailing outer robe and the jewelled headpiece.
    outfit=Outfit(
        tunic_color="#b8bcbc",
        boot_color="#3a3a38",
        undersleeve_color="#e8e7e7",
        belt_color="#8d9291",
        # The teal, which is the one thing about her that already reads from
        # across a room, was standing in as `skirt_color` before the hakama
        # existed as its own garment; it moves here rather than staying
        # duplicated on both.
        hakama_color="#4d9ca8",
        hakama_length=0.95,
        # See Satoko's `skirt_length_chibi` comment: same reasoning, applied
        # to the hakama's own chibi-end field. This is the one #103 was
        # originally about, so the chibi hem stays exactly where that pass
        # tuned it while the pull-back mechanism itself is gone.
        hakama_length_chibi=0.610,
        robe_color="#c6cac9",
        sleeve_drop=0.70,
        belt_scale=2.2,
    ),
    frame=-0.4,
    face=FaceStyle(
        eye_size=0.92,
        eye_width=1.06,
        eye_openness=0.86,
        eye_tilt=0.16,
        eye_corner=0.50,
        iris_size=1.04,
        brow_tilt=0.05,
        brow_weight=0.65,
        # Gentle and serene rather than cold, which the document says is a
        # deliberate departure from the original spec and was kept.
        mouth_curve=0.25,
        mouth_width=0.66,
        blush=0.20,
    ),
)

REINHARD = CharacterParams(
    skin_tone="#eccaa9",
    # Cool ash-blond rather than the warmer light-brown/dark-blond a
    # reference image landed on, and a pale storm-blue eye rather than a
    # generic gray-blue: restrained rather than loud, matching a controlled,
    # unreadable character who is not meant to visually announce himself.
    # Beard matched to the hair below, one tone rather than two.
    hair_color="#c2b58a",
    hairstyle="short_layered",
    hair_length=0.22,
    eye_color="#7fa0b3",
    beard_color="#c2b58a",
    beard_length=0.07,
    outfit=Outfit(
        tunic_color=UNIFORM,
        boot_color=UNIFORM_BOOTS,
        undersleeve_color=UNIFORM,
        belt_color=UNIFORM_BELT,
        trouser_color=UNIFORM,
        skirt_color=None,
        tunic_tucked=True,
        collar_color=UNIFORM,
        placket_color=UNIFORM_BELT,
        chest_pocket_color=UNIFORM,
        strap_color=UNIFORM_BELT,
        boot_shaft=1.0,
        # Rank in Woden's Ravens (`characters.md`), and the expedition's own
        # crystal cargo was his order: the issued kit belongs on him same as
        # any other Wodensreich soldier in the cast.
        crystal_color_1=CRYSTAL_KIT[0],
        crystal_color_2=CRYSTAL_KIT[1],
        crystal_color_3=CRYSTAL_KIT[2],
        crystal_color_4=CRYSTAL_KIT[3],
    ),
    frame=1.0,
    face=FaceStyle(
        eye_size=0.86,
        eye_width=1.08,
        eye_openness=0.88,
        eye_tilt=0.08,
        eye_corner=0.55,
        iris_size=1.05,
        brow_tilt=0.20,
        brow_weight=0.85,
        # The faint knowing expression: present, and small enough not to read as
        # a smile.
        mouth_curve=0.18,
        mouth_width=0.70,
        blush=0.0,
    ),
)

TENNO = CharacterParams(
    skin_tone=SKIN_WORN,
    # Full silver-white rather than a duller "graying" tone: regal even
    # diminished. Warm brown eyes carry the permanently apologetic read his
    # writeup calls for.
    hair_color="#c9c6c2",
    hairstyle="short_layered",
    hair_length=0.24,
    eye_color="#8a6a4a",
    # Waiting on: the uniform cut in khaki, and a cane, which is deferred with
    # the other props but is load-bearing for his pose.
    outfit=Outfit(
        tunic_color=KHAKI,
        boot_color="#5c4632",
        undersleeve_color=KHAKI,
        belt_color="#5b4432",
        trouser_color="#a3947c",
        skirt_color=None,
        tunic_tucked=True,
        collar_color=KHAKI,
        placket_color="#4b3a2a",
        chest_pocket_color=KHAKI,
        boot_shaft=0.55,
    ),
    frame=0.5,
    face=aged(
        FaceStyle(
            eye_size=0.88,
            eye_width=1.06,
            eye_tilt=0.02,
            eye_corner=0.60,
            iris_size=1.09,
            # Inner ends raised: the permanently apologetic expression the
            # document describes, which is the sorrow direction rather than the
            # stern one, and the one thing that separates him from Daizen at
            # tile size once both are grey.
            brow_tilt=-0.35,
            brow_weight=0.75,
            mouth_curve=-0.15,
            mouth_width=0.66,
            blush=0.0,
        )
    ),
)

VIKTOR = CharacterParams(
    skin_tone="#f0cfb2",
    # Deep slate-teal rather than plain dark hair, against warm gold eyes:
    # cool and moody on the surface, warmer and sharper underneath than he
    # lets on, which is exactly his written trait, clocking the same thread
    # as Reinhard and not bothering to chase it.
    hair_color="#3c5c66",
    hairstyle="short_layered",
    hair_length=0.20,
    eye_color="#c9a24a",
    # Lieutenant, Woden's Ravens (`characters.md`): the same issued kit as
    # the rest of the cast's Wodensreich soldiers.
    outfit=Outfit(
        tunic_color=UNIFORM,
        boot_color=UNIFORM_BOOTS,
        undersleeve_color=UNIFORM,
        belt_color=UNIFORM_BELT,
        trouser_color=UNIFORM,
        skirt_color=None,
        tunic_tucked=True,
        collar_color=UNIFORM,
        placket_color=UNIFORM_BELT,
        chest_pocket_color=UNIFORM,
        strap_color=UNIFORM_BELT,
        boot_shaft=1.0,
        crystal_color_1=CRYSTAL_KIT[0],
        crystal_color_2=CRYSTAL_KIT[1],
        crystal_color_3=CRYSTAL_KIT[2],
        crystal_color_4=CRYSTAL_KIT[3],
    ),
    frame=0.8,
    face=FaceStyle(
        eye_size=0.88,
        eye_width=1.10,
        eye_openness=0.84,
        eye_tilt=0.14,
        eye_corner=0.58,
        iris_size=1.03,
        brow_tilt=0.15,
        brow_weight=0.75,
        # The relaxed half-smile: he coasts, and it should show.
        mouth_curve=0.40,
        mouth_width=0.72,
        blush=0.15,
    ),
)

# Katherina Beaumont, protagonist of ../time_slider_katharina (working title
# "The Shifted Hours"), a separate book from Valley of Mist's own cast above.
# Dark purple hair and amber eyes are canon from the book's own Ch1 prose
# (`../time_slider_katharina/docs/continuity_reference.md`); the amber-flecks
# detail described there (a mark near the left pupil, not a uniform iris
# tone) has no field to carry it here, so the base iris colour alone stands
# in for it. Hair worn tied back (`hair_tail`) per the same chapter's "hair
# coming loose from whatever I'd tied it back with hours ago"; `hair_knot`
# was the other candidate for that line but reads closer to a topknot than a
# ponytail, and a working academic's practical tie is closer to the intent.
# Outfit reaches for "prestigious magic academy," not folk-witch: a dark,
# tailored coat over a plain tunic and skirt, gold trim standing in for
# academic rank rather than embroidery or a pointed hat (no hat shape exists
# in this tool yet; deliberately left off rather than faked with a headscarf,
# see that repo's own design notes on the cover work this preset is for).
KATHERINA = CharacterParams(
    skin_tone="#f2c9a8",
    hair_color="#4b2c5e",
    hairstyle="long_traced",
    hair_length=0.55,
    hair_tail=0.7,
    eye_color="#c98a3e",
    outfit=Outfit(
        tunic_color="#2b2438",
        skirt_color="#241f30",
        boot_color="#1a1a1a",
        belt_color="#3a3226",
        collar_color="#c9a13b",
        coat_color="#1b1f33",
        coat_length=0.62,
        sleeve_long=True,
    ),
    frame=-0.1,
    face=FaceStyle(
        eye_size=1.05,
        eye_width=1.02,
        eye_openness=0.90,
        iris_size=1.10,
        # A level, appraising brow rather than a friendly one: the character
        # reads people as problems to be assessed, not company to be warmed
        # to (`../time_slider_katharina/docs/characters.md`).
        brow_tilt=-0.05,
        brow_weight=0.68,
        mouth_curve=0.10,
        mouth_width=0.68,
        blush=0.1,
    ),
)

PRESETS: dict[str, CharacterParams] = {
    "katherina": KATHERINA,
    "satoko": SATOKO,
    "satoshi": SATOSHI,
    "kyoko": KYOKO,
    "tomohiro": TOMOHIRO,
    "chiyo": CHIYO,
    "daizen": DAIZEN,
    "elara": ELARA,
    "haruto": HARUTO,
    "keiko": KEIKO,
    "krista": KRISTA,
    "reika": REIKA,
    "reinhard": REINHARD,
    "tenno": TENNO,
    "viktor": VIKTOR,
}

# What a character is called on a sheet, where the preset key is not it: the
# reference sheets label "Reinhard von Falkenrath" and "Elara Sturm" while the
# key stays short enough to type at a CLI.
#
# A plain mapping rather than a field on `CharacterParams`, because this is
# presentation metadata in the same category as `REALISTIC_REFS` and not part of
# who a character is. It also keeps a name out of every preset constructor.
DISPLAY_NAMES: dict[str, str] = {
    "katherina": "Katherina Beaumont",
    "satoko": "Satoko",
    "satoshi": "Satoshi",
    "kyoko": "Kyoko",
    "tomohiro": "Tomohiro",
    "chiyo": "Chiyo",
    "daizen": "Daizen Kurogane",
    "elara": "Elara Sturm",
    "haruto": "Haruto Kisaragi",
    "keiko": "Keiko Natsume",
    "krista": "Krista Bastler",
    "reika": "Reika Mizuki",
    "reinhard": "Reinhard von Falkenrath",
    "tenno": "Tenno Amatsuki",
    # The sheets spell him "Viktor Grau" while the reference file is
    # `ref/victor.png`. The design document flags the spelling and keeps the
    # filename, so we do the same: the character is Viktor, and renaming a
    # checked-in reference to match would be the more disruptive half of the fix.
    "viktor": "Viktor Grau",
}

# Who appears on a sheet, in the order they appear.
#
# The four personas lead because they are the two characters the rest of the
# cast is drawn to match, and the others follow alphabetically, which is an
# order rather than a ranking.
ROSTERS: dict[str, tuple[str, ...]] = {
    "cast": (
        "satoko",
        "satoshi",
        "kyoko",
        "tomohiro",
        "chiyo",
        "daizen",
        "elara",
        "haruto",
        "keiko",
        "krista",
        "reika",
        "reinhard",
        "tenno",
        "viktor",
    ),
}
# The other of the two reference rosters: Satoshi's persona rather than
# Satoko's, so Tomohiro stays and Satoko and Kyoko drop, the owner's call on
# 2026-08-09. Derived from `cast` rather than listed a second time, since
# `cast` and `satoshi` share ten members and a second hand-written tuple is
# exactly the thing that drifts the day a fifteenth character is added to one
# list and not the other. `sorted()` gives the same alphabetical order `cast`
# already uses for everyone after its four leads.
ROSTERS["satoshi"] = (
    "satoshi",
    *sorted(n for n in ROSTERS["cast"] if n not in ("satoshi", "satoko", "kyoko")),
)

# Which characters get a realistic-build render checked into `ref-out/real/`.
#
# The owner's call on 2026-08-08 was to defer the build entirely: "the real
# ones don't work so well so I suggest we defer them, the chibis are where the
# music is at." So the chibi became the build this project publishes, and the
# tall figures moved to a subdirectory that says what they are, down to just
# Satoko and Satoshi, the two ever measured against a reference
# (`ref/satoko-real.jpg`, `ref/satoshi-real.jpg`).
#
# Reopened on 2026-08-11: the owner asked for every named character's
# realistic render in `ref-out/real/`, not only the pair with a reference to
# judge against. `tuple(PRESETS)` rather than a second hand-written list, the
# same reasoning `ROSTERS["satoshi"]` already uses for not repeating `cast`:
# a name typed twice is a name that drifts, and a new preset already lands in
# `ref-out/` at chibi with no second step, so the realistic build should not
# need one either.
#
# This is still a **publishing** decision and lives on its own rather than as
# a field on `CharacterParams`, which is about who a character is. Nothing
# stops `--build realistic` on any preset, and `BUILDS` is untouched: the
# build itself was never deferred, only which renders of it were checked in.
REALISTIC_REFS: tuple[str, ...] = tuple(PRESETS)


# ---------------------------------------------------------------------------
# Neutral bases, for the web tool rather than the novel.
#
# `docs/web-gui-plan.md` settles on three kinds of starting point: the named
# cast above, and a neutral male and female base for a visitor who wants to
# make a character of their own rather than recolour Krista. These are that
# pair, and they stay out of `PRESETS`, `DISPLAY_NAMES` and `ROSTERS` on
# purpose: that dict is the fourteen named characters and nothing else, the
# README table and `ref-out/` are keyed off it, and a base has no design to
# publish there, only defaults to hand a visitor.
#
# Undyed, unscarred, no beard, no accessories, and coloured with
# `CharacterParams`' and `Outfit`'s own stock defaults rather than a palette
# invented for this document: the point of a base is that nothing about it has
# been decided yet, and the first thing the web tool's colour controls do is
# override every one of these anyway. What the two differ on is silhouette,
# because that is the one choice a colour picker cannot make: a skirt or
# trousers, and a haircut to match. `BASE_FEMALE` changes nothing from
# `CharacterParams()`'s own defaults, which already draw the skirted silhouette
# `Outfit` was built around; `BASE_MALE` swaps in trousers and `short_crop`,
# at 0.65, the length the cut was traced at (see `SATOSHI`, which carries the
# same value for the same reason).
BASE_FEMALE = CharacterParams()

BASE_MALE = CharacterParams(
    hairstyle="short_crop",
    hair_length=0.65,
    outfit=Outfit(
        skirt_color=None,
        trouser_color="#4f7a52",
    ),
)

# Keyed by the same short lowercase names the web catalogue will use, per the
# plan's "male base" and "female base". A separate dict rather than folded
# into `PRESETS`, for the reason given above.
NEUTRAL_BASES: dict[str, CharacterParams] = {
    "female": BASE_FEMALE,
    "male": BASE_MALE,
}

# Named expressions, checked in for the same reason a character is: a mood that
# worked once should be reusable rather than re-derived from four numbers
# someone half remembers. Each is a delta, so any of these goes on any
# character without touching what their face *is*; see `Expression`.
#
# These came out of choosing a face for the cover of "The Hero of the Mist
# Tragedy" on 2026-08-08, judged both as head crops and at thumbnail size. The
# finding worth keeping is that **the brow is the weak lever**: brow-only moods
# shift under 1% of the face at either size, while anything touching
# `eye_openness` shifts two to three times that, because a brow is a thin
# stroke and a lid is the edge of a filled shape. A mood that has to survive
# being shrunk moves a lid.
EXPRESSIONS: dict[str, Expression] = {
    # Brows down, mouth turned. Reads as anger rather than sorrow, which makes
    # it a fighting face: right for a confrontation, wrong for a tragedy.
    "stern": Expression(brow_tilt=0.55, mouth_curve=-0.25),
    # The same further, with the mouth set small. Same caveat, more of it.
    "grim": Expression(brow_tilt=0.75, mouth_curve=-0.45, mouth_width=0.62),
    # Worn out rather than angry, and the strongest of these at any size. This
    # is the cover's, chosen 2026-08-08: "this cost him something" is what the
    # title promises, and the lid is what still says it at thumbnail size.
    # It does spend some of the wide-eyed look that reads as *him*, which is
    # the trade it makes.
    "hollow": Expression(eye_openness=0.66, brow_tilt=0.30, mouth_curve=-0.20),
    # Inner brow ends **raised**, the opposite direction to stern. Grief stated
    # rather than implied.
    "sorrow": Expression(brow_tilt=-0.40, mouth_curve=-0.30, eye_openness=0.82),
    # Brows down over a wide-open eye. Reads closer to alarm than to resolve,
    # kept because that is worth knowing before anyone tries the combination
    # again.
    "resolute": Expression(brow_tilt=0.50, mouth_curve=0.0, eye_openness=1.0, mouth_width=0.80),
}
