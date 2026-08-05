"""Named characters.

A preset is just a CharacterParams, so a character is a checked-in artifact
that gets re-rendered as the shape code improves, rather than a pile of CLI
flags someone has to remember.
"""

from __future__ import annotations

from character import CharacterParams, FaceStyle

# Satoko: blonde fading to white at the ends, muted green eyes, green
# working tunic, brown leather boots. Colors sampled from ref-local/satoko.png.
# Guarded expression: half-lidded eyes, thin level-to-stern brows, no smile,
# scar on her left cheek.
SATOKO = CharacterParams(
    skin_tone="#f6dbc2",
    hair_color="#e6b53c",
    hair_tip_color="#eceae3",
    eye_color="#74905e",
    outfit_color="#4a6845",
    boot_color="#6d4c33",
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

PRESETS: dict[str, CharacterParams] = {
    "satoko": SATOKO,
}
