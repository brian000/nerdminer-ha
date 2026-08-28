"""NerdMiner sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NerdMinerCoordinator


@dataclass(frozen=True)
class SensorDescription:
    """Describe one NerdMiner sensor."""

    key: str
    name: str
    path: tuple[str, ...]
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    entity_category: EntityCategory | None = None


SENSORS = (
    SensorDescription("current_khs", "Current Hashrate", ("hashing", "current_khs"), "kH/s"),
    SensorDescription("average_1m_khs", "1 Minute Average Hashrate", ("hashing", "average_1m_khs"), "kH/s"),
    SensorDescription("average_5m_khs", "5 Minute Average Hashrate", ("hashing", "average_5m_khs"), "kH/s"),
    SensorDescription("shares_accepted", "Shares Accepted", ("hashing", "shares_accepted")),
    SensorDescription("shares_rejected", "Shares Rejected", ("hashing", "shares_rejected")),
    SensorDescription("best_diff", "Best Difficulty", ("hashing", "best_diff")),
    SensorDescription("best_session_diff", "Best Session Difficulty", ("hashing", "best_session_diff")),
    SensorDescription("valid_blocks", "Valid Blocks", ("hashing", "valid_blocks")),
    SensorDescription("hw_khs", "Hardware Hashrate", ("hashing", "hw_khs"), "kH/s"),
    SensorDescription("sw_khs", "Software Hashrate", ("hashing", "sw_khs"), "kH/s"),
    SensorDescription("temp_board_c", "Board Temperature", ("hardware", "temp_board_c"), UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    SensorDescription("uptime_s", "Uptime", ("hardware", "uptime_s"), "s"),
    SensorDescription("cpu_freq_mhz", "CPU Frequency", ("hardware", "cpu_freq_mhz"), "MHz"),
    SensorDescription("mac", "MAC Address", ("device", "mac"), entity_category=EntityCategory.DIAGNOSTIC),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up NerdMiner sensors from a config entry."""
    coordinator: NerdMinerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(NerdMinerSensor(coordinator, entry, description) for description in SENSORS)


class NerdMinerSensor(CoordinatorEntity[NerdMinerCoordinator], SensorEntity):
    """Represent one value from a NerdMiner device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NerdMinerCoordinator,
        entry: ConfigEntry,
        description: SensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_native_unit_of_measurement = description.unit
        self._attr_device_class = description.device_class
        self._attr_entity_category = description.entity_category
        device = coordinator.data.get("device", {}) if coordinator.data else {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=device.get("hostname", entry.title),
            manufacturer="Nerdminer-HA",
            model=device.get("board"),
            sw_version=coordinator.data.get("firmware", {}).get("version") if coordinator.data else None,
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value from the API response."""
        value: Any = self.coordinator.data
        for key in self.entity_description.path:
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value
