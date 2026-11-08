import struct

from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import DeviceClass, DeviceKey

from sensirion_ble import SensirionBluetoothDeviceData
from sensirion_ble.const import COMPANY_IDENTIFIER
from sensirion_ble.converters import SAMPLE_FIELDS

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


# Captured from a DIY gadget (ESP32 with SCD30, SFA30 and SEN54) running
# Sensirion's arduino-ble-gadget with DataType::T_RH_CO2_VOC_PM25_HCHO.
SENSOR_DATA_TYPE_20 = bytes.fromhex("00149bc27b64e3755a02100054030e00")


def test_parsing_type_20():
    device = SensirionBluetoothDeviceData()
    advertisement = bytes_to_service_info(SENSOR_DATA_TYPE_20)
    assert device.supported(advertisement)
    up = device.update(advertisement)
    assert up.devices[None].name == "MyCO2 9BC2"
    values = {key.key: value.native_value for key, value in up.entity_values.items()}
    assert values[DeviceClass.TEMPERATURE] == 23.7  # °C
    assert values[DeviceClass.HUMIDITY] == 46.1  # %
    assert values[DeviceClass.CO2] == 602  # ppm
    assert values["voc_index"] == 16
    assert values[DeviceClass.PM25] == 13.0  # µg/m³
    assert values[DeviceClass.FORMALDEHYDE] == 2.8  # ppb
    voc = up.entity_values[DeviceKey(key="voc_index", device_id=None)]
    assert voc.name == "VOC index"


def test_sample_fields():
    for sample_type, fields in sorted(SAMPLE_FIELDS.items()):
        payload = bytes([0, sample_type, 0xAB, 0xCD]) + struct.pack(
            f"<{len(fields)}H", *range(1000, 1000 + len(fields))
        )
        device = SensirionBluetoothDeviceData()
        up = device.update(bytes_to_service_info(payload))
        assert up.devices[None].name == "MyCO2 ABCD", sample_type
        keys = {key.key for key in up.entity_values} - {"signal_strength"}
        expected = {sensor.key or sensor.device_class for sensor, _ in fields}
        assert keys == expected, sample_type
        # a truncated sample is ignored
        assert not SensirionBluetoothDeviceData().supported(
            bytes_to_service_info(payload[:-1])
        ), sample_type


def test_pm_sample():
    payload = bytes.fromhex("0022abcd") + struct.pack("<HHHH", 28, 32, 33, 34)
    up = SensirionBluetoothDeviceData().update(bytes_to_service_info(payload))
    values = {key.key: value.native_value for key, value in up.entity_values.items()}
    assert values[DeviceClass.PM1] == 2.8
    assert values[DeviceClass.PM25] == 3.2
    assert values[DeviceClass.PM4] == 3.3
    assert values[DeviceClass.PM10] == 3.4


def test_unsupported_sample_type():
    device = SensirionBluetoothDeviceData()
    assert not device.supported(bytes_to_service_info(bytes.fromhex("0026abcd1234")))
