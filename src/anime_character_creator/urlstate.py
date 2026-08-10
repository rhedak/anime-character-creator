"""A character, as a URL.

`docs/web-gui-plan.md` takes this as a default worth having without being
asked: "Encode the parameters into the address bar, so a made character is a
link someone can send or bookmark." It also turns out to be what the
metadata parameter on `render_character` needs, since "the parameter URL
that reproduces the character" has to come from somewhere, so this lives
next to `character.py` rather than under `web/`, and the JavaScript side of
the web tool is a port of the same two functions rather than a second design.

Full fidelity, not the catalogue's limited middle tier: a preset carries
fields the web tool never exposes as a control (`scar_side`, `frame`, a
disguise's `hair_tip_color=None`), and a shared link has to reproduce
*that* character, not just the part of it a visitor could have built by
hand. So this round-trips the whole of `CharacterParams`, encoding it as
compact JSON, which stays legible in a browser's network tab and in a git
diff, then URL-safe base64, which is what keeps it out of the characters a
query string has to percent-encode.
"""

from __future__ import annotations

import base64
import json
from dataclasses import asdict

from .character import CharacterParams, FaceStyle, Outfit

# The query parameter a link carries the character under, short because it
# sits in a URL a person reads: `?c=...`.
QUERY_PARAM = "c"


def params_to_dict(p: CharacterParams) -> dict:
    """`p` as a plain, JSON-able dict: `dataclasses.asdict`, named so the web
    bridge's Python side has one obvious function to call rather than an
    import of `dataclasses` of its own."""
    return asdict(p)


def params_from_dict(data: dict) -> CharacterParams:
    """The inverse of `params_to_dict`, and the validating half both
    `decode_params` and the web bridge's live-edit path share: a `dict` in,
    however it arrived, either becomes a real `CharacterParams` or raises
    `ValueError`, never a character quietly missing the fields that failed.
    """
    data = dict(data)
    try:
        outfit = Outfit(**data.pop("outfit", {}))
        face = FaceStyle(**data.pop("face", {}))
        return CharacterParams(**data, outfit=outfit, face=face)
    except TypeError as e:
        raise ValueError(f"not a valid character: {e}") from e


def encode_params(p: CharacterParams) -> str:
    """`p`, as the value half of a `?c=...` query parameter.

    Deterministic: `sort_keys=True` and no whitespace, so the same character
    always encodes to the same string, which is what lets two links be
    compared for equality without decoding either.
    """
    data = json.dumps(params_to_dict(p), separators=(",", ":"), sort_keys=True)
    return base64.urlsafe_b64encode(data.encode("utf-8")).decode("ascii").rstrip("=")


def decode_params(encoded: str) -> CharacterParams:
    """The inverse of `encode_params`.

    Raises `ValueError` on anything that is not one of this project's own
    links: malformed base64, JSON that is not an object, or a key that is
    not a real field on `CharacterParams`, `Outfit` or `FaceStyle`. A link
    typed in by hand or mangled by a chat client should fail loudly here
    rather than build a character out of whatever survived.
    """
    padded = encoded + "=" * (-len(encoded) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except Exception as e:
        raise ValueError(f"not a valid character link: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("not a valid character link: not an object")
    return params_from_dict(data)


def character_url(p: CharacterParams, base_url: str) -> str:
    """The full link for `p`, off `base_url`, which is the deployed page's own
    address and not something this module invents."""
    return f"{base_url}?{QUERY_PARAM}={encode_params(p)}"
