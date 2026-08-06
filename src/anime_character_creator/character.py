"""Assembles a character from flat vector shapes anchored to a
Skeleton. Every shape is plain SVG (paths, circles, capsule-strokes) so
recoloring is just swapping a fill/stroke attribute and the whole figure
scales as one unit via the skeleton's head_r.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field, replace

from .colorutil import shade
from .skeleton import DEFAULT_HEADS, Skeleton, build_skeleton

# Every line on the figure. Near black rather than the dark grey this was: the
# canon's outline samples at #080808 and its dark pixels pile up in the 0-9 value
# bucket, 17% of the figure's ink, where ours sat at 43 and piled up in 40-49.
# Same quantity of line, softer colour, and the whole figure read hazier for it.
# Not pure black, which is a hair harder than the canon and gains nothing.
OUTLINE = "#0d0d0d"


def _stroke_w(sk: Skeleton) -> float:
    """Silhouette stroke weight for this figure.

    The canon draws its line as a fraction of the figure, not of the canvas:
    about 0.017 of head width at chibi and 0.023 at realistic, measured off
    ref/satoko-chibi.jpg and ref/satoko-real.jpg, so the smaller head carries
    the relatively heavier line. The canvas constant this replaces came out
    thin at one end and heavy at the other. Interior lines take fractions of
    this weight: they divide surfaces rather than bound them.
    """
    return sk.head_r * (0.041 + 0.017 * sk.build)


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
    # A pouch on each hip, hanging from the belt band. Working-outfit detail
    # the canon keeps even at chibi. Needs a belt to hang from.
    pouch_color: str | None = None
    # Skirt hem, measured hip (0) to ankle (1), the way hair_length is measured
    # chin to hip, so one garment keeps its length across builds. None takes the
    # skeleton's own hem anchor, which is where a hem sits when nobody asks for
    # anything in particular.
    skirt_length: float | None = None


@dataclass(frozen=True)
class CharacterParams:
    """Everything about a character that is not its proportions.

    The public interface of the package: colours, the garments in `outfit`, the
    expression in `face`, which haircut and how long, plus the two skeleton knobs
    (`heads`, `frame`) used when `render_character` is not handed a skeleton of
    its own. Frozen, so a variant is `dataclasses.replace(base, ...)` and a
    preset can be shared without anything downstream editing it.

    Anything a character needs to differ on belongs here, on `Outfit` or on
    `FaceStyle` with a neutral default, never hardcoded into a part function:
    that is what keeps this a generator rather than one character's renderer.
    """

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


def _curve(
    cx: float, cy: float, r: float, start: Point, segments: list[Segment], close: bool = True
) -> str:
    """Build a path 'd' from a start point plus quadratic segments, all in
    head-radius units. Keeping the shapes as point data rather than format
    strings means a silhouette can be reshaped without rewriting SVG."""
    d = ["M " + _head_units(cx, cy, r, start)]
    for ctrl, end in segments:
        d.append("Q " + _head_units(cx, cy, r, ctrl) + " " + _head_units(cx, cy, r, end))
    if close:
        d.append("Z")
    return " ".join(d)


# No hair ink may reach above -1.36 head radii from the head centre, and the
# stroke's outer half counts as ink. That is the headroom `build_skeleton`'s
# `hair_margin` leaves above the skull, and nothing derives the bound from the
# shapes here, so a taller crown silently comes out sliced flat against the
# canvas edge, which is how both chibis shipped before it was measured. The
# tallest point below is the short cut's crown, painted edge about -1.30.
#
# Hair is described in two zones. Above the cheek line it is pinned to the
# skull, so those points are literal head-radius units. Below it the shape is
# a fall whose points are given as a fraction of the way to the tips, so
# `hair_length` restyles the whole thing without touching the crown, and the
# hair keeps its relationship to the body when proportions change.
_HAIR_CHEEK_Y = 0.72
_HAIR_TIP_CLIP_ID = "hair-tips"
_HAIR_FRONT_CLIP_ID = "hair-front"

# Where a two-tone head of hair changes tone, as a fraction of its own height
# from the crown down to its lowest tips. Half and half is the owner's ratio.
#
# A fraction of the whole silhouette, not of the fall: the fall lengthens with
# the body while the crown stays pinned to the skull, so one fall fraction
# comes out at different heights per build. The line that sat three quarters
# of the way down the chibi's hair sat two thirds of the way down the adult's,
# which is the same character coloured differently at each build. Stated this
# way one number holds for both cuts at every build, and moving the fade is
# moving this.
_HAIR_FADE = 0.50
# Top of the long cut's silhouette, which is the crown anchor in
# `_hair_mass_shape`. The short cut's own top is its crown radius, `_CROWN_R`.
_HAIR_CROWN_Y = -1.16


def _fade_y(top: float, bottom: float) -> float:
    """The two-tone boundary for hair running from `top` to `bottom`, both in
    head radii. Cuts wave their own edge around this line rather than sitting
    flat on it, since a level boundary reads as a painted band."""
    return top + _HAIR_FADE * (bottom - top)


# The short cut's crown is an arc of a circle about the head centre, so 0.28 head
# radii of hair over a skull of radius 1. It runs temple to temple, the temple
# being the point on that circle at y = -0.30, below which the mass flares out to
# the cheek and the side locks begin.
_CROWN_R = 1.28
_CROWN_TO_TEMPLE = math.degrees(math.acos(0.30 / _CROWN_R))


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


def _arc(r: float, from_deg: float, to_deg: float, segments: int) -> tuple[Point, list[Segment]]:
    """A circular arc about the head centre, as quadratics, in head-radius units.
    Angles are degrees clockwise from straight up, so 0 is the top of the head.

    A quadratic follows a circle closely enough at these spans if its control
    point sits on the bisector at `r / cos(half the segment's angle)`, the same
    construction `_head_shape` uses. Placing anchors and controls by hand instead
    is what gives a crown that scallops between them: the wobble is not texture,
    it is the segments failing to agree on a radius.
    """

    def pt(deg: float, radius: float) -> Point:
        a = math.radians(deg)
        return (radius * math.sin(a), -radius * math.cos(a))

    step = (to_deg - from_deg) / segments
    ctrl_r = r / math.cos(math.radians(step / 2))
    return pt(from_deg, r), [
        (pt(from_deg + step * (i + 0.5), ctrl_r), pt(from_deg + step * (i + 1), r))
        for i in range(segments)
    ]


# The long cut's fall, as the five x values its outer edge is built from, in head
# radii. They live here because three separate places have to agree on them: the
# mass draws this edge, `_fall_edge` hands the same edge to the front lock, and
# the hairline's closing path meets it at the cheek. Moving one and not the others
# opens a sliver of mass outside the lock with a stroke down each side of it,
# which is the double line the hair contract warns about, and it is what happened
# the first time this was tried.
#
# `_CHEEK` is the one that decides how much hair shows beside the face, which is
# the fall's visible width where it matters most.
# A fourth thing has to move with them, which is not expressible here: the two
# strand lines down each fall sit at fixed head radii, so widening the edge
# without pushing them out leaves one of them lying outside the new lock and
# reading as the fall's boundary. `_long_strands` carries a matching offset.
_FALL_TEMPLE_X = 1.22
_FALL_CHEEK_X = 1.26
_FALL_MID_X = 1.36
_FALL_WIDE_X = 1.44
_FALL_FLARE_X = 1.52
_FALL_TIP_X = 1.22


def _fall_edge(length: float) -> tuple[Point, list[Segment]]:
    """The mass's outer edge on the right side, tip up to the cheek. Both the
    mass and the front lock are built from this, so their edges coincide
    exactly: where the mass shows, the two strokes land on each other, and
    where the body covers it, the lock's stroke carries the silhouette on."""

    def y(f: float) -> float:
        return _fall(f, length)

    return (_FALL_TIP_X, y(1.00)), [
        ((_FALL_FLARE_X, y(0.82)), (_FALL_WIDE_X, y(0.62))),
        ((_FALL_MID_X, y(0.30)), (_FALL_CHEEK_X, _HAIR_CHEEK_Y)),
    ]


