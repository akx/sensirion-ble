from __future__ import annotations

import struct

from sensor_state_data import SensorDeviceClass, Units

from sensirion_ble.types import ConversionResult

CO2_PPM = (SensorDeviceClass.CO2, Units.CONCENTRATION_PARTS_PER_MILLION)
RH_PERCENTAGE = (SensorDeviceClass.HUMIDITY, Units.PERCENTAGE)
TEMP_CELSIUS = (SensorDeviceClass.TEMPERATURE, Units.TEMP_CELSIUS)


def _convert_type_4(raw_data: bytes) -> ConversionResult:
    # SHT3x gadgets. UNTESTED.
    temp_ticks, humidity_ticks = struct.unpack("<HH", raw_data[4:8])
    # Conversion:
    # T = - 45 + ((175.0 * ticks) / (2^16 - 1))
    # RH = (100.0 * ticks) / (2^16 - 1)
    temp = -45 + ((175.0 * temp_ticks) / (2**16 - 1))
    humidity = (100.0 * humidity_ticks) / (2**16 - 1)
    data = {
        TEMP_CELSIUS: round(temp, 1),
        RH_PERCENTAGE: round(humidity, 1),
    }
    return ConversionResult(raw_data[2:4].hex().upper(), data)


def _convert_type_6(raw_data: bytes) -> ConversionResult:
    # SHT4x gadgets.
    temp_ticks, humidity_ticks = struct.unpack("<HH", raw_data[4:8])
    # Conversion:
    # T = - 45 + ((175.0 * ticks) / (2^16 - 1))
    # RH = -6 + (125.0 * ticks) / (2^16 - 1)
    temp = -45 + ((175.0 * temp_ticks) / (2**16 - 1))
    humidity = -6 + (125.0 * humidity_ticks) / (2**16 - 1)
    data = {
        TEMP_CELSIUS: round(temp, 2),
        RH_PERCENTAGE: round(humidity, 2),
    }
    return ConversionResult(raw_data[2:4].hex().upper(), data)


def _convert_type_8(raw_data: bytes) -> ConversionResult:
    # Sensirion MyCO2.
    temp_ticks, humidity_ticks, co2 = struct.unpack("<HHH", raw_data[4:10])
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
        TEMP_CELSIUS: round(temp, 1),
        RH_PERCENTAGE: round(humidity, 1),
        CO2_PPM: co2,
    }
    return ConversionResult(raw_data[2:4].hex().upper(), data)

# Add parcer for Advanced CO2 Gadget
def _convert_type_a(raw_data: bytes) -> ConversionResult:
    # Check for CO2 Gadget pattern: 00 0A 00 51
    if len(raw_data) < 10 or raw_data[0:4] != b'\x00\x0a\x00\x51':
        return None  # Not our format
        
    # Parse all values (little-endian)
    temp_raw = int.from_bytes(raw_data[4:6], 'little')
    hum_raw = int.from_bytes(raw_data[6:8], 'little')
    co2_raw = int.from_bytes(raw_data[8:10], 'little')
    
    # Convert to physical values
    temperature = round((temp_raw * 175.0 / 65535) - 45.0, 1)
    humidity = round(hum_raw * 100.0 / 65535)
    co2 = co2_raw
    
    data = {
        # The datasheet for the SCD4x sensor states that the accuracy
        # of the temperature sensor is ±0.8°C, so one digit after the
        # decimal point should be enough.
        TEMP_CELSIUS: temperature,
        RH_PERCENTAGE: humidity,
        CO2_PPM: co2,
    }
    return ConversionResult(raw_data[2:4].hex().upper(), data)

CONVERTERS = {
    b"\x00\x04": _convert_type_4,
    b"\x00\x06": _convert_type_6,
    b"\x00\x08": _convert_type_8,
    b"\x00\x0a": _convert_type_a,
}
