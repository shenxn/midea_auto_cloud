"""Exact-model selection, metadata and actual HA entity command contracts."""

import ast
import asyncio
import copy
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.const import Platform
from midea_auto_cloud.device_mapping.T0xAC import DEVICE_MAPPING
from midea_auto_cloud.device_mapping._verified_central import VERIFIED_CENTRAL_MODELS
from midea_auto_cloud.select import MideaSelectEntity
from midea_auto_cloud.switch import MideaSwitchEntity

# Execute the real selector function without running account setup imports.
source = (
    Path(__file__).resolve().parents[1]
    / "custom_components/midea_auto_cloud/__init__.py"
)
node = next(
    n
    for n in ast.parse(source.read_text()).body
    if isinstance(n, ast.FunctionDef) and n.name == "get_device_mapping"
)
ns = {"re": re, "MideaLogger": SimpleNamespace(warning=lambda *a: None)}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), ns)
select_mapping = ns["get_device_mapping"]


def entity(cls, key, config, attributes):
    obj = object.__new__(cls)
    obj._config = config
    obj._entity_key = key
    obj._condition = config.get("condition")
    obj._rationale = config.get("rationale", ["off", "on"])
    obj._include_current = []
    obj._is_central_ac = False
    obj._device = None
    obj.coordinator = SimpleNamespace(
        data=SimpleNamespace(attributes=attributes, available=True),
        async_set_attributes=AsyncMock(),
    )
    return obj


@pytest.mark.parametrize("model", VERIFIED_CENTRAL_MODELS)
def test_exact_mapping_precedes_generic_tuple(model):
    mapping = select_mapping(DEVICE_MAPPING, 0xAC, model, "", "central-air-conditioner")
    assert mapping is DEVICE_MAPPING[model]
    assert (
        mapping["entities"][Platform.CLIMATE]["thermostat"]["target_humidity"]
        == "dehumidity"
    )
    sensors = mapping["entities"][Platform.SENSOR]
    assert sensors["indoor_co2"]["unit_of_measurement"] == "ppm"
    assert sensors["indoor_pm25"]["unit_of_measurement"] == "µg/m³"
    assert "unit_of_measurement" not in sensors["indoor_tvoc"]
    assert "device_class" not in sensors["wind_speed_real"]


def test_shared_templates_are_not_modified():
    original = next(
        v for k, v in DEVICE_MAPPING.items() if isinstance(k, tuple) and "22397061" in k
    )
    assert "indoor_tvoc" not in original["entities"][Platform.SENSOR]
    assert "female_care" not in original["entities"].get(Platform.SELECT, {})
    assert DEVICE_MAPPING["22397061"] is not DEVICE_MAPPING["22397063"]


@pytest.mark.parametrize(
    "key,capability",
    [
        ("follow_body_sense", "has_follow_body_sense"),
        ("no_wind_sense", "has_no_wind_sense"),
        ("inner_purifier", "has_purifier"),
    ],
)
@pytest.mark.parametrize("turn_on", [False, True])
def test_real_switch_payload_and_capability_gate(key, capability, turn_on):
    cfg = DEVICE_MAPPING["22397061"]["entities"][Platform.SWITCH][key]
    attrs = {key: "off", capability: 1}
    obj = entity(MideaSwitchEntity, key, cfg, attrs)
    assert obj.available
    asyncio.run(obj.async_turn_on() if turn_on else obj.async_turn_off())
    expected = {"single_control": 1, key: "on" if turn_on else "off"}
    if key == "follow_body_sense":
        expected["follow_body_sense_enable"] = 1
    obj.coordinator.async_set_attributes.assert_awaited_once_with(expected)
    assert attrs[key] == "off"  # no fabricated state from sending a command
    attrs[capability] = 0
    assert not obj.available
    attrs.pop(capability)
    assert not obj.available


@pytest.mark.parametrize("enabled", [False, True])
def test_moisturizing_command_and_state_match(enabled):
    cfg = DEVICE_MAPPING["22397061"]["entities"][Platform.SELECT]["female_care"]
    obj = entity(
        MideaSelectEntity,
        "female_care",
        cfg,
        {"female_care": int(enabled), "has_female_care": 1},
    )
    obj._key_options = cfg["options"]
    obj._status_key = cfg["status_key"]
    obj._ignore_values = []
    obj._last_option = None
    option = "开启（26°C / 60%）" if enabled else "关闭"
    assert obj.current_option == option
    asyncio.run(obj.async_select_option(option))
    expected = {"female_care": int(enabled), "single_control": 1}
    if enabled:
        expected.update(
            temperature=26, small_temperature=0, dehumidity=60, airoptimization="off"
        )
    obj.coordinator.async_set_attributes.assert_awaited_once_with(expected)
