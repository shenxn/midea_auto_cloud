import asyncio

import pytest
from homeassistant.components.climate import HVACAction
from midea_auto_cloud.climate import MideaHydronicClimateEntity
from midea_auto_cloud.device_mapping.T0xAC import DEVICE_MAPPING
from test_central_cloud import entity


def hydronic():
    cfg = DEVICE_MAPPING['22397061']['entities']['climate']['hydronic_module']
    obj = entity(MideaHydronicClimateEntity, 'hydronic_module', cfg, {
        'has_water_model':1, 'water_model_power':'off', 'power':'on',
        'water_model_temperature_set':25, 'temperature':18,
        'tw1_out_water_temp':23, 'indoor_temperature':27,
        'water_model_temperature_auto':'off',
    })
    obj._key_hvac_modes = cfg['hvac_modes']
    obj._key_preset_modes = cfg['preset_modes']
    obj._key_current_temperature = cfg['current_temperature']
    obj._key_target_temperature = cfg['target_temperature']
    obj._key_power = cfg['power']
    obj._key_target_temperature_low = None
    obj._key_target_temperature_high = None
    obj._device_type = 0xAC
    obj._last_hvac_mode = 'off'
    return obj


def test_only_selected_entry_exposes_shared_module():
    for model in ['22397061','22397067','22397057','22397063']:
        cfg=DEVICE_MAPPING[model]
        assert ('hydronic_module' in cfg['entities']['climate']) == (model=='22397061')
        assert ({'query_type':'water_model_run_status'} in cfg['queries']) == (model=='22397061')
        assert 'thermostat' in cfg['entities']['climate']
    assert 'link' not in DEVICE_MAPPING['22397061']['entities']['climate']['hydronic_module']['preset_modes']


@pytest.mark.parametrize('action,value',[('async_turn_on','on'),('async_turn_off','off')])
def test_power_never_changes_the_air_conditioner(action,value):
    obj=hydronic()
    asyncio.run(getattr(obj,action)())
    obj.coordinator.async_set_attributes.assert_awaited_once_with({'single_control':1,'water_model_power':value})
    assert obj.coordinator.data.attributes['power']=='on'


@pytest.mark.parametrize('temperature',[25,26,60])
def test_manual_water_setpoint_disables_auto_without_starting_heat(temperature):
    obj=hydronic()
    asyncio.run(obj.async_set_temperature(temperature=temperature))
    obj.coordinator.async_set_attributes.assert_awaited_once_with({'single_control':1,'water_model_temperature_set':temperature,'water_model_temperature_auto':'off'})


@pytest.mark.parametrize('temperature',[24,61,25.5,float('nan'),float('inf')])
def test_invalid_water_setpoints_do_not_send(temperature):
    obj=hydronic()
    with pytest.raises(ValueError):asyncio.run(obj.async_set_temperature(temperature=temperature))
    obj.coordinator.async_set_attributes.assert_not_awaited()


@pytest.mark.parametrize('preset,value',[('手动','off'),('自动','on')])
def test_automatic_water_temperature_control(preset,value):
    obj=hydronic()
    asyncio.run(obj.async_set_preset_mode(preset))
    obj.coordinator.async_set_attributes.assert_awaited_once_with({'single_control':1,'water_model_temperature_auto':value})


def test_status_uses_water_fields_and_does_not_infer_heating():
    obj=hydronic()
    assert obj.available
    assert obj.current_temperature == 23
    assert obj.target_temperature == 25
    assert obj.hvac_mode == 'off'
    assert obj.hvac_action == HVACAction.OFF
    obj.coordinator.data.attributes['water_model_power']='on'
    assert obj.hvac_mode == 'heat'
    assert obj.hvac_action is None
    obj.coordinator.data.attributes.pop('tw1_out_water_temp')
    assert obj.current_temperature is None


def test_air_commands_cannot_pass_the_hydronic_surface():
    obj=hydronic()
    with pytest.raises(ValueError):asyncio.run(obj.async_set_attributes({'power':'on'}))
    obj.coordinator.async_set_attributes.assert_not_awaited()


def test_six_hydronic_entities_share_one_group_without_grouping_air_entities():
    e = DEVICE_MAPPING['22397061']['entities']
    grouped = [(str(p), k) for p, configs in e.items() for k,c in configs.items() if c.get('device_group')=='hydronic']
    assert len(grouped)==6
    assert ('climate','hydronic_module') in grouped
    assert 'device_group' not in e['climate']['thermostat']
    for model in ['22397067','22397057','22397063']:
        assert not any(c.get('device_group') for configs in DEVICE_MAPPING[model]['entities'].values() for c in configs.values())


def test_device_split_preserves_entity_identity_and_cloud_transport(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import MagicMock
    from midea_auto_cloud import midea_entity as module

    monkeypatch.setattr(module, 'Debouncer', MagicMock())
    coordinator = SimpleNamespace(hass=MagicMock(), config_entry=None)
    device = MagicMock()
    def make(group):
        return module.MideaEntity(coordinator,123,'AC','T0xAC','parent-serial','22397061','CAKW71','hydronic_module',device=device,config={'device_group':group})
    old = make(None)
    new = make('hydronic')
    assert old.unique_id == new.unique_id
    assert new._device_id == old._device_id == 123
    assert new._device is old._device is device
    assert old.device_info['identifiers'] == {('midea_auto_cloud','123')}
    assert new.device_info['identifiers'] == {('midea_auto_cloud','123:hydronic')}
    assert new.device_info['via_device'] == ('midea_auto_cloud','123')
    assert new.device_info['name'] == '地暖水力模块'
    assert 'serial_number' not in new.device_info
