"""Support for connectedcars.io / Min Volkswagen integration."""

from datetime import UTC, datetime, timedelta, timezone
import logging
import traceback

from homeassistant import config_entries, core
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    # SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolume,
)

# from homeassistant.helpers.entity import Entity
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up the Connectedcars_io sensor platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]

    _connectedcarsclient = config["connectedcarsclient"]

    try:
        sensors = []
        sensors_update_later = []
        data = await _connectedcarsclient.get_vehicle_instances(True)
        for vehicle in data:
            if "outdoorTemperature" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(
                        vehicle, "outdoorTemperature", True, _connectedcarsclient
                    )
                )
            if "BatteryVoltage" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(vehicle, "BatteryVoltage", True, _connectedcarsclient)
                )
            if "odometer" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(vehicle, "odometer", True, _connectedcarsclient)
                )
            if "fuelPercentage" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(vehicle, "fuelPercentage", True, _connectedcarsclient)
                )
            if "fuelLevel" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(vehicle, "fuelLevel", True, _connectedcarsclient)
                )
            if "fuelEconomy" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(vehicle, "fuel economy", False, _connectedcarsclient)
                )
            if "NextServicePredicted" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(
                        vehicle, "NextServicePredicted", False, _connectedcarsclient
                    )
                )
            if "EVchargePercentage" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(
                        vehicle, "EVchargePercentage", True, _connectedcarsclient
                    )
                )
            if "EVHVBattTemp" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(vehicle, "EVHVBattTemp", True, _connectedcarsclient)
                )
            if "RangeTotal" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(vehicle, "Range", False, _connectedcarsclient)
                )
            if "Speed" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(vehicle, "Speed", True, _connectedcarsclient)
                )
            if "totalTripStatistics" in vehicle["has"]:
                sensors.append(
                    MinVwEntity(
                        vehicle, "mileage latest year", False, _connectedcarsclient
                    )
                )
                sensors.append(
                    MinVwEntity(
                        vehicle, "mileage latest month", False, _connectedcarsclient
                    )
                )            
            if (
                "refuelEvents" in vehicle["has"]
                and "trips" in vehicle["has"]
                and "odometer" in vehicle["has"]
            ):
                sensors_update_later.append(
                    MinVwEntityRestore(
                        vehicle, "mileage since refuel", False, _connectedcarsclient
                    )
                )
            sensors.append(
                    MinVwEntity(
                        vehicle, "latest refresh", True, _connectedcarsclient
                    )
                )
            
        async_add_entities(sensors, update_before_add=True)
        async_add_entities(sensors_update_later, update_before_add=False)

    except Exception as err:
        _LOGGER.warning("Failed to add sensors: %s", err)
        _LOGGER.debug("%s", traceback.format_exc())
        raise PlatformNotReady from err
    
    async def handle_refresh_data_event(event):
        """Handle button press event and refresh sensor data."""
        vin = event.data["vin"]
        _LOGGER.info("Received refresh event for VIN: %s", vin)
        MinVwEntity.async_update(vehicle)

    # Build array with devices to keep
    devices = [(DOMAIN, vehicle["vin"]) for vehicle in data]
    # devices = []
    # for vehicle in data:
    #    devices.append((DOMAIN, vehicle["vin"]))

    # Remove devices no longer reported
    device_registry = dr.async_get(hass)
    for device_entry in dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    ):
        for identifier in device_entry.identifiers:
            if identifier not in devices:
                _LOGGER.warning("Removing device: %s", identifier)
                device_registry.async_remove_device(device_entry.id)


