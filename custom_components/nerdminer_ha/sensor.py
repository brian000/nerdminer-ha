"""NerdMiner sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NerdMinerCoordinator


SENSORS = (
    SensorEntityDescription(key="current_khs", name="Current Hashrate", native_unit_of_measurement="kH/s"),
    SensorEntityDescription(key="average_1m_khs", name="1 Minute Average Hashrate", native_unit_of_measurement="kH/s"),
    SensorEntityDescription(key="average_5m_khs", name="5 Minute Average Hashrate", native_unit_of_measurement="kH/s"),
    SensorEntityDescription(key="shares_accepted", name="Shares Accepted"),
    SensorEntityDescription(key="shares_rejected", name="Shares Rejected"),
    SensorEntityDescription(key="best_diff", name="Best Difficulty"),
    SensorEntityDescription(key="best_session_diff", name="Best Session Difficulty"),
    SensorEntityDescription(key="valid_blocks", name="Valid Blocks"),
    SensorEntityDescription(key="hw_khs", name="Hardware Hashrate", native_unit_of_measurement="kH/s"),
    SensorEntityDescription(key="sw_khs", name="Software Hashrate", native_unit_of_measurement="kH/s"),
    SensorEntityDescription(key="temp_board_c", name="Board Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE),
    SensorEntityDescription(key="uptime_s", name="Uptime", native_unit_of_measurement="s"),
    SensorEntityDescription(key="cpu_freq_mhz", name="CPU Frequency", native_unit_of_measurement="MHz"),
    SensorEntityDescription(key="mac", name="MAC Address", entity_category=EntityCategory.DIAGNOSTIC),
)

SENSOR_PATHS = {
    **{description.key: ("hashing", description.key) for description in SENSORS[:10]},
    "temp_board_c": ("hardware", "temp_board_c"),
    "uptime_s": ("hardware", "uptime_s"),
    "cpu_freq_mhz": ("hardware", "cpu_freq_mhz"),
    "mac": ("device", "mac"),
}


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
        for key in SENSOR_PATHS[self.entity_description.key]:
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value
