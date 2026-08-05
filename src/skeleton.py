"""Proportion anchors the character is built around.

Everything downstream (hair, clothes, limbs) positions itself relative to
these points instead of using hardcoded coordinates, so changing the
proportions here doesn't require touching every shape.

The whole figure derives from one number, `heads`: how many head-heights
tall it stands. Vertical anchors are fractions of the body (chin to floor),
so they keep their relationship at any height, while widths interpolate
between builds, since a 2-head chibi is narrow-shouldered and wide-hipped
in a way a 6-head figure is not.
"""

from __future__ import annotations

from dataclasses import dataclass

# Named builds. Most characters want one of these rather than a number, but
# `heads` stays open for anything in between (4.0 is a common middle ground).
BUILDS: dict[str, float] = {
    "chibi": 2.4,
    "realistic": 7.0,
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
    head_cx: float
    head_cy: float
    head_r: float
    neck_y: float
    neck_half_w: float
    shoulder_y: float
    shoulder_half_w: float
    waist_y: float
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
    top_margin: float = 0.035,
    bottom_margin: float = 0.03,
) -> Skeleton:
    fig_h = canvas_h * (1.0 - top_margin - bottom_margin)
    head_h = fig_h / heads
    head_r = head_h / 2
    head_cy = canvas_h * top_margin + head_r
    chin_y = head_cy + head_r
    body = fig_h - head_h

    # 0 at a 2-head chibi, 1 at a 7-head adult. Both the widths and where the
    # landmarks sit along the body slide along this: a chibi is nearly
    # neckless with its hips high in a short body, an adult is not.
    t = min(1.0, max(0.0, (heads - 2.0) / 5.0))

    return Skeleton(
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        heads=heads,
        head_cx=canvas_w / 2,
        head_cy=head_cy,
        head_r=head_r,
        neck_y=head_cy + head_r * 0.85,
        neck_half_w=head_r * _lerp(0.21, 0.40, t),
        shoulder_y=chin_y + body * _lerp(0.02, 0.042, t),
        shoulder_half_w=head_r * _lerp(0.68, 1.55, t),
        waist_y=chin_y + body * _lerp(0.46, 0.333, t),
        hip_y=chin_y + body * _lerp(0.58, 0.417, t),
        hip_half_w=head_r * _lerp(0.95, 1.30, t),
        hem_y=chin_y + body * _lerp(0.70, 0.58, t),
        hem_half_w=head_r * _lerp(1.11, 1.60, t),
        arm_half_w=head_r * _lerp(0.22, 0.33, t),
        arm_x=head_r * _lerp(0.75, 1.20, t),
        leg_half_w=head_r * _lerp(0.15, 0.42, t),
        knee_y=chin_y + body * _lerp(0.81, 0.708, t),
        ankle_y=chin_y + body * _lerp(0.93, 0.95, t),
        foot_y=chin_y + body,
    )
