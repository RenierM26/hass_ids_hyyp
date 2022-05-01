"""Support for IDS Hyyp Switches."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyhyypapi.exceptions import HTTPError, HyypApiError

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import HyypDataUpdateCoordinator
from .entity import HyypEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Hyyp switch based on a config entry."""
    coordinator: HyypDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    async_add_entities(
        [
            HyypSwitch(coordinator, partition_id, zone_id)
            for partition_id in coordinator.data
            for zone_id in coordinator.data[partition_id]["zones"]
        ]
    )


class HyypSwitch(HyypEntity, SwitchEntity):
    """Representation of a IDS Hyyp entity Switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self, coordinator: HyypDataUpdateCoordinator, partition_id: str, zone_id: str
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, partition_id)
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
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError("Failed to turn on switch {self._attr_name}") from err

        if update_ok:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch entity off."""
        try:
            update_ok = await self.hass.async_add_executor_job(
                self.coordinator.hyyp_client.set_zone_bypass,
                self._partition_id,
                self._zone_id,
                0,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError("Failed to turn on switch {self._attr_name}") from err

        if update_ok:
            await self.coordinator.async_request_refresh()
