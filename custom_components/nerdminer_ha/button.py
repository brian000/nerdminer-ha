"""Nerdminer-HA buttons."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NerdMinerCoordinator


@dataclass(frozen=True)
class ButtonDescription:
    """Describe a Nerdminer-HA button."""

    key: str
    name: str
    path: str


BUTTONS = (
    ButtonDescription("restart", "Restart", "/api/axehub/v1/system/restart"),
    ButtonDescription("reset_stats", "Reset Statistics", "/api/axehub/v1/system/reset_stats"),
    ButtonDescription("display_next", "Next Display Mode", "/api/axehub/v1/display/mode"),
    ButtonDescription("buzzer_test", "Test Buzzer", "/api/axehub/v1/buzzer/test"),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nerdminer-HA buttons."""
    coordinator: NerdMinerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        NerdMinerButton(coordinator, entry, description) for description in BUTTONS
    )


class NerdMinerButton(CoordinatorEntity[NerdMinerCoordinator], ButtonEntity):
    """Represent an action on a Nerdminer-HA device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, description: ButtonDescription) -> None:
        super().__init__(coordinator)
        device = coordinator.data.get("device", {})
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=device.get("hostname", entry.title),
            manufacturer="Nerdminer-HA",
            model=device.get("board"),
            sw_version=coordinator.data.get("firmware", {}).get("version"),
        )
        self.description = description

    async def async_press(self) -> None:
        """Call the button's API endpoint."""
        payload = {"action": "next"} if self.description.key == "display_next" else None
        await self.coordinator.async_request(self.description.path, payload=payload)
        if self.description.key not in {"restart", "reset_stats"}:
            await self.coordinator.async_refresh()