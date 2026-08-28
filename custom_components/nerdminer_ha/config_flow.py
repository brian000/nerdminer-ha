"""Config flow for NerdMiner."""

from __future__ import annotations

import voluptuous as vol
from aiohttp import ClientError
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig

from .const import API_PATH, DEFAULT_NAME, DOMAIN


class NerdMinerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a NerdMiner config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip().rstrip("/")
            try:
                session = async_get_clientsession(self.hass)
                async with session.get(f"http://{host}{API_PATH}") as response:
                    response.raise_for_status()
                    data = await response.json()
            except (ClientError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                mac = data.get("device", {}).get("mac") if isinstance(data, dict) else None
                if not isinstance(mac, str) or not mac:
                    errors["base"] = "invalid_response"
                else:
                    await self.async_set_unique_id(mac.lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=data.get("device", {}).get("hostname", DEFAULT_NAME),
                        data={CONF_HOST: host},
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): TextSelector(
                    TextSelectorConfig(type="text", autocomplete="off")
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
