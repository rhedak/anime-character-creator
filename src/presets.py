"""Named characters.

A preset is just a CharacterParams, so a character is a checked-in artifact
that gets re-rendered as the shape code improves, rather than a pile of CLI
flags someone has to remember.
"""

from __future__ import annotations

from character import CharacterParams

# Satoko: blonde fading to white at the ends, muted green eyes, green
# working tunic, brown leather boots. Colors sampled from ref-local/satoko.png.
SATOKO = CharacterParams(
    skin_tone="#f6dbc2",
    hair_color="#e6b53c",
    hair_tip_color="#eceae3",
    eye_color="#74905e",
    outfit_color="#4a6845",
    boot_color="#6d4c33",
)

PRESETS: dict[str, CharacterParams] = {
    "satoko": SATOKO,
}
