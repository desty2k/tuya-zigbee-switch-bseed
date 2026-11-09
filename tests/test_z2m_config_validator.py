"""The Zigbee2MQTT converter's config string check accepts what the firmware parser accepts."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")

# Loads validateDeviceConfig from the rendered converter without its
# zigbee-herdsman-converters imports, then checks each [config, maxPinIndex]
# case read from stdin and prints the error message or null per case.
HARNESS = r"""
const fs = require("fs");
const source = fs.readFileSync(process.argv[1], "utf8");
const start = source.indexOf("const validateDeviceConfig = ");
const end = source.indexOf("\n};\n", start);
const assertString = (value) => { if (typeof value !== "string") throw new Error("not a string"); };
const validateDeviceConfig = eval(source.slice(start, end + 2).replace("const validateDeviceConfig = ", "(") + ")");
const cases = JSON.parse(fs.readFileSync(0, "utf8"));
console.log(JSON.stringify(cases.map(([value, maxPinIndex]) => {
    try { validateDeviceConfig(value, maxPinIndex); return null; } catch (error) { return error.message; }
})));
"""

TELINK = 7
SILABS = 15


@pytest.fixture(scope="module")
def converter(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("z2m") / "switch_custom.js"
    rendered = subprocess.run(
        [sys.executable, "helper_scripts/make_z2m_custom_converters.py", "device_db.yaml"],
        cwd=ROOT, check=True, capture_output=True, text=True).stdout
    path.write_text(rendered)
    return path


def check(converter: Path, cases: list) -> list:
    result = subprocess.run(["node", "-e", HARNESS, str(converter)], input=json.dumps(cases),
                            check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_every_board_config_string_is_accepted(converter: Path) -> None:
    db = yaml.safe_load((ROOT / "device_db.yaml").read_text())
    boards = [(name, board["config_str"], SILABS if board.get("mcu_family") == "Silabs" else TELINK)
              for name, board in db.items() if board.get("build", True)]
    errors = check(converter, [[config, pins] for _, config, pins in boards])
    rejected = {name: error for (name, _, _), error in zip(boards, errors) if error}
    assert not rejected
    assert len(boards) > 100


VALID = [
    "Mf;Model;",
    ";;",
    "Mf;Model;SA0",
    "Mf;Model;SA0u;SB1U;SC2d;SD3f;BA7u;RB4;RC2C3;LD2i;ID3;PA1i;BTB5;M;SLP",
    "Mf;Model;SA0u;RB4",  # no ; after the last entry
    "Mf;Model;D1;D200;G100;G2000;i0;i65535;D007",
    "Mf;Model;K3;K03:500;KfFfF:0;K0:65535;XA0A1u;XA0A1A2;CB1B2;EBC0C1C2i;EBC0C1C2",
    "Mf;Model;SA07u",  # leading zero in the pin index
    "Mf;Model;LP10;LP500;LP50;RA0A1;LC2",
]

INVALID = [
    "Mf;Model",
    "Mf",
    "",
    "Mf;Model;;",
    "Mf;Model;;SA0u;",
    "M" * 32 + ";Model;",
    "Mf;" + "M" * 32 + ";",
    "Mf;Model;SA0" + "u" * 29 + ";",
    "Mf;Model;" + "RA0;" * 40,
    "Mf;Model;D0;",
    "Mf;Model;D201;",
    "Mf;Model;D;",
    "Mf;Model;G99;",
    "Mf;Model;G2001;",
    "Mf;Model;i65536;",
    "Mf;Model;ix;",
    "Mf;Model;K;",
    "Mf;Model;K12345;",
    "Mf;Model;K3:;",
    "Mf;Model;K3:65536;",
    "Mf;Model;K3-5;",
    "Mf;Model;SA8u;",
    "Mf;Model;SE0u;",
    "Mf;Model;Sa0u;",
    "Mf;Model;SA100u;",
    "Mf;Model;SA0x;",
    "Mf;Model;SA0uu;",
    "Mf;Model;BT;",
    "Mf;Model;BTA0u;",
    "Mf;Model;RA0A1A2;",
    "Mf;Model;RA0x;",
    "Mf;Model;LA0x;",
    "Mf;Model;PA0ii;",
    "Mf;Model;XA0u;",
    "Mf;Model;XA0A1E5u;",
    "Mf;Model;CA0;",
    "Mf;Model;CA0A1u;",
    "Mf;Model;EA0A1A2;",
    "Mf;Model;EBA0A1;",
    "Mf;Model;EBA0A1A2x;",
    "Mf;Model;Mx;",
    "Mf;Model;SLPX;",
    "Mf;Model;LP9;",
    "Mf;Model;LP501;",
    "Mf;Model;LP;",
    "Mf;Model;LP5x;",
    "Mf;Model;Z1;",
]


def test_parser_syntax_and_ranges(converter: Path) -> None:
    assert check(converter, [[value, TELINK] for value in VALID]) == [None] * len(VALID)
    errors = check(converter, [[value, TELINK] for value in INVALID])
    accepted = [value for value, error in zip(INVALID, errors) if error is None]
    assert not accepted


def test_pin_range_follows_the_mcu(converter: Path) -> None:
    cases = ["Mf;Model;SA8u;", "Mf;Model;SD15u;", "Mf;Model;SA16u;"]
    assert check(converter, [[value, SILABS] for value in cases])[:2] == [None, None]
    assert all(check(converter, [[value, TELINK] for value in cases]))
    assert check(converter, [[cases[2], SILABS]])[0]
