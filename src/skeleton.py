"""Proportion anchors the character is built around.

Everything downstream (hair, clothes, limbs) positions itself relative
to these points instead of using hardcoded coordinates, so changing the
proportions here (e.g. moving away from chibi later) doesn't require
touching every shape.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Skeleton:
    canvas_w: float
    canvas_h: float
    head_cx: float
    head_cy: float
    head_r: float
    neck_y: float
    shoulder_y: float
    shoulder_half_w: float
    waist_y: float
    hem_y: float
    hem_half_w: float
    knee_y: float
    ankle_y: float
    foot_y: float


def build_skeleton(canvas_w: float = 400, canvas_h: float = 500) -> Skeleton:
    """Chibi proportions: oversized head, short body (~2.3 head-heights
    tall total). All other measurements derive from head_r so the whole
    figure scales as one unit."""
    head_r = canvas_h * 0.18
    head_cy = canvas_h * 0.28
    return Skeleton(
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        head_cx=canvas_w / 2,
        head_cy=head_cy,
        head_r=head_r,
        neck_y=head_cy + head_r * 0.85,
        shoulder_y=head_cy + head_r * 1.05,
        shoulder_half_w=head_r * 0.75,
        waist_y=head_cy + head_r * 2.3,
        hem_y=head_cy + head_r * 3.0,
        hem_half_w=head_r * 1.15,
        knee_y=head_cy + head_r * 3.3,
        ankle_y=head_cy + head_r * 3.65,
        foot_y=head_cy + head_r * 3.85,
    )
