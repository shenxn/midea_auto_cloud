"""One hydronic control surface through the selected living-room AC model."""
from homeassistant.const import Platform


def add_hydronic_module(config):
    """The installation has one shared module; other indoor units stay unchanged."""
    config['queries'].append({'query_type': 'water_model_run_status'})
    condition = {'eq': ['has_water_model', 1]}
    e = config['entities']
    e[Platform.CLIMATE]['hydronic_module'] = {
        'name': '地暖水力模块',
        'hydronic_module': True,
        'condition': condition,
        'power': 'water_model_power',
        'hvac_modes': {
            'off': {'water_model_power': 'off'},
            'heat': {'water_model_power': 'on'},
        },
        'preset_modes': {
            '手动': {'water_model_temperature_auto': 'off'},
            '自动': {'water_model_temperature_auto': 'on'},
        },
        'target_temperature': 'water_model_temperature_set',
        'current_temperature': 'tw1_out_water_temp',
        'min_temp': 25,
        'max_temp': 60,
        'precision': 1,
        'temperature_unit': '°C',
    }
    for key, name in [
        ('water_model_ptc', '地暖电辅热'),
        ('water_model_power_save', '地暖节能'),
        ('water_model_go_out', '地暖外出'),
    ]:
        e[Platform.SWITCH][key] = {
            'name': name,
            'rationale': ['off', 'on'],
            'condition': condition,
            'command': {'single_control': 1},
        }
    for key, name in [('tw1_in_water_temp', '地暖进水温度'), ('tw1_out_water_temp', '地暖出水温度')]:
        e[Platform.SENSOR][key] = {
            'name': name,
            'condition': condition,
            'device_class': 'temperature',
            'unit_of_measurement': '°C',
            'state_class': 'measurement',
        }

    # All six entities share one logical device, while retaining their unique IDs.
    for platform, keys in {
        Platform.CLIMATE: ["hydronic_module"],
        Platform.SWITCH: ["water_model_ptc", "water_model_power_save", "water_model_go_out"],
        Platform.SENSOR: ["tw1_in_water_temp", "tw1_out_water_temp"],
    }.items():
        for key in keys:
            e[platform][key]["device_group"] = "hydronic"
    names = {"hydronic_module": "温控", "water_model_ptc": "电辅热",
             "water_model_power_save": "节能", "water_model_go_out": "外出",
             "tw1_in_water_temp": "进水温度", "tw1_out_water_temp": "出水温度"}
    for configs in e.values():
        for key, entity in configs.items():
            if entity.get("device_group") == "hydronic":
                entity["name"] = names[key]
