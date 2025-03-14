import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the refresh button."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    connectedcarsclient = config["connectedcarsclient"]
    
    async_add_entities([ConnectedCarsRefreshButton(connectedcarsclient)], True)

class ConnectedCarsRefreshButton(ButtonEntity):
    """Button entity to refresh ConnectedCars data."""

    def __init__(self, connectedcarsclient):
        """Initialize the refresh button."""
        self._connectedcarsclient = connectedcarsclient
        self._attr_name = "Refresh ConnectedCars Data"
        self._attr_unique_id = f"{DOMAIN}_refresh_button"

    async def async_press(self):
        """Handle button press to refresh data."""
        _LOGGER.info("Manually refreshing ConnectedCars data...")
        await self._connectedcarsclient.update_data()
