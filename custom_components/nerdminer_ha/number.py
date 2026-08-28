"""Nerdminer-HA number entities."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NerdMinerCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nerdminer-HA number entities."""
    async_add_entities([NerdMinerBrightness(hass.data[DOMAIN][entry.entry_id], entry)])


class NerdMinerBrightness(CoordinatorEntity[NerdMinerCoordinator], NumberEntity):
    """Control display brightness."""

    _attr_has_entity_name = True
    _attr_name = "Display Brightness"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        device = coordinator.data.get("device", {})
        self._attr_unique_id = f"{entry.entry_id}_brightness"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=device.get("hostname", entry.title),
            manufacturer="Nerdminer-HA",
            model=device.get("board"),
            sw_version=coordinator.data.get("firmware", {}).get("version"),
        )

    @property
    def native_value(self):
        """Return brightness as a percentage."""
        return self.coordinator.data.get("display", {}).get("brightness_pct")

    async def async_set_native_value(self, value: float) -> None:
        """Set brightness on the device."""
        await self.coordinator.async_request(
            "/api/axehub/v1/display/brightness",
            payload={"value": round(value * 255 / 100), "persist": True},
        )
        await self.coordinator.async_refresh()