"""Assembles a character from flat vector shapes anchored to a
Skeleton. Every shape is plain SVG (paths, circles, capsule-strokes) so
recoloring is just swapping a fill/stroke attribute and the whole figure
scales as one unit via the skeleton's head_r.
"""

from __future__ import annotations

import math

from collections.abc import Callable
from dataclasses import dataclass, field

from colorutil import shade
from skeleton import DEFAULT_HEADS, Skeleton, build_skeleton

OUTLINE = "#2b2b2b"
STROKE_W = 3


@dataclass(frozen=True)
class FaceStyle:
    """Expression knobs. Every default reproduces the stock chibi face, so a
    character only states what it differs on."""

    eye_size: float = 1.0
    # Aperture width against its height. Below 1 gives a tall eye, above 1 a
    # long narrow one.
    eye_width: float = 0.88
    # How high the upper lid rides. 1.0 is wide open, lower is half-lidded.
    # The iris keeps its size and gets cropped, which is what reads as lidded
    # rather than simply small-eyed.
    eye_openness: float = 1.0
    # How far the lower lid drops. Below 1 flattens the underside.
    eye_lower_lid: float = 1.0
    # Raises the outer corner above the inner one.
    eye_tilt: float = 0.10
    # 0 is a rounded oval, 1 pulls all four corners out to sharp points.
    eye_corner: float = 0.35
    # Iris against the aperture's smaller half-axis. Below 1 leaves white
    # sclera showing all the way around it.
    iris_size: float = 0.72
    # 0 is level. Positive drops the inner ends (stern), negative raises them.
    brow_tilt: float = 0.0
    brow_weight: float = 1.0
    # 1.0 is the stock smile, 0 is a flat line, negative frowns.
    mouth_curve: float = 1.0
    mouth_width: float = 1.0
    blush: float = 1.0
    # -1 scars the left cheek, 1 the right, 0 none.
    scar_side: int = 0


@dataclass(frozen=True)
class Outfit:
    """What the character wears, one field per garment.

    A garment is present when its color is set, so a character states only the
    layers it has rather than carrying a flag per piece, and the parts that draw
    absent garments return nothing. Colors default to the plain tunic-and-skirt
    the generator started with; the layered values live on the presets.
    """

    tunic_color: str = "#4f7a52"
    boot_color: str = "#5b4632"
    # Long sleeve worn under the tunic's short one. None leaves the arm bare.
    undersleeve_color: str | None = None
    belt_color: str | None = None
    # Front panel hanging from the belt, over the skirt.
    apron_color: str | None = None
    skirt_color: str | None = "#4f7a52"
    # A second, longer skirt under the first, so its hem shows below the other's.
    underskirt_color: str | None = None
    # Trousers instead of a skirt. Fills the legs, which are otherwise bare skin.
    trouser_color: str | None = None
    # Skirt hem, measured hip (0) to ankle (1), the way hair_length is measured
    # chin to hip, so one garment keeps its length across builds. None takes the
    # skeleton's own hem anchor, which is where a hem sits when nobody asks for
    # anything in particular.
    skirt_length: float | None = None


@dataclass(frozen=True)
class CharacterParams:
    skin_tone: str = "#f2c9a1"
    hair_color: str = "#e8b84b"
    # Tone the hair fades into below the jaw. None means single-tone hair.
    hair_tip_color: str | None = None
    # Where the hair ends, measured chin (0) to hip (1), so it stays the same
    # haircut across builds. Roughly: 0.15 jaw, 0.45 chest, 1.0 hip.
    hair_length: float = 0.45
    # Which haircut, by name from HAIRSTYLES.
    hairstyle: str = "long_blunt"
    eye_color: str = "#4a9c6d"
    outfit: Outfit = field(default_factory=Outfit)
    face: FaceStyle = field(default_factory=FaceStyle)
    # Head-heights tall. Ignored when render_character is handed a skeleton.
    heads: float = DEFAULT_HEADS
    # Shoulder against hip: -1 narrow-shouldered and wide-hipped, 0 neutral, +1
    # the other way. Only bites at taller builds. Ignored when handed a skeleton.
    frame: float = 0.0
    shaded: bool = True


def _capsule(x1: float, y1: float, x2: float, y2: float, width: float, color: str) -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="{width:.1f}" stroke-linecap="round" />'
    )


Point = tuple[float, float]
Segment = tuple[Point, Point]


def _head_units(cx: float, cy: float, r: float, pt: Point) -> str:
    """Map a point given in head-radius units (origin = head center) to
    absolute canvas coordinates."""
    return f"{cx + pt[0] * r:.1f} {cy + pt[1] * r:.1f}"


def _curve(cx: float, cy: float, r: float, start: Point, segments: list[Segment], close: bool = True) -> str:
    """Build a path 'd' from a start point plus quadratic segments, all in
    head-radius units. Keeping the shapes as point data rather than format
    strings means a silhouette can be reshaped without rewriting SVG."""
    d = ["M " + _head_units(cx, cy, r, start)]
    for ctrl, end in segments:
        d.append("Q " + _head_units(cx, cy, r, ctrl) + " " + _head_units(cx, cy, r, end))
    if close:
        d.append("Z")
    return " ".join(d)


# Hair is described in two zones. Above the cheek line it is pinned to the
# skull, so those points are literal head-radius units. Below it the shape is
# a fall whose points are given as a fraction of the way to the tips, so
# `hair_length` restyles the whole thing without touching the crown, and the
# hair keeps its relationship to the body when proportions change.
_HAIR_CHEEK_Y = 0.72
_HAIR_TIP_CLIP_ID = "hair-tips"


def _fall(f: float, length: float) -> float:
    return _HAIR_CHEEK_Y + f * (length - _HAIR_CHEEK_Y)


def _mirror(start: Point, segments: list[Segment]) -> tuple[Point, list[Segment]]:
    def flip(q: Point) -> Point:
        return (-q[0], q[1])

    return flip(start), [(flip(c), flip(e)) for c, e in segments]


def _reverse(start: Point, segments: list[Segment]) -> tuple[Point, list[Segment]]:
    """Walk a quadratic chain backwards. Reversing a quadratic is just
    swapping its endpoints and keeping the control point, so this is exact
    and the two directions trace the same pixels."""
    anchors = [start] + [end for _, end in segments]
    controls = [ctrl for ctrl, _ in segments]
    return anchors[-1], [(controls[i], anchors[i]) for i in range(len(controls) - 1, -1, -1)]


