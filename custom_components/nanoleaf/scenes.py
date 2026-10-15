"""Bundled scenes and scene building, saved onto the strip itself.

Each scene is a Nanoleaf color-flow animation: the same motion engine the
built-in scenes use, with our own palette. Installing one writes it to the
device's own effect list, so it keeps working from any controller even
without this integration.
"""

from __future__ import annotations

from typing import Any, TypedDict

from aionanoleaf2 import Nanoleaf


class Scene(TypedDict):
    """Shape of a Nanoleaf plugin animation."""

    animType: str
    pluginType: str
    pluginUuid: str
    hexPalette: list[str]
    pluginOptions: list[dict[str, Any]]


# Motion UUID behind the built-in color-flow scenes (e.g. Northern Lights).
FLOW_MOTION_UUID = "6970681a-20b5-4c5e-8813-bdaebc4ee4fa"


def build_scene(
    palette: list[str],
    trans_time: int = 30,
    direction: str = "right",
) -> Scene:
    """Build a looping color-flow scene over a hex palette."""
    return {
        "animType": "plugin",
        "pluginType": "color",
        "pluginUuid": FLOW_MOTION_UUID,
        "hexPalette": palette,
        "pluginOptions": [
            {"name": "linDirection", "value": direction},
            {"name": "loop", "value": True},
            {"name": "nColorsPerFrame", "value": 3},
            {"name": "transTime", "value": trans_time},
        ],
    }


def expand_gradient(palette: list[str], steps: int = 6) -> list[str]:
    """Grow a short palette into a smooth multi-stop gradient."""
    if len(palette) >= steps:
        return palette
    stops = [tuple(int(c[i : i + 2], 16) for i in (0, 2, 4)) for c in palette]
    out: list[str] = []
    span = steps - 1
    for i in range(steps):
        pos = i * (len(stops) - 1) / span
        left = int(pos)
        right = min(left + 1, len(stops) - 1)
        frac = pos - left
        rgb = tuple(round(a + (b - a) * frac) for a, b in zip(stops[left], stops[right], strict=True))
        out.append("".join(f"{c:02X}" for c in rgb))
    return out


SCENES: dict[str, Scene] = {
    "Moonlight": build_scene(["0D1B2A", "1B263B", "415A77", "778DA9", "C5D5E0", "FFFFFF"], trans_time=40),
    "Ember": build_scene(["1A0A00", "4A1500", "8C2F00", "D96010", "F2A13C", "FFD9A0"], trans_time=30),
    "Deep Sea": build_scene(["001219", "003049", "005F73", "0A9396", "94D2BD", "E9F5F2"], trans_time=50),
}


def install_payload(name: str, scene: Scene) -> dict[str, Any]:
    """OpenAPI request body that saves a scene on the device."""
    return {"write": {"command": "add", "animName": name, **scene}}


async def install_scene(nanoleaf: Nanoleaf, name: str, scene: Scene) -> None:
    """Save a scene on the strip and refresh the cached effect list."""
    # ponytail: aionanoleaf2 has no public "add effect" call, so we use its
    # generic request hook. Ceiling: breaks if upstream renames _request.
    # Upgrade path: switch to a public write method when one lands upstream.
    await nanoleaf._request("put", "effects", install_payload(name, scene))
    await nanoleaf.get_info()
