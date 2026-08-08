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
        # the iris and the face read startled. Chosen by eye.
        iris_size=0.72,
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
        iris_size=0.72,
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


def _before(base: CharacterParams) -> CharacterParams:
    """The same person before the dye and the burn."""
    return replace(
        base,
        hair_color=BLACK_HAIR,
        hair_tip_color=None,
        face=replace(base.face, scar_side=0),
    )


KYOKO = _before(SATOKO)
TOMOHIRO = _before(SATOSHI)

PRESETS: dict[str, CharacterParams] = {
    "satoko": SATOKO,
    "satoshi": SATOSHI,
    "kyoko": KYOKO,
    "tomohiro": TOMOHIRO,
}

# Which characters get a realistic-build render checked into `ref-out/real/`.
#
# The owner's call on 2026-08-08: "the real ones don't work so well so I suggest
# we defer them, the chibis are where the music is at." So the chibi is the
# build this project publishes, and the tall figures move to a subdirectory that
# says what they are. The pair below are the two that were measured against
# `ref/satoko-real.jpg` and `ref/satoshi-real.jpg`, so they are the only ones
# whose realistic render was ever judged against anything.
#
# This is a **publishing** decision and it lives on its own rather than as a
# field on `CharacterParams`, which is about who a character is. Nothing stops
# `--build realistic` on any preset, and `BUILDS` is untouched: the direction of
# the project is still to edge toward less deformed proportions, so the build
# stays available and only the checked-in artifacts shrink.
REALISTIC_REFS: tuple[str, ...] = ("satoko", "satoshi")


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
