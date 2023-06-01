from __future__ import annotations

import logging

from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo

from .const import COMPANY_IDENTIFIER
from .converters import CONVERTERS
from .types import ConversionResult

_LOGGER = logging.getLogger(__name__)


def _convert_advertisement(raw_data: bytes) -> ConversionResult | None:
    """
    Convert a Sensirion advertisement to a device name and a dictionary of sensor values.
    """
    converter = CONVERTERS.get(raw_data[:2])
    if converter:
        return converter(raw_data)
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
