"""Checks for the bundled scenes."""

import re

from custom_components.nanoleaf.scenes import (
    SCENES,
    build_scene,
    expand_gradient,
    install_payload,
)

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
    write = install_payload(name, SCENES[name])["write"]
    assert write["command"] == "add"
    assert write["animName"] == name
    assert write["hexPalette"] == SCENES[name]["hexPalette"]


def test_build_scene_uses_the_flow_motion() -> None:
    """Service-built scenes share the built-in motion engine."""
    scene = build_scene(["FF0000", "00FF00"])
    assert scene["pluginType"] == "color"
    assert scene["pluginOptions"][0] == {"name": "linDirection", "value": "right"}


def test_expand_gradient_fills_short_palettes() -> None:
    """Two colors become a smooth multi-stop gradient."""
    grad = expand_gradient(["000000", "FFFFFF"])
    assert len(grad) == 6
    assert grad[0] == "000000"
    assert grad[-1] == "FFFFFF"
    assert all(HEX_COLOR.match(c) for c in grad)
