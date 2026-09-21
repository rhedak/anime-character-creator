"""Proportion anchors the character is built around.

Everything downstream (hair, clothes, limbs) positions itself relative to
these points instead of using hardcoded coordinates, so changing the
proportions here doesn't require touching every shape.

The whole figure derives from one number, `heads`: how many head-heights
tall it stands. Vertical anchors are fractions of the body (chin to floor),
so they keep their relationship at any height, while widths interpolate
between builds, since a 2-head chibi is narrow-shouldered and wide-hipped
in a way an adult figure is not.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

# Named builds. Most characters want one of these rather than a number, but
# `heads` stays open for anything in between (4.0 is a common middle ground).
# Above 6 the figure just gets longer; the widths are already at their limit.
BUILDS: dict[str, float] = {
    "chibi": 2.4,
    # 6 rather than a life-drawing 8, and rather than the 7 this started at.
    # Anime figures run shorter than real ones, and at 7 the head was small
    # enough against the body that the result stopped reading as the style.
    "realistic": 6.0,
}
DEFAULT_BUILD = "chibi"
DEFAULT_HEADS = BUILDS[DEFAULT_BUILD]


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


@dataclass(frozen=True)
class Skeleton:
    canvas_w: float
    canvas_h: float
    heads: float
    # How far along the chibi-to-adult range this build sits: 0 at a 2-head
    # chibi, 1 at the 6-head adult `realistic` names. Every lerp below rides on
    # it, and parts that need to deform with the build read it rather than
    # recomputing it.
    build: float
    head_cx: float
    head_cy: float
    head_r: float
    neck_y: float
    neck_half_w: float
    shoulder_y: float
    shoulder_half_w: float
    waist_y: float
    waist_half_w: float
    # Where a bust sits on the torso and how far it carries. The height is a
    # proportion of the build like every other anchor: what a character differs
    # on is the size, not where a bust is on a body. At `bust=0` the half-width
    # is exactly what the shoulder-to-waist run already gives at that height, so
    # the anchor draws nothing and changes nothing until it is asked for
    # (`docs/bust-plan.md`).
    bust_y: float
    bust_half_w: float
    hip_y: float
    hip_half_w: float
    hem_y: float
    hem_half_w: float
    arm_half_w: float
    # Where the arms hang. A chibi's arms are thick enough that they have to
    # sit outside the shoulder to read as limbs; a longer figure's tuck in.
    arm_x: float
    leg_half_w: float
    knee_y: float
    ankle_y: float
    foot_y: float


@dataclass(frozen=True)
class BodyProfile:
    """One character's measured proportions, laid over a built skeleton.

    Every build is a lerp between the chibi and adult anchors, which is right
    for a cast designed at those two ends and wrong for a character whose own
    design sits somewhere else: Katherina's reference stands 3.47 heads tall
    with a high belt, a short coat and tall boots, and the lerp at 3.47 heads
    puts her waist most of a head radius too low. A profile names the figure's
    height and whichever landmarks were measured, each in head radii from the
    head centre (y down, widths as half-widths), and leaves every other field
    where `build_skeleton` put it. `None` is "not measured, keep the lerp".

    `build` stays at the named build's own value rather than the one `heads`
    implies: it drives the face and the limb tapers, which are a style choice
    (a big-eyed chibi face), not a proportion, and moving it would redraw the
    face along with the body.
    """

    heads: float
    shoulder_y: float | None = None
    waist_y: float | None = None
    hip_y: float | None = None
    hem_y: float | None = None
    knee_y: float | None = None
    ankle_y: float | None = None
    shoulder_half_w: float | None = None
    waist_half_w: float | None = None
    hip_half_w: float | None = None
    hem_half_w: float | None = None
    arm_half_w: float | None = None
    arm_x: float | None = None
    leg_half_w: float | None = None

    def head_scaled(self, s: float) -> BodyProfile:
        """The same body under a head `s` times as big.

        Every landmark is in head radii, so a bigger head against the same body
        means each distance measured in the new, larger radius is smaller. With the
        chin held where it is: a height `y` from the head centre becomes
        `(y - 1 + s) / s` (the head centre moves up by the growth), a width `w`
        becomes `w / s`, and the figure stands `(heads - 1 + s) / s` heads tall.
        `heads` alone would only rescale the whole figure and leave the proportion
        where it was. `s = 1` is the identity.
        """

        def y(v: float | None) -> float | None:
            return None if v is None else (v - 1.0 + s) / s

        def w(v: float | None) -> float | None:
            return None if v is None else v / s

        return BodyProfile(
            heads=(self.heads - 1.0 + s) / s,
            shoulder_y=y(self.shoulder_y),
            waist_y=y(self.waist_y),
            hip_y=y(self.hip_y),
            hem_y=y(self.hem_y),
            knee_y=y(self.knee_y),
            ankle_y=y(self.ankle_y),
            shoulder_half_w=w(self.shoulder_half_w),
            waist_half_w=w(self.waist_half_w),
            hip_half_w=w(self.hip_half_w),
            hem_half_w=w(self.hem_half_w),
            arm_half_w=w(self.arm_half_w),
            arm_x=w(self.arm_x),
            leg_half_w=w(self.leg_half_w),
        )

    def applied(self, sk: Skeleton, build: float) -> Skeleton:
        ys = ("shoulder_y", "waist_y", "hip_y", "hem_y", "knee_y", "ankle_y")
        ws = (
            "shoulder_half_w",
            "waist_half_w",
            "hip_half_w",
            "hem_half_w",
            "arm_half_w",
            "arm_x",
            "leg_half_w",
        )
        changes: dict[str, float] = {"build": build}
        for name in ys:
            v = getattr(self, name)
            if v is not None:
                changes[name] = sk.head_cy + v * sk.head_r
        for name in ws:
            v = getattr(self, name)
            if v is not None:
                changes[name] = v * sk.head_r
        return replace(sk, **changes)


def default_hair_margin(heads: float) -> float:
    """Headroom above the skull a figure at `heads` gets by default, in head
    radii, so the hair has somewhere to go.

    It is head-relative rather than a fraction of the canvas because that is
    what it measures. As a canvas fraction it was generous at a tall build and,
    at a chibi, less than the crown of any hairstyle here needs: the head is a
    third of the figure, so the same 3.5% of canvas came to under a fifth of a
    head radius and every chibi came out with the top of its hair sliced flat
    against the canvas edge.

    This is the allowance a hairstyle's crown has to stay inside: no hair
    ink, including the outer half of the stroke, may reach above
    -(1 + hair_margin) head radii from the head centre. With 0.36 here the
    ceiling is -1.36 and the tallest crown in character.py paints to about
    -1.30. A new cut that goes higher needs this raised with it, because
    nothing computes the bound from the shapes: the short cut's cowlick
    flicks (tried and reverted) bled at exactly this boundary and needed
    0.44 for the day they existed.

    It rides the build rather than being one number, because the canon does not
    give a chibi and an adult the same volume of hair. Measured off both Satoshi
    references, the chibi's hair stands 0.73 head radii clear of its skull
    against the adult's 0.29, so a chibi's crown needs roughly twice the
    headroom for the same haircut (`docs/gap-analysis.md`, gap 1). Holding one
    margin at both ends means either the chibi is capped or the adult is given
    headroom it never uses, and headroom is not free: it comes straight out of
    the figure's height on the canvas, 7% at the chibi end between these two
    values.
    """
    t0 = min(1.0, max(0.0, (heads - 2.0) / 4.0))
    return _lerp(0.75, 0.36, t0)


# Where the bust sits between the shoulder and the waist, and how far `bust=1`
# carries it out, in head radii. The height is anatomy and does not vary; the
# reach rides the build, because the shared chibi is a small child's proportion
# and an adult figure carries more. Both are first guesses for `harness/bust/`
# to refine by eye, which is the only way this gets decided: no reference in
# this project measures a bust (`docs/bust-plan.md`, B0).
_BUST_ALONG = 0.45
_BUST_REACH = (0.10, 0.20)


def build_skeleton(
    canvas_w: float = 400,
    canvas_h: float = 500,
    heads: float = DEFAULT_HEADS,
    frame: float = 0.0,
    bust: float = 0.0,
    hair_margin: float | None = None,
    bottom_margin: float = 0.03,
    min_hair_margin: float = 0.0,
) -> Skeleton:
    # Passing `hair_margin` explicitly overrides `default_hair_margin` entirely;
    # see its docstring for what the number means.
    if hair_margin is None:
        hair_margin = default_hair_margin(heads)
    # A floor rather than an override, for something worn above the hair: a
    # witch's hat stands far taller than any crown, and the figure is what gives
    # way for it, standing smaller on the same canvas. `character.hat_hair_margin`
    # says how much a character's hat needs; passing it where a character's
    # skeleton is built is what keeps its tip on the page.
    hair_margin = max(hair_margin, min_hair_margin)
    fig_h = canvas_h * (1.0 - bottom_margin) / (1.0 + hair_margin / (2.0 * heads))
    head_h = fig_h / heads
    head_r = head_h / 2
    head_cy = head_r * (1.0 + hair_margin)
    chin_y = head_cy + head_r
    body = fig_h - head_h

    # 0 at a 2-head chibi, 1 at 6 heads and up. Both the widths and where the
    # landmarks sit along the body slide along this: a chibi is nearly
    # neckless with its hips high in a short body, an adult is not.
    #
    # The top of the range is where `realistic` sits, not some taller figure
    # beyond it, so that the named build actually reaches the adult widths these
    # lerps were tuned for. Anything above 6 heads clamps to the same anchors and
    # only gets longer.
    t = min(1.0, max(0.0, (heads - 2.0) / 4.0))

    # Frame is the shoulder-against-hip ratio: -1 narrow-shouldered and wide in
    # the hip, 0 the neutral figure every build gave before it existed, +1 the
    # other way. It rides on t because a frame needs a body to show on. At 2.4
    # heads the head swamps the torso and the whole difference comes to well under
    # a percent of the width, so a chibi comes out the same whatever it is handed.
    f = max(-1.0, min(1.0, frame)) * t

    shoulder_y = chin_y + body * _lerp(0.02, 0.028, t)
    shoulder_half_w = head_r * _lerp(0.68, 1.55, t) * (1.0 + 0.09 * f)
    waist_y = chin_y + body * _lerp(0.46, 0.333, t)
    waist_half_w = head_r * _lerp(0.88, 1.00, t) * (1.0 + 0.03 * f)
    bust_y = shoulder_y + (waist_y - shoulder_y) * _BUST_ALONG
    # The width the torso already has at that height, plus whatever the
    # character asks for. The first term is what makes `bust=0` a no-op, and it
    # has to stay exactly the shoulder-to-waist interpolation `_body_knots`
    # hands the garment placement, or the anchor alone moves every traced cut.
    bust_half_w = shoulder_half_w + (waist_half_w - shoulder_half_w) * _BUST_ALONG
    bust_half_w += head_r * _lerp(*_BUST_REACH, t) * max(0.0, bust)

    return Skeleton(
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        heads=heads,
        build=t,
        head_cx=canvas_w / 2,
        head_cy=head_cy,
        head_r=head_r,
        neck_y=head_cy + head_r * 0.85,
        neck_half_w=head_r * _lerp(0.21, 0.40, t),
        shoulder_y=shoulder_y,
        shoulder_half_w=shoulder_half_w,
        waist_y=waist_y,
        # A chibi barely has a waist: it stays wider than its own shoulders and
        # only a little narrower than its hips, which is what keeps it reading as
        # a small child rather than a shrunken adult. An adult takes in sharply.
        waist_half_w=waist_half_w,
        bust_y=bust_y,
        bust_half_w=bust_half_w,
        hip_y=chin_y + body * _lerp(0.58, 0.417, t),
        hip_half_w=head_r * _lerp(0.95, 1.30, t) * (1.0 - 0.11 * f),
        hem_y=chin_y + body * _lerp(0.70, 0.58, t),
        # The canon's chibi flare is gentler than 1.11 read: measured on the
        # silhouette at 0.80 and 0.85 of figure height, where the skirt hem and
        # the underskirt band are what the outline is made of, ours ran 13% to
        # 18% wide of it. The underskirt narrows in the same change; between them
        # they are the whole of that row.
        hem_half_w=head_r * _lerp(1.02, 1.60, t),
        # Legs run wider than arms at every build, the way limbs do. This
        # started the other way around at chibi (arms 0.22, legs 0.15), which
        # read as wrong the moment it was pointed at: measured off the canon
        # chibis, sleeves come to about 0.155 head radii and legs about 0.23,
        # an arm-to-leg ratio of roughly 0.7, the same as the adult's.
        arm_half_w=head_r * _lerp(0.14, 0.33, t),
        # Rides the frame with the shoulder it hangs off. Broadening the shoulder
        # without moving the arm out leaves the garment's shoulder sticking out
        # past the sleeve, and two characters on different frames then disagree
        # about where the arm meets the body.
        #
        # The chibi end sits at 0.85 rather than the 0.75 it started at: the
        # canon hangs a chibi's arms clear of the tunic's sides, and at 0.75
        # the thick chibi arm covered a third of the garment.
        arm_x=head_r * _lerp(0.85, 1.20, t) * (1.0 + 0.09 * f),
        leg_half_w=head_r * _lerp(0.22, 0.42, t),
        knee_y=chin_y + body * _lerp(0.81, 0.708, t),
        ankle_y=chin_y + body * _lerp(0.93, 0.95, t),
        foot_y=chin_y + body,
    )