def _fall_edge(length: float) -> tuple[Point, list[Segment]]:
    """The mass's outer edge on the right side, tip up to the cheek. Both the
    mass and the front lock are built from this, so their edges coincide
    exactly: where the mass shows, the two strokes land on each other, and
    where the body covers it, the lock's stroke carries the silhouette on."""

    def y(f: float) -> float:
        return _fall(f, length)

    return (1.06, y(1.00)), [
        ((1.29, y(0.93)), (1.28, y(0.76))),
        ((1.26, y(0.41)), (1.19, _HAIR_CHEEK_Y)),
    ]


def _hair_mass_shape(length: float) -> tuple[Point, list[Segment]]:
    """Crown, flaring out past the cheeks, then a straight fall to blunt tips
    that flick outward. This one shape carries the hair's only outer contour."""

    def y(f: float) -> float:
        return _fall(f, length)

    return (-1.02, -0.30), [
        ((-0.86, -1.26), (0.00, -1.20)),
        ((0.86, -1.26), (1.02, -0.30)),
        ((1.20, 0.20), (1.19, _HAIR_CHEEK_Y)),
        ((1.26, y(0.41)), (1.28, y(0.76))),
        ((1.29, y(0.93)), (1.06, y(1.00))),
        ((0.55, y(1.10)), (0.00, y(1.08))),
        ((-0.55, y(1.10)), (-1.06, y(1.00))),
        ((-1.29, y(0.93)), (-1.28, y(0.76))),
        ((-1.26, y(0.41)), (-1.19, _HAIR_CHEEK_Y)),
        ((-1.20, 0.20), (-1.02, -0.30)),
    ]


def _hair_tip_edge(length: float) -> tuple[Point, list[Segment]]:
    """Where hair fades to its tip tone. Only the part crossing the two side
    falls is ever visible, the rest sits behind the head and body, but the
    edge is waved along its whole length so the transition never reads as a
    ruled line. Closes into a region covering everything below the wave."""

    def y(f: float) -> float:
        return _fall(f, length)

    floor = length + 1.5
    return (-1.90, y(0.07)), [
        ((-1.55, y(0.00)), (-1.30, y(0.12))),
        ((-1.12, y(0.21)), (-0.95, y(0.10))),
        ((-0.78, y(0.00)), (-0.55, y(0.17))),
        ((-0.28, y(0.32)), (0.00, y(0.24))),
        ((0.28, y(0.32)), (0.55, y(0.17))),
        ((0.78, y(0.00)), (0.95, y(0.10))),
        ((1.12, y(0.21)), (1.30, y(0.12))),
        ((1.55, y(0.00)), (1.90, y(0.07))),
        ((1.90, floor * 0.6), (1.90, floor)),
        ((0.00, floor), (-1.90, floor)),
    ]


def _hairline_shape(length: float) -> tuple[Point, list[Segment], list[Segment]]:
    """The hairline: up one lock in front of the cheek, across the fringe to
    the parting at the crown, then back down the other side. This is the only
    line drawn inside the mass, which is what lets front and back hair read as
    a single object. Both ends land exactly on the mass's own tips, where the
    silhouette stroke takes over, so the line never stops in mid-air.

    The second list closes the fringe's fill back to the start. It stays just
    inside the mass the whole way, so the two fills overlap rather than butt
    together, and outside the head circle, so the skull outline never shows
    through the hair.
    """

    def y(f: float) -> float:
        return _fall(f, length)

    start: Point = (-1.06, y(1.00))
    line: list[Segment] = [
        ((-1.00, y(0.97)), (-0.94, y(0.85))),
        ((-0.88, y(0.60)), (-0.88, y(0.28))),
        ((-0.92, 0.70), (-0.88, 0.35)),
        ((-0.86, -0.26), (-0.40, -0.72)),
        ((-0.16, -0.88), (0.00, -0.94)),
        ((0.16, -0.88), (0.40, -0.72)),
        ((0.86, -0.26), (0.88, 0.35)),
        ((0.92, 0.70), (0.88, y(0.28))),
        ((0.88, y(0.60)), (0.94, y(0.85))),
        ((1.00, y(0.97)), (1.06, y(1.00))),
    ]
    # Down the fall the fringe's outer edge is the mass's own edge, so the
    # lock can carry the silhouette where the body hides the mass. Above the
    # cheek it tucks inside instead, which is what keeps the temple seamless.
    _, right_edge = _fall_edge(length)
    _, left_down = _reverse(*_mirror(*_fall_edge(length)))
    back: list[Segment] = [
        *right_edge,
        ((1.09, 0.10), (1.00, -0.30)),
        ((0.84, -1.20), (0.00, -1.14)),
        ((-0.84, -1.20), (-1.00, -0.30)),
        ((-1.09, 0.10), (-1.19, _HAIR_CHEEK_Y)),
        *left_down,
    ]
    return start, line, back


def _short_mass_shape(tip: float) -> tuple[Point, list[Segment]]:
    """A short layered cut: the skull, side locks coming down in front of the
    ears to ragged points, and the nape tucked up behind the jaw.

    Its points are placed straight off `tip` instead of going through `_fall`,
    which measures a long fall down from the cheek line and so cannot describe
    hair that ends above the chin at all.
    """
    return (-1.00, -0.34), [
        ((-0.88, -1.26), (0.00, -1.20)),
        ((0.88, -1.26), (1.00, -0.34)),
        ((1.08, 0.02), (1.03, tip - 0.20)),
        ((1.05, tip + 0.04), (0.84, tip)),
        ((0.68, tip - 0.16), (0.46, tip + 0.02)),
        ((0.24, tip - 0.22), (0.00, tip - 0.08)),
        ((-0.24, tip - 0.22), (-0.46, tip + 0.02)),
        ((-0.68, tip - 0.16), (-0.84, tip)),
        ((-1.05, tip + 0.04), (-1.03, tip - 0.20)),
        ((-1.08, 0.02), (-1.00, -0.34)),
    ]


def _short_fall_edge(tip: float) -> tuple[Point, list[Segment]]:
    """The side lock's outer edge, tip up to the temple. Traces the mass's own
    outer edge in reverse, exactly, for the same reason `_fall_edge` does."""
    return (0.84, tip), [
        ((1.05, tip + 0.04), (1.03, tip - 0.20)),
        ((1.08, 0.02), (1.00, -0.34)),
    ]


