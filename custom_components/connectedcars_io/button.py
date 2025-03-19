from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up buttons from a config entry."""
    config = hass.data["connectedcars_io"][config_entry.entry_id]
    _connectedcarsclient = config["connectedcarsclient"]

    try:
        buttons = []
        data = await _connectedcarsclient.get_vehicle_instances(True)
        for vehicle in data:
            buttons.append(MyCustomButton(vehicle, _connectedcarsclient))

        async_add_entities(buttons, update_before_add=True)
    except Exception as err:
        _LOGGER.warning("Failed to add button: %s", err)

class MyCustomButton(ButtonEntity):
    """Define a custom button for a vehicle."""

    def __init__(self, vehicle, client):
        """Initialize the button."""
        self._vehicle = vehicle
        self._client = client
        self._attr_name = f"{vehicle['vin']} Update Data Button"
        self._attr_unique_id = f"{vehicle['vin']}_update_data_button"

    async def async_press(self):
        """Handle button press."""
        _LOGGER.info("Button pressed for vehicle: %s", self._vehicle["vin"])
        # Call some API action on press
        # await self._client.get_vehicle_instances(True)
        self.hass.bus.async_fire("connectedcars_refresh_data", {"vin": self._vehicle["vin"]})

