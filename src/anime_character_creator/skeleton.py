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

from dataclasses import dataclass

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


def build_skeleton(
    canvas_w: float = 400,
    canvas_h: float = 500,
    heads: float = DEFAULT_HEADS,
    frame: float = 0.0,
    hair_margin: float = 0.36,
    bottom_margin: float = 0.03,
) -> Skeleton:
    # Headroom above the skull, in head radii, so the hair has somewhere to go.
    # It is head-relative rather than a fraction of the canvas because that is
    # what it measures. As a canvas fraction it was generous at a tall build and,
    # at a chibi, less than the crown of any hairstyle here needs: the head is a
    # third of the figure, so the same 3.5% of canvas came to under a fifth of a
    # head radius and every chibi came out with the top of its hair sliced flat
    # against the canvas edge.
    #
    # This is the allowance a hairstyle's crown has to stay inside: no hair
    # ink, including the outer half of the stroke, may reach above
    # -(1 + hair_margin) head radii from the head centre. With 0.36 here the
    # ceiling is -1.36 and the tallest crown in character.py paints to about
    # -1.30. A new cut that goes higher needs this raised with it, because
    # nothing computes the bound from the shapes: the short cut's cowlick
    # flicks (tried and reverted) bled at exactly this boundary and needed
    # 0.44 for the day they existed.
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
        shoulder_y=chin_y + body * _lerp(0.02, 0.028, t),
        shoulder_half_w=head_r * _lerp(0.68, 1.55, t) * (1.0 + 0.09 * f),
        waist_y=chin_y + body * _lerp(0.46, 0.333, t),
        # A chibi barely has a waist: it stays wider than its own shoulders and
        # only a little narrower than its hips, which is what keeps it reading as
        # a small child rather than a shrunken adult. An adult takes in sharply.
        waist_half_w=head_r * _lerp(0.88, 1.00, t) * (1.0 + 0.03 * f),
        hip_y=chin_y + body * _lerp(0.58, 0.417, t),
        hip_half_w=head_r * _lerp(0.95, 1.30, t) * (1.0 - 0.11 * f),
        hem_y=chin_y + body * _lerp(0.70, 0.58, t),
        hem_half_w=head_r * _lerp(1.11, 1.60, t),
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