def _short_tip_edge(tip: float) -> tuple[Point, list[Segment]]:
    """Where a short cut fades to its tip tone: across the bottom third of the
    locks, measured up from the tips.

    Measuring from the tips is the whole point. The long style's boundary sits a
    fixed fraction of the way down a fall that starts at the cheek line, and on
    hair this short that puts the pale tone at the jaw, where it reads as a
    collar rather than as hair going white at the ends.
    """
    hi, lo = tip - 0.40, tip - 0.26
    floor = tip + 1.5
    return (-1.90, hi), [
        ((-1.58, lo), (-1.30, hi)),
        ((-1.05, lo), (-0.80, hi)),
        ((-0.42, lo), (0.00, hi)),
        ((0.42, lo), (0.80, hi)),
        ((1.05, lo), (1.30, hi)),
        ((1.58, lo), (1.90, hi)),
        ((1.90, floor * 0.6), (1.90, floor)),
        ((0.00, floor), (-1.90, floor)),
    ]


def _short_hairline_shape(tip: float) -> tuple[Point, list[Segment], list[Segment]]:
    """The short cut's fringe: up one side lock, across a fringe that stops just
    above the brows, and down the other. Both ends land on the mass's own tips,
    same contract as the long style's hairline. The fringe's two halves are not
    mirror images, which is what gives it a sweep without the asymmetry having to
    reach the silhouette."""
    start: Point = (-0.84, tip)
    line: list[Segment] = [
        ((-0.94, tip - 0.18), (-0.92, tip - 0.38)),
        ((-0.88, 0.10), (-0.82, -0.22)),
        ((-0.66, -0.48), (-0.30, -0.56)),
        ((-0.08, -0.62), (0.16, -0.52)),
        ((0.48, -0.40), (0.82, -0.22)),
        ((0.88, 0.10), (0.92, tip - 0.38)),
        ((0.94, tip - 0.18), (0.84, tip)),
    ]
    _, right_edge = _short_fall_edge(tip)
    _, left_down = _reverse(*_mirror(*_short_fall_edge(tip)))
    back: list[Segment] = [
        *right_edge,
        ((0.84, -1.20), (0.00, -1.14)),
        ((-0.84, -1.20), (-1.00, -0.34)),
        *left_down,
    ]
    return start, line, back


@dataclass(frozen=True)
class Hairstyle:
    """One haircut, as the four outlines that have to agree with each other.

    The mass carries the entire outer contour; the fall edge is the stretch of it
    the front lock has to retrace exactly, so the two strokes land on each other
    where the mass shows and the lock carries the silhouette where the body hides
    it; the hairline is the only line drawn inside the mass; and the tip edge is
    where the two tones meet. Each takes the tip depth in head radii, which
    `_hair_fall` derives from the body-relative `hair_length`.
    """

    mass: Callable[[float], tuple[Point, list[Segment]]]
    hairline: Callable[[float], tuple[Point, list[Segment], list[Segment]]]
    fall_edge: Callable[[float], tuple[Point, list[Segment]]]
    tip_edge: Callable[[float], tuple[Point, list[Segment]]]
    # What hair_length 0 and 1 mean for this cut, as depth below the head centre
    # in head radii. None measures the body instead, chin to hip, which is what
    # keeps a long haircut the same haircut across builds.
    #
    # A cut that ends on the head needs its own range, because the body-relative
    # one cannot express anything above the chin: chin is its zero. It is also
    # the more correct unit for short hair, which is pinned to the skull and so
    # should not change length when the body gets longer.
    tip_range: tuple[float, float] | None = None


HAIRSTYLES: dict[str, Hairstyle] = {
    "long_blunt": Hairstyle(_hair_mass_shape, _hairline_shape, _fall_edge, _hair_tip_edge),
    "short_layered": Hairstyle(
        _short_mass_shape,
        _short_hairline_shape,
        _short_fall_edge,
        _short_tip_edge,
        # Ear to chin: a crop at 0, locks brushing the jaw at 1.
        tip_range=(0.42, 1.00),
    ),
}
DEFAULT_HAIRSTYLE = "long_blunt"


def _hair_fall(sk: Skeleton, p: CharacterParams) -> float:
    """How far below the head center the hair ends, in head radii, which is the
    unit the hair shapes are built in.

    Which range `hair_length` spans is the haircut's own business: a cut that
    falls past the chin is measured against the body, so it survives a change of
    build, and a cut that ends on the head is measured against the head. Doing
    the conversion in one place is what lets both kinds share one knob.
    """
    style = HAIRSTYLES[p.hairstyle]
    if style.tip_range is not None:
        lo, hi = style.tip_range
        return lo + p.hair_length * (hi - lo)
    chin_y = sk.head_cy + sk.head_r
    tip_y = chin_y + p.hair_length * (sk.hip_y - chin_y)
    return (tip_y - sk.head_cy) / sk.head_r


def _hair_tip_tone(p: CharacterParams) -> str | None:
    """The tone the hair fades into, or None when the hair is single-tone."""
    if p.hair_tip_color is None or p.hair_tip_color == p.hair_color:
        return None
    return p.hair_tip_color


def _hair_defs(sk: Skeleton, p: CharacterParams) -> str:
    if _hair_tip_tone(p) is None:
        return ""
    start, segments = HAIRSTYLES[p.hairstyle].tip_edge(_hair_fall(sk, p))
    d = _curve(sk.head_cx, sk.head_cy, sk.head_r, start, segments)
    return f'<defs><clipPath id="{_HAIR_TIP_CLIP_ID}"><path d="{d}" /></clipPath></defs>'


def _two_tone_hair(d: str, p: CharacterParams) -> list[str]:
    """Fill a hair shape, then repaint its lower part in the tip tone. Fill
    and outline are separate draws so the second fill can't cover the inner
    half of the outline stroke."""
    parts = [f'<path d="{d}" fill="{p.hair_color}" />']
    tips = _hair_tip_tone(p)
    if tips is not None:
        parts.append(f'<path d="{d}" fill="{tips}" clip-path="url(#{_HAIR_TIP_CLIP_ID})" />')
    return parts


def _hair_mass(sk: Skeleton, p: CharacterParams) -> str:
    start, segments = HAIRSTYLES[p.hairstyle].mass(_hair_fall(sk, p))
    d = _curve(sk.head_cx, sk.head_cy, sk.head_r, start, segments)
    parts = _two_tone_hair(d, p)
    parts.append(f'<path d="{d}" fill="none" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />')
    return "".join(parts)


def _neck(sk: Skeleton, p: CharacterParams) -> str:
    w = sk.neck_half_w * 2
    x = sk.head_cx - w / 2
    # Runs past the shoulder line so the tunic's V notch, which is drawn
    # over it, opens onto skin rather than onto the hair behind the body.
    h = sk.shoulder_y - sk.neck_y + sk.neck_half_w * 1.1
    rx = w * 0.35
    return f'<rect x="{x:.1f}" y="{sk.neck_y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{shade(p.skin_tone)}" />'


