"""Support for IDS Hyyp alarms."""
from __future__ import annotations

from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from pyhyypapi.exceptions import HTTPError, HyypApiError

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import HyypDataUpdateCoordinator
from .entity import HyypEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Ezviz alarm control panel."""
    coordinator: HyypDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    async_add_entities(
        [HyypAlarm(coordinator, partition_id) for partition_id in coordinator.data]
    )


class HyypAlarm(HyypEntity, AlarmControlPanelEntity):
    """Representation of a Hyyp alarm control panel."""

    coordinator: HyypDataUpdateCoordinator
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_NIGHT
        | AlarmControlPanelEntityFeature.ARM_AWAY
    )
    _attr_code_arm_required = True

    def __init__(
        self, coordinator: HyypDataUpdateCoordinator, partition_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, partition_id)
        self._attr_name = self.data["name"]
        self._attr_unique_id = f"{self._site_id}_{partition_id}_Alarm"

    @property
    def available(self) -> bool:
        """Check if device is reporting online from api."""
        return self.data["site"][self._site_id]

    @property
    def state(self) -> StateType:
        """Update alarm state."""

        if self.data["alarm"]:
            return self._attr_state == STATE_ALARM_TRIGGERED

        if self.data["armed"] and not self.data["stayArmed"]:
            self._attr_state = STATE_ALARM_ARMED_AWAY

        if not self.data["armed"] and not self.data["stayArmed"]:
            self._attr_state = STATE_ALARM_DISARMED

        if self.data["armed"] and self.data["stayArmed"]:
            self._attr_state = STATE_ALARM_ARMED_NIGHT

        return self._attr_state

    def alarm_disarm(self, code: Any = None) -> None:
        """Send disarm command."""
        try:
            response = self.coordinator.hyyp_client.arm_site(
                arm=False,
                pin=code,
                partition_id=self._partition_id,
                site_id=self._site_id,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError("Cannot disarm alarm") from err

        if response["status"] == "SUCCESS":
            self._attr_state = STATE_ALARM_DISARMED

        else:
            raise HTTPError("Cannot disarm alarm.")

    def alarm_arm_away(self, code: Any = None) -> None:
        """Send arm away command."""
        try:
            response = self.coordinator.hyyp_client.arm_site(
                arm=True,
                pin=code,
                partition_id=self._partition_id,
                site_id=self._site_id,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError("Cannot disarm alarm") from err

        if response["status"] == "SUCCESS":
            self._attr_state = STATE_ALARM_ARMED_AWAY

        else:
            raise HTTPError("Cannot arm alarm, check for violated zones.")

    def alarm_arm_night(self, code: Any = None) -> None:
        """Send arm night command."""
        try:
            response = self.coordinator.hyyp_client.arm_site(
                arm=True,
                pin=code,
                partition_id=self._partition_id,
                site_id=self._site_id,
                stay_profile_id=self._arm_night_profile_id,
            )

        except (HTTPError, HyypApiError) as err:
            raise HyypApiError("Cannot disarm alarm") from err

        if response["status"] == "SUCCESS":
            self._attr_state = STATE_ALARM_ARMED_NIGHT

        else:
            raise HTTPError("Cannot arm alarm, check for violated zones.")
