# sensirion-ble

Parser for Sensirion BLE devices.

## Supported devices

* [MyCO2 (aka SCD4x CO2 Gadget)](https://sensirion.com/products/catalog/SCD4x-CO2-Gadget/)
* [SHT43 DemoBoard](https://sensirion.com/products/catalog/SHT43-DemoBoard)

## Untested devices

* SHT3x based gadgets

## DIY gadgets

Gadgets built with Sensirion's [arduino-ble-gadget](https://github.com/Sensirion/arduino-ble-gadget)
library advertise one of the live data samples of the [Sensirion BLE services specification][sbs].
Sample types 10, 12, 14, 16, 20, 22, 24, 26, 28, 30, 32, 34, 36, 42 and 44 are decoded
(temperature, humidity, CO2, VOC index, NOx index, PM and formaldehyde).
Only type 20 has been tested with real hardware.

Other devices could be supported at a later time, but I don't have any at hand.

## Reference

The parser is based on the [Sensirion Bluetooth Low Energy (BLE) Specification][sble] (also available in the `reference` folder).

[sble]: https://github.com/Sensirion/arduino-ble-gadget/blob/master/documents/Sensirion_BLE_communication_protocol.pdf
[sbs]: https://sensirion.github.io/ble-services/#/live-data