def _tunic(sk: Skeleton, p: CharacterParams) -> str:
    """The torso garment, shoulder to hip. Reads the waist anchor rather than
    running straight from shoulder to hem, which is what stops a tall build from
    coming out as a box: a chibi still widens all the way down, an adult takes in
    and back out."""
    cx = sk.head_cx
    sw, ww, hw = sk.shoulder_half_w, sk.waist_half_w, sk.hip_half_w
    sy, wy, hy = sk.shoulder_y, sk.waist_y, sk.hip_y
    notch = sk.neck_half_w * 0.8

    # Control points sit at the shoulder's own width and the hip's own width, so
    # the curve leaves each landmark vertically and the taper reads as a body
    # rather than as a cone.
    shoulder_ctrl_y = wy - (wy - sy) * 0.35
    hip_ctrl_y = hy - (hy - wy) * 0.45

    def down(s: int) -> str:
        return (
            f"Q {cx + s * sw:.1f} {shoulder_ctrl_y:.1f} {cx + s * ww:.1f} {wy:.1f} "
            f"Q {cx + s * hw:.1f} {hip_ctrl_y:.1f} {cx + s * hw:.1f} {hy:.1f} "
        )

    def up(s: int) -> str:
        return (
            f"Q {cx + s * hw:.1f} {hip_ctrl_y:.1f} {cx + s * ww:.1f} {wy:.1f} "
            f"Q {cx + s * sw:.1f} {shoulder_ctrl_y:.1f} {cx + s * sw:.1f} {sy:.1f} "
        )

    d = (
        f"M {cx - notch:.1f} {sy:.1f} "
        f"L {cx - sw:.1f} {sy:.1f} " + down(-1) + f"L {cx + hw:.1f} {hy:.1f} " + up(1) + f"L {cx + notch:.1f} {sy:.1f} "
        f"L {cx:.1f} {sy + notch:.1f} "
        f"Z"
    )
    fill = p.outfit.tunic_color
    shape = f'<path d="{d}" fill="{fill}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'
    if not p.shaded:
        return shape
    # One shadow down the far side of the torso, turning under at the waist.
    shadow = (
        f'<path d="M {cx + ww * 0.34:.1f} {sy:.1f} '
        f"Q {cx + sw * 0.9:.1f} {wy - (wy - sy) * 0.3:.1f} {cx + ww:.1f} {wy:.1f} "
        f"Q {cx + hw:.1f} {hy - (hy - wy) * 0.45:.1f} {cx + hw:.1f} {hy:.1f} "
        f"L {cx + ww * 0.34:.1f} {hy:.1f} Z\" "
        f'fill="{shade(fill)}" opacity="0.55" />'
    )
    return shape + shadow


def _skirt_half_w(sk: Skeleton, y: float) -> float:
    """Half-width of an A-line skirt at a given height. The flare angle comes
    from the skeleton's own hip and hem anchors, so a longer skirt flares
    further instead of needing a width of its own."""
    span = sk.hem_y - sk.hip_y
    if span <= 0:
        return sk.hip_half_w
    return sk.hip_half_w + (sk.hem_half_w - sk.hip_half_w) * (y - sk.hip_y) / span


def _skirt_hem_y(sk: Skeleton, length: float | None) -> float:
    """Where a skirt ends. `length` is measured hip (0) to ankle (1); None takes
    the skeleton's own hem anchor, which is where a hem sits when nobody asks
    for anything in particular.

    A requested length only fully applies at an adult build. The shorter the
    build, the further the hem is pulled back toward the skeleton's own hem: a
    chibi's legs are so short that a full-length skirt swallows them and the
    figure reads as a bell with no limbs, which is why chibi versions of a long
    garment are drawn shorter. Same reason the widths interpolate in the first
    place.
    """
    if length is None:
        return sk.hem_y
    asked = sk.hip_y + length * (sk.ankle_y - sk.hip_y)
    return sk.hem_y + (asked - sk.hem_y) * sk.build


def _skirt_corner_y(sk: Skeleton, hem_y: float) -> float:
    """Where a skirt's side stops running straight and starts turning under into
    its hem. Measured up from the hem in body units rather than as a fraction of
    the panel's own height, so two panels sharing a hem turn under together: a
    shadow band that rounded over a different span than the panel it sits on
    poked out past its side, which is how this got its own function."""
    return hem_y - (sk.ankle_y - sk.hip_y) * 0.07


def _skirt_path(sk: Skeleton, top_y: float, hem_y: float, top_w: float | None = None, hem_w: float | None = None) -> str:
    """An A-line skirt panel. Widths default to the flare the skeleton implies,
    but a layer underneath can pass its own: an underskirt that kept flaring past
    the hem above it would stick out sideways as a shelf rather than hanging."""
    cx = sk.head_cx
    top_w = _skirt_half_w(sk, top_y) if top_w is None else top_w
    hem_w = _skirt_half_w(sk, hem_y) if hem_w is None else hem_w
    corner = _skirt_corner_y(sk, hem_y)
    return (
        f"M {cx - top_w:.1f} {top_y:.1f} "
        f"L {cx - hem_w:.1f} {corner:.1f} "
        f"Q {cx - hem_w:.1f} {hem_y:.1f} {cx - hem_w * 0.6:.1f} {hem_y:.1f} "
        f"L {cx + hem_w * 0.6:.1f} {hem_y:.1f} "
        f"Q {cx + hem_w:.1f} {hem_y:.1f} {cx + hem_w:.1f} {corner:.1f} "
        f"L {cx + top_w:.1f} {top_y:.1f} "
        f"Z"
    )


# Where the other lower-body layers sit relative to the skirt's own hem, as a
# fraction of the hip-to-ankle span. Relative to the skirt rather than measured
# from the hip on their own, because a chibi's skirt is drawn shorter than asked
# for and measuring each layer independently would collapse them all onto the
# same hem: the underskirt has to keep showing below the skirt, and the apron has
# to keep stopping above it, at every build.
_UNDERSKIRT_DROP = 0.13
_APRON_LIFT = 0.26


