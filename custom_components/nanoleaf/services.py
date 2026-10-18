"""Services for the Nanoleaf integration."""

from __future__ import annotations

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from probatio import Optional, Required, Schema

from .const import DOMAIN
from .coordinator import NanoleafConfigEntry
from .scenes import (
    Motion,
    build_scene,
    delete_scene,
    expand_gradient,
    install_scene,
)

EXTRA_OPTIONS = {
    "block_size": "blockSize",
    "delay_time": "delayTime",
    "main_color_prob": "mainColorProb",
    "background": "enableBackgroundColor",
}

ADD_SCENE_SCHEMA = Schema(
    {
        Required(ATTR_ENTITY_ID): str,
        Required("name"): str,
        Required("colors"): [str],
        Optional("trans_time"): int,
        Optional("direction"): str,
        Optional("motion"): str,
        Optional("n_colors_per_frame"): int,
        Optional("block_size"): int,
        Optional("delay_time"): int,
        Optional("main_color_prob"): int,
        Optional("background"): bool,
    }
)

REMOVE_SCENE_SCHEMA = Schema(
    {
        Required(ATTR_ENTITY_ID): str,
        Required("name"): str,
    }
)


def _entry_for_entity(hass: HomeAssistant, entity_id: str) -> NanoleafConfigEntry:
    """Resolve the Nanoleaf config entry behind a light entity."""
    entry = er.async_get(hass).async_get(entity_id)
    config_entry = (
        hass.config_entries.async_get_entry(entry.config_entry_id) if entry and entry.config_entry_id else None
    )
    if config_entry is None or config_entry.domain != DOMAIN:
        raise ServiceValidationError(f"{entity_id} is not a Nanoleaf light")
    return config_entry


def async_setup_services(hass: HomeAssistant) -> None:
    """Register the Nanoleaf services."""

    async def handle_add_scene(call: ServiceCall) -> None:
        """Install a scene on the targeted strip."""
        config_entry = _entry_for_entity(hass, call.data[ATTR_ENTITY_ID])
        name = call.data["name"]
        nanoleaf = config_entry.runtime_data.nanoleaf
        if name in nanoleaf.effects_list:
            raise ServiceValidationError(f"A scene named '{name}' already exists on {config_entry.title}")

        try:
            motion = Motion[call.data.get("motion", "flow").upper()]
        except KeyError:
            valid = ", ".join(m.name.lower() for m in Motion)
            raise ServiceValidationError(f"Unknown motion '{call.data.get('motion')}'. Valid: {valid}") from None

        extra = {EXTRA_OPTIONS[key]: call.data[key] for key in EXTRA_OPTIONS if key in call.data}

        palette = call.data["colors"]
        if len(palette) == 2:
            palette = expand_gradient(palette)

        await install_scene(
            nanoleaf,
            name,
            build_scene(
                palette,
                call.data.get("trans_time", 30),
                call.data.get("direction", "right"),
                motion=motion,
                n_colors=call.data.get("n_colors_per_frame", 3),
                extra_options=extra or None,
            ),
        )
        config_entry.runtime_data.async_set_updated_data(None)

    async def handle_remove_scene(call: ServiceCall) -> None:
        """Remove a scene from the targeted strip."""
        config_entry = _entry_for_entity(hass, call.data[ATTR_ENTITY_ID])
        name = call.data["name"]
        nanoleaf = config_entry.runtime_data.nanoleaf
        if name not in nanoleaf.effects_list:
            raise ServiceValidationError(f"No scene named '{name}' on {config_entry.title}")
        await delete_scene(nanoleaf, name)
        config_entry.runtime_data.async_set_updated_data(None)

    hass.services.async_register(DOMAIN, "add_scene", handle_add_scene, schema=ADD_SCENE_SCHEMA)
    hass.services.async_register(DOMAIN, "remove_scene", handle_remove_scene, schema=REMOVE_SCENE_SCHEMA)
