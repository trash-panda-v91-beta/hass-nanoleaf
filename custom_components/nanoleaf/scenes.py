"""Bundled scenes, saved onto the strip itself.

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


def _flow(palette: list[str], trans_time: int) -> Scene:
    """Build a looping color-flow scene over a hex palette."""

    def option(name: str, value: Any) -> dict[str, Any]:
        return {"name": name, "value": value}

    return {
        "animType": "plugin",
        "pluginType": "color",
        "pluginUuid": FLOW_MOTION_UUID,
        "hexPalette": palette,
        "pluginOptions": [
            option("linDirection", "right"),
            option("loop", True),
            option("nColorsPerFrame", 3),
            option("transTime", trans_time),
        ],
    }


SCENES: dict[str, Scene] = {
    "Moonlight": _flow(["0D1B2A", "1B263B", "415A77", "778DA9", "C5D5E0", "FFFFFF"], trans_time=40),
    "Ember": _flow(["1A0A00", "4A1500", "8C2F00", "D96010", "F2A13C", "FFD9A0"], trans_time=30),
    "Deep Sea": _flow(["001219", "003049", "005F73", "0A9396", "94D2BD", "E9F5F2"], trans_time=50),
}


def install_payload(name: str) -> dict[str, Any]:
    """OpenAPI request body that saves a scene on the device."""
    return {"write": {"command": "add", "animName": name, **SCENES[name]}}


async def install_scene(nanoleaf: Nanoleaf, name: str) -> None:
    """Save a scene on the strip and refresh the cached effect list."""
    # ponytail: aionanoleaf2 has no public "add effect" call, so we use its
    # generic request hook. Ceiling: breaks if upstream renames _request.
    # Upgrade path: switch to a public write method when one lands upstream.
    await nanoleaf._request("put", "effects", install_payload(name))
    await nanoleaf.get_info()
