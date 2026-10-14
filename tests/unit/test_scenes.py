"""Checks for the bundled scenes."""

import re

from custom_components.nanoleaf.scenes import SCENES, install_payload

HEX_COLOR = re.compile(r"^[0-9A-Fa-f]{6}$")


def test_scenes_are_well_formed() -> None:
    """Every scene must be a valid color-flow animation."""
    for name, scene in SCENES.items():
        assert scene["animType"] == "plugin", name
        assert scene["pluginType"] == "color", name
        assert scene["pluginUuid"], name
        assert scene["hexPalette"], name
        assert all(HEX_COLOR.match(color) for color in scene["hexPalette"]), name


def test_scene_names_are_unique_and_stable() -> None:
    """Scene names land on the device as effect names: keep them stable."""
    assert list(SCENES) == ["Moonlight", "Ember", "Deep Sea"]


def test_install_payload_wraps_the_add_command() -> None:
    """The payload must be a valid OpenAPI effects add command."""
    name = next(iter(SCENES))
    write = install_payload(name)["write"]
    assert write["command"] == "add"
    assert write["animName"] == name
    assert write["hexPalette"] == SCENES[name]["hexPalette"]
