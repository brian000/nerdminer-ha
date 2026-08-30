"""Data coordinator for NerdMiner devices."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_HEADERS, API_PATH, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__package__)


class NerdMinerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate polling a NerdMiner API endpoint."""

    def __init__(self, hass, host: str) -> None:
        self.host = host
        self.url = f"http://{host}{API_PATH}"
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"Nerdminer-HA {host}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the current device information."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(self.url, headers=API_HEADERS) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except (ClientError, ValueError) as err:
            raise UpdateFailed(f"Unable to fetch data from {self.host}") from err

        if not isinstance(data, dict):
            raise UpdateFailed("Nerdminer-HA API returned an invalid response")
        return data

    async def async_post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST a control command to the device and return the JSON response."""
        session = async_get_clientsession(self.hass)
        url = f"http://{self.host}{path}"
        try:
            async with session.post(url, headers=API_HEADERS, json=payload) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except (ClientError, ValueError) as err:
            raise UpdateFailed(f"Unable to send command to {self.host}") from err
        return data if isinstance(data, dict) else {}