def _hair_mass_shape(length: float) -> tuple[Point, list[Segment]]:
    """Crown, then falls that flare outward on the way down, ending in
    pointed locks. This one shape carries the hair's only outer contour.

    The silhouette is a bell, not a curtain: slimmer where it passes the
    face (1.16 at the cheek), widest below the shoulders (1.52 at the
    controls), then tapering back to the tips. Widest at the skull it read
    as a tall egg next to the canon, which flares every fall outward and
    keeps the crown low. Chosen from a side-by-side lab over the straight
    version and a half-bell; the full bell won at both builds.

    The bottom edge is tips and notches rather than a blunt curve: the canon
    ends every fall in points. Offsets around the tip line are absolute head
    radii rather than fractions of the fall, so the points stay the same
    size on the chibi's short fall as on the adult's long one, the way the
    short cut's lock ends are sized.
    """

    def y(f: float) -> float:
        return _fall(f, length)

    tip = y(1.00)
    return (-1.02, -0.30), [
        ((-0.86, _HAIR_CROWN_Y - 0.06), (0.00, _HAIR_CROWN_Y)),
        ((0.86, _HAIR_CROWN_Y - 0.06), (1.02, -0.30)),
        ((_FALL_TEMPLE_X, 0.20), (_FALL_CHEEK_X, _HAIR_CHEEK_Y)),
        ((_FALL_MID_X, y(0.30)), (_FALL_WIDE_X, y(0.62))),
        ((_FALL_FLARE_X, y(0.82)), (_FALL_TIP_X, tip)),
        ((1.08, tip + 0.04), (0.92, tip - 0.24)),
        ((0.76, tip - 0.16), (0.60, tip + 0.10)),
        ((0.44, tip + 0.02), (0.30, tip - 0.20)),
        ((0.14, tip - 0.12), (0.00, tip + 0.06)),
        ((-0.14, tip - 0.12), (-0.30, tip - 0.20)),
        ((-0.44, tip + 0.02), (-0.60, tip + 0.10)),
        ((-0.76, tip - 0.16), (-0.92, tip - 0.24)),
        ((-1.08, tip + 0.04), (-_FALL_TIP_X, tip)),
        ((-_FALL_FLARE_X, y(0.82)), (-_FALL_WIDE_X, y(0.62))),
        ((-_FALL_MID_X, y(0.30)), (-_FALL_CHEEK_X, _HAIR_CHEEK_Y)),
        ((-_FALL_TEMPLE_X, 0.20), (-1.02, -0.30)),
    ]


