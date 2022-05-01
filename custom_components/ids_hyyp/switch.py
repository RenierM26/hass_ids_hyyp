"""Support for IDS Hyyp Switches."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyhyypapi.exceptions import HTTPError, HyypApiError

from .const import ATTR_BYPASS_CODE, DATA_COORDINATOR, DOMAIN, SERVICE_BYPASS_ZONE
from .coordinator import HyypDataUpdateCoordinator
from .entity import HyypEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Hyyp switch based on a config entry."""
    coordinator: HyypDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    bypass_code = entry.options.get(ATTR_BYPASS_CODE)

    async_add_entities(
        [
            HyypSwitch(coordinator, partition_id, zone_id, bypass_code)
            for partition_id in coordinator.data
            for zone_id in coordinator.data[partition_id]["zones"]
        ]
    )

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_BYPASS_ZONE,
        {vol.Required(ATTR_BYPASS_CODE): str},
        "perform_zone_bypass_code",
    )


class HyypSwitch(HyypEntity, SwitchEntity):
    """Representation of a IDS Hyyp entity Switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator: HyypDataUpdateCoordinator,
        partition_id: str,
        zone_id: str,
        bypass_code,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, partition_id)
        self._bypass_code = bypass_code
        self._zone_id = zone_id
        self._attr_name = f"{self.data['zones'][zone_id]['name'].title()}"
        self._attr_unique_id = f"{self._site_id}_{partition_id}_{zone_id}"

    @property
    def available(self) -> bool:
        """Check if device is reporting online from api."""
        return self.data["site"][self._site_id]

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return not self.data["zones"][self._zone_id]["bypassed"]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch entity on."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.set_zone_bypass,
                self._partition_id,
                self._zone_id,
                0,
                self._bypass_code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to turn on switch {self._attr_name}") from err

        if update_ok["status"] == "SUCCESS":
            await self.coordinator.async_request_refresh()

        elif update_ok["status"] == "PENDING":
            raise HyypApiError(f"Code required to bypass zone {self._attr_name}")

        else:
            raise HyypApiError(
                f"Failed to bypass zone {self._attr_name} failed with: {update_ok}"
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch entity off."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.set_zone_bypass,
                self._partition_id,
                self._zone_id,
                0,
                self._bypass_code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError("Failed to turn on switch {self._attr_name}") from err

        if update_ok["status"] == "SUCCESS":
            await self.coordinator.async_request_refresh()

        elif update_ok["status"] == "PENDING":
            raise HyypApiError(f"Code required to bypass zone {self._attr_name}")

        else:
            raise HyypApiError(
                f"Disable bypass on zone {self._attr_name} failed with: {update_ok}"
            )

    async def perform_zone_bypass_code(self, code: Any = None) -> None:
        """Service to bypass zone if code is not set in options."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.set_zone_bypass,
                self._partition_id,
                self._zone_id,
                0,
                code,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError(f"Failed to turn on switch {self._attr_name}") from err

        if update_ok["status"] == "SUCCESS":
            await self.coordinator.async_request_refresh()

        else:
            raise HyypApiError(
                f"Disable bypass on zone {self._attr_name} failed with: {update_ok}"
            )
