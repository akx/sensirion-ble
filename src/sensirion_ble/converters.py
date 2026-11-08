from __future__ import annotations

import struct
from typing import Callable

from sensor_state_data import SensorDeviceClass, Units

from sensirion_ble.types import ConversionResult, Sensor

CO2_PPM = Sensor(SensorDeviceClass.CO2, Units.CONCENTRATION_PARTS_PER_MILLION)
RH_PERCENTAGE = Sensor(SensorDeviceClass.HUMIDITY, Units.PERCENTAGE)
TEMP_CELSIUS = Sensor(SensorDeviceClass.TEMPERATURE, Units.TEMP_CELSIUS)
HCHO_PPB = Sensor(SensorDeviceClass.FORMALDEHYDE, Units.CONCENTRATION_PARTS_PER_BILLION)
PM1 = Sensor(SensorDeviceClass.PM1, Units.CONCENTRATION_MICROGRAMS_PER_CUBIC_METER)
PM25 = Sensor(SensorDeviceClass.PM25, Units.CONCENTRATION_MICROGRAMS_PER_CUBIC_METER)
PM4 = Sensor(SensorDeviceClass.PM4, Units.CONCENTRATION_MICROGRAMS_PER_CUBIC_METER)
PM10 = Sensor(SensorDeviceClass.PM10, Units.CONCENTRATION_MICROGRAMS_PER_CUBIC_METER)
# The VOC and NOx indices are unitless and have no device class of their own.
VOC_INDEX = Sensor(None, None, key="voc_index", name="VOC index")
NOX_INDEX = Sensor(None, None, key="nox_index", name="NOx index")

Converter = Callable[[bytes], "ConversionResult | None"]
Scale = Callable[[int], float]

FULL_SCALE = 2**16 - 1


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


# Scaling of the uint16 fields, as given in the live data section of
# https://sensirion.github.io/ble-services/


def _temperature(ticks: int) -> float:
    return round(-45 + (175.0 * ticks) / FULL_SCALE, 1)


def _humidity(ticks: int) -> float:
    return round((100.0 * ticks) / FULL_SCALE, 1)


def _as_is(ticks: int) -> float:
    return ticks


def _tenths(ticks: int) -> float:
    return round(ticks / 10, 1)


def _fifths(ticks: int) -> float:
    return round(ticks / 5, 1)


def _pm25_full_scale(ticks: int) -> float:
    # Sample types 12, 16 and 20 spread 0..1000 µg/m³ over the uint16 range;
    # the later ones send tenths of µg/m³.
    return round((1000.0 * ticks) / FULL_SCALE, 1)


T = (TEMP_CELSIUS, _temperature)
RH = (RH_PERCENTAGE, _humidity)
CO2 = (CO2_PPM, _as_is)
VOC = (VOC_INDEX, _as_is)
NOX = (NOX_INDEX, _as_is)
HCHO = (HCHO_PPB, _fifths)
PM25_TENTHS = (PM25, _tenths)
PM25_FULL_SCALE = (PM25, _pm25_full_scale)

# Sample type -> consecutive uint16 fields, starting at byte 4.
# These are the samples a gadget built with Sensirion's arduino-ble-gadget
# library can advertise. Only type 20 has been tested with real hardware.
# Types 38 (air velocity) and 40 (H2, pressure) are left out: the
# specification gives no unit for them.
SAMPLE_FIELDS: dict[int, tuple[tuple[Sensor, Scale], ...]] = {
    10: (T, RH, CO2),
    12: (T, RH, CO2, PM25_FULL_SCALE),
    14: (T, RH, HCHO),
    16: (T, RH, VOC, PM25_FULL_SCALE),
    20: (T, RH, CO2, VOC, PM25_FULL_SCALE, HCHO),
    22: (T, RH, VOC, NOX),
    24: (T, RH, VOC, NOX, PM25_TENTHS),
    26: (T, RH, CO2, VOC, NOX, PM25_TENTHS),
    28: (T, RH, CO2, PM25_TENTHS),
    30: (T, RH, VOC, PM25_TENTHS),
    32: (T, RH, CO2, VOC, PM25_TENTHS, HCHO),
    34: ((PM1, _tenths), PM25_TENTHS, (PM4, _tenths), (PM10, _tenths)),
    36: (CO2,),
    42: (T, RH, PM25_TENTHS),
    44: (T, RH, HCHO, VOC, NOX, PM25_TENTHS),
}


def _make_converter(fields: tuple[tuple[Sensor, Scale], ...]) -> Converter:
    fmt = f"<{len(fields)}H"
    size = 4 + struct.calcsize(fmt)

    def convert(raw_data: bytes) -> ConversionResult | None:
        if len(raw_data) < size:
            return None
        ticks = struct.unpack_from(fmt, raw_data, 4)
        data = {sensor: scale(value) for (sensor, scale), value in zip(fields, ticks)}
        return ConversionResult(raw_data[2:4].hex().upper(), data)

    return convert


CONVERTERS: dict[bytes, Converter] = {
    b"\x00\x04": _convert_type_4,
    b"\x00\x06": _convert_type_6,
    b"\x00\x08": _convert_type_8,
    **{
        bytes([0, sample_type]): _make_converter(fields)
        for sample_type, fields in SAMPLE_FIELDS.items()
    },
}
