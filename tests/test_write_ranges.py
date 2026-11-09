"""Settings refuse values outside their range in the VALIDATE phase.

A refused write stores nothing: the attribute keeps its value, also after a
restart.
"""

import pytest

from client import StubProc
from conftest import Device
from zcl_consts import (
    ZCL_ATTR_COVER_SWITCH_BINDED_MODE,
    ZCL_ATTR_COVER_SWITCH_COVER_INDEX,
    ZCL_ATTR_COVER_SWITCH_LOCAL_MODE,
    ZCL_ATTR_COVER_SWITCH_LONG_PRESS_DURATION,
    ZCL_ATTR_COVER_SWITCH_REVERSAL,
    ZCL_ATTR_COVER_SWITCH_SWITCH_TYPE,
    ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_ACTIONS,
    ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_BINDING_MODE,
    ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_LEVEL_MOVE_RATE,
    ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_LONG_PRESS_DUR,
    ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_MODE,
    ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_RELAY_MODE,
    ZCL_ATTR_ONOFF_INDICATOR_MODE,
    ZCL_ATTR_ONOFF_INDICATOR_STATE,
    ZCL_ATTR_START_UP_ONOFF,
    ZCL_CLUSTER_COVER_SWITCH_CONFIG,
    ZCL_CLUSTER_ON_OFF,
    ZCL_CLUSTER_ON_OFF_SWITCH_CONFIG,
)

# Endpoints: 1 switch, 2 relay (with indicator LED), 3 cover switch, 4 cover.
CONFIG = "Range;Test;SA0u;RB0;IB1;XC0C1u;CD0D1;"
SWITCH_EP = 1
RELAY_EP = 2
COVER_SWITCH_EP = 3

SW = (SWITCH_EP, ZCL_CLUSTER_ON_OFF_SWITCH_CONFIG)
RELAY = (RELAY_EP, ZCL_CLUSTER_ON_OFF)
COVER_SW = (COVER_SWITCH_EP, ZCL_CLUSTER_COVER_SWITCH_CONFIG)

# (endpoint, cluster, attribute, accepted value, refused value)
RANGES = [
    (*SW, ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_MODE, 2, 3),
    (*SW, ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_ACTIONS, 4, 5),
    (*SW, ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_RELAY_MODE, 4, 5),
    (*SW, ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_BINDING_MODE, 1, 0),
    (*SW, ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_BINDING_MODE, 2, 4),
    (*SW, ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_LONG_PRESS_DUR, 5000, 5001),
    (*SW, ZCL_ATTR_ONOFF_CONFIGURATION_SWITCH_LEVEL_MOVE_RATE, 1, 0),
    (*RELAY, ZCL_ATTR_START_UP_ONOFF, 2, 3),
    (*RELAY, ZCL_ATTR_START_UP_ONOFF, 0xFF, 0xFE),
    (*RELAY, ZCL_ATTR_ONOFF_INDICATOR_MODE, 2, 3),
    (*RELAY, ZCL_ATTR_ONOFF_INDICATOR_STATE, 0, 2),
    (*COVER_SW, ZCL_ATTR_COVER_SWITCH_SWITCH_TYPE, 0, 2),
    (*COVER_SW, ZCL_ATTR_COVER_SWITCH_COVER_INDEX, 0, 2),
    (*COVER_SW, ZCL_ATTR_COVER_SWITCH_REVERSAL, 1, 2),
    (*COVER_SW, ZCL_ATTR_COVER_SWITCH_LOCAL_MODE, 0, 4),
    (*COVER_SW, ZCL_ATTR_COVER_SWITCH_BINDED_MODE, 0, 4),
    (*COVER_SW, ZCL_ATTR_COVER_SWITCH_LONG_PRESS_DURATION, 5000, 5001),
]


def _write(proc: StubProc, ep: int, cluster: int, attr: int, value: int):
    return proc.exec(f"zcl_write {ep} 0x{cluster:04X} 0x{attr:04X} {value}")


@pytest.mark.parametrize(
    "ep,cluster,attr,accepted,refused",
    RANGES,
    ids=[f"ep{ep}-0x{cluster:04X}-0x{attr:04X}-{refused}"
         for ep, cluster, attr, _, refused in RANGES],
)
def test_out_of_range_write_is_refused_and_stores_nothing(
    ep: int, cluster: int, attr: int, accepted: int, refused: int
) -> None:
    with StubProc(device_config=CONFIG) as proc:
        device = Device(proc)
        assert _write(proc, ep, cluster, attr, accepted).ok
        assert device.read_zigbee_attr(ep, cluster, attr) == str(accepted)
        assert not _write(proc, ep, cluster, attr, refused).ok
        assert device.read_zigbee_attr(ep, cluster, attr) == str(accepted)

    with StubProc(device_config=CONFIG) as proc:
        assert Device(proc).read_zigbee_attr(ep, cluster, attr) == str(accepted)


def test_cover_index_is_limited_to_the_covers_of_the_device() -> None:
    with StubProc(device_config="Range;Test;XC0C1u;") as proc:
        device = Device(proc)
        assert not _write(proc, 1, ZCL_CLUSTER_COVER_SWITCH_CONFIG,
                          ZCL_ATTR_COVER_SWITCH_COVER_INDEX, 1).ok
        assert _write(proc, 1, ZCL_CLUSTER_COVER_SWITCH_CONFIG,
                      ZCL_ATTR_COVER_SWITCH_COVER_INDEX, 0).ok
        assert device.read_zigbee_attr(1, ZCL_CLUSTER_COVER_SWITCH_CONFIG,
                                       ZCL_ATTR_COVER_SWITCH_COVER_INDEX) == "0"
