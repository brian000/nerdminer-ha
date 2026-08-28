"""Constants for the NerdMiner integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "nerdminer_ha"
CONF_HOST: Final = "host"
DEFAULT_NAME: Final = "Nerdminer-HA"
DEFAULT_SCAN_INTERVAL: Final = 30
API_PATH: Final = "/api/axehub/v1/info"
API_HEADERS: Final = {"X-AxeHub-Compat": "1"}

