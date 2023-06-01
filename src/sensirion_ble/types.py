from __future__ import annotations

from typing import NamedTuple

from sensor_state_data import SensorDeviceClass, Units


class ConversionResult(NamedTuple):
    identifier: str
    data: dict[tuple[SensorDeviceClass, Units], float]
