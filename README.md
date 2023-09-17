
# Connectedcars.io (Min Volkswagen)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

The `Connectedcars.io (Min Volkswagen)` component is a Home Assistant custom component for showing car information for Danish Volkswagens equipped with the hardware to send data to the mobile app "Min Volkswagen". 
Min Skoda, Min Seat and Mit Audi all use the same backend and should work as well, although still not tested.

## Installation
---
### Manual Installation
  1. Copy  `connectedcars_io`  folder into your custom_components folder in your hass configuration directory.
  2. Restart Home Assistant.

### Installation with HACS (Home Assistant Community Store)
  1. Ensure that [HACS](https://hacs.xyz/) is installed.
  2. In HACS / Integrations / Kebab menu / Custom repositories, add the url the this repository.
  3. Search for and install the `Connectedcars.io (Min Volkswagen)` integration.
  4. Restart Home Assistant.


## Configuration

It is configurable through config flow, meaning it will popup a dialog after adding the integration.
  1. Head to Configuration --> Integrations
  2. Add new and search for `Connectedcars.io (Min Volkswagen)` 
  3. Enter credentials and namespace.

#### Currently known namespaces
 - minvolkswagen *(default)*
 - minskoda
 - minseat
 - mitaudi

#### Multiple cars
If you have multiple cars on the same account, they should all appear.  
If you have multiple cars of different brands, add the integration multiple times each with the suitable namespace.  
*So far only tested with a single car*

## State and attributes
A device is created for each car.
For each car the following sensors can be created, but only when data is present. Thus fuel based cars should have fuel level sensors, while EVs should have battery sensors. 

The naming scheme is `{brand} {model} <name>`.  
Sensor names:
* BatteryVoltage (12V battery)
* EVHVBattTemp (EV)
* EVchargePercentage (EV)
* fuelLevel
* fuelPercentage
* GeoLocation
* Health (severity threshold configurable)
  * Attribute: Leads array may help to explain the cause
* Ignition
* Lamp *+name* (one sensor per each reported lamp, disabled by default)
* NextServicePredicted (disabled by default)
* odometer
* outdoorTemperature
* Speed
* Fuel economy (disabled by default)
* Mileage latest year (disabled by default)
* Mileage latest month (disabled by default)
* Mileage since refuel (disabled by default)

All sensors may not be reported correctedly with all cars.
Among others fuelPercentage is one of those.

## Debugging
It is possible to debug log the raw response from the API. This is done by setting up logging like below in configuration.yaml in Home Assistant. It is also possible to set the log level through a service call in UI.  

```
logger: 
  default: info
  logs: 
    custom_components.connectedcars_io: debug
```

## Examples

Configuration  
![Config](https://github.com/jnxxx/homeassistant-connectedcars_io/raw/main/images/config.png)  
![Options](https://github.com/jnxxx/homeassistant-connectedcars_io/raw/main/images/options.png)

Device  
![Device](https://github.com/jnxxx/homeassistant-connectedcars_io/raw/main/images/device.png)

Dashboard  
![Dashboard](https://github.com/jnxxx/homeassistant-connectedcars_io/raw/main/images/dashboard.png)

Location state  
![Location state](https://github.com/jnxxx/homeassistant-connectedcars_io/raw/main/images/location_state.png)
