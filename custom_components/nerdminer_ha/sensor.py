"""NerdMiner sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfFrequency,
    UnitOfInformation,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NerdMinerCoordinator

# Hashrate figures from the AxeHub API are reported in kH/s.
_HASHRATE_KEYS = ("current_khs", "average_1m_khs", "average_5m_khs", "hw_khs", "sw_khs")

SENSORS = (
    SensorEntityDescription(
        key="current_khs",
        name="Current Hashrate",
        native_unit_of_measurement="kH/s",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:pickaxe",
    ),
    SensorEntityDescription(
        key="average_1m_khs",
        name="1 Minute Average Hashrate",
        native_unit_of_measurement="kH/s",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:pickaxe",
    ),
    SensorEntityDescription(
        key="average_5m_khs",
        name="5 Minute Average Hashrate",
        native_unit_of_measurement="kH/s",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:pickaxe",
    ),
    SensorEntityDescription(
        key="hw_khs",
        name="Hardware Hashrate",
        native_unit_of_measurement="kH/s",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:pickaxe",
    ),
    SensorEntityDescription(
        key="sw_khs",
        name="Software Hashrate",
        native_unit_of_measurement="kH/s",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:pickaxe",
    ),
    SensorEntityDescription(
        key="shares_accepted",
        name="Shares Accepted",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:check-bold",
    ),
    SensorEntityDescription(
        key="shares_rejected",
        name="Shares Rejected",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:close-circle",
    ),
    SensorEntityDescription(
        key="best_diff",
        name="Best Difficulty",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key="best_session_diff",
        name="Best Session Difficulty",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key="valid_blocks",
        name="Valid Blocks",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:bitcoin",
    ),
    SensorEntityDescription(
        key="temp_board_c",
        name="Board Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="uptime_s",
        name="Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.DAYS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="cpu_freq_mhz",
        name="CPU Frequency",
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="heap_free_bytes",
        name="Free Heap",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="wifi_rssi_dbm",
        name="Wi-Fi Signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="last_reset_reason",
        name="Last Reset Reason",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="hostname",
        name="Hostname",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="board",
        name="Board",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

# Maps each sensor key to its (section, field) location in the /info payload.
SENSOR_PATHS = {
    **{key: ("hashing", key) for key in (*_HASHRATE_KEYS, "shares_accepted", "shares_rejected", "best_diff", "best_session_diff", "valid_blocks")},
    "temp_board_c": ("hardware", "temp_board_c"),
    "uptime_s": ("hardware", "uptime_s"),
    "cpu_freq_mhz": ("hardware", "cpu_freq_mhz"),
    "heap_free_bytes": ("hardware", "heap_free_bytes"),
    "wifi_rssi_dbm": ("hardware", "wifi_rssi_dbm"),
    "last_reset_reason": ("hardware", "last_reset_reason"),
    "firmware_version": ("firmware", "version"),
    "mac": ("device", "mac"),
    "hostname": ("device", "hostname"),
    "board": ("device", "board"),
    "chip": ("device", "chip"),
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
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        device = coordinator.data.get("device", {}) if coordinator.data else {}
        mac = device.get("mac") if isinstance(device, dict) else None
        firmware_version = (coordinator.data or {}).get("firmware", {}).get("version") if coordinator.data else None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=device.get("hostname", entry.title),
            manufacturer="Nerdminer-HA",
            model=device.get("board"),
            hw_version=device.get("chip"),
            sw_version=firmware_version,
            connections={(CONNECTION_NETWORK_MAC, mac)} if isinstance(mac, str) and mac else None,
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
