from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import Entity

class CustomButton(ButtonEntity):
    def __init__(self, name: str):
        self._attr_name = name

    def press(self):
        """Handle button press."""
        print(f"Button {self._attr_name} was pressed!")

def setup_platform(hass, config, add_entities, discovery_info=None):
    add_entities([CustomButton("My Button")])
