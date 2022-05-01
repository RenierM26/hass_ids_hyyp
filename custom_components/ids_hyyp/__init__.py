"""Support for Ezviz camera."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TIMEOUT, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from pyhyypapi import HTTPError, HyypApiError, HyypClient, InvalidURL

from .const import CONF_PKG, DATA_COORDINATOR, DEFAULT_TIMEOUT, DOMAIN
from .coordinator import HyypDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: dict[str, list] = {
    Platform.ALARM_CONTROL_PANEL,
    Platform.SWITCH,
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IDS Hyyp from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    if not entry.options:
        options = {
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
        }

        hass.config_entries.async_update_entry(entry, options=options)

    hyyp_client = HyypClient(
        token=entry.data.get(CONF_TOKEN), pkg=entry.data.get(CONF_PKG)
    )

    coordinator = HyypDataUpdateCoordinator(
        hass, api=hyyp_client, api_timeout=entry.options[CONF_TIMEOUT]
    )

    hass.data[DOMAIN][entry.entry_id] = {DATA_COORDINATOR: coordinator}

    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
