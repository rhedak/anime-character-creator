"""Assembles a character from flat vector shapes anchored to a
Skeleton. Every shape is plain SVG (paths, circles, capsule-strokes) so
recoloring is just swapping a fill/stroke attribute and the whole figure
scales as one unit via the skeleton's head_r.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace

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
    # Fine wire spectacles. On `FaceStyle` rather than `Outfit` because they are
    # part of a face the way a scar is: nobody in this cast is drawn once with
    # them and once without, and an expression must not be able to remove them.
    glasses: bool = False
    # Which cheek carries a scar, **stated from the viewer's side**: -1 the left
    # of the picture, 1 the right, 0 none. The figure faces us, so the viewer's
    # right is the character's left, and a description written the other way
    # round ("a burn along her left cheek") means 1 here, not -1. Worth spelling
    # out because both frames are in use: this file counts in picture space and
    # every character description counts in body space, and the two disagree on
    # every single scar without ever disagreeing visibly enough to notice.
    scar_side: int = 0


@dataclass(frozen=True)
class Expression:
    """A mood, as a **delta** on whatever face a character already has.

    Not a `FaceStyle`, and the distinction is the whole point. A `FaceStyle`
    carries two different kinds of thing: what a face *is* (`eye_size`,
    `eye_width`, `eye_corner`, `eye_tilt`, `iris_size`) and what it is *doing*
    right now (`brow_tilt`, `mouth_curve`, `eye_openness`). Satoshi's aperture is
    0.92 wide and 1.08 long because that is his face at rest, in every scene, and
    an expression that arrived as a whole `FaceStyle` would quietly overwrite it
    with the stock values and hand back a different character wearing the right
    mood.

    So every field here is `None` by default, meaning *leave that one alone*, and
    only the named fields are written. `None` rather than a neutral number
    because there is no number that means "unchanged": 0.0 is a real brow tilt,
    and a level brow is a choice a mood can make.

    Fields are limited to the ones a mood moves. Adding `eye_size` here would be
    a way to make a character stop being themselves.
    """

    # 0 is level. Positive drops the inner ends (stern), negative raises them,
    # which is the grief reading rather than more of the same.
    brow_tilt: float | None = None
    brow_weight: float | None = None
    # How high the upper lid rides. This is the one that survives being shrunk:
    # a brow is a thin stroke and washes out at thumbnail size, where a lid
    # changes the shape of a filled mass. Measured at about four times the
    # signal of `brow_tilt` on the cover, at both sizes.
    eye_openness: float | None = None
    eye_lower_lid: float | None = None
    mouth_curve: float | None = None
    mouth_width: float | None = None

    def on(self, face: FaceStyle) -> FaceStyle:
        """This mood, over one face, leaving everything unnamed as it was."""
        stated = {k: v for k, v in asdict(self).items() if v is not None}
        return replace(face, **stated)

    def applied_to(self, p: CharacterParams) -> CharacterParams:
        """The same, on a whole character."""
        return replace(p, face=self.on(p.face))


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
    # --- Uniform trim. Five fields rather than one `uniform=True`, because the
    # cast does not wear the uniform as a unit: Tenno has the cut without the
    # strap, Elara and Krista hang crystals off the belt that nobody else
    # carries, and a coat wants the collar without any of the rest. Each is off
    # by default and draws nothing, which is what keeps them general.
    #
    # What is here is the minimum that reads at the size a character is seen on
    # a sheet: a closed collar, a line of buttons, a pocket on each breast, a
    # strap across the chest, a boot that climbs the calf. Rank tabs, shoulder
    # boards, cuff piping and hip pockets are all in the references and all
    # below that line; see `docs/character-roster-plan.md`.
    #
    # A standing collar closing at the throat, in place of the open V. Its own
    # colour, so a uniform's collar can differ from the tunic it sits on.
    collar_color: str | None = None
    # A row of buttons down the centre front, from collar to belt.
    placket_color: str | None = None
    # A flapped pocket on each breast.
    chest_pocket_color: str | None = None
    # A strap from one shoulder across to the opposite hip. Worn over the tunic
    # and under the arms, which is where a real one sits and also the only place
    # it does not clip a hand.
    strap_color: str | None = None
    # How far up the shin the boot climbs, on top of the ankle boot every
    # character already has: 0 leaves it alone, 1 takes it to the knee.
    boot_shaft: float = 0.0
    # --- Robe. Three fields, and between them they carry the whole cluster:
    # what says "kimono" at tile size is a front that crosses, a sleeve that
    # hangs, and a wide sash. Embroidery, the checked panels, layered inner
    # collars and sword furniture are all in the references and all below the
    # first-draft line.
    #
    # A panel crossing the chest, right over left, in place of the tunic's
    # symmetric front. Its own colour so an outer robe can sit over an inner one.
    robe_color: str | None = None
    # How far the sleeve hangs below the tunic's own short one, shoulder (0) to
    # hip (1). A kimono sleeve is a bag of cloth, not a tube on an arm, so this
    # hangs from the shoulder rather than following the arm inside it.
    sleeve_drop: float = 0.0
    # How much taller the belt band is than the default. An obi is the same
    # object as a belt, three or four times the height, and giving it a scalar
    # rather than its own garment means a buckle and a sash cannot disagree
    # about where the waist is.
    belt_scale: float = 1.0
    # A wide pleated lower garment worn over the legs, under an open kimono or
    # robe: Haruto and Reika both wear one. Its own field rather than a pleat
    # count on `skirt_color`, because the two are not the same shape at the
    # same length: nobody wears both, but Haruto wears trousers under a hakama
    # that stops short of his boots, which only works if the two are
    # independent layers rather than one field pulling double duty.
    hakama_color: str | None = None
    # Same hip(0)-ankle(1) measure `skirt_length` uses. A hakama reads close to
    # floor-length in both references; `None` takes the skeleton's own hem,
    # which is shorter, so a hakama that wants the reference's length has to
    # ask for it explicitly the way `skirt_length` already does.
    hakama_length: float | None = None
    # A cloth tied over the head, covering the crown and leaving the face and a
    # little hair showing. Worn rather than grown, so it is here and not on
    # `CharacterParams` beside the hair.
    headscarf_color: str | None = None
    # A pair of lenses on a strap, pushed up onto the forehead rather than worn
    # over the eyes. Frame and strap color only; the lens tone is derived from
    # it with `shade()` the same way a shadow tone is, lighter rather than
    # darker, so a goggle color always ships with a glass that reads against it.
    goggle_color: str | None = None
    # An outer layer hanging open over whatever is worn under it: a cropped
    # jacket, a lab coat, a long coat. One garment rather than three, because
    # the three differ only in where the hem lands.
    coat_color: str | None = None
    # Where the coat's hem falls, shoulder (0) to ankle (1). Roughly: 0.30 a
    # jacket cropped at the waist, 0.62 below the knee, 0.75 mid-calf.
    coat_length: float = 0.55
    # Four mana crystals clipped to the belt, two a side, the carrying rig
    # Elara and Krista wear instead of a pouch: a crystal is dangerous to grip
    # bare-handed (`valley_of_mist/docs/design.md`, "Donarsblut"), so it rides
    # in a loop rather than a pocket, and stays visible rather than stowed.
    # Four fields rather than one `crystal_color`, because the point of a
    # working mage's rig is that the stock is not all the same type; each
    # slot is independently optional, so a character can wear fewer than
    # four, same as any other garment here. Left outer, left inner, right
    # inner, right outer. Needs a belt to clip to, same as `pouch_color`.
    crystal_color_1: str | None = None
    crystal_color_2: str | None = None
    crystal_color_3: str | None = None
    crystal_color_4: str | None = None
    # A small cutting/handling tool clipped beside the rig, standard Crystal
    # Conclave kit for a stock nobody grips bare-handed. Optional and off by
    # default: it is a second read at a scale where the crystals alone are
    # already close to the floor, so it only earns its keep on a character
    # deliberate enough about the kit to ask for it explicitly. Draws nothing
    # unless a belt is worn.
    crystal_tongs: bool = False


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
    # Hair that leaves the skull and comes back: a tail hanging behind the head,
    # and a knot gathered on the crown. Both are separate parts rather than
    # `Hairstyle` entries, which is what makes them cheap: a `Hairstyle` is five
    # callables that have to agree with each other and with the ceiling test,
    # while these two compose with *any* cut, so one shape gives Krista her
    # ponytail and Haruto and Daizen their topknots without touching the five
    # existing cuts at all.
    #
    # How far the tail falls, shoulder (0) to hip (1). 0 is no tail.
    hair_tail: float = 0.0
    # A knot gathered on the crown, sitting proud of the skull.
    hair_knot: bool = False
    # Facial hair. None leaves the face bare, which is everybody but two.
    # Its own colour rather than reading `hair_color`, because a beard greys
    # before the head does on one of the two who wear one, and because a
    # character could dye one and not the other.
    beard_color: str | None = None
    # How far the beard drops below the chin, in head radii: 0.07 is the short
    # groomed beard Reinhard wears, 0.17 the fuller one Daizen does.
    beard_length: float = 0.15
    outfit: Outfit = field(default_factory=Outfit)
    face: FaceStyle = field(default_factory=FaceStyle)
    # Head-heights tall. Ignored when render_character is handed a skeleton.
    heads: float = DEFAULT_HEADS
    # Shoulder against hip: -1 narrow-shouldered and wide-hipped, 0 neutral, +1
    # the other way. Only bites at taller builds. Ignored when handed a skeleton.
    frame: float = 0.0
    shaded: bool = True


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


def _scale_point(pt: Point, k: float) -> Point:
    """A point scaled by `k` from the head centre. Shared by whichever traced
    contour is being blown up from its as-measured size, long or crop."""
    return (pt[0] * k, pt[1] * k)


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


def _center_part_hairline_shape(length: float) -> tuple[Point, list[Segment], list[Segment]]:
    """`_hairline_shape`, with the fringe parted at the centre instead of swept
    to one side: two even sweeps off a single peak at x=0, mirrored left and
    right, in place of the one asymmetric sweep off a part right of centre
    that cut carries. Everything else, both falls, the crown closure, is
    that function's own geometry unchanged, since this cut reuses
    `_hair_mass_shape` and `_fall_edge` outright and has to retrace their
    seams exactly or the double-line the hair contract warns about (see
    `_hairline_shape`) shows up here too.
    """

    def y(f: float) -> float:
        return _fall(f, length)

    start: Point = (-1.22, y(1.00))
    line: list[Segment] = [
        ((-1.18, y(0.97)), (-1.08, y(0.85))),
        ((-0.98, y(0.60)), (-0.90, y(0.28))),
        ((-0.92, 0.70), (-0.88, 0.35)),
        # The part: two even sweeps off one peak at the crown's own centre
        # line. This is the entire visual difference from `_hairline_shape`;
        # everything else in this function is copied from it verbatim.
        ((-0.68, 0.14), (-0.42, -0.14)),
        ((-0.18, -0.36), (0.00, -0.46)),
        ((0.18, -0.36), (0.42, -0.14)),
        ((0.68, 0.14), (0.88, 0.35)),
        ((0.92, 0.70), (0.90, y(0.28))),
        ((0.98, y(0.60)), (1.08, y(0.85))),
        ((1.18, y(0.97)), (1.22, y(1.00))),
    ]
    _, right_edge = _fall_edge(length)
    _, left_down = _reverse(*_mirror(*_fall_edge(length)))
    back: list[Segment] = [
        *right_edge,
        ((1.05, 0.10), (1.00, -0.30)),
        ((0.84, -1.16), (0.00, -1.10)),
        ((-0.84, -1.16), (-1.00, -0.30)),
        ((-1.05, 0.10), (-_FALL_CHEEK_X, _HAIR_CHEEK_Y)),
        *left_down,
    ]
    return start, line, back


def _center_part_strands(length: float) -> list[tuple[Point, list[Segment]]]:
    """Division lines for the centre-part cut: mirrored sweeps off the part
    in place of `_long_strands`' off-centre crown sweeps and fringe flicks.
    The fall-dividing lines (`outer_lock` and the shorter inner pair) are
    `_long_strands`' own, unchanged, since both cuts share the same fall."""

    def y(f: float) -> float:
        return _fall(f, length)

    outer_lock: tuple[Point, list[Segment]] = (
        (1.14, 0.10),
        [((1.42, y(0.28)), (1.38, y(0.58))), ((1.32, y(0.78)), (1.36, y(0.94)))],
    )
    sweep_outer: tuple[Point, list[Segment]] = (
        (-0.30, -0.86),
        [((-0.54, -0.68), (-0.72, -0.44))],
    )
    sweep_inner: tuple[Point, list[Segment]] = (
        (-0.12, -0.82),
        [((-0.28, -0.62), (-0.40, -0.40))],
    )
    flick: tuple[Point, list[Segment]] = (
        (-0.14, -0.60),
        [((-0.26, -0.48), (-0.36, -0.32))],
    )
    return [
        sweep_outer,
        _mirror(*sweep_outer),
        sweep_inner,
        _mirror(*sweep_inner),
        outer_lock,
        _mirror(*outer_lock),
        ((1.04, 0.40), [((1.18, y(0.30)), (1.15, y(0.55)))]),
        ((-1.04, 0.40), [((-1.18, y(0.30)), (-1.15, y(0.55)))]),
        flick,
        _mirror(*flick),
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
# Holds for both the chibi trace below and the realistic one further down:
# both put the same number of segments between a fall's tip and the crown, so
# the split lands in the same place in either list.
_LONG_CROWN_AT = 9

# Satoko's realistic-build hair, traced directly off `ref/satoko-real.jpg`
# rather than scaled up from the chibi trace above. The chibi crown, run
# through `_long_scaled`, used to stand in for the adult one too: only the
# fall stretched, and the crown, sized for the chibi's own 2.5x hair
# clearance, rode along unchanged onto a head with much less room for it. The
# strand lines cut for that fuller crown then crossed and doubled back on
# themselves over the smaller one, which is the "lines overlap" the owner
# flagged. `harness/trace/real/satoko_real.py` carries the trace: a hair-
# colour region grown from a seed in the crown, since there is no isolated
# hair crop for this reference the way `../satoko.py`'s chibi trace has, and
# reading ink on the full photo would confuse the mass's edge with the
# tunic's the moment a bearing crossed both, the same failure the fringe
# trace hit and solved the same way, by region rather than by ink.
_LONG_REAL_EDGE_START: Point = (-0.609, 1.875)
_LONG_REAL_EDGE: list[Segment] = [
    ((-0.654, 1.953), (-0.699, 2.031)),
    ((-0.832, 1.572), (-0.859, 1.273)),
    ((-0.976, 1.374), (-1.050, 1.393)),
    ((-1.055, 1.376), (-1.061, 1.359)),
    ((-0.978, 0.829), (-0.933, 0.606)),
    ((-0.928, 0.053), (-0.870, -0.334)),
    ((-0.837, -0.460), (-0.783, -0.590)),
    ((-0.702, -0.733), (-0.579, -0.859)),
    ((-0.471, -0.941), (-0.346, -1.006)),
    ((-0.152, -1.078), (0.056, -1.071)),
    ((0.329, -0.999), (0.571, -0.879)),
    ((0.698, -0.755), (0.785, -0.613)),
    ((0.840, -0.471), (0.881, -0.338)),
    ((0.935, 0.061), (0.955, 0.694)),
    ((1.015, 0.927), (1.074, 1.374)),
    ((1.015, 1.402), (0.870, 1.290)),
    ((0.832, 1.570), (0.710, 2.061)),
]
_LONG_REAL_LINE_START: Point = (-0.566, 1.599)
_LONG_REAL_LINE: list[Segment] = [
    ((-0.634, 1.105), (-0.695, 0.571)),
    ((-0.695, 0.264), (-0.679, -0.036)),
    ((-0.622, -0.036), (-0.574, -0.050)),
    ((-0.396, -0.163), (-0.253, -0.262)),
    ((-0.219, -0.230), (-0.186, -0.199)),
    ((-0.113, -0.232), (-0.060, -0.261)),
    ((0.027, -0.343), (0.130, -0.454)),
    ((0.183, -0.532), (0.224, -0.616)),
    ((0.256, -0.518), (0.308, -0.424)),
    ((0.434, -0.274), (0.583, -0.124)),
    ((0.624, -0.080), (0.680, -0.071)),
    ((0.689, -0.021), (0.704, 0.025)),
    ((0.715, 0.317), (0.705, 0.613)),
    ((0.637, 1.116), (0.588, 1.597)),
]
# The `fall` (`_hair_fall`'s return value) this trace was measured at: Satoko's
# own `hair_length=0.45` run through the realistic build's own chin-hip span.
# It is not a build number because `fall` already is one, folding build and
# hair_length into a single figure, and this trace is only valid at the
# specific silhouette it was read off, not at "any adult build" or "any
# length". A longer or shorter cut would need its own trace, which is the
# `docs/character-roster-plan.md`-style work the owner deferred to a later
# pass; the same goes for anything taller than `--build realistic` itself,
# since `fall` keeps growing past heads 6 (the body keeps lengthening even
# though the head-relative anchors are already clamped) and carries no trace
# of its own to fall back on out there.
#
# `_LONG_REAL_TOL` used to be 0.05, wide enough that a `--heads` some way off
# 6.0 could still land inside it: Krista's own `fall` (2.751 at exactly
# `realistic`, a different length on the same cut) drifts up to 2.86-2.89 by
# `--heads` 6.2-6.5 and was wrongly picked up there. 0.001 is tight enough to
# still catch Satoko and Kyoko at `--build realistic` (their computed `fall`
# is 2.8765, 0.0005 off the constant above, which is only the gap from
# writing it down to three places, not something the tolerance needs to
# cover on its own) while shrinking Krista's and Keiko's accidental windows
# from about 0.2 of a head to a few thousandths, well past anything a
# `--heads` typed by hand would land on. It does not remove the possibility
# outright, a bare `fall` match can never rule out every coincidence, only
# make one implausible: this was a deliberate, narrower call than threading
# `heads` through the whole hairstyle dispatch, made because the taller-build
# gap above is already out of scope for this trace.
_LONG_REAL_FALL = 2.877
_LONG_REAL_TOL = 0.001
# The trace above is faithful to the photo and reads thin next to the chibi:
# this house's whole style is built on a chibi's generous, larger-than-life
# hair, and a silhouette sized exactly to an adult reference loses that
# weight even though it is the more "correct" contour. Scaled up from the
# head centre rather than re-measured bigger, since the shape that fixed the
# overlapping lines is worth keeping; only its size against the head was
# ever the complaint. Capped under 1.26: `build_skeleton`'s `hair_margin` at
# the realistic build puts the ceiling no hair ink may cross at 1.36 head
# radii above centre, and the traced crown's own apex already sits at 1.078,
# so anything scaled past about 1.26 paints into the canvas edge.
_LONG_REAL_SCALE = 1.2
# How far above the real trace's own lower edge the gold gives way to the
# pale tips, in the same head radii the trace's points are in. `_LONG_TONE_LIFT`
# is this cut's chibi value and does not carry over as it stands: it is
# multiplied there by `fall / _LONG_BASE_TIP`, a scale factor that only
# means something against the chibi-scaled edge, which stretches with
# `fall`. The real trace's edge does not stretch, it is a fixed, already-
# adult shape, so that multiplier (about 1.7 at this trace's own `fall`) was
# being applied to the wrong basis.
#
# 0 rather than some other positive number: swept 0, 0.3, 0.62, 1.06, 1.6 and
# 2.4 against a render. None of them move the split most of the mass reads
# at, which `_fade_y`'s own clamp sets regardless of `lift` for every point
# already above it, that is most of the mass at this trace's depth. What
# every *nonzero* value in that sweep did instead was poke a small gold
# wedge through the pale at the foot of one fall or the other, the same
# defect the docstring above already names, and which side it poked through
# did not move smoothly with `lift`: left at 0.3, right at 0.62, left again
# at 1.06, right at 1.6, neither at 2.4. That is the six-samples-per-segment
# walk crossing the fade threshold at a different sample for a different
# `lift`, a threshold effect rather than a continuous one, so do not expect
# some nearby value to be smoothly better or worse than 0. 0 is simply the
# one value tried that hit neither side, and it costs nothing obvious to
# read off: this trace's own two tips already sit within 0.03 head radii of
# each other (`_LONG_REAL_EDGE`'s two endpoints), so a level cut and a
# tip-following one do not visibly differ here anyway.
_LONG_REAL_TONE_LIFT = 0.0


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

    Except right at `_LONG_REAL_FALL`, where a real trace exists and is used
    outright instead of stretching the chibi one further than it was ever
    measured to go.
    """
    if abs(fall - _LONG_REAL_FALL) < _LONG_REAL_TOL:
        return _scale_point(_LONG_REAL_EDGE_START, _LONG_REAL_SCALE), [
            (_scale_point(c, _LONG_REAL_SCALE), _scale_point(e, _LONG_REAL_SCALE))
            for c, e in _LONG_REAL_EDGE
        ]
    span = _LONG_BASE_TIP - _HAIR_CHEEK_Y
    k = (fall - _HAIR_CHEEK_Y) / span if span else 1.0

    def q(pt: Point) -> Point:
        y = pt[1]
        return (pt[0], _HAIR_CHEEK_Y + (y - _HAIR_CHEEK_Y) * k) if y > _HAIR_CHEEK_Y else pt

    return q(_LONG_EDGE_START), [(q(c), q(e)) for c, e in _LONG_EDGE]


def _long_line(fall: float) -> tuple[Point, list[Segment]]:
    """The traced hairline, with the stretch that the falls get and the face does
    not: above the cheek line it is pinned to the head, below it it rides the
    fall down. Same `_LONG_REAL_FALL` exception `_long_scaled` has, and for the
    same reason: the traced hairline is already the realistic-build answer,
    not a chibi one waiting to be stretched further."""
    if abs(fall - _LONG_REAL_FALL) < _LONG_REAL_TOL:
        return _scale_point(_LONG_REAL_LINE_START, _LONG_REAL_SCALE), [
            (_scale_point(c, _LONG_REAL_SCALE), _scale_point(e, _LONG_REAL_SCALE))
            for c, e in _LONG_REAL_LINE
        ]
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
    start, edge = _long_scaled(fall)
    if abs(fall - _LONG_REAL_FALL) < _LONG_REAL_TOL:
        lift = _LONG_REAL_TONE_LIFT
    else:
        lift = _LONG_TONE_LIFT * (fall / _LONG_BASE_TIP)
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
    fall. They scale with the mass, since they live on it.

    Except at `_LONG_REAL_FALL`: these points are fixed in head radii, tuned
    against the chibi crown's own 2.5x hair clearance, and `_long_scaled`
    stopped inflating that crown up to realistic-build size once the real
    trace existed. Left in place, they sat where the old, bigger crown used
    to be, well outside the new, tighter one, which is the crossing,
    doubled-back lines the owner flagged as "just doesn't work." Two lines
    placed by eye against `ref/satoko-real.jpg`, the same way the chibi ones
    were: the reference is not run through this trace's own pipeline, since
    a couple of soft, nearly-straight strokes off a parting do not carry
    enough contrast for a region grow or a bearing sweep to find on their own.
    """
    if abs(fall - _LONG_REAL_FALL) < _LONG_REAL_TOL:
        return [
            (
                _scale_point(start, _LONG_REAL_SCALE),
                [(_scale_point(c, _LONG_REAL_SCALE), _scale_point(e, _LONG_REAL_SCALE))],
            )
            for start, c, e in (
                ((-0.16, -0.92), (-0.42, -0.68), (-0.62, -0.32)),
                ((0.20, -0.94), (0.46, -0.70), (0.66, -0.34)),
                ((-0.92, 0.10), (-0.98, 0.75), (-0.94, 1.35)),
                ((0.94, 0.10), (1.00, 0.75), (0.96, 1.35)),
            )
        ]
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

# Satoshi's realistic-build crop, traced directly off `ref/satoshi-real.jpg`
# rather than the chibi trace above at `v` near 1. `_CROP_BASE_TIP` is
# calibrated so `v` already sits at 1.0002 at the realistic build, which
# means the chibi-traced crown was never actually being scaled there at
# all, just reused outright on a head with much less room for the same
# absolute shape, the same "hair rides the build and the crown does not"
# mismatch `STATUS.md` already had measured (crown-to-hairline band 1.035
# head radii at chibi, 0.683 at realistic, against a fixed fringe). Traced
# with `harness/trace/real/satoshi_real.py`, the same region-grown method
# `satoko_real.py` uses.
#
# The first version of this trace (2026-08-11) grew from one seed near the
# crown and stopped at both ears: the reference draws a separate sideburn
# tuft below each ear, a few small pointed locks with no hair-coloured
# pixels joining them to the crown mass, so a single seed's flood fill
# never reached them and the resulting silhouette simply stopped above the
# ears, leaving the jaw unframed. That read as worse than the chibi-scaled
# shape it replaced, which happened to reach nearly to the jaw already
# (its own trace goes to 0.86 head radii on the side against this one's
# 0.36), the wrong kind of "more faithful": faithful to the crown, wrong
# about how far the hair actually goes. Confirmed disconnected rather than
# assumed: a fresh flood fill seeded inside either tuft gives a blob a few
# hundred pixels wide, nothing like the ~14000-pixel main mass. Four more
# seeds, two per side, since each side's tuft is itself two separate blobs,
# fixed it; the trace now reaches the jaw on both sides, matching the
# reference and the chibi build, which already framed the head properly.
#
# `_CROP_REAL_TEMPLE_L/R` and `_CROP_REAL_CROWN_AT` are this trace's own
# version of `_CROP_TEMPLE_L/R`/`_CROP_CROWN_AT`, picked by the same rule
# those were, the segment ending just above the ear and the one ending
# nearest the crown's own centre: the index numbers do not carry over,
# since this list is 42 segments long against the chibi trace's 26, most
# of the extra length being the two sideburn tufts this trace did not use
# to carry at all.
_CROP_REAL_START: Point = (-0.411, 0.968)
_CROP_REAL_EDGE: list[Segment] = [
    ((-0.429, 0.963), (-0.436, 0.935)),
    ((-0.455, 0.935), (-0.498, 0.977)),
    ((-0.517, 0.870), (-0.548, 0.812)),
    ((-0.581, 0.845), (-0.615, 0.878)),
    ((-0.633, 0.790), (-0.648, 0.719)),
    ((-0.684, 0.735), (-0.745, 0.771)),
    ((-0.714, 0.550), (-0.747, 0.449)),
    ((-0.859, 0.414), (-0.895, 0.326)),
    ((-0.965, 0.341), (-1.036, 0.357)),
    ((-0.993, 0.196), (-0.998, 0.070)),
    ((-1.046, 0.064), (-1.094, 0.057)),
    ((-1.012, -0.066), (-1.016, -0.179)),
    ((-1.176, -0.228), (-1.123, -0.239)),
    ((-1.099, -0.377), (-1.050, -0.512)),
    ((-0.994, -0.609), (-0.926, -0.698)),
    ((-0.990, -0.760), (-1.053, -0.823)),
    ((-0.898, -0.845), (-0.814, -0.904)),
    ((-0.634, -1.072), (-0.404, -1.172)),
    ((-0.288, -1.201), (-0.171, -1.216)),
    ((-0.072, -1.202), (0.021, -1.184)),
    ((0.033, -1.246), (0.046, -1.307)),
    ((0.102, -1.283), (0.154, -1.255)),
    ((0.223, -1.186), (0.277, -1.110)),
    ((0.323, -1.132), (0.375, -1.153)),
    ((0.468, -1.163), (0.554, -1.136)),
    ((0.537, -1.078), (0.519, -1.019)),
    ((0.653, -0.969), (0.751, -0.863)),
    ((0.848, -0.661), (1.009, -0.514)),
    ((0.952, -0.475), (0.895, -0.437)),
    ((0.926, -0.268), (0.998, -0.105)),
    ((1.052, -0.091), (0.882, -0.062)),
    ((0.862, 0.115), (0.930, 0.357)),
    ((0.850, 0.392), (0.770, 0.427)),
    ((0.756, 0.513), (0.757, 0.635)),
    ((0.691, 0.589), (0.625, 0.543)),
    ((0.594, 0.595), (0.635, 0.757)),
    ((0.631, 0.795), (0.534, 0.709)),
    ((0.516, 0.772), (0.504, 0.873)),
    ((0.478, 0.865), (0.432, 0.812)),
    ((0.402, 0.856), (0.388, 0.961)),
    ((0.380, 0.992), (0.337, 0.925)),
    ((0.318, 0.948), (0.299, 0.979)),
]
# The two sideburn tufts sit close enough to the skull's own jaw/cheek
# edge that at `_CROP_REAL_SCALE` alone, most of each tuft lands behind
# the head shape drawn over it rather than past it: checked directly
# against `_head_edge_x`, several of the tuft's own points sit inside the
# skull's edge, not outside it, and several more clear it by only a few
# hundredths of a head radius, thin enough that the tuft still reads as a
# broken scribble rather than visible hair. This is the same "clear the
# skull" problem `_EAR_OUT` already exists to solve for the ear, and it
# gets the same kind of fix: an outward push, x only, since y is already
# the tuft's own measured reach and does not need moving. The ranges are
# this trace's own two tufts and stop exactly where each one already
# cleared the skull on its own: edge indices 0-7 (left) and 32-41
# (right); `_CROP_REAL_START` is the left tuft's own tip, pushed the same
# way.
#
# Pushing every point in those ranges the same amount overshot: a few of
# them, at the same height as the ear itself (`_EAR_TOP_Y` to
# `_EAR_BOT_Y`), moved from inside the ear's own outline, correctly
# leaving it visible, to past it, so the pushed hair and the ear fought
# over the same few pixels there. That turned out to be one case of a
# wider problem, not unique to the push: `_ears` draws only the sliver
# standing clear of the skull, from the skull's own edge out to
# `_EAR_OUT` past it, and only within that same height band. Checked
# directly at the realistic build, the only build this trace ever runs
# at, that sliver spans about `_CROP_REAL_EAR_X` in head radii. Several
# of the mass's own points, not only the pushed ones, land inside that
# exact strip at that exact height (the pre-existing zigzag right above
# the ear included), so the hair's own outline and the ear's outline were
# both drawing into the same few pixels regardless of the push, which is
# the tangle the owner flagged rather than a clean ear in a clean window
# the way the canon draws it and the way `_crop_hairline_shape` already
# gives the fringe higher up ("the front hair stops above the ear on
# purpose"). Any such point retreats to the skull's own edge instead,
# computed directly with `_head_edge_x` rather than a guessed margin,
# ceding the strip to the ear. Points at ear height but already outside
# that strip, on either side of it, are untouched: retreating them too
# would pull in hair that was never competing with the ear to begin with.
_CROP_REAL_SIDEBURN_PUSH = 1.3
# -1 stands for `_CROP_REAL_START` itself, the left tuft's own tip.
_CROP_REAL_SIDEBURN_L = range(-1, 8)
_CROP_REAL_SIDEBURN_R = range(32, 42)
_CROP_REAL_EAR_X = (0.717, 0.967)


def _crop_real_point(i: int, pt: Point) -> Point:
    """A point from `_CROP_REAL_EDGE` (or `_CROP_REAL_START` at `i=-1`), at
    render size."""
    x, y = pt
    at_ear_height = _EAR_TOP_Y <= y <= _EAR_BOT_Y
    if at_ear_height and _CROP_REAL_EAR_X[0] <= abs(x) <= _CROP_REAL_EAR_X[1]:
        edge_x = _head_edge_x(y, 1.0)
        x = math.copysign(min(abs(x), edge_x), x)
    elif not at_ear_height and (i in _CROP_REAL_SIDEBURN_L or i in _CROP_REAL_SIDEBURN_R):
        x = x * _CROP_REAL_SIDEBURN_PUSH
    return _scale_point((x, y), _CROP_REAL_SCALE)


_CROP_REAL_TEMPLE_L = 10
_CROP_REAL_TEMPLE_R = 29
_CROP_REAL_CROWN_AT = 20
# The `fall` this trace was measured at: Satoshi's own `hair_length=0.65` (the
# range's neutral value, the length the crop was traced at in the first
# place) run through the realistic build's chin-hip span. Same reasoning
# `_LONG_REAL_FALL` documents: `fall` already folds build and hair_length
# together, so this is only valid at the specific silhouette it was read
# off. Tomohiro shares it unchanged, the same way Kyoko shares Satoko's.
_CROP_REAL_FALL = 0.87215
_CROP_REAL_TOL = 0.01
# Scaled up from the head centre for the same reason `_LONG_REAL_SCALE` is:
# a silhouette sized exactly to the reference reads thin next to a chibi's
# generous hair, and the shape that fixed the crown-vs-fringe mismatch is
# worth keeping at a bigger size rather than re-measuring bigger. Capped
# under where the crown's own apex (1.307 head radii here) would cross
# `build_skeleton`'s realistic-build hair ceiling of 1.36. That ceiling
# bounds all hair ink, the outline stroke's outer half included (see
# `hair_margin`'s own comment), and `_stroke_w` at the realistic build is
# 0.058 head radii, so the apex has only 1.36 - 0.029 = 1.331 to clear
# rather than the full 1.36: 1.331 / 1.307 is about 1.018, tighter headroom
# than Satoko's trace had. An earlier version of this comment compared
# against the full 1.36 and read 1.04, and 1.03 sat here on that basis, past
# the true limit; it painted a few antialiased pixels into row 0 of the
# exported canvas. 1.005 clears it (checked by rendering and reading the
# PNG's own top row back, not by the math alone: antialiasing bleeds the
# stroke a pixel or so past its analytic centre, so the margin computed
# above still isn't quite enough on its own).
_CROP_REAL_SCALE = 1.005

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
#
# **0.26 is the design, not an approximation of the reference.** It was cut to
# 0.14 on 2026-08-09 to bring it closer to `ref/satoshi.png`, which shows gold
# nearly to the tips, and the owner reversed that the same day: at 0.14 the white
# on his fringe is barely noticeable, and the wider split reads better. So this
# is one of the places the reference is deliberately not the target, and the
# standing rule applies, that the references are guides and the final call is by
# eye. Do not "correct" it toward the canon again.
#
# It is also the only thing that sets his boundary. Sweeping `_HAIR_FADE` across
# its whole range leaves his fringe byte-identical, because the lifted edge
# already sits below the level line and so wins; Satoko is the mirror image,
# untouched by this and set entirely by the clamp. The two cuts are independent
# here, which is why his could be put back without moving her.
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
    if abs(fall - _CROP_REAL_FALL) < _CROP_REAL_TOL:
        return _crop_real_point(-1, _CROP_REAL_START), [
            (_crop_real_point(i, c), _crop_real_point(i, e))
            for i, (c, e) in enumerate(_CROP_REAL_EDGE)
        ]
    v = fall / _CROP_BASE_TIP
    start = (_CROP_START[0] * v, _CROP_START[1] * v)
    return start, [((c[0] * v, c[1] * v), (e[0] * v, e[1] * v)) for c, e in _CROP_EDGE]


def _crop_indices(fall: float) -> tuple[int, int, int]:
    """`(temple_l, temple_r, crown_at)` for whichever trace `_crop_outline`
    picked at this `fall`, since the two traces disagree on where those
    points fall in their own point lists."""
    if abs(fall - _CROP_REAL_FALL) < _CROP_REAL_TOL:
        return _CROP_REAL_TEMPLE_L, _CROP_REAL_TEMPLE_R, _CROP_REAL_CROWN_AT
    return _CROP_TEMPLE_L, _CROP_TEMPLE_R, _CROP_CROWN_AT


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
    _, _, crown_at = _crop_indices(fall)
    return [
        _reverse(edge[crown_at][1], edge[crown_at + 1 :]),
        (start, edge[: crown_at + 1]),
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
    temple_l, temple_r, _ = _crop_indices(fall)
    left_temple = edge[temple_l][1]
    right_temple = edge[temple_r][1]
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
    crown = _reverse(edge[temple_l][1], edge[temple_l + 1 : temple_r + 1])[1]
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
    "long_center_part": Hairstyle(
        _hair_mass_shape,
        _center_part_hairline_shape,
        _long_fall_edges,
        _hair_tip_edge,
        strands=_center_part_strands,
        # No `tip_range` and no `volume`, same as `long_blunt`: same mass, same
        # fall, so the same body-relative `hair_length` measure applies.
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
    # How deep the neckline cuts. A working tunic wears an open V; a garment
    # with a standing collar closes at the throat, so the V shrinks to a seam
    # the collar then covers. Left at 0.8 under a collar, the V's outline pokes
    # out below the collar's lower edge and reads as a second neckline.
    notch = sk.neck_half_w * (0.28 if p.outfit.collar_color else 0.8)
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
    if p.outfit.undersleeve_color is not None and p.outfit.collar_color is None:
        # The undersleeve shows once more at the neckline: a sliver of its tone
        # trimming the V, which both canon builds wear. Drawn just inside the
        # notch so the tunic's own outline still bounds it. Not under a collar,
        # where there is no V left to trim.
        notch_t = notch * 0.78
        shape += (
            f'<path d="M {cx - notch_t:.1f} {sy + notch * 0.10:.1f} L {cx:.1f} {sy + notch_t:.1f} '
            f'L {cx + notch_t:.1f} {sy + notch * 0.10:.1f}" fill="none" '
            f'stroke="{p.outfit.undersleeve_color}" stroke-width="{_stroke_w(sk) * 0.9:.1f}" />'
        )
    return shape


def _hair_tail(sk: Skeleton, p: CharacterParams) -> str:
    """A gathered tail hanging behind the head.

    Drawn *behind* the hair mass and the head, so it emerges from the silhouette
    rather than sitting on the face. That is the whole reason this is a part and
    not a `Hairstyle`: a cut owns the outline around the skull, and a tail is by
    definition outside it.

    Narrow where it is bound and swelling below, because a bundle of hair does
    that, and because a constant-width strip reads as a ribbon.
    """
    if p.hair_tail <= 0.0:
        return ""
    cx, r = sk.head_cx, sk.head_r
    color = p.hair_color
    sw = _stroke_w(sk)
    tie_x, tie_y = _tail_tie(sk)
    length = (sk.hip_y - sk.shoulder_y) * max(0.0, min(1.0, p.hair_tail))
    tip_y = tie_y + r * 0.45 + length
    # Off to one side, and **outside the cut**. Measured on the shipped
    # hairstyles, the mass spans about 1.34 to 1.39 head radii either way, so a
    # tail drawn anywhere inside that is behind a filled shape wider than it is
    # and simply does not exist. The first attempt put the belly at 0.42 and drew
    # nothing at all. It has to swing clear of the hair before it falls.
    # Both edges sit **outside the hair**, not just the outer one. The cut spans
    # about 1.39 head radii and the torso is drawn over this as well, so a tail
    # whose inner edge is at 1.02 has its whole body hidden behind one or the
    # other and shows as a sliver. Starting the near edge past the cut is what
    # makes it a bundle beside the head rather than a rim behind it.
    belly = r * 1.88
    near = r * 1.42
    # Pinched at the tie and swelling below it, which is what a bundle of hair
    # gathered in a band does, and what a strip of constant width does not: the
    # first version ran the same width the whole way and read as one side of the
    # haircut being longer than the other.
    d = (
        f"M {tie_x:.1f} {tie_y:.1f} "
        f"Q {cx + belly:.1f} {tie_y + (tip_y - tie_y) * 0.30:.1f} "
        f"{cx + belly * 0.84:.1f} {tip_y:.1f} "
        f"Q {cx + near * 0.86:.1f} {tip_y - (tip_y - tie_y) * 0.18:.1f} "
        f"{cx + near * 0.52:.1f} {tie_y + (tip_y - tie_y) * 0.30:.1f} "
        f"Z"
    )
    return f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'


def _tail_tie(sk: Skeleton) -> tuple[float, float]:
    """Where a ponytail is bound, in canvas coordinates.

    Shared between the tail and the band that binds it, because the two only
    read as one object while they agree, and they are drawn in different layers:
    the tail goes behind the hair and the band in front of it.

    High and back, level with the top of the ear rather than at the nape. That
    height is most of what tells a ponytail from hair simply hanging down, and
    the first version tied it at 0.30 head radii below centre, which is low
    enough that the tail left the head beside the ear and read as a long side
    lock.

    Pulled out from 0.62 head radii above centre to 0.46, and right from 0.62
    to 0.78, once Krista also carried goggles: the two were tuned without
    knowledge of each other and the tie used to land inside the goggle strap's
    own footprint, close enough that the strap only painted over its centre
    and left the tie's own outline poking out past the right lens. Moved along
    the same high-and-back direction rather than picked to dodge the strap, so
    a character with the tail and no goggles is unaffected in anything that
    would show at this size.
    """
    return sk.head_cx + sk.head_r * 0.78, sk.head_cy - sk.head_r * 0.46


# Where the cloth's lower edge meets the side of the head, in head radii: just
# above the ear, which leaves a band of hair showing under it at the temples.
_SCARF_EDGE_Y = -0.26
# How far outside the hair the cloth sits, as a multiple of the cut's own half
# width. Cloth has a thickness and a hem, so a scarf tied over hair stands very
# slightly proud of it; at exactly 1.00 the two outlines land on each other and
# read as one line, which says the cap is painted on.
_SCARF_CLEAR = 1.04


def _headscarf(sk: Skeleton, p: CharacterParams) -> str:
    """A cloth tied over the crown, with a knot at the side.

    Over the hair and over the fringe, because a scarf covers what it is tied
    over; the hair below its edge still shows, which is what stops it reading as
    a swim cap.

    It is the single strongest signal Chiyo's reference carries, and none of the
    levers `aged()` has could reach it: age there is the aperture and the brow,
    and a working woman's headscarf is neither. Worth having as a garment rather
    than as part of a hairstyle, since it is a thing put on and taken off and
    anyone could wear one.

    The edge sits low at the sides and dips at the brow, which is how a scarf
    tied at the back sits. Level across, it reads as a headband.
    """
    if p.outfit.headscarf_color is None:
        return ""
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    color = p.outfit.headscarf_color
    sw = _stroke_w(sk)
    edge_y = _SCARF_EDGE_Y
    # **The hair's width, not the skull's.** This part already knew the rule and
    # applied it in one axis only: `crown` below clears the cut rather than the
    # bone, and this line took the bone. On a long cut that is a fifth of a head
    # radius of hair standing outside the cloth tied over it, so the two outlines
    # cross and the cap reads as a shape painted on the hair rather than as
    # something put on. The owner's report on 2026-08-09.
    #
    # The height this is read at barely matters, which is worth knowing before
    # anyone moves `edge_y`: across the whole band from -0.36 to -0.16 the cut's
    # silhouette runs 1.217 to 1.248, because the falls are near vertical where
    # they pass the temple. The skull over the same band moves twice as far.
    x_edge = _hair_edge_x(edge_y, sk, p) * _SCARF_CLEAR
    # It has to clear the hair, not the skull, or it is buried the way the first
    # topknot was. The cuts top out near -1.28 head radii, and a scarf tied over
    # one sits on it rather than replacing it.
    crown = -1.33
    # An elliptical arc, not a chain of quadratics. Two attempts at this with
    # quadratics came out square-topped, because a quadratic whose control shares
    # its endpoint's height runs flat into that endpoint, and every arrangement
    # of two or four of them that fixes the top breaks the sides. An arc states
    # the dome directly and cannot be flat anywhere.
    rx = x_edge * r
    ry = (edge_y - crown) * r
    left_x = cx - rx
    right_x = cx + rx
    edge_py = cy + edge_y * r
    d = (
        f"M {left_x:.1f} {edge_py:.1f} "
        f"A {rx:.1f} {ry:.1f} 0 0 1 {right_x:.1f} {edge_py:.1f} "
        # The brow edge, dipping toward the face in the middle. A straight run
        # between the two temples is a headband.
        f"Q {cx:.1f} {cy + (edge_y + 0.30) * r:.1f} {left_x:.1f} {edge_py:.1f} Z"
    )
    # The knot, off to one side where a scarf is tied. Two small lobes, because
    # one is a bump and two is a knot.
    kx, ky = cx + x_edge * r * 0.94, cy - r * 0.52
    lobe = r * 0.17
    knot = "".join(
        f'<ellipse cx="{kx + dx * lobe:.1f}" cy="{ky + dy * lobe:.1f}" rx="{lobe:.1f}" '
        f'ry="{lobe * 0.82:.1f}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'
        for dx, dy in ((0.55, -0.5), (0.95, 0.6))
    )
    return f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />{knot}'


def _hair_tie(sk: Skeleton, p: CharacterParams) -> str:
    """The band a ponytail is gathered in, drawn over the hair.

    Over, like the knot and unlike the tail, and for the same reason: the cut is
    a filled shape wider than the skull, so anything behind it is gone. Without
    this the tail emerges from the silhouette with nothing to say it was bound,
    and a bundle of hair that is not visibly tied is just more hair.
    """
    if p.hair_tail <= 0.0:
        return ""
    x, y = _tail_tie(sk)
    r = sk.head_r
    sw = _stroke_w(sk)
    w, h = r * 0.20, r * 0.13
    return (
        f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{w:.1f}" ry="{h:.1f}" '
        f'fill="{p.hair_color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'
        f'<path d="M {x - w * 0.72:.1f} {y - h * 0.30:.1f} '
        f'L {x + w * 0.72:.1f} {y - h * 0.30:.1f}" fill="none" stroke="{OUTLINE}" '
        f'stroke-width="{sw * 0.7:.1f}" stroke-linecap="round" />'
    )


def _hair_knot(sk: Skeleton, p: CharacterParams) -> str:
    """A knot gathered on the crown.

    **Over** the hair mass, not behind it, which is the opposite of the tail and
    the only thing that works. A cut carries its own volume: the shipped ones top
    out around -1.25 to -1.28 head radii while `build_skeleton`'s hair margin
    puts the ceiling at -1.36, so there is under a tenth of a radius of daylight
    above a cut for a knot to poke through. Drawn behind, it is invisible; drawn
    over, it reads as what it is, hair gathered on top of hair, and it cannot
    clip the canvas because it never has to reach above the cut to be seen.
    """
    if not p.hair_knot:
        return ""
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    sw = _stroke_w(sk)
    rx, ry = r * 0.24, r * 0.19
    # Poking above the cut rather than sitting inside it. The shipped cuts top
    # out around -1.25 to -1.28 head radii and the canvas ceiling is -1.36, so
    # this rides at -1.13 and paints to about -1.34 once the stroke's outer half
    # is counted, which is what the ceiling counts. Buried at -1.02 it was a
    # same-coloured ellipse on same-coloured hair, which is nothing at all; at
    # -1.15 it cleared the hair and went 0.001 past the margin, which the test
    # caught and the eye did not.
    cyk = cy - r * 1.13
    # A band under it. One line, and it is the difference between a knot and a
    # lump: hair gathered has to look tied.
    band_w = rx * 0.85
    return (
        f'<ellipse cx="{cx:.1f}" cy="{cyk:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
        f'fill="{p.hair_color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'
        f'<path d="M {cx - band_w:.1f} {cyk + ry * 0.86:.1f} '
        f'L {cx + band_w:.1f} {cyk + ry * 0.86:.1f}" fill="none" stroke="{OUTLINE}" '
        f'stroke-width="{sw * 0.7:.1f}" stroke-linecap="round" />'
    )


def _robe_front(sk: Skeleton, p: CharacterParams) -> str:
    """A kimono's crossed front: one panel laid over the other, right under left.

    The tunic underneath keeps the silhouette; this only changes what the front
    of it says. That is the whole trick at this size, and it is why the robe
    cluster did not need a garment of its own: a torso is a torso, and what makes
    one a kimono is the diagonal where the two panels meet.

    Drawn as one filled panel with a diagonal top edge rather than two panels
    with a seam. Two would be the honest construction and would put a line down
    the middle of the chest, which is what a *coat* does; a kimono's visible
    edge runs from the far shoulder down to the near hip, and only one of them
    shows because the other is underneath.
    """
    if p.outfit.robe_color is None:
        return ""
    cx = sk.head_cx
    color = p.outfit.robe_color
    sw = _stroke_w(sk)
    sy, wy = sk.shoulder_y, sk.waist_y
    belt_y, _bh = _belt_band(sk)
    ww = sk.waist_half_w
    neck = sk.neck_half_w * 0.62
    # The overlapping panel: from the wearer's right shoulder, across the chest,
    # down to the left hip. Its far edge follows the torso, so it cannot show
    # outside the tunic it is laid on.
    torso_at_shoulder = _sleeve_half_w(sk) * 0.80
    d = (
        f"M {cx - neck:.1f} {sy + sk.neck_half_w * 0.45:.1f} "
        f"L {cx - torso_at_shoulder:.1f} {sy + (wy - sy) * 0.22:.1f} "
        f"Q {cx - torso_at_shoulder:.1f} {wy:.1f} {cx - ww:.1f} {belt_y:.1f} "
        f"L {cx + ww * 0.72:.1f} {belt_y:.1f} "
        f"Z"
    )
    # The fold's own edge, drawn as a line rather than left as a fill boundary:
    # panel and tunic can be the same colour on a character who wears one robe,
    # and then the diagonal is the only thing saying anything crossed at all.
    fold = (
        f'<path d="M {cx - neck:.1f} {sy + sk.neck_half_w * 0.45:.1f} '
        f'L {cx + ww * 0.72:.1f} {belt_y:.1f}" fill="none" stroke="{OUTLINE}" '
        f'stroke-width="{sw * 0.8:.1f}" stroke-linecap="round" />'
    )
    return f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw * 0.7:.1f}" />{fold}'


def _hanging_sleeves(sk: Skeleton, p: CharacterParams) -> str:
    """The bag of cloth a kimono sleeve is, hanging off the shoulder.

    Not a tube on an arm. `_arms` draws a limb and a sleeve that follows it,
    which is right for every other garment here and wrong for this one: a
    furisode hangs straight down from the shoulder seam and the arm inside it is
    somewhere else entirely. So this is its own shape, drawn behind the arms, and
    the arm carries on being drawn over it.

    Squared off at the bottom with a rounded outer corner, which is the shape,
    and hanging from the tunic's own sleeve line so the two share an edge instead
    of stacking two outlines at the shoulder.
    """
    drop = max(0.0, min(1.0, p.outfit.sleeve_drop))
    if drop <= 0.0 or p.outfit.robe_color is None:
        return ""
    cx = sk.head_cx
    color = p.outfit.robe_color
    sw = _stroke_w(sk)
    top = _sleeve_hem_y(sk)
    hem = top + (sk.hip_y - sk.shoulder_y) * drop
    outer = _sleeve_half_w(sk) * 1.02
    inner = sk.waist_half_w * 0.98
    r = (outer - inner) * 0.35
    parts = []
    for s in (-1, 1):
        d = (
            f"M {cx + s * inner:.1f} {top:.1f} "
            f"L {cx + s * outer:.1f} {top:.1f} "
            f"L {cx + s * outer:.1f} {hem - r:.1f} "
            f"Q {cx + s * outer:.1f} {hem:.1f} {cx + s * (outer - r):.1f} {hem:.1f} "
            f"L {cx + s * inner:.1f} {hem:.1f} "
            f"Z"
        )
        parts.append(f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />')
    return "".join(parts)


# How far the lapel rises to meet the neck, and how far out from it, both as
# multiples of `neck_half_w`. Named because they were found by rendering a grid
# against `ref/keiko.png`, not picked from the geometry: see `harness/coat/lapel.py`.
_COAT_LAPEL_OUT = 1.7
_COAT_LAPEL_UP = 1.8


def _coat(sk: Skeleton, p: CharacterParams) -> str:
    """An outer layer hanging open, as two panels with the body between them.

    Two panels rather than one shape with a hole in it, which is what makes it
    read as *open*: each has its own outline, and the gap between them shows
    whatever is worn underneath. A single silhouette with a slit drawn on it is
    a coat that is done up, however the slit is coloured.

    One garment covers Tomohiro's cropped jacket, Keiko's lab coat and Kyoko's
    long coat, because those three differ only in where the hem lands, which is
    `coat_length`. Building three would have meant three sets of the same
    mistakes.

    The panels flare on the way down, following the skirt's own flare so a coat
    and a skirt worn together do not disagree about which way cloth hangs, and
    they leave the arms alone: sleeves are the undersleeve's job, and a coat
    sleeve drawn here would land underneath the arm that is drawn after it.

    Each panel's top used to run in one line straight from the throat to the
    shoulder point, which never touches the neck at all: that line sits at or
    below the shoulder height the whole way, so the strip of shoulder next to the
    neck was bare skin on both sides and the two panels read as separate wedges
    resting on the chest rather than one garment worn from the shoulders down.
    The lapel point added between them is what a collar is drawn as everywhere
    else in this file, cloth hugging the side of the neck, and it is what says
    the two panels are the same coat rather than two.
    """
    if p.outfit.coat_color is None:
        return ""
    cx = sk.head_cx
    color = p.outfit.coat_color
    sw = _stroke_w(sk)
    sy = sk.shoulder_y
    hem_y = sy + (sk.ankle_y - sy) * max(0.0, min(1.0, p.outfit.coat_length))
    shoulder_w = _sleeve_half_w(sk) * 0.92
    # The opening: narrow at the throat, wider at the hem, which is how an
    # unfastened coat hangs. Level edges read as a zip left undone.
    gap_top = sk.neck_half_w * 0.55
    gap_hem = sk.waist_half_w * 0.52
    # Follows the skirt's flare where there is one to follow, so the two hems
    # agree; on a character with no skirt it is the same widening a coat does.
    out_hem = max(sk.hip_half_w * 1.06, _skirt_half_w(sk, hem_y) * 0.94)
    waist_y = sk.waist_y
    throat_y = sy + sk.neck_half_w * 0.5
    lapel_x = sk.neck_half_w * _COAT_LAPEL_OUT
    lapel_y = sy - sk.neck_half_w * _COAT_LAPEL_UP
    shoulder_y = sy + (waist_y - sy) * 0.16
    parts = []
    for s in (-1, 1):
        d = (
            f"M {cx + s * gap_top:.1f} {throat_y:.1f} "
            f"L {cx + s * lapel_x:.1f} {lapel_y:.1f} "
            f"L {cx + s * shoulder_w:.1f} {shoulder_y:.1f} "
            f"Q {cx + s * shoulder_w * 1.02:.1f} {waist_y:.1f} "
            f"{cx + s * out_hem:.1f} {hem_y:.1f} "
            f"L {cx + s * gap_hem:.1f} {hem_y:.1f} "
            f"Q {cx + s * gap_top * 1.35:.1f} {waist_y:.1f} "
            f"{cx + s * gap_top:.1f} {throat_y:.1f} Z"
        )
        parts.append(f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />')
    return "".join(parts)


# Where `_face` draws the mouth, in head radii below the head's centre. Shared
# rather than copied, because the beard is built around the mouth: the moustache
# has to clear the lip and the jaw run has to meet it at the corner, and a beard
# built around its own copy of this number agrees with the face on the day it is
# written and silently stops agreeing the first time the mouth moves.
_MOUTH_Y = 0.55

# Where the beard's mass meets the face at the sides, and how far inside the
# skull's edge it lands there. Named constants rather than literals so a sweep
# can try candidates without editing the drawing code; see `harness/beard/`.
#
# The inset was 1.00, landing the top corners exactly on the skull's contour so
# the two outlines merged into one jaw. That was right about the outline and
# wrong about everything else: at the widest part of the face it left no cheek
# either side, so the mass ran ear to ear and the beard read as a hood with a
# face hole cut in it. Pulling it in to 0.87 put skin back beside the beard,
# which is what says the hair is growing on a jaw rather than wrapped round one.
# Four candidates were rendered against both references at head size and at tile
# size, since this part fails in opposite directions at the two sizes.
#
# It then moved back out to 0.93 on 2026-08-09, when the sideburns came to ride
# the same contour: the cheek is now held clear by the top edge's dive past the
# mouth rather than by this number, so what 0.87 bought was no longer a cheek but
# a band of skin between the strip and the hair above it, and a sideburn that
# does not reach the hair is a strap. 0.98 was tried too and is the old failure
# coming back, the beard meeting the hair along the whole side and closing the
# face in. See `harness/beard/sideburn.py`, which carries the old two-quadratic
# version alongside so the change can be judged as one.
_BEARD_TOP = 0.63
_BEARD_SIDE_INSET = 0.93
# How high the sideburn strip climbs the side of the face, in head radii from the
# head centre. About level with the top of the ear: high enough to meet the hair,
# and no higher, because a strip that carries on past the ear is a chinstrap.
_BEARD_SIDEBURN_Y = 0.02
# How far out the strip's outer edge starts, as a share of the skull's own edge.
# Just inside rather than on it, so the outline's stroke has somewhere to sit: at
# 1.00 half the line weight lands outside the head.
_BEARD_SIDEBURN_OUT = 0.99
# The strip's width in head radii, at the top and where it runs into the mass.
#
# **Wider at the bottom**, which is the way round a real sideburn goes and the
# opposite of what was here. The strip used to start 0.31 head radii wide at eye
# level and converge to 0.06 at the jaw, and a band whose two edges converge is a
# triangle: it read as a cut-out or a chinstrap rather than as hair, on both
# wearers, at both sizes. Against `ref/reinhard.png` the strip is narrow down the
# front of the ear and only spreads where it meets the beard, so the taper is
# inverted here and the numbers are small.
#
# The top width does two more jobs, and both want it small. It sets how much of
# the strip's top cut shows, that cut being a horizontal level with the top of the
# ear, and a long one reads as the edge of something worn rather than the top of
# some hair. And it decides how hard the strip collides with what is already at
# that height: 0.02 head radii is the head at its widest, where the side hair
# comes down and one hundredth above where the ear attaches, so three outlines
# arrive in the same place and at 0.08 they butt into each other instead of one
# tucking under another. At 0.04 the strip arrives as a taper thin enough to slip
# under the fringe, and it clears the ear rather than crossing it.
_BEARD_SIDEBURN_W_TOP = 0.04
_BEARD_SIDEBURN_W_BOT = 0.17
# How late the strip opens out. Above 1 it stays near its top width for longer and
# flares near the jaw instead of widening evenly the whole way down.
#
# Which is what the crowding actually wants, because only one end of this span is
# crowded. Widening evenly puts the strip back at a colliding width a short way
# down, still inside the stretch the ear runs alongside; at 2.0 it is half its
# final width only in the last third, which is past everything it can hit and is
# also the shape `ref/reinhard.png` has, a thin line in front of the ear that
# spreads at the jaw.
_BEARD_SIDEBURN_W_EASE = 2.0
# The moustache: how high it reaches at the centre, and how far out it runs
# before the edge turns down the jaw. Both in head radii.
#
# This is what stops the beard reading as a neckbeard. The top edge used to dive
# to about 0.895 in the middle with the chin at 1.0, so the mass covered the last
# tenth of the chin and hung below it, leaving bare skin from the lower lip to the
# jaw: shaved the face, kept the neck. The owner's call on 2026-08-09 was to bring
# the coverage up over the chin and around the mouth.
#
# **Raising the edge is not the same as raising it evenly**, and that distinction
# is the whole part. A level edge across the lower face is a surgical mask, which
# is what the first attempt at this drew and what the dive existed to avoid. So
# the edge stays low where it crosses the cheek and rises only in the middle, over
# a span narrow enough to read as a moustache. `_BEARD_TASH_HALF` is that span;
# past about 0.36 the lobe stops being a moustache and the mask comes back.
#
# The height is set by what is left between the lobe and the lip, not by where the
# lobe sits. At 0.46 that band came to 0.037 head radii, which on an 88 pixel head
# is 3.3 pixels of hair inside a 4 pixel outline: what got drawn was a line above
# the mouth rather than a moustache, and the owner's read was exactly that. At
# 0.36 it is 0.137, about a seventh of a head, which is a moustache. The other end
# is close: 0.31 was rendered too and the lobe starts climbing toward the nose and
# reads as a snout.
_BEARD_TASH_Y = 0.36
_BEARD_TASH_HALF = 0.28
# The lips, showing through. Both as multiples of the mouth's own half width, so
# the lozenge keeps its proportions on a character whose mouth is narrow; zero
# draws none.
#
# Without this the hair round the mouth and the hair under it are one unbroken
# field of colour, and a solid field over the whole lower face is a mask no
# matter what its outline does. The lip is what makes the same shape read as a
# moustache above and a beard below, and it is why a beard can cover the mouth
# at all without swallowing the face.
_BEARD_LIP_W = 2.3
_BEARD_LIP_H = 0.63


def _beard(sk: Skeleton, p: CharacterParams) -> str:
    """Facial hair: a mass round the mouth and the chin, hanging below the jaw.

    Welded to the skull the way the ear is, by sampling `_head_edge_x` rather
    than by assuming a circle, so it follows the jaw taper as the build gets
    taller instead of standing off the face at one end of the range.

    Drawn over the head and under the face, which is what lets the moustache
    exist: the skull's chin outline would otherwise run across the mass, and the
    mouth has to sit on top of the hair around it rather than under it.

    A moustache is not a separate part. It is the middle of this one path's top
    edge, lifted over the lip, which is also why that edge is four curves: it has
    to stay off the cheek at the sides and climb in the middle, and one curve can
    only do one of those.
    """
    if p.beard_color is None:
        return ""
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    b = sk.build
    color = p.beard_color
    sw = _stroke_w(sk)
    # Where the mass meets the face at the sides. Level with the mouth, which is
    # as high as it can go before the cheek starts disappearing: the head is at
    # its widest just above this, so every step upward here adds a band of face
    # width to the mass and the beard turns into a hood.
    top = _BEARD_TOP
    # How deep the growth is, which since 2026-08-09 is a depth rather than a
    # length: the bottom rides the jaw and this is how far it sinks below it. It
    # used to set how far a swung arc reached past the chin, which is why the
    # preset values dropped by more than half when the shape changed.
    drop = max(0.0, p.beard_length)
    # Everything below rides `_BEARD_SIDE_INSET`, which keeps the mass **on** the
    # skull's edge rather than inside it. Tucked inside, the face's own outline
    # runs across above the beard, the mass below reads as a separate object
    # hanging off the chin, and what comes out is a scarf. The cheek is kept clear
    # by *height* instead: `top` sits below the head's widest point, so there is
    # face above the beard rather than beside it.
    #
    # **The sideburns are what make it read as facial hair at all.** Without them
    # the mass hangs under the jaw connected to nothing, and every version of that
    # came out as a scarf, a collar or a neck warmer no matter how it was shaped
    # or toned. A strip running up the side of the face to the hairline is the
    # thing that says the beard grows out of the head, and it costs two points on
    # each side of the path.
    #
    # Narrow, and **following the skull's own edge point by point**, so the strip
    # hugs the cheek instead of standing off it. Both edges used to be one
    # quadratic apiece, which chords across a curve rather than riding it: the
    # control could set where the line bulged but not make it agree with the face,
    # and what came out was two straight diagonals. `_face_track` samples the same
    # contour the outline is drawn from, so the strip curves with the cheek at any
    # build for free.
    #
    # `_BEARD_SIDEBURN_Y` is where it reaches: high enough to meet the hair, and
    # no higher, since a strip climbing past the ear is a chinstrap.
    burn_y = _BEARD_SIDEBURN_Y
    # The inner edge runs lower than the outer one, down to where it meets the top
    # edge's dive, so it gets its own span rather than sharing the outer one.
    join_y = top + 0.14
    outer = _face_track(burn_y, top, b, _BEARD_SIDEBURN_OUT, _BEARD_SIDE_INSET)
    inner = _face_track(
        burn_y,
        join_y,
        b,
        _BEARD_SIDEBURN_OUT,
        _BEARD_SIDE_INSET,
        _BEARD_SIDEBURN_W_TOP,
        _BEARD_SIDEBURN_W_BOT,
        _BEARD_SIDEBURN_W_EASE,
    )

    # Where the top edge turns: the moustache's outer end sits a touch below the
    # mouth so the two corners meet, which is where a beard and a moustache join
    # on a face.
    x_join = inner[-1][0]
    corner_y = _MOUTH_Y + 0.02
    tash_half = _BEARD_TASH_HALF
    tash_y = _BEARD_TASH_Y

    def line(pts: list[Point], s: int) -> str:
        return "".join(f"L {cx + s * x * r:.1f} {cy + y * r:.1f} " for x, y in pts)

    # The bottom, from the left top corner round to the right one: the jaw's own
    # line, sunk by the depth of the growth.
    #
    # What was here was an arc swung wide of the jaw and squared off under the
    # chin, a shape with bulk of its own rather than one following the face, and
    # what it read as was hair on a neck. The jaw line is also the version that
    # survives being made short, which is what the owner asked for on 2026-08-09:
    # a shallow arc is a crescent that could be anything, while a jaw line is
    # still a jaw at any depth. The arc is kept in `harness/beard/hang.py` so the
    # two can be put side by side again.
    jaw = _jaw_track(top, b, drop, _BEARD_SIDE_INSET)
    bottom_d = f"{line(jaw, -1)}{line(jaw[-2::-1], 1)}"

    d = (
        # Down the outside: sideburn, then round the bottom and back up.
        f"M {cx - outer[0][0] * r:.1f} {cy + burn_y * r:.1f} "
        f"{line(outer[1:], -1)}"
        f"{bottom_d}"
        # Back up the right side, then across the top of the strip and down its
        # inner edge.
        f"{line(outer[-2::-1], 1)}"
        f"{line(inner, 1)}"
        # The top edge, right to left. Four curves rather than one, because it has
        # to do two opposite things: stay off the cheek at the sides and climb
        # over the lip in the middle. One curve between the two joins can only
        # pick a single height and is wrong at one end whichever it picks, which
        # is how this part produced both a surgical mask and a neckbeard from the
        # same line. In from each join to the corner of the mouth, then up and
        # across the moustache.
        f"Q {cx + x_join * r * 0.99:.1f} {cy + (corner_y + (join_y - corner_y) * 0.34) * r:.1f} "
        f"{cx + tash_half * r:.1f} {cy + corner_y * r:.1f} "
        f"Q {cx + tash_half * r * 0.55:.1f} {cy + tash_y * r:.1f} {cx:.1f} {cy + tash_y * r:.1f} "
        f"Q {cx - tash_half * r * 0.55:.1f} {cy + tash_y * r:.1f} "
        f"{cx - tash_half * r:.1f} {cy + corner_y * r:.1f} "
        f"Q {cx - x_join * r * 0.99:.1f} {cy + (corner_y + (join_y - corner_y) * 0.34) * r:.1f} "
        f"{cx - x_join * r:.1f} {cy + join_y * r:.1f} "
        f"{line(inner[-2::-1], -1)}"
        f"Z"
    )
    mass = f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'
    if _BEARD_LIP_W <= 0:
        return mass
    # Outlined, at well under the usual weight. Unstroked was tried first, on the
    # reasoning that the mouth's own line lands on this a layer later and a second
    # ring round it would read as a second mouth, and that is true at full weight
    # and false at this one: an outline here reads as the edge of a lip. It also
    # has to be *some* outline, since a colour patch with no ink round it is the
    # one soft edge in a drawing where everything else is hard-edged.
    #
    # Both radii ride `mouth_width`, so the lozenge stays the same shape on a
    # character with a small mouth instead of turning into a different lozenge.
    lip = 0.12 * p.face.mouth_width
    return (
        f"{mass}"
        f'<ellipse cx="{cx:.1f}" cy="{cy + _MOUTH_Y * r:.1f}" '
        f'rx="{lip * _BEARD_LIP_W * r:.1f}" ry="{lip * _BEARD_LIP_H * r:.1f}" '
        f'fill="{p.skin_tone}" stroke="{OUTLINE}" stroke-width="{sw * 0.4:.1f}" />'
    )


# How far outside the aperture's own bounding box the rim sits. A rounded rect
# is not an almond, so a rim drawn tight against the eye's exact extremes clips
# the corners; this is the same kind of clearance `_SCARF_CLEAR` gives a cap over
# hair, sized larger because a rim's rounded corner cuts in further than a cloth
# hem does.
_GLASSES_CLEAR = 1.18


def _glasses(sk: Skeleton, p: CharacterParams) -> str:
    """Fine wire spectacles: two rims and a bridge, no lenses.

    No fill, so the eyes read through them. A tinted lens would be a second tone
    over the iris and would take the eye colour with it, and the eye is the one
    thing on a face that has to survive being shrunk.

    Sized off the eye's own aperture rather than a second guess at it. This used
    to carry its own copy of every number `_eye_placement` returns, at different
    values, `eye_dx` 0.34 against the real 0.46 and `eye_y` at `+0.10` against
    the real `+0.16` among them, so the rim sat closer to the nose and lower than
    the eye it was meant to frame and the eye showed outside it on two sides.
    `_eye_placement` is now the only definition of where an eye is, and
    `_eye_shape`'s own half extents are the only definition of how big the
    aperture is, so a rim built from both cannot drift off the eye however
    a character's face is tuned.
    """
    if not p.face.glasses:
        return ""
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    eye_dx, eye_y, eye_r, f = _eye_placement(sk, p)
    sw = _stroke_w(sk)
    # The aperture's own half extents, in the same terms `_eye_shape` builds it
    # from: apex and base sit exactly at `top` and `bot`, and the inner and outer
    # corners exactly at `w`, so this is the aperture's true bounding box rather
    # than an approximation of it.
    half_w = eye_r * f.eye_width * _EYE_ASPECT * _GLASSES_CLEAR
    top_h = eye_r * f.eye_openness * _GLASSES_CLEAR
    bot_h = eye_r * f.eye_lower_lid * _GLASSES_CLEAR
    stroke = f'fill="none" stroke="{OUTLINE}" stroke-width="{sw * 0.55:.1f}"'
    parts = [
        f'<rect x="{cx + s * eye_dx - half_w:.1f}" y="{eye_y - top_h:.1f}" '
        f'width="{half_w * 2:.1f}" height="{top_h + bot_h:.1f}" '
        f'rx="{min(half_w, top_h + bot_h) * 0.3:.1f}" {stroke} />'
        for s in (-1, 1)
    ]
    parts.append(
        f'<path d="M {cx - eye_dx + half_w:.1f} {eye_y:.1f} '
        f'L {cx + eye_dx - half_w:.1f} {eye_y:.1f}" {stroke} />'
    )
    # Arms to the temples, which is what stops the pair reading as two rings
    # floating on the cheeks. Read off the skull at the height the arm actually
    # leaves at, rather than a second guess at eye height: the arm used to query
    # the skull's edge at a fixed 0.10 head radii while the eye it left from sat
    # at 0.16, which is the same drift as everything else here.
    arm_y = eye_y - top_h * 0.35
    arm_y_hr = (arm_y - cy) / r
    for s in (-1, 1):
        parts.append(
            f'<path d="M {cx + s * (eye_dx + half_w):.1f} {eye_y:.1f} '
            f'L {cx + s * _head_edge_x(arm_y_hr, sk.build) * r:.1f} {arm_y:.1f}" {stroke} />'
        )
    return "".join(parts)


# How far above the eye the lenses rest, in eye radii. Pushed up onto the
# forehead rather than worn over the eyes, which is the one thing that tells a
# pair of goggles from a pair of glasses; too small a lift and they read as
# spectacles that missed the eyes rather than as a pair worn up.
_GOGGLE_LIFT = 2.6
# How much closer together the lenses sit than the eyes below them: two lenses
# on a bridge sit close, where two eyes sit apart for the face to read.
_GOGGLE_DX_SCALE = 0.72
_GOGGLE_R_SCALE = 0.98
# How far into the hairstyle's own edge each strap arm reaches, as a fraction
# of that edge: short of it, not past it. The arm has to disappear under the
# hair, and the hair mass only covers what is inside its own silhouette, so an
# arm run out to or beyond the edge `_hair_edge_x` reports lands partly in open
# air with nothing left to draw over it, which is what the first version of
# this did. Inset rather than run exactly to the edge, so the tip sits solidly
# inside the mass rather than riding its outline, where antialiasing or a
# hairstyle a pixel narrower than the one this was tuned against could still
# expose it.
_GOGGLE_ARM_INSET = 0.85


def _goggle_geometry(sk: Skeleton, p: CharacterParams) -> tuple[float, float, float]:
    """`(lens_y, lens_r, lens_dx)`: where the lenses sit and how big they are.

    Shared between `_goggles_strap`, drawn under the hair, and `_goggles`,
    drawn over it, so the two halves of one object agree on where it sits
    without a second copy of the numbers drifting apart, the same reason
    `_eye_placement` exists.
    """
    eye_dx, eye_y, eye_r, _f = _eye_placement(sk, p)
    lens_r = eye_r * _GOGGLE_R_SCALE
    lens_dx = eye_dx * _GOGGLE_DX_SCALE
    lens_y = eye_y - eye_r * _GOGGLE_LIFT
    return lens_y, lens_r, lens_dx


def _goggles_strap(sk: Skeleton, p: CharacterParams) -> str:
    """The strap's two temple arms, drawn before the hair mass.

    A strap that goes around the head runs under the hair at the sides, not
    across the top of it, so unlike the rest of the goggles this half is drawn
    before `_hair_front` rather than after: the hair mass is a filled shape
    that already reads as being in front of the ear and the beard's sideburns
    for the same reason, and an arm drawn here inherits that for free instead
    of needing to fake a cut edge of its own.

    Each arm starts at its own lens (`_goggle_geometry`'s `lens_dx`, so the
    lens drawn later covers the seam) and runs out to a point inset from the
    hairstyle's own edge, read with `_hair_edge_x` rather than `_head_edge_x`:
    a strap sized to the skull stops well short of the hair, and it is
    exactly this gap, between where the strap end sat and where the hair
    actually is, that read as the strap stopping in mid-air rather than
    continuing around the head.
    """
    if p.outfit.goggle_color is None:
        return ""
    cx, cy, r = sk.head_cx, sk.head_cy, sk.head_r
    color = p.outfit.goggle_color
    sw = _stroke_w(sk)
    lens_y, lens_r, lens_dx = _goggle_geometry(sk, p)
    strap_h = lens_r * 0.5
    strap_y_hr = (lens_y - cy) / r
    x_far = _hair_edge_x(strap_y_hr, sk, p) * r * _GOGGLE_ARM_INSET
    parts = []
    for side in (-1, 1):
        x0 = cx + side * lens_dx
        x1 = cx + side * x_far
        parts.append(
            f'<path d="M {x0:.1f} {lens_y - strap_h / 2:.1f} '
            f"L {x1:.1f} {lens_y - strap_h / 2:.1f} "
            f"L {x1:.1f} {lens_y + strap_h / 2:.1f} "
            f'L {x0:.1f} {lens_y + strap_h / 2:.1f} Z" '
            f'fill="{color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'
        )
    return "".join(parts)


def _goggles(sk: Skeleton, p: CharacterParams) -> str:
    """A pair of lenses on a bridge, pushed up onto the forehead.

    Reads off `_eye_placement` the same way `_glasses` does, lifted above the
    brow rather than framing the eye: this is what keeps the pair centred over
    the face at every build, an eye that moves and a pair of goggles that does
    not agree with it is the same drift `_glasses` was pulled off a second copy
    of the eye to fix.

    This is the half of the goggles drawn over the hair: the lenses themselves
    and the bridge joining them, which cross the bare forehead and have
    nothing to disappear into. `_goggles_strap` draws the other half, the
    strap's two temple arms, before the hair mass instead of after it. Glass
    is a lighter, paler tone of the frame color rather than a second color of
    its own: `shade()` already derives a shadow tone from a base one, and a
    lens is the same derivation run the other way, so a goggle color always
    ships with a glass that reads against it instead of needing one
    hand-picked to match.
    """
    if p.outfit.goggle_color is None:
        return ""
    cx = sk.head_cx
    color = p.outfit.goggle_color
    glass = shade(color, value_factor=1.8, saturation_boost=0.55)
    sw = _stroke_w(sk)
    lens_y, lens_r, lens_dx = _goggle_geometry(sk, p)
    parts = [
        # The bridge joining the lenses, under them so their own rims cover
        # its ends rather than leaving a bar visible between two circles.
        f'<path d="M {cx - lens_dx:.1f} {lens_y:.1f} L {cx + lens_dx:.1f} {lens_y:.1f}" '
        f'fill="none" stroke="{color}" stroke-width="{lens_r * 0.5:.1f}" stroke-linecap="round" />',
    ]
    for side in (-1, 1):
        lx = cx + side * lens_dx
        parts.append(
            f'<circle cx="{lx:.1f}" cy="{lens_y:.1f}" r="{lens_r:.1f}" '
            f'fill="{color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'
        )
        parts.append(
            f'<circle cx="{lx:.1f}" cy="{lens_y:.1f}" r="{lens_r * 0.72:.1f}" fill="{glass}" />'
        )
        parts.append(
            f'<circle cx="{lx - lens_r * 0.24:.1f}" cy="{lens_y - lens_r * 0.24:.1f}" '
            f'r="{lens_r * 0.16:.1f}" fill="white" opacity="0.75" />'
        )
    return "".join(parts)


def _collar(sk: Skeleton, p: CharacterParams) -> str:
    """A standing collar closing at the throat, over the tunic's open V.

    The tunic's neckline is a V that shows the undersleeve's tone at its edge,
    which is right for a working tunic and wrong for a uniform, where the
    garment closes at the neck. Rather than give the tunic a second neckline
    shape, this covers the V with a band: the silhouette underneath is
    unchanged, and a collar is a separate piece of cloth on the reference too.

    Two shapes, not one. The band around the neck reads as a collar only once
    something says which way it faces, so the front carries a shallow notch
    where the two halves meet, which is the same trick the V was doing.
    """
    if p.outfit.collar_color is None:
        return None or ""
    cx, sy = sk.head_cx, sk.shoulder_y
    color = p.outfit.collar_color
    sw = _stroke_w(sk)
    # Off the neck, not off the shoulder: a collar wraps a throat, and reading
    # the shoulder here would widen it into a yoke as the frame gets broader.
    half = sk.neck_half_w * 1.70
    h = sk.neck_half_w * 1.75
    # Sits high, most of it above the shoulder line. A collar drawn down onto
    # the chest reads as a bib; what says "closed at the throat" is cloth
    # standing up the neck, and at tile size the part below the shoulder is
    # indistinguishable from the tunic it is the same colour as anyway.
    top = sy - h * 0.80
    d = (
        f"M {cx - half:.1f} {top:.1f} L {cx + half:.1f} {top:.1f} "
        f"L {cx + half * 0.86:.1f} {top + h:.1f} L {cx - half * 0.86:.1f} {top + h:.1f} Z"
    )
    notch = h * 0.55
    return (
        f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'
        f'<path d="M {cx:.1f} {top:.1f} L {cx:.1f} {top + notch:.1f}" fill="none" '
        f'stroke="{OUTLINE}" stroke-width="{sw * 0.7:.1f}" />'
    )


def _placket(sk: Skeleton, p: CharacterParams) -> str:
    """A line of buttons down the centre front, collar to belt.

    The one piece of uniform trim that is pure line work, and the one that does
    most of the work: a plain coloured torso reads as a jersey, and a seam down
    the middle of it reads as a coat that fastens. The buttons are dots on that
    seam rather than drawn discs, because at tile size a disc with an outline is
    a smudge and a dot is a button.
    """
    if p.outfit.placket_color is None:
        return ""
    cx = sk.head_cx
    color = p.outfit.placket_color
    sw = _stroke_w(sk)
    top = sk.shoulder_y + sk.neck_half_w * 0.9
    belt_y, _belt_h = _belt_band(sk)
    bottom = belt_y
    # Slightly off centre, the way a real placket is: the flap that carries the
    # buttons laps over the other side rather than meeting it edge to edge. A
    # dead-centre line reads as a fold in the cloth instead.
    x = cx + sk.waist_half_w * 0.13
    parts = [
        f'<path d="M {x:.1f} {top:.1f} L {x:.1f} {bottom:.1f}" fill="none" '
        f'stroke="{color}" stroke-width="{sw * 0.7:.1f}" stroke-linecap="round" />'
    ]
    # Four, which is what fits between a collar and a belt without the row
    # reading as a zip. They ride the line rather than sitting beside it.
    n = 4
    for i in range(n):
        by = top + (bottom - top) * (i + 0.5) / n
        parts.append(f'<circle cx="{x:.1f}" cy="{by:.1f}" r="{sw * 0.62:.1f}" fill="{color}" />')
    return "".join(parts)


def _chest_pockets(sk: Skeleton, p: CharacterParams) -> str:
    """A flapped pocket on each breast.

    Drawn as a flap alone rather than a pocket with a flap over it. The pocket's
    own outline is a rectangle behind the flap and is invisible at every size
    this is looked at, so all it would add is two more lines to thicken the
    shape; what says "military tunic" is the horizontal flap with a stitch under
    it.
    """
    if p.outfit.chest_pocket_color is None:
        return ""
    cx = sk.head_cx
    color = p.outfit.chest_pocket_color
    sw = _stroke_w(sk)
    # Between the armpit and the waist, and inside the torso's own width at that
    # height, so a pocket cannot ride out over the side contour on a broad frame.
    top = _sleeve_hem_y(sk) + (sk.waist_y - _sleeve_hem_y(sk)) * 0.28
    w = sk.waist_half_w * 0.38
    h = sk.waist_half_w * 0.30
    off = sk.waist_half_w * 0.50
    parts = []
    for s in (-1, 1):
        px = cx + s * off
        parts.append(
            # The flap takes the second tone, which is the pouch-flap and
            # boot-cuff case the flat-colour rule leaves open: a turn of cloth
            # reading as thickness on a small element, not a plane across a
            # panel. Without it the flap is the tunic's own colour and all that
            # survives being shrunk is a faint rectangle of outline.
            f'<rect x="{px - w / 2:.1f}" y="{top:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{h * 0.22:.1f}" fill="{shade(color)}" stroke="{OUTLINE}" '
            f'stroke-width="{sw * 0.7:.1f}" />'
        )
    return "".join(parts)


def _strap(sk: Skeleton, p: CharacterParams) -> str:
    """A strap over the right shoulder and across to the opposite hip.

    Every uniformed character in the references wears one the same way round, so
    the direction is fixed rather than a field: it is part of the uniform, not
    something a character chooses. Tenno is the one who goes without, and he does
    that by leaving the colour unset.

    Drawn over the tunic and under the arms. Over the arms it would cross a hand
    at the wrist, and under the tunic it would not exist.
    """
    if p.outfit.strap_color is None:
        return ""
    cx = sk.head_cx
    color = p.outfit.strap_color
    sw = _stroke_w(sk)
    top_x = cx + sk.shoulder_half_w * 0.52
    top_y = sk.shoulder_y + (sk.waist_y - sk.shoulder_y) * 0.10
    belt_y, _h = _belt_band(sk)
    bot_x = cx - sk.waist_half_w * 0.72
    w = sk.neck_half_w * 0.42
    # A band with two parallel edges rather than a thick line, so it takes an
    # outline like every other garment and does not read as a drawn stroke.
    dx, dy = bot_x - top_x, belt_y - top_y
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * w, dx / length * w
    d = (
        f"M {top_x + nx:.1f} {top_y + ny:.1f} L {bot_x + nx:.1f} {belt_y + ny:.1f} "
        f"L {bot_x - nx:.1f} {belt_y - ny:.1f} L {top_x - nx:.1f} {top_y - ny:.1f} Z"
    )
    return f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw * 0.8:.1f}" />'


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

    The pull-back is floored at half rather than running all the way down to
    `sk.build`, which is 0.1 at the chibi build: at that strength two lengths as
    far apart as 0.60 and 0.95 land within four pixels of each other, task
    #103's report, and it is why Reika's near-floor-length reference hakama
    used to read mid-thigh at the published build. `harness/hem/pullback.py`
    swept five strengths against four references at both ends of the range in
    use, Satoko's skirt through Reika's hakama; half was the owner's pick on
    2026-08-10, enough to fix Reika without changing Satoko's already-settled
    look past what the reference asks for. A short hem stays available to
    anyone who wants one: this is how much of a *requested* length lands, not a
    floor under how short `length` itself may be.
    """
    if length is None:
        return sk.hem_y
    asked = sk.hip_y + length * (sk.ankle_y - sk.hip_y)
    return sk.hem_y + (asked - sk.hem_y) * max(sk.build, 0.5)


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


def _hakama(sk: Skeleton, p: CharacterParams) -> str:
    """A wide pleated garment over the legs, from the waist to near the floor.

    The same A-line panel `_skirt` and `_underskirt` already draw, not a second
    silhouette invented for this: `_skirt_path`'s flare comes off the
    skeleton's own hip and hem anchors, and a hakama sharing it is what keeps a
    lower-body garment skeleton-relative instead of a shape with its own
    private idea of how wide the hips are.

    What actually makes it read as a hakama and not a plain skirt is the
    pleats. `_skirt` draws two folds as a suggestion of drape; a hakama is
    defined by them, so this draws a comb across the whole panel the way
    `_underskirt` combs its own hem band, just over the full height instead of
    a strip at the bottom. Flat colour and thin lines rather than a second
    tone, the same call every other lower-body garment here makes: a wedge
    wide enough to see is a plane this figure does not have room for twice.

    Legs or trousers are drawn first and this paints over the top of them,
    which is what lets the two coexist without this needing to know whether
    the legs under it are bare or in trousers, or how long they run: Reika's
    is close to floor-length over bare legs and Haruto's stops well short of
    his boots, over trousers that carry the rest of the way down.
    """
    color = p.outfit.hakama_color
    if color is None:
        return ""
    sw = _stroke_w(sk)
    top_y = sk.waist_y
    hem_y = _skirt_hem_y(sk, p.outfit.hakama_length)
    d = _skirt_path(sk, top_y, hem_y)
    shape = f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw:.1f}" />'
    if not p.shaded:
        return shape
    # Pleats run to the corner where the panel turns under, not through it, so
    # the turn stays one unbroken edge the way `_underskirt`'s does.
    corner = _skirt_corner_y(sk, hem_y)
    if corner - top_y <= sw * 4:
        return shape
    pleat_sw = max(1.0, sw * 0.4)
    parts = [shape]
    for i in range(-3, 4):
        at = i / 3.5
        x0 = sk.head_cx + _skirt_half_w(sk, top_y) * at
        x1 = sk.head_cx + _skirt_half_w(sk, corner) * at
        parts.append(
            f'<line x1="{x0:.1f}" y1="{top_y:.1f}" x2="{x1:.1f}" y2="{corner:.1f}" '
            f'stroke="{shade(color)}" stroke-width="{pleat_sw:.1f}" opacity="0.75" />'
        )
    return "".join(parts)


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
    # However the legs are covered, the boots go in the same two places, so the
    # gap floor is shared rather than duplicated per branch. The reference leaves
    # each inner edge about 0.09 head radii off centre, which is where the
    # presets land without the floor biting.
    gap = max(gap, w_top + sk.leg_half_w * 0.2)
    if trousers:
        parts = [_trousers(sk, p, trousers, gap, w_top, w_knee, w_calf, w_ankle)]
    else:
        # One seat, not two tubes with a gap between them: see `_bare_seat`. What
        # used to be here drew each leg as its own closed path starting a few
        # pixels above the skirt's hem, which left the hip and the top of the
        # inner thigh as untouched canvas the instant nothing covered them, a
        # skirt shorter than default, both garments off entirely, and read as
        # the figure's legs not being attached to its body.
        parts = [_bare_seat(sk, p, gap, w_top, w_knee, w_calf, w_ankle)]
    for side in (-1, 1):
        parts.append(_boot(sk, p, sk.head_cx + side * gap, w_ankle, side))
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


def _leg_tuck_top_y(sk: Skeleton, p: CharacterParams) -> float:
    """Where a garment covering both legs as one seat starts: inside the belt
    band when the tunic is tucked, the hip otherwise. Shared by `_trousers` and
    `_bare_seat` so a tucked tunic with no trousers still has something under
    it rather than a gap the width of the belt.
    """
    belt_y, belt_h = _belt_band(sk)
    return belt_y + belt_h * 0.5 if p.outfit.tunic_tucked else sk.hip_y


def _seat_notch_d(
    sk: Skeleton,
    cx: float,
    gap: float,
    top_y: float,
    crotch_y: float,
    w_top: float,
    w_knee: float,
    w_calf: float,
    w_ankle: float,
) -> str:
    """A seat with a notch cut out of it, not two tubes: one closed silhouette
    from the waist to both ankles, meeting at `crotch_y` and parting below it.

    The canon draws no gap between the legs above the crotch and no seam across
    the top of the thigh either. Measured on both Satoshi sheets, the silhouette
    below the belt is a single run until roughly a quarter of the way to the
    floor, where background first appears between the legs, and from there the
    slot opens smoothly to about a third of the garment's width by the boot.

    Shared by `_trousers` and `_bare_seat`, which differ only in fill, outline
    weight and whether a seam gets drawn on top: the crotch itself is the one
    thing that must never draw two different ways depending on what the legs
    are wearing.
    """
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
    return (
        f"M {cx - w_waist:.1f} {top_y:.1f} L {cx + w_waist:.1f} {top_y:.1f} "
        + outer_down(1)
        + inner_up(1)
        + inner_down(-1)
        + outer_up(-1)
        + "Z"
    )


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

    What was here before was a wedge drawn behind two separately stroked tubes,
    and the wedge's lower V hung below the tunic's hem between two legs that had
    a slot of canvas running all the way up between them: it read as a flap
    hanging off the belt rather than as the seat of a garment. `_seat_notch_d`
    is the fix, shared with the bare-skin case in `_bare_seat` below.

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
    top_y = _leg_tuck_top_y(sk, p)
    crotch_y = sk.hip_y + (sk.knee_y - sk.hip_y) * _CROTCH_AT
    d = _seat_notch_d(sk, cx, gap, top_y, crotch_y, w_top, w_knee, w_calf, w_ankle)
    # Rounded joins, because the inseam meets itself at a point at the crotch and
    # SVG's default miter shoots a spike off any sharp corner. `_hair_mass` hit
    # the same thing at a lock's tip.
    return (
        f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" '
        f'stroke-linejoin="round" />' + _trouser_seams(sk, p, color, gap, w_top, top_y, crotch_y)
    )


# A fixed placeholder, not a character trait: nobody's design in
# docs/mist-characters/character_designs.md specifies underwear, so there is
# nothing for a per-character field to hold, the way there is for a tunic or a
# skirt. A plain neutral cotton tone, the way OUTLINE is a plain neutral line
# regardless of what it outlines.
_UNDERWEAR_COLOR = "#e8e4dc"


def _underpants(sk: Skeleton, gap: float, top_y: float, crotch_y: float, w_top: float) -> str:
    """A modesty layer over the top of `_bare_seat`, not full-length: it never
    reaches the point the legs part, so it needs no notch of its own and is
    just a plain block with a shallow curved hem, the way a brief is cut higher
    than trousers rather than a shorter copy of them.
    """
    cx = sk.head_cx
    hem_y = crotch_y + (sk.knee_y - crotch_y) * 0.22
    w_waist = gap + w_top
    # A little narrower at the hem than the waist, which is what a hem gathered
    # by elastic looks like rather than a straight-sided box.
    w_hem = w_waist * 0.82
    dip = (hem_y - top_y) * 0.10
    d = (
        f"M {cx - w_waist:.1f} {top_y:.1f} L {cx + w_waist:.1f} {top_y:.1f} "
        f"L {cx + w_hem:.1f} {hem_y - dip:.1f} "
        f"Q {cx:.1f} {hem_y:.1f} {cx - w_hem:.1f} {hem_y - dip:.1f} Z"
    )
    return (
        f'<path d="{d}" fill="{_UNDERWEAR_COLOR}" stroke="{OUTLINE}" '
        f'stroke-width="{_stroke_w(sk) * 0.85:.1f}" stroke-linejoin="round" />'
    )


def _bare_seat(
    sk: Skeleton,
    p: CharacterParams,
    gap: float,
    w_top: float,
    w_knee: float,
    w_calf: float,
    w_ankle: float,
) -> str:
    """Bare legs, as one silhouette rather than two separate tubes with a gap
    between them, the same fix `_trousers` got and for the same reason: two
    independent shapes leave a slot of background between them, which used to
    run all the way up to the hip the moment nothing else covered it, skirt and
    trousers both off, or a skirt shorter than default. A placeholder pair of
    underpants rides on top, so the figure reads as dressed rather than as a
    body with a hole cut in the middle of it.
    """
    cx = sk.head_cx
    top_y = _leg_tuck_top_y(sk, p)
    crotch_y = sk.hip_y + (sk.knee_y - sk.hip_y) * _CROTCH_AT
    d = _seat_notch_d(sk, cx, gap, top_y, crotch_y, w_top, w_knee, w_calf, w_ankle)
    # No tone down the leg, same as the old two-tube version: a stripe down a
    # leg reads the way one down a sleeve does, one flat surface with an outline
    # doing the work instead.
    return (
        f'<path d="{d}" fill="{p.skin_tone}" stroke="{OUTLINE}" '
        f'stroke-width="{_stroke_w(sk) * 0.85:.1f}" stroke-linejoin="round" />'
        + _underpants(sk, gap, top_y, crotch_y, w_top)
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


def _boot(sk: Skeleton, p: CharacterParams, cx: float, w_ankle: float, side: int) -> str:
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
    #
    # `boot_shaft` extends that toward the knee without changing anything else
    # about the boot: the five uniformed characters and Kyoko all wear a tall
    # boot with the trouser tucked into it, which is a different garment from the
    # ankle boot the rest of the cast wears and reads as one at any size. It
    # stops a little short of the knee itself, because a shaft that reaches the
    # joint reads as a legging rather than as a boot pulled on.
    shaft_reach = 0.32 + (0.92 - 0.32) * max(0.0, min(1.0, p.outfit.boot_shaft))
    top_y = sk.ankle_y - (sk.ankle_y - sk.knee_y) * shaft_reach
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


def _belt_band(sk: Skeleton, scale: float = 1.0) -> tuple[float, float]:
    """Where the belt sits and how deep it is, as (top y, height).

    Shared rather than computed where it is needed, because three parts depend
    on it now: the belt draws it, a tucked tunic ends inside it, and trousers
    start inside it. Two of those only work while all three agree, and the
    failure is a band of bare canvas at the waist.

    `scale` is how an obi is drawn: the same band three or four times as deep,
    growing about its own centre so the waist does not move. Only `_belt` passes
    it. The tucked tunic and the trousers deliberately keep asking for the plain
    band, because their join has to land where a belt of any depth covers it, and
    the unscaled midpoint is inside every scaled band by construction.
    """
    h = (sk.hip_y - sk.waist_y) * 0.42 * max(0.2, scale)
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
    y, h = _belt_band(sk, p.outfit.belt_scale)
    parts = [
        f'<rect x="{cx - half_w:.1f}" y="{y:.1f}" width="{half_w * 2:.1f}" height="{h:.1f}" '
        f'rx="{h * 0.18:.1f}" fill="{color}" stroke="{OUTLINE}" stroke-width="{_stroke_w(sk):.1f}" />'
    ]
    if p.shaded:
        parts.append(
            f'<rect x="{cx - half_w:.1f}" y="{y + h * 0.62:.1f}" width="{half_w * 2:.1f}" height="{h * 0.38:.1f}" '
            f'rx="{h * 0.18:.1f}" fill="{shade(color)}" opacity="0.8" />'
        )
    # A buckle, but not on a sash. An obi is the same band three times as deep
    # and it is *tied*, not fastened, so a metal buckle on one is the single
    # detail that would say "belt" loudest on the three characters the depth is
    # there to dress. The cut-off sits between a wide belt and a narrow sash.
    obi = p.outfit.belt_scale > 1.6
    # With an apron, whether the buckle shows rides on the build: `ref/satoko-
    # chibi.jpg`'s apron sits high enough to cover it, but `ref/satoko-real.jpg`
    # does not, the buckle sitting clear above the panel with the strap's tail
    # running down over it. So the old rule ("an apron hides it, full stop",
    # true at chibi) undershot the realistic build, where the reference shows
    # both the buckle and the hanging tie together. `sk.build > 0.5` is the
    # same cut a bare-headed chibi nose uses for the same reason: a detail that
    # only reads once the figure has grown into the room for it.
    show_buckle = (p.outfit.apron_color is None or sk.build > 0.5) and not obi
    # Whenever the buckle is not carrying the belt on its own: an obi (never
    # gets a buckle) or an apron at any build below where the buckle joins it,
    # same as before this build split existed. With both an apron and the
    # buckle showing, the tie stays too, since that is the realistic build's
    # own reference.
    show_tie = not show_buckle or p.outfit.apron_color is not None
    tie_top = y + h * 0.55
    if show_buckle:
        # Metal is a fixed neutral tone, like the blush: it is not anyone's
        # palette.
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
        # The tail continues from the buckle's own bottom edge when both show,
        # so the strap reads as one piece running through the buckle rather
        # than two unrelated ornaments stacked on the belt.
        tie_top = by + bh
    if show_tie:
        # The strap's knotted end hanging down the apron's front, the one
        # thing on the assembly that says the panel hangs *from* the belt
        # rather than being a pocket sewn across it. Skips its own knot box
        # when the buckle is also showing, since the buckle already anchors
        # the strap and a second knot directly under it doubles up.
        sw = _stroke_w(sk)
        tie_w = h * 0.30
        knot_h = h * 0.55
        knot_y = tie_top
        if not show_buckle:
            parts.append(
                f'<rect x="{cx - h * 0.42:.1f}" y="{knot_y:.1f}" width="{h * 0.84:.1f}" '
                f'height="{knot_h:.1f}" rx="{knot_h * 0.35:.1f}" fill="{shade(color, 0.86)}" '
                f'stroke="{OUTLINE}" stroke-width="{sw * 0.7:.1f}" />'
            )
        # Two different heights off the same knot, not one: the top edge sits
        # inside where the knot box would be (or right at the buckle's own
        # edge when there is no box), and the drop is measured from a full
        # knot_h down, past where the box would end.
        tail_start = knot_y + knot_h * 0.7 if not show_buckle else knot_y
        tail_base = knot_y + knot_h if not show_buckle else knot_y
        for s, drop in ((-1, 0.62), (1, 0.48)):
            # Two ends of unequal length, because a knot with two equal tails
            # reads as a ribbon.
            x0 = cx + s * h * 0.20
            parts.append(
                f'<path d="M {x0 - tie_w / 2:.1f} {tail_start:.1f} '
                f"L {x0 + tie_w / 2:.1f} {tail_start:.1f} "
                f"L {x0 + s * h * 0.10 + tie_w / 2:.1f} {tail_base + (sk.hip_y - sk.waist_y) * drop:.1f} "
                f"L {x0 + s * h * 0.10 - tie_w / 2:.1f} {tail_base + (sk.hip_y - sk.waist_y) * drop:.1f} "
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


# Where each crystal sits along the belt, as a fraction of `waist_half_w`
# either side of centre, outer to inner. Kept inboard of the pouch's own
# 0.68-0.76 span (`_pouches`) so a character wearing both does not stack a
# gem on a flap: nothing in the cast does yet, but the rig and a pouch are
# both belt-mounted kit and there is no reason a future character couldn't
# wear both.
_CRYSTAL_X_FRACS = (-0.60, -0.28, 0.28, 0.60)


def _crystal_harness(sk: Skeleton, p: CharacterParams) -> str:
    """Up to four mana crystals clipped along the belt band, two a side.

    Flat kite-shaped gems, no glow: a crystal is dangerous to grip
    bare-handed (`valley_of_mist/docs/design.md`, "Donarsblut"), which is
    what the rig is about, not a light source, and a glow at chibi scale
    reads as clutter before it reads as danger anyway. The shape, the flat
    color and the loop clipping it to the belt are what say "crystal", the
    same way a flat rectangle with a flap says "pouch". Drawn after the belt
    and pouches, in front of both, so the rig reads as riding over the band.
    """
    colors = (
        p.outfit.crystal_color_1,
        p.outfit.crystal_color_2,
        p.outfit.crystal_color_3,
        p.outfit.crystal_color_4,
    )
    if p.outfit.belt_color is None or all(c is None for c in colors):
        return ""
    cx = sk.head_cx
    sw = _stroke_w(sk)
    belt_h = (sk.hip_y - sk.waist_y) * 0.42 * max(0.2, p.outfit.belt_scale)
    belt_y = sk.waist_y - belt_h * 0.35
    band_cy = belt_y + belt_h * 0.5
    # A little taller than the pouch's own head-relative size: a gem this
    # small still has to read as faceted rather than as a dot.
    h = sk.head_r * (0.30 + 0.12 * sk.build)
    w = h * 0.58
    parts = []
    for frac, color in zip(_CRYSTAL_X_FRACS, colors, strict=True):
        if color is None:
            continue
        gx = cx + frac * sk.waist_half_w
        top = (gx, band_cy - h / 2)
        right = (gx + w / 2, band_cy - h * 0.08)
        bottom = (gx, band_cy + h / 2)
        left = (gx - w / 2, band_cy - h * 0.08)
        d = (
            f"M {top[0]:.1f} {top[1]:.1f} "
            f"L {right[0]:.1f} {right[1]:.1f} "
            f"L {bottom[0]:.1f} {bottom[1]:.1f} "
            f"L {left[0]:.1f} {left[1]:.1f} Z"
        )
        parts.append(
            f'<path d="{d}" fill="{color}" stroke="{OUTLINE}" stroke-width="{sw * 0.8:.1f}" />'
        )
        # One facet line, top point to bottom point: the cheap cue that reads
        # as a cut stone rather than a bead, without a second fill or a
        # gradient.
        parts.append(
            f'<line x1="{top[0]:.1f}" y1="{top[1]:.1f}" x2="{bottom[0]:.1f}" y2="{bottom[1]:.1f}" '
            f'stroke="{shade(color, 0.6)}" stroke-width="{sw * 0.5:.1f}" />'
        )
        # The loop clipping it to the belt: a short stroke standing in for a
        # leather keeper, the same idea as the buckle's own keeper in `_belt`.
        parts.append(
            f'<line x1="{gx:.1f}" y1="{band_cy - h * 0.60:.1f}" x2="{gx:.1f}" y2="{top[1]:.1f}" '
            f'stroke="{OUTLINE}" stroke-width="{sw * 0.6:.1f}" stroke-linecap="round" />'
        )
        # A leather strap wrapping the gem at its widest point, holding it to
        # the belt rather than leaving it looking merely balanced there.
        # Belt-colored so it reads as the same rig, not a second accessory.
        strap_h = h * 0.24
        strap_w = w * 1.22
        strap_y = band_cy - h * 0.08 - strap_h / 2
        parts.append(
            f'<rect x="{gx - strap_w / 2:.1f}" y="{strap_y:.1f}" width="{strap_w:.1f}" '
            f'height="{strap_h:.1f}" fill="{p.outfit.belt_color}" '
            f'stroke="{OUTLINE}" stroke-width="{sw * 0.6:.1f}" />'
        )
    if p.outfit.crystal_tongs:
        # A small crossed-tongs silhouette hanging below the outer right
        # gem, on the thigh rather than beside it: further out at belt
        # height sits behind the arm, the same room problem the pouches
        # solve by hanging low instead of wide. Standard Crystal Conclave
        # kit for a stock nobody grips bare-handed. Fixed neutral metal
        # tone, like the belt buckle: not anyone's palette.
        tx = cx + _CRYSTAL_X_FRACS[3] * sk.waist_half_w
        ty = band_cy + h * 1.05
        arm = h * 0.75
        parts.append(
            f'<line x1="{tx - arm * 0.22:.1f}" y1="{ty - arm * 0.55:.1f}" '
            f'x2="{tx + arm * 0.28:.1f}" y2="{ty + arm * 0.55:.1f}" '
            f'stroke="#8a8578" stroke-width="{sw * 0.7:.1f}" stroke-linecap="round" />'
        )
        parts.append(
            f'<line x1="{tx + arm * 0.22:.1f}" y1="{ty - arm * 0.55:.1f}" '
            f'x2="{tx - arm * 0.28:.1f}" y2="{ty + arm * 0.55:.1f}" '
            f'stroke="#8a8578" stroke-width="{sw * 0.7:.1f}" stroke-linecap="round" />'
        )
        parts.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="{sw * 0.6:.1f}" fill="#6b665c" />')
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


def _hair_edge_x(y: float, sk: Skeleton, p: CharacterParams) -> float:
    """How far off centre the *silhouette* sits at height `y`, in head radii.

    The hair's own contour where the hair reaches that height, the skull's where
    it does not, so a caller gets the outline a viewer actually sees rather than
    the bone under it. `_head_edge_x` answers the other question and the two are
    a head radius apart at the temples on a long cut.

    Which is the distinction three parts have now got wrong in the same
    direction. A hat, a tie or a knot sized against the skull sits inside the
    hair it is supposed to be on, and what it reads as is a shape painted on the
    hair rather than an object placed over it.

    The widest crossing rather than the first: the contour can cross a height
    more than once, at a lock's edge or a notch, and what a garment has to clear
    is the outermost of them.

    Walks the mass's quadratics rather than taking the style's word for it, for
    the reason `_head_edge_x` walks the skull's: a second formula agrees with the
    drawing until somebody retunes one of them.
    """
    start, segments = HAIRSTYLES[p.hairstyle].mass(_hair_fall(sk, p))
    widest = _head_edge_x(y, sk.build)
    prev = start
    for ctrl, end in segments:
        here = prev
        for i in range(1, 25):
            t = i / 24
            u = 1.0 - t
            nxt = (
                u * u * prev[0] + 2 * u * t * ctrl[0] + t * t * end[0],
                u * u * prev[1] + 2 * u * t * ctrl[1] + t * t * end[1],
            )
            lo, hi = sorted((here[1], nxt[1]))
            if lo <= y <= hi and nxt[1] != here[1]:
                f = (y - here[1]) / (nxt[1] - here[1])
                widest = max(widest, abs(here[0] + (nxt[0] - here[0]) * f))
            here = nxt
        prev = end
    return widest


def _jaw_track(y0: float, build: float, drop: float, inset: float, steps: int = 12) -> list[Point]:
    """The lower skull from height `y0` round to the chin, sunk by `drop`.

    The jaw's own line, moved down rather than replaced by an arc of somebody
    else's shape. The sink ramps in from nothing at `y0`, so the curve leaves the
    top corner where the sideburn left it instead of stepping away from it, and
    the x scale ramps the other way, from the mass's inset at the top to the
    skull's full width at the chin. Both ramps exist for the same reason: a beard
    that starts exactly where the strip ended and ends exactly under the chin has
    no seam anywhere, whatever the build does to the jaw underneath it.

    Right side only, ending on the centre line, which is where `_head_pt` puts the
    chin. The caller mirrors it.
    """
    deg0 = next((d for d in range(90, 181) if _head_pt(float(d), 1.0, build)[1] >= y0), 90)
    pts = []
    for i in range(steps + 1):
        f = i / steps
        x, y = _head_pt(deg0 + (180.0 - deg0) * f, 1.0, build)
        pts.append((x * (inset + (1.0 - inset) * f), y + drop * f))
    # `deg0` is a whole degree, so it lands at or just past `y0`, which leaves the
    # first point up to a fiftieth of a head radius below where the strip ended.
    # That is a kink rather than a gap, since the path runs a straight line into
    # it, but it is a kink that moves with the build, and the point it should be
    # at is known exactly.
    pts[0] = (_head_edge_x(y0, build) * inset, y0)
    return pts


def _face_track(
    y0: float,
    y1: float,
    build: float,
    r0: float,
    r1: float,
    w0: float = 0.0,
    w1: float = 0.0,
    w_ease: float = 1.0,
    steps: int = 10,
) -> list[Point]:
    """Points down the skull's edge from `y0` to `y1`, in head radii.

    Each point sits `r` of the way out to the edge and then `w` further in, both
    interpolated across the span, so a caller can lay a band along the cheek that
    holds its own width while the face under it narrows. The two knobs are not
    the same thing and both are needed: a ratio alone gives a band that thins as
    the jaw draws in, and a width alone gives one that ignores the taper.

    `w_ease` bends the width's interpolation: above 1 it holds the band near `w0`
    for longer and opens it late. That matters when only one end of the span is
    crowded, which is the usual case for a band laid against a head, since the
    top of the face is where the hair and the ear both arrive.

    Sampled off `_head_edge_x` rather than fitted, for the reason that helper
    exists at all: it cannot drift away from the drawn outline. A polyline is
    enough at the size this is looked at, ten segments over a quarter of the
    skull being finer than the eight quadratics that draw the skull itself.
    """
    pts = []
    for i in range(steps + 1):
        f = i / steps
        y = y0 + (y1 - y0) * f
        x = _head_edge_x(y, build) * (r0 + (r1 - r0) * f) - (w0 + (w1 - w0) * f**w_ease)
        pts.append((x, y))
    return pts


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


def _eye(
    ex: float, ey: float, er: float, side: int, f: FaceStyle, eye_color: str, sw: float
) -> str:
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
        f'<circle cx="{ex:.1f}" cy="{iris_cy:.1f}" r="{iris_r:.1f}" fill="{shade(eye_color, 0.45)}" />'
    )
    parts.append(
        f'<circle cx="{ex:.1f}" cy="{iris_cy:.1f}" r="{iris_r * 0.84:.1f}" fill="{eye_color}" />'
    )
    parts.append(
        f'<circle cx="{ex:.1f}" cy="{iris_cy + iris_r * 0.10:.1f}" r="{iris_r * 0.40:.1f}" '
        f'fill="{shade(eye_color, 0.18)}" />'
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


def _eye_placement(sk: Skeleton, p: CharacterParams) -> tuple[float, float, float, FaceStyle]:
    """Where an eye sits and how big it is: `(eye_dx, eye_y, eye_r, face)`.

    One source for both `_face` and `_glasses`, which is what `_glasses` claimed
    to be reading and was not: it carried its own copy of every number here, at
    different values, so the rims sat closer together and lower than the eyes
    they were meant to frame. A second definition agrees with the first on the
    day it is written and stops agreeing the moment either one is retuned, which
    is the same failure `_MOUTH_Y` was pulled out to stop.

    Returns the build-adjusted `FaceStyle` along with the geometry, not just the
    numbers, because a caller sizing the aperture itself, the way `_glasses`
    does, needs the lids at the values they are actually drawn at. The canon
    lids the adult eye, almond where the chibi gets a round-open aperture, so
    the adjustment happens once, here, rather than once per caller.
    """
    r = sk.head_r
    cy = sk.head_cy
    f = p.face
    if sk.build > 0:
        # Measured directly off ref/satoko-real.jpg and ref/satoshi-real.jpg
        # (aperture width/height read by eye off a pixel grid, since the
        # automated `eyes` probe finds the iris highlight dot on this art
        # rather than the aperture, a known failure of that tool on these
        # two references): the realistic aperture runs about 2.2 times wider
        # than tall, against the chibi's roughly 1.4, which is a flatter,
        # more closed eye rather than a uniformly smaller one. The previous
        # 0.20/0.10 reduction undershot that: it closed the aperture by
        # about 15% at full build where closing it by about 30% lands on
        # the measured ratio.
        f = replace(
            f,
            eye_openness=f.eye_openness * (1.0 - 0.40 * sk.build),
            eye_lower_lid=f.eye_lower_lid * (1.0 - 0.20 * sk.build),
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
    return eye_dx, eye_y, eye_r, f


def _face(sk: Skeleton, p: CharacterParams) -> str:
    r = sk.head_r
    cx, cy = sk.head_cx, sk.head_cy
    eye_dx, eye_y, eye_r, f = _eye_placement(sk, p)
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
        parts.append(_eye(ex, eye_y, eye_r, side, f, p.eye_color, sw))

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

    mouth_y = cy + r * _MOUTH_Y
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


def render_character(
    p: CharacterParams | None = None,
    sk: Skeleton | None = None,
    background: str | None = None,
    metadata: bool = False,
) -> str:
    """Draw one character and return the whole SVG document as a string.

    `p` carries what the character *is* (colours, garments, face, haircut) and
    `sk` what its proportions are. Passing no skeleton builds one from `p.heads`
    and `p.frame`, which is the common case; passing one is how the same
    character is rendered at another build, or on a canvas of another size:

        render_character(PRESETS["satoko"])
        render_character(PRESETS["satoko"], build_skeleton(heads=BUILDS["realistic"]))

    `background` is any SVG paint, and defaults to **none at all**, so the
    figure comes out on transparency. That is what a character is for here: it
    gets composited onto a scene, and a white rectangle behind it is not part of
    the drawing, it is something the caller then has to remove. Pass
    `background="white"` to get the old opaque document back, which is what the
    CLI's `--background` does.

    One consequence worth knowing before measuring anything: tools that find the
    figure by looking for near-white background need the alpha flattened onto
    white first, or every transparent pixel reads as black and the whole canvas
    counts as ink. `probe.py` and the `harness/` scripts do that on load.

    Nothing is written to disk and nothing is rasterized here. The document is
    deterministic: the same arguments give the same bytes, which is what lets
    `ref-out/` be compared rather than eyeballed.

    `metadata` embeds an SVG `<metadata>` block naming the tool, the licence
    and a link that reproduces `p`; see `attribution.metadata_block`. Off by
    default, so the fourteen files under `ref-out/` do not churn on every
    unrelated change: the web tool is what turns it on.
    """
    p = p or CharacterParams()
    sk = sk or build_skeleton(heads=p.heads, frame=p.frame)

    # Back to front. The legs go under the skirts so a hem covers the thigh, and
    # the arms go over every garment so nothing can clip a hand: the apron is
    # narrow enough to sit between them, but only just, and the hands are the
    # one place a collision would show.
    layers = [
        _hair_defs(sk, p),
        # Behind the mass, so both emerge from the silhouette instead of sitting
        # on the face. That is the whole point of them being parts rather than
        # hairstyles: a cut owns the outline around the skull, and these two are
        # by definition outside it.
        _hair_tail(sk, p),
        _hair_mass(sk, p),
        _neck(sk, p),
        _legs_and_boots(sk, p),
        _underskirt(sk, p),
        _skirt(sk, p),
        # Over the legs and whatever they wear, under the kimono top: the top of
        # a hakama sits at the waist, so the tunic and the robe front drawn next
        # cover its upper reach the same way they cover the top of a skirt.
        _hakama(sk, p),
        # Behind the tunic: a kimono sleeve hangs off the shoulder seam, so the
        # torso's own outline has to close over the top of it.
        _hanging_sleeves(sk, p),
        _tunic(sk, p),
        # The crossed front, over the tunic it re-fronts and under the obi.
        _robe_front(sk, p),
        # Uniform trim, over the tunic it sits on and under the belt that
        # crosses it. The placket has to stop at the belt and the strap has to
        # pass behind it, which this order gives for nothing.
        _placket(sk, p),
        _chest_pockets(sk, p),
        _strap(sk, p),
        _apron(sk, p),
        # Over the tunic and the trim on it, under the belt and the arms: a coat
        # hangs open in front of the body and behind the arms, and a belt worn
        # with one is worn over it.
        _coat(sk, p),
        _belt(sk, p),
        _pouches(sk, p),
        _crystal_harness(sk, p),
        _arms(sk, p),
        # After the arms and before the ear: a standing collar wraps the throat,
        # so it belongs over the neck and the tunic's V, and it is the one
        # garment high enough that the head has to be drawn after it.
        _collar(sk, p),
        # The ear goes under the head and over the back hair: the canon runs the
        # face's outline unbroken across the ear and hangs the hair behind it.
        _ears(sk, p),
        _head(sk, p),
        # Over the head and under the face. Over the head because a beard covers
        # the jaw it grows on, and the skull's own chin outline would otherwise
        # run straight across it. Under the face because a moustache goes over the
        # lip and the lip is drawn on top of it: with the beard above, raising the
        # coverage to where the owner asked for it on 2026-08-09 simply deleted
        # the mouth. Nothing else in `_face` reaches this far down, so the move
        # costs nothing above.
        #
        # Lifting the hair or the ear back over the beard was tried on 2026-08-09,
        # to stop the three of them colliding at the temple, and neither can be
        # bought at this price. The hair mass is a filled shape wider and taller
        # than the head, so over the beard it is over the face too and the figure
        # loses its face entirely. The ear is not even a judgement: the beard is
        # over the head and the ear is under it, so in one list "ear over the
        # beard, still under the head" does not exist, and what can be drawn
        # instead is the ear over the face, which `_ears` records as the wrong
        # arrangement. The crowding is geometry; `_BEARD_SIDEBURN_W_TOP` is where
        # it lives.
        _beard(sk, p),
        _face(sk, p),
        # Over the face: spectacles sit in front of the eyes, not behind them.
        _glasses(sk, p),
        # Before the hair, unlike the rest of the goggles: a strap that goes
        # around the head runs under the hair at the sides, and drawing its
        # arms here is what lets the hair mass cover their ends the way it
        # already covers the ear and the beard's sideburns.
        _goggles_strap(sk, p),
        _hair_front(sk, p),
        # Last of the hair, unlike the tail, which is first. See `_hair_knot`: a
        # cut leaves under a tenth of a head radius of daylight above itself, so
        # a knot drawn behind the mass is invisible; drawn between the mass and
        # the fringe it is invisible too, because the fringe covers the crown.
        _hair_knot(sk, p),
        _hair_tie(sk, p),
        # After the fringe, like the scarf: the lenses and the bridge cross
        # the bare forehead and sit over whatever hair reaches that far.
        _goggles(sk, p),
        # Last of all the head: a scarf covers the hair it is tied over.
        _headscarf(sk, p),
    ]

    body = "\n  ".join(layer for layer in layers if layer)
    # Emitted only when asked for, rather than always drawn and sometimes
    # painted over: an absent rect is the transparency, there is no other way to
    # say it in SVG.
    bg = f'  <rect width="100%" height="100%" fill="{background}" />\n' if background else ""
    # A local import: `attribution` imports `character_url` from `urlstate`,
    # which imports `CharacterParams` from here, so importing it at module
    # level would be a cycle. Only paid for when `metadata=True` asks for it.
    md = ""
    if metadata:
        from .attribution import metadata_block

        md = f"  {metadata_block(p)}\n"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sk.canvas_w:.0f}" height="{sk.canvas_h:.0f}" '
        f'viewBox="0 0 {sk.canvas_w:.0f} {sk.canvas_h:.0f}">\n'
        f"{md}"
        f"{bg}"
        f"  {body}\n"
        f"</svg>\n"
    )
