"""The Nanoleaf integration."""

from __future__ import annotations

import asyncio
from contextlib import suppress

from aionanoleaf2 import EffectsEvent, Nanoleaf, StateEvent
from homeassistant.const import CONF_HOST, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .coordinator import NanoleafConfigEntry, NanoleafCoordinator
from .services import async_setup_services

PLATFORMS = [Platform.BUTTON, Platform.LIGHT]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Nanoleaf services."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: NanoleafConfigEntry) -> bool:
    """Set up Nanoleaf from a config entry."""
    nanoleaf = Nanoleaf(async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_TOKEN])
    coordinator = NanoleafCoordinator(hass, entry, nanoleaf)
    await coordinator.async_config_entry_first_refresh()

    async def on_event(event: StateEvent | EffectsEvent) -> None:
        """Push device state into the coordinator."""
        coordinator.async_set_updated_data(None)

    event_listener = asyncio.create_task(nanoleaf.listen_events(state_callback=on_event, effects_callback=on_event))

    async def _cancel_listener() -> None:
        event_listener.cancel()
        with suppress(asyncio.CancelledError):
            await event_listener

    entry.async_on_unload(_cancel_listener)
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NanoleafConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
