"""An abstract class common to all Hyyp entities."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import HyypDataUpdateCoordinator


class HyypEntity(CoordinatorEntity[HyypDataUpdateCoordinator], Entity):
    """Generic entity encapsulating common features of Hyyp Alarms."""

    def __init__(
        self,
        coordinator: HyypDataUpdateCoordinator,
        partition_id: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._partition_id = partition_id
        self._site_id = list(self.data["site"])[0]
        self._arm_home_profile_id = list(self.data["stayProfile"])[
            0
        ]  # Supports multiple stay profiles. Assume first is arm home.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._site_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=self.data["name"],
        )

    @property
    def data(self) -> Any:
        """Return coordinator data for this entity."""
        return self.coordinator.data[self._partition_id]
