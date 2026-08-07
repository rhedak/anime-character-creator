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
    # Tunic tucked in at the belt rather than hanging over it: the tunic's hem
    # stops inside the belt band and whatever is worn below rises to meet it, so
    # the belt is the boundary between the two garments. Both Satoshi
    # references wear it this way, with the tunic's green ending above the
    # belt's lower edge rather than below it. One flag moves both garments,
    # which is the point: they have to agree on the line they meet at, and the
    # belt is only wide enough to hide a disagreement of a few pixels.
    tunic_tucked: bool = False


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


def _mirrored(edge: tuple[Point, list[Segment]]) -> list[tuple[Point, list[Segment]]]:
    """Both sides of a symmetric cut's lock edge, right first.

    Ordered, never a set: `ref-out/` is compared byte for byte, so the order
    these come out in has to be the order they went in.
    """
    return [edge, _mirror(*edge)]


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


def _hair_tip_edge(length: float) -> list[tuple[Point, list[Segment]]]:
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
    # One region, because this cut's locks all hang the same way: a wave across
    # them is already a per-lock boundary, near enough. A cut whose locks point in
    # different directions returns one region each instead.
    return [
        (
            (-1.90, hi(0.045)),
            [
                ((-1.60, lo(0.075)), (-1.24, hi(0.040))),
                ((-0.98, lo(0.080)), (-0.72, hi(0.050))),
                ((-0.48, lo(0.070)), (-0.24, hi(0.040))),
                ((0.00, lo(0.085)), (0.24, hi(0.040))),
                ((0.48, lo(0.070)), (0.72, hi(0.050))),
                ((0.98, lo(0.080)), (1.24, hi(0.040))),
                ((1.60, lo(0.075)), (1.90, hi(0.045))),
                ((1.90, floor * 0.6), (1.90, floor)),
                ((0.00, floor), (-1.90, floor)),
            ],
        )
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


def _short_tip_edge(tip: float) -> list[tuple[Point, list[Segment]]]:
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
    return [
        (
            (-1.90, mid - 0.10),
            [
                ((-1.58, mid + 0.06), (-1.30, mid - 0.04)),
                ((-1.06, mid + 0.10), (-0.86, mid - 0.02)),
                ((-0.55, mid + 0.10), (-0.30, mid)),
                ((0.00, mid + 0.12), (0.30, mid)),
                ((0.55, mid + 0.10), (0.86, mid - 0.02)),
                ((1.06, mid + 0.10), (1.30, mid - 0.04)),
                ((1.58, mid + 0.06), (1.90, mid - 0.10)),
                ((1.90, floor * 0.6), (1.90, floor)),
                ((0.00, floor), (-1.90, floor)),
            ],
        )
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


# Satoko's traced cut.
#
# Both boundaries come off `ref/satoko-chibi-hair.png`, her hair cut out of the
# chibi reference by the owner, and the signal is **the drawn black outline**
# rather than the crop's alpha. The alpha is a rough selection: some of the page
# came through opaque and the face opening's edge is a staircase. The ink is the
# artist's own line and is exact wherever the selection is not.
#
# Reading ink works on a crop of the hair alone and does not on a whole face,
# because brows and eyes are the only other dark things on one. Here the
# furthest ink along a bearing is the mass and the nearest is the hairline, with
# nothing between them that could be either. `out/trace/satoko.py` carries it,
# and the crop places back into the reference at a mean squared error of 1.
#
# 18 and 8 segments: the finest levels with no edge under two stroke widths at
# either build, the same bound the other traced cuts were chosen on.
_LONG_EDGE_START: Point = (-0.782, 1.677)
_LONG_EDGE: list[Segment] = [
    ((-0.933, 1.651), (-1.050, 1.557)),
    ((-1.165, 1.666), (-1.171, 1.612)),
    ((-1.250, 1.572), (-1.306, 1.502)),
    ((-1.362, 1.434), (-1.388, 1.341)),
    ((-1.283, 0.169), (-1.232, -0.307)),
    ((-1.183, -0.490), (-1.094, -0.657)),
    ((-0.997, -0.821), (-0.858, -0.953)),
    ((-0.721, -1.070), (-0.561, -1.150)),
    ((-0.342, -1.242), (-0.109, -1.251)),
    ((0.140, -1.229), (0.386, -1.187)),
    ((0.556, -1.141), (0.701, -1.040)),
    ((0.878, -0.907), (1.002, -0.728)),
    ((1.128, -0.525), (1.186, -0.296)),
    ((1.230, 0.160), (1.338, 1.338)),
    ((1.314, 1.432), (1.260, 1.501)),
    ((1.199, 1.562), (1.127, 1.609)),
    ((1.126, 1.670), (1.006, 1.550)),
    ((0.883, 1.665), (0.710, 1.672)),
]
_LONG_LINE_START: Point = (-0.767, 1.674)
_LONG_LINE: list[Segment] = [
    ((-0.881, 1.265), (-0.927, 0.794)),
    ((-0.936, 0.396), (-0.884, -0.000)),
    ((-0.588, -0.091), (-0.315, -0.237)),
    ((-0.083, -0.378), (0.103, -0.587)),
    ((0.237, -0.364), (0.440, -0.205)),
    ((0.624, -0.074), (0.838, 0.015)),
    ((0.886, 0.371), (0.881, 0.724)),
    ((0.876, 0.756), (0.785, 0.756)),
    ((0.877, 0.756), (0.877, 0.792)),
    ((0.828, 1.275), (0.716, 1.676)),
]
# How far above the mass's own lower edge the gold gives way to the pale tips.
# Larger than the crop's because these are falls rather than blades: the tips
# run a long way and the canon turns them pale over roughly their last third.
_LONG_BASE_TIP = 1.677
_LONG_TONE_LIFT = 0.62
# How far inside the silhouette the front hair's fill boundary is pulled.
_LONG_FILL_INSET = 0.05
# How far the hairline's two ends are pulled toward the centre, in head radii.
_LONG_LINE_TUCK = 0.04
# Which segment ends on the crown's apex, so the two sides can be taken apart.
_LONG_CROWN_AT = 9


def _long_scaled(fall: float) -> tuple[Point, list[Segment]]:
    """The traced contour with its fall stretched to `fall`, its crown left alone.

    A long cut does not scale as one piece, and the contract already says so:
    above the cheek line hair is pinned to the skull, below it the points are a
    fraction of the way down to the tips. So only y below `_HAIR_CHEEK_Y` is
    remapped, and x is left as traced, because a fall that hangs further does not
    also hang wider.

    Scaling the whole contour was tried and is wrong twice over. It carries the
    crown up with the tips, which at the adult build puts it past the canvas
    ceiling; and it needs a head-relative `tip_range` to stay inside that, which
    stops a long cut lengthening with the body at all. That is the thing the
    body-relative branch of `_hair_fall` exists for.
    """
    span = _LONG_BASE_TIP - _HAIR_CHEEK_Y
    k = (fall - _HAIR_CHEEK_Y) / span if span else 1.0

    def q(pt: Point) -> Point:
        y = pt[1]
        return (pt[0], _HAIR_CHEEK_Y + (y - _HAIR_CHEEK_Y) * k) if y > _HAIR_CHEEK_Y else pt

    return q(_LONG_EDGE_START), [(q(c), q(e)) for c, e in _LONG_EDGE]


def _long_line(fall: float) -> tuple[Point, list[Segment]]:
    """The traced hairline, with the stretch that the falls get and the face does
    not: above the cheek line it is pinned to the head, below it it rides the
    fall down."""
    span = _LONG_BASE_TIP - _HAIR_CHEEK_Y
    k = (fall - _HAIR_CHEEK_Y) / span if span else 1.0

    def q(pt: Point) -> Point:
        y = pt[1]
        return (pt[0], _HAIR_CHEEK_Y + (y - _HAIR_CHEEK_Y) * k) if y > _HAIR_CHEEK_Y else pt

    line = [(q(c), q(e)) for c, e in _LONG_LINE]
    # The two ends are tucked toward the centre. At a fall's bottom tip the inner
    # and outer edges of the hair converge, so the traced hairline's last point
    # and the traced mass's last point are within a stroke of each other, and the
    # fit can put the inner one a hair outside. This keeps the fill inside the
    # silhouette without moving anything a viewer can see.
    start = (q(_LONG_LINE_START)[0] + _LONG_LINE_TUCK, q(_LONG_LINE_START)[1])
    ctrl, end = line[-1]
    line[-1] = (ctrl, (end[0] - _LONG_LINE_TUCK, end[1]))
    return start, line


def _long_traced_mass(fall: float) -> tuple[Point, list[Segment]]:
    """The whole silhouette, closed behind the shoulders where it is never seen."""
    start, edge = _long_scaled(fall)
    end = edge[-1][1]
    return start, [*edge, (((end[0] + start[0]) / 2, max(end[1], start[1]) + 0.16), start)]


def _long_traced_fall_edge(fall: float) -> list[tuple[Point, list[Segment]]]:
    """Both sides of the outline, each from its tip up to the crown. Taken out of
    the mass's own points rather than restated, and given per side rather than
    mirrored, since nothing here promises the trace is symmetric."""
    start, edge = _long_scaled(fall)
    return [
        _reverse(edge[_LONG_CROWN_AT][1], edge[_LONG_CROWN_AT + 1 :]),
        (start, edge[: _LONG_CROWN_AT + 1]),
    ]


def _long_traced_hairline(fall: float) -> tuple[Point, list[Segment], list[Segment]]:
    """Her parting, and the line down the inside of each fall.

    That second part is the whole of what a viewer reads as hair lying in front
    of the shoulder rather than behind it, and the first version of this cut did
    not have it: the inner boundary was traced by sweeping bearings from the head
    centre, and below the cheek a fall runs almost straight down, so a whole
    fall's worth of it fell between two bearings. `out/trace/satoko.py` scans rows
    there instead and the two readings agree where they meet, both being the same
    drawn line.

    `back` closes the fill on the mass's own contour, so the front hair covers
    exactly the band between the hairline and the silhouette, which is what the
    hair *is*. The two short connectors across each fall's bottom are the only
    invented geometry here.
    """
    start, edge = _long_scaled(fall)
    hs, hg = _long_line(fall)
    end = hg[-1][1]
    mass_start, mass_back = _reverse(start, edge)
    inset = 1.0 - _LONG_FILL_INSET
    # Straight chords, not bowed ones: a control placed off the line between two
    # points on the silhouette can leave it, which at a fall's bottom tip put the
    # fill 0.010 head radii outside its own outline.
    back: list[Segment] = [
        (((end[0] + mass_start[0]) / 2, (end[1] + mass_start[1]) / 2), mass_start)
    ]
    back += [
        ((c[0] * inset, c[1] * inset), (e[0] * inset, e[1] * inset)) for c, e in mass_back[:-1]
    ]
    last = mass_back[-1][1]
    back.append((((last[0] + hs[0]) / 2, (last[1] + hs[1]) / 2), hs))
    return hs, hg, back


def _long_traced_tip_edge(fall: float) -> list[tuple[Point, list[Segment]]]:
    """Where the falls turn pale: the mass's own edge, lifted, but never above the
    half-way line.

    Two rules, and the second is what a long cut needs that a crop does not. The
    lift is the crop's trick: a uniform lift over an edge whose tips end at
    different depths leaves every tip pale from a fixed distance above its own
    point, so the pale follows the hair instead of cutting a level line across it.
    The clamp then holds the boundary at `_fade_y`'s half-and-half height wherever
    the lifted edge would climb above it, which is everywhere but the two falls.
    Without it the lift carries on over the crown and turns the whole head pale.

    A first version took only the segments lying below the head centre, which is
    not a contiguous run, and left a gold wedge poking into the pale at the foot
    of each fall.
    """
    v = fall / _LONG_BASE_TIP
    start, edge = _long_scaled(fall)
    lift = _LONG_TONE_LIFT * v
    top = min(e[1] for _, e in edge)
    bottom = max(e[1] for _, e in edge)
    fade = _fade_y(top, bottom)
    floor = bottom + 1.0
    wide = max(abs(e[0]) for _, e in edge) + 0.25

    # The contour, sampled and pushed up, then held at the fade line.
    pts: list[Point] = []
    prev = start
    for ctrl, end in edge:
        for i in range(1, 7):
            t = i / 6
            x = (1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * ctrl[0] + t**2 * end[0]
            y = (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * ctrl[1] + t**2 * end[1]
            pts.append((x, max(y - lift, fade)))
        prev = end

    chain: list[Segment] = []
    here: Point = (-wide, fade)
    for q in [*pts, (wide, fade), (wide, floor), (-wide, floor), (-wide, fade)]:
        chain.append((((here[0] + q[0]) / 2, (here[1] + q[1]) / 2), q))
        here = q
    return [((-wide, fade), chain)]


def _long_traced_strands(fall: float) -> list[tuple[Point, list[Segment]]]:
    """The two sweep lines the canon draws off the parting, and one down each
    fall. They scale with the mass, since they live on it."""
    v = fall / _LONG_BASE_TIP
    out = []
    for x0, y0, cx0, cy0, x1, y1 in (
        (-0.30, -0.72, -0.62, -0.42, -0.86, -0.05),
        (0.34, -0.74, 0.66, -0.44, 0.90, -0.08),
    ):
        out.append(((x0, y0), [((cx0, cy0), (x1, y1))]))
    for side in (-1, 1):
        out.append(
            (
                (side * 1.02 * v, 0.10 * v),
                [((side * 1.10 * v, 0.70 * v), (side * 1.06 * v, 1.30 * v))],
            )
        )
    return out


# Satoshi's traced crop.
#
# The outline here is not authored, it is measured. `out/trace/` pulls the canon's
# hair silhouette off `ref/satoshi-real.jpg` as a radius per bearing in head-radius
# units, simplifies it with Douglas-Peucker and least-squares fits one control
# point per span, which is exact for a quadratic with its endpoints pinned. So
# these numbers are the canon's own contour rather than anyone's idea of it, and
# the way to change them is to re-trace rather than to nudge.
#
# 26 segments because that is the finest level whose every edge is at least two
# stroke widths long. Below it the fit is more faithful on paper and worse on the
# page: `_stroke_w` is figure-relative, so a feature shorter than the line that
# draws it closes up, and no amount of rendering bigger helps. See
# `docs/gap-analysis.md` gap 1 and the PITFALLS entry in the gap-analysis skill.
#
# The contour is asymmetric because the canon's is. Nothing here mirrors, which
# the contract has always allowed and no cut had used.
_CROP_START: Point = (-0.706, 0.872)
_CROP_EDGE: list[Segment] = [
    ((-0.751, 0.829), (-0.687, 0.687)),
    ((-0.837, 0.784), (-0.869, 0.756)),
    ((-0.798, 0.522), (-0.839, 0.428)),
    ((-1.071, 0.514), (-1.062, 0.473)),
    ((-0.938, 0.293), (-0.949, 0.202)),
    ((-0.984, 0.159), (-1.112, 0.117)),
    ((-1.009, 0.049), (-0.990, -0.000)),
    ((-1.105, -0.110), (-1.070, -0.227)),
    ((-1.040, -0.452), (-0.899, -0.630)),
    ((-1.119, -0.811), (-1.069, -0.805)),
    ((-0.886, -0.809), (-0.798, -0.856)),
    ((-0.596, -1.027), (-0.351, -1.149)),
    ((-0.200, -1.199), (-0.042, -1.189)),
    ((-0.003, -1.374), (0.045, -1.301)),
    ((0.238, -1.296), (0.360, -1.109)),
    ((0.551, -1.176), (0.707, -1.089)),
    ((0.780, -1.109), (0.714, -0.947)),
    ((0.900, -0.712), (1.172, -0.474)),
    ((1.213, -0.464), (1.011, -0.368)),
    ((1.018, -0.188), (1.152, -0.000)),
    ((1.233, 0.023), (0.989, 0.035)),
    ((0.949, 0.190), (1.092, 0.463)),
    ((1.124, 0.515), (0.890, 0.434)),
    ((0.839, 0.530), (0.907, 0.761)),
    ((0.902, 0.801), (0.727, 0.678)),
    ((0.797, 0.836), (0.724, 0.863)),
]

# Which segment ends on the crown's apex, so the two sides can be taken apart.
_CROP_CROWN_AT = 13
# Which segments end on the temple either side, where the fringe meets the
# silhouette. Both sit above the ear's top at 0.03, which is what leaves the ear
# somewhere to be seen; move them down and the front hair swallows it again.
_CROP_TEMPLE_L = 7
_CROP_TEMPLE_R = 19
# The lowest point of the trace as measured, which is what `fall` scales against:
# a cut whose tips reach `fall` is the trace at `fall / _CROP_BASE_TIP`.
_CROP_BASE_TIP = 0.872
# The fringe, traced off `ref/satoshi-chibi-fringe.png`: the canon's fringe cut
# out of the chibi reference by the owner, background removed.
#
# That crop is what made this measurable. Five readings off the full drawing all
# failed and each failed differently, because the canon's pale tips sit
# colorimetrically between its gold and its skin, so no threshold puts all three
# on the right side of it. What the crop changes is not its alpha, which is a
# coarse outer selection with the gaps between blades left opaque, but what it
# leaves out: no brows and no eyes. On the full drawing the deepest ink in a
# column is the brow, which is why reading the drawn line found eyebrows. In the
# crop the deepest ink can only be the blade that made it.
#
# The crop is placed back in the reference by template match rather than by an
# eyeballed offset, and matches to a mean squared error of 1, so the calibration
# is the reference's own. `out/trace/fringe3.py` carries it.
#
# Fixed rather than scaled by the build: the mass grows and the fringe does not,
# because it sits on a brow that has not moved.
_CROP_FRINGE_START: Point = (-1.039, -0.181)
_CROP_FRINGE: list[Segment] = [
    ((-0.924, -0.200), (-0.817, -0.215)),
    ((-0.741, -0.290), (-0.641, -0.356)),
    ((-0.641, -0.237), (-0.624, -0.237)),
    ((-0.435, -0.272), (-0.278, -0.385)),
    ((-0.275, -0.288), (-0.272, -0.192)),
    ((-0.080, -0.219), (0.068, -0.351)),
    ((0.068, -0.249), (0.080, -0.249)),
    ((0.193, -0.291), (0.289, -0.374)),
    ((0.397, -0.477), (0.448, -0.618)),
    ((0.512, -0.439), (0.653, -0.311)),
    ((0.711, -0.271), (0.772, -0.237)),
    ((0.783, -0.237), (0.783, -0.356)),
    ((0.812, -0.328), (0.840, -0.300)),
    ((0.885, -0.215), (0.885, -0.112)),
    ((0.919, -0.112), (0.919, -0.243)),
    ((0.985, -0.204), (1.061, -0.186)),
]
_CROP_NOTCHES: list[Point] = [
    (-0.641, -0.356),
    (-0.278, -0.385),
    (0.068, -0.351),
    (0.448, -0.618),
    (0.783, -0.356),
    (0.919, -0.243),
]
# How far inside the silhouette the front hair's own fill boundary is pulled,
# in fractions of the radius. It only ever has to be enough that the fill cannot
# cross the outline between two traced points; the mass paints the strip left
# over in the same colour, so nothing shows.
_CROP_FILL_INSET = 0.06
# How far above the fringe's own edge the gold gives way to the pale tips, in
# head radii. The blades run about 0.5 from notch to tip, so this is roughly how
# much of each blade comes out pale.
_CROP_TONE_LIFT = 0.26
# How far the lock divisions lean off vertical, and how far they run up from
# their notch. Short: a division marks a join, it does not have to travel, and
# full-length ones hang off the fringe as a curtain of needles.
_CROP_SWEEP = 0.06
_CROP_STRAND_RUN = 0.34


def _crop_outline(fall: float) -> tuple[Point, list[Segment]]:
    """The traced contour at the size this build wants, left tip round to right.

    One scalar carries the whole build difference, and that is a measurement
    rather than a convenience: the canon's chibi contour over its adult one is
    1.32 across the crown with a standard deviation of 0.008, and stays near 1.23
    even down at the jaw where the shoulders make the reading worst. A cut that
    needed its proportions to change with the build would not come out that flat.
    """
    v = fall / _CROP_BASE_TIP
    start = (_CROP_START[0] * v, _CROP_START[1] * v)
    return start, [((c[0] * v, c[1] * v), (e[0] * v, e[1] * v)) for c, e in _CROP_EDGE]


def _crop_mass_shape(fall: float) -> tuple[Point, list[Segment]]:
    """The whole silhouette, closed across the nape.

    The closing edge runs behind the neck and the shoulders at every build and is
    never seen, so it is one quadratic rather than a shape. It dips below both
    tips so the join cannot cut the corner off either of them.
    """
    start, edge = _crop_outline(fall)
    end = edge[-1][1]
    nape = ((end[0] + start[0]) / 2, max(end[1], start[1]) + 0.18)
    return start, [*edge, (nape, start)]


def _crop_fall_edge(fall: float) -> list[tuple[Point, list[Segment]]]:
    """Both sides of the outline, each running from its bottom tip to the crown.

    Taken out of the mass's own point data rather than restated, so the two
    cannot drift apart the way the long cut's fall edge did before task 59 pulled
    it into shared constants. Two entries rather than one mirrored, because this
    cut is not symmetric: the canon's is not, and handing back one side let the
    drawing code stamp the right-hand edge onto the left.
    """
    start, edge = _crop_outline(fall)
    return [
        _reverse(edge[_CROP_CROWN_AT][1], edge[_CROP_CROWN_AT + 1 :]),
        (start, edge[: _CROP_CROWN_AT + 1]),
    ]


def _crop_hairline_shape(fall: float) -> tuple[Point, list[Segment], list[Segment]]:
    """The fringe, temple to temple, and nothing else.

    **The front hair stops above the ear on purpose.** The first version ran the
    line all the way down both sides to the mass's bottom tips and closed `back`
    on the mass's whole reversed chain, which meant the front fill covered
    everything the mass covered. Nothing was left for an ear to be seen in: the
    ear reads at the chibi and all but vanishes at the adult, and the fix is not
    to float the ear over the hair but to stop the hair filling the place the
    canon keeps for it.

    Both ends sit on the mass's own outline, at the temple points the trace
    already has, so the stroke still never stops in mid-air.

    The fringe itself is **not traced yet**. These are the overlapping wedge locks
    the short cut settled on, tips dipping toward the brow and notches rising
    about a third of the way back, which is what reads as hair lying over hair
    rather than as a row of teeth. Tracing it is the next step and wants its own
    measurement: the canon's fringe boundary is hair against skin, so it can be
    read off the reference the way the silhouette was.
    """
    _, edge = _crop_outline(fall)
    left_temple = edge[_CROP_TEMPLE_L][1]
    right_temple = edge[_CROP_TEMPLE_R][1]
    lx, ly = _CROP_FRINGE_START
    rx, ry = _CROP_FRINGE[-1][1]
    line: list[Segment] = [
        # out to the temple, past where the forehead ends and the trace with it
        (((left_temple[0] + lx) / 2, ly - 0.10), (lx, ly)),
        *_CROP_FRINGE,
        (((right_temple[0] + rx) / 2, ry - 0.10), right_temple),
    ]
    # Back over the crown, taken off the mass's own points and pulled in a
    # fraction of a radius so it is inside the silhouette at every bearing.
    #
    # This was three hand-picked quadratics for a round and it leaked: written as
    # flat multiples of the scale they sat at a constant radius while the traced
    # crown does not, so between two tips the fill ran outside the outline and
    # painted a smooth gold arc past the spikes. The lesson is the one task 59
    # already paid for on the long cut, that an edge stated twice drifts. Nothing
    # here restates the crown.
    crown = _reverse(edge[_CROP_TEMPLE_L][1], edge[_CROP_TEMPLE_L + 1 : _CROP_TEMPLE_R + 1])[1]
    k = 1.0 - _CROP_FILL_INSET
    back: list[Segment] = [((c[0] * k, c[1] * k), (e[0] * k, e[1] * k)) for c, e in crown]
    # The last end has to be the temple itself, not the pulled-in copy of it, so
    # the fill closes exactly where the fringe's stroke started.
    back[-1] = (back[-1][0], left_temple)
    return left_temple, line, back


def _crop_tip_edge(fall: float) -> list[tuple[Point, list[Segment]]]:
    """Where the crop fades to its tip tone: the fringe's own edge, lifted.

    The same traced chain the fringe is drawn from, moved up by `_CROP_TONE_LIFT`
    and extended out to the mass on both sides. That is the cheap way to get what
    the canon has, and it works for a reason worth stating: a *uniform* lift over
    a boundary whose blades end at different depths leaves every blade pale from a
    fixed distance above its own tip, so the pale sits in the tips and the gold at
    the roots without any of it being stated per lock.

    What it does not reproduce is that the canon varies how far the pale climbs
    from lock to lock. This gives them all the same depth. The bar here is the
    spirit of an edge per lock rather than the canon's own, and one list used
    twice is worth more than a second list that can drift from the first.

    It replaces a single wave at a fixed height, which could only ever say "pale
    below this line" and read as a white liner under a gold cap.
    """
    v = fall / _CROP_BASE_TIP
    lift = _CROP_TONE_LIFT
    edge = 1.35 * v
    floor = fall + 1.5
    sx, sy = _CROP_FRINGE_START
    ex, ey = _CROP_FRINGE[-1][1]
    return [
        (
            (-edge, sy - lift),
            [
                (((-edge + sx) / 2, sy - lift), (sx, sy - lift)),
                *(((c[0], c[1] - lift), (e[0], e[1] - lift)) for c, e in _CROP_FRINGE),
                (((ex + edge) / 2, ey - lift), (edge, ey - lift)),
                ((edge, floor * 0.6), (edge, floor)),
                ((0.0, floor), (-edge, floor)),
            ],
        )
    ]


def _crop_strands(fall: float) -> list[tuple[Point, list[Segment]]]:
    """Lines dividing the crown into locks, each aimed at a notch of the fringe.

    Without them the crown is one field of hair colour, which is what makes a cut
    read as an object the colour of hair rather than as hair. They scale with the
    mass, since they live on it.
    """
    v = fall / _CROP_BASE_TIP
    out: list[tuple[Point, list[Segment]]] = []
    for x, y in _CROP_NOTCHES:
        # Up from a notch of the traced fringe, leaning the way the lock sweeps.
        # One line where two locks meet is what reads as overlap rather than as a
        # gap, which is the thing the canon does and a plain zigzag does not.
        top = (x + _CROP_SWEEP, y - _CROP_STRAND_RUN)
        out.append(((x, y), [(((x + top[0]) / 2 + _CROP_SWEEP * 0.5, (y + top[1]) / 2), top)]))
    # Two long ones over the crown as well, or the top of the head is one field of
    # hair colour and the cut reads as an object rather than as hair.
    for x0, y0, x1, y1 in ((-0.62, -0.72, -1.00, -0.24), (0.70, -0.70, 1.04, -0.22)):
        out.append(
            (
                (x0 * v, y0 * v),
                [(((x0 + x1) / 2 * v, (y0 + y1) / 2 * v), (x1 * v, y1 * v))],
            )
        )
    return out


# Satoshi's tousled crop.
#
# Built from its locks rather than from an outline with texture drawn on it,
# which is what the other two cuts are. The canon crop is a bundle of pointed
# locks, each gold at the root and pale toward its own tip, and the difference
# that makes is structural rather than decorative: one tone boundary running
# level across a whole head can only say "pale below this height", so a cut whose
# locks point in different directions comes out with a band painted across it.
# `tip_edge` returning a region per lock is what this cut needs and what it is
# for.
#
# The fringe is one list of points used three ways: the hairline chains through
# it, the pale wedges are cut from it, and the strand lines aim at its notches.
# Spelling those out separately is what let the old cut's lines drift off its
# own locks.
_TOUSLE_NOTCHES: list[Point] = [
    (-0.98, -0.30),
    (-0.78, -0.52),
    (-0.50, -0.70),
    (-0.16, -0.76),
    (0.20, -0.70),
    (0.56, -0.58),
    (0.86, -0.40),
    (0.98, -0.30),
]
# One per gap in the list above. Deliberately uneven in width, length and
# direction: a row of equal points is a comb. The canon's fringe is longest at
# the temples and shortest either side of the parting, which sits right of
# centre, and its notches cut most of the way back up the forehead, so each lock
# is a blade with dark either side of it rather than a tooth on a band.
_TOUSLE_TIPS: list[Point] = [
    (-0.90, -0.04),
    (-0.64, -0.20),
    (-0.33, -0.40),
    (0.02, -0.34),
    (0.38, -0.26),
    (0.72, -0.14),
    (0.92, 0.00),
]
# Where the crown meets the side, and how far out the temple spike flicks. The
# canon crop is widest here, at the temples, and narrows below; the cut it
# replaces was widest at the bottom of its mass, because that mass was a circle.
_TOUSLE_TEMPLE: Point = (1.18, -0.46)


def _lerp(a: Point, b: Point, f: float) -> Point:
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def _tousle_side(tip: float) -> list[Segment]:
    """The right side, temple down to the side lock's point. One piece because
    the mass draws it and `fall_edge` hands the same points to the front lock,
    the same agreement `_FALL_*` exists for on the long cut."""
    return [
        ((1.30, -0.24), (1.26, 0.02)),
        ((1.20, 0.26), (1.12, tip - 0.20)),
        ((1.18, tip + 0.04), (1.02, tip + 0.06)),
    ]


# The crown, as the lock tips and the notches between them, each a bearing in
# degrees clockwise from straight up and a radius in head radii. Tips stand out
# at 1.28 to 1.40, notches cut back to 1.10 to 1.18, and the run is walked with
# straight lines, so every tip is a corner rather than the top of an arc.
#
# That distinction is the whole of what was learned from the reverted attempt.
# Bumps added *onto* a circular crown read as wobble, because a circle with a
# lump on it is a circle with a lump on it however the lump is drawn. A silhouette
# that is nothing but tips and notches has no circle left in it to spoil.
#
# The cowlick is the 20-degree mark, thin because its notches sit close either
# side of it, and tall enough to clear the rest by 0.10 head radii but no more:
# `test_hair_stays_under_the_canvas_ceiling` is about 0.01 away at this height.
_TOUSLE_CROWN: list[tuple[float, float]] = [
    (-70.0, 1.24),
    (-58.0, 1.12),
    (-40.0, 1.20),
    (-20.0, 1.24),
    (-4.0, 1.26),
    (10.0, 1.14),
    (18.0, 1.36),
    (25.0, 1.08),
    (35.0, 1.28),
    (46.0, 1.06),
    (60.0, 1.18),
]


def _polar(deg: float, radius: float) -> Point:
    a = math.radians(deg)
    return (radius * math.sin(a), -radius * math.cos(a))


def _straight(a: Point, b: Point) -> Segment:
    """A quadratic that is a straight line, so the anchors either side of it stay
    corners. Tips have to be corners: a control point off the line rounds the
    point over and the lock stops reading as a lock."""
    return (_lerp(a, b, 0.5), b)


def _chain(start: Point, points: list[Point]) -> list[Segment]:
    segments = []
    prev = start
    for q in points:
        segments.append(_straight(prev, q))
        prev = q
    return segments


def _tousle_mass_shape(tip: float) -> tuple[Point, list[Segment]]:
    """The crop's outer contour: a spiked crown rising to a cowlick right of
    centre, temple spikes, side locks past the ear, and a ragged nape."""
    left_side = [(_mirror_pt(c), _mirror_pt(e)) for c, e in _tousle_side(tip)]
    left_temple = (-_TOUSLE_TEMPLE[0], _TOUSLE_TEMPLE[1])
    return left_temple, [
        *_chain(left_temple, [_polar(d, r) for d, r in _TOUSLE_CROWN]),
        _straight(_polar(*_TOUSLE_CROWN[-1]), _TOUSLE_TEMPLE),
        *_tousle_side(tip),
        # The nape, right to left: shorter points than the sides, and the middle
        # of it tucks up behind the skull where the neck covers it anyway.
        ((1.00, tip + 0.10), (0.88, tip + 0.24)),
        ((0.76, tip + 0.02), (0.62, tip + 0.14)),
        ((0.42, tip + 0.28), (0.20, tip + 0.20)),
        ((0.00, tip + 0.32), (-0.20, tip + 0.20)),
        ((-0.42, tip + 0.28), (-0.62, tip + 0.14)),
        ((-0.76, tip + 0.02), (-0.88, tip + 0.24)),
        ((-1.00, tip + 0.10), (-1.10, tip + 0.04)),
        *_reverse(left_temple, left_side)[1],
    ]


def _mirror_pt(q: Point) -> Point:
    return (-q[0], q[1])


def _tousle_fall_edge(tip: float) -> tuple[Point, list[Segment]]:
    """The side lock's outer edge, its point back up to the temple. Traces the
    mass's own side exactly, so the two strokes land on each other."""
    return _reverse(_TOUSLE_TEMPLE, _tousle_side(tip))


def _tousle_hairline_shape(tip: float) -> tuple[Point, list[Segment], list[Segment]]:
    """Up the left side lock, across the fringe, down the right.

    The fringe is a row of separate pointed locks, not a scalloped edge: the
    notches rise most of the way back up the forehead, so each lock is a blade
    with dark either side of it rather than a tooth on a band. That is the single
    biggest difference between the crop the canon draws and the one this
    replaces, and it is why the notch list is as deep as it is.
    """
    right_edge = _tousle_fall_edge(tip)
    left_down = _reverse(*_mirror(*_tousle_fall_edge(tip)))
    # Back across the crown inside the mass, so the mass's own outline carries
    # the silhouette and the skull outline never shows through the hair.
    # The radius comes off the crown's own deepest notch rather than being picked.
    # At a picked 1.16 this arc stood outside the silhouette near the temple, where
    # the crown's notches drop to 1.06, and the fill painted past the outline with
    # no stroke on it to show what had happened. A constant radius under a notched
    # crown is the mistake; the notch that decides it has to be the one in the data.
    _, inner_crown = _arc(
        min(r for _, r in _TOUSLE_CROWN) - 0.04, _CROWN_TO_TEMPLE, -_CROWN_TO_TEMPLE, 4
    )
    back: list[Segment] = [*right_edge[1], *inner_crown, *left_down[1]]
    start: Point = back[-1][1]
    line: list[Segment] = [
        # Up the inside of the left side lock to where the fringe starts.
        ((-1.16, tip - 0.14), (-1.10, tip - 0.40)),
        ((-1.04, -0.06), (-0.98, _TOUSLE_NOTCHES[0][1])),
        *_tousle_fringe_line(),
        # Down the inside of the right side lock to its point.
        ((1.04, -0.06), (1.10, tip - 0.40)),
        ((1.16, tip - 0.14), right_edge[0]),
    ]
    return start, line, back


def _tousle_fringe_line() -> list[Segment]:
    """The fringe as quadratics: notch, point, notch, point. Controls sit along
    each edge rather than off it, so a lock is a blade with a slight bow in it
    and not a bulge."""
    segments: list[Segment] = []
    for i, point in enumerate(_TOUSLE_TIPS):
        left, right = _TOUSLE_NOTCHES[i], _TOUSLE_NOTCHES[i + 1]
        segments.append((_lerp(left, point, 0.55), point))
        segments.append((_lerp(right, point, 0.55), right))
    return segments


def _tousle_tip_edge(tip: float) -> list[tuple[Point, list[Segment]]]:
    """One pale region per lock, which is the whole point of this cut.

    Each fringe lock gets a wedge covering the last `1 - _HAIR_FADE` of its own
    length, so the boundary runs along the lock the way the canon's does, and the
    ratio of the two tones is the shared one rather than this cut's own. The
    regions overlap freely: a clip path is the union of its children, so they only
    have to cover the right area between them, not tile it.
    """
    regions: list[tuple[Point, list[Segment]]] = []
    for i, point in enumerate(_TOUSLE_TIPS):
        left, right = _TOUSLE_NOTCHES[i], _TOUSLE_NOTCHES[i + 1]
        # The top edge drops to each lock's own fade height, but keeps the notch
        # x values rather than following the lock's edges inward. Following them
        # inward is the obvious construction and it is wrong: it gives a wedge
        # the same shape as the lock and half the size, which is narrower than
        # the two outline strokes running down the lock's sides, so the tone is
        # painted and then covered up. Measured on the first attempt, only three
        # locks out of eight showed any of it. Keeping the notch x values makes
        # the region wider than the lock at every height, and a clip only has to
        # cover the area, not match it.
        a = (left[0], left[1] + (point[1] - left[1]) * (1.0 - _HAIR_FADE))
        b = (right[0], right[1] + (point[1] - right[1]) * (1.0 - _HAIR_FADE))
        # Past the point rather than up to it, for the same reason.
        far = _lerp(_lerp(left, right, 0.5), point, 1.35)
        # Controls on the midpoints, so each side of the region is a straight line.
        regions.append(
            (
                a,
                [
                    (_lerp(a, b, 0.5), b),
                    (_lerp(b, far, 0.5), far),
                    (_lerp(far, a, 0.5), a),
                ],
            )
        )
    # The sides and the nape, which hang the same way as each other and so take
    # one region between them, bounded above by a line sloping out to the temples.
    floor = tip + 1.5
    regions.append(
        (
            (-1.60, -0.30),
            [
                ((-1.20, 0.16), (-0.90, 0.24)),
                ((0.00, 0.40), (0.90, 0.24)),
                ((1.20, 0.16), (1.60, -0.30)),
                ((1.60, floor * 0.6), (1.60, floor)),
                ((0.00, floor), (-1.60, floor)),
            ],
        )
    )
    return regions


def _tousle_strands(tip: float) -> list[tuple[Point, list[Segment]]]:
    """Lines dividing the crown into locks, each aimed at a notch of the fringe.

    Aimed at the notches on purpose: a line that dies over the middle of a lock
    contradicts the lock it is lying on, and a line that runs to the crown itself
    turns the whole set into spokes, which is what made the old cut an umbrella.
    They start part way down for that reason and there are fewer of them than
    there are notches, because the canon draws two or three, not one per lock.
    """
    return [
        ((-0.60, -1.02), [((-0.86, -0.80), (-0.96, -0.52))]),
        ((-0.10, -1.08), [((-0.34, -0.86), (-0.52, -0.66))]),
        ((0.22, -1.14), [((0.16, -0.90), (0.02, -0.72))]),
        ((0.34, -1.06), [((0.52, -0.86), (0.66, -0.62))]),
        ((0.80, -1.04), [((1.02, -0.80), (1.10, -0.50))]),
        # One down each side lock, following it rather than crossing it.
        ((1.26, -0.30), [((1.30, 0.10), (1.20, tip - 0.24))]),
        ((-1.26, -0.30), [((-1.30, 0.10), (-1.20, tip - 0.24))]),
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
    # One chain per side. A list rather than one chain the drawing code mirrors,
    # because mirroring is an assumption that a cut is symmetric and it fails
    # without a sound: an asymmetric cut gets one side's lock edge stamped onto
    # the other, standing off the silhouette where the mass does not agree.
    # Symmetric cuts say so explicitly, with `_mirrored`.
    fall_edge: Callable[[float], list[tuple[Point, list[Segment]]]]
    # One or more closed regions whose union is the tip-toned area. A list rather
    # than one region because a tone boundary that runs level across a whole head
    # can only say "pale below this height", and the canon says "pale from here to
    # the tip of *this lock*", which is a different region per lock and cannot be
    # one curve unless the locks happen to line up. A clip path is the union of
    # its children, so per-lock regions compose with no other machinery.
    #
    # It stays a list, never a set or a dict's values: `ref-out/` is compared byte
    # for byte, so the order these come out in has to be the order they went in.
    tip_edge: Callable[[float], list[tuple[Point, list[Segment]]]]
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
    # How much bigger the whole cut is at the chibi end than at the adult end, as
    # a multiplier on `tip_range`'s answer. None leaves a cut the same size against
    # its head at every build, which is what every cut here did before this and
    # what the two older ones still do.
    #
    # It exists because the canon does not work that way. Measured off both
    # Satoshi references in head-radius units, the chibi's hair stands 0.73 head
    # radii clear of its skull where the adult's stands 0.29, and the ratio
    # between the two contours is 1.32 across the crown with a standard deviation
    # of 0.008. So a chibi wears visibly more hair for the same head, one scalar
    # describes it, and a cut that ignores this comes out with an adult's volume
    # on a child's head. See `docs/gap-analysis.md` gap 1.
    #
    # A cut that raises this needs `build_skeleton`'s `hair_margin` to have room
    # for it at the chibi end, and the ceiling test is what says so.
    volume: tuple[float, float] | None = None


def _long_fall_edges(length: float) -> list[tuple[Point, list[Segment]]]:
    return _mirrored(_fall_edge(length))


def _short_fall_edges(tip: float) -> list[tuple[Point, list[Segment]]]:
    return _mirrored(_short_fall_edge(tip))


def _tousle_fall_edges(tip: float) -> list[tuple[Point, list[Segment]]]:
    return _mirrored(_tousle_fall_edge(tip))


HAIRSTYLES: dict[str, Hairstyle] = {
    "long_blunt": Hairstyle(
        _hair_mass_shape, _hairline_shape, _long_fall_edges, _hair_tip_edge, strands=_long_strands
    ),
    "short_layered": Hairstyle(
        _short_mass_shape,
        _short_hairline_shape,
        _short_fall_edges,
        _short_tip_edge,
        strands=_short_strands,
        # Where the side tips end: a tight crop pinned to the skull at 0, a
        # shaggy ear-length cut at 1. The old (0.42, 1.00) range described the
        # bob this used to be, with locks reaching for the jaw.
        tip_range=(0.25, 0.70),
    ),
    "long_traced": Hairstyle(
        _long_traced_mass,
        _long_traced_hairline,
        _long_traced_fall_edge,
        _long_traced_tip_edge,
        strands=_long_traced_strands,
        # No `tip_range`, so `hair_length` measures the body, chin to hip. That
        # is what keeps a long haircut the same haircut when the build changes;
        # a head-relative range would freeze her hair at one length and it would
        # ride up the adult's back.
    ),
    "short_crop": Hairstyle(
        _crop_mass_shape,
        _crop_hairline_shape,
        _crop_fall_edge,
        _crop_tip_edge,
        strands=_crop_strands,
        # Where the side tips reach. `hair_length` 0.65, which is what Satoshi
        # carries, puts the cut at exactly the size it was traced at.
        tip_range=(0.800, 0.911),
        volume=(1.30, 1.00),
    ),
    "short_tousled": Hairstyle(
        _tousle_mass_shape,
        _tousle_hairline_shape,
        _tousle_fall_edges,
        _tousle_tip_edge,
        strands=_tousle_strands,
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
        fall = lo + p.hair_length * (hi - lo)
        if style.volume is not None:
            chibi, adult = style.volume
            fall *= adult + (chibi - adult) * (1.0 - sk.build)
        return fall
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
        # Several regions clip to their union, which is what lets a cut give each
        # lock its own tone boundary instead of running one line across them all.
        regions = "".join(
            f'<path d="{_curve(sk.head_cx, sk.head_cy, sk.head_r, start, segments)}" />'
            for start, segments in style.tip_edge(fall)
        )
        clips.append(f'<clipPath id="{_HAIR_TIP_CLIP_ID}">{regions}</clipPath>')
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
        f'<path d="{d}" fill="none" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
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
    if p.outfit.tunic_tucked:
        # Tucked in: the hem stops half way into the belt band rather than
        # carrying on to the hip, so the belt covers the join from both sides
        # and the garment below rises to the same line. Drawn to the hip and
        # relying on z-order instead, the tunic would simply paint over the top
        # of the trousers, because it is stacked above them.
        belt_y, belt_h = _belt_band(sk)
        hy = belt_y + belt_h * 0.5
        # A shade over the waist's own width, so the short run below the waist
        # reads as cloth gathered into the belt rather than as a taper.
        hw = ww * 1.01
    notch = sk.neck_half_w * 0.8
    sleeve_w = _sleeve_half_w(sk)
    cuff_y = _sleeve_hem_y(sk)
    # Shoulders slope. A horizontal shoulder line is what made the sleeve look
    # bolted on even once it was the right shape. 0.14 was not enough of it: the
    # canon's shoulder leaves the neck already going down as well as out, and at
    # 0.14 ours held its height across most of the span and then dropped at the
    # end, which is a horizontal cap with a corner on it rather than a slope.
    slope = (wy - sy) * 0.24
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
        # The control sits half way out and most of the way down, so the edge
        # leaves the neck descending and arrives at the sleeve's tip nearly
        # horizontal. Putting it far out and barely down, which is what was here,
        # gives the opposite: a flat run and then a corner.
        return (
            f"Q {cx + s * sleeve_w * 0.50:.1f} {sy + slope * 0.62:.1f} "
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


# Where the other lower-body layers sit, both stated against the skirt rather
# than measured from the hip on their own: a chibi's skirt is drawn shorter than
# asked for, and layers measured independently collapse onto one hem, where the
# underskirt has to keep showing below the skirt and the apron has to keep
# stopping above it, at every build.
#
# How far the underskirt hangs past the skirt's hem, as a fraction of the
# hip-to-ankle span.
_UNDERSKIRT_DROP = 0.13
# How far down the apron hangs, as a share of the skirt's own drop from the
# apron's top edge to the skirt's hem. A share rather than a fixed lift off that
# hem, which is what the apron used to take: measured hip to ankle, the lift was
# most of a chibi's whole body and left a band across its hips.
_APRON_DROP = 0.74


def _underskirt(sk: Skeleton, p: CharacterParams) -> str:
    """A second skirt, longer than the one over it, so its hem shows as a band of
    a different tone below the other's."""
    color = p.outfit.underskirt_color
    if color is None:
        return ""
    skirt_hem = _skirt_hem_y(sk, p.outfit.skirt_length)
    hem_y = skirt_hem + (sk.ankle_y - sk.hip_y) * _UNDERSKIRT_DROP
    # Hangs straight below the skirt's own hem rather than continuing to flare,
    # and clearly narrower, so it reads as being under the other one. At 0.97 it
    # was the skirt's own width to within a stroke, so the silhouette held the
    # skirt's flare all the way down past the hem, which is where ours ran wide
    # of the canon: theirs has already narrowed toward the legs by then. It is
    # also what made the chibi's dark band under a wide hem read as a tray.
    hem_w = _skirt_half_w(sk, skirt_hem) * 0.86
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
    parts = [shape, f'<path d="{band}" fill="{shade(color)}" opacity="0.7" />']
    # Pleats, as lines rather than as tone, the same call the outer skirt's folds
    # got: the canon adult's underskirt is a pleated skirt and the vertical fold
    # lines are the whole of what says so. They start at the skirt hem above,
    # since nothing higher is ever seen, and they run to the band, not through it,
    # so the turn under the hem stays one unbroken edge.
    #
    # Only where the band is deep enough to hold them. On a chibi the visible
    # strip is a few pixels and a row of lines across it reads as a comb.
    if hem_y - skirt_hem > _stroke_w(sk) * 4:
        pleat_sw = max(1.0, _stroke_w(sk) * 0.45)
        for i in range(-3, 4):
            at = i / 3.5
            x0 = sk.head_cx + _skirt_half_w(sk, skirt_hem) * 0.86 * at
            x1 = sk.head_cx + hem_w * at
            parts.append(
                f'<line x1="{x0:.1f}" y1="{skirt_hem:.1f}" x2="{x1:.1f}" y2="{band_y:.1f}" '
                f'stroke="{shade(color)}" stroke-width="{pleat_sw:.1f}" opacity="0.75" />'
            )
    return "".join(parts)


def _apron(sk: Skeleton, p: CharacterParams) -> str:
    """A front panel hanging from the belt over the skirt. Narrow enough to leave
    the hands clear on both sides, which is what fixes its width more than the
    reference does."""
    color = p.outfit.apron_color
    if color is None:
        return ""
    cx = sk.head_cx
    # Starts above the waist so the belt drawn over it covers the top edge.
    # A fraction of the skirt's own drop rather than a fixed lift off its hem.
    # The lift was measured from the hip to the ankle, which is most of a chibi's
    # whole body, so on a chibi it ate nearly the entire panel and left a band
    # across the hips where the canon hangs an apron down the skirt. Stated as a
    # share of the skirt the apron hangs over, one number holds at both builds.
    top_y = sk.waist_y - (sk.hip_y - sk.waist_y) * 0.40
    bot_y = top_y + (_skirt_hem_y(sk, p.outfit.skirt_length) - top_y) * _APRON_DROP
    # Narrower than the waist by a quarter rather than a tenth. At 0.90 the panel
    # reached the hips, so the pouches hanging there landed on its top corners and
    # the belt, apron and pouches read as one satchel strapped across the body,
    # which is what the canon chibi does not do: there the apron is a panel hung
    # in the middle with the pouches flanking it, and the gap between them is what
    # tells the three pieces apart. The pouches move outboard to match.
    top_w = sk.waist_half_w * 0.74
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
    # The arm is narrower than the sleeve it comes out of, which is what says
    # "sleeve" rather than "plank". It used to be the sleeve's own width, to 1%,
    # deliberately, so the two outlines landed on each other and the silhouette
    # ran from shoulder to wrist with no step in it. That reads as one continuous
    # limb wearing nothing: the canon puts a visible step at the hem on both
    # characters and at both builds, and a garment hanging over a thinner arm is
    # the whole of what the step means.
    #
    # The arm's top edge still sits exactly on `_sleeve_hem_y`, so the hem line
    # and the top of the limb remain one line and the narrower arm simply leaves
    # the outer stretch of that line showing either side of it.
    out_top = _sleeve_half_w(sk) * 0.86
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
        if p.outfit.undersleeve_color is not None:
            parts.append(_wrist_cuff(sk, sleeve, x(centre_wrist), wrist_y, w_wrist))
        parts.append(_hand(sk, p, x(centre_wrist), wrist_y, w_wrist, s))
    return "".join(parts)


def _wrist_cuff(sk: Skeleton, color: str, cx: float, wrist_y: float, w: float) -> str:
    """A band closing the undersleeve at the wrist.

    Small element, so it takes the second tone: this is the pouch-flap and
    boot-cuff case the flat-colour rule leaves open, a turn of cloth reading as
    thickness, not a plane across a panel.

    Satoko's canon undersleeves end in one of these and Satoshi's are rolled at
    the forearm instead, with a thicker cuff, two roll lines and bare arm below.
    Only this one is drawn: the roll belongs to the satoshi references, which
    drive his haircut and nothing else about his design (the owner's call,
    2026-08-07). Drawn only when there is an undersleeve, since a cuff on a bare
    arm is a bracelet.
    """
    h = w * 0.55
    # The arm still tapers across the band's own height, so the top is a shade
    # wider than the bottom. Without that the cuff reads as pasted on.
    top_w = w * 1.05
    return (
        f'<path d="M {cx - top_w:.1f} {wrist_y - h:.1f} L {cx + top_w:.1f} {wrist_y - h:.1f} '
        f'L {cx + w:.1f} {wrist_y:.1f} L {cx - w:.1f} {wrist_y:.1f} Z" '
        f'fill="{shade(color)}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk) * 0.85:.1f}" />'
    )


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
        # Fingers, as two short strokes running in from the outer edge rather
        # than as separate digits. The canon indicates them exactly this way, and
        # a hand drawn as four modelled fingers at this size reads as noise: the
        # mitten with a thumb stays, these divide it. They stop short of the
        # centre so the hand keeps one silhouette.
        for at, reach in ((0.62, 0.62), (0.80, 0.50)):
            parts.append(
                f'<path d="M {x(hw * 0.98):.1f} {wrist_y + length * at:.1f} '
                f"Q {x(hw * (0.98 - reach * 0.5)):.1f} {wrist_y + length * (at + 0.05):.1f} "
                f'{x(hw * (0.98 - reach)):.1f} {wrist_y + length * (at + 0.07):.1f}" '
                f'fill="none" stroke="{OUTLINE}" stroke-width="{sw * 0.45:.1f}" opacity="0.55" '
                f'stroke-linecap="round" />'
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
    # need their own outline, they start at the belt rather than under a hem, and
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
    # Bare legs are separately filled paths drawn in a loop, so if they ever met,
    # the second one's fill would cover the first one's, and the crotch would
    # come out as an asymmetric seam. This keeps a slot open no matter what frame
    # widens the thigh or narrows the hip. The reference leaves each inner edge
    # about 0.09 head radii off centre, which is where the presets land without
    # the floor biting. Trousers are one path and would not need this, but they
    # share the number so the boots stand in the same place either way.
    gap = max(gap, w_top + sk.leg_half_w * 0.2)
    if trousers:
        parts = [_trousers(sk, p, trousers, gap, w_top, w_knee, w_calf, w_ankle)]
        for side in (-1, 1):
            parts.append(_boot(sk, p, sk.head_cx + side * gap, w_ankle, w_knee, side))
        return "".join(parts)

    # A bare leg has to start at or above whatever hem is going to cover its top,
    # and the skirt's hem moves with `skirt_length`. Pinning it to the skeleton's
    # own hem leaves a band of bare canvas across the hips as soon as a skirt is
    # asked to be shorter than that.
    top_y = min(sk.hem_y, _skirt_hem_y(sk, p.outfit.skirt_length)) - 4
    calf_y = sk.knee_y + (sk.ankle_y - sk.knee_y) * 0.35
    # No tone down the leg. It was there to separate the two of them when both are
    # the same flat colour, but they are separate paths with a slot between them,
    # so the silhouette was already doing that, and a stripe down a leg reads the
    # way one down a sleeve does.
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
        parts.append(f'<path d="{d}" fill="{p.skin_tone}" />')
        parts.append(_boot(sk, p, cx, w_ankle, w_knee, side))
    return "".join(parts)


# Where the legs part, measured hip to knee. Both canon sheets put the crotch at
# very nearly a quarter of belt-to-floor, 0.28 on the chibi and 0.23 on the
# adult, which lands within a percent of the body's height of this one fraction
# at both builds, so it does not need to ride the build.
#
# Those two numbers are where *background* first shows between the legs, which
# is a stroke-width below the point the two edges actually meet: until the notch
# is wider than the two strokes facing each other across it, it paints solid. So
# ours reads a little lower than the canon's at the same fraction, ours being the
# heavier line. Correcting for it would move the crotch by well under a percent
# of the figure's height, and the render is right by eye, so it is left alone.
_CROTCH_AT = 0.28


def _trousers(
    sk: Skeleton,
    p: CharacterParams,
    color: str,
    gap: float,
    w_top: float,
    w_knee: float,
    w_calf: float,
    w_ankle: float,
) -> str:
    """Trousers as one garment: a seat with a notch cut out of it, not two tubes.

    The canon draws no gap between the legs above the crotch and no seam across
    the top of the thigh either. Measured on both Satoshi sheets, the silhouette
    below the belt is a single run until roughly a quarter of the way to the
    floor, where background first appears between the legs, and from there the
    slot opens smoothly to about a third of the garment's width by the boot.

    So this is one closed path, and the inseam is its own stroke rather than a
    line drawn on. What was here before was a wedge drawn behind two separately
    stroked tubes, and the wedge's lower V hung below the tunic's hem between
    two legs that had a slot of canvas running all the way up between them: it
    read as a flap hanging off the belt rather than as the seat of a garment.

    Starts inside the belt band when the tunic is tucked, which is the other
    half of the same fix. The trousers used to begin at the hip, a good part of
    the way down from the belt, with the tunic covering the difference, so the
    tunic hung in a band below its own belt and the trousers appeared to start
    at the tunic's hem. Both references tuck the tunic in and start the trousers
    at the belt. Untucked they still begin at the hip, since a tunic hanging to
    the hip is over them either way and a waist drawn under it could only ever
    show through some later change to the garment above.
    """
    cx = sk.head_cx
    belt_y, belt_h = _belt_band(sk)
    # Rising into the belt is the tucked case only. Under a tunic that hangs to
    # the hip there is nothing to see up there, and drawing it anyway would put
    # the whole waist of the garment under another garment, where the only thing
    # it could ever do is show through a later change to the one above it.
    tucked = p.outfit.tunic_tucked
    top_y = belt_y + belt_h * 0.5 if tucked else sk.hip_y
    crotch_y = sk.hip_y + (sk.knee_y - sk.hip_y) * _CROTCH_AT
    calf_y = sk.knee_y + (sk.ankle_y - sk.knee_y) * 0.35
    # The two outer edges run straight, at the leg's own width, from the belt all
    # the way to the ankle: the only taper in them is the leg's own 1.10 thigh to
    # 0.92 ankle, which is a couple of degrees off vertical.
    #
    # Flaring them out to `hip_half_w` at the hip was tried first, on the
    # reasoning that the garment should carry the body's width through the belt.
    # It does not work here, and the owner's call on it was to put the straight
    # line back. Our chibi's leg is 0.24 of its belt's half-width where the
    # canon's is 0.39 (`docs/gap-analysis.md`), so a hip drawn at full width has
    # to shed 40% of it before the knee, and no distribution of that hides it:
    # low it becomes a saddlebag on each side, high it becomes a wedge with the
    # leg thick at the hip and thin at the boot. A straight column is what the
    # canon draws at both builds anyway. The cost is that the belt is wider than
    # the trousers under it, and that is a leg-width gap, not a trouser one.
    knee_ctrl_y = sk.knee_y - (sk.knee_y - top_y) * 0.3

    def outer_down(s: int) -> str:
        """Belt to ankle down one side, on the leg's own contour throughout."""
        return (
            f"Q {cx + s * (gap + w_top):.1f} {knee_ctrl_y:.1f} "
            f"{cx + s * (gap + w_knee):.1f} {sk.knee_y:.1f} "
            f"Q {cx + s * (gap + w_calf):.1f} {calf_y:.1f} "
            f"{cx + s * (gap + w_ankle):.1f} {sk.ankle_y:.1f} "
        )

    def inner_up(s: int) -> str:
        """One ankle's inside up to the crotch, which is the inseam."""
        return (
            f"L {cx + s * (gap - w_ankle):.1f} {sk.ankle_y:.1f} "
            f"Q {cx + s * (gap - w_top):.1f} {sk.knee_y:.1f} {cx:.1f} {crotch_y:.1f} "
        )

    def inner_down(s: int) -> str:
        return (
            f"Q {cx + s * (gap - w_top):.1f} {sk.knee_y:.1f} "
            f"{cx + s * (gap - w_ankle):.1f} {sk.ankle_y:.1f} "
            f"L {cx + s * (gap + w_ankle):.1f} {sk.ankle_y:.1f} "
        )

    def outer_up(s: int) -> str:
        return (
            f"Q {cx + s * (gap + w_calf):.1f} {calf_y:.1f} "
            f"{cx + s * (gap + w_knee):.1f} {sk.knee_y:.1f} "
            f"Q {cx + s * (gap + w_top):.1f} {knee_ctrl_y:.1f} "
            f"{cx + s * (gap + w_top):.1f} {top_y:.1f} "
        )

    w_waist = gap + w_top
    d = (
        f"M {cx - w_waist:.1f} {top_y:.1f} L {cx + w_waist:.1f} {top_y:.1f} "
        + outer_down(1)
        + inner_up(1)
        + inner_down(-1)
        + outer_up(-1)
        + "Z"
    )
    # Rounded joins, because the inseam meets itself at a point at the crotch and
    # SVG's default miter shoots a spike off any sharp corner. `_hair_mass` hit
    # the same thing at a lock's tip.
    return (
        f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" '
        f'stroke-linejoin="round" />' + _trouser_seams(sk, p, color, gap, w_top, top_y, crotch_y)
    )


def _trouser_seams(
    sk: Skeleton,
    p: CharacterParams,
    color: str,
    gap: float,
    w_top: float,
    top_y: float,
    crotch_y: float,
) -> str:
    """The fly and the two hip pocket seams.

    Lines rather than tone, the same call the skirt's folds and the underskirt's
    pleats got. The fly ends on the crotch rather than at a fraction of the way
    to the knee: it is the seam that runs down to where the legs part, so it has
    to move when the crotch does.
    """
    if not p.shaded:
        return ""
    cx = sk.head_cx
    drop = crotch_y - top_y
    seam_sw = max(1.0, _stroke_w(sk) * 0.45)
    parts = [
        f'<line x1="{cx:.1f}" y1="{top_y + drop * 0.12:.1f}" x2="{cx:.1f}" y2="{crotch_y:.1f}" '
        f'stroke="{shade(color)}" stroke-width="{seam_sw:.1f}" opacity="0.8" />'
    ]
    for s in (-1, 1):
        parts.append(
            f'<path d="M {cx + s * (gap + w_top * 0.90):.1f} {top_y + drop * 0.16:.1f} '
            f"Q {cx + s * (gap + w_top * 0.40):.1f} {top_y + drop * 0.46:.1f} "
            f'{cx + s * (gap - w_top * 0.10):.1f} {top_y + drop * 0.86:.1f}" '
            f'fill="none" stroke="{shade(color)}" stroke-width="{seam_sw:.1f}" opacity="0.8" />'
        )
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
    # `docs/gap-analysis.md` had this 17% to 27% narrow of the canon through the
    # foot at the realistic build. It is not: measured on the boot's own colour
    # rather than on the silhouette, the canon's adult boot is 0.058 of figure
    # height across and ours is 0.076, so ours is a third *wider*. The silhouette
    # agreed only because the canon stands its feet further apart than we do, and
    # outer-edge-to-outer-edge is stance plus boot. Widening this to chase that
    # number was tried in task 68 and took the whole foot 22% past the canon.
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
    # Turned cuff at the top of the shaft, the one thing that says "boot" rather
    # than "sock". A band now rather than a line: the canon turns the leather over
    # and the depth of the turn is what reads, where a single line reads as a
    # seam. This is the small-element case the flat-colour rule leaves open, a
    # turn of material showing its thickness.
    cuff_h = (sk.ankle_y - top_y) * 0.34
    parts.append(
        f'<rect x="{cx - shaft_w:.1f}" y="{top_y:.1f}" width="{shaft_w * 2:.1f}" '
        f'height="{cuff_h:.1f}" fill="{shade(color, 0.78)}" stroke="{OUTLINE}" '
        f'stroke-width="{_stroke_w(sk) * 0.7:.1f}" />'
    )
    # The tongue, under the laces and above the instep. Drawn before them so they
    # cross it, which is the only way a tongue reads on a front view.
    tongue_w = shaft_w * 0.50
    parts.append(
        f'<path d="M {cx - tongue_w:.1f} {top_y + cuff_h:.1f} L {cx + tongue_w:.1f} {top_y + cuff_h:.1f} '
        f"Q {cx + tongue_w * 0.86:.1f} {instep_y + foot_h * 0.10:.1f} "
        f"{cx:.1f} {instep_y + foot_h * 0.18:.1f} "
        f'Q {cx - tongue_w * 0.86:.1f} {instep_y + foot_h * 0.10:.1f} {cx - tongue_w:.1f} {top_y + cuff_h:.1f} Z" '
        f'fill="{shade(color, 0.88)}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk) * 0.55:.1f}" />'
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
    # Eyelets where the laces turn, which is where the canon puts them. Only at
    # the taller builds: at chibi they land under a stroke's width of each other
    # and read as grit on the boot.
    if sk.build > 0.4:
        for i in range(steps + 1):
            for s in (-1, 1):
                parts.append(
                    f'<circle cx="{cx + s * lace_w:.1f}" cy="{lace_top + i * dy:.1f}" '
                    f'r="{lace_sw * 0.9:.1f}" fill="{shade(color, 0.35)}" />'
                )
    return "".join(parts)


def _belt_band(sk: Skeleton) -> tuple[float, float]:
    """Where the belt sits and how deep it is, as (top y, height).

    Shared rather than computed where it is needed, because three parts depend
    on it now: the belt draws it, a tucked tunic ends inside it, and trousers
    start inside it. Two of those only work while all three agree, and the
    failure is a band of bare canvas at the waist.
    """
    h = (sk.hip_y - sk.waist_y) * 0.42
    return sk.waist_y - h * 0.35, h


def _belt(sk: Skeleton, p: CharacterParams) -> str:
    """A band at the waist. On a front view this is what actually makes a waist
    read, since the arms hang over the silhouette's own taper and hide it."""
    color = p.outfit.belt_color
    if color is None:
        return ""
    cx = sk.head_cx
    # Wraps over the tunic, so it is a shade wider than the body at the waist.
    half_w = sk.waist_half_w * 1.03
    y, h = _belt_band(sk)
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
        # The keeper, the loop that holds the strap's loose end down past the
        # buckle. One small band, and it is most of what tells a buckle from the
        # hollow square this used to read as: a square alone is a shape, a square
        # with a strap running through a loop beside it is a fastening.
        kw = h * 0.22
        parts.append(
            f'<rect x="{bx + bw + h * 0.30:.1f}" y="{y + h * 0.08:.1f}" width="{kw:.1f}" '
            f'height="{h * 0.84:.1f}" rx="{kw * 0.3:.1f}" fill="{shade(color, 0.7)}" '
            f'stroke="{OUTLINE}" stroke-width="{sw * 0.55:.1f}" />'
        )
    else:
        # With an apron over the belt the buckle is hidden behind the panel, which
        # is why the canon draws Satoshi's and not Satoko's. What it draws instead
        # is the strap's knotted end hanging down the apron's front, and that tie
        # is the one thing on the assembly that says the panel hangs *from* the
        # belt rather than being a pocket sewn across it.
        sw = _stroke_w(sk)
        tie_w = h * 0.30
        knot_h = h * 0.55
        knot_y = y + h * 0.55
        parts.append(
            f'<rect x="{cx - h * 0.42:.1f}" y="{knot_y:.1f}" width="{h * 0.84:.1f}" '
            f'height="{knot_h:.1f}" rx="{knot_h * 0.35:.1f}" fill="{shade(color, 0.86)}" '
            f'stroke="{OUTLINE}" stroke-width="{sw * 0.7:.1f}" />'
        )
        for s, drop in ((-1, 0.62), (1, 0.48)):
            # Two ends of unequal length, because a knot with two equal tails
            # reads as a ribbon.
            x0 = cx + s * h * 0.20
            parts.append(
                f'<path d="M {x0 - tie_w / 2:.1f} {knot_y + knot_h * 0.7:.1f} '
                f"L {x0 + tie_w / 2:.1f} {knot_y + knot_h * 0.7:.1f} "
                f"L {x0 + s * h * 0.10 + tie_w / 2:.1f} {knot_y + knot_h + (sk.hip_y - sk.waist_y) * drop:.1f} "
                f"L {x0 + s * h * 0.10 - tie_w / 2:.1f} {knot_y + knot_h + (sk.hip_y - sk.waist_y) * drop:.1f} "
                f'Z" fill="{shade(color, 0.86)}" stroke="{OUTLINE}" stroke-width="{sw * 0.7:.1f}" />'
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
    # How far out the pouches hang. They flank the apron rather than sitting on
    # its corners: the canon chibi leaves a gap of skirt between panel and pouch,
    # and that gap is what tells belt, apron and pouch apart instead of letting
    # them read as one satchel across the hips. Still short of the band's ends,
    # because a chibi's arms are thick and hang over them, which is what the
    # earlier inboard value was really guarding against.
    x_frac = 0.68 + 0.08 * sk.build
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

# How much width the whole skull loses by the adult end, as a fraction. The
# measurement that produced this is in `docs/gap-analysis.md` under gap 7: read
# below the hair, where the canon jaw can actually be seen, our jaw was already
# close, so the head did not read round because the jaw was wide. It read round
# because the whole upper face was, and a taper cannot fix that without eating the
# jaw as well.
_SKULL_NARROW = 0.10
# Where the jaw taper begins, in head radii, negative being above the head
# centre. A taper that begins at the cheek line holds full width down the whole
# cheek and then loses it in the last tenth, which reads as a round head with a
# point stuck on. Starting a quarter of a radius higher costs 2% of the width at
# the cheek line, too little to strand the hairline, and lets the cheek run.
_JAW_START_Y = -0.25
# How the taper eases from there to the chin. Squared is a curve that stays wide
# and then dives; nearer to linear is the straighter cheek the canon draws.
_JAW_EASE = 1.4


def _head_pt(deg: float, radius: float, build: float) -> Point:
    """One point on the skull's profile, in head radii, clockwise from the crown.

    A bearing rather than a height, because the taper below `_JAW_START_Y` moves a
    point in both axes at once and so cannot be inverted in closed form. This is
    the single definition of where the skull's edge is: `_head_shape` walks it to
    lay down the outline and `_head_edge_x` samples it to find the edge at a given
    height, so a part welded to the head follows the taper for free.
    """
    narrow = 1.0 - _SKULL_NARROW * build
    jaw_pull = 0.20 * build
    chin_drop = 0.05 * build
    th = math.radians(deg)
    x, y = math.sin(th) * radius * narrow, -math.cos(th) * radius
    if y > _JAW_START_Y:
        # 0 where the taper starts, 1 at the chin.
        lean = min(1.0, (y - _JAW_START_Y) / (1.0 - _JAW_START_Y))
        x *= 1.0 - jaw_pull * lean**_JAW_EASE
        y *= 1.0 + chin_drop * lean
    return (x, y)


def _head_edge_x(y: float, build: float) -> float:
    """How far off centre the skull's edge sits at height `y`, in head radii.

    Walks the right half of the profile a degree at a time and interpolates,
    which is exact enough at this scale and, more to the point, cannot drift
    away from the drawn outline the way a second formula would. Heights outside
    the skull clamp to its ends rather than raising, since the callers are
    placing a part against the head, not asking a question about geometry.
    """
    prev = _head_pt(0.0, 1.0, build)
    for deg in range(1, 181):
        cur = _head_pt(float(deg), 1.0, build)
        if prev[1] <= y <= cur[1]:
            span = cur[1] - prev[1]
            f = (y - prev[1]) / span if span else 0.0
            return prev[0] + (cur[0] - prev[0]) * f
        prev = cur
    return prev[0]


def _head_shape(build: float) -> tuple[Point, list[Segment]]:
    """The skull: a circle at the chibi end, a narrower jawed oval at the adult end.

    Eight quadratics that trace a unit circle when nothing narrows or tapers them,
    so the chibi keeps the round head it always had, and the head loses width and
    gains a jaw as the build gets taller. A plain circle is fine at 2.4 heads and
    reads as a ball on a stick at 7, which is what this is for.

    Two knobs rather than one, because the canon needs both. Against
    `ref/satoko-real.jpg`, normalised on figure height and read at matched depths
    above each figure's own drawn chin, the canon jaw runs 0.095, 0.081 and 0.061 H
    and the old shape ran 0.104, 0.085 and 0.059: near enough that no amount of
    taper was the answer, and a taper strong enough to change the look pulled the
    jaw to 0.087, 0.071 and 0.050, out the other side. Narrowing the skull 10% and
    tapering it *less* holds the jaw at 0.094, 0.079 and 0.056 while taking the
    width out of the cheeks, which is where the roundness actually was.

    The cheek itself cannot be measured against the canon: their hair lies across
    the temples and ours stands off them, so what is visible there is a hair
    difference wearing a face's clothes. That half was judged on the strips
    (`out/62/round2_satoko.png`, `round2_satoshi.png`).
    """
    # Control-point radius that makes a quadratic chain trace a circle.
    k = 1 / math.cos(math.pi / _HEAD_SEGMENTS)
    step = 360 / _HEAD_SEGMENTS
    anchors = [_head_pt(i * step, 1.0, build) for i in range(_HEAD_SEGMENTS)]
    controls = [_head_pt((i + 0.5) * step, k, build) for i in range(_HEAD_SEGMENTS)]
    return anchors[0], [
        (controls[i], anchors[(i + 1) % _HEAD_SEGMENTS]) for i in range(_HEAD_SEGMENTS)
    ]


# Where the ear meets the skull, top and bottom, in head radii from the head
# centre with y down.
#
# Measured off `ref/satoshi-real.jpg`, which is the one reference that draws the
# ear plainly: the hair hangs around it rather than over it. The life-drawing
# rule of thumb, ear from the brow line to the nose, is *not* what the canon
# draws and following it put the ear 0.16 head radii too high. The canon's ear
# top sits level with the top of the eye aperture, not the brow, and its bottom
# runs to 0.49, which is lower than our own nose at 0.36. Ours and the canon's
# noses do not agree about where they sit against the skull, so the ear is
# placed against the skull and the eye, which do agree, rather than against a
# nose that would drag it up.
#
# The fit is eye centre to drawn chin: our eye sits at 0.16 head radii and our
# chin ink at 1.05, so that run is 0.89 r, and both ends are unambiguous ink in
# the reference. Eye to mouth was tried first and is not usable here, since the
# canon's mouth sits lower against its head than ours does; it gave a head
# radius 38% different from the one eye-to-chin gives.
#
# Stated as named constants because the hair wants them too. A side lock's
# length and flare were being chosen against nothing at all, which is most of
# why they took five rounds and still did not settle; the ear is the landmark
# they were missing, so a lock that should tuck behind it or flick past it now
# has something to say that against.
_EAR_TOP_Y = 0.03
_EAR_BOT_Y = 0.49
# How far the ear stands clear of the skull at its widest, in head radii.
#
# The canon's own ear is 0.263 r wide, and that is not transferable as it
# stands: it sticks out past a cheek sitting at 0.632 r, where ours sits at
# 0.81 (adult) to 0.94 (chibi), so the canon's whole head-plus-ear reaches 0.895
# r and our bare skull is already past that at the chibi. Our head being wide
# against the canon's is the open residual under gap 2, not something the ear
# can fix, so the ear takes a width that reads at our scale rather than one that
# matches a silhouette we cannot match anyway.
_EAR_OUT = 0.17
# The ear is the same size against the head at both builds, deliberately. A
# child's ear really is larger against its skull than an adult's, and that was
# in here for a round as a shrink on the build, but the span above is measured
# off the *adult* reference, so a shrink made the one build the number came from
# the one build that did not reproduce it: the adult came out 12% short while
# the chibi got the canon figure exactly.
#
# **Retraction.** This used to say there was no chibi ear to measure, both cuts
# covering it. There is: `ref/satoshi-chibi.jpg` draws the viewer-right one
# clear of the hair, and the owner's crop of it is `ref/satoshi-ear.png`.
# Measured (`out/ear2/`), the chibi's ear runs 0.024 to 0.614 head radii against
# the adult's 0.03 to 0.49, so it really is about 30% taller against the skull,
# the way anatomy says. The span here is still the adult's and the shrink is
# still gone: resolving that into a build-riding span is a placement change and
# a separate decision from the shape below, which is what the trace is used for.

# The ear's outline and its one inner fold, traced off the canon chibi and held
# in the ear's own frame rather than in head radii: y runs 0 at the top attach to
# 1 at the bottom, and x runs 0 on the chord between them to 1 at the widest
# stand-out. That is what makes the trace a *shape* and leaves where the ear
# sits and how far it stands out to `_EAR_TOP_Y`, `_EAR_BOT_Y` and `_EAR_OUT`
# above, which are measured off the adult and should not be spent on this.
#
# Simplified to the finest level with no edge under two stroke widths at either
# build, the same rule the hair silhouette settled on. The rim's own weight sets
# the floor for the outline and 0.55 of it for the fold, so the fold gets to
# keep more detail than the rim does.
_EAR_ARC_START: Point = (0.000, 0.000)
_EAR_ARC: list[Segment] = [
    ((0.008, 0.345), (0.135, 0.655)),
    ((0.273, 0.943), (0.500, 1.000)),
    ((0.661, 0.944), (0.779, 0.768)),
    ((0.963, 0.406), (1.000, 0.000)),
]
# The antihelix, which the canon draws as one stroke shaped like a question
# mark: an upper crescent that turns back on itself and runs down into a hook.
# Isolating it took three readings. It is not a separate piece of ink, since it
# runs into the rim at the top, so connectivity does not find it; and it is not
# the second run of ink along a row either, since a row-scan hops between the
# crescent, the hook and the rim and comes out a zigzag lying on none of them.
# What works is eroding the silhouette until the rim, which is its boundary by
# definition, has nothing left, while a stroke drawn across the middle survives.
#
# Its x is normalised across its own width rather than shared with the rim's.
# The canon's fold reaches a third of the ear's stand-out *left* of the attach
# chord, which our ear has no room for: our chord is a straight line between two
# points on the skull, and a skull is convex, so it bulges out past the chord
# everywhere in between. The canon's ear overlaps the cheek and ours is welded
# to it. So the two constants below say which band of the ear's width the fold
# lands in, and the trace says only what shape it is inside that band.
_EAR_FOLD_START: Point = (0.404, 1.000)
_EAR_FOLD: list[Segment] = [
    ((0.294, 0.955), (0.255, 0.778)),
    ((0.229, 0.591), (0.260, 0.408)),
    ((0.338, 0.255), (0.428, 0.105)),
    ((0.430, 0.402), (0.615, 0.465)),
    ((0.731, 0.258), (0.731, 0.000)),
]
# Where that band sits, as a share of the stand-out: inner edge, then width.
# Solved rather than picked (`out/ear2/band.py`). Every point of the fold has to
# clear the skull on one side and the rim on the other by a crease's own stroke
# width, at both builds, which is two inequalities per point and linear in these
# two numbers; this is the widest band that satisfies all of them, and it leaves
# the inner edge with a hundredth of slack. Three candidate bands were rendered
# first and the chibi tiles were not distinguishable by eye, which is what makes
# this worth solving instead: the eye had nothing to go on and the constraint
# does. The band picked by eye turned out to be infeasible at the adult.
_EAR_FOLD_IN = 0.30
_EAR_FOLD_SPAN = 0.45


def _ear_span(build: float) -> tuple[Point, Point]:
    """Where the ear joins the skull, top and bottom, on the right side."""
    return (
        (_head_edge_x(_EAR_TOP_Y, build), _EAR_TOP_Y),
        (_head_edge_x(_EAR_BOT_Y, build), _EAR_BOT_Y),
    )


def _ear_place(build: float) -> Callable[[Point], Point]:
    """Maps a traced (along, out) onto the skull, in head radii.

    `along` runs the attach chord and `out` is measured straight along x, not
    perpendicular to the chord. The chord is not near vertical, 16 degrees off
    at the chibi and 19 at the adult, so the two are not the same thing: x is
    the deliberate one, because `_EAR_OUT` is defined as how far the ear stands
    clear of the skull sideways, and a perpendicular offset would shorten it by
    the cosine and by a different amount at each build. Riding the chord rather
    than a fixed x is what welds the traced shape to a skull whose own width
    moves with the build.
    """
    (top_x, top_y), (bot_x, bot_y) = _ear_span(build)

    def place(pt: Point) -> Point:
        along, out = pt
        return (top_x + (bot_x - top_x) * along + out * _EAR_OUT, top_y + (bot_y - top_y) * along)

    return place


def _ear_outer(build: float) -> tuple[Point, list[Segment]]:
    """The ear's outer contour, top attach to bottom attach, on the right side.

    The helix is the only thing this draws, traced off the canon chibi. What was
    here before was two quadratics out to a widest point and back, which is the
    right idea and the wrong curve: the canon's rim leaves the top attach much
    faster than a single control can, holds its width through the middle of the
    ear rather than peaking, and comes back in along the lobe. Four segments,
    which is the finest the line weight supports.
    """
    place = _ear_place(build)
    return place(_EAR_ARC_START), [(place(c), place(e)) for c, e in _EAR_ARC]


def _ears(sk: Skeleton, p: CharacterParams) -> str:
    """Ears, drawn *under* the head so the face's own outline runs across them.

    That is the canon's construction, and looking at it beside ours was what
    settled it (`out/ear2/depth.png`, the owner's call on 2026-08-07): the
    reference draws one unbroken heavy line down the side of the face and the
    ear behind it, with only the part past that line showing. Drawn over the
    head instead, the ear's rim runs into the face's outline and joins it, and
    the two read as one silhouette that happens to bulge rather than as an ear
    behind a face.

    So what is visible here is the arc outside the skull and nothing else. The
    fill still closes on a straight chord between the attach points, but the
    chord and everything inboard of it is now painted over by the head; it is
    there to give the sliver outside the skull something to be part of. Only the
    outer arc carries a stroke, and the arc meets the skull exactly at both
    attach points, so it emerges from the face's outline rather than crossing
    it.
    """
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    sw = _stroke_w(sk)
    start, segments = _ear_outer(sk.build)
    place = _ear_place(sk.build)

    # The antihelix, traced with the rim. It stops well short of both ends, as
    # the canon's does: run it to the lobe and it closes into a second outline,
    # which reads as a hole rather than as the turn of a rim.
    def fold(pt: Point) -> Point:
        return place((pt[0], _EAR_FOLD_IN + pt[1] * _EAR_FOLD_SPAN))

    crease_start = fold(_EAR_FOLD_START)
    crease = [(fold(c), fold(e)) for c, e in _EAR_FOLD]

    parts = []
    for side in (-1, 1):
        ear_start, ear_segments = (start, segments) if side > 0 else _mirror(start, segments)
        c_start, c_segments = (crease_start, crease) if side > 0 else _mirror(crease_start, crease)
        parts.append(
            f'<path d="{_curve(cx, cy, r, ear_start, ear_segments)}" fill="{p.skin_tone}" />'
        )
        parts.append(
            f'<path d="{_curve(cx, cy, r, ear_start, ear_segments, close=False)}" fill="none" '
            f'stroke="{OUTLINE}" stroke-width="{sw:.1f}" stroke-linecap="round" />'
        )
        parts.append(
            f'<path d="{_curve(cx, cy, r, c_start, c_segments, close=False)}" fill="none" '
            f'stroke="{OUTLINE}" stroke-width="{sw * 0.55:.1f}" stroke-linecap="round" />'
        )
    return "".join(parts)


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
    # A list, one entry per side, rather than one chain mirrored here. Mirroring
    # was a hidden assumption that every cut is symmetric, and it was silent until
    # one was not: the traced crop's right-hand edge got stamped onto its left,
    # where the mass is a different shape, and drew a row of black barbs standing
    # off the silhouette with white between them and the hair. A cut that is
    # symmetric says so by handing back both sides.
    for edge_start, edge_segments in style.fall_edge(fall):
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
        # The ear goes under the head and over the back hair: the canon runs the
        # face's outline unbroken across the ear and hangs the hair behind it.
        _ears(sk, p),
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
