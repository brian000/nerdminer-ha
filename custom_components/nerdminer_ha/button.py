"""NerdMiner buttons."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NerdMinerCoordinator


BUTTONS = (
    ButtonEntityDescription(
        key="restart",
        name="Restart",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ButtonEntityDescription(
        key="next_display",
        name="Next Display",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up NerdMiner buttons from a config entry."""
    coordinator: NerdMinerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        NerdMinerButton(coordinator, entry, description) for description in BUTTONS
    )


class NerdMinerButton(CoordinatorEntity[NerdMinerCoordinator], ButtonEntity):
    """Represent a NerdMiner action button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NerdMinerCoordinator,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

        device = coordinator.data.get("device", {}) if coordinator.data else {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=device.get("hostname", entry.title),
            manufacturer="Nerdminer-HA",
            model=device.get("board"),
            hw_version=device.get("chip"),
            sw_version=(coordinator.data or {}).get("firmware", {}).get("version") if coordinator.data else None,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        if self.entity_description.key == "restart":
            await self.coordinator.async_post("/system/restart", {})
            return

        if self.entity_description.key == "next_display":
            await self.coordinator.async_post("/display/mode", {"action": "next"})
