"""Bundled scenes and scene building, saved onto the strip itself.

Each scene is a Nanoleaf color-flow animation: the same motion engine the
built-in scenes use, with our own palette. Installing one writes it to the
device's own effect list, so it keeps working from any controller even
without this integration.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, TypedDict

from aionanoleaf2 import Nanoleaf


class Scene(TypedDict):
    """Shape of a Nanoleaf plugin animation."""

    animType: str
    pluginType: str
    pluginUuid: str
    hexPalette: list[str]
    pluginOptions: list[dict[str, Any]]


class Motion(StrEnum):
    """Movement styles available on the strips (one per built-in scene family)."""

    FLOW = "6970681a-20b5-4c5e-8813-bdaebc4ee4fa"  # Northern Lights drift
    WAVE = "e2eb1818-07ac-495f-a10d-7c192d7df705"  # Ocean Waves
    GLOW = "0794a6b3-f6cc-452d-a900-30081604b7ec"  # Cozy Glow
    SCATTER = "db8ce916-88de-484f-bdbb-afd732053105"  # Radioactive
    PULSE = "e8b69f65-df13-480b-a949-db1bbc9a1cde"  # Pump Up
    UFO = "29929fc2-6905-41c0-a7d7-1582a8c11f17"  # UFO sweep
    TWINKLE = "ba632d3e-9c2b-4413-a965-510c839b3f71"  # Starry Night
    FLASH = "70b7c636-6bf8-491f-89c1-f4103508d642"  # Flash Light


MOTION_NAMES = [m.name.lower() for m in Motion]


def build_scene(
    palette: list[str],
    trans_time: int = 30,
    direction: str = "right",
    motion: Motion = Motion.FLOW,
    n_colors: int = 3,
    extra_options: dict[str, Any] | None = None,
) -> Scene:
    """Build a looping color-flow scene over a hex palette."""
    scene: Scene = {
        "animType": "plugin",
        "pluginType": "color",
        "pluginUuid": str(motion),
        "hexPalette": palette,
        "pluginOptions": [
            {"name": "linDirection", "value": direction},
            {"name": "loop", "value": True},
            {"name": "nColorsPerFrame", "value": n_colors},
            {"name": "transTime", "value": trans_time},
        ],
    }
    if extra_options:
        scene["pluginOptions"] += [{"name": k, "value": v} for k, v in extra_options.items()]
    return scene


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


def delete_payload(name: str) -> dict[str, Any]:
    """OpenAPI request body that removes a scene from the device."""
    return {"write": {"command": "delete", "animName": name}}


async def install_scene(nanoleaf: Nanoleaf, name: str, scene: Scene) -> None:
    """Save a scene on the strip and refresh the cached effect list."""
    # ponytail: aionanoleaf2 has no public "add effect" call, so we use its
    # generic request hook. Ceiling: breaks if upstream renames _request.
    # Upgrade path: switch to a public write method when one lands upstream.
    await nanoleaf._request("put", "effects", install_payload(name, scene))
    await nanoleaf.get_info()


async def delete_scene(nanoleaf: Nanoleaf, name: str) -> None:
    """Remove a scene from the strip and refresh the cached effect list."""
    await nanoleaf._request("put", "effects", delete_payload(name))
    await nanoleaf.get_info()
