"""Config flow for La Meteo Agricole."""

from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import parse_qs, urlparse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LaMeteoAgricoleClient, LaMeteoAgricoleError, normalize_url
from .const import CONF_URL, DOMAIN


class LaMeteoAgricoleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for La Meteo Agricole."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = normalize_url(user_input[CONF_URL])
            parsed = urlparse(url)
            commune = _unique_id_from_url(url)

            await self.async_set_unique_id(commune)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = LaMeteoAgricoleClient(session, url)
            try:
                weather = await client.async_get_weather()
            except LaMeteoAgricoleError:
                errors["base"] = "cannot_connect"
            else:
                title = weather.location_name or f"La Meteo Agricole {commune}"
                return self.async_create_entry(title=title, data={CONF_URL: url})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default="https://www.lameteoagricole.net/previsions-meteo-agricole/Fains-la-Folie-28150.html",
                    ): str
                }
            ),
            errors=errors,
        )


def _unique_id_from_url(url: str) -> str:
    """Build a stable unique id from supported La Meteo Agricole URLs."""
    parsed = urlparse(url)
    communehome = parse_qs(parsed.query).get("communehome")
    if communehome:
        return communehome[0]

    slug = PurePosixPath(parsed.path).name.removesuffix(".html")
    return slug.lower() or url
