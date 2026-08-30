"""NerdMiner LCD backlight control."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NerdMinerCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the NerdMiner backlight light from a config entry."""
    coordinator: NerdMinerCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.data and "display" in coordinator.data:
        async_add_entities([NerdMinerBacklightLight(coordinator, entry)])


class NerdMinerBacklightLight(CoordinatorEntity[NerdMinerCoordinator], LightEntity):
    """Represent the TFT backlight of a NerdMiner device."""

    _attr_has_entity_name = True
    _attr_name = "Backlight"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator: NerdMinerCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_backlight"
        device = coordinator.data.get("device", {}) if coordinator.data else {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=device.get("hostname", entry.title),
            manufacturer="Nerdminer-HA",
            model=device.get("board"),
            sw_version=coordinator.data.get("firmware", {}).get("version") if coordinator.data else None,
        )

    @property
    def brightness(self) -> int | None:
        """Return the current PWM brightness (0-255)."""
        display = self.coordinator.data.get("display", {}) if self.coordinator.data else {}
        value = display.get("brightness")
        return min(int(value), 255) if isinstance(value, (int, float)) else None

    @property
    def is_on(self) -> bool | None:
        """Return whether the backlight is on."""
        brightness = self.brightness
        return None if brightness is None else brightness > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the backlight, optionally at a given brightness."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, self.brightness or 255)
        await self.coordinator.async_post("/api/axehub/v1/display/brightness", {"value": brightness})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the backlight."""
        await self.coordinator.async_post("/api/axehub/v1/display/brightness", {"value": 0})
        await self.coordinator.async_request_refresh()