def _underskirt(sk: Skeleton, p: CharacterParams) -> str:
    """A second skirt, longer than the one over it, so its hem shows as a band of
    a different tone below the other's."""
    color = p.outfit.underskirt_color
    if color is None:
        return ""
    skirt_hem = _skirt_hem_y(sk, p.outfit.skirt_length)
    hem_y = skirt_hem + (sk.ankle_y - sk.hip_y) * _UNDERSKIRT_DROP
    # Hangs straight below the skirt's own hem rather than continuing to flare,
    # and a shade narrower, so it reads as being under the other one.
    hem_w = _skirt_half_w(sk, skirt_hem) * 0.97
    d = _skirt_path(sk, sk.waist_y, hem_y, hem_w=hem_w)
    shape = f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'
    if not p.shaded:
        return shape
    # Only the band below the skirt above it is ever visible, so the shading is
    # a single turn under the hem rather than the folds the outer skirt gets. It
    # has to follow the panel's own taper: drawn at the hem's width all the way
    # up, it hangs out past the sides as a shelf, which is exactly what it did.
    # Starting the band exactly where the panel turns under means it is the
    # panel's own hem cap, at the same width, so it cannot overhang.
    band_y = _skirt_corner_y(sk, hem_y)
    band = _skirt_path(sk, band_y, hem_y, top_w=hem_w, hem_w=hem_w)
    return shape + f'<path d="{band}" fill="{shade(color)}" opacity="0.7" />'


def _apron(sk: Skeleton, p: CharacterParams) -> str:
    """A front panel hanging from the belt over the skirt. Narrow enough to leave
    the hands clear on both sides, which is what fixes its width more than the
    reference does."""
    color = p.outfit.apron_color
    if color is None:
        return ""
    cx = sk.head_cx
    # Starts above the waist so the belt drawn over it covers the top edge.
    top_y = sk.waist_y - (sk.hip_y - sk.waist_y) * 0.40
    bot_y = _skirt_hem_y(sk, p.outfit.skirt_length) - (sk.ankle_y - sk.hip_y) * _APRON_LIFT
    top_w = sk.waist_half_w * 0.90
    # Flares only a little. Following the skirt's own flare down to a hem this
    # low turns the panel into a cone that swallows the garment under it, and the
    # reference's apron is a straight-hanging panel.
    bot_w = min(top_w * 1.12, _skirt_half_w(sk, bot_y) * 0.70)
    r = bot_w * 0.14
    d = (
        f"M {cx - top_w:.1f} {top_y:.1f} "
        f"L {cx - bot_w:.1f} {bot_y - r:.1f} "
        f"Q {cx - bot_w:.1f} {bot_y:.1f} {cx - bot_w + r:.1f} {bot_y:.1f} "
        f"L {cx + bot_w - r:.1f} {bot_y:.1f} "
        f"Q {cx + bot_w:.1f} {bot_y:.1f} {cx + bot_w:.1f} {bot_y - r:.1f} "
        f"L {cx + top_w:.1f} {top_y:.1f} "
        f"Z"
    )
    shape = f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'
    if not p.shaded:
        return shape
    shadow = (
        f'<path d="M {cx + top_w * 0.30:.1f} {top_y:.1f} L {cx + top_w:.1f} {top_y:.1f} '
        f"L {cx + bot_w:.1f} {bot_y - r:.1f} "
        f"Q {cx + bot_w:.1f} {bot_y:.1f} {cx + bot_w - r:.1f} {bot_y:.1f} "
        f'L {cx + bot_w * 0.34:.1f} {bot_y:.1f} Z" fill="{shade(color)}" opacity="0.5" />'
    )
    return shape + shadow


def _skirt(sk: Skeleton, p: CharacterParams) -> str:
    color = p.outfit.skirt_color
    if color is None:
        return ""
    hem_y = _skirt_hem_y(sk, p.outfit.skirt_length)
    # Starts above the hip so the tunic drawn over it has something to overlap
    # and the waistband never opens onto skin.
    top_y = sk.waist_y
    d = _skirt_path(sk, top_y, hem_y)
    shape = f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'
    if not p.shaded:
        return shape
    # Two folds, drawn as shadow wedges narrowing toward the waist, which is all
    # the drape a flat garment needs to stop reading as a cut-out.
    folds = []
    for s, at in ((-1, 0.52), (1, 0.30)):
        x0 = sk.head_cx + s * _skirt_half_w(sk, top_y) * at
        x1 = sk.head_cx + s * _skirt_half_w(sk, hem_y) * (at + 0.30)
        x2 = sk.head_cx + s * _skirt_half_w(sk, hem_y) * (at + 0.06)
        folds.append(
            f'<path d="M {x0:.1f} {top_y:.1f} L {x1:.1f} {hem_y:.1f} L {x2:.1f} {hem_y:.1f} Z" '
            f'fill="{shade(color)}" opacity="0.45" />'
        )
    return shape + "".join(folds)


def _arms(sk: Skeleton, p: CharacterParams) -> str:
    """Shoulder to hand, and the tunic's short sleeve over the top of it.

    The sleeve belongs to the tunic to look at, but it is drawn here because the
    arm has to sit under it while the hands have to sit over every garment: the
    apron is only just narrower than the arm span, and a clipped hand is the one
    collision that would show.

    Whatever the undersleeve is, it carries the arm's whole length. Against a
    green tunic a tan sleeve is what separates the arm from the torso; left bare,
    the arm is skin and does the same job.
    """
    width = sk.arm_half_w * 2
    y1 = sk.shoulder_y + sk.arm_half_w * 0.4
    y2 = sk.hip_y + sk.arm_half_w * 0.8
    sleeve = p.outfit.undersleeve_color or p.skin_tone
    cap_color = p.outfit.tunic_color
    # The short sleeve ends around mid-upper-arm, which on this skeleton is a
    # third of the way from the shoulder to the hand.
    cap_at = 0.34
    parts = []
    for side in (-1, 1):
        x1 = sk.head_cx + side * sk.arm_x
        x2 = sk.head_cx + side * (sk.arm_x + sk.arm_half_w * 0.35)
        parts.append(_capsule(x1, y1, x2, y2, width + STROKE_W * 2, OUTLINE))
        parts.append(_capsule(x1, y1, x2, y2, width, sleeve))
        if p.shaded:
            # Shadow down the inner half of the sleeve, so a bare arm and a
            # clothed one both turn away from the light the way the torso does.
            inner = x1 - side * sk.arm_half_w * 0.45
            parts.append(_capsule(inner, y1, inner + (x2 - x1), y2, width * 0.45, shade(sleeve)))
        hand_r = sk.arm_half_w * 0.9
        parts.append(
            f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="{hand_r:.1f}" fill="{p.skin_tone}" stroke="{OUTLINE}" stroke-width="2" />'
        )
        # Sleeve last, so it laps over the top of the arm the way a garment does.
        cx_end = x1 + (x2 - x1) * cap_at
        cy_end = y1 + (y2 - y1) * cap_at
        cap_w = width * 1.14
        parts.append(_capsule(x1, y1, cx_end, cy_end, cap_w + STROKE_W * 2, OUTLINE))
        parts.append(_capsule(x1, y1, cx_end, cy_end, cap_w, cap_color))
        if p.shaded:
            off = side * cap_w * 0.30
            parts.append(_capsule(x1 - off, y1, cx_end - off, cy_end, cap_w * 0.3, shade(cap_color)))
    return "".join(parts)


