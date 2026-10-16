"""Color helpers for the flat cel-shading look: every shape gets a base
color and a single darker "shadow" tone, derived rather than hand-picked,
so palettes stay internally consistent across characters."""

from __future__ import annotations

import colorsys


def hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return r, g, b


def rgb01_to_hex(rgb: tuple[float, float, float]) -> str:
    r, g, b = (max(0, min(255, round(c * 255))) for c in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def shade(hex_color: str, value_factor: float = 0.80, saturation_boost: float = 1.08) -> str:
    """Darker, slightly more saturated variant for shadow shapes."""
    r, g, b = hex_to_rgb01(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = min(1.0, s * saturation_boost)
    v = max(0.0, v * value_factor)
    return rgb01_to_hex(colorsys.hsv_to_rgb(h, s, v))


def tint(hex_color: str, amount: float = 0.5) -> str:
    """Lighter variant, `amount` of the way to white. For the soft finish's
    highlights and glows, which `shade()` has no counterpart for."""
    r, g, b = hex_to_rgb01(hex_color)
    return rgb01_to_hex((r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount))


def lit_tone(hex_color: str, rise: float) -> str:
    """Lighter by `rise` of value, keeping the saturation, hue nudged a little warm when the colour
    has one. Where value would pass white the saturation gives way instead, by part of the
    overshoot. `tint` washes a colour toward white and halves its saturation, which on dark red
    reads as frosting; this stays the same colour, only brighter."""
    h, s, v = colorsys.rgb_to_hsv(*hex_to_rgb01(hex_color))
    v2 = v + rise
    if v2 > 1.0:
        s = max(0.0, s - (v2 - 1.0) * 0.6)
        v2 = 1.0
    if (
        s >= 0.35
    ):  # a warm nudge means nothing on near-grey or near-black hair and turns it lavender
        h = (h + 4.0 / 360.0) % 1.0
    return rgb01_to_hex(colorsys.hsv_to_rgb(h, s, v2))


def highlight_rise(hex_color: str) -> float:
    """How far a strong highlight rises in value: more on dark colours, little on light ones."""
    v = colorsys.rgb_to_hsv(*hex_to_rgb01(hex_color))[2]
    return min(0.28, max(0.06, 0.30 * (1.0 - v) + 0.08))


def soft_shadow_tone(hex_color: str) -> str:
    """A step darker than the colour, gentler than `shade` so a shadow clump is a tone and not a
    stripe, quieter still on pale or grey colours, and with yellow pulled a little toward orange
    so its shadow is warm and not olive."""
    _, s0, v0 = colorsys.rgb_to_hsv(*hex_to_rgb01(hex_color))
    factor = 0.92 if s0 < 0.35 else 0.87 - 0.05 * v0
    h, s, v = colorsys.rgb_to_hsv(*hex_to_rgb01(shade(hex_color, factor, saturation_boost=1.3)))
    if 30.0 / 360.0 < h < 70.0 / 360.0:
        h -= 7.0 / 360.0
    return rgb01_to_hex(colorsys.hsv_to_rgb(h, s, v))
