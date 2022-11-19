from __future__ import annotations

import logging
import struct

from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import DeviceClass, Units

from .const import COMPANY_IDENTIFIER

_LOGGER = logging.getLogger(__name__)


def _convert_advertisement(
    raw_data: bytes,
) -> tuple[str | None, dict[tuple[DeviceClass, Units], float]] | None:
    """
    Convert a Sensirion advertisement to a device name and a dictionary of sensor values.
    """
    if raw_data[:2] == b"\x00\x08":  # Sample type 8
        temp_ticks, humidity_ticks, co2 = struct.unpack("<hhh", raw_data[4:10])
        # Conversion:
        # T = - 45 + ((175.0 * ticks) / (2^16 - 1))
        # RH = (100.0 * ticks) / (2^16 - 1)
        # CO2 = transmitted value
        temp = -45 + ((175.0 * temp_ticks) / (2**16 - 1))
        humidity = (100.0 * humidity_ticks) / (2**16 - 1)
        data = {
            # The datasheet for the SCD4x sensor states that the accuracy
            # of the temperature sensor is ±0.8°C, so one digit after the
            # decimal point should be enough.
            (DeviceClass.TEMPERATURE, Units.TEMP_CELSIUS): round(temp, 1),
            (DeviceClass.HUMIDITY, Units.PERCENTAGE): round(humidity, 1),
            (DeviceClass.CO2, Units.CONCENTRATION_PARTS_PER_MILLION): co2,
        }
        return (raw_data[2:4].hex().upper(), data)
    _LOGGER.debug("Data format not supported: %s", raw_data)
    return None


class SensirionBluetoothDeviceData(BluetoothData):
    """Data for Sensirion BLE sensors."""

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        try:
            raw_data = service_info.manufacturer_data[COMPANY_IDENTIFIER]
        except (KeyError, IndexError):
            _LOGGER.debug("Manufacturer ID not found in data")
            return None

        result = _convert_advertisement(raw_data)
        if result is None:
            return
        identifier, data = result
        self.set_device_type(f"Sensirion {service_info.name}")
        self.set_device_manufacturer("Sensirion AG")
        identifier = identifier or short_address(service_info.address)
        self.set_device_name(f"{service_info.name} {identifier}")
        for (device_class, unit), value in data.items():
            self.update_sensor(
                key=device_class,
                device_class=device_class,
                native_unit_of_measurement=unit,
                native_value=value,
            )