def _legs_and_boots(sk: Skeleton, p: CharacterParams) -> str:
    # A straight rectangle passes as a leg on a chibi and reads as a stick on
    # a tall build, so the leg tapers from thigh to ankle with a calf bulge.
    # How much it tapers rides on the build, via the skeleton's own widths.
    taper = sk.build
    # Trousers are the outermost garment on the leg, so unlike bare skin they
    # need their own outline, they start at the hip rather than under a hem, and
    # they carry a thigh: a shin-width tube running up to the hip reads as a
    # stilt once there is no skirt covering the top of it.
    trousers = p.outfit.trouser_color
    w_top = sk.leg_half_w * (1.55 if trousers else 1.0)
    w_knee = sk.leg_half_w * (0.95 - 0.17 * taper)
    w_ankle = sk.leg_half_w * (0.85 - 0.30 * taper)
    gap = sk.leg_half_w * 1.45
    # A bare leg has to start at or above whatever hem is going to cover its top,
    # and the skirt's hem moves with `skirt_length`. Pinning it to the skeleton's
    # own hem leaves a band of bare canvas across the hips as soon as a skirt is
    # asked to be shorter than that.
    top_y = sk.hip_y if trousers else min(sk.hem_y, _skirt_hem_y(sk, p.outfit.skirt_length)) - 4
    calf_y = sk.knee_y + (sk.ankle_y - sk.knee_y) * 0.35
    fill = trousers or p.skin_tone
    stroke = f' stroke="{OUTLINE}" stroke-width="{STROKE_W}"' if trousers else ""
    parts = []
    for side in (-1, 1):
        cx = sk.head_cx + side * gap
        d = (
            f"M {cx - w_top:.1f} {top_y:.1f} L {cx + w_top:.1f} {top_y:.1f} "
            f"Q {cx + w_top:.1f} {sk.knee_y - (sk.knee_y - top_y) * 0.3:.1f} {cx + w_knee:.1f} {sk.knee_y:.1f} "
            f"Q {cx + w_knee * 1.14:.1f} {calf_y:.1f} {cx + w_ankle:.1f} {sk.ankle_y:.1f} "
            f"L {cx - w_ankle:.1f} {sk.ankle_y:.1f} "
            f"Q {cx - w_knee * 1.14:.1f} {calf_y:.1f} {cx - w_knee:.1f} {sk.knee_y:.1f} "
            f"Q {cx - w_top:.1f} {sk.knee_y - (sk.knee_y - top_y) * 0.3:.1f} {cx - w_top:.1f} {top_y:.1f} Z"
        )
        parts.append(f'<path d="{d}" fill="{fill}"{stroke} />')
        if trousers and p.shaded:
            # Shadow down the inner side of each leg, which is what separates the
            # two of them when both are the same flat tone.
            inner = cx - side * w_knee * 0.55
            parts.append(_capsule(inner, sk.knee_y - (sk.knee_y - top_y) * 0.5, inner, sk.ankle_y, w_knee * 0.7, shade(fill)))
        parts.append(_boot(sk, p, cx, w_ankle, w_knee))
    return "".join(parts)


