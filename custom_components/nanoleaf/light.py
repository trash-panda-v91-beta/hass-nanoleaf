"""Support for Nanoleaf lights."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import EMERSION_MODELS, EMERSION_MODES, STRIP_MODEL_PREFIXES
from .coordinator import NanoleafConfigEntry, NanoleafCoordinator
from .entity import NanoleafEntity
from .scenes import SCENES, install_scene

RESERVED_EFFECTS = ("*Solid*", "*Static*", "*Dynamic*")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NanoleafConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Nanoleaf light."""
    async_add_entities([NanoleafLight(entry.runtime_data)])


class NanoleafLight(NanoleafEntity, LightEntity):
    """Representation of a Nanoleaf light."""

    _attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.HS}
    _attr_supported_features = LightEntityFeature.EFFECT | LightEntityFeature.TRANSITION
    _attr_name = None
    _attr_translation_key = "light"

    def __init__(self, coordinator: NanoleafCoordinator) -> None:
        """Initialize the Nanoleaf light."""
        super().__init__(coordinator)
        self._attr_unique_id = self._nanoleaf.serial_no
        self._attr_max_color_temp_kelvin = self._nanoleaf.color_temperature_max
        self._attr_min_color_temp_kelvin = self._nanoleaf.color_temperature_min

    @property
    def icon(self) -> str | None:
        """Return the icon based on the device shape."""
        if self._nanoleaf.model.startswith(STRIP_MODEL_PREFIXES):
            return "mdi:led-strip-variant"
        return "mdi:triangle-outline"

    @property
    def brightness(self) -> int:
        """Return the brightness of the light."""
        return int(self._nanoleaf.brightness * 2.55)

    @property
    def color_temp_kelvin(self) -> int:
        """Return the current color temperature."""
        return self._nanoleaf.color_temperature

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        # The API reports *Solid* when the light is in HS or CT mode, and
        # *Static* / *Dynamic* are not selectable effects. None of them are in
        # the effect list: https://forum.nanoleaf.me/docs/openapi#_byoot0bams8f
        if self._nanoleaf.effect in RESERVED_EFFECTS:
            return None
        if self._nanoleaf.effect == "*Emersion*":
            return self._nanoleaf.emersion
        return self._nanoleaf.effect

    @property
    def effect_list(self) -> list[str]:
        """Return device effects plus the bundled scenes."""
        effects: OrderedDict[str, None] = OrderedDict.fromkeys(self._nanoleaf.effects_list)
        effects.update(OrderedDict.fromkeys(SCENES))
        if self._nanoleaf.model in EMERSION_MODELS:
            effects.update(OrderedDict.fromkeys(EMERSION_MODES))
        return list(effects)

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        return self._nanoleaf.is_on

    @property
    def hs_color(self) -> tuple[int, int]:
        """Return the color in HS."""
        return self._nanoleaf.hue, self._nanoleaf.saturation

    @property
    def color_mode(self) -> ColorMode | None:
        """Return the color mode of the light."""
        # The API color mode is "ct", "effect" or "hs"; Home Assistant has no
        # effect color mode, so report those as HS.
        # https://forum.nanoleaf.me/docs/openapi#_4qgqrz96f44d
        if self._nanoleaf.color_mode == "ct":
            return ColorMode.COLOR_TEMP
        return ColorMode.HS

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        hs_color = kwargs.get(ATTR_HS_COLOR)
        color_temp_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)
        effect = kwargs.get(ATTR_EFFECT)
        transition = kwargs.get(ATTR_TRANSITION)

        if effect:
            if effect not in self.effect_list:
                raise ValueError(f"Attempting to apply effect not in the effect list: '{effect}'")
            if effect in EMERSION_MODES:
                await self._nanoleaf.set_emersion(effect)
            else:
                await self._async_select_effect(effect)

        elif hs_color:
            hue, saturation = hs_color
            await self._nanoleaf.set_hue(int(hue))
            await self._nanoleaf.set_saturation(int(saturation))

        elif color_temp_kelvin:
            await self._nanoleaf.set_color_temperature(color_temp_kelvin)

        if transition:
            # Tune brightness over the transition window instead of snapping.
            await self._nanoleaf.set_brightness(int((brightness or 100) / 2.55), transition=int(transition))
        else:
            await self._nanoleaf.turn_on()
            if brightness:
                await self._nanoleaf.set_brightness(int(brightness / 2.55))
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        transition: float | None = kwargs.get(ATTR_TRANSITION)
        await self._nanoleaf.turn_off(None if transition is None else int(transition))
        await self.coordinator.async_refresh()

    async def _async_select_effect(self, name: str) -> None:
        """Select an effect, installing a bundled scene on the device on first use."""
        if name in SCENES and name not in self._nanoleaf.effects_list:
            await install_scene(self._nanoleaf, name, SCENES[name])
        await self._nanoleaf.set_effect(name)
