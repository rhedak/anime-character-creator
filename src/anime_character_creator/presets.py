"""Named characters.

A preset is just a CharacterParams, so a character is a checked-in artifact
that gets re-rendered as the shape code improves, rather than a pile of CLI
flags someone has to remember.
"""

from __future__ import annotations

from .character import CharacterParams, FaceStyle, Outfit

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
# which keeps chibi eyes big and open even on a wary character. Scar on her
# left cheek.
SATOKO = CharacterParams(
    skin_tone="#f6dbc2",
    hair_color=HAIR,
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
# differs is a short layered cut, trousers instead of skirt and apron, and a
# face that carries no scar. Colors sampled from ref/satoshi.png.
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
    ),
)

PRESETS: dict[str, CharacterParams] = {
    "satoko": SATOKO,
    "satoshi": SATOSHI,
}
