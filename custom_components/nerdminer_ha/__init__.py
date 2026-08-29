"""NerdMiner integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import NerdMinerCoordinator

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the NerdMiner integration."""
    card_path = Path(__file__).parent / "nerdminer-card.js"
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                "/nerdminer_ha/nerdminer-card.js", str(card_path), cache_headers=False
            )
        ]
    )
    frontend.add_extra_js_url(hass, "/nerdminer_ha/nerdminer-card.js")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NerdMiner from a config entry."""
    coordinator = NerdMinerCoordinator(hass, entry.data[CONF_HOST])
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a NerdMiner config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
