"""What the web tool is allowed to show, and nothing it has to guess.

`docs/web-gui-plan.md` calls for "a limited set of choices: pick a character,
change colours, and swap between the hairstyles and garments that already
exist", deliberately short of a full parameter editor. `CharacterParams` alone
cannot answer that: it is `dataclasses.fields()` away from FaceStyle's fourteen
floats and `shaded`, a killed behaviour with a live field still attached to
it, neither of which belong on a page for someone who has never opened a
terminal (see "Knobs that are traps" in that document). `heads` used to be in
that list too, as "a continuous slider over builds nobody has looked at"; it
is exposed now, but still never as that slider, only as `BUILD`'s two-option
choice between the named entries in `BUILDS`, which is the form the plan
document itself said would be acceptable.

So this module is the curated middle: a small, explicit list of which fields
are public, in which order, with which labels and ranges, built once here
against the real dataclasses so a rename anywhere it points at breaks a test
rather than silently drifting. It emits that list as JSON via `to_json()`,
written to `ref-out/catalogue.json` by `refresh-catalogue.sh` the same way
`refresh-ref-out.sh` writes the SVGs, so the web page's first paint and its
Pyodide-driven controls read one committed file rather than two descriptions
that can disagree.

**The web layer learns no geometry from this.** Every range below is a
number this project already looked at, on a rendered chibi, not the type's
full domain: see the note on `skirt_length` and `hakama_length` for the one
place that used to be false and no longer is.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields

from .character import EYESTYLES, HAIRSTYLES, CharacterParams, FaceStyle, Outfit
from .presets import DISPLAY_NAMES, NEUTRAL_BASES, PRESETS
from .skeleton import BUILDS


@dataclass(frozen=True)
class ColorField:
    field: str
    label: str
    # None if this color is always present (the tunic, the boots); a garment
    # with an optional color is off entirely when its value is None, which is
    # how `Outfit` already encodes "not worn" and why the web layer never
    # needs a separate presence flag.
    optional: bool = False


@dataclass(frozen=True)
class RangeField:
    field: str
    label: str
    lo: float
    hi: float


@dataclass(frozen=True)
class BoolField:
    field: str
    label: str


@dataclass(frozen=True)
class SelectField:
    field: str
    label: str
    # Value/label pairs, in display order. Value is whatever the real field
    # holds (an int, for `scar_side`), not a string re-encoding of it, so the
    # bridge never has to translate a selection back into the model's own
    # type.
    options: tuple[tuple[object, str], ...]


@dataclass(frozen=True)
class GarmentSlot:
    """One layer of `Outfit`: its color and whatever else travels with it.

    `ranges` and `bools` are the companion fields that only mean anything once
    the slot's color is set, `sleeve_drop` without a `robe_color` draws
    nothing, so the web layer only needs to show them when the slot is on.
    """

    id: str
    label: str
    color: ColorField
    ranges: tuple[RangeField, ...] = ()
    bools: tuple[BoolField, ...] = ()
    # A slot that only reads once another is already on: the pouches hang from
    # a belt, so offering them with no belt draws nothing and looks broken.
    requires: str | None = None


def _existing_fields(cls: type) -> frozenset[str]:
    return frozenset(f.name for f in fields(cls))


_OUTFIT_FIELDS = _existing_fields(Outfit)
_CHARACTER_FIELDS = _existing_fields(CharacterParams)
_FACE_FIELDS = _existing_fields(FaceStyle)


def _color(field: str, label: str, *, optional: bool = True) -> ColorField:
    assert field in _OUTFIT_FIELDS, f"Outfit has no field {field!r}"
    return ColorField(field, label, optional=optional)


def _range(field: str, label: str, lo: float, hi: float) -> RangeField:
    assert field in _OUTFIT_FIELDS, f"Outfit has no field {field!r}"
    return RangeField(field, label, lo, hi)


def _bool(field: str, label: str) -> BoolField:
    assert field in _OUTFIT_FIELDS, f"Outfit has no field {field!r}"
    return BoolField(field, label)


def _face_range(field: str, label: str, lo: float, hi: float) -> RangeField:
    assert field in _FACE_FIELDS, f"FaceStyle has no field {field!r}"
    return RangeField(field, label, lo, hi)


def _face_bool(field: str, label: str) -> BoolField:
    assert field in _FACE_FIELDS, f"FaceStyle has no field {field!r}"
    return BoolField(field, label)


def _face_select(field: str, label: str, options: tuple[tuple[object, str], ...]) -> SelectField:
    assert field in _FACE_FIELDS, f"FaceStyle has no field {field!r}"
    return SelectField(field, label, options)


def _char_select(field: str, label: str, options: tuple[tuple[object, str], ...]) -> SelectField:
    assert field in _CHARACTER_FIELDS, f"CharacterParams has no field {field!r}"
    return SelectField(field, label, options)


# Always worn, so no toggle: a character with `tunic_color=None` is not
# something the generator can draw. `TUNIC_TUCKED` rides with it because it
# only changes where the tunic's own hem sits.
TUNIC = GarmentSlot(
    "tunic",
    "Tunic",
    _color("tunic_color", "Tunic", optional=False),
    bools=(_bool("tunic_tucked", "Tucked in"),),
)
# Always worn, likewise. `boot_shaft` is 0 (ankle) to 1 (knee) across the
# whole cast, Tenno's 0.55 through the uniform's 1.0, so the full declared
# range is one that has actually been looked at.
BOOTS = GarmentSlot(
    "boots",
    "Boots",
    _color("boot_color", "Boots", optional=False),
    ranges=(_range("boot_shaft", "Boot height", 0.0, 1.0),),
)

# Optional layers. Each is off (draws nothing) until its color is set, which
# is `Outfit`'s own presence rule and the reason none of these need a separate
# on/off field.
UNDERSLEEVE = GarmentSlot(
    "undersleeve",
    "Undersleeves (long sleeves underneath)",
    _color("undersleeve_color", "Undersleeves (long sleeves underneath)"),
)
BELT = GarmentSlot(
    "belt",
    "Belt",
    _color("belt_color", "Belt"),
    # 1.0 (the default) through 2.8, Chiyo's obi and the tallest in the cast.
    # Capped a little above that rather than left open, since nothing wider has
    # been rendered and judged.
    ranges=(_range("belt_scale", "Belt height", 1.0, 3.0),),
)
APRON = GarmentSlot("apron", "Apron", _color("apron_color", "Apron"), requires="belt")
CRYSTAL_1 = GarmentSlot(
    "crystal_1",
    "Crystal (outer left)",
    _color("crystal_color_1", "Crystal (outer left)"),
    requires="belt",
)
CRYSTAL_2 = GarmentSlot(
    "crystal_2",
    "Crystal (inner left)",
    _color("crystal_color_2", "Crystal (inner left)"),
    requires="belt",
)
CRYSTAL_3 = GarmentSlot(
    "crystal_3",
    "Crystal (inner right)",
    _color("crystal_color_3", "Crystal (inner right)"),
    requires="belt",
)
CRYSTAL_4 = GarmentSlot(
    "crystal_4",
    "Crystal (outer right)",
    _color("crystal_color_4", "Crystal (outer right)"),
    bools=(_bool("crystal_tongs", "Handling tongs (a small clipped tool)"),),
    requires="belt",
)
SKIRT = GarmentSlot(
    "skirt",
    "Skirt",
    _color("skirt_color", "Skirt"),
    # Hip (0) to ankle (1), same measure `hair_length` uses chin to hip. Used
    # to be a knob that visibly did nothing at the chibi build: `_skirt_hem_y`
    # pulled a requested length back toward the skeleton's own hem so hard
    # that 0.60 and 0.95 landed within four pixels of each other, the finding
    # `harness/hem/pullback.py` recorded. That was fixed in `d9fb68d`, the
    # commit before this document's own baseline, flooring the pull-back at
    # half strength: the same two lengths are 16px apart on the published
    # chibi now (measured directly against `_skirt_hem_y` while building this
    # catalogue), which is what makes the full 0..1 range worth exposing
    # rather than the trap the plan warned about.
    ranges=(_range("skirt_length", "Skirt length", 0.0, 1.0),),
)
UNDERSKIRT = GarmentSlot(
    "underskirt",
    "Underskirt (a second, longer skirt underneath)",
    _color("underskirt_color", "Underskirt (a second, longer skirt underneath)"),
    requires="skirt",
)
TROUSER = GarmentSlot("trouser", "Trousers (Pants)", _color("trouser_color", "Trousers (Pants)"))
POUCH = GarmentSlot("pouch", "Pouch", _color("pouch_color", "Pouch"), requires="belt")
COLLAR = GarmentSlot("collar", "Collar", _color("collar_color", "Collar"))
PLACKET = GarmentSlot("placket", "Buttons", _color("placket_color", "Buttons"))
CHEST_POCKET = GarmentSlot(
    "chest_pocket", "Chest pocket", _color("chest_pocket_color", "Chest pocket")
)
STRAP = GarmentSlot(
    "strap", "Strap (cross-body strap)", _color("strap_color", "Strap (cross-body strap)")
)
ROBE = GarmentSlot(
    "robe",
    "Robe (open outer layer, kimono-style)",
    _color("robe_color", "Robe (open outer layer, kimono-style)"),
    # Shoulder (0) to hip (1). The cast spans 0.44 (Tomohiro's jacket) to 0.70
    # (Reika's), and the docstring states the endpoints as meaningful rather
    # than merely legal, so the full range is exposed.
    ranges=(_range("sleeve_drop", "Sleeve drop", 0.0, 1.0),),
)
HAKAMA = GarmentSlot(
    "hakama",
    "Hakama (wide pleated trousers/skirt)",
    _color("hakama_color", "Hakama (wide pleated trousers/skirt)"),
    # Same hip-to-ankle measure as `skirt_length`, and the same fix applies.
    ranges=(_range("hakama_length", "Hakama length", 0.0, 1.0),),
)
HEADSCARF = GarmentSlot("headscarf", "Headscarf", _color("headscarf_color", "Headscarf"))
GOGGLES = GarmentSlot("goggles", "Goggles", _color("goggle_color", "Goggles"))
COAT = GarmentSlot(
    "coat",
    "Coat",
    _color("coat_color", "Coat"),
    # The docstring's own three named lengths run 0.30 to 0.75; the cast's
    # widest span is Tomohiro's 0.44 to Keiko's 0.80, so the range is bounded a
    # little past both rather than left at the type's full domain.
    ranges=(_range("coat_length", "Coat length", 0.30, 0.85),),
)

# Order here is display order: the two always-worn layers first, then
# everything else in the rough order a figure is dressed, innermost to
# outermost. Not alphabetical, because "add and remove garment slots" reads
# better as an outfit than as a word list.
GARMENTS: tuple[GarmentSlot, ...] = (
    TUNIC,
    BOOTS,
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
    COLLAR,
    PLACKET,
    CHEST_POCKET,
    STRAP,
    HAKAMA,
    ROBE,
    COAT,
    HEADSCARF,
    GOGGLES,
)


def _outfit_fields_named() -> frozenset[str]:
    """Every `Outfit` field name reachable from `GARMENTS`, so a field added to
    `Outfit` and forgotten here shows up as a set difference rather than a
    silent gap in the web tool."""
    out: set[str] = set()
    for g in GARMENTS:
        out.add(g.color.field)
        out.update(r.field for r in g.ranges)
        out.update(b.field for b in g.bools)
    return frozenset(out)


assert _outfit_fields_named() == _OUTFIT_FIELDS, (
    f"GARMENTS and Outfit have drifted apart: "
    f"missing {_OUTFIT_FIELDS - _outfit_fields_named()}, "
    f"extra {_outfit_fields_named() - _OUTFIT_FIELDS}"
)

# The named builds, `heads` under the hood but never the continuous slider
# `docs/web-gui-plan.md`'s "Knobs that are traps" warns against: only the
# two entries in `BUILDS` have ever been rendered and judged, so the control
# offers exactly those two rather than the type's full domain. Chibi is the
# default (`CharacterParams.heads`'s own default), same as everywhere else
# in this tool; realistic was deliberately left off the web tool on
# 2026-08-10 while its face read noticeably worse than the chibi's, which
# the eye, mouth and nose passes since then (`STATUS.md`) were aimed at
# closing. Reopened here on the strength of that work, not by re-litigating
# the original call, which stands as a record of why it was off rather than
# as a reason to leave it off now.
BUILD = _char_select(
    "heads", "Build", ((BUILDS["chibi"], "Chibi"), (BUILDS["realistic"], "Realistic"))
)

# Character-level colors, the ones every figure has regardless of what it
# wears. `hair_tip_color` is optional the same way a garment is: unset means
# single-tone hair.
COLORS: tuple[ColorField, ...] = (
    ColorField("skin_tone", "Skin", optional=False),
    ColorField("hair_color", "Hair", optional=False),
    ColorField("hair_tip_color", "Tip colour", optional=True),
    ColorField("eye_color", "Eyes", optional=False),
)
for _c in COLORS:
    assert _c.field in _CHARACTER_FIELDS, f"CharacterParams has no field {_c.field!r}"

# Chin (0) to hip (1), the same measure documented on `CharacterParams`.
# Every haircut maps its own end of this range to where it actually falls
# (`_hair_fall`), so 0..1 is meaningful for all five rather than only some.
HAIR_LENGTH = RangeField("hair_length", "Hair length", 0.0, 1.0)
assert HAIR_LENGTH.field in _CHARACTER_FIELDS

# A gathered tail and a crown knot: both drawn over any cut (`_hair_tail`,
# `_hair_knot`), not part of `Hairstyle` itself, and both already carried by a
# real preset (Krista's tail, Daizen's and Haruto's knots) but never exposed
# here before now. Shoulder (0) to hip (1), same as `HAIR_LENGTH`'s own scale.
HAIR_TAIL = RangeField("hair_tail", "Tail (ponytail/braid)", 0.0, 1.0)
assert HAIR_TAIL.field in _CHARACTER_FIELDS
HAIR_KNOT = BoolField("hair_knot", "Top-knot")
assert HAIR_KNOT.field in _CHARACTER_FIELDS

# `HAIRSTYLES` is the real registry; this only checks it still has the five
# keys the cast currently uses; sorted so a new cut appears in one place, here
# and in `HAIRSTYLES` itself, and needs no companion edit.
HAIRSTYLE_LABELS: dict[str, str] = {
    "long_blunt": "Long, blunt",
    "short_layered": "Short, layered",
    "long_traced": "Long",
    "short_crop": "Short crop",
    "short_tousled": "Short, tousled",
    "long_center_part": "Long, center part",
}
assert set(HAIRSTYLE_LABELS) == set(HAIRSTYLES), (
    "HAIRSTYLE_LABELS and HAIRSTYLES have drifted apart; a cut was added or "
    "removed on one side without the other"
)

# `FaceStyle` carries fourteen floats, and `docs/web-gui-plan.md` calls the
# whole set "a mixing desk, not a limited set of choices" and keeps it out of
# the catalogue entirely. What follows is a deliberately smaller, curated
# subset: the fields that read as "what shape are the eyes and mouth" and
# "is there a scar", not the ones that read as "what mood is this face making
# right now" (`brow_tilt`, `mouth_curve`, `blush`, ...) or duplicate what a
# preset already states at rest (`eye_openness`, `eye_lower_lid`,
# `brow_weight`).
# Bounds are the min and max actually used across the fourteen presets (see
# `presets.py`), the same "rendered and judged" rule `skirt_length` and
# `coat_length` already follow above, widened by a small margin so the
# default chibi face sits inside every range rather than at its edge.
# `mouth_width`'s default (1.0, `BASE_FEMALE`/`BASE_MALE`'s own value) sits
# above every named preset's own 0.66-0.80, which is why its own high end
# is 1.05 rather than a margin over the cast alone.
#
# `eye_corner` reads differently at the two builds now that `_eye_placement`
# doubles it at the realistic one (`STATUS.md`, 2026-08-12): this range's own
# top of 0.65 becomes an effective 1.3 there. Checked directly rather than
# derated for it, since the "malformed combinations are the visitor's own
# responsibility" call in `docs/web-gui-plan.md` already covers a sharper
# corner than either reference draws: 0.65 at the realistic build renders a
# sharp but intact corner, not a self-intersecting one, at both ends of every
# other range here too.
FACE_RANGES: tuple[RangeField, ...] = (
    _face_range("eye_size", "Eye size", 0.80, 1.05),
    _face_range("eye_width", "Eye width (round to narrow)", 0.85, 1.10),
    _face_range("eye_tilt", "Eye tilt", 0.0, 0.20),
    _face_range("eye_corner", "Eye corner (round to sharp)", 0.30, 0.65),
    _face_range("iris_size", "Iris size", 0.60, 0.80),
    _face_range("mouth_width", "Mouth width", 0.60, 1.05),
)
for _fr in FACE_RANGES:
    assert _fr.field in _FACE_FIELDS

FACE_BOOLS: tuple[BoolField, ...] = (_face_bool("glasses", "Glasses"),)
for _fb in FACE_BOOLS:
    assert _fb.field in _FACE_FIELDS

# Stated from the viewer's side, matching `FaceStyle.scar_side`'s own
# docstring: "Right cheek" here is the viewer's right, the character's left.
FACE_SCAR: SelectField = _face_select(
    "scar_side", "Scar", ((0, "None"), (-1, "Left cheek"), (1, "Right cheek"))
)

# Which of `EYESTYLES` draws the eye, exposed the way the plan's "swap
# between the hairstyles that already exist" treats hairstyles: the two
# styles are already in the generator, this just lets a visitor pick. Values
# come from `EYESTYLES` itself, keyed as a plain dict the way `HAIRSTYLES`
# keys hairstyles, so a third style added there shows up here with no second
# list to keep in step.
FACE_EYE_STYLE: SelectField = _face_select(
    "eye_style", "Eye style", tuple((name, name.capitalize()) for name in EYESTYLES)
)

FACE_SELECTS: tuple[SelectField, ...] = (FACE_EYE_STYLE, FACE_SCAR)
for _fs in FACE_SELECTS:
    assert _fs.field in _FACE_FIELDS


@dataclass(frozen=True)
class StartingPoint:
    id: str
    label: str


def _cast_points() -> tuple[StartingPoint, ...]:
    return tuple(StartingPoint(name, DISPLAY_NAMES[name]) for name in sorted(PRESETS))


def _base_points() -> tuple[StartingPoint, ...]:
    labels = {"female": "Female base", "male": "Male base"}
    return tuple(StartingPoint(name, labels[name]) for name in sorted(NEUTRAL_BASES))


def _color_json(c: ColorField) -> dict[str, object]:
    return {"field": c.field, "label": c.label, "optional": c.optional}


def _range_json(r: RangeField) -> dict[str, object]:
    return {"field": r.field, "label": r.label, "min": r.lo, "max": r.hi}


def _bool_json(b: BoolField) -> dict[str, object]:
    return {"field": b.field, "label": b.label}


def _select_json(s: SelectField) -> dict[str, object]:
    return {
        "field": s.field,
        "label": s.label,
        "options": [{"value": v, "label": lbl} for v, lbl in s.options],
    }


def _garment_json(g: GarmentSlot) -> dict[str, object]:
    out: dict[str, object] = {
        "id": g.id,
        "label": g.label,
        "color": _color_json(g.color),
    }
    if g.ranges:
        out["ranges"] = [_range_json(r) for r in g.ranges]
    if g.bools:
        out["bools"] = [_bool_json(b) for b in g.bools]
    if g.requires is not None:
        out["requires"] = g.requires
    return out


def build_catalogue() -> dict[str, object]:
    """The whole public surface, as plain JSON-able data.

    No coordinate, no head-radius fraction, nothing derived from a `Skeleton`:
    only field names, labels and the ranges that have actually been rendered
    and judged. A visitor's browser turns this into controls without ever
    knowing what the fields mean; only `render_character` does.
    """
    return {
        "starting_points": {
            "cast": [{"id": s.id, "label": s.label} for s in _cast_points()],
            "bases": [{"id": s.id, "label": s.label} for s in _base_points()],
        },
        "build": _select_json(BUILD),
        "colors": [_color_json(c) for c in COLORS],
        "hairstyles": [
            {"id": name, "label": HAIRSTYLE_LABELS[name]} for name in sorted(HAIRSTYLES)
        ],
        "hair_length": _range_json(HAIR_LENGTH),
        "hair_tail": _range_json(HAIR_TAIL),
        "hair_knot": _bool_json(HAIR_KNOT),
        "garments": [_garment_json(g) for g in GARMENTS],
        "face": {
            "ranges": [_range_json(r) for r in FACE_RANGES],
            "bools": [_bool_json(b) for b in FACE_BOOLS],
            "selects": [_select_json(s) for s in FACE_SELECTS],
        },
    }


def to_json() -> str:
    """The committed form: stable key order, trailing newline, diffable."""
    return json.dumps(build_catalogue(), indent=2, sort_keys=False) + "\n"


if __name__ == "__main__":
    import sys

    sys.stdout.write(to_json())
