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

CHIBI_HEADS = 2.4
DEFAULT_HEADS = 4.0


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

    # 0 at 2 heads, 1 at 6. Widths that read right on a chibi read wrong on a
    # longer figure, so they slide along this instead of being fixed.
    t = min(1.0, max(0.0, (heads - 2.0) / 4.0))

    return Skeleton(
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        heads=heads,
        head_cx=canvas_w / 2,
        head_cy=head_cy,
        head_r=head_r,
        neck_y=head_cy + head_r * 0.85,
        neck_half_w=head_r * _lerp(0.22, 0.32, t),
        shoulder_y=chin_y + body * 0.07,
        shoulder_half_w=head_r * _lerp(0.72, 1.60, t),
        waist_y=chin_y + body * 0.34,
        hip_y=chin_y + body * 0.48,
        hip_half_w=head_r * _lerp(1.00, 1.45, t),
        hem_y=chin_y + body * 0.60,
        hem_half_w=head_r * _lerp(1.15, 1.50, t),
        arm_half_w=head_r * _lerp(0.23, 0.30, t),
        arm_x=head_r * _lerp(0.84, 1.05, t),
        leg_half_w=head_r * _lerp(0.16, 0.34, t),
        knee_y=chin_y + body * 0.72,
        ankle_y=chin_y + body * 0.90,
        foot_y=chin_y + body,
    )