def _hair_tip_edge(length: float) -> tuple[Point, list[Segment]]:
    """Where hair fades to its tip tone. Only the part crossing the two side
    falls is ever visible, the rest sits behind the head and body. The edge
    scallops deeply, dipping toward the tips between anchors, so the fade
    follows the locks the way the canon's does instead of waving gently
    across them as one line. Closes into a region covering everything below.

    Both the line and the scallops around it are placed as fractions of the
    hair's own height rather than of the fall, so the ratio of the two tones
    and the size of the wave hold at every build. See `_HAIR_FADE`.
    """
    span = length - _HAIR_CROWN_Y

    # Above the line and below it, by a fraction of that height. Anchors ride
    # high and the controls pull the curve down between them, so each scallop
    # hangs from two points rather than arching over them, and the depths vary
    # a little so the row does not come out as one repeated wave.
    def hi(d: float) -> float:
        return _fade_y(_HAIR_CROWN_Y, length) - span * d

    def lo(d: float) -> float:
        return _fade_y(_HAIR_CROWN_Y, length) + span * d

    floor = length + 1.5
    return (-1.90, hi(0.045)), [
        ((-1.60, lo(0.075)), (-1.24, hi(0.040))),
        ((-0.98, lo(0.080)), (-0.72, hi(0.050))),
        ((-0.48, lo(0.070)), (-0.24, hi(0.040))),
        ((0.00, lo(0.085)), (0.24, hi(0.040))),
        ((0.48, lo(0.070)), (0.72, hi(0.050))),
        ((0.98, lo(0.080)), (1.24, hi(0.040))),
        ((1.60, lo(0.075)), (1.90, hi(0.045))),
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

    start: Point = (-1.22, y(1.00))
    line: list[Segment] = [
        ((-1.18, y(0.97)), (-1.08, y(0.85))),
        ((-0.98, y(0.60)), (-0.90, y(0.28))),
        ((-0.92, 0.70), (-0.88, 0.35)),
        # The fringe is a high part with two sweeps, not a curtain: the apex
        # sits well up the forehead and the sweeps descend toward the outer eye
        # corners, so a triangle of skin shows. That structure is the canon's
        # and stays. An earlier pass pulled the whole fringe down to the brow
        # line to cure a bare-headed look and was reverted, correctly: the cure
        # is the sweeps, not blanket coverage, and hair can sit high as long as
        # it visibly comes *from* the part and lies across the forehead on its
        # way down. The part is right of centre, where the crown strands
        # radiate from, and the two sweeps are unequal, so the cut reads parted
        # without the silhouette giving up its mirrored point data.
        #
        # What was wrong was the amount, not the idea. Measured down the centre
        # line, the canon's fringe reaches 0.147 of the figure's height and ours
        # reached 0.109, so the apex sat about 0.19 head radii too high and the
        # triangle it opened was half again too tall. The forehead run below is
        # that much lower, blended to nothing at the temples so the side locks
        # do not move, which leaves the part and the exposed wedge intact and
        # only takes back the excess. Lowering it further closes the part and
        # crowds the brows, which is where the reverted pass went wrong.
        ((-0.72, 0.16), (-0.52, -0.18)),
        ((-0.22, -0.31), (0.12, -0.49)),
        ((0.36, -0.31), (0.58, -0.20)),
        ((0.78, 0.10), (0.88, 0.35)),
        ((0.92, 0.70), (0.90, y(0.28))),
        ((0.98, y(0.60)), (1.08, y(0.85))),
        ((1.18, y(0.97)), (1.22, y(1.00))),
    ]
    # Down the fall the fringe's outer edge is the mass's own edge, so the
    # lock can carry the silhouette where the body hides the mass. Above the
    # cheek it tucks inside instead, which is what keeps the temple seamless.
    _, right_edge = _fall_edge(length)
    _, left_down = _reverse(*_mirror(*_fall_edge(length)))
    back: list[Segment] = [
        *right_edge,
        ((1.05, 0.10), (1.00, -0.30)),
        ((0.84, -1.16), (0.00, -1.10)),
        ((-0.84, -1.16), (-1.00, -0.30)),
        # Meets the mirrored fall edge at the cheek, so this has to be the same
        # x the mass and `_fall_edge` use. Hardcoded here it silently disagreed
        # with them the first time the fall was widened, and the left fall came
        # out with a sliver of mass outside the lock.
        ((-1.05, 0.10), (-_FALL_CHEEK_X, _HAIR_CHEEK_Y)),
        *left_down,
    ]
    return start, line, back


def _long_strands(length: float) -> list[tuple[Point, list[Segment]]]:
    """Lines dividing the long cut into locks: sweeps off a parting just right
    of centre across the crown, a pair down each fall, and short flicks in the
    fringe. Unlike the short cut's, which radiate from a crown whorl, these
    fall with the hair: the fall lines run nearly the whole drop, which is
    what turns the two side curtains into hanging locks.
    """

    def y(f: float) -> float:
        return _fall(f, length)

    # The outer line down the right fall. Long enough that writing its mirror out
    # as a second row wraps, and a wrapped row no longer reads as the twin of the
    # one above it, so this pair is mirrored rather than spelled twice.
    #
    # These x values ride with `_FALL_CHEEK_X` and its neighbours, 0.10 head radii
    # further out than they were when the fall was narrower. A strand that stays
    # put while the edge moves out ends up outside its own lock, and then it is
    # not a division inside the hair, it is a second boundary a hair's width in
    # from the silhouette: two parallel lines down the fall, which is what the
    # first attempt at widening this produced.
    outer_lock: tuple[Point, list[Segment]] = (
        (1.14, 0.10),
        [((1.42, y(0.28)), (1.38, y(0.58))), ((1.32, y(0.78)), (1.36, y(0.94)))],
    )
    return [
        # Crown sweeps, following the parting right of centre like the fringe's
        # own peak. They start part way down rather than at the crown itself: run
        # all the way up, four lines converging inside a patch a fifth of a head
        # radius across read as spokes off a hub, which is the same thing that
        # made the short cut look like an umbrella. Cut back to the outer half of
        # each sweep they read as the divisions between locks instead, which is
        # what the canon draws, and it draws fewer of them than this.
        ((-0.32, -0.87), [((-0.53, -0.70), (-0.66, -0.50))]),
        ((-0.59, -0.73), [((-0.84, -0.50), (-0.96, -0.24))]),
        ((0.41, -0.79), [((0.54, -0.58), (0.62, -0.34))]),
        ((0.68, -0.63), [((0.89, -0.37), (1.00, -0.06))]),
        # One long line down each fall, drifting outward with the bell, and a
        # shorter inner one, so the fall divides into three unequal locks.
        outer_lock,
        _mirror(*outer_lock),
        ((1.04, 0.40), [((1.18, y(0.30)), (1.15, y(0.55)))]),
        ((-1.04, 0.40), [((-1.18, y(0.30)), (-1.15, y(0.55)))]),
        # Fringe flicks following the sweeps, ending just above the hairline.
        ((0.26, -0.74), [((0.36, -0.64), (0.42, -0.55))]),
        ((-0.16, -0.76), [((-0.32, -0.64), (-0.46, -0.48))]),
    ]


def _short_mass_shape(tip: float) -> tuple[Point, list[Segment]]:
    """A short layered cut: the skull, side locks coming down in front of the
    ears to ragged points, and the nape tucked up behind the jaw.

    Its points are placed straight off `tip` instead of going through `_fall`,
    which measures a long fall down from the cheek line and so cannot describe
    hair that ends above the chin at all.

    The silhouette is a crop, not a bob: the bulk ends around ear level,
    hugging the skull at 1.26 past the cheek, and what reaches lower is only
    ragged tips, a side spike flicking down and out, a second tip below it,
    and a nape flick that shows beside the neck. It used to fall in two long
    side locks framing the face to below the cheeks, which is a girl's bob in
    miniature; every satoshi ref ends the bulk at the ear. The centre of the
    rim tucks behind the skull, so only the outer tips are ever visible, and
    more of the nape shows at taller builds as the jaw narrows off it.

    The crown is one circular arc, kept deliberately clean. Hand-placed
    points once scalloped it, and a later attempt at additive cowlick flicks
    (bumps rising off the arc, tried 2026-08-06) read as wobble too and was
    reverted on the owner's call; the tousle may be revisited, but any
    version of it has to beat the plain circle by eye first. The hair reads
    as locks through the strands, the fringe and the rim, so the crown does
    not have to carry any of it.
    """
    left_temple, crown = _arc(_CROWN_R, -_CROWN_TO_TEMPLE, _CROWN_TO_TEMPLE, 4)
    return left_temple, [
        *crown,
        ((1.30, -0.10), (1.26, 0.08)),
        ((1.34, tip - 0.34), (1.31, tip - 0.08)),
        ((1.16, tip - 0.28), (1.05, tip - 0.04)),
        ((1.02, tip + 0.02), (0.97, tip + 0.20)),
        ((0.88, tip - 0.04), (0.78, tip + 0.10)),
        ((0.68, tip + 0.16), (0.54, tip + 0.44)),
        ((0.30, tip + 0.16), (0.00, tip + 0.22)),
        ((-0.30, tip + 0.16), (-0.54, tip + 0.44)),
        ((-0.68, tip + 0.16), (-0.78, tip + 0.10)),
        ((-0.88, tip - 0.04), (-0.97, tip + 0.20)),
        ((-1.02, tip + 0.02), (-1.05, tip - 0.04)),
        ((-1.16, tip - 0.28), (-1.31, tip - 0.08)),
        ((-1.34, tip - 0.34), (-1.26, 0.08)),
        ((-1.30, -0.10), left_temple),
    ]


def _short_fall_edge(tip: float) -> tuple[Point, list[Segment]]:
    """The side lock's outer edge, tip up to the temple. Traces the mass's own
    outer edge in reverse, exactly, for the same reason `_fall_edge` does, which
    is why it has to end on the same temple point the crown arc starts from."""
    _, crown = _arc(_CROWN_R, -_CROWN_TO_TEMPLE, _CROWN_TO_TEMPLE, 4)
    right_temple = crown[-1][1]
    return (0.97, tip + 0.20), [
        ((1.02, tip + 0.02), (1.05, tip - 0.04)),
        ((1.16, tip - 0.28), (1.31, tip - 0.08)),
        ((1.34, tip - 0.34), (1.26, 0.08)),
        ((1.30, -0.10), right_temple),
    ]


def _short_tip_edge(tip: float) -> tuple[Point, list[Segment]]:
    """Where the crop fades to its tip tone: a wave about the line half way
    down the cut, so the sideburns, the rim tips, the nape and the lower part
    of the fringe are all pale and the crown stays in the base colour. This is
    what the canon shows, and it is the same ratio the long cut carries.

    The wave is deep enough to cross the fringe's lock tips rather than run
    level over them: a straight line there reads as a band painted across the
    head, and the fringe is the one place on this cut where the boundary is
    seen against a wide field of hair rather than down a narrow lock.

    The offsets are absolute head radii rather than fractions of the height,
    which the long cut needs: this cut's `tip` comes from a `tip_range`, so it
    sits at the same depth whatever the build, and the whole silhouette with it.

    Earlier passes put this band far lower, at a third of the way up from the
    tips. A per-spike boundary hugging each tip was tried before that and lost
    the two-tone look almost entirely.
    """
    # Half way down what is seen of the crop rather than half way down its
    # silhouette. The nape flick and the inner rim run behind the jaw and the
    # shoulders at every build, so the height the ratio divides ends at the
    # sideburn tips, not at the lowest point of the shape. Even then the line
    # came out just under the fringe and the cut still read as a blonde head
    # with pale sides, so it lifts another 0.07 head radii to cross the
    # fringe's own tips, where the canon has it.
    mid = _fade_y(-_CROWN_R, tip + 0.20) - 0.07
    floor = tip + 1.5
    return (-1.90, mid - 0.10), [
        ((-1.58, mid + 0.06), (-1.30, mid - 0.04)),
        ((-1.06, mid + 0.10), (-0.86, mid - 0.02)),
        ((-0.55, mid + 0.10), (-0.30, mid)),
        ((0.00, mid + 0.12), (0.30, mid)),
        ((0.55, mid + 0.10), (0.86, mid - 0.02)),
        ((1.06, mid + 0.10), (1.30, mid - 0.04)),
        ((1.58, mid + 0.06), (1.90, mid - 0.10)),
        ((1.90, floor * 0.6), (1.90, floor)),
        ((0.00, floor), (-1.90, floor)),
    ]


def _short_hairline_shape(tip: float) -> tuple[Point, list[Segment], list[Segment]]:
    """The short cut's fringe: up one side lock, across a fringe that stops just
    above the brows, and down the other. Both ends land on the mass's own tips,
    same contract as the long style's hairline. The fringe's two halves are not
    mirror images, which is what gives it a sweep without the asymmetry having to
    reach the silhouette.

    Brows sit at about -0.35, so the fringe bottoms out just above them, same
    line the long style settled on. It used to stop around -0.55, which left the
    tall bare forehead that had already been fixed on the long cut. The temples
    come down to eye level too, where the fringe runs into the side locks.

    The fringe is a row of overlapping wedge locks rather than one arc: tips dip
    toward the brows and the notches between them rise only about a third as far,
    so it reads as hair lying over hair. Rising the whole way between tips gives a
    row of teeth instead, which is worth knowing because it was the first thing
    tried. The locks lengthen away from the parting, which sits right of centre.
    """
    _, right_edge = _short_fall_edge(tip)
    _, left_down = _reverse(*_mirror(*_short_fall_edge(tip)))
    # Back across the crown on a smaller arc than the mass's, so the mass's own
    # outline carries the silhouette rather than being painted over, and well
    # outside the head circle, so the skull outline never shows through the hair.
    # This edge is only ever a fill boundary, never stroked, so it can start from
    # the outer temple the fall edge left off at without the radius change showing.
    _, inner_crown = _arc(_CROWN_R - 0.10, _CROWN_TO_TEMPLE, -_CROWN_TO_TEMPLE, 4)
    back: list[Segment] = [*right_edge, *inner_crown, *left_down]
    # Both ends land on the mass's own lock tips, which is what `back` starts and
    # finishes on, so the hairline never stops in mid-air wherever those move to.
    start: Point = back[-1][1]
    line: list[Segment] = [
        ((-1.06, tip - 0.02), (-1.02, tip - 0.30)),
        ((-0.98, 0.10), (-0.92, -0.18)),
        # The locks vary in width, depth and direction on purpose: a wide
        # shallow one, a high notch showing a patch of forehead, a deep
        # narrow tip reaching for the brow, a small crossing kink. The old
        # row repeated one wedge and read as a pattern, and a fringe is the
        # one place this style wants its irregularity.
        ((-0.86, -0.46), (-0.70, -0.34)),
        ((-0.58, -0.58), (-0.44, -0.52)),
        ((-0.36, -0.24), (-0.28, -0.14)),
        ((-0.20, -0.44), (-0.06, -0.40)),
        ((0.04, -0.20), (0.14, -0.24)),
        ((0.24, -0.52), (0.40, -0.46)),
        ((0.52, -0.26), (0.62, -0.30)),
        ((0.78, -0.16), (0.94, -0.16)),
        ((0.98, 0.10), (1.02, tip - 0.30)),
        ((1.06, tip - 0.02), (0.97, tip + 0.20)),
    ]
    return start, line, back


def _short_strands(tip: float) -> list[tuple[Point, list[Segment]]]:
    """Lines dividing the crop into locks: across the crown on the parting's own
    lines, each dying near a notch of the fringe, plus one line down each
    sideburn. They no longer reach the parting itself, for the reason below.
    The sideburns used to carry a second line each, but the crop's
    side band is too narrow for two: they read as tram lines and were cut.

    Without these the crown is one unbroken field of hair colour, which is what
    made the cut read as an object rather than as hair: a render with the strands
    suppressed and everything else in place still looks like a pot.
    """
    # Each crown line starts part way along its own path rather than at the
    # crown. Drawn full length all six left the same patch at the top of the
    # skull, and six lines from one point on a part-circle mass is a beach
    # umbrella: the spokes were doing as much damage as the dome. Trimmed to
    # their outer halves they sit spread across the crown, each still aimed at
    # its notch of the fringe, and read as the seams between locks. Trimming
    # further, or dropping to four lines, empties the crown and the cut goes back
    # to reading as one smooth field.
    #
    # The dome itself is untouched here. That is the parked crown tousle, and
    # what is left after this is exactly the shape of it.
    return [
        ((-0.49, -0.85), [((-0.67, -0.64), (-0.74, -0.38))]),
        ((-0.15, -0.77), [((-0.22, -0.56), (-0.12, -0.44))]),
        ((0.24, -0.81), [((0.29, -0.62), (0.36, -0.48))]),
        ((0.52, -0.81), [((0.64, -0.61), (0.66, -0.36))]),
        ((0.74, -0.68), [((0.95, -0.44), (1.06, -0.18))]),
        ((-0.70, -0.71), [((-0.95, -0.47), (-1.06, -0.20))]),
        ((1.14, -0.44), [((1.20, 0.04), (1.14, tip - 0.28))]),
        ((-1.14, -0.44), [((-1.20, 0.04), (-1.14, tip - 0.28))]),
    ]


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
    # Open chains drawn inside the mass, dividing it into locks. One flat shape
    # with no interior line reads as an object the colour of hair rather than as
    # hair, which is the difference between a haircut and a helmet. None leaves
    # the cut undivided, so a style that does not want them says nothing.
    strands: Callable[[float], list[tuple[Point, list[Segment]]]] | None = None
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
    "long_blunt": Hairstyle(
        _hair_mass_shape, _hairline_shape, _fall_edge, _hair_tip_edge, strands=_long_strands
    ),
    "short_layered": Hairstyle(
        _short_mass_shape,
        _short_hairline_shape,
        _short_fall_edge,
        _short_tip_edge,
        strands=_short_strands,
        # Where the side tips end: a tight crop pinned to the skull at 0, a
        # shaggy ear-length cut at 1. The old (0.42, 1.00) range described the
        # bob this used to be, with locks reaching for the jaw.
        tip_range=(0.25, 0.70),
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
    style = HAIRSTYLES[p.hairstyle]
    fall = _hair_fall(sk, p)
    clips = []
    if _hair_tip_tone(p) is not None:
        start, segments = style.tip_edge(fall)
        d = _curve(sk.head_cx, sk.head_cy, sk.head_r, start, segments)
        clips.append(f'<clipPath id="{_HAIR_TIP_CLIP_ID}"><path d="{d}" /></clipPath>')
    if style.strands is not None:
        # Strands are open chains, so nothing stops one running out past the
        # silhouette; clipping them to the shape they divide means a strand can be
        # drawn long enough to reach its lock's tip without having to end exactly on
        # the outline.
        start, line, back = style.hairline(fall)
        d = _curve(sk.head_cx, sk.head_cy, sk.head_r, start, line + back)
        clips.append(f'<clipPath id="{_HAIR_FRONT_CLIP_ID}"><path d="{d}" /></clipPath>')
    return f"<defs>{''.join(clips)}</defs>" if clips else ""


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
    parts.append(
        f'<path d="{d}" fill="none" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'
    )
    return "".join(parts)


def _neck(sk: Skeleton, p: CharacterParams) -> str:
    # Plain skin, not a shadow tone. The head's own outline already separates the
    # jaw from the neck, so darkening it only made the throat look grubby; flat
    # skin lets the two read as one piece with a line across it.
    w = sk.neck_half_w * 2
    x = sk.head_cx - w / 2
    # Runs past the shoulder line so the tunic's V notch, which is drawn
    # over it, opens onto skin rather than onto the hair behind the body.
    h = sk.shoulder_y - sk.neck_y + sk.neck_half_w * 1.1
    rx = w * 0.35
    parts = [
        f'<rect x="{x:.1f}" y="{sk.neck_y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{p.skin_tone}" />'
    ]
    # The throat's own contour, which is silhouette between the jaw and the
    # shoulder and so carries full weight. Each line starts up inside the skull
    # and is covered by the head drawn over it, so the throat comes out from under
    # the jaw wherever the jaw happens to be at this build, without this having to
    # know. The tunic covers the bottom end the same way.
    for side in (-1, 1):
        nx = sk.head_cx + side * sk.neck_half_w
        parts.append(
            f'<line x1="{nx:.1f}" y1="{sk.neck_y:.1f}" x2="{nx:.1f}" y2="{sk.neck_y + h:.1f}" '
            f'stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'
        )
    return "".join(parts)


# Garment panels carry no shadow tone at all. The canon draws the tunic, the
# skirt, the apron, the sleeves and the trousers flat and puts their form on the
# outline; a second tone appears only on small elements, a pouch flap or a boot
# cuff or the turn under a hem, where it reads as a thickness rather than as
# light. Ours used to shade a third of the torso, most of the apron and a stripe
# down every limb, which came to 15% of the figure's ink at the taller build and
# was the most artificial thing on it.
#
# Narrowing those planes to edge turns was tried first and rejected by eye: it
# fixed the torso, but a stripe down something as long and thin as a sleeve or a
# trouser leg reads as two-tone at any width. What is left below is line work,
# which is what the canon uses for drape.


def _sleeve_hem_y(sk: Skeleton) -> float:
    """Where the tunic's short sleeve ends, which is also where the arm starts.
    Both parts read it, since the sleeve hem and the arm's top edge are the same
    line and have to land on each other."""
    return sk.shoulder_y + (sk.waist_y - sk.shoulder_y) * 0.42


def _sleeve_half_w(sk: Skeleton) -> float:
    """How far out the sleeve reaches.

    It has to cover the arm, so it is the arm's own outer edge with a little
    ease, and it can be wider than the anatomical shoulder: at chibi it has to
    be, because the shoulders there are narrow while the arms are thick, so a
    sleeve that stopped at `shoulder_half_w` would not reach the limb it is
    supposed to be on.
    """
    return max(sk.shoulder_half_w, sk.arm_x + sk.arm_half_w * 1.10)


def _tunic(sk: Skeleton, p: CharacterParams) -> str:
    """The torso garment, shoulder to hip, with its own short sleeves.

    Reads the waist anchor rather than running straight from shoulder to hem,
    which is what stops a tall build from coming out as a box: a chibi still
    widens all the way down, an adult takes in and back out.

    The sleeve is part of this silhouette rather than a shape laid over it. Drawn
    as its own capsule with its own closed outline it read as a shoulder pad
    bolted to the chest, because a garment's seam is not a contour. Here the
    outline runs neck, down the sloped shoulder, out to the sleeve, down its
    outside, then steps in at the hem and carries on down the torso, so the whole
    upper body is one continuous edge.
    """
    cx = sk.head_cx
    sw, ww, hw = sk.shoulder_half_w, sk.waist_half_w, sk.hip_half_w
    sy, wy, hy = sk.shoulder_y, sk.waist_y, sk.hip_y
    notch = sk.neck_half_w * 0.8
    sleeve_w = _sleeve_half_w(sk)
    cuff_y = _sleeve_hem_y(sk)
    # Shoulders slope. A horizontal shoulder line is what made the sleeve look
    # bolted on even once it was the right shape.
    slope = (wy - sy) * 0.14
    # The torso's own width where the sleeve leaves it. Measured up from the
    # waist, not down from the shoulder: `shoulder_half_w` is the span across the
    # deltoids, so a ribcage derived from it comes out wider than the arm hanging
    # in front of it, and the arm then covers the body's side contour instead of
    # standing clear of it. Both refs show the torso's side and the arm as two
    # separate edges with daylight between them below the armpit.
    torso_at_cuff = ww + (sw - ww) * 0.12

    # Control points sit at the shoulder's own width and the hip's own width, so
    # the curve leaves each landmark vertically and the taper reads as a body
    # rather than as a cone.
    hip_ctrl_y = hy - (hy - wy) * 0.45

    def shoulder(s: int) -> str:
        """Neck to the outer tip of the sleeve, then down the sleeve's outside."""
        return (
            f"Q {cx + s * sleeve_w * 0.62:.1f} {sy + slope * 0.30:.1f} "
            f"{cx + s * sleeve_w:.1f} {sy + slope:.1f} "
            f"Q {cx + s * sleeve_w * 1.03:.1f} {sy + slope + (cuff_y - sy - slope) * 0.55:.1f} "
            f"{cx + s * sleeve_w * 0.99:.1f} {cuff_y:.1f} "
            f"L {cx + s * torso_at_cuff:.1f} {cuff_y:.1f} "
        )

    # Leaves the armpit vertically and curves in to the waist, rather than being
    # pulled out toward the shoulder's own width on the way.
    rib_ctrl_y = cuff_y + (wy - cuff_y) * 0.55

    def down(s: int) -> str:
        return (
            f"Q {cx + s * torso_at_cuff:.1f} {rib_ctrl_y:.1f} {cx + s * ww:.1f} {wy:.1f} "
            f"Q {cx + s * hw:.1f} {hip_ctrl_y:.1f} {cx + s * hw:.1f} {hy:.1f} "
        )

    def up(s: int) -> str:
        return (
            f"Q {cx + s * hw:.1f} {hip_ctrl_y:.1f} {cx + s * ww:.1f} {wy:.1f} "
            f"Q {cx + s * torso_at_cuff:.1f} {rib_ctrl_y:.1f} {cx + s * torso_at_cuff:.1f} {cuff_y:.1f} "
        )

    def shoulder_up(s: int) -> str:
        """The mirror of `shoulder`, cuff back up to the neck."""
        return (
            f"L {cx + s * sleeve_w * 0.99:.1f} {cuff_y:.1f} "
            f"Q {cx + s * sleeve_w * 1.03:.1f} {sy + slope + (cuff_y - sy - slope) * 0.55:.1f} "
            f"{cx + s * sleeve_w:.1f} {sy + slope:.1f} "
            f"Q {cx + s * sleeve_w * 0.62:.1f} {sy + slope * 0.30:.1f} {cx + s * notch:.1f} {sy:.1f} "
        )

    d = (
        f"M {cx - notch:.1f} {sy:.1f} "
        + shoulder(-1)
        + down(-1)
        + f"L {cx + hw:.1f} {hy:.1f} "
        + up(1)
        + shoulder_up(1)
        + f"L {cx:.1f} {sy + notch:.1f} "
        f"Z"
    )
    fill = p.outfit.tunic_color
    shape = f'<path d="{d}" fill="{fill}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'
    if p.outfit.undersleeve_color is not None:
        # The undersleeve shows once more at the neckline: a sliver of its tone
        # trimming the V, which both canon builds wear. Drawn just inside the
        # notch so the tunic's own outline still bounds it.
        notch_t = notch * 0.78
        shape += (
            f'<path d="M {cx - notch_t:.1f} {sy + notch * 0.10:.1f} L {cx:.1f} {sy + notch_t:.1f} '
            f'L {cx + notch_t:.1f} {sy + notch * 0.10:.1f}" fill="none" '
            f'stroke="{p.outfit.undersleeve_color}" stroke-width="{_stroke_w(sk) * 0.9:.1f}" />'
        )
    return shape


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


def _skirt_path(
    sk: Skeleton, top_y: float, hem_y: float, top_w: float | None = None, hem_w: float | None = None
) -> str:
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
    shape = f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'
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
    return f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'


def _skirt(sk: Skeleton, p: CharacterParams) -> str:
    color = p.outfit.skirt_color
    if color is None:
        return ""
    hem_y = _skirt_hem_y(sk, p.outfit.skirt_length)
    # Starts above the hip so the tunic drawn over it has something to overlap
    # and the waistband never opens onto skin.
    top_y = sk.waist_y
    d = _skirt_path(sk, top_y, hem_y)
    shape = f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'
    if not p.shaded:
        return shape
    # Two folds, as thin lines rather than the shadow wedges they used to be. The
    # canon suggests this garment's drape with a line: a wedge wide enough to see
    # was a third plane on a figure that already had two, and on the chibi, where
    # the skirt below the apron is only a band, it filled it.
    folds = []
    for s, at in ((-1, 0.52), (1, 0.30)):
        x0 = sk.head_cx + s * _skirt_half_w(sk, top_y) * at
        x1 = sk.head_cx + s * _skirt_half_w(sk, hem_y) * (at + 0.06)
        folds.append(
            f'<line x1="{x0:.1f}" y1="{top_y + (hem_y - top_y) * 0.30:.1f}" '
            f'x2="{x1:.1f}" y2="{hem_y:.1f}" stroke="{shade(color)}" '
            f'stroke-width="{max(1.0, _stroke_w(sk) * 0.45):.1f}" opacity="0.7" />'
        )
    return shape + "".join(folds)


def _arms(sk: Skeleton, p: CharacterParams) -> str:
    """The arm from the sleeve hem down to the hand.

    The tunic draws its own sleeve now, so this starts where the sleeve ends. The
    arm's top edge is flat and sits exactly on the sleeve hem, at the same width,
    so the two strokes land on each other and read as one line: the hem of the
    garment and the top of the limb are the same edge, the way `_fall_edge` is
    shared between the hair's mass and its front lock.

    Still drawn last of everything below the neck, because the hands have to be
    over every garment. The apron's edge sits about three pixels inside the hand
    at chibi, and a clipped hand is the one collision that would show.

    Whatever the undersleeve is, it carries the arm's whole length. Against a
    green tunic a tan sleeve is what separates the arm from the torso; left bare,
    the arm is skin and does the same job.
    """
    cx = sk.head_cx
    sleeve = p.outfit.undersleeve_color or p.skin_tone
    top_y = _sleeve_hem_y(sk)
    wrist_y = sk.hip_y + sk.arm_half_w * 0.8
    elbow_y = sk.waist_y

    # Tapers on the build, the way the leg does. A constant-width tube is right at
    # chibi and matches ref/girl-chibi.png; at a taller build it reads as a pipe.
    w_top = sk.arm_half_w
    w_elbow = sk.arm_half_w * (1.0 - 0.15 * sk.build)
    w_wrist = sk.arm_half_w * (1.0 - 0.34 * sk.build)
    # The arm's outer edge picks up where the sleeve's did, so the silhouette runs
    # on down the limb without a step at the hem.
    out_top = _sleeve_half_w(sk) * 0.99
    centre_top = out_top - w_top
    # Arms drift outward on the way down, so daylight opens between forearm and
    # waist. The drift lives in the forearm: the upper arm hangs near vertical
    # and the bend happens at the elbow, which is what the canon's arms do and
    # what a straight slant from shoulder to wrist failed to read as. The
    # chibi keeps a modest drift of its own now: the canon's chibi hands hang
    # beside the skirt, not against it.
    centre_wrist = centre_top + sk.arm_half_w * (0.50 + 0.70 * sk.build)
    centre_elbow = centre_top + (centre_wrist - centre_top) * 0.35

    parts = []
    for s in (-1, 1):
        # Called only inside the iteration that defines it and never stored, so
        # the late binding B023 warns about cannot bite. Taking `s` as a
        # defaulted parameter to satisfy the check would show up in every call
        # site below, which is noise for a closure two lines long.
        def x(offset: float) -> float:
            return cx + s * offset  # noqa: B023

        d = (
            f"M {x(centre_top - w_top):.1f} {top_y:.1f} "
            f"L {x(centre_top + w_top):.1f} {top_y:.1f} "
            f"Q {x(centre_top + w_top * 1.03):.1f} {top_y + (elbow_y - top_y) * 0.55:.1f} "
            f"{x(centre_elbow + w_elbow):.1f} {elbow_y:.1f} "
            f"Q {x(centre_wrist + w_wrist * 1.06):.1f} {elbow_y + (wrist_y - elbow_y) * 0.5:.1f} "
            f"{x(centre_wrist + w_wrist):.1f} {wrist_y:.1f} "
            f"L {x(centre_wrist - w_wrist):.1f} {wrist_y:.1f} "
            f"Q {x(centre_wrist - w_wrist * 1.06):.1f} {elbow_y + (wrist_y - elbow_y) * 0.5:.1f} "
            f"{x(centre_elbow - w_elbow):.1f} {elbow_y:.1f} "
            f"Q {x(centre_top - w_top * 1.03):.1f} {top_y + (elbow_y - top_y) * 0.55:.1f} "
            f"{x(centre_top - w_top):.1f} {top_y:.1f} "
            f"Z"
        )
        # No tone down the sleeve. It was a turn along the inner side, and a
        # narrower one was tried, but a stripe running the length of something as
        # long and thin as a sleeve reads as a two-tone plank at any width. The
        # canon's are flat tan, separated from the torso by the outline alone.
        parts.append(
            f'<path d="{d}" fill="{sleeve}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'
        )
        parts.append(_hand(sk, p, x(centre_wrist), wrist_y, w_wrist, s))
    return "".join(parts)


def _hand(
    sk: Skeleton, p: CharacterParams, cx: float, wrist_y: float, w_wrist: float, side: int
) -> str:
    """A mitten hand hanging at the side, thumb on the inner edge.

    The canon's chibi hand is a mitten with one visible thumb, which is what
    separates a hand from the featureless stub this used to be. Still no
    fingers: the canon suggests them with a crease at most at the realistic
    build, and at this size separate digits read as noise rather than as a
    hand.
    """
    hw = w_wrist * 1.02
    # Sized to land the canon's hand, about 0.10 of head width at chibi. The
    # factor absorbs the arm it hangs off: when the chibi arm slimmed from
    # 0.22 to 0.14 head radii this went up to keep the hand itself the same.
    length = sk.arm_half_w * (1.35 + 1.10 * sk.build)
    tip = hw * (1.0 - 0.32 * sk.build)

    def x(offset: float) -> float:
        """Offsets are for the right hand, thumb toward -x; the left mirrors."""
        return cx + side * offset

    d = (
        f"M {x(hw):.1f} {wrist_y:.1f} "
        f"Q {x(hw * 1.14):.1f} {wrist_y + length * 0.55:.1f} {x(tip * 0.74):.1f} {wrist_y + length:.1f} "
        f"Q {x(0.0):.1f} {wrist_y + length * 1.16:.1f} {x(-tip * 0.70):.1f} {wrist_y + length * 0.97:.1f} "
        f"Q {x(-hw * 1.02):.1f} {wrist_y + length * 0.80:.1f} {x(-hw * 0.86):.1f} {wrist_y + length * 0.60:.1f} "
        f"Q {x(-hw * 1.32):.1f} {wrist_y + length * 0.50:.1f} {x(-hw * 1.12):.1f} {wrist_y + length * 0.28:.1f} "
        f"Q {x(-hw * 0.98):.1f} {wrist_y + length * 0.16:.1f} {x(-hw):.1f} {wrist_y:.1f} "
        f"Z"
    )
    sw = _stroke_w(sk)
    parts = [
        f'<path d="{d}" fill="{p.skin_tone}" stroke="{OUTLINE}" stroke-width="{sw * 0.85:.1f}" />'
    ]
    if p.shaded and sk.build > 0.5:
        # One crease along the thumb's root, only once there is room for it.
        parts.append(
            f'<path d="M {x(-hw * 0.70):.1f} {wrist_y + length * 0.26:.1f} '
            f'Q {x(-hw * 0.40):.1f} {wrist_y + length * 0.48:.1f} {x(-hw * 0.48):.1f} {wrist_y + length * 0.70:.1f}" '
            f'fill="none" stroke="{OUTLINE}" stroke-width="{sw * 0.45:.1f}" opacity="0.55" stroke-linecap="round" />'
        )
    return "".join(parts)


def _legs_and_boots(sk: Skeleton, p: CharacterParams) -> str:
    # The taper belongs in the thigh, and nearly nowhere else. Measured off
    # ref/satoshi.png, the trouser leg is 1.42 leg-half-widths at the thigh, 1.03
    # at the knee, 1.01 through the calf and 0.85 at the ankle: it fills out under
    # the hip, then runs close to straight. This used to run 1.55 down to 0.55, a
    # two-to-one cone that read as fat thighs on stick shins, and the fix was
    # widening the shin rather than thinning the thigh. A plain untapered tube,
    # tried against this, beat the cone and lost to it.
    #
    # The thigh ships at 1.26 rather than the measured 1.42, by preference: the
    # reference's leg is photographed on a hip wider than this skeleton's, so the
    # full measurement came out heavy on it. The knee, calf and ankle are the
    # measured values.
    taper = sk.build
    # Trousers are the outermost garment on the leg, so unlike bare skin they
    # need their own outline, they start at the hip rather than under a hem, and
    # they carry more thigh: a shin-width tube running up to the hip reads as a
    # stilt once there is no skirt covering the top of it.
    trousers = p.outfit.trouser_color
    thigh = (1.10 + 0.16 * taper) if trousers else (1.00 + 0.12 * taper)
    w_top = sk.leg_half_w * thigh
    w_knee = sk.leg_half_w * (1.00 + 0.03 * taper)
    # Held, not bulged: the reference measures 72, 71, 71 pixels from knee through
    # calf before it takes in at the ankle.
    w_calf = sk.leg_half_w * (1.00 + 0.01 * taper)
    w_ankle = sk.leg_half_w * (0.92 - 0.07 * taper)
    # Where the legs hang. At a tall build the outer edge of the thigh lands on
    # the hip, which is what the tunic's own hem is drawn to, so the body's side
    # carries straight on down into the leg instead of the trousers overhanging
    # it. Since the hip rides on `frame`, a narrow-hipped figure's legs come in
    # and a wider-hipped one's go out, which is the frame doing its job.
    #
    # A chibi keeps its legs tucked in close instead: its hips are nearly as wide
    # as an adult's in head radii while its legs are notably thinner, so
    # hanging them off the hip would splay them to the corners of the body.
    tuck = sk.leg_half_w * 1.45
    gap = tuck + (sk.hip_half_w - w_top - tuck) * taper
    # The two legs are separately stroked filled paths drawn in a loop, so if they
    # ever met, the second one's fill would cover the first one's outline and the
    # crotch would come out as an asymmetric seam. This keeps a slot open no
    # matter what frame widens the thigh or narrows the hip. The reference leaves
    # each inner edge about 0.09 head radii off centre, which is where the
    # presets land without the floor biting.
    gap = max(gap, w_top + sk.leg_half_w * 0.2)
    # A bare leg has to start at or above whatever hem is going to cover its top,
    # and the skirt's hem moves with `skirt_length`. Pinning it to the skeleton's
    # own hem leaves a band of bare canvas across the hips as soon as a skirt is
    # asked to be shorter than that.
    top_y = sk.hip_y if trousers else min(sk.hem_y, _skirt_hem_y(sk, p.outfit.skirt_length)) - 4
    calf_y = sk.knee_y + (sk.ankle_y - sk.knee_y) * 0.35
    fill = trousers or p.skin_tone
    stroke = f' stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}"' if trousers else ""
    parts = []
    for side in (-1, 1):
        cx = sk.head_cx + side * gap
        d = (
            f"M {cx - w_top:.1f} {top_y:.1f} L {cx + w_top:.1f} {top_y:.1f} "
            f"Q {cx + w_top:.1f} {sk.knee_y - (sk.knee_y - top_y) * 0.3:.1f} {cx + w_knee:.1f} {sk.knee_y:.1f} "
            f"Q {cx + w_calf:.1f} {calf_y:.1f} {cx + w_ankle:.1f} {sk.ankle_y:.1f} "
            f"L {cx - w_ankle:.1f} {sk.ankle_y:.1f} "
            f"Q {cx - w_calf:.1f} {calf_y:.1f} {cx - w_knee:.1f} {sk.knee_y:.1f} "
            f"Q {cx - w_top:.1f} {sk.knee_y - (sk.knee_y - top_y) * 0.3:.1f} {cx - w_top:.1f} {top_y:.1f} Z"
        )
        parts.append(f'<path d="{d}" fill="{fill}"{stroke} />')
        # No tone down the leg either. It was there to separate the two of them
        # when both are the same flat colour, but each leg is a stroked path with a
        # slot between them, so the outline was already doing that, and a stripe
        # down a trouser leg reads the same way one down a sleeve does. The canon
        # divides trousers with seams instead, which they do not have yet.
        parts.append(_boot(sk, p, cx, w_ankle, w_knee, side))
    return "".join(parts)


def _boot(
    sk: Skeleton, p: CharacterParams, cx: float, w_ankle: float, w_knee: float, side: int
) -> str:
    """One boot: a shaft over the ankle, an instep, and a toe pointing a
    little outward, the pair standing in the canon's slight duck stance. The
    toe is what stopped this reading as a brown block: a symmetric rounded
    rectangle has no front, and a foot is mostly front.

    Cross-laces run down the instep. The canon keeps them at both builds, so
    the old rule that they do not survive chibification is gone with the old
    reference that set it."""
    color = p.outfit.boot_color
    # A foot is a foot: measured off the leg rather than off the ankle, so it
    # keeps its size when the shin's width is retuned. As a multiple of the ankle
    # it doubled the moment the leg stopped tapering to a point. The multiplier
    # was retuned when the chibi leg thickened from 0.15 to 0.22 head radii, so
    # the boot itself, already sized to the canon, came out the same.
    boot_w = sk.leg_half_w * (2.08 - 0.08 * sk.build)
    foot_h = sk.foot_y - sk.ankle_y
    # The shaft climbs a third of the way to the knee, so it stays a boot rather
    # than becoming a waders as the shin gets longer at taller builds.
    top_y = sk.ankle_y - (sk.ankle_y - sk.knee_y) * 0.32
    # Off the ankle it wraps, not off the knee above it, so the shaft cannot come
    # out wider than the leg going into it.
    shaft_w = w_ankle * 1.10
    instep_y = sk.ankle_y + foot_h * 0.30
    # The heel can never come in narrower than the shaft above it, or the boot
    # tucks inward below the ankle, which is what it briefly did at realistic,
    # where the leg is thick against the whole boot.
    heel_w = max(boot_w * 0.42, shaft_w * 1.02)
    toe_x = heel_w + boot_w * 0.34
    r = boot_w * 0.18

    def x(offset: float) -> float:
        """Offsets are for the right boot, toe toward +x; the left mirrors."""
        return cx + side * offset

    d = (
        f"M {x(-shaft_w):.1f} {top_y:.1f} "
        f"L {x(-shaft_w):.1f} {sk.ankle_y:.1f} "
        f"Q {x(-heel_w):.1f} {instep_y:.1f} {x(-heel_w):.1f} {sk.foot_y - r:.1f} "
        f"Q {x(-heel_w):.1f} {sk.foot_y:.1f} {x(-heel_w + r):.1f} {sk.foot_y:.1f} "
        f"L {x(toe_x - r):.1f} {sk.foot_y:.1f} "
        f"Q {x(toe_x):.1f} {sk.foot_y:.1f} {x(toe_x):.1f} {sk.foot_y - r * 1.2:.1f} "
        f"Q {x(toe_x * 0.96):.1f} {sk.ankle_y + foot_h * 0.42:.1f} {x(shaft_w * 1.30):.1f} {sk.ankle_y + foot_h * 0.26:.1f} "
        f"Q {x(shaft_w * 1.06):.1f} {sk.ankle_y + foot_h * 0.16:.1f} {x(shaft_w):.1f} {sk.ankle_y:.1f} "
        f"L {x(shaft_w):.1f} {top_y:.1f} "
        f"Z"
    )
    parts = [
        f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'
    ]
    if not p.shaded:
        return "".join(parts)
    sole_h = foot_h * 0.24
    parts.append(
        f'<path d="M {x(-heel_w):.1f} {sk.foot_y - sole_h:.1f} L {x(toe_x):.1f} {sk.foot_y - sole_h:.1f} '
        f"L {x(toe_x):.1f} {sk.foot_y - r:.1f} "
        f"Q {x(toe_x):.1f} {sk.foot_y:.1f} {x(toe_x - r):.1f} {sk.foot_y:.1f} "
        f"L {x(-heel_w + r):.1f} {sk.foot_y:.1f} "
        f"Q {x(-heel_w):.1f} {sk.foot_y:.1f} {x(-heel_w):.1f} {sk.foot_y - r:.1f} "
        f'Z" fill="{shade(color, 0.7)}" />'
    )
    # Turned cuff at the top of the shaft, the one line that says "boot" rather
    # than "sock".
    parts.append(
        f'<line x1="{cx - shaft_w:.1f}" y1="{top_y + (sk.ankle_y - top_y) * 0.3:.1f}" '
        f'x2="{cx + shaft_w:.1f}" y2="{top_y + (sk.ankle_y - top_y) * 0.3:.1f}" '
        f'stroke="{shade(color, 0.7)}" stroke-width="{max(1.0, _stroke_w(sk) * 0.6):.1f}" />'
    )
    # Cross-laces down the instep, between the cuff and the sole. Dark tone of
    # the boot's own leather, thin: they divide a surface, they do not bound one.
    lace_color = shade(color, 0.45)
    lace_w = shaft_w * 0.52
    lace_top = top_y + (sk.ankle_y - top_y) * 0.45
    lace_bot = instep_y + foot_h * 0.16
    lace_sw = max(1.0, _stroke_w(sk) * 0.4)
    steps = 3
    dy = (lace_bot - lace_top) / steps
    for i in range(steps):
        y0 = lace_top + i * dy
        for s in (-1, 1):
            parts.append(
                f'<line x1="{cx - s * lace_w:.1f}" y1="{y0:.1f}" x2="{cx + s * lace_w:.1f}" y2="{y0 + dy:.1f}" '
                f'stroke="{lace_color}" stroke-width="{lace_sw:.1f}" stroke-linecap="round" />'
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
        f'rx="{h * 0.18:.1f}" fill="{color}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'
    ]
    if p.shaded:
        parts.append(
            f'<rect x="{cx - half_w:.1f}" y="{y + h * 0.62:.1f}" width="{half_w * 2:.1f}" height="{h * 0.38:.1f}" '
            f'rx="{h * 0.18:.1f}" fill="{shade(color)}" opacity="0.8" />'
        )
    if p.outfit.apron_color is None:
        # A buckle, but only where an apron does not hang over the belt's
        # centre: with one there the buckle sits under the panel, which is why
        # the canon shows Satoshi's and not chibi Satoko's. Metal is a fixed
        # neutral tone, like the blush: it is not anyone's palette.
        sw = _stroke_w(sk)
        bw, bh = h * 1.5, h * 1.08
        bx, by = cx - bw / 2, y + (h - bh) / 2
        inset = h * 0.26
        parts.append(
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="{bh * 0.22:.1f}" '
            f'fill="#8a8578" stroke="{OUTLINE}" stroke-width="{sw * 0.85:.1f}" />'
        )
        parts.append(
            f'<rect x="{bx + inset:.1f}" y="{by + inset:.1f}" width="{bw - inset * 2:.1f}" '
            f'height="{bh - inset * 2:.1f}" rx="{bh * 0.10:.1f}" fill="{shade(color, 0.7)}" />'
        )
        parts.append(
            f'<line x1="{cx:.1f}" y1="{by:.1f}" x2="{cx:.1f}" y2="{by + bh * 0.55:.1f}" '
            f'stroke="{OUTLINE}" stroke-width="{sw * 0.5:.1f}" stroke-linecap="round" />'
        )
    return "".join(parts)


def _pouches(sk: Skeleton, p: CharacterParams) -> str:
    """A pouch on each hip, hanging from the belt band over whatever sits
    under it. Body, flap and button are three flat tones off one color, the
    same recipe as everything else. Drawn after the belt and apron so it
    hangs in front of both, and before the arms so a hand can hang over it,
    which is exactly how the canon stacks them.
    """
    color = p.outfit.pouch_color
    if color is None or p.outfit.belt_color is None:
        return ""
    cx = sk.head_cx
    sw = _stroke_w(sk)
    belt_h = (sk.hip_y - sk.waist_y) * 0.42
    belt_y = sk.waist_y - belt_h * 0.35
    # Sized off the head, not the band: the chibi's band is a sliver while its
    # canon pouch is nearly half a head radius, so a band-relative pouch
    # vanishes exactly where the canon makes it loudest.
    h = sk.head_r * (0.30 + 0.16 * sk.build)
    w = h * 0.95
    top = belt_y + belt_h * 0.55
    r = w * 0.18
    # How far out the pouches hang rides the build: a chibi's arms are thick
    # and hang right over the band's outer ends, so pouches there disappear
    # behind them. The canon tucks the chibi's pouches inboard, flanking the
    # apron, and lets the adult's sit out at the band's ends.
    x_frac = 0.52 + 0.22 * sk.build
    parts = []
    for side in (-1, 1):
        x = cx + side * sk.waist_half_w * x_frac - w / 2
        parts.append(
            f'<rect x="{x:.1f}" y="{top:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r:.1f}" '
            f'fill="{color}" stroke="{OUTLINE}" stroke-width="{sw * 0.85:.1f}" />'
        )
        flap_h = h * 0.44
        parts.append(
            f'<rect x="{x:.1f}" y="{top:.1f}" width="{w:.1f}" height="{flap_h:.1f}" rx="{r:.1f}" '
            f'fill="{shade(color, 0.82)}" stroke="{OUTLINE}" stroke-width="{sw * 0.85:.1f}" />'
        )
        parts.append(
            f'<circle cx="{x + w / 2:.1f}" cy="{top + flap_h:.1f}" r="{w * 0.10:.1f}" '
            f'fill="{shade(color, 0.5)}" />'
        )
    return "".join(parts)


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
    return anchors[0], [
        (controls[i], anchors[(i + 1) % _HEAD_SEGMENTS]) for i in range(_HEAD_SEGMENTS)
    ]


def _head(sk: Skeleton, p: CharacterParams) -> str:
    """The face is deliberately the one flat surface on the figure.

    A shadow down the far cheek is what the cel-shaded look would call for, and
    it was tried, but at this level of simplification it reads as a smudge or a
    dirty mark rather than as a turn away from the light: there is no nose or
    brow ridge for it to fall off, so it has nothing to explain it. The hair
    already darkens one side of the head, which is enough.
    """
    start, segments = _head_shape(sk.build)
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    fill = _curve(cx, cy, r, start, segments)
    parts = [f'<path d="{fill}" fill="{p.skin_tone}" />']

    # The outline is drawn in two weights rather than as one closed stroke. Around
    # the skull and cheeks it is silhouette, so it carries full weight. Under the
    # chin it is not: the throat stands in front of the underside of the jaw, so a
    # full-weight line there reads as the whole jaw seen edge-on instead of as the
    # front of it. Splitting at the two lower corners of the shape is what lets
    # the same point data carry both.
    anchors = [start] + [end for _, end in segments]
    chin_from, chin_to = 3, 5  # the two segments either side of the chin
    silhouette = _curve(
        cx, cy, r, anchors[chin_to], segments[chin_to:] + segments[:chin_from], close=False
    )
    under_chin = _curve(cx, cy, r, anchors[chin_from], segments[chin_from:chin_to], close=False)
    sw = _stroke_w(sk)
    parts.append(
        f'<path d="{silhouette}" fill="none" stroke="{OUTLINE}" stroke-width="{sw:.1f}" '
        f'stroke-linecap="round" />'
    )
    parts.append(
        f'<path d="{under_chin}" fill="none" stroke="{OUTLINE}" stroke-width="{sw * 0.6:.1f}" '
        f'stroke-linecap="round" />'
    )
    return "".join(parts)


# How wide the aperture runs against its own height, shared by every character
# so `FaceStyle.eye_width` stays what it says it is: one character's deviation
# from the house eye, not the house eye itself. At 1.0 this is a no-op and
# `eye_width` alone decides the shape, which is how it used to work.
#
# The canon eye is a wide almond and ours was nearly circular: measured on the
# chibi, aperture width against height came to 1.12 where the canon draws 1.51.
# 1.28 here lands the aperture's width on the canon's to within a pixel, 0.1137
# of figure height against 0.111. It is a shared number rather than a bigger
# `eye_width` per preset because the roundness was the house shape's, not either
# character's, and the two presets' values differ from each other on purpose.
#
# The aspect still comes out at 1.41 rather than 1.51, because the canon's
# aperture is also about a tenth shorter than ours. That part lives in
# `eye_openness` and `eye_lower_lid`, which are per-character expression values
# the owner set deliberately, so it is left alone rather than tuned to a ratio.
_EYE_ASPECT = 1.28


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
    w = er * f.eye_width * _EYE_ASPECT
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
    d = (
        lid
        + f" Q {pt(ctrl(outer, base, bot))} {pt(base)} Q {pt(ctrl(inner, base, bot))} {pt(inner)} Z"
    )
    return d, lid


def _eye(ex: float, ey: float, er: float, side: int, p: CharacterParams, sw: float) -> str:
    f = p.face
    d, lid = _eye_shape(ex, ey, er, side, f)
    clip_id = f"eye-{'l' if side < 0 else 'r'}"

    # Size the iris off whichever half-axis of the aperture is smaller, so a
    # narrow or half-lidded eye keeps white at its corners instead of filling
    # solid with color. Everything inside the eye is placed off the iris, and
    # the iris off the aperture's own center. It rides high in the aperture:
    # the canon tucks the iris up under the lash line, and white showing above
    # it reads as a startled stare rather than a resting gaze.
    iris_r = f.iris_size * min(er * f.eye_width, er * (f.eye_openness + f.eye_lower_lid) / 2)
    iris_cy = ey + er * (f.eye_lower_lid - f.eye_openness) / 2 - iris_r * 0.10

    # Still clipped to the aperture, so a low lid crops the iris rather than
    # letting it hang over the lash line.
    parts = [f'<defs><clipPath id="{clip_id}"><path d="{d}" /></clipPath></defs>']
    parts.append(f'<path d="{d}" fill="white" stroke="{OUTLINE}" stroke-width="{sw * 0.85:.1f}" />')
    parts.append(f'<g clip-path="url(#{clip_id})">')
    # Canon iris: a rim of the eye color's own darker tone around the color,
    # with a distinct near-dark pupil inside that. Three flat tones, which is
    # what makes the eye read at a glance where a single disc read as a bead.
    parts.append(
        f'<circle cx="{ex:.1f}" cy="{iris_cy:.1f}" r="{iris_r:.1f}" fill="{shade(p.eye_color, 0.45)}" />'
    )
    parts.append(
        f'<circle cx="{ex:.1f}" cy="{iris_cy:.1f}" r="{iris_r * 0.84:.1f}" fill="{p.eye_color}" />'
    )
    parts.append(
        f'<circle cx="{ex:.1f}" cy="{iris_cy + iris_r * 0.10:.1f}" r="{iris_r * 0.40:.1f}" '
        f'fill="{shade(p.eye_color, 0.18)}" />'
    )
    parts.append(
        f'<circle cx="{ex - iris_r * 0.42:.1f}" cy="{iris_cy - iris_r * 0.48:.1f}" r="{iris_r * 0.34:.1f}" fill="white" />'
    )
    parts.append(
        f'<circle cx="{ex + iris_r * 0.35:.1f}" cy="{iris_cy + iris_r * 0.42:.1f}" r="{iris_r * 0.16:.1f}" '
        f'fill="white" opacity="0.85" />'
    )
    parts.append("</g>")
    # The upper lash line carries more weight than the rest of the outline,
    # noticeably so: it is the heaviest line on the figure, which is the one
    # thing every anime eye construction agrees on and what the canon leans on.
    parts.append(
        f'<path d="{lid}" fill="none" stroke="{OUTLINE}" stroke-width="{sw * 1.6:.1f}" stroke-linecap="round" />'
    )
    return "".join(parts)


def _scar(sk: Skeleton, side: int) -> str:
    """A nick with a short cross-tick on one cheek. One line alone reads as a
    stray stroke at this size; two equal lines read as a cartoon X, so the
    tick is kept short."""
    r, cx, cy = sk.head_r, sk.head_cx, sk.head_cy
    sw = _stroke_w(sk)

    def line(x1: float, y1: float, x2: float, y2: float, w: float) -> str:
        return (
            f'<line x1="{cx + side * r * x1:.1f}" y1="{cy + r * y1:.1f}" '
            f'x2="{cx + side * r * x2:.1f}" y2="{cy + r * y2:.1f}" '
            f'stroke="{OUTLINE}" stroke-width="{w:.1f}" stroke-linecap="round" opacity="0.6" />'
        )

    return line(0.52, 0.56, 0.65, 0.35, sw * 0.6) + line(0.55, 0.44, 0.63, 0.49, sw * 0.45)


def _face(sk: Skeleton, p: CharacterParams) -> str:
    r = sk.head_r
    cx, cy = sk.head_cx, sk.head_cy
    f = p.face
    # The canon lids the adult eye: ref/satoko-real.jpg draws an almond where
    # the chibi gets a round-open aperture, on the same character. Riding the
    # lids on the build keeps that one construction, so a preset states its
    # chibi eye and the taller build derives its own.
    if sk.build > 0:
        f = replace(
            f,
            eye_openness=f.eye_openness * (1.0 - 0.20 * sk.build),
            eye_lower_lid=f.eye_lower_lid * (1.0 - 0.10 * sk.build),
        )
    # Canon face geometry, shared by every character; what differs per
    # character stays in FaceStyle. Eyes sit below the head's centre line and
    # well apart (the canon puts them at about half the face's half-width,
    # where they used to crowd the middle), and shrink relative to the head
    # as the build climbs: the canon draws the realistic iris about a quarter
    # smaller against the head than the chibi's, which is how an adult face
    # avoids going saucer-eyed while the chibi stays big-eyed.
    eye_y = cy + r * 0.16
    eye_dx = r * 0.46
    eye_r = r * 0.26 * (1.0 - 0.22 * sk.build) * f.eye_size
    sw = _stroke_w(sk)
    # Brows are hair, so they carry the hair's own darker tone rather than the
    # outline color. On dark hair the difference vanishes, which is correct.
    # 0.45 rather than a softer tint because the brows are what carry
    # expression now the eyes stay open: too faint and the face goes blank.
    brow_color = shade(p.hair_color, 0.45)
    parts = []

    for side in (-1, 1):
        ex = cx + side * eye_dx
        # Just above the lash line, nearly touching it. The canon's sternness
        # lives in that closeness: a brow floating high off the eye reads as
        # mild surprise whatever its tilt says.
        brow_y = eye_y - eye_r * 1.30
        tilt = f.brow_tilt * eye_r * 0.28
        parts.append(
            f'<line x1="{ex - side * eye_r:.1f}" y1="{brow_y + tilt:.1f}" '
            f'x2="{ex + side * eye_r:.1f}" y2="{brow_y - tilt:.1f}" '
            f'stroke="{brow_color}" stroke-width="{sw * f.brow_weight:.1f}" stroke-linecap="round" />'
        )
        parts.append(_eye(ex, eye_y, eye_r, side, p, sw))

    if sk.build > 0.5:
        # A nose, one short stroke leaning off to the left, only at builds
        # where the face has room for it. The chibi face reads through eyes
        # and mouth alone, which is why the canon chibi draws none either.
        nose_y = cy + r * 0.36
        nose_len = r * 0.09 * sk.build
        parts.append(
            f'<path d="M {cx + r * 0.012:.1f} {nose_y - nose_len:.1f} '
            f'Q {cx - r * 0.020:.1f} {nose_y - nose_len * 0.3:.1f} {cx - r * 0.028:.1f} {nose_y:.1f}" '
            f'fill="none" stroke="{OUTLINE}" stroke-width="{sw * 0.45:.1f}" opacity="0.75" stroke-linecap="round" />'
        )

    mouth_y = cy + r * 0.55
    mouth_half = r * 0.12 * f.mouth_width
    parts.append(
        f'<path d="M {cx - mouth_half:.1f} {mouth_y:.1f} '
        f'Q {cx:.1f} {mouth_y + r * 0.08 * f.mouth_curve:.1f} {cx + mouth_half:.1f} {mouth_y:.1f}" '
        f'fill="none" stroke="{OUTLINE}" stroke-width="{sw * 0.85:.1f}" stroke-linecap="round" />'
    )

    if f.blush > 0:
        for side in (-1, 1):
            # Below and outside the eyes, which sit lower than they used to;
            # at the old height the blush clipped under the lower lids.
            bx = cx + side * r * 0.58
            by = cy + r * 0.44
            parts.append(
                f'<ellipse cx="{bx:.1f}" cy="{by:.1f}" rx="{r * 0.16:.1f}" ry="{r * 0.09:.1f}" '
                f'fill="#e8879a" opacity="{0.45 * f.blush:.2f}" />'
            )

    if f.scar_side:
        parts.append(_scar(sk, 1 if f.scar_side > 0 else -1))

    return "".join(parts)


def _hair_front(sk: Skeleton, p: CharacterParams) -> str:
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    sw = _stroke_w(sk)

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
        f'<path d="{line_d}" fill="none" stroke="{OUTLINE}" stroke-width="{sw:.1f}" '
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
            f'<path d="{edge_d}" fill="none" stroke="{OUTLINE}" stroke-width="{sw:.1f}" '
            f'stroke-linecap="round" />'
        )
    # Interior strands last, so they sit over the fill and the hairline both.
    # Lighter than the silhouette, the same relation the jaw line has to the head
    # outline: these divide one surface, they do not bound it.
    if style.strands is not None:
        for s_start, s_segments in style.strands(fall):
            s_d = _curve(cx, cy, r, s_start, s_segments, close=False)
            parts.append(
                f'<path d="{s_d}" fill="none" stroke="{OUTLINE}" stroke-width="{sw * 0.55:.1f}" '
                f'stroke-linecap="round" clip-path="url(#{_HAIR_FRONT_CLIP_ID})" />'
            )
    return "".join(parts)


def render_character(p: CharacterParams | None = None, sk: Skeleton | None = None) -> str:
    """Draw one character and return the whole SVG document as a string.

    `p` carries what the character *is* (colours, garments, face, haircut) and
    `sk` what its proportions are. Passing no skeleton builds one from `p.heads`
    and `p.frame`, which is the common case; passing one is how the same
    character is rendered at another build, or on a canvas of another size:

        render_character(PRESETS["satoko"])
        render_character(PRESETS["satoko"], build_skeleton(heads=BUILDS["realistic"]))

    Nothing is written to disk and nothing is rasterized here. The document is
    deterministic: the same arguments give the same bytes, which is what lets
    `ref-out/` be compared rather than eyeballed.
    """
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
        _pouches(sk, p),
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
