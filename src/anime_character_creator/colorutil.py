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
