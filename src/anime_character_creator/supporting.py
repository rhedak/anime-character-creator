"""Supporting characters: people a story needs once and the web tool does not.

Kept apart from `PRESETS` on purpose, the owner's call of 2026-10-09: the web
tool offers `sorted(PRESETS)` as its starting points and there are enough of them.
These are drawn the same way as every preset, with the same generator, and are
rendered by name from here (`SUPPORTING["kenzo"]`); they are simply not offered.

Each is a first draft built from what the book says of them, judged by eye, and
none of it is more than the text gives: no reference exists, so nothing here is
traced from one. The book's own descriptions are in
`valley_of_mist/books/book1_hero_of_the_mist_tragedy/docs/continuity_reference.md`.
"""

from __future__ import annotations

from .character import CharacterParams, FaceStyle, Outfit
from .presets import MAN_LASH

# Kenzo: the old man at the inn's window table, "weathered the color of the oak sill",
# who calls the village by its old name in a voice pitched to carry. An Okiri survivor,
# so the village's own plain dress, not the occupiers'. The oldest face the generator
# draws (`face_age=2.0`, as Daizen and Tenno), narrowed and level: the flat, unhopeful
# attention he saves for bad weather. Thin white hair, a short grey beard, a faded blue
# long-sleeved tunic, a little shorter than the grown men from a lifetime of stooping.
KENZO = CharacterParams(
    face_age=2.0,
    skin_tone="#c79f7a",
    hair_color="#cfcbc2",
    hairstyle="short_layered",
    hair_length=0.15,
    eye_color="#5b4632",
    beard_color="#b8b4aa",
    beard_length=0.10,
    outfit=Outfit(
        tunic_color="#56677a",
        undersleeve_color="#a79a82",
        belt_color="#4a3c2c",
        boot_color="#4e3d2c",
        trouser_color="#4a4640",
        skirt_color=None,
        tunic_tucked=True,
        sleeve_long=True,
    ),
    frame=0.2,
    chest=1.0,
    height=0.96,
    face=FaceStyle(
        lash=MAN_LASH,
        eye_size=0.86,
        eye_width=1.05,
        eye_tilt=0.05,
        eye_corner=0.55,
        iris_size=1.0,
        brow_tilt=0.25,
        brow_weight=0.9,
        mouth_curve=-0.1,
        mouth_width=0.66,
        blush=0.0,
    ),
)

# Dieter: the Wodensreich district clerk, "thin and perpetually damp about the collar",
# who resents his posting and copies ledgers he does not write. The occupiers' cooler
# steel tones (`docs/character_designs.md`), a plain grey-blue tunic with no rank on it,
# a narrow frame, a pale and tired face with the mouth turned down.
DIETER = CharacterParams(
    face_age=1.0,
    skin_tone="#ecd2bf",
    hair_color="#6a5a48",
    hairstyle="short_crop",
    hair_length=0.5,
    eye_color="#6b7a86",
    outfit=Outfit(
        tunic_color="#4c5660",
        undersleeve_color="#9aa3aa",
        belt_color="#2f2b28",
        boot_color="#241f1d",
        trouser_color="#34383e",
        skirt_color=None,
        tunic_tucked=True,
        sleeve_long=True,
    ),
    frame=0.1,
    chest=0.8,
    height=1.02,
    face=FaceStyle(
        lash=MAN_LASH,
        eye_size=0.9,
        eye_width=1.0,
        eye_openness=0.9,
        brow_tilt=0.15,
        brow_weight=0.9,
        mouth_curve=-0.2,
        mouth_width=0.7,
        blush=0.0,
    ),
)

# The cart driver: one of the men waiting out the checkpoint delay, unnamed, "more startled
# than offended". Broad and weather-browned, a plain brown work tunic, nothing about him
# says soldier, which is the point of the panel he is in.
DRIVER = CharacterParams(
    face_age=1.0,
    skin_tone="#d6a47b",
    hair_color="#5a4630",
    hairstyle="short_layered",
    hair_length=0.3,
    eye_color="#4b3a2a",
    outfit=Outfit(
        tunic_color="#7b5b3c",
        undersleeve_color="#c0ad8b",
        belt_color="#463828",
        boot_color="#3d2f22",
        trouser_color="#4b4036",
        skirt_color=None,
        tunic_tucked=True,
        sleeve_long=True,
    ),
    frame=1.0,
    chest=1.0,
    height=1.05,
    face=FaceStyle(lash=MAN_LASH, eye_size=0.95, brow_weight=1.0, mouth_width=0.8, blush=0.0),
)

SUPPORTING: dict[str, CharacterParams] = {
    "kenzo": KENZO,
    "dieter": DIETER,
    "driver": DRIVER,
}

DISPLAY_NAMES: dict[str, str] = {
    "kenzo": "Kenzo",
    "dieter": "Dieter",
    "driver": "Cart driver",
}
