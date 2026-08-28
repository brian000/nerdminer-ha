"""Nerdminer-HA switches."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
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
    """Set up the Nerdminer-HA invert-colors switch."""
    async_add_entities([NerdMinerInvertColors(hass.data[DOMAIN][entry.entry_id], entry)])


class NerdMinerInvertColors(CoordinatorEntity[NerdMinerCoordinator], SwitchEntity):
    """Control display color inversion."""

    _attr_has_entity_name = True
    _attr_name = "Invert Display Colors"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        device = coordinator.data.get("device", {})
        self._attr_unique_id = f"{entry.entry_id}_invert_colors"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=device.get("hostname", entry.title),
            manufacturer="Nerdminer-HA",
            model=device.get("board"),
            sw_version=coordinator.data.get("firmware", {}).get("version"),
        )

    @property
    def is_on(self):
        """Return whether display inversion is enabled."""
        return self.coordinator.data.get("display", {}).get("invert_colors")

    async def async_turn_on(self, **kwargs) -> None:
        """Enable display inversion."""
        await self._async_set_inversion(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable display inversion."""
        await self._async_set_inversion(False)

    async def _async_set_inversion(self, enabled: bool) -> None:
        await self.coordinator.async_request(
            "/api/axehub/v1/display/invert", payload={"on": enabled}
        )
        await self.coordinator.async_refresh()