class MinVwEntity(SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self, vehicle, itemName, entity_registry_enabled_default, connectedcarsclient
    ) -> None:
        """Initialize the sensor."""
        self._state = None
        self._data_date = None
        self._unit = None
        self._vehicle = vehicle
        self._itemName = itemName
        self._icon = "mdi:car"
        self._suggested_display_precision = None
        self._name = (
            f"{self._vehicle['make']} {self._vehicle['model']} {self._itemName}"
        )
        self._unique_id = f"{DOMAIN}-{self._vehicle['vin']}-{self._itemName}"
        self._device_class = None
        self._connectedcarsclient = connectedcarsclient
        self._entity_registry_enabled_default = entity_registry_enabled_default
        self._dict = {}
        self._updated = None

        if self._itemName == "outdoorTemperature":
            self._unit = UnitOfTemperature.CELSIUS
            self._icon = "mdi:thermometer"
            self._device_class = SensorDeviceClass.TEMPERATURE
        elif self._itemName == "BatteryVoltage":
            self._unit = UnitOfElectricPotential.VOLT
            self._icon = "mdi:car-battery"
            self._device_class = SensorDeviceClass.VOLTAGE
        elif self._itemName == "fuelPercentage":
            self._unit = PERCENTAGE
            self._icon = "mdi:gas-station"
            # self._device_class = SensorDeviceClass.
        elif self._itemName == "fuelLevel":
            self._unit = UnitOfVolume.LITERS
            self._icon = "mdi:gas-station"
            self._device_class = SensorDeviceClass.VOLUME
        elif self._itemName == "odometer":
            self._unit = UnitOfLength.KILOMETERS
            self._icon = "mdi:counter"
            self._device_class = SensorDeviceClass.DISTANCE
            self._attr_state_class = SensorStateClass.TOTAL
        elif self._itemName == "NextServicePredicted":
            # self._unit = ATTR_LOCATION
            self._icon = "mdi:wrench"
            self._device_class = SensorDeviceClass.DATE
        elif self._itemName == "EVchargePercentage":
            self._unit = PERCENTAGE
            self._icon = "mdi:battery"
            self._device_class = SensorDeviceClass.BATTERY
        elif self._itemName == "EVHVBattTemp":
            self._unit = UnitOfTemperature.CELSIUS
            self._icon = "mdi:thermometer"
            self._device_class = SensorDeviceClass.TEMPERATURE
        elif self._itemName == "Range":
            self._unit = UnitOfLength.KILOMETERS
            self._icon = "mdi:map-marker-distance"
            self._device_class = SensorDeviceClass.DISTANCE
        elif self._itemName == "Speed":
            self._unit = UnitOfSpeed.KILOMETERS_PER_HOUR
            self._icon = "mdi:speedometer"
            self._device_class = SensorDeviceClass.SPEED
        elif self._itemName == "mileage latest year":
            self._unit = UnitOfLength.KILOMETERS
            self._icon = "mdi:counter"
            self._device_class = SensorDeviceClass.DISTANCE
        elif self._itemName == "mileage latest month":
            self._unit = UnitOfLength.KILOMETERS
            self._icon = "mdi:counter"
            self._device_class = SensorDeviceClass.DISTANCE
        elif self._itemName == "mileage since refuel":
            self._unit = UnitOfLength.KILOMETERS
            self._icon = "mdi:counter"
            self._device_class = SensorDeviceClass.DISTANCE
        elif self._itemName == "fuel economy":
            self._unit = "km/l"
            self._icon = "mdi:gas-station-outline"
            self._suggested_display_precision = 1
        elif self._itemName == "latest refresh":
            self._device_class = SensorDeviceClass.DATE
            self._icon = "mdi:clock"
        _LOGGER.debug("Adding sensor: %s", self._unique_id)

    @property
    def device_info(self):
        """Device info."""
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._vehicle["vin"])
            },
            "name": f"{self._vehicle['make']} {self._vehicle['model']}",  # self._vehicle["name"],
            "manufacturer": self._vehicle["make"],
            "model": self._vehicle["name"]
            .removeprefix("VW")
            .removeprefix("Skoda")
            .removeprefix("Seat")
            .removeprefix("Audi")
            .strip(),
            "sw_version": self._vehicle["licensePlate"],
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def entity_registry_enabled_default(self):
        """Enabled by default."""
        return self._entity_registry_enabled_default

    @property
    def icon(self):
        """Icon."""
        return self._icon

    @property
    def unique_id(self):
        """The unique id of the sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def available(self):
        """Availability."""
        return self._state is not None

    @property
    def device_class(self):
        """Device class."""
        return self._device_class

    @property
    def extra_state_attributes(self):
        """Return state attributes."""
        attributes = {}
        # attributes['state_class'] = self._state_class
        #        if self._device_class is not None:
        #            attributes['device_class'] = self._device_class
        if self._updated is not None:
            attributes["Updated"] = self._updated
        attributes.update(self._dict)
        # for key in self._dict:
        #    attributes[key] = self._dict[key]
        return attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def suggested_display_precision(self):
        """Return the suggested_display_precision."""
        return self._suggested_display_precision

    async def async_update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        # _LOGGER.debug(f"Setting status for {self._name}")

        if self._itemName == "outdoorTemperature":
            self._state = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["outdoorTemperatures", 0, "celsius"]
            )
            self._updated = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["outdoorTemperatures", 0, "time"]
            )
        if self._itemName == "BatteryVoltage":
            self._state = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["latestBatteryVoltage", "voltage"]
            )
            self._updated = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["latestBatteryVoltage", "time"]
            )
        if self._itemName == "fuelPercentage":
            self._state = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["fuelPercentage", "percent"]
            )
            self._updated = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["fuelPercentage", "time"]
            )
        if self._itemName == "fuelLevel":
            self._state = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["fuelLevel", "liter"]
            )
            self._updated = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["fuelLevel", "time"]
            )
        if self._itemName == "odometer":
            self._state = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["odometer", "odometer"]
            )
            self._updated = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["odometer", "time"]
            )
        if self._itemName == "NextServicePredicted":
            self._state = (
                await self._connectedcarsclient.get_next_service_data_predicted(
                    self._vehicle["id"]
                )
            )
        if self._itemName == "Speed":
            self._state = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["position", "speed"]
            )
            self._dict["Direction"] = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["position", "direction"]
            )
            self._updated = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["position", "time"]
            )
        if self._itemName == "mileage latest year" and (
            self._data_date is None
            or datetime.now(UTC) >= self._data_date + timedelta(hours=1)
        ):
            (
                self._state,
                self._dict,
            ) = await self._connectedcarsclient.get_latest_years_mileage(
                self._vehicle["id"], False
            )
            if self._state is not None:
                self._data_date = datetime.now(UTC)
        if self._itemName == "mileage latest month" and (
            self._data_date is None
            or datetime.now(UTC) >= self._data_date + timedelta(hours=1)
        ):
            (
                self._state,
                self._dict,
            ) = await self._connectedcarsclient.get_latest_years_mileage(
                self._vehicle["id"], True
            )
            if self._state is not None:
                self._data_date = datetime.now(UTC)
        if self._itemName == "mileage since refuel":
            self._state = None

            refuel_event_time = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["refuelEvents", 0, "time"]
            )
            valid_date = is_date_valid(refuel_event_time)
            if valid_date:
                # Has refuel timestamp changed?
                if (
                    "Refueled at" not in self._dict
                    or self._dict["Refueled at"] is None
                    or refuel_event_time != self._dict["Refueled at"]
                ):
                    _LOGGER.debug("Refuel event detected")
                    self._dict["Refueled at"] = refuel_event_time
                    self._dict["Odometer"] = None

                # Do we have odometer value corresponding to refuel timestamp?
                if "Odometer" not in self._dict or self._dict["Odometer"] is None:
                    trip = await self._connectedcarsclient.get_trip_at_time(
                        self._vehicle["id"], refuel_event_time
                    )
                    if (
                        trip is not None
                        and "startOdometer" in trip
                        and trip["startOdometer"] is not None
                    ):
                        _LOGGER.debug(
                            "Got odometer value at refuel event: %s",
                            trip["startOdometer"],
                        )
                        self._dict["Odometer"] = trip["startOdometer"]

            # Subtract refuel odometer from current odometer
            if "Odometer" in self._dict and self._dict["Odometer"] is not None:
                odometer_current = await self._connectedcarsclient.get_value(
                    self._vehicle["id"], ["odometer", "odometer"]
                )
                if odometer_current is not None:
                    distance_since_refuel = odometer_current - self._dict["Odometer"]
                    if distance_since_refuel >= 0:
                        self._state = distance_since_refuel

            # ignition = (
            #     str(
            #         await self._connectedcarsclient.get_value(
            #             self._vehicle["id"], ["ignition", "on"]
            #         )
            #     ).lower()
            #     == "true"
            # )
            # try:
            #     ignition_time = datetime.fromisoformat(
            #         str(
            #             await self._connectedcarsclient.get_value(
            #                 self._vehicle["id"], ["ignition", "time"]
            #             )
            #         ).replace("Z", "+00:00")
            #     )
            # except Exception as err:  # pylint: disable=broad-except
            #     _LOGGER.warning("Unable to parse ignition timestamp. Err: %s", err)
            # _LOGGER.debug("ignition: %s, time: %s", ignition, ignition_time)

            # if (
            #     self._data_date is None
            #     or datetime.utcnow() >= self._data_date + timedelta(hours=1)
            #     or (
            #         not ignition
            #         and ignition_time > self._data_date.replace(tzinfo=timezone.utc)
            #     )
            # ):
            #     (
            #         self._state,
            #         self._dict,
            #     ) = await self._connectedcarsclient.get_mileage_since_refuel(
            #         self._vehicle["id"]
            #     )
            #     _LOGGER.debug("5")
            #     if self._state is not None:
            #         self._data_date = datetime.utcnow()

        if self._itemName == "fuel economy":
            self._state = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["fuelEconomy"]
            )
            # if fuelEconomy is not None:
            #     fuelEconomy = round(fuelEconomy, 1)
            # self._state = fuelEconomy

        # EV
        if self._itemName = "latest refresh":
            self._state = datetime.datetime.now();
        if self._itemName == "EVchargePercentage":
            self._state = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["chargePercentage", "pct"]
            )
            self._updated = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["chargePercentage", "time"]
            )

            batlevel = round(self._state / 10) * 10
            if batlevel == 100:
                self._icon = "mdi:battery"
            elif batlevel == 0:
                self._icon = "mdi:battery-outline"
            else:
                self._icon = f"mdi:battery-{batlevel}"
        if self._itemName == "EVHVBattTemp":
            self._state = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["highVoltageBatteryTemperature", "celsius"]
            )
            self._updated = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["highVoltageBatteryTemperature", "time"]
            )
        if self._itemName == "Range":
            self._state = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["rangeTotalKm", "km"]
            )
            self._updated = await self._connectedcarsclient.get_value(
                self._vehicle["id"], ["rangeTotalKm", "time"]
            )


def is_date_valid(date) -> bool:
    """Check date validity."""
    valid_date = True
    try:
        valid_date = (
            False
            if (date is None)
            else bool(datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f%z"))
        )
    except ValueError:
        valid_date = False
    return valid_date


class MinVwEntityRestore(MinVwEntity, RestoreSensor):
    """Representation of a restoring sensor."""

    # def __init__(
    #     self, vehicle, itemName, entity_registry_enabled_default, connectedcarsclient
    # ):
    #     """Inherited"""
    #     super().__init__(
    #         vehicle, itemName, entity_registry_enabled_default, connectedcarsclient
    #     )

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()

        if (
            (last_state := await self.async_get_last_state()) is not None
            # and (extra_data := await self.async_get_last_sensor_data()) is not None
            and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)
            # The trigger might have fired already while we waited for stored data,
            # then we should not restore state
            #            and CONF_STATE not in self._rendered
        ):
            _LOGGER.debug(
                "Read previously stored state and attributes for sensor: %s",
                self._unique_id,
            )
            self._state = last_state.state

            for key in last_state.attributes:
                if key not in [
                    "unit_of_measurement",
                    "device_class",
                    "icon",
                    "friendly_name",
                ]:
                    self._dict[key] = last_state.attributes[key]
            _LOGGER.debug("State: %s, Attributes: %s", last_state.state, self._dict)

        await MinVwEntity.async_update(self)
        self.async_write_ha_state()

    # async def async_get_last_sensor_data(self):
    #     """Restore Utility Meter Sensor Extra Stored Data."""
    #     _LOGGER.debug("2")
    #     if (restored_last_extra_data := await self.async_get_last_extra_data()) is None:
    #         return None

    #     _LOGGER.debug("3")
    #     return restored_last_extra_data.as_dict()
