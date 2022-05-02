"""Support for Hyyp sensors."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import HyypDataUpdateCoordinator
from .entity import HyypEntity

PARALLEL_UPDATES = 1

SENSOR_TYPES: dict[str, SensorEntityDescription] = {
    "dateTime": SensorEntityDescription(key="dateTime"),
    "eventName": SensorEntityDescription(key="eventName"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up IDS Hyyp sensors based on a config entry."""
    coordinator: HyypDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    async_add_entities(
        [
            HyypSensor(coordinator, partition_id, sensor)
            for partition_id in coordinator.data
            for sensor in coordinator.data[partition_id]["lastNotification"].keys()
        ]
    )


class HyypSensor(HyypEntity, SensorEntity):
    """Representation of a IDS Hyyp sensor."""

    coordinator: HyypDataUpdateCoordinator

    def __init__(
        self, coordinator: HyypDataUpdateCoordinator, partition_id: str, sensor: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, partition_id)
        self._sensor_name = sensor
        self._attr_name = (
            f"{self.data['site'][self._site_id]['name']} Last Event {sensor.title()}"
        )
        self._attr_unique_id = f"{self._site_id}_{partition_id}_{sensor}"
        self.entity_description = SENSOR_TYPES[sensor]

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.data["lastNotification"][self._sensor_name]
