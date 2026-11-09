# Custom firmware for Tuya Zigbee switches (BSEED fork)

[![Firmware](https://img.shields.io/github/v/tag/desty2k/tuya-zigbee-switch-bseed?include_prereleases&sort=semver&label=firmware&color=blue)](https://github.com/desty2k/tuya-zigbee-switch-bseed/tags)
[![Tests](https://img.shields.io/github/actions/workflow/status/desty2k/tuya-zigbee-switch-bseed/test.yml?branch=main&label=tests)](https://github.com/desty2k/tuya-zigbee-switch-bseed/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Boards](https://img.shields.io/badge/boards-204-informational)](./docs/supported_devices.md)

[![Telink TLSR8258/8253](https://img.shields.io/badge/Telink-TLSR8258%20%7C%20TLSR8253-6f42c1)](./docs/flashing/telink.md)
[![Silabs EFR32MG21/MG22](https://img.shields.io/badge/Silabs-EFR32MG21%20%7C%20MG22-d91e2a)](./docs/flashing/silabs.md)
[![Zigbee2MQTT](https://img.shields.io/badge/Zigbee2MQTT-converter-ffc135)](./docs/updating.md#integration-files)
[![ZHA](https://img.shields.io/badge/ZHA-quirk-41bdf5)](./docs/updating.md#integration-files)
[![HOMEd](https://img.shields.io/badge/HOMEd-extension-0a7bbb)](./docs/updating.md#integration-files)
[![OTA](https://img.shields.io/badge/OTA-from%20stock%20firmware-brightgreen)](./docs/updating.md)

Open firmware for Tuya-style Zigbee wall switches, relay modules, outlets,
shutter switches and battery remotes on Telink (TLSR8258/TLSR8253) and Silabs
(EFR32MG21/MG22) chips. It replaces the vendor firmware, fixes its bugs (two
buttons pressed together toggling one relay) and turns a wall switch into a
configurable Zigbee remote.

> [!IMPORTANT]
> This repository, [desty2k/tuya-zigbee-switch-bseed](https://github.com/desty2k/tuya-zigbee-switch-bseed),
> is a separate project built on [romasku/tuya-zigbee-switch](https://github.com/romasku/tuya-zigbee-switch).
> - Moving a device from upstream firmware (or 1.x) to this fork's 2.x resets
>   its settings. Network membership, binds and groups survive.
> - Settings survive OTA updates between fork 2.x releases.
> - The fork's Zigbee2MQTT converter, ZHA quirk and HOMEd extension match fork
>   firmware only. Update them together with the firmware and never mix them
>   with upstream converters.

## Features

- **Relay control from the buttons**, with the moment of switching per button:
  on press, on release, on long press, or after a resolved single click
  (`deferred_single`, which leaves double clicks for automations).
- **Detached mode**: a button that only sends commands and events.
- **Button events**: press, release, hold, hold release and 1–10 clicks per
  button, with configurable multi-click gap and debounce.
- **Direct binding** to lights, relays and covers: On/Off commands, and
  dimming of bound lights while a button is held.
- **Switch types**: rocker, push button (normally open or closed), with five
  action modes that keep relays and bound devices in step.
- **Child lock** of the local buttons, toggled from Zigbee or by a hold gesture
  on the device.
- **Relay interlock** (`K` config token, plus a per-relay interlock group) with
  dead time, and **inching** (automatic switch-off after a set time).
- **Power-on behaviour** per relay: off, on, toggle, previous.
- **Relay indicator LEDs**: same as the relay, opposite, or manual.
- **Covers** (shutters, blinds): position tracking from travel times,
  calibration with deadzones and overrun, go to position, stop button.
- **Power metering** with the BL0937 chip (Telink): voltage, current, power,
  energy, with calibration.
- **Battery remotes** with battery reporting.
- **Router and end-device images** for no-neutral switches.
- **Diagnostics**: counters for inputs, button events and the network.
- **Recovery graph**: a device with an unusable configuration stays reachable
  for a corrected configuration or an OTA update.
- **OTA updates** from Zigbee2MQTT and ZHA, including conversion of stock
  Telink devices.
- **Factory reset** by a configurable number of presses or the onboard button.

## Devices

Every board in [`device_db.yaml`](./device_db.yaml) is built and published as
a release candidate (2.0.0-rc.6), except the Sonoff ZBMINIL2, which has no 2.x
image yet ([known issues](./docs/known_issues.md#release-status)). Only these
boards are tested on hardware with 2.x firmware:

| Board | Device | Stock model |
| --- | --- | --- |
| `SWITCH_BSEED_TS0726_3GANG` | BSEED Echo Click / Scale 3-gang switch | TS0726 `_TZ3002_iedhxgyi` |
| `SWITCH_BSEED_TS0726_4GANG` | BSEED Echo Click / Scale 4-gang switch | TS0726 `_TZ3002_pzao9ls1` |
| `OUTLET_BSEED_TS011F_PM_DRZLXJNE` | BSEED outlet with power metering | TS011F `_TZ3210_drzlxjne` |
| `COVER_BSEED_TS130F_VSJ5O7DM` | BSEED shutter switch | TS130F `_TZ3000_vsj5o7dm` |

All other boards are published release candidates, untested on hardware in
2.x. The full generated list is
[docs/supported_devices.md](./docs/supported_devices.md).

## Quick start

1. Point Zigbee2MQTT at the fork's OTA index and install the fork's converter
   ([updating.md](./docs/updating.md)).
2. Check for an update on the device and install it; a stock Telink device is
   converted over the air.
3. Pair it again if it left the network, then set it up from its Zigbee2MQTT
   page ([configuration.md](./docs/usage/configuration.md)).

## Installation

- Over the air from Zigbee2MQTT or ZHA (Telink devices): [docs/updating.md](./docs/updating.md)
- By wire: [docs/flashing/](./docs/flashing/)
- A device not on the list: [docs/contribute/porting.md](./docs/contribute/porting.md)

## Documentation

Using the firmware:

- [updating.md](./docs/updating.md): OTA index, integration files, converting, updating, router or end device
- [usage/configuration.md](./docs/usage/configuration.md): every setting with its default and range, child lock, factory reset
- [usage/button_events.md](./docs/usage/button_events.md): clicks and holds in automations
- [usage/config_string.md](./docs/usage/config_string.md): the device config string and the recovery graph
- [usage/endpoints.md](./docs/usage/endpoints.md): endpoints, binding, groups, cluster reference
- [faq.md](./docs/faq.md): troubleshooting
- [known_issues.md](./docs/known_issues.md)
- [changelog_fw.md](./docs/changelog_fw.md)
- [flashing/](./docs/flashing/): wired flashing for Telink, Silabs and the Sonoff ZBMINIL2

Developing it:

- [contribute/architecture.md](./docs/contribute/architecture.md)
- [contribute/design_decisions.md](./docs/contribute/design_decisions.md)
- [contribute/open_work.md](./docs/contribute/open_work.md)
- [contribute/porting.md](./docs/contribute/porting.md)
- [contribute/](./docs/contribute/)

## Support

Report bugs and ask questions on the fork's
[issue tracker](https://github.com/desty2k/tuya-zigbee-switch-bseed/issues).

## Acknowledgements

- [romasku/tuya-zigbee-switch](https://github.com/romasku/tuya-zigbee-switch):
  the upstream project this fork is built on
- [doctor64/tuyaZigbee](https://github.com/doctor64/tuyaZigbee): firmware for
  other Tuya Zigbee devices
- [medium.com/@omaslyuchenko](https://medium.com/@omaslyuchenko): the *Hello
  Zigbee World* series of Zigbee programming guides
