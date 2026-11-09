import pytest

from tests.client import StubProc
from tests.conftest import Device
from tests.management_protocol_consts import (
    ZCL_ATTR_DEVICE_CONFIG_STATUS_LED_MODE,
    ZCL_CLUSTER_DEVICE_CONFIG,
)

HAL_ZIGBEE_NETWORK_NOT_JOINED = 0
HAL_ZIGBEE_NETWORK_JOINED = 1
HAL_ZIGBEE_NETWORK_JOINING = 2

LED_MODE_NETWORK = 0
LED_MODE_OFF = 1
LED_MODE_ON = 2

RETRY_BASES_MS = [1000, 2000, 4000, 8000, 16000, 30000, 30000]
JOIN_BLINK_CYCLES = 7


def steering_times(device: Device) -> list[int]:
    return [int(event.payload["t"]) for event in device._events
            if event.kind == "zcl_start_network_steering"]


def fail_attempt(device: Device) -> int:
    """End the running steering attempt without a join; returns the time."""
    assert device.status()["joined"] == str(HAL_ZIGBEE_NETWORK_JOINING)
    device.set_network(HAL_ZIGBEE_NETWORK_NOT_JOINED)
    device.step_time(0)
    return device.millis()


def next_attempt_delay(device: Device, base_ms: int) -> int:
    failed_at = fail_attempt(device)
    count = len(steering_times(device))
    device.step_time(base_ms * 5 // 4 + 1)
    times = steering_times(device)
    assert len(times) == count + 1, times
    return times[-1] - failed_at


def assert_within_jitter(delay_ms: int, base_ms: int) -> None:
    assert base_ms * 3 // 4 <= delay_ms <= base_ms * 5 // 4, (delay_ms, base_ms)


@pytest.mark.parametrize("seed", [0, 1, 12345, 4000000000])
def test_steering_retries_back_off_with_jitter(seed: int) -> None:
    with StubProc(device_config="A;B;LB0;", joined=False) as proc:
        device = Device(proc)
        assert proc.exec(f"rand_seed {seed}").ok
        # The first attempt starts at boot, before machine events are on.
        assert device.counters()["steering_attempts"] == 1

        delays = [next_attempt_delay(device, base) for base in RETRY_BASES_MS]

        for delay, base in zip(delays, RETRY_BASES_MS):
            assert_within_jitter(delay, base)
        assert device.counters()["steering_attempts"] == len(RETRY_BASES_MS) + 1


def test_steering_does_not_retry_before_the_delay() -> None:
    with StubProc(device_config="A;B;LB0;", joined=False) as proc:
        device = Device(proc)
        fail_attempt(device)

        device.step_time(749)
        assert steering_times(device) == []
        assert device.status()["joined"] == str(HAL_ZIGBEE_NETWORK_NOT_JOINED)


def test_jitter_differs_between_seeds() -> None:
    delays = set()
    for seed in (1, 2, 3, 4):
        with StubProc(device_config="A;B;LB0;", joined=False) as proc:
            device = Device(proc)
            assert proc.exec(f"rand_seed {seed}").ok
            delays.add(next_attempt_delay(device, 1000))
    assert len(delays) > 1


def test_schedule_restarts_after_join_and_leave() -> None:
    with StubProc(device_config="A;B;LB0;", joined=False) as proc:
        device = Device(proc)
        for base in RETRY_BASES_MS[:3]:
            next_attempt_delay(device, base)

        device.set_network(HAL_ZIGBEE_NETWORK_JOINED)
        device.step_time(0)
        count = len(steering_times(device))

        device.set_network(HAL_ZIGBEE_NETWORK_NOT_JOINED)
        device.step_time(0)
        times = steering_times(device)
        assert len(times) == count + 1
        assert times[-1] == device.millis()

        assert_within_jitter(next_attempt_delay(device, 1000), 1000)
        assert_within_jitter(next_attempt_delay(device, 2000), 2000)


def test_schedule_restarts_after_factory_reset() -> None:
    with StubProc(device_config="A;B;BA0u;", joined=False) as proc:
        device = Device(proc)
        for base in RETRY_BASES_MS[:3]:
            next_attempt_delay(device, base)
        failed_at = fail_attempt(device)
        count = len(steering_times(device))

        device.press_button("A0")
        device.step_time(2500)

        times = steering_times(device)
        assert len(times) == count + 1
        assert times[-1] - failed_at < 8000 * 3 // 4
        assert_within_jitter(next_attempt_delay(device, 1000), 1000)


def set_led_mode(device: Device, mode: int) -> None:
    device.write_zigbee_attr(1, ZCL_CLUSTER_DEVICE_CONFIG,
                             ZCL_ATTR_DEVICE_CONFIG_STATUS_LED_MODE, mode)


def led_levels(device: Device, pin: str, samples: int) -> list[bool]:
    levels = []
    for _ in range(samples):
        levels.append(device.get_gpio(pin, refresh=True))
        device.step_time(500)
    return levels


@pytest.mark.parametrize(
    "mode,lit",
    [(LED_MODE_NETWORK, True), (LED_MODE_OFF, False), (LED_MODE_ON, True)],
    ids=["network", "off", "on"],
)
def test_join_by_steering_blinks_then_shows_mode(mode: int, lit: bool) -> None:
    with StubProc(device_config="A;B;LB0;") as proc:
        device = Device(proc)
        set_led_mode(device, mode)
        device.set_network(HAL_ZIGBEE_NETWORK_NOT_JOINED)
        device.step_time(0)
        assert device.status()["joined"] == str(HAL_ZIGBEE_NETWORK_JOINING)

        device.set_network(HAL_ZIGBEE_NETWORK_JOINED)
        device.step_time(0)

        blink = led_levels(device, "B0", 2 * JOIN_BLINK_CYCLES)
        assert blink == [True, False] * JOIN_BLINK_CYCLES
        assert led_levels(device, "B0", 4) == [lit] * 4


def test_join_by_steering_blinks_relay_indicators() -> None:
    with StubProc(device_config="A;B;SA0u;IA1;", joined=False) as proc:
        device = Device(proc)
        device.set_network(HAL_ZIGBEE_NETWORK_JOINED)
        device.step_time(0)

        blink = led_levels(device, "A1", 2 * JOIN_BLINK_CYCLES)
        assert blink == [True, False] * JOIN_BLINK_CYCLES
        assert led_levels(device, "A1", 4) == [False] * 4


def test_boot_already_joined_does_not_blink() -> None:
    with StubProc(device_config="A;B;LB0;") as proc:
        device = Device(proc)

        assert led_levels(device, "B0", 6) == [True] * 6
        assert steering_times(device) == []


def test_rejoin_without_steering_does_not_blink() -> None:
    with StubProc(device_config="A;B;LB0;") as proc:
        device = Device(proc)
        device.set_network(HAL_ZIGBEE_NETWORK_JOINING)
        device.step_time(0)
        device.set_network(HAL_ZIGBEE_NETWORK_JOINED)
        device.step_time(0)

        assert led_levels(device, "B0", 6) == [True] * 6
        assert steering_times(device) == []
