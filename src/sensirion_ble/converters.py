from __future__ import annotations

import struct

from sensor_state_data import SensorDeviceClass, Units

from sensirion_ble.types import ConversionResult


def _convert_type_8(raw_data: bytes) -> ConversionResult:
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
        (SensorDeviceClass.TEMPERATURE, Units.TEMP_CELSIUS): round(temp, 1),
        (SensorDeviceClass.HUMIDITY, Units.PERCENTAGE): round(humidity, 1),
        (SensorDeviceClass.CO2, Units.CONCENTRATION_PARTS_PER_MILLION): co2,
    }
    return ConversionResult(raw_data[2:4].hex().upper(), data)


CONVERTERS = {
    b"\x00\x08": _convert_type_8,
}
