"""Assembles a chibi character from flat vector shapes anchored to a
Skeleton. Every shape is plain SVG (paths, circles, capsule-strokes) so
recoloring is just swapping a fill/stroke attribute and the whole figure
scales as one unit via the skeleton's head_r.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from colorutil import shade
from skeleton import Skeleton, build_skeleton

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
class CharacterParams:
    skin_tone: str = "#f2c9a1"
    hair_color: str = "#e8b84b"
    # Tone the hair fades into below the jaw. None means single-tone hair.
    hair_tip_color: str | None = None
    eye_color: str = "#4a9c6d"
    outfit_color: str = "#4f7a52"
    boot_color: str = "#5b4632"
    face: FaceStyle = field(default_factory=FaceStyle)
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


# The whole hair silhouette: crown, flaring out past the cheeks, then a
# straight shoulder-length fall to blunt tips that flick outward. This one
# shape carries the only outer contour the hair has.
_HAIR_MASS_START: Point = (-1.02, -0.30)
_HAIR_MASS: list[Segment] = [
    ((-0.86, -1.26), (0.00, -1.20)),
    ((0.86, -1.26), (1.02, -0.30)),
    ((1.20, 0.20), (1.19, 0.72)),
    ((1.26, 1.20), (1.28, 1.62)),
    ((1.29, 1.82), (1.06, 1.90)),
    ((0.55, 1.99), (0.00, 1.97)),
    ((-0.55, 1.99), (-1.06, 1.90)),
    ((-1.29, 1.82), (-1.28, 1.62)),
    ((-1.26, 1.20), (-1.19, 0.72)),
    ((-1.20, 0.20), (-1.02, -0.30)),
]

# Where hair fades to its tip tone. Only the part crossing the two side
# falls is ever visible, the rest sits behind the head and body, but the
# edge is waved along its whole length so the transition never reads as a
# ruled line. Closes into a region covering everything below the wave.
_HAIR_TIP_EDGE_START: Point = (-1.90, 0.80)
_HAIR_TIP_EDGE: list[Segment] = [
    ((-1.55, 0.72), (-1.30, 0.86)),
    ((-1.12, 0.97), (-0.95, 0.84)),
    ((-0.78, 0.72), (-0.55, 0.92)),
    ((-0.28, 1.10), (0.00, 1.00)),
    ((0.28, 1.10), (0.55, 0.92)),
    ((0.78, 0.72), (0.95, 0.84)),
    ((1.12, 0.97), (1.30, 0.86)),
    ((1.55, 0.72), (1.90, 0.80)),
    ((1.90, 2.00), (1.90, 3.20)),
    ((0.00, 3.20), (-1.90, 3.20)),
]
_HAIR_TIP_CLIP_ID = "hair-tips"

# The hairline: up one lock in front of the cheek, across the fringe to the
# parting at the crown, then back down the other side. This is the only
# line drawn inside the mass, which is what lets front and back hair read
# as a single object. Both ends land exactly on the mass's own tips, where
# the silhouette stroke takes over, so the line never stops in mid-air.
_HAIRLINE_START: Point = (-1.06, 1.90)
_HAIRLINE: list[Segment] = [
    ((-1.02, 1.87), (-0.95, 1.75)),
    ((-0.86, 1.45), (-0.88, 1.05)),
    ((-0.92, 0.70), (-0.88, 0.35)),
    ((-0.86, -0.26), (-0.40, -0.72)),
    ((-0.16, -0.88), (0.00, -0.94)),
    ((0.16, -0.88), (0.40, -0.72)),
    ((0.86, -0.26), (0.88, 0.35)),
    ((0.92, 0.70), (0.88, 1.05)),
    ((0.86, 1.45), (0.95, 1.75)),
    ((1.02, 1.87), (1.06, 1.90)),
]

# Outer edge of the fringe and locks, closing the shape back to the start.
# It stays just inside _HAIR_MASS the whole way, so the two fills overlap
# rather than butt together, and stays outside the head circle so the skull
# outline never shows through the hair.
_HAIRLINE_BACK: list[Segment] = [
    ((1.24, 1.79), (1.24, 1.62)),
    ((1.22, 1.20), (1.15, 0.72)),
    ((1.09, 0.10), (1.00, -0.30)),
    ((0.84, -1.20), (0.00, -1.14)),
    ((-0.84, -1.20), (-1.00, -0.30)),
    ((-1.09, 0.10), (-1.15, 0.72)),
    ((-1.22, 1.20), (-1.24, 1.62)),
    ((-1.24, 1.79), (-1.06, 1.90)),
]


def _hair_tip_tone(p: CharacterParams) -> str | None:
    """The tone the hair fades into, or None when the hair is single-tone."""
    if p.hair_tip_color is None or p.hair_tip_color == p.hair_color:
        return None
    return p.hair_tip_color


def _hair_defs(sk: Skeleton, p: CharacterParams) -> str:
    if _hair_tip_tone(p) is None:
        return ""
    d = _curve(sk.head_cx, sk.head_cy, sk.head_r, _HAIR_TIP_EDGE_START, _HAIR_TIP_EDGE)
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
    d = _curve(sk.head_cx, sk.head_cy, sk.head_r, _HAIR_MASS_START, _HAIR_MASS)
    parts = _two_tone_hair(d, p)
    parts.append(f'<path d="{d}" fill="none" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />')
    return "".join(parts)


def _neck(sk: Skeleton, p: CharacterParams) -> str:
    w = sk.head_r * 0.45
    x = sk.head_cx - w / 2
    # Runs past the shoulder line so the dress's V notch, which is drawn
    # over it, opens onto skin rather than onto the hair behind the body.
    h = sk.shoulder_y - sk.neck_y + sk.head_r * 0.25
    rx = w * 0.35
    return f'<rect x="{x:.1f}" y="{sk.neck_y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{shade(p.skin_tone)}" />'


def _dress(sk: Skeleton, p: CharacterParams) -> str:
    cx = sk.head_cx
    sw, hw = sk.shoulder_half_w, sk.hem_half_w
    sy, hy = sk.shoulder_y, sk.hem_y
    notch = sk.head_r * 0.18
    flare_y = hy - sk.head_r * 0.15
    d = (
        f"M {cx - notch:.1f} {sy:.1f} "
        f"L {cx - sw:.1f} {sy:.1f} "
        f"L {cx - hw:.1f} {flare_y:.1f} "
        f"Q {cx - hw:.1f} {hy:.1f} {cx - hw * 0.6:.1f} {hy:.1f} "
        f"L {cx + hw * 0.6:.1f} {hy:.1f} "
        f"Q {cx + hw:.1f} {hy:.1f} {cx + hw:.1f} {flare_y:.1f} "
        f"L {cx + sw:.1f} {sy:.1f} "
        f"L {cx + notch:.1f} {sy:.1f} "
        f"L {cx:.1f} {sy + notch:.1f} "
        f"Z"
    )
    fill = p.outfit_color
    shape = f'<path d="{d}" fill="{fill}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'
    if not p.shaded:
        return shape
    # single hem shadow band for a bit of cel-shaded depth
    shadow_y = hy - (hy - sy) * 0.22
    sd = (
        f"M {cx - hw * 0.85:.1f} {shadow_y:.1f} "
        f"L {cx - hw:.1f} {flare_y:.1f} "
        f"Q {cx - hw:.1f} {hy:.1f} {cx - hw * 0.6:.1f} {hy:.1f} "
        f"L {cx + hw * 0.6:.1f} {hy:.1f} "
        f"Q {cx + hw:.1f} {hy:.1f} {cx + hw:.1f} {flare_y:.1f} "
        f"L {cx + hw * 0.85:.1f} {shadow_y:.1f} "
        f"Z"
    )
    shadow = f'<path d="{sd}" fill="{shade(p.outfit_color)}" opacity="0.9" />'
    return shape + shadow


def _arms(sk: Skeleton, p: CharacterParams) -> str:
    width = sk.head_r * 0.46
    y1 = sk.shoulder_y + sk.head_r * 0.1
    y2 = sk.waist_y + sk.head_r * 0.3
    sleeve = shade(p.outfit_color, 1.08, 0.9)
    parts = []
    for side in (-1, 1):
        x1 = sk.head_cx + side * sk.shoulder_half_w * 1.05
        x2 = sk.head_cx + side * sk.shoulder_half_w * 1.2
        parts.append(_capsule(x1, y1, x2, y2, width + STROKE_W * 2, OUTLINE))
        parts.append(_capsule(x1, y1, x2, y2, width, sleeve))
        hand_r = sk.head_r * 0.2
        parts.append(
            f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="{hand_r:.1f}" fill="{p.skin_tone}" stroke="{OUTLINE}" stroke-width="2" />'
        )
    return "".join(parts)


def _legs_and_boots(sk: Skeleton, p: CharacterParams) -> str:
    leg_w = sk.head_r * 0.32
    gap = sk.head_r * 0.22
    parts = []
    for side in (-1, 1):
        lx = sk.head_cx + side * gap - leg_w / 2
        parts.append(
            f'<rect x="{lx:.1f}" y="{sk.hem_y - 4:.1f}" width="{leg_w:.1f}" height="{sk.ankle_y - sk.hem_y + 4:.1f}" fill="{p.skin_tone}" />'
        )
        boot_w = leg_w * 1.5
        bx = sk.head_cx + side * gap - boot_w / 2
        boot_h = sk.foot_y - sk.ankle_y
        parts.append(
            f'<rect x="{bx:.1f}" y="{sk.ankle_y:.1f}" width="{boot_w:.1f}" height="{boot_h:.1f}" rx="{boot_w * 0.25:.1f}" '
            f'fill="{p.boot_color}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'
        )
        sole_h = boot_h * 0.28
        parts.append(
            f'<rect x="{bx:.1f}" y="{sk.foot_y - sole_h:.1f}" width="{boot_w:.1f}" height="{sole_h:.1f}" rx="{sole_h * 0.4:.1f}" '
            f'fill="{shade(p.boot_color, 0.7)}" />'
        )
    return "".join(parts)


def _head(sk: Skeleton, p: CharacterParams) -> str:
    circle = f'<circle cx="{sk.head_cx:.1f}" cy="{sk.head_cy:.1f}" r="{sk.head_r:.1f}" fill="{p.skin_tone}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'
    if not p.shaded:
        return circle
    shadow_r = sk.head_r
    sd = (
        f'<path d="M {sk.head_cx:.1f} {sk.head_cy - shadow_r:.1f} '
        f"A {shadow_r:.1f} {shadow_r:.1f} 0 0 1 {sk.head_cx:.1f} {sk.head_cy + shadow_r:.1f} "
        f'A {shadow_r * 0.9:.1f} {shadow_r:.1f} 0 0 0 {sk.head_cx:.1f} {sk.head_cy - shadow_r:.1f} Z" '
        f'fill="{shade(p.skin_tone, 0.93)}" opacity="0.7" />'
    )
    return circle + sd


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
    fill_d = _curve(cx, cy, r, _HAIRLINE_START, _HAIRLINE + _HAIRLINE_BACK)
    line_d = _curve(cx, cy, r, _HAIRLINE_START, _HAIRLINE, close=False)
    parts = _two_tone_hair(fill_d, p)
    parts.append(
        f'<path d="{line_d}" fill="none" stroke="{OUTLINE}" stroke-width="{STROKE_W}" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
    )
    return "".join(parts)


def render_character(p: CharacterParams | None = None, sk: Skeleton | None = None) -> str:
    p = p or CharacterParams()
    sk = sk or build_skeleton()

    layers = [
        _hair_defs(sk, p),
        _hair_mass(sk, p),
        _neck(sk, p),
        _dress(sk, p),
        _legs_and_boots(sk, p),
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
