"""Data coordinator for NerdMiner devices."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_HEADERS, API_JSON_HEADERS, API_PATH, DEFAULT_SCAN_INTERVAL

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
        return await self.async_request(API_PATH)

    async def async_request(
        self,
        path: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        expect_json: bool = True,
    ) -> dict[str, Any] | None:
        """Make an authenticated request to the device API."""
        session = async_get_clientsession(self.hass)
        try:
            headers = API_JSON_HEADERS if payload is not None else API_HEADERS
            async with session.request(
                method,
                f"http://{self.host}{path}",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                if not expect_json:
                    return None
                data = await response.json(content_type=None)
        except (ClientError, ValueError) as err:
            _LOGGER.error("Nerdminer-HA request failed: %s %s", method, path)
            raise UpdateFailed(f"Unable to request data from {self.host}") from err

        if not isinstance(data, dict):
            raise UpdateFailed("Nerdminer-HA API returned an invalid response")
        return data
