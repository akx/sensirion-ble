from __future__ import annotations

from typing import NamedTuple

from sensor_state_data import SensorDeviceClass, Units


class Sensor(NamedTuple):
    device_class: SensorDeviceClass | None
    unit: Units | None
    # Key and name of the sensor; they default to those of the device class.
    # Needed for values without a device class, such as the VOC and NOx indices.
    key: str | None = None
    name: str | None = None


class ConversionResult(NamedTuple):
    identifier: str
    data: dict[Sensor, float]