def _boot(sk: Skeleton, p: CharacterParams, cx: float, w_ankle: float, w_knee: float) -> str:
    """One boot: a shaft coming up over the ankle, flaring into the foot.

    A bare foot block reads as a brown lump at every build, which is what the
    single rectangle used to give. The shaft is what makes it a boot, so it is
    the one piece of detail worth having here; the laces are not, at either
    build."""
    color = p.outfit.boot_color
    boot_w = w_ankle * 3.4
    foot_h = sk.foot_y - sk.ankle_y
    # The shaft climbs a third of the way to the knee, so it stays a boot rather
    # than becoming a waders as the shin gets longer at taller builds.
    top_y = sk.ankle_y - (sk.ankle_y - sk.knee_y) * 0.32
    shaft_w = w_knee * 1.16
    instep_y = sk.ankle_y + foot_h * 0.30
    r = boot_w * 0.22
    d = (
        f"M {cx - shaft_w:.1f} {top_y:.1f} "
        f"L {cx - shaft_w:.1f} {sk.ankle_y:.1f} "
        f"Q {cx - boot_w / 2:.1f} {instep_y:.1f} {cx - boot_w / 2:.1f} {sk.foot_y - r:.1f} "
        f"Q {cx - boot_w / 2:.1f} {sk.foot_y:.1f} {cx - boot_w / 2 + r:.1f} {sk.foot_y:.1f} "
        f"L {cx + boot_w / 2 - r:.1f} {sk.foot_y:.1f} "
        f"Q {cx + boot_w / 2:.1f} {sk.foot_y:.1f} {cx + boot_w / 2:.1f} {sk.foot_y - r:.1f} "
        f"Q {cx + boot_w / 2:.1f} {instep_y:.1f} {cx + shaft_w:.1f} {sk.ankle_y:.1f} "
        f"L {cx + shaft_w:.1f} {top_y:.1f} "
        f"Z"
    )
    parts = [f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />']
    if not p.shaded:
        return "".join(parts)
    sole_h = foot_h * 0.24
    parts.append(
        f'<path d="M {cx - boot_w / 2:.1f} {sk.foot_y - sole_h:.1f} L {cx + boot_w / 2:.1f} {sk.foot_y - sole_h:.1f} '
        f"L {cx + boot_w / 2:.1f} {sk.foot_y - r:.1f} "
        f"Q {cx + boot_w / 2:.1f} {sk.foot_y:.1f} {cx + boot_w / 2 - r:.1f} {sk.foot_y:.1f} "
        f"L {cx - boot_w / 2 + r:.1f} {sk.foot_y:.1f} "
        f"Q {cx - boot_w / 2:.1f} {sk.foot_y:.1f} {cx - boot_w / 2:.1f} {sk.foot_y - r:.1f} "
        f'Z" fill="{shade(color, 0.7)}" />'
    )
    # Turned cuff at the top of the shaft, the one line that says "boot" rather
    # than "sock".
    parts.append(
        f'<line x1="{cx - shaft_w:.1f}" y1="{top_y + (sk.ankle_y - top_y) * 0.3:.1f}" '
        f'x2="{cx + shaft_w:.1f}" y2="{top_y + (sk.ankle_y - top_y) * 0.3:.1f}" '
        f'stroke="{shade(color, 0.7)}" stroke-width="{max(1.5, STROKE_W * 0.6):.1f}" />'
    )
    return "".join(parts)


def _belt(sk: Skeleton, p: CharacterParams) -> str:
    """A band at the waist. On a front view this is what actually makes a waist
    read, since the arms hang over the silhouette's own taper and hide it."""
    color = p.outfit.belt_color
    if color is None:
        return ""
    cx = sk.head_cx
    # Wraps over the tunic, so it is a shade wider than the body at the waist.
    half_w = sk.waist_half_w * 1.03
    h = (sk.hip_y - sk.waist_y) * 0.42
    y = sk.waist_y - h * 0.35
    parts = [
        f'<rect x="{cx - half_w:.1f}" y="{y:.1f}" width="{half_w * 2:.1f}" height="{h:.1f}" '
        f'rx="{h * 0.18:.1f}" fill="{color}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'
    ]
    if p.shaded:
        parts.append(
            f'<rect x="{cx - half_w:.1f}" y="{y + h * 0.62:.1f}" width="{half_w * 2:.1f}" height="{h * 0.38:.1f}" '
            f'rx="{h * 0.18:.1f}" fill="{shade(color)}" opacity="0.8" />'
        )
    return "".join(parts)


_HEAD_CLIP_ID = "head"
_HEAD_SEGMENTS = 8


def _head_shape(build: float) -> tuple[Point, list[Segment]]:
    """The skull: a circle at the chibi end, a jawed oval at the adult end.

    Eight quadratics that trace a unit circle when nothing tapers them, so the
    chibi keeps exactly the round head it always had, and the lower half narrows
    toward a chin as the build gets taller. A plain circle is fine at 2.4 heads
    and reads as a ball on a stick at 7, which is what this is for.

    The taper is confined to below the cheek line on purpose. The hair's crown and
    temple points are pinned to this shape in the same head-radius units, so
    narrowing the skull up there would leave the hairline floating off the face.
    """
    jaw_pull = 0.30 * build
    chin_drop = 0.05 * build
    # Control-point radius that makes a quadratic chain trace a circle.
    k = 1 / math.cos(math.pi / _HEAD_SEGMENTS)

    def pt(deg: float, radius: float) -> Point:
        th = math.radians(deg)
        x, y = math.sin(th) * radius, -math.cos(th) * radius
        if y > 0:
            lean = min(1.0, y)  # 0 at the cheek line, 1 at the chin
            x *= 1.0 - jaw_pull * lean * lean
            y *= 1.0 + chin_drop * lean
        return (x, y)

    step = 360 / _HEAD_SEGMENTS
    anchors = [pt(i * step, 1.0) for i in range(_HEAD_SEGMENTS)]
    controls = [pt((i + 0.5) * step, k) for i in range(_HEAD_SEGMENTS)]
    return anchors[0], [(controls[i], anchors[(i + 1) % _HEAD_SEGMENTS]) for i in range(_HEAD_SEGMENTS)]


def _head(sk: Skeleton, p: CharacterParams) -> str:
    start, segments = _head_shape(sk.build)
    d = _curve(sk.head_cx, sk.head_cy, sk.head_r, start, segments)
    shape = f'<path d="{d}" fill="{p.skin_tone}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'
    if not p.shaded:
        return shape
    # Clipped to the skull rather than described a second time, so the shadow
    # follows the jaw at every build without the jaw being written down twice.
    clip = f'<defs><clipPath id="{_HEAD_CLIP_ID}"><path d="{d}" /></clipPath></defs>'
    band = _curve(
        sk.head_cx,
        sk.head_cy,
        sk.head_r,
        (0.10, -1.20),
        [
            ((0.30, -0.40), (0.16, 0.30)),
            ((0.02, 0.85), (0.12, 1.25)),
            ((1.40, 1.25), (1.40, -1.20)),
        ],
    )
    shadow = (
        f'<path d="{band}" fill="{shade(p.skin_tone, 0.93)}" opacity="0.7" '
        f'clip-path="url(#{_HEAD_CLIP_ID})" />'
    )
    return clip + shape + shadow


def _eye_shape(ex: float, ey: float, er: float, side: int, f: FaceStyle) -> tuple[str, str]:
    """Eye aperture as a closed almond, plus its upper lid on its own so the
    lash line can be redrawn heavier over the iris.

    Four quadratics run inner corner, apex, outer corner, base, back to the
    inner corner. Each control point sits at the extreme of its half and is
    slid along x by `eye_corner`: sitting directly over a corner it gives an
    elliptical quarter and the corner reads round, pulled toward the middle
    the curve leaves the corner shallowly and reads pointed. Points are built
    with x measured outward from the face center, then mirrored per side.
    """
    w = er * f.eye_width
    top = er * f.eye_openness
    bot = er * f.eye_lower_lid
    tilt = er * f.eye_tilt * 0.30
    reach = 0.55 * f.eye_corner

    inner = (-w, tilt)
    apex = (w * 0.05, -top)
    outer = (w, -tilt)
    base = (-w * 0.10, bot)

    def pt(p: Point) -> str:
        return f"{ex + side * p[0]:.1f} {ey + p[1]:.1f}"

    def ctrl(corner: Point, toward: Point, y: float) -> Point:
        return (corner[0] + (toward[0] - corner[0]) * reach, y)

    lid = (
        f"M {pt(inner)} Q {pt(ctrl(inner, apex, -top))} {pt(apex)} "
        f"Q {pt(ctrl(outer, apex, -top))} {pt(outer)}"
    )
    d = lid + f" Q {pt(ctrl(outer, base, bot))} {pt(base)} Q {pt(ctrl(inner, base, bot))} {pt(inner)} Z"
    return d, lid


def _eye(ex: float, ey: float, er: float, side: int, p: CharacterParams) -> str:
    f = p.face
    d, lid = _eye_shape(ex, ey, er, side, f)
    clip_id = f"eye-{'l' if side < 0 else 'r'}"

    # Size the iris off whichever half-axis of the aperture is smaller, so a
    # narrow or half-lidded eye keeps white at its corners instead of filling
    # solid with color. Everything inside the eye is placed off the iris, and
    # the iris off the aperture's own center rather than a fixed offset.
    iris_r = f.iris_size * min(er * f.eye_width, er * (f.eye_openness + f.eye_lower_lid) / 2)
    iris_cy = ey + er * (f.eye_lower_lid - f.eye_openness) / 2 + iris_r * 0.08

    # Still clipped to the aperture, so a low lid crops the iris rather than
    # letting it hang over the lash line.
    parts = [f'<defs><clipPath id="{clip_id}"><path d="{d}" /></clipPath></defs>']
    parts.append(f'<path d="{d}" fill="white" stroke="{OUTLINE}" stroke-width="2.5" />')
    parts.append(f'<g clip-path="url(#{clip_id})">')
    parts.append(f'<circle cx="{ex:.1f}" cy="{iris_cy:.1f}" r="{iris_r:.1f}" fill="{p.eye_color}" />')
    parts.append(
        f'<circle cx="{ex:.1f}" cy="{iris_cy + iris_r * 0.14:.1f}" r="{iris_r * 0.45:.1f}" '
        f'fill="{shade(p.eye_color, 0.35)}" />'
    )
    parts.append(
        f'<circle cx="{ex - iris_r * 0.42:.1f}" cy="{iris_cy - iris_r * 0.48:.1f}" r="{iris_r * 0.34:.1f}" fill="white" />'
    )
    parts.append(
        f'<circle cx="{ex + iris_r * 0.35:.1f}" cy="{iris_cy + iris_r * 0.42:.1f}" r="{iris_r * 0.16:.1f}" '
        f'fill="white" opacity="0.85" />'
    )
    parts.append("</g>")
    # The upper lash line carries more weight than the rest of the outline.
    parts.append(f'<path d="{lid}" fill="none" stroke="{OUTLINE}" stroke-width="4" stroke-linecap="round" />')
    return "".join(parts)


def _scar(sk: Skeleton, side: int) -> str:
    """A nick with a short cross-tick on one cheek. One line alone reads as a
    stray stroke at this size; two equal lines read as a cartoon X, so the
    tick is kept short."""
    r, cx, cy = sk.head_r, sk.head_cx, sk.head_cy

    def line(x1: float, y1: float, x2: float, y2: float, w: float) -> str:
        return (
            f'<line x1="{cx + side * r * x1:.1f}" y1="{cy + r * y1:.1f}" '
            f'x2="{cx + side * r * x2:.1f}" y2="{cy + r * y2:.1f}" '
            f'stroke="{OUTLINE}" stroke-width="{w}" stroke-linecap="round" opacity="0.6" />'
        )

    return line(0.52, 0.56, 0.65, 0.35, 1.8) + line(0.55, 0.44, 0.63, 0.49, 1.4)


def _face(sk: Skeleton, p: CharacterParams) -> str:
    r = sk.head_r
    cx, cy = sk.head_cx, sk.head_cy
    f = p.face
    eye_y = cy + r * 0.08
    eye_dx = r * 0.42
    eye_r = r * 0.26 * f.eye_size
    parts = []

    for side in (-1, 1):
        ex = cx + side * eye_dx
        brow_y = eye_y - eye_r * 1.75
        tilt = f.brow_tilt * eye_r * 0.28
        parts.append(
            f'<line x1="{ex - side * eye_r * 0.9:.1f}" y1="{brow_y + tilt:.1f}" '
            f'x2="{ex + side * eye_r * 0.9:.1f}" y2="{brow_y - tilt:.1f}" '
            f'stroke="{OUTLINE}" stroke-width="{3 * f.brow_weight:.1f}" stroke-linecap="round" />'
        )
        parts.append(_eye(ex, eye_y, eye_r, side, p))

    mouth_y = cy + r * 0.55
    mouth_half = r * 0.12 * f.mouth_width
    parts.append(
        f'<path d="M {cx - mouth_half:.1f} {mouth_y:.1f} '
        f'Q {cx:.1f} {mouth_y + r * 0.08 * f.mouth_curve:.1f} {cx + mouth_half:.1f} {mouth_y:.1f}" '
        f'fill="none" stroke="{OUTLINE}" stroke-width="2.5" stroke-linecap="round" />'
    )

    if f.blush > 0:
        for side in (-1, 1):
            bx = cx + side * r * 0.55
            by = cy + r * 0.35
            parts.append(
                f'<ellipse cx="{bx:.1f}" cy="{by:.1f}" rx="{r * 0.16:.1f}" ry="{r * 0.09:.1f}" '
                f'fill="#e8879a" opacity="{0.45 * f.blush:.2f}" />'
            )

    if f.scar_side:
        parts.append(_scar(sk, 1 if f.scar_side > 0 else -1))

    return "".join(parts)


def _hair_front(sk: Skeleton, p: CharacterParams) -> str:
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r

    # Fringe and side locks are one shape in the same flat tone as the mass,
    # drawn without a stroke of its own. The only line added is the hairline,
    # so nothing divides the hair into separate pieces.
    style = HAIRSTYLES[p.hairstyle]
    fall = _hair_fall(sk, p)
    start, line, back = style.hairline(fall)
    fill_d = _curve(cx, cy, r, start, line + back)
    line_d = _curve(cx, cy, r, start, line, close=False)
    parts = _two_tone_hair(fill_d, p)
    parts.append(
        f'<path d="{line_d}" fill="none" stroke="{OUTLINE}" stroke-width="{STROKE_W}" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
    )
    # Outer edge of each lock. Redundant where the mass shows behind the body,
    # since it lands on the mass's own stroke, and the silhouette where it
    # doesn't.
    for side in (-1, 1):
        edge = style.fall_edge(fall)
        edge_start, edge_segments = edge if side > 0 else _mirror(*edge)
        edge_d = _curve(cx, cy, r, edge_start, edge_segments, close=False)
        parts.append(
            f'<path d="{edge_d}" fill="none" stroke="{OUTLINE}" stroke-width="{STROKE_W}" '
            f'stroke-linecap="round" />'
        )
    return "".join(parts)


def render_character(p: CharacterParams | None = None, sk: Skeleton | None = None) -> str:
    p = p or CharacterParams()
    sk = sk or build_skeleton(heads=p.heads, frame=p.frame)

    # Back to front. The legs go under the skirts so a hem covers the thigh, and
    # the arms go over every garment so nothing can clip a hand: the apron is
    # narrow enough to sit between them, but only just, and the hands are the
    # one place a collision would show.
    layers = [
        _hair_defs(sk, p),
        _hair_mass(sk, p),
        _neck(sk, p),
        _legs_and_boots(sk, p),
        _underskirt(sk, p),
        _skirt(sk, p),
        _tunic(sk, p),
        _apron(sk, p),
        _belt(sk, p),
        _arms(sk, p),
        _head(sk, p),
        _face(sk, p),
        _hair_front(sk, p),
    ]

    body = "\n  ".join(layer for layer in layers if layer)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sk.canvas_w:.0f}" height="{sk.canvas_h:.0f}" '
        f'viewBox="0 0 {sk.canvas_w:.0f} {sk.canvas_h:.0f}">\n'
        f'  <rect width="100%" height="100%" fill="white" />\n'
        f"  {body}\n"
        f"</svg>\n"
    )
