"""Named characters.

A preset is just a CharacterParams, so a character is a checked-in artifact
that gets re-rendered as the shape code improves, rather than a pile of CLI
flags someone has to remember.
"""

from __future__ import annotations

from character import CharacterParams, FaceStyle, Outfit

# Satoko and Satoshi are meant to read as related, so the palette they share
# lives here once rather than being duplicated per character. What tells them
# apart is the haircut, the lower body, and the frame, not the colors.
HAIR = "#e6b53c"
HAIR_TIPS = "#eceae3"
TUNIC = "#4a6845"
UNDERSLEEVE = "#ab9e86"
BELT = "#5f4f42"
BOOTS = "#6d4c33"

# Satoko: blonde fading to white at the ends, muted green eyes, green
# working tunic, brown leather boots. Colors sampled from ref/satoko.png.
# Guarded expression: half-lidded eyes, thin level-to-stern brows, no smile,
# scar on her left cheek.
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
        skirt_length=0.70,
    ),
    # Slightly the narrower-shouldered of the two. Only bites at taller builds.
    frame=-0.3,
    face=FaceStyle(
        eye_size=0.95,
        eye_width=1.10,
        eye_openness=0.68,
        eye_lower_lid=0.85,
        eye_tilt=0.22,
        eye_corner=0.70,
        brow_tilt=0.35,
        brow_weight=0.75,
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
    hairstyle="short_layered",
    # Within the short cut's own range, so this is locks reaching down toward the
    # jaw rather than anything measured against the body. Shorter than this and
    # the side locks stop at the cheekbone and read as sideburns; much longer and
    # they pass the jaw and the cut starts reading as a bob.
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
        eye_width=1.12,
        eye_openness=0.74,
        eye_lower_lid=0.82,
        eye_tilt=0.16,
        eye_corner=0.72,
        brow_tilt=0.20,
        brow_weight=0.70,
        mouth_curve=0.0,
        mouth_width=0.70,
        blush=0.0,
    ),
)

PRESETS: dict[str, CharacterParams] = {
    "satoko": SATOKO,
    "satoshi": SATOSHI,
}
