"""Assembles a chibi character from flat vector shapes anchored to a
Skeleton. Every shape is plain SVG (paths, circles, capsule-strokes) so
recoloring is just swapping a fill/stroke attribute and the whole figure
scales as one unit via the skeleton's head_r.
"""

from __future__ import annotations

from dataclasses import dataclass

from colorutil import shade
from skeleton import Skeleton, build_skeleton

OUTLINE = "#2b2b2b"
STROKE_W = 3


@dataclass(frozen=True)
class CharacterParams:
    skin_tone: str = "#f2c9a1"
    hair_color: str = "#e8b84b"
    eye_color: str = "#4a9c6d"
    outfit_color: str = "#4f7a52"
    boot_color: str = "#5b4632"
    shaded: bool = True


def _capsule(x1: float, y1: float, x2: float, y2: float, width: float, color: str) -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="{width:.1f}" stroke-linecap="round" />'
    )


def _back_hair(sk: Skeleton, p: CharacterParams) -> str:
    cx, r = sk.head_cx, sk.head_r
    cy = sk.head_cy + r * 1.35
    rx, ry = r * 0.95, r * 1.7
    fill = shade(p.hair_color, 0.88) if p.shaded else p.hair_color
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'


def _neck(sk: Skeleton, p: CharacterParams) -> str:
    w = sk.head_r * 0.45
    x = sk.head_cx - w / 2
    h = sk.shoulder_y - sk.neck_y + 6
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


def _face(sk: Skeleton, p: CharacterParams) -> str:
    r = sk.head_r
    cx, cy = sk.head_cx, sk.head_cy
    eye_y = cy + r * 0.08
    eye_dx = r * 0.42
    eye_r = r * 0.26
    parts = []

    for side in (-1, 1):
        ex = cx + side * eye_dx
        parts.append(
            f'<line x1="{ex - eye_r * 0.9:.1f}" y1="{eye_y - eye_r * 1.7:.1f}" '
            f'x2="{ex + eye_r * 0.9:.1f}" y2="{eye_y - eye_r * 1.85:.1f}" '
            f'stroke="{OUTLINE}" stroke-width="3" stroke-linecap="round" />'
        )
        parts.append(
            f'<circle cx="{ex:.1f}" cy="{eye_y:.1f}" r="{eye_r:.1f}" fill="white" stroke="{OUTLINE}" stroke-width="2.5" />'
        )
        iris_r = eye_r * 0.72
        parts.append(f'<circle cx="{ex:.1f}" cy="{eye_y + eye_r * 0.05:.1f}" r="{iris_r:.1f}" fill="{p.eye_color}" />')
        pupil_r = eye_r * 0.34
        parts.append(f'<circle cx="{ex:.1f}" cy="{eye_y + eye_r * 0.12:.1f}" r="{pupil_r:.1f}" fill="{shade(p.eye_color, 0.35)}" />')
        parts.append(f'<circle cx="{ex - eye_r * 0.28:.1f}" cy="{eye_y - eye_r * 0.32:.1f}" r="{eye_r * 0.22:.1f}" fill="white" />')
        parts.append(f'<circle cx="{ex + eye_r * 0.22:.1f}" cy="{eye_y + eye_r * 0.28:.1f}" r="{eye_r * 0.1:.1f}" fill="white" opacity="0.85" />')

    mouth_y = cy + r * 0.55
    parts.append(
        f'<path d="M {cx - r * 0.12:.1f} {mouth_y:.1f} Q {cx:.1f} {mouth_y + r * 0.08:.1f} {cx + r * 0.12:.1f} {mouth_y:.1f}" '
        f'fill="none" stroke="{OUTLINE}" stroke-width="2.5" stroke-linecap="round" />'
    )

    for side in (-1, 1):
        bx = cx + side * r * 0.55
        by = cy + r * 0.35
        parts.append(f'<ellipse cx="{bx:.1f}" cy="{by:.1f}" rx="{r * 0.16:.1f}" ry="{r * 0.09:.1f}" fill="#e8879a" opacity="0.45" />')

    return "".join(parts)


def _front_hair(sk: Skeleton, p: CharacterParams) -> str:
    cx, r = sk.head_cx, sk.head_r
    cy = sk.head_cy
    outer = [
        (cx - r * 0.98, cy - r * 0.2),
        (cx - r * 0.55, cy - r * 1.05),
        (cx, cy - r * 0.6),
        (cx + r * 0.55, cy - r * 1.05),
        (cx + r * 0.98, cy - r * 0.2),
    ]
    inner = [
        (cx + r * 0.8, cy - r * 0.02),
        (cx + r * 0.35, cy - r * 0.15),
        (cx, cy - r * 0.32),
        (cx - r * 0.35, cy - r * 0.15),
        (cx - r * 0.8, cy - r * 0.02),
    ]
    d = f"M {outer[0][0]:.1f} {outer[0][1]:.1f} "
    d += f"Q {outer[1][0]:.1f} {outer[1][1]:.1f} {outer[2][0]:.1f} {outer[2][1]:.1f} "
    d += f"Q {outer[3][0]:.1f} {outer[3][1]:.1f} {outer[4][0]:.1f} {outer[4][1]:.1f} "
    d += f"L {inner[0][0]:.1f} {inner[0][1]:.1f} "
    d += f"Q {inner[1][0]:.1f} {inner[1][1]:.1f} {inner[2][0]:.1f} {inner[2][1]:.1f} "
    d += f"Q {inner[3][0]:.1f} {inner[3][1]:.1f} {inner[4][0]:.1f} {inner[4][1]:.1f} "
    d += "Z"
    bangs = f'<path d="{d}" fill="{p.hair_color}" stroke="{OUTLINE}" stroke-width="{STROKE_W}" />'

    lock_w = r * 0.34
    lock_y2 = sk.shoulder_y + r * 0.5
    locks = _capsule(cx - r * 0.85, cy - r * 0.1, cx - r * 1.0, lock_y2, lock_w, p.hair_color)
    locks += _capsule(cx + r * 0.85, cy - r * 0.1, cx + r * 1.0, lock_y2, lock_w, p.hair_color)

    return locks + bangs


def render_character(p: CharacterParams | None = None, sk: Skeleton | None = None) -> str:
    p = p or CharacterParams()
    sk = sk or build_skeleton()

    layers = [
        _back_hair(sk, p),
        _dress(sk, p),
        _legs_and_boots(sk, p),
        _arms(sk, p),
        _neck(sk, p),
        _head(sk, p),
        _face(sk, p),
        _front_hair(sk, p),
    ]

    body = "\n  ".join(layers)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sk.canvas_w:.0f}" height="{sk.canvas_h:.0f}" '
        f'viewBox="0 0 {sk.canvas_w:.0f} {sk.canvas_h:.0f}">\n'
        f'  <rect width="100%" height="100%" fill="white" />\n'
        f"  {body}\n"
        f"</svg>\n"
    )
