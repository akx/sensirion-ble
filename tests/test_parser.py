from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import DeviceClass, DeviceKey

from sensirion_ble import SensirionBluetoothDeviceData
from sensirion_ble.const import COMPANY_IDENTIFIER

SENSOR_DATA_1 = b"\x00\x08\x84\xe3>_3G\xd4\x02"
SENSOR_DATA_2 = b"\x00\x08\x84\xe3N_\rG\xd4\x02"

KEY_CO2 = DeviceKey(key=DeviceClass.CO2, device_id=None)
KEY_TEMPERATURE = DeviceKey(key=DeviceClass.TEMPERATURE, device_id=None)
KEY_HUMIDITY = DeviceKey(key=DeviceClass.HUMIDITY, device_id=None)


def bytes_to_service_info(payload: bytes) -> BluetoothServiceInfo:
    return BluetoothServiceInfo(
        name="MyCO2",
        address="00:00:00:00:00:00",
        rssi=-60,
        manufacturer_data={COMPANY_IDENTIFIER: payload},
        service_data={},
        service_uuids=[],
        source="",
    )


def test_parsing():
    device = SensirionBluetoothDeviceData()
    advertisement = bytes_to_service_info(SENSOR_DATA_1)
    assert device.supported(advertisement)
    up = device.update(advertisement)
    expected_name = "MyCO2 84E3"
    assert up.devices[None].name == expected_name  # Parsed from advertisement
    assert up.entity_values[KEY_CO2].native_value == 724  # ppm
    assert up.entity_values[KEY_TEMPERATURE].native_value == 20.1  # °C
    assert up.entity_values[KEY_HUMIDITY].native_value == 27.8  # %
