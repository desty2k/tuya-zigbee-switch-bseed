import pytest

from tests.client import StubProc
from tests.conftest import Device
from tests.management_protocol_consts import (
    ZCL_ATTR_DEVICE_CONFIG_STATUS_LED_MODE,
    ZCL_CLUSTER_DEVICE_CONFIG,
)

HAL_ZIGBEE_NETWORK_NOT_JOINED = 0
HAL_ZIGBEE_NETWORK_JOINED = 1

LED_MODE_NETWORK = 0
LED_MODE_OFF = 1
LED_MODE_ON = 2

DEVICE_CONFIG = "A;B;SA0u;LB1;RB2;"
STATUS_LED = "B1"


def set_led_mode(device: Device, mode: int) -> None:
    device.write_zigbee_attr(1, ZCL_CLUSTER_DEVICE_CONFIG,
                             ZCL_ATTR_DEVICE_CONFIG_STATUS_LED_MODE, mode)


def led_levels(device: Device, samples: int = 4) -> list[bool]:
    levels = []
    for _ in range(samples):
        levels.append(device.get_gpio(STATUS_LED, refresh=True))
        device.step_time(500)
    return levels


def assert_blinking(device: Device) -> None:
    levels = led_levels(device)
    assert all(a != b for a, b in zip(levels, levels[1:])), levels


@pytest.mark.parametrize(
    "mode,lit",
    [(LED_MODE_NETWORK, True), (LED_MODE_OFF, False), (LED_MODE_ON, True)],
    ids=["network", "off", "on"],
)
def test_status_led_while_joined(mode: int, lit: bool) -> None:
    with StubProc(device_config=DEVICE_CONFIG) as proc:
        device = Device(proc)
        set_led_mode(device, mode)

        assert led_levels(device) == [lit] * 4


@pytest.mark.parametrize("mode", [LED_MODE_NETWORK, LED_MODE_OFF],
                         ids=["network", "off"])
def test_status_led_blinks_while_not_joined(mode: int) -> None:
    with StubProc(device_config=DEVICE_CONFIG) as proc:
        device = Device(proc)
        set_led_mode(device, mode)
        device.set_network(HAL_ZIGBEE_NETWORK_NOT_JOINED)

        assert_blinking(device)


def test_status_led_mode_on_stays_lit_while_not_joined() -> None:
    with StubProc(device_config=DEVICE_CONFIG) as proc:
        device = Device(proc)
        set_led_mode(device, LED_MODE_ON)
        device.set_network(HAL_ZIGBEE_NETWORK_NOT_JOINED)

        assert led_levels(device) == [True] * 4


def test_status_led_mode_on_survives_restart_while_not_joined() -> None:
    with StubProc(device_config=DEVICE_CONFIG) as proc:
        set_led_mode(Device(proc), LED_MODE_ON)
    with StubProc(joined=False) as proc:
        assert led_levels(Device(proc)) == [True] * 4


def test_status_led_mode_change_applies_while_not_joined() -> None:
    with StubProc(device_config=DEVICE_CONFIG, joined=False) as proc:
        device = Device(proc)
        assert_blinking(device)

        set_led_mode(device, LED_MODE_ON)
        assert led_levels(device) == [True] * 4

        set_led_mode(device, LED_MODE_OFF)
        assert_blinking(device)

        set_led_mode(device, LED_MODE_ON)
        set_led_mode(device, LED_MODE_NETWORK)
        assert_blinking(device)


def test_status_led_mode_change_applies_while_joined() -> None:
    with StubProc(device_config=DEVICE_CONFIG) as proc:
        device = Device(proc)

        set_led_mode(device, LED_MODE_OFF)
        assert led_levels(device) == [False] * 4
        set_led_mode(device, LED_MODE_ON)
        assert led_levels(device) == [True] * 4
        set_led_mode(device, LED_MODE_OFF)
        set_led_mode(device, LED_MODE_NETWORK)
        assert led_levels(device) == [True] * 4


def test_relay_indicators_blink_while_not_joined_without_status_led() -> None:
    with StubProc(device_config="A;B;SA0u;RB2;IA1;", joined=False) as proc:
        device = Device(proc)
        levels = []
        for _ in range(4):
            levels.append(device.get_gpio("A1", refresh=True))
            device.step_time(500)

        assert all(a != b for a, b in zip(levels, levels[1:])), levels
