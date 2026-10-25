"""Regressions from four live cloud models, without account access or actuation."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from midea_auto_cloud.device_mapping import T0xED, T0xE1, T0xB6, T0xE3
from midea_auto_cloud.sensor import MideaSensorEntity
from midea_auto_cloud.select import MideaSelectEntity
from midea_auto_cloud.switch import MideaSwitchEntity
from test_central_cloud import entity, select_mapping


@pytest.mark.parametrize('module,kind,model,category', [
    (T0xED, 0xED, '63200872', 'water_purifier'),
    (T0xE1, 0xE1, '7600002B', 'dishwasher'),
    (T0xB6, 0xB6, '730006AE', 'range-hood'),
    (T0xE3, 0xE3, '5111102Z', 'gas-water-heater'),
])
def test_exact_models_leave_generic_templates_intact(module, kind, model, category):
    c = select_mapping(module.DEVICE_MAPPING, kind, model, '', category)
    assert c is module.DEVICE_MAPPING[model]
    assert c is not module.DEVICE_MAPPING.get('default')
    assert T0xED.DEVICE_MAPPING['default_water_purifier']['centralized'] == ['custom_temperature_1']
    assert 'lamp_control1_power' in T0xE3.DEVICE_MAPPING['default']['entities']['switch']


def test_purifier_no_boiler_or_softener_controls_and_correct_filter_labels():
    c = T0xED.DEVICE_MAPPING['63200872']
    e = c['entities']
    assert not c['centralized']
    assert not {'heat', 'cool', 'regeneration', 'soften'} & set(e['switch'])
    assert 'number' not in e  # Unknown model-specific ranges must not be invented.
    assert e['sensor']['life_1']['name'].startswith('RO')
    assert e['sensor']['life_2']['name'].startswith('PCB')
    obj = entity(MideaSwitchEntity, 'leak_water_protection', e['switch']['leak_water_protection'], {'leak_water_protect':'on'})
    assert obj.is_on
    obj.coordinator.async_set_attribute = AsyncMock()
    asyncio.run(obj.async_turn_off())
    obj.coordinator.async_set_attribute.assert_awaited_once_with('leak_water_protect','off')


def select_obj(key, cfg, attrs):
    obj = entity(MideaSelectEntity, key, cfg, attrs)
    obj._key_options = cfg['options']
    obj._last_option = None
    obj._status_key = cfg.get('status_key')
    obj._ignore_values = []
    return obj


def test_idle_dishwasher_does_not_start_a_cycle():
    cfg = T0xE1.DEVICE_MAPPING['7600002B']['entities']['select']['wash_mode']
    obj = select_obj('wash_mode', cfg, {'mode':'neutral_gear','work_status':'power_off'})
    assert obj.current_option == '待机（停止）'
    asyncio.run(obj.async_select_option('待机（停止）'))
    obj.coordinator.async_set_attributes.assert_awaited_once_with({'mode':'neutral_gear','work_status':'power_off'})


def test_storage_zero_matches_integer_report():
    cfg = T0xE1.DEVICE_MAPPING['7600002B']['entities']['select']['air_set_hour']
    obj = select_obj('air_set_hour', cfg, {'air_set_hour':0})
    assert obj.current_option == '0'


def test_dishwasher_beep_writes_command_key_but_reads_report_key():
    cfg = T0xE1.DEVICE_MAPPING['7600002B']['entities']['switch']['beep_control']
    obj = entity(MideaSwitchEntity, 'beep_control', cfg, {'beep_control':1})
    assert obj.is_on
    asyncio.run(obj.async_turn_off())
    obj.coordinator.async_set_attributes.assert_awaited_once_with({'common_down_type':5,'switch':0})


def test_hood_setting_keeps_wire_metadata_and_does_not_send_brightness():
    cfg = T0xB6.DEVICE_MAPPING['730006AE']['entities']['switch']['air_curtain_switch']
    obj = entity(MideaSwitchEntity, 'air_curtain_switch', cfg, {'air_curtain_switch':'on','lightness':80})
    asyncio.run(obj.async_turn_off())
    obj.coordinator.async_set_attributes.assert_awaited_once_with({'electronic_control_version':2,'type':'b6','b6_action':'setting','setting':'air_curtain','air_curtain_switch':'off'})
    assert not T0xB6.DEVICE_MAPPING['730006AE']['centralized']


def test_only_explicit_wire_keys_bypass_report_filter():
    p = Path(__file__).resolve().parents[1]/'custom_components/midea_auto_cloud/core/device.py'
    cls = next(n for n in ast.parse(p.read_text()).body if isinstance(n, ast.ClassDef) and n.name=='MiedaDevice')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name=='_has_attribute')
    ns = {'LAMP_CONTROL_KEYS':set()}
    exec(compile(ast.Module(body=[method],type_ignores=[]),str(p),'exec'),ns)
    d = SimpleNamespace(_attributes={'power':'off'}, _control_keys={'type','setting','b6_action'})
    assert ns['_has_attribute'](d,'b6_action')
    assert not ns['_has_attribute'](d,'invented_command')


def test_heater_typo_and_none_error_are_valid_but_global_missing_values_unchanged():
    e = T0xE3.DEVICE_MAPPING['5111102Z']['entities']['sensor']
    obj = entity(MideaSensorEntity,'gas_lift_percent',e['gas_lift_percent'],{'gas_lift_precent':0})
    assert obj.native_value == 0
    obj = entity(MideaSensorEntity,'error_code',e['error_code'],{'error_code':'none'})
    assert obj.native_value == '无故障'
    obj._config = {}
    assert obj.native_value is None
    obj.coordinator.data.attributes['error_code']='E1'
    assert obj.native_value == 'E1'


def test_heater_coupled_controls_keep_the_current_parameter():
    e = T0xE3.DEVICE_MAPPING['5111102Z']['entities']['switch']
    for key, parameter, value in [('bathtub','bathtub_water_level',0), ('person_mode_one','person_tem_one',40)]:
        obj = entity(MideaSwitchEntity,key,e[key],{key:'off',parameter:value})
        obj._include_current = e[key]['include_current']
        asyncio.run(obj.async_turn_on())
        obj.coordinator.async_set_attributes.assert_awaited_once_with({key:'on',parameter:value})
    assert e['bubble']['rationale'] == [0,1]


def test_hood_light_uses_the_vendor_setting_route():
    cfg = T0xB6.DEVICE_MAPPING['730006AE']['entities']['switch']['light']
    assert cfg['command'] == {'electronic_control_version':2,'type':'b6','b6_action':'setting','setting':'light'}


def test_reported_program_does_not_depend_on_command_work_state():
    cfg = T0xE1.DEVICE_MAPPING['7600002B']['entities']['select']['wash_mode']
    obj = select_obj('wash_mode', cfg, {'mode':'eco_wash','work_status':'cancel'})
    assert obj.current_option == 'eco_wash'


def test_storage_duration_accepts_reported_four_hours():
    cfg = T0xE1.DEVICE_MAPPING['7600002B']['entities']['select']['air_set_hour']
    obj = select_obj('air_set_hour',cfg,{'air_set_hour':4})
    assert obj.current_option == '4'
    assert set(map(int,cfg['options'])) == set(range(73))